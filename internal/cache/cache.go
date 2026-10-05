package cache

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"
	"sync"
	"time"
)

const MaxEntries = 64
const MaxBytes = 4 << 20
const TTL = 60 * time.Second

type entry struct {
	data    []byte
	expires time.Time
	order   uint64
}
type Cache struct {
	mu                sync.Mutex
	entries           map[string]entry
	bytes             int
	order, generation uint64
	now               func() time.Time
}

func New() *Cache { return &Cache{entries: make(map[string]entry), now: time.Now} }
func Scope(credential string) string {
	sum := sha256.Sum256([]byte(credential))
	return hex.EncodeToString(sum[:]) + ":"
}
func (c *Cache) remove(key string) {
	c.bytes -= len(key) + len(c.entries[key].data)
	delete(c.entries, key)
}
func (c *Cache) sweep() {
	for k, e := range c.entries {
		if !c.now().Before(e.expires) {
			c.remove(k)
		}
	}
}
func (c *Cache) Sweep()             { c.mu.Lock(); defer c.mu.Unlock(); c.sweep() }
func (c *Cache) Generation() uint64 { c.mu.Lock(); defer c.mu.Unlock(); return c.generation }
func (c *Cache) Purge(credential string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.generation++
	for k := range c.entries {
		if strings.HasPrefix(k, Scope(credential)) {
			c.remove(k)
		}
	}
}

// A rejection observed during older work prevents that work from refilling or
// reading a stale result. The global generation is deliberately conservative.
func (c *Cache) Get(key string, generation uint64) ([]byte, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.sweep()
	if generation != c.generation {
		return nil, false
	}
	e, ok := c.entries[key]
	return append([]byte(nil), e.data...), ok
}
func (c *Cache) Put(key string, data []byte, generation uint64) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.sweep()
	if generation != c.generation || len(data) > 1<<20 || len(data)+len(key) > MaxBytes {
		return
	}
	if _, ok := c.entries[key]; ok {
		c.remove(key)
	}
	for len(c.entries) >= MaxEntries || c.bytes+len(key)+len(data) > MaxBytes {
		oldest := ""
		var ordinal uint64
		for k, e := range c.entries {
			if oldest == "" || e.order < ordinal {
				oldest, ordinal = k, e.order
			}
		}
		c.remove(oldest)
	}
	c.order++
	c.entries[key] = entry{append([]byte(nil), data...), c.now().Add(TTL), c.order}
	c.bytes += len(key) + len(data)
}
