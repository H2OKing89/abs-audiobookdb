package provider

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"

	"abs-audiobookdb/internal/audiobookdb"
)

func TestInputRules(t *testing.T) {
	for _, raw := range []string{"query=Invented+Example&author=An+Author", "author=An+Author", "query=B000000001", "asin=B000000001", "query=ab&author=Someone"} {
		if _, err := Parse(raw); err != nil {
			t.Errorf("rejected %s", raw)
		}
	}
	for _, raw := range []string{"", "query=ab", "query=9780000000002", "isbn=9780000000002&query=Other", "asin=invalid", "asin=B000000001&isbn=9780000000002", "asin=B000000001&query=B000000002", "query=Valid&mediaType=podcast", "query=a&query=b", "query=%ff", "query=%zz", "query=" + strings.Repeat("a", 513)} {
		if _, err := Parse(raw); err == nil {
			t.Errorf("accepted %s", raw)
		}
	}
}
func TestFixtureMapping(t *testing.T) {
	raw, err := os.ReadFile("../../spikes/SPIKE-003/fixtures.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixtures struct {
		Cases []struct {
			Name  string `json:"name"`
			Input struct {
				Book     audiobookdb.Book      `json:"book"`
				Releases []audiobookdb.Release `json:"releases"`
			} `json:"input"`
		} `json:"cases"`
	}
	if err := json.Unmarshal(raw, &fixtures); err != nil {
		t.Fatal(err)
	}
	for _, tc := range fixtures.Cases {
		if tc.Input.Book.ID == "" {
			continue
		}
		for _, r := range tc.Input.Releases {
			m, err := mapRelease(tc.Input.Book, r)
			if err != nil {
				t.Fatal(err)
			}
			if m.Title == "" {
				t.Fatal("missing title")
			}
			switch tc.Name {
			case "known-title-author":
				var expected Match
				if err := json.Unmarshal([]byte(`{"title":"Invented Example","subtitle":"Synthetic subtitle","author":"Synthetic Author","narrator":"Narrator A","publisher":"Synthetic Publisher","language":"English","description":"Invented description for local fixture testing only.","isbn":"9780000000002","asin":"B000000001","publishedYear":"2026","duration":120,"cover":"https://assets.example.invalid/release-cover/large.jpg","genres":["Synthetic Genre"],"tags":["Synthetic Tag"]}`), &expected); err != nil {
					t.Fatal(err)
				}
				if !reflect.DeepEqual(m, expected) {
					t.Fatal("full metadata mismatch")
				}
			case "fractional-and-zero-series":
				if len(m.Series) != 2 || m.Series[0].Sequence != "0" || m.Series[1].Sequence != "0.5" {
					t.Fatal("series sequence")
				}
			case "multiple-authors-narrators":
				if m.Author != "Synthetic Author, Second Synthetic Author" || m.Narrator != "Narrator A, Second Synthetic Narrator" {
					t.Fatal("contributor ordering")
				}
			case "missing-cover-identifiers-runtime":
				if m.Duration != nil || m.ISBN != "" || m.Cover != "" || m.PublishedYear != "2026" {
					t.Fatal("missing values")
				}
			}
		}
	}
	book := fixtures.Cases[0].Input.Book
	r := fixtures.Cases[0].Input.Releases[0]
	book.Description = `<img src=x onerror="alert(1)">`
	r.Title = " "
	r.ReleaseDate = "invalid"
	m, err := mapRelease(book, r)
	if err != nil || strings.Contains(m.Description, "<") || m.Title != book.Title || m.PublishedYear != "2026" {
		t.Fatal("escaping and fallbacks")
	}
	r.Book = &audiobookdb.Summary{ID: "wrong"}
	if _, err := mapRelease(book, r); err == nil {
		t.Fatal("identity mismatch")
	}
}
func TestPipelineCacheAuthRoundRobinAndExact(t *testing.T) {
	t.Parallel()
	var mu sync.Mutex
	var paths []string
	rejected := false
	failDetail := false
	up := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		paths = append(paths, r.URL.Path)
		reject := rejected
		fail := failDetail
		mu.Unlock()
		if reject || r.Header.Get("X-API-Key") == "invalid" {
			w.WriteHeader(401)
			return
		}
		switch r.URL.Path {
		case "/auth/session":
			w.Write([]byte(`{"id":"invented"}`))
		case "/search":
			w.Write([]byte(`[{"id":"book1","title":"Invented","genres":["Synthetic Genre"],"tags":["Synthetic Tag"],"series":["Synthetic Series"]},{"id":"book2","title":"Invented"}]`))
		case "/books/book1":
			w.Write([]byte(`{"id":"book1","title":"Invented","releases":[{"id":"r1"},{"id":"r3"},{"id":"r5"},{"id":"r7"}]}`))
		case "/books/book2":
			w.Write([]byte(`{"id":"book2","title":"Invented","releases":[{"id":"r2"},{"id":"r4"},{"id":"r6"}]}`))
		case "/audiobooks/external/audible/B000000001":
			w.Write([]byte(`{"id":"book1","title":"Invented","matchedReleaseId":"r1"}`))
		case "/audiobooks/external/audible/B000000002":
			w.WriteHeader(404)
		default:
			if !strings.HasPrefix(r.URL.Path, "/releases/") {
				w.WriteHeader(404)
				return
			}
			if fail {
				w.WriteHeader(500)
				return
			}
			id := strings.TrimPrefix(r.URL.Path, "/releases/")
			book := "book1"
			if id == "r2" || id == "r4" || id == "r6" {
				book = "book2"
			}
			json.NewEncoder(w).Encode(map[string]any{"id": id, "title": "Invented", "book": map[string]string{"id": book}, "people": []map[string]any{{"role": map[string]string{"name": "Narrator"}, "person": map[string]string{"name": id}}}, "external": []map[string]any{{"category": map[string]string{"title": "Audible"}, "itemId": "B000000001"}}})
		}
	}))
	defer up.Close()
	client := audiobookdb.New(up.URL, "operator@example.invalid", up.Client().Transport)
	defer client.Close()
	p := New(client)
	in, _ := Parse("query=Invented")
	var cold []byte
	var wg sync.WaitGroup
	for _, key := range []string{"synthetic", "cold2", "cold3"} {
		wg.Add(1)
		go func() {
			defer wg.Done()
			data, err := p.Search(context.Background(), key, in)
			if err != nil {
				t.Errorf("concurrent cold search: %v", err)
				return
			}
			var result struct {
				Matches []Match `json:"matches"`
			}
			if err := json.Unmarshal(data, &result); err != nil || len(result.Matches) != 6 {
				t.Error("incomplete concurrent cold search")
			}
			if key == "synthetic" {
				cold = data
			}
		}()
	}
	wg.Wait()
	if t.Failed() {
		t.FailNow()
	}
	mu.Lock()
	coldCalls := len(paths)
	mu.Unlock()
	if coldCalls != 30 {
		t.Fatalf("three cold searches made %d calls, want 30", coldCalls)
	}
	var result struct {
		Matches []Match `json:"matches"`
	}
	json.Unmarshal(cold, &result)
	var narrators []string
	for _, m := range result.Matches {
		narrators = append(narrators, m.Narrator)
	}
	if !reflect.DeepEqual(narrators, []string{"r1", "r2", "r3", "r4", "r5", "r6"}) {
		t.Fatal("round-robin editions")
	}
	mu.Lock()
	before := len(paths)
	mu.Unlock()
	warm, err := p.Search(context.Background(), "synthetic", in)
	if err != nil || string(warm) != string(cold) {
		t.Fatal("warm result")
	}
	mu.Lock()
	if len(paths) != before+1 || paths[len(paths)-1] != "/auth/session" {
		t.Fatal("fresh-auth warm path")
	}
	rejected = true
	mu.Unlock()
	if _, err := p.Search(context.Background(), "synthetic", in); audiobookdb.AsFault(err).Status != 401 {
		t.Fatal("cached authorization bypass")
	}
	mu.Lock()
	rejected = false
	mu.Unlock()
	exact, _ := Parse("asin=B000000001")
	exactData, err := p.Search(context.Background(), "synthetic", exact)
	if err != nil {
		t.Fatal(err)
	}
	json.Unmarshal(exactData, &result)
	if len(result.Matches) != 1 || result.Matches[0].ASIN != "B000000001" {
		t.Fatal("exact identifier")
	}
	unknown, _ := Parse("asin=B000000002")
	data, err := p.Search(context.Background(), "synthetic", unknown)
	if err != nil || string(data) != `{"matches":[]}` {
		t.Fatal("unknown exact identifier")
	}
	mu.Lock()
	failDetail = true
	mu.Unlock()
	if _, err := p.Search(context.Background(), "other", in); audiobookdb.AsFault(err).Status != 502 {
		t.Fatal("silently incomplete result")
	}
}
func TestAdmissionAndCancellation(t *testing.T) {
	up := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() }))
	defer up.Close()
	client := audiobookdb.New(up.URL, "operator@example.invalid", up.Client().Transport)
	defer client.Close()
	p := New(client)
	for i := 0; i < 3; i++ {
		p.active <- struct{}{}
	}
	in, _ := Parse("query=Invented")
	if _, err := p.Search(context.Background(), "synthetic", in); audiobookdb.AsFault(err).Status != 503 {
		t.Fatal("admission cap")
	}
	for i := 0; i < 3; i++ {
		<-p.active
	}
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	before := time.Now()
	if _, err := p.Search(ctx, "synthetic", in); audiobookdb.AsFault(err).Status != 504 || time.Since(before) > 500*time.Millisecond {
		t.Fatal("cancellation")
	}
}

func TestExactIdentityFailures(t *testing.T) {
	for _, tc := range []struct {
		name, resolver, release string
		status                  int
	}{
		{"missing_matched_release", `{"id":"book","title":"Invented"}`, "", 502},
		{"wrong_release_identity", `{"id":"book","title":"Invented","matchedReleaseId":"release"}`, `{"id":"wrong","book":{"id":"book"},"title":"Invented"}`, 502},
		{"wrong_work_identity", `{"id":"book","title":"Invented","matchedReleaseId":"release"}`, `{"id":"release","book":{"id":"other"},"title":"Invented","external":[{"category":{"title":"Audible"},"itemId":"B000000001"}]}`, 502},
		{"wrong_asin", `{"id":"book","title":"Invented","matchedReleaseId":"release"}`, `{"id":"release","book":{"id":"book"},"title":"Invented","external":[{"category":{"title":"Audible"},"itemId":"B000000002"}]}`, 502},
	} {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			up := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				switch r.URL.Path {
				case "/auth/session":
					w.Write([]byte(`{"id":"invented"}`))
				case "/audiobooks/external/audible/B000000001":
					w.Write([]byte(tc.resolver))
				default:
					w.Write([]byte(tc.release))
				}
			}))
			defer up.Close()
			client := audiobookdb.New(up.URL, "operator@example.invalid", up.Client().Transport)
			defer client.Close()
			p := New(client)
			in, _ := Parse("asin=B000000001")
			if _, err := p.Search(context.Background(), "synthetic", in); err == nil || audiobookdb.AsFault(err).Status != tc.status {
				t.Fatal("invalid exact identity accepted")
			}
		})
	}
}
