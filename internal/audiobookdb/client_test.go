package audiobookdb

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestCombinedBudget(t *testing.T) {
	b := &Budget{}
	for _, cost := range []int{1, 3, 1, 1, 1, 1, 1, 1, 1, 1} {
		if !b.reserve(cost) {
			t.Fatal("valid cold path rejected")
		}
	}
	if b.reserve(1) {
		t.Fatal("attempt overshoot")
	}
	n, c := b.Counts()
	if n != 10 || c != 12 {
		t.Fatal("incorrect counts")
	}
	b = &Budget{}
	for i := 0; i < 4; i++ {
		if !b.reserve(3) {
			t.Fatal("cost")
		}
	}
	if b.reserve(1) {
		t.Fatal("cost overshoot")
	}
	if !b.consume(MaxBytes) || b.consume(1) {
		t.Fatal("aggregate byte cap")
	}
}

func TestRetryAfterFormatsAndScopedCooldown(t *testing.T) {
	now := time.Date(2026, 10, 5, 12, 0, 0, 200000000, time.UTC)
	date := now.Truncate(time.Second).Add(120 * time.Second)
	for _, tc := range []struct {
		name, header string
		seconds      int
	}{
		{"seconds", "120", 120},
		{"HTTP date", date.Format(http.TimeFormat), 120},
		{"obsolete RFC850 date", date.Format(time.RFC850), 120},
		{"obsolete ANSI date", date.Format(time.ANSIC), 120},
		{"past date", now.Add(-time.Minute).Format(http.TimeFormat), 1},
		{"long date", now.Add(time.Hour).Format(http.TimeFormat), 300},
		{"bounded integer", "9999", 300},
		{"integer overflow", "9999999999999999999999999999999999999", 300},
		{"zero", "0", 1},
		{"empty", "", 1},
		{"negative", "-20", 1},
		{"signed", "+20", 1},
		{"malformed", "tomorrow", 1},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var calls atomic.Int32
			up := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				calls.Add(1)
				w.Header().Set("Retry-After", tc.header)
				w.WriteHeader(429)
			}))
			defer up.Close()
			c := New(up.URL, "operator@example.invalid", up.Client().Transport)
			defer c.Close()
			c.now = func() time.Time { return now }
			f := AsFault(c.Authorize(context.Background(), &Budget{}, "synthetic"))
			if f.Status != 503 || f.RetryAfter != tc.seconds {
				t.Fatalf("429 translated to status %d / retry %d, want 503 / %d", f.Status, f.RetryAfter, tc.seconds)
			}
			f = AsFault(c.Authorize(context.Background(), &Budget{}, "synthetic"))
			if f.Status != 503 || f.RetryAfter != tc.seconds || calls.Load() != 1 {
				t.Fatal("cooldown was bypassed or rounded beyond its bound")
			}
			if c.cooldown("other") != 0 {
				t.Fatal("cooldown leaked across credentials")
			}
			nowAtExpiry := now.Add(time.Duration(tc.seconds) * time.Second)
			c.now = func() time.Time { return nowAtExpiry }
			if c.cooldown("synthetic") != 0 {
				t.Fatal("cooldown did not expire at its boundary")
			}
		})
	}
}
func TestResponsesRateAndNoRedirect(t *testing.T) {
	var calls atomic.Int32
	up := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		if (r.Header.Get("X-API-Key") != "synthetic" && r.Header.Get("X-API-Key") != "other") || !strings.Contains(r.Header.Get("User-Agent"), "operator@example.invalid") {
			t.Error("headers")
		}
		switch r.URL.Path {
		case "/auth/session":
			w.Write([]byte(`{"id":"invented"}`))
		case "/limited":
			w.Header().Set("Retry-After", "9999")
			w.WriteHeader(429)
		case "/redirect":
			w.Header().Set("Location", "/auth/session")
			w.WriteHeader(302)
		case "/bad":
			w.Write([]byte(`{"id":"invented"} trailing`))
		case "/huge":
			w.Write([]byte(strings.Repeat("x", 100)))
		case "/null":
			w.Write([]byte(`null`))
		case "/denied":
			w.WriteHeader(403)
		}
	}))
	defer up.Close()
	c := New(up.URL, "operator@example.invalid", up.Client().Transport)
	defer c.Close()
	ctx := context.Background()
	if err := c.Authorize(ctx, &Budget{}, "synthetic"); err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct {
		path, code    string
		status, limit int
	}{{"/redirect", "upstream_unavailable", 502, 100}, {"/bad", "upstream_schema", 502, 100}, {"/huge", "upstream_size", 502, 64}, {"/null", "upstream_schema", 502, 100}, {"/denied", "unauthorized", 401, 100}} {
		var out any
		err := c.read(ctx, &Budget{}, "synthetic", "GET", tc.path, nil, tc.limit, 1, &out)
		f := AsFault(err)
		if f.Status != tc.status || f.Code != tc.code {
			t.Errorf("%s: %v", tc.path, err)
		}
	}
	var out any
	err := c.read(ctx, &Budget{}, "synthetic", "GET", "/limited", nil, 100, 1, &out)
	f := AsFault(err)
	if f.Status != 503 || f.RetryAfter != 300 {
		t.Fatal("retry-after bound")
	}
	before := calls.Load()
	if err := c.Authorize(ctx, &Budget{}, "synthetic"); AsFault(err).Status != 503 || calls.Load() != before {
		t.Fatal("cooldown bypass")
	}
	if err := c.Authorize(ctx, &Budget{}, "other"); AsFault(err).Status == 503 {
		t.Fatal("cooldown scope")
	}
}
func TestPacingCancellationAndConcurrency(t *testing.T) {
	var mu sync.Mutex
	var starts []time.Time
	var active, peak atomic.Int32
	up := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		a := active.Add(1)
		defer active.Add(-1)
		for {
			p := peak.Load()
			if a <= p || peak.CompareAndSwap(p, a) {
				break
			}
		}
		mu.Lock()
		starts = append(starts, time.Now())
		mu.Unlock()
		select {
		case <-r.Context().Done():
			return
		case <-time.After(400 * time.Millisecond):
		}
		json.NewEncoder(w).Encode(map[string]string{"id": "invented"})
	}))
	defer up.Close()
	c := New(up.URL, "operator@example.invalid", up.Client().Transport)
	defer c.Close()
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
			defer cancel()
			if err := c.Authorize(ctx, &Budget{}, "synthetic"); err != nil {
				t.Error(err)
			}
		}()
	}
	wg.Wait()
	if peak.Load() > 4 {
		t.Fatal("concurrency overshoot")
	}
	mu.Lock()
	for i := 1; i < len(starts); i++ {
		if starts[i].Sub(starts[i-1]) < 200*time.Millisecond {
			t.Fatal("unpaced dispatch")
		}
	}
	mu.Unlock()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	before := time.Now()
	if err := c.Authorize(ctx, &Budget{}, "synthetic"); AsFault(err).Status != 504 || time.Since(before) > 100*time.Millisecond {
		t.Fatal("cancellation")
	}
}
func TestTLSValidationAndAttemptTimeout(t *testing.T) {
	up := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() }))
	defer up.Close()
	untrusted := New(up.URL, "operator@example.invalid", nil)
	defer untrusted.Close()
	if err := untrusted.Authorize(context.Background(), &Budget{}, "synthetic"); AsFault(err).Status != 502 {
		t.Fatal("TLS trust not enforced")
	}
	c := New(up.URL, "operator@example.invalid", up.Client().Transport)
	defer c.Close()
	started := time.Now()
	if err := c.Authorize(context.Background(), &Budget{}, "synthetic"); AsFault(err).Status != 504 || time.Since(started) > 2500*time.Millisecond {
		t.Fatal("attempt timeout")
	}
}
