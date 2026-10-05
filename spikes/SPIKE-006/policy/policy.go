// Package policy verifies final planning rules; it is not production adapter code.
package policy

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"sync"
	"time"
)

const (
	Deadline         = 8 * time.Second
	CallTimeout      = 2 * time.Second
	MaxAttempts      = 10
	MaxCost          = 12
	MaxActive        = 8
	MaxUpstream      = 4
	MaxEntries       = 64
	MaxCacheBytes    = 4 << 20
	MaxResponseBytes = 1 << 20
	CacheTTL         = 60 * time.Second
)

type Fault struct{ Status int }

func (f *Fault) Error() string { return "request failed" }

type Budget struct {
	mu             sync.Mutex
	attempts, cost int
}

func (b *Budget) Reserve(cost int) bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	if cost <= 0 || b.attempts >= MaxAttempts || b.cost+cost > MaxCost {
		return false
	}
	b.attempts++
	b.cost += cost
	return true
}
func (b *Budget) Counts() (int, int) { b.mu.Lock(); defer b.mu.Unlock(); return b.attempts, b.cost }

type entry struct {
	payload []byte
	expires time.Time
	order   uint64
}
type Policy struct {
	mu         sync.Mutex
	entries    map[string]entry
	bytes      int
	order      uint64
	generation uint64
	now        func() time.Time
	active     chan struct{}
	upstream   chan struct{}
}

func New() *Policy {
	return &Policy{entries: map[string]entry{}, now: time.Now, active: make(chan struct{}, MaxActive), upstream: make(chan struct{}, MaxUpstream)}
}
func scope(key string) string {
	sum := sha256.Sum256([]byte(key))
	return hex.EncodeToString(sum[:]) + ":"
}
func (p *Policy) remove(key string) {
	p.bytes -= len(p.entries[key].payload) + len(key)
	delete(p.entries, key)
}
func (p *Policy) sweep() {
	for k, e := range p.entries {
		if !p.now().Before(e.expires) {
			p.remove(k)
		}
	}
}
func (p *Policy) Sweep()            { p.mu.Lock(); defer p.mu.Unlock(); p.sweep() }
func (p *Policy) Stats() (int, int) { p.mu.Lock(); defer p.mu.Unlock(); return len(p.entries), p.bytes }
func (p *Policy) Purge(credential string) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.generation++
	prefix := scope(credential)
	for k := range p.entries {
		if len(k) >= len(prefix) && k[:len(prefix)] == prefix {
			p.remove(k)
		}
	}
}
func (p *Policy) get(key string) ([]byte, bool) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.sweep()
	e, ok := p.entries[key]
	return append([]byte(nil), e.payload...), ok
}
func (p *Policy) put(key string, data []byte, generation uint64) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.sweep()
	if generation != p.generation {
		return
	}
	if _, ok := p.entries[key]; ok {
		p.remove(key)
	}
	for len(p.entries) >= MaxEntries || p.bytes+len(data)+len(key) > MaxCacheBytes {
		var oldest string
		var ordinal uint64
		for k, e := range p.entries {
			if oldest == "" || e.order < ordinal {
				oldest, ordinal = k, e.order
			}
		}
		if oldest == "" {
			return
		}
		p.remove(oldest)
	}
	p.order++
	p.entries[key] = entry{append([]byte(nil), data...), p.now().Add(CacheTTL), p.order}
	p.bytes += len(data) + len(key)
}

// UpstreamCall supplies the global gate and per-call timeout to every actual read.
func (p *Policy) UpstreamCall(ctx context.Context, budget *Budget, cost int, call func(context.Context) error) error {
	select {
	case p.upstream <- struct{}{}:
	case <-ctx.Done():
		return &Fault{504}
	}
	defer func() { <-p.upstream }()
	if ctx.Err() != nil {
		return &Fault{504}
	}
	if !budget.Reserve(cost) {
		return &Fault{502}
	}
	callCtx, cancel := context.WithTimeout(ctx, CallTimeout)
	defer cancel()
	err := call(callCtx)
	if callCtx.Err() != nil {
		return &Fault{504}
	}
	return err
}

// Authorization runs before every cache lookup. Callbacks model documented API reads.
// Cross-request singleflight is deliberately deferred; no caller reuses another's auth.
func (p *Policy) Lookup(ctx context.Context, credential, query string,
	authorize func(context.Context) error, fetch func(context.Context, *Budget) ([]byte, error)) ([]byte, error) {
	if credential == "" {
		return nil, &Fault{401}
	}
	if query == "" || len(query) > 1024 {
		return nil, &Fault{400}
	}
	ctx, cancel := context.WithTimeout(ctx, Deadline)
	defer cancel()
	select {
	case p.active <- struct{}{}:
	default:
		return nil, &Fault{503}
	}
	defer func() { <-p.active }()
	budget := &Budget{}
	p.mu.Lock()
	generation := p.generation
	p.mu.Unlock()
	if err := p.UpstreamCall(ctx, budget, 1, authorize); err != nil {
		if f, ok := err.(*Fault); ok && (f.Status == 401 || f.Status == 403) {
			p.Purge(credential)
			return nil, &Fault{401}
		}
		return nil, err
	}
	if ctx.Err() != nil {
		return nil, &Fault{504}
	}
	cacheKey := scope(credential) + query
	if data, ok := p.get(cacheKey); ok {
		return data, nil
	}
	data, err := fetch(ctx, budget)
	if err != nil {
		if f, ok := err.(*Fault); ok && (f.Status == 401 || f.Status == 403) {
			p.Purge(credential)
			return nil, &Fault{401}
		}
		return nil, err
	}
	if ctx.Err() != nil {
		return nil, &Fault{504}
	}
	if len(data) > MaxResponseBytes {
		return nil, &Fault{502}
	}
	p.put(cacheKey, data, generation)
	return append([]byte(nil), data...), nil
}
