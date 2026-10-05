package server

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"sync/atomic"
	"time"

	"abs-audiobookdb/internal/audiobookdb"
	"abs-audiobookdb/internal/config"
	"abs-audiobookdb/internal/provider"
)

type Searcher interface {
	Search(context.Context, string, provider.Input) ([]byte, error)
}
type Handler struct {
	provider Searcher
	fallback string
	logger   *slog.Logger
	ids      atomic.Uint64
	ready    atomic.Bool
}

func New(p Searcher, fallback string, logger *slog.Logger) *Handler {
	h := &Handler{provider: p, fallback: fallback, logger: logger}
	h.ready.Store(true)
	return h
}
func (h *Handler) Stop() { h.ready.Store(false) }
func credential(headers http.Header, fallback string) (string, error) {
	values, exists := headers["Authorization"]
	key := fallback
	if exists {
		if len(values) != 1 {
			return "", audiobookdb.Failure(401, "unauthorized")
		}
		key = strings.TrimSpace(values[0])
		parts := strings.Fields(key)
		if len(parts) == 2 && strings.EqualFold(parts[0], "bearer") {
			key = parts[1]
		} else if len(parts) != 1 || strings.EqualFold(key, "bearer") {
			return "", audiobookdb.Failure(401, "unauthorized")
		}
	}
	if !config.ValidKey(key) {
		return "", audiobookdb.Failure(401, "unauthorized")
	}
	return key, nil
}
func writeError(w http.ResponseWriter, err error) int {
	f := audiobookdb.AsFault(err)
	if f.RetryAfter > 0 {
		w.Header().Set("Retry-After", strconv.Itoa(f.RetryAfter))
	}
	w.WriteHeader(f.Status)
	json.NewEncoder(w).Encode(map[string]string{"error": f.Code})
	return f.Status
}
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	headerBytes := len(r.Host) + len("Host: \r\n")
	for name, values := range r.Header {
		for _, value := range values {
			headerBytes += len(name) + len(value) + 4
		}
	}
	if headerBytes > 8<<10 {
		writeError(w, audiobookdb.Failure(431, "headers_too_large"))
		return
	}
	if r.Method != "GET" {
		w.Header().Set("Allow", "GET")
		writeError(w, audiobookdb.Failure(405, "method_not_allowed"))
		return
	}
	if r.URL.Path == "/health" || r.URL.Path == "/ready" {
		if !h.ready.Load() {
			writeError(w, audiobookdb.Failure(503, "not_ready"))
			return
		}
		w.Write([]byte("{\"status\":\"ok\"}\n"))
		return
	}
	if r.URL.Path != "/search" {
		writeError(w, audiobookdb.Failure(404, "not_found"))
		return
	}
	started := time.Now()
	id := h.ids.Add(1)
	w.Header().Set("X-Request-ID", strconv.FormatUint(id, 10))
	status := 200
	code := "ok"
	defer func() {
		h.logger.Info("search", "request_id", id, "status", status, "code", code, "duration_ms", time.Since(started).Milliseconds())
	}()
	if !h.ready.Load() {
		code = "not_ready"
		status = writeError(w, audiobookdb.Failure(503, code))
		return
	}
	input, err := provider.Parse(r.URL.RawQuery)
	if err != nil {
		code = audiobookdb.AsFault(err).Code
		status = writeError(w, err)
		return
	}
	key, err := credential(r.Header, h.fallback)
	if err != nil {
		code = "unauthorized"
		status = writeError(w, err)
		return
	}
	data, err := h.provider.Search(r.Context(), key, input)
	if err != nil {
		code = audiobookdb.AsFault(err).Code
		status = writeError(w, err)
		return
	}
	w.Write(data)
}
