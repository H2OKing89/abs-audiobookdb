package audiobookdb

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"abs-audiobookdb/internal/buildinfo"
	"abs-audiobookdb/internal/cache"
)

const Deadline = 8 * time.Second
const CallTimeout = 2 * time.Second
const MaxAttempts = 10
const MaxCost = 12
const MaxBytes = 8 << 20
const MaxResponse = 1 << 20

type Fault struct {
	Status     int
	Code       string
	RetryAfter int
}

func (f *Fault) Error() string               { return f.Code }
func Failure(status int, code string) *Fault { return &Fault{Status: status, Code: code} }

type Budget struct {
	mu                    sync.Mutex
	attempts, cost, bytes int
}

func (b *Budget) reserve(cost int) bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	if cost < 1 || b.attempts >= MaxAttempts || b.cost+cost > MaxCost {
		return false
	}
	b.attempts++
	b.cost += cost
	return true
}
func (b *Budget) consume(size int) bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.bytes += size
	return b.bytes <= MaxBytes
}
func (b *Budget) Counts() (int, int) { b.mu.Lock(); defer b.mu.Unlock(); return b.attempts, b.cost }

type Client struct {
	base, agent string
	http        *http.Client
	gate        chan struct{}
	mu          sync.Mutex
	next        time.Time
	waiters     []*pacingWaiter
	cooldowns   map[string]time.Time
	now         func() time.Time
}

type pacingWaiter struct{ ready chan struct{} }

func New(base, contact string, transport http.RoundTripper) *Client {
	if transport == nil {
		t := http.DefaultTransport.(*http.Transport).Clone()
		t.Proxy = nil
		t.MaxConnsPerHost = 4
		t.MaxIdleConnsPerHost = 4
		t.ResponseHeaderTimeout = CallTimeout
		transport = t
	}
	return &Client{base: strings.TrimRight(base, "/"), agent: "abs-audiobookdb/" + buildinfo.Current().Version + " (" + contact + ")", http: &http.Client{Transport: transport, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}, gate: make(chan struct{}, 4), cooldowns: map[string]time.Time{}, now: time.Now}
}
func (c *Client) Close() { c.http.CloseIdleConnections() }
func (c *Client) cooldown(key string) int {
	c.mu.Lock()
	defer c.mu.Unlock()
	now := c.now()
	for k, t := range c.cooldowns {
		if !now.Before(t) {
			delete(c.cooldowns, k)
		}
	}
	if t, ok := c.cooldowns[cache.Scope(key)]; ok {
		return int((t.Sub(now) + time.Second - 1) / time.Second)
	}
	return 0
}
func (c *Client) backoff(key string, seconds int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if len(c.cooldowns) >= 128 {
		var oldest string
		var expiry time.Time
		for k, t := range c.cooldowns {
			if oldest == "" || t.Before(expiry) {
				oldest, expiry = k, t
			}
		}
		delete(c.cooldowns, oldest)
	}
	c.cooldowns[cache.Scope(key)] = c.now().Add(time.Duration(seconds) * time.Second)
}
func (c *Client) pace(ctx context.Context) error {
	// Keep waiters in arrival order. Competing timers let fresh warm requests
	// repeatedly take the next slot while older cold detail reads starved.
	waiter := &pacingWaiter{ready: make(chan struct{})}
	c.mu.Lock()
	c.waiters = append(c.waiters, waiter)
	if len(c.waiters) == 1 {
		close(waiter.ready)
	}
	c.mu.Unlock()
	defer func() {
		c.mu.Lock()
		defer c.mu.Unlock()
		for i, queued := range c.waiters {
			if queued != waiter {
				continue
			}
			copy(c.waiters[i:], c.waiters[i+1:])
			c.waiters[len(c.waiters)-1] = nil
			c.waiters = c.waiters[:len(c.waiters)-1]
			if i == 0 && len(c.waiters) > 0 {
				close(c.waiters[0].ready)
			}
			break
		}
	}()
	select {
	case <-ctx.Done():
		return Failure(504, "deadline")
	case <-waiter.ready:
	}
	c.mu.Lock()
	delay := c.next.Sub(c.now())
	c.mu.Unlock()
	if delay > 0 {
		timer := time.NewTimer(delay)
		defer timer.Stop()
		select {
		case <-ctx.Done():
			return Failure(504, "deadline")
		case <-timer.C:
		}
	}
	if ctx.Err() != nil {
		return Failure(504, "deadline")
	}
	c.mu.Lock()
	c.next = c.now().Add(time.Second / 4)
	c.mu.Unlock()
	return nil
}
func (c *Client) read(ctx context.Context, b *Budget, key, method, path string, body any, limit, cost int, output any) error {
	if retry := c.cooldown(key); retry > 0 {
		return &Fault{503, "rate_limited", retry}
	}
	select {
	case c.gate <- struct{}{}:
	case <-ctx.Done():
		return Failure(504, "deadline")
	}
	defer func() { <-c.gate }()
	if err := c.pace(ctx); err != nil {
		return err
	}
	if retry := c.cooldown(key); retry > 0 {
		return &Fault{503, "rate_limited", retry}
	}
	if ctx.Err() != nil {
		return Failure(504, "deadline")
	}
	if !b.reserve(cost) {
		return Failure(502, "budget_exhausted")
	}
	callCtx, cancel := context.WithTimeout(ctx, CallTimeout)
	defer cancel()
	var input io.Reader
	if body != nil {
		data, err := json.Marshal(body)
		if err != nil {
			return Failure(502, "upstream_schema")
		}
		input = bytes.NewReader(data)
	}
	req, err := http.NewRequestWithContext(callCtx, method, c.base+path, input)
	if err != nil {
		return Failure(502, "upstream_unavailable")
	}
	req.Header.Set("X-API-Key", key)
	req.Header.Set("User-Agent", c.agent)
	req.Header.Set("Accept", "application/json")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := c.http.Do(req)
	if err != nil {
		if callCtx.Err() != nil {
			return Failure(504, "deadline")
		}
		return Failure(502, "upstream_unavailable")
	}
	defer resp.Body.Close()
	if resp.StatusCode == 401 || resp.StatusCode == 403 {
		return Failure(401, "unauthorized")
	}
	if resp.StatusCode == 429 {
		seconds := retryAfter(resp.Header.Get("Retry-After"), c.now())
		c.backoff(key, seconds)
		return &Fault{503, "rate_limited", seconds}
	}
	if resp.StatusCode == 404 {
		return Failure(404, "not_found")
	}
	if resp.StatusCode != 200 {
		return Failure(502, "upstream_unavailable")
	}
	data, err := io.ReadAll(io.LimitReader(resp.Body, int64(limit+1)))
	if callCtx.Err() != nil {
		return Failure(504, "deadline")
	}
	if err != nil || len(data) > limit || !b.consume(len(data)) {
		return Failure(502, "upstream_size")
	}
	if bytes.Equal(bytes.TrimSpace(data), []byte("null")) {
		return Failure(502, "upstream_schema")
	}
	if err := json.Unmarshal(data, output); err != nil {
		return Failure(502, "upstream_schema")
	}
	return nil
}

// Retry-After accepts delay seconds and HTTP dates. Keep the existing bounded
// cooldown policy and round future dates upward so callers do not retry early.
func retryAfter(value string, now time.Time) int {
	value = strings.TrimSpace(value)
	if value != "" && strings.IndexFunc(value, func(r rune) bool { return r < '0' || r > '9' }) < 0 {
		n, err := strconv.ParseUint(value, 10, 64)
		if err != nil || n > 300 {
			return 300
		}
		if n == 0 {
			return 1
		}
		return int(n)
	}
	date, err := http.ParseTime(value)
	if err != nil || !date.After(now) {
		return 1
	}
	delay := date.Sub(now)
	if delay >= 300*time.Second {
		return 300
	}
	return int((delay + time.Second - 1) / time.Second)
}

var validID = regexp.MustCompile(`^[A-Za-z0-9_-]{1,128}$`)

func ValidID(id string) bool { return validID.MatchString(id) }
func (c *Client) Authorize(ctx context.Context, b *Budget, key string) error {
	var session struct {
		ID string `json:"id"`
	}
	if err := c.read(ctx, b, key, "GET", "/auth/session", nil, 64<<10, 1, &session); err != nil {
		return err
	}
	if strings.TrimSpace(session.ID) == "" {
		return Failure(502, "upstream_schema")
	}
	return nil
}
func (c *Client) Search(ctx context.Context, b *Budget, key, query, author string) ([]SearchHit, error) {
	body := map[string]any{"q": query, "type": "books"}
	if author != "" {
		body["filters"] = map[string]string{"person": author, "role": "Author"}
	}
	var out []SearchHit
	err := c.read(ctx, b, key, "POST", "/search", body, MaxResponse, 3, &out)
	if err != nil {
		return nil, err
	}
	if out == nil || len(out) > 10 {
		return nil, Failure(502, "upstream_schema")
	}
	for _, v := range out {
		if !ValidID(v.ID) || strings.TrimSpace(v.Title) == "" {
			return nil, Failure(502, "upstream_schema")
		}
	}
	return out, nil
}
func (c *Client) Book(ctx context.Context, b *Budget, key, id string) (Book, error) {
	var out Book
	if !ValidID(id) {
		return out, Failure(502, "upstream_schema")
	}
	err := c.read(ctx, b, key, "GET", "/books/"+id, nil, MaxResponse, 1, &out)
	if err == nil && (out.ID != id || strings.TrimSpace(out.Title) == "") {
		err = Failure(502, "upstream_schema")
	}
	return out, err
}
func (c *Client) Release(ctx context.Context, b *Budget, key, id string) (Release, error) {
	var out Release
	if !ValidID(id) {
		return out, Failure(502, "upstream_schema")
	}
	err := c.read(ctx, b, key, "GET", "/releases/"+id, nil, MaxResponse, 1, &out)
	if err == nil && (out.ID != id || out.Book == nil || !ValidID(out.Book.ID)) {
		err = Failure(502, "upstream_schema")
	}
	return out, err
}
func (c *Client) Resolve(ctx context.Context, b *Budget, key, asin string) (Book, error) {
	var out Book
	err := c.read(ctx, b, key, "GET", "/audiobooks/external/audible/"+asin, nil, MaxResponse, 1, &out)
	if err == nil && (!ValidID(out.ID) || strings.TrimSpace(out.Title) == "" || !ValidID(out.MatchedReleaseID)) {
		err = Failure(502, "upstream_schema")
	}
	return out, err
}
func AsFault(err error) *Fault {
	var f *Fault
	if errors.As(err, &f) {
		return f
	}
	return Failure(502, "upstream_unavailable")
}
