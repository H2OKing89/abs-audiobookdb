package provider

import (
	"context"
	"encoding/json"
	"sort"
	"strings"
	"time"

	"abs-audiobookdb/internal/audiobookdb"
	"abs-audiobookdb/internal/cache"
)

type Provider struct {
	Client *audiobookdb.Client
	Cache  *cache.Cache
	active chan struct{}
}

func New(client *audiobookdb.Client) *Provider {
	return &Provider{Client: client, Cache: cache.New(), active: make(chan struct{}, 3)}
}
func (p *Provider) Sweep(ctx context.Context) {
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			p.Cache.Sweep()
		}
	}
}
func (p *Provider) Search(ctx context.Context, key string, in Input) ([]byte, error) {
	ctx, cancel := context.WithTimeout(ctx, audiobookdb.Deadline)
	defer cancel()
	select {
	case p.active <- struct{}{}:
	default:
		return nil, audiobookdb.Failure(503, "overloaded")
	}
	defer func() { <-p.active }()
	budget := &audiobookdb.Budget{}
	generation := p.Cache.Generation()
	fail := func(err error) ([]byte, error) {
		f := audiobookdb.AsFault(err)
		if f.Status == 401 {
			p.Cache.Purge(key)
		}
		if f.Status == 404 {
			f = audiobookdb.Failure(502, "upstream_unavailable")
		}
		return nil, f
	}
	if err := p.Client.Authorize(ctx, budget, key); err != nil {
		return fail(err)
	}
	if ctx.Err() != nil {
		return nil, audiobookdb.Failure(504, "deadline")
	}
	cacheKey := cache.Scope(key) + in.Canonical()
	if data, ok := p.Cache.Get(cacheKey, generation); ok {
		return data, nil
	}
	var matches []Match
	var err error
	if in.Mode == "asin" {
		matches, err = p.exact(ctx, budget, key, in.Identifier)
	} else {
		matches, err = p.title(ctx, budget, key, in)
	}
	if err != nil {
		return fail(err)
	}
	if ctx.Err() != nil {
		return nil, audiobookdb.Failure(504, "deadline")
	}
	if matches == nil {
		matches = []Match{}
	}
	data, err := json.Marshal(struct {
		Matches []Match `json:"matches"`
	}{matches})
	if err != nil || len(data) > audiobookdb.MaxResponse {
		return nil, audiobookdb.Failure(502, "upstream_size")
	}
	p.Cache.Put(cacheKey, data, generation)
	return data, nil
}
func (p *Provider) exact(ctx context.Context, b *audiobookdb.Budget, key, asin string) ([]Match, error) {
	book, err := p.Client.Resolve(ctx, b, key, asin)
	if err != nil {
		if audiobookdb.AsFault(err).Status == 404 {
			return []Match{}, nil
		}
		return nil, err
	}
	release, err := p.Client.Release(ctx, b, key, book.MatchedReleaseID)
	if err != nil {
		return nil, err
	}
	valid := false
	for _, e := range release.External {
		if e.Category != nil && strings.EqualFold(e.Category.Title, "audible") && strings.EqualFold(e.ItemID, asin) {
			valid = true
			break
		}
	}
	if !valid {
		return nil, audiobookdb.Failure(502, "upstream_identity")
	}
	match, err := mapRelease(book, release)
	if err != nil {
		return nil, err
	}
	match.ASIN = asin
	return []Match{match}, nil
}
func (p *Provider) title(ctx context.Context, b *audiobookdb.Budget, key string, in Input) ([]Match, error) {
	hits, err := p.Client.Search(ctx, b, key, in.Query, in.Author)
	if err != nil {
		return nil, err
	}
	sort.SliceStable(hits, func(i, j int) bool {
		return strings.EqualFold(normalize(hits[i].Title), in.Query) && !strings.EqualFold(normalize(hits[j].Title), in.Query)
	})
	var books []audiobookdb.Book
	seenBooks := map[string]bool{}
	for _, hit := range hits {
		if seenBooks[hit.ID] {
			continue
		}
		seenBooks[hit.ID] = true
		book, err := p.Client.Book(ctx, b, key, hit.ID)
		if err != nil {
			return nil, err
		}
		books = append(books, book)
		if len(books) == 2 {
			break
		}
	}
	type finalist struct {
		book int
		id   string
	}
	var selected []finalist
	seen := map[string]bool{}
	for index := 0; len(selected) < 6; index++ {
		any := false
		for i, book := range books {
			if index >= len(book.Releases) {
				continue
			}
			any = true
			id := book.Releases[index].ID
			if !audiobookdb.ValidID(id) {
				return nil, audiobookdb.Failure(502, "upstream_schema")
			}
			if !seen[id] {
				selected = append(selected, finalist{i, id})
				seen[id] = true
			}
			if len(selected) == 6 {
				break
			}
		}
		if !any {
			break
		}
	}
	var out []Match
	for _, s := range selected {
		r, err := p.Client.Release(ctx, b, key, s.id)
		if err != nil {
			return nil, err
		}
		match, err := mapRelease(books[s.book], r)
		if err != nil {
			return nil, err
		}
		out = append(out, match)
	}
	sort.SliceStable(out, func(i, j int) bool {
		return strings.EqualFold(normalize(out[i].Title), in.Query) && !strings.EqualFold(normalize(out[j].Title), in.Query)
	})
	return out, nil
}
