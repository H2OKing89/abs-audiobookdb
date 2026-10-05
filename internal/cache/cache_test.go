package cache

import (
	"bytes"
	"fmt"
	"sync"
	"testing"
	"time"
)

func TestBoundsExpiryIsolationGeneration(t *testing.T) {
	c := New()
	now := time.Now()
	c.now = func() time.Time { return now }
	a, b := Scope("fixture-a"), Scope("fixture-b")
	g := c.Generation()
	c.Put(a+"title", []byte("first"), g)
	out, ok := c.Get(a+"title", g)
	if !ok {
		t.Fatal("missing result")
	}
	out[0] = 'x'
	again, _ := c.Get(a+"title", g)
	if string(again) != "first" {
		t.Fatal("mutable cache")
	}
	if _, ok := c.Get(b+"title", g); ok {
		t.Fatal("credential leakage")
	}
	for i := 0; i < 100; i++ {
		c.Put(a+fmt.Sprint(i), bytes.Repeat([]byte{'z'}, 100000), g)
	}
	if len(c.entries) > MaxEntries || c.bytes > MaxBytes {
		t.Fatal("unbounded cache")
	}
	c.Purge("fixture-a")
	c.Put(a+"old", []byte("old"), g)
	if len(c.entries) != 0 {
		t.Fatal("old work refilled rejected scope")
	}
	g = c.Generation()
	for i := 0; i < 100; i++ {
		c.Put(b+fmt.Sprint(i), []byte("small"), g)
	}
	if len(c.entries) != MaxEntries {
		t.Fatal("entry cap")
	}
	now = now.Add(TTL)
	c.Sweep()
	if len(c.entries) != 0 || c.bytes != 0 {
		t.Fatal("expiry")
	}
}
func TestParallelScopes(t *testing.T) {
	c := New()
	g := c.Generation()
	var wg sync.WaitGroup
	for i := 0; i < 32; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			key := Scope(fmt.Sprint(i)) + "query"
			want := []byte(fmt.Sprint(i))
			c.Put(key, want, g)
			got, ok := c.Get(key, g)
			if !ok || !bytes.Equal(got, want) {
				t.Error("scope mismatch")
			}
		}(i)
	}
	wg.Wait()
}
