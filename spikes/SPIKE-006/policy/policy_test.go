package policy

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestCombinedAttemptAndCostBudget(t *testing.T) {
	b := &Budget{}
	for _, cost := range []int{1, 3, 1, 1, 1, 1, 1, 1, 1, 1} {
		if !b.Reserve(cost) {
			t.Fatal("valid maximum cold path rejected")
		}
	}
	if b.Reserve(1) {
		t.Fatal("eleventh attempt allowed")
	}
	a, c := b.Counts()
	if a != 10 || c != 12 {
		t.Fatal("budget counts mismatch")
	}
	other := &Budget{}
	for i := 0; i < 4; i++ {
		if !other.Reserve(3) {
			t.Fatal("valid cost rejected")
		}
	}
	if other.Reserve(1) {
		t.Fatal("cost limit bypassed below attempt limit")
	}
	t.Logf("Cold path bounded to %d attempts and %d documented cost units including authorization", a, c)
}

func TestFreshAuthBeforeEveryHitAndRevocationPurge(t *testing.T) {
	p := New()
	var revoked atomic.Bool
	var validations, fetches atomic.Int32
	auth := func(context.Context) error {
		validations.Add(1)
		if revoked.Load() {
			return &Fault{401}
		}
		return nil
	}
	fetch := func(context.Context, *Budget) ([]byte, error) {
		fetches.Add(1)
		return []byte(`{"matches":[{"title":"Invented"}]}`), nil
	}
	for i := 0; i < 2; i++ {
		if _, err := p.Lookup(context.Background(), "synthetic-key-a", "title", auth, fetch); err != nil {
			t.Fatal("valid path failed")
		}
	}
	if validations.Load() != 2 || fetches.Load() != 1 {
		t.Fatal("warm hit bypassed auth or refetched")
	}
	revoked.Store(true)
	if _, err := p.Lookup(context.Background(), "synthetic-key-a", "title", auth, fetch); err == nil {
		t.Fatal("revoked fixture key reached warm results")
	}
	entries, bytes := p.Stats()
	if entries != 0 || bytes != 0 {
		t.Fatal("rejected credential retained cached payload")
	}
	if fetches.Load() != 1 {
		t.Fatal("rejected credential reached fetch")
	}
}

func TestCredentialPartitionAndPayloadIsolation(t *testing.T) {
	p := New()
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			key := fmt.Sprintf("synthetic-key-%d", i%2)
			want := []byte(key)
			data, err := p.Lookup(context.Background(), key, "same", func(context.Context) error { return nil }, func(context.Context, *Budget) ([]byte, error) { return want, nil })
			if err != nil || string(data) != key {
				t.Error("credential isolation failed")
				return
			}
			data[0] = 'X'
		}(i)
	}
	wg.Wait()
	for i := 0; i < 2; i++ {
		key := fmt.Sprintf("synthetic-key-%d", i)
		data, err := p.Lookup(context.Background(), key, "same", func(context.Context) error { return nil }, func(context.Context, *Budget) ([]byte, error) { t.Error("expected warm payload"); return nil, nil })
		if err != nil || string(data) != key {
			t.Fatal("returned payload mutation affected cache")
		}
	}
}

func TestRejectedCredentialCannotBeRepopulatedByOlderWork(t *testing.T) {
	p := New()
	started, release := make(chan struct{}), make(chan struct{})
	done := make(chan error, 1)
	go func() {
		_, err := p.Lookup(context.Background(), "key", "cold", func(context.Context) error { return nil }, func(context.Context, *Budget) ([]byte, error) {
			close(started)
			<-release
			return []byte(`{"matches":[]}`), nil
		})
		done <- err
	}()
	<-started
	p.Purge("key")
	close(release)
	if <-done != nil {
		t.Fatal("fresh caller failed")
	}
	entries, bytes := p.Stats()
	if entries != 0 || bytes != 0 {
		t.Fatal("old authenticated work repopulated rejected credential")
	}
}

func TestEntryByteAndExpiryBounds(t *testing.T) {
	p := New()
	clock := time.Now()
	p.now = func() time.Time { return clock }
	auth := func(context.Context) error { return nil }
	for i := 0; i < MaxEntries+2; i++ {
		_, err := p.Lookup(context.Background(), "key", fmt.Sprint(i), auth, func(context.Context, *Budget) ([]byte, error) { return []byte(`{"matches":[]}`), nil })
		if err != nil {
			t.Fatal("small payload failed")
		}
	}
	entries, _ := p.Stats()
	if entries != MaxEntries {
		t.Fatal("entry cap failed")
	}
	for i := 0; i < 8; i++ {
		_, err := p.Lookup(context.Background(), "key", "large"+fmt.Sprint(i), auth, func(context.Context, *Budget) ([]byte, error) { return make([]byte, MaxResponseBytes-1024), nil })
		if err != nil {
			t.Fatal("large fixture failed")
		}
	}
	entries, bytes := p.Stats()
	if bytes > MaxCacheBytes || entries >= 8 {
		t.Fatal("byte cap not enforced")
	}
	clock = clock.Add(CacheTTL)
	p.Sweep()
	entries, bytes = p.Stats()
	if entries != 0 || bytes != 0 {
		t.Fatal("expired bytes retained after sweep")
	}
	t.Logf("Cache bounded to %d entries / %d bytes; expired payloads swept", MaxEntries, MaxCacheBytes)
}

func TestConcurrencyAdmissionAndCancellation(t *testing.T) {
	p := New()
	var active, peak atomic.Int32
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			b := &Budget{}
			err := p.UpstreamCall(context.Background(), b, 1, func(context.Context) error {
				n := active.Add(1)
				defer active.Add(-1)
				for {
					old := peak.Load()
					if n <= old || peak.CompareAndSwap(old, n) {
						break
					}
				}
				time.Sleep(20 * time.Millisecond)
				return nil
			})
			if err != nil {
				t.Error("bounded call failed")
			}
		}()
	}
	wg.Wait()
	if peak.Load() > MaxUpstream {
		t.Fatal("global upstream cap exceeded")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	start := time.Now()
	_, err := p.Lookup(ctx, "key", "slow", func(ctx context.Context) error { <-ctx.Done(); return ctx.Err() }, func(context.Context, *Budget) ([]byte, error) { t.Error("canceled auth reached data"); return nil, nil })
	if err == nil || time.Since(start) > 500*time.Millisecond {
		t.Fatal("cancellation bound failed")
	}
	for i := 0; i < MaxActive; i++ {
		p.active <- struct{}{}
	}
	_, err = p.Lookup(context.Background(), "key", "overload", func(context.Context) error { t.Error("overload reached auth"); return nil }, nil)
	if f, ok := err.(*Fault); !ok || f.Status != 503 {
		t.Fatal("ninth active request not rejected")
	}
	t.Logf("Peak upstream concurrency %d; active request cap %d", peak.Load(), MaxActive)
}

func TestDeadlineAndNoOversizeOrFailureCaching(t *testing.T) {
	p := New()
	auth := func(ctx context.Context) error {
		deadline, ok := ctx.Deadline()
		if !ok || time.Until(deadline) > CallTimeout {
			t.Error("missing per-call deadline")
		}
		return nil
	}
	for i := 0; i < 2; i++ {
		_, err := p.Lookup(context.Background(), "key", "too-big", auth, func(ctx context.Context, b *Budget) ([]byte, error) {
			deadline, ok := ctx.Deadline()
			if !ok || time.Until(deadline) > Deadline {
				t.Error("missing total deadline")
			}
			return make([]byte, MaxResponseBytes+1), nil
		})
		if err == nil {
			t.Fatal("oversized mapped response accepted")
		}
	}
	entries, _ := p.Stats()
	if entries != 0 {
		t.Fatal("oversized payload cached")
	}
	for i := 0; i < 2; i++ {
		_, err := p.Lookup(context.Background(), "key", "fault", auth, func(context.Context, *Budget) ([]byte, error) { return nil, &Fault{502} })
		if err == nil {
			t.Fatal("upstream failure ignored")
		}
	}
	entries, _ = p.Stats()
	if entries != 0 {
		t.Fatal("transient failure cached")
	}
}
