package provider

import (
	"encoding/json"
	"net/url"
	"regexp"
	"strings"
	"unicode/utf8"

	"abs-audiobookdb/internal/audiobookdb"
)

type Input struct{ Mode, Query, Author, Identifier string }

var asinPattern = regexp.MustCompile(`(?i)^[0-9A-Z]{10}$`)
var pastedASINPattern = regexp.MustCompile(`(?i)^B[0-9A-Z]{9}$`)
var isbnPattern = regexp.MustCompile(`^(?:[0-9]{9}[0-9Xx]|[0-9]{13})$`)

func normalize(s string) string { return strings.Join(strings.Fields(s), " ") }
func Parse(raw string) (Input, error) {
	var in Input
	bad := func() (Input, error) { return in, audiobookdb.Failure(400, "invalid_input") }
	if len(raw) > 4096 {
		return bad()
	}
	q, err := url.ParseQuery(raw)
	if err != nil {
		return bad()
	}
	for _, name := range []string{"query", "author", "mediaType", "asin", "isbn"} {
		if len(q[name]) > 1 {
			return bad()
		}
		if !utf8.ValidString(q.Get(name)) {
			return bad()
		}
	}
	in.Query, in.Author = normalize(q.Get("query")), normalize(q.Get("author"))
	if len(in.Query) > 512 || len(in.Author) > 512 {
		return bad()
	}
	if media := q.Get("mediaType"); media != "" && media != "book" {
		return bad()
	}
	asin, isbn := strings.TrimSpace(q.Get("asin")), strings.TrimSpace(q.Get("isbn"))
	if asin != "" && isbn != "" {
		return bad()
	}
	compact := strings.NewReplacer("-", "", " ", "").Replace(in.Query)
	if isbn != "" || isbnPattern.MatchString(compact) {
		return in, audiobookdb.Failure(400, "isbn_unsupported")
	}
	if asin != "" || pastedASINPattern.MatchString(in.Query) {
		if asin == "" {
			asin = in.Query
		}
		if !asinPattern.MatchString(asin) {
			return bad()
		}
		if in.Query != "" && pastedASINPattern.MatchString(in.Query) && !strings.EqualFold(in.Query, asin) {
			return bad()
		}
		in.Mode, in.Identifier = "asin", strings.ToUpper(asin)
		in.Query = ""
		in.Author = ""
		return in, nil
	}
	if utf8.RuneCountInString(in.Query) < 3 && in.Author == "" {
		return bad()
	}
	in.Mode = "title"
	return in, nil
}
func (i Input) Canonical() string { data, _ := json.Marshal(i); return string(data) }
