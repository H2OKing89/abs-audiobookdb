package server

import (
	"bytes"
	"context"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"abs-audiobookdb/internal/provider"
)

type fake struct {
	key   string
	calls int
}

func (f *fake) Search(_ context.Context, key string, _ provider.Input) ([]byte, error) {
	f.key = key
	f.calls++
	return []byte(`{"matches":[]}`), nil
}
func TestCredentialRulesAndSafeLogs(t *testing.T) {
	var logs bytes.Buffer
	search := &fake{}
	h := New(search, "fallback-sentinel", slog.New(slog.NewJSONHandler(&logs, nil)))
	for _, tc := range []struct {
		header []string
		status int
		key    string
	}{{nil, 200, "fallback-sentinel"}, {[]string{"raw-sentinel"}, 200, "raw-sentinel"}, {[]string{"bEaReR bearer-sentinel"}, 200, "bearer-sentinel"}, {[]string{""}, 401, ""}, {[]string{"Bearer"}, 401, ""}, {[]string{"a", "b"}, 401, ""}, {[]string{"two words"}, 401, ""}} {
		r := httptest.NewRequest("GET", "/search?query=private-title-sentinel", nil)
		if tc.header != nil {
			r.Header["Authorization"] = tc.header
		}
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		if w.Code != tc.status || tc.status == 200 && search.key != tc.key {
			t.Fatalf("credential rule: %d", w.Code)
		}
	}
	for _, private := range []string{"fallback-sentinel", "raw-sentinel", "bearer-sentinel", "private-title-sentinel"} {
		if strings.Contains(logs.String(), private) {
			t.Fatal("private log value")
		}
	}
	before := search.calls
	for _, path := range []string{"/health", "/ready"} {
		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest("GET", path, nil))
		if w.Code != 200 || search.calls != before {
			t.Fatal("health must not call upstream")
		}
	}
	h.Stop()
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/ready", nil))
	if w.Code != 503 {
		t.Fatal("shutdown readiness")
	}
}
func TestMethodsInputAndHeaderLimits(t *testing.T) {
	h := New(&fake{}, "fallback", slog.New(slog.NewTextHandler(&bytes.Buffer{}, nil)))
	for _, tc := range []struct {
		method, path string
		status       int
	}{{"POST", "/search?query=Valid", 405}, {"GET", "/unknown", 404}, {"GET", "/search?isbn=9780000000002", 400}} {
		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest(tc.method, tc.path, nil))
		if w.Code != tc.status {
			t.Error("status", w.Code)
		}
	}
	r := httptest.NewRequest(http.MethodGet, "/search?query=Valid", nil)
	r.Header.Set("X-Large", strings.Repeat("x", 8192))
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != 431 {
		t.Fatal("header ceiling")
	}
}
