package bounds

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

const keyA = "SYNTHETIC-SECRET-A"
const keyB = "SYNTHETIC-SECRET-B"

type fixture struct {
	revoked       atomic.Bool
	active        atomic.Int32
	peak          atomic.Int32
	lookups       atomic.Int32
	details       atomic.Int32
	canceled      atomic.Int32
	sharedRelease chan struct{}
}

func setup(t *testing.T) (*Client, *fixture) {
	t.Helper()
	f := &fixture{sharedRelease: make(chan struct{})}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		active := f.active.Add(1)
		defer f.active.Add(-1)
		for {
			old := f.peak.Load()
			if active <= old || f.peak.CompareAndSwap(old, active) {
				break
			}
		}
		key := r.Header.Get("Authorization")
		if key != keyA && key != keyB || key == keyA && f.revoked.Load() {
			w.WriteHeader(401)
			w.Write([]byte(key))
			return
		}
		if r.URL.Path == "/validate" {
			w.Write([]byte(`{}`))
			return
		}
		query := r.URL.Query().Get("q")
		if r.URL.Path == "/lookup" {
			f.lookups.Add(1)
			switch query {
			case "shared":
				select {
				case <-f.sharedRelease:
				case <-r.Context().Done():
					f.canceled.Add(1)
					return
				}
			case "missing":
				w.WriteHeader(404)
				return
			case "fault400":
				w.WriteHeader(400)
				return
			case "fault500":
				w.WriteHeader(500)
				w.Write([]byte(key))
				return
			case "fault503":
				w.WriteHeader(503)
				return
			case "limited":
				w.Header().Set("Retry-After", "1")
				w.WriteHeader(429)
				return
			case "malformed":
				w.Write([]byte(`{"bad":true}`))
				return
			case "oversized":
				w.Write([]byte(strings.Repeat("x", (1<<20)+5)))
				return
			case "slow":
				select {
				case <-r.Context().Done():
					f.canceled.Add(1)
					return
				case <-time.After(3 * time.Second):
				}
			}
			w.Write([]byte(`[1,2,3,4]`))
			return
		}
		if r.URL.Path == "/detail" {
			f.details.Add(1)
			select {
			case <-r.Context().Done():
				f.canceled.Add(1)
				return
			case <-time.After(20 * time.Millisecond):
			}
			tenant := "tenant-a"
			if key == keyB {
				tenant = "tenant-b"
			}
			json.NewEncoder(w).Encode(tenant)
			return
		}
		w.WriteHeader(404)
	}))
	t.Cleanup(server.Close)
	return New(server.URL), f
}
func faultStatus(err error) int {
	var f *Fault
	if errors.As(err, &f) {
		return f.Status
	}
	return 0
}

func TestCredentialCacheAndFlightIsolation(t *testing.T) {
	c, f := setup(t)
	var wg sync.WaitGroup
	failures := make(chan bool, 32)
	start := time.Now()
	for i := 0; i < 32; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			key, want := keyA, "tenant-a"
			if i%2 == 1 {
				key, want = keyB, "tenant-b"
			}
			data, err := c.Search(context.Background(), key, "same-query")
			if err != nil || len(data) != 4 {
				failures <- true
				return
			}
			for _, v := range data {
				if v != want {
					failures <- true
					return
				}
			}
		}(i)
	}
	wg.Wait()
	close(failures)
	for range failures {
		t.Fatal("credential isolation failed")
	}
	if f.lookups.Load() != 2 || f.details.Load() != 8 {
		t.Fatal("work was not coalesced per credential")
	}
	if f.peak.Load() > 4 {
		t.Fatal("concurrency cap exceeded")
	}
	t.Logf("32 interleaved requests: %d lookup calls, %d detail calls, peak %d; elapsed %s", f.lookups.Load(), f.details.Load(), f.peak.Load(), time.Since(start))
}

func TestRevocationCannotUseWarmCache(t *testing.T) {
	c, f := setup(t)
	if _, err := c.Search(context.Background(), keyA, "same-query"); err != nil {
		t.Fatal("cold request failed")
	}
	before := f.lookups.Load()
	if _, err := c.Search(context.Background(), keyA, "same-query"); err != nil || f.lookups.Load() != before {
		t.Fatal("warm cache failed")
	}
	f.revoked.Store(true)
	_, err := c.Search(context.Background(), keyA, "same-query")
	if faultStatus(err) != 401 {
		t.Fatal("revoked credential reached cached data")
	}
	if strings.Contains(err.Error(), keyA) {
		t.Fatal("secret in error")
	}
	c.mu.Lock()
	size := len(c.cache)
	c.mu.Unlock()
	if size != 0 {
		t.Fatal("rejected credential cache retained")
	}
}

func TestErrorsRetryAfterAndNoSecretErrors(t *testing.T) {
	c, _ := setup(t)
	for _, test := range []struct {
		query  string
		status int
	}{{"fault400", 502}, {"fault500", 502}, {"fault503", 502}, {"limited", 503}, {"malformed", 502}, {"oversized", 502}} {
		t.Run(test.query, func(t *testing.T) {
			started := time.Now()
			_, err := c.Search(context.Background(), keyA, test.query)
			if faultStatus(err) != test.status {
				t.Fatal("incorrect failure status")
			}
			if strings.Contains(err.Error(), keyA) || strings.Contains(err.Error(), keyB) {
				t.Fatal("secret in error")
			}
			if test.query == "limited" && time.Since(started) < time.Second {
				t.Fatal("Retry-After was not honored")
			}
		})
	}
	data, err := c.Search(context.Background(), keyA, "missing")
	if err != nil || len(data) != 0 {
		t.Fatal("not-found became a failure")
	}
	if _, err = c.Search(context.Background(), keyA, ""); faultStatus(err) != 400 {
		t.Fatal("input validation failed")
	}
	if _, err = c.Search(context.Background(), "", "query"); faultStatus(err) != 401 {
		t.Fatal("missing credential accepted")
	}
	if _, err = c.Search(context.Background(), "rejected-synthetic-key", "query"); faultStatus(err) != 401 {
		t.Fatal("invalid credential accepted")
	}
}

func TestCancellationAndWaiterOwnership(t *testing.T) {
	c, f := setup(t)
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()
	started := time.Now()
	_, err := c.Search(ctx, keyA, "slow")
	if faultStatus(err) != 504 {
		t.Fatal("cancel did not stop caller")
	}
	for deadline := time.Now().Add(300 * time.Millisecond); f.canceled.Load() == 0 && time.Now().Before(deadline); {
		time.Sleep(time.Millisecond)
	}
	if f.canceled.Load() == 0 || time.Since(started) > 500*time.Millisecond {
		t.Fatal("upstream work did not cancel within bound")
	}
	// A canceled waiter must not cancel another caller's shared flight.
	var releaseOnce sync.Once
	releaseShared := func() { releaseOnce.Do(func() { close(f.sharedRelease) }) }
	t.Cleanup(releaseShared)
	sharedKey := scope(keyA) + ":shared"
	ctx1, cancel1 := context.WithCancel(context.Background())
	defer cancel1()
	done := make(chan error, 1)
	go func() { _, err := c.Search(ctx1, keyA, "shared"); done <- err }()
	for deadline := time.Now().Add(time.Second); ; {
		c.mu.Lock()
		shared := c.flights[sharedKey]
		count := 0
		if shared != nil {
			count = shared.waiters
		}
		c.mu.Unlock()
		if count > 0 {
			break
		}
		if time.Now().After(deadline) {
			t.Fatal("flight did not start")
		}
		time.Sleep(time.Millisecond)
	}
	second := make(chan error, 1)
	go func() { _, err := c.Search(context.Background(), keyA, "shared"); second <- err }()
	for deadline := time.Now().Add(time.Second); ; {
		c.mu.Lock()
		waiters := 0
		if shared := c.flights[sharedKey]; shared != nil {
			waiters = shared.waiters
		}
		c.mu.Unlock()
		if waiters >= 2 {
			break
		}
		if time.Now().After(deadline) {
			t.Fatal("second waiter did not join")
		}
		time.Sleep(time.Millisecond)
	}
	cancel1()
	if faultStatus(<-done) != 504 {
		t.Fatal("canceled waiter did not exit")
	}
	releaseShared()
	if <-second != nil {
		t.Fatal("one canceled waiter killed shared work")
	}
}

func TestBoundedCacheAndTransientFailures(t *testing.T) {
	c, f := setup(t)
	for _, query := range []string{"q1", "q2", "q3", "q4", "q5", "q6"} {
		if _, err := c.Search(context.Background(), keyA, query); err != nil {
			t.Fatal("cache fixture failed")
		}
	}
	c.mu.Lock()
	size := len(c.cache)
	c.mu.Unlock()
	if size > 4 {
		t.Fatal("cache entry cap exceeded")
	}
	before := f.lookups.Load()
	for i := 0; i < 2; i++ {
		c.Search(context.Background(), keyA, "fault500")
	}
	if f.lookups.Load()-before != 2 {
		t.Fatal("transient failure cached")
	}
	t.Logf("Cache bounded to %d entries; transient failures refetched", size)
}
