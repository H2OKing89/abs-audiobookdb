// Package bounds is an isolated design experiment, not production adapter code.
package bounds

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"sync"
	"sync/atomic"
	"time"
)

type Fault struct{ Status int }

func (f *Fault) Error() string { return http.StatusText(f.Status) }

type entry struct {
	data    []string
	expires time.Time
}
type flight struct {
	done    chan struct{}
	cancel  context.CancelFunc
	waiters int
	data    []string
	err     error
}
type Client struct {
	Base    string
	HTTP    *http.Client
	mu      sync.Mutex
	cache   map[string]entry
	flights map[string]*flight
	gate    chan struct{}
}

func New(base string) *Client {
	return &Client{Base: base, HTTP: &http.Client{Timeout: 2 * time.Second}, cache: map[string]entry{}, flights: map[string]*flight{}, gate: make(chan struct{}, 4)}
}
func scope(key string) string { sum := sha256.Sum256([]byte(key)); return hex.EncodeToString(sum[:]) }
func (c *Client) invalidate(key string) {
	prefix := scope(key) + ":"
	c.mu.Lock()
	defer c.mu.Unlock()
	for k := range c.cache {
		if len(k) >= len(prefix) && k[:len(prefix)] == prefix {
			delete(c.cache, k)
		}
	}
}

func (c *Client) get(ctx context.Context, key, route string, budget *atomic.Int32) ([]byte, error) {
	for attempt := 0; attempt < 2; attempt++ {
		if budget.Add(1) > 10 {
			return nil, &Fault{502}
		}
		select {
		case c.gate <- struct{}{}:
		case <-ctx.Done():
			return nil, &Fault{504}
		}
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.Base+route, nil)
		if err != nil {
			<-c.gate
			return nil, &Fault{502}
		}
		req.Header.Set("Authorization", key)
		res, err := c.HTTP.Do(req)
		if err != nil {
			<-c.gate
			if ctx.Err() != nil {
				return nil, &Fault{504}
			}
			return nil, &Fault{502}
		}
		raw, readErr := io.ReadAll(io.LimitReader(res.Body, (1<<20)+1))
		res.Body.Close()
		<-c.gate
		if readErr != nil || len(raw) > 1<<20 {
			return nil, &Fault{502}
		}
		if res.StatusCode == 429 && attempt == 0 {
			seconds, err := strconv.Atoi(res.Header.Get("Retry-After"))
			if err != nil || seconds < 0 || seconds > 1 {
				return nil, &Fault{503}
			}
			timer := time.NewTimer(time.Duration(seconds) * time.Second)
			select {
			case <-timer.C:
				continue
			case <-ctx.Done():
				timer.Stop()
				return nil, &Fault{504}
			}
		}
		switch res.StatusCode {
		case 200:
			return raw, nil
		case 401, 403:
			c.invalidate(key)
			return nil, &Fault{401}
		case 404:
			return nil, &Fault{404}
		case 429:
			return nil, &Fault{503}
		default:
			return nil, &Fault{502}
		}
	}
	return nil, &Fault{503}
}

func (c *Client) work(ctx context.Context, key, query string) ([]string, error) {
	var budget atomic.Int32
	raw, err := c.get(ctx, key, "/lookup?q="+url.QueryEscape(query), &budget)
	if err != nil {
		var f *Fault
		if errors.As(err, &f) && f.Status == 404 {
			return []string{}, nil
		}
		return nil, err
	}
	var ids []int
	if json.Unmarshal(raw, &ids) != nil || len(ids) > 4 {
		return nil, &Fault{502}
	}
	result := make([]string, len(ids))
	errs := make(chan error, len(ids))
	var wg sync.WaitGroup
	for index, id := range ids {
		wg.Add(1)
		go func(i, id int) {
			defer wg.Done()
			raw, err := c.get(ctx, key, "/detail?id="+strconv.Itoa(id), &budget)
			if err != nil {
				errs <- err
				return
			}
			if json.Unmarshal(raw, &result[i]) != nil {
				errs <- &Fault{502}
			}
		}(index, id)
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		return nil, err
	}
	return result, nil
}

func (c *Client) Search(ctx context.Context, key, query string) ([]string, error) {
	if key == "" {
		return nil, &Fault{401}
	}
	if query == "" {
		return nil, &Fault{400}
	}
	// Fresh authorization is deliberately modeled before every cache hit. The
	// fixture's /validate route is synthetic; no equivalent upstream route is assumed.
	var authBudget atomic.Int32
	if _, err := c.get(ctx, key, "/validate", &authBudget); err != nil {
		return nil, err
	}
	cacheKey := scope(key) + ":" + query
	c.mu.Lock()
	if hit, okay := c.cache[cacheKey]; okay && time.Now().Before(hit.expires) {
		data := append([]string{}, hit.data...)
		c.mu.Unlock()
		return data, nil
	}
	f, okay := c.flights[cacheKey]
	if !okay {
		workCtx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		f = &flight{done: make(chan struct{}), cancel: cancel}
		c.flights[cacheKey] = f
		go func() {
			data, err := c.work(workCtx, key, query)
			c.mu.Lock()
			f.data, f.err = data, err
			if err == nil && workCtx.Err() == nil {
				if len(c.cache) >= 4 {
					var oldest string
					var oldestTime time.Time
					for k, e := range c.cache {
						if oldest == "" || e.expires.Before(oldestTime) {
							oldest, oldestTime = k, e.expires
						}
					}
					delete(c.cache, oldest)
				}
				c.cache[cacheKey] = entry{append([]string{}, data...), time.Now().Add(time.Second)}
			}
			delete(c.flights, cacheKey)
			close(f.done)
			c.mu.Unlock()
			cancel()
		}()
	}
	f.waiters++
	c.mu.Unlock()
	defer func() {
		c.mu.Lock()
		f.waiters--
		if f.waiters == 0 {
			f.cancel()
		}
		c.mu.Unlock()
	}()
	select {
	case <-ctx.Done():
		return nil, &Fault{504}
	case <-f.done:
		return append([]string{}, f.data...), f.err
	}
}
