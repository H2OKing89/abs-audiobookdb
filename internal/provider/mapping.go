package provider

import (
	"encoding/json"
	"html"
	"net/url"
	"strconv"
	"strings"
	"time"

	"abs-audiobookdb/internal/audiobookdb"
)

type Series struct {
	Name     string `json:"series"`
	Sequence string `json:"sequence,omitempty"`
}
type Match struct {
	Title         string   `json:"title"`
	Subtitle      string   `json:"subtitle,omitempty"`
	Author        string   `json:"author,omitempty"`
	Narrator      string   `json:"narrator,omitempty"`
	Publisher     string   `json:"publisher,omitempty"`
	Language      string   `json:"language,omitempty"`
	PublishedYear string   `json:"publishedYear,omitempty"`
	Description   string   `json:"description,omitempty"`
	Cover         string   `json:"cover,omitempty"`
	ISBN          string   `json:"isbn,omitempty"`
	ASIN          string   `json:"asin,omitempty"`
	Genres        []string `json:"genres,omitempty"`
	Tags          []string `json:"tags,omitempty"`
	Series        []Series `json:"series,omitempty"`
	Duration      *int64   `json:"duration,omitempty"`
}

func pick(a, b string) string {
	if strings.TrimSpace(a) != "" {
		return a
	}
	return b
}
func names(edges []audiobookdb.Person, role string) string {
	seen := map[string]bool{}
	var out []string
	for _, e := range edges {
		if e.Role == nil || e.Person == nil || e.Role.Name != role {
			continue
		}
		name := e.Person.Name
		if strings.TrimSpace(name) != "" && !seen[name] {
			out = append(out, name)
			seen[name] = true
		}
	}
	return strings.Join(out, ", ")
}
func titles(items []audiobookdb.Titled) []string {
	seen := map[string]bool{}
	var out []string
	for _, i := range items {
		if strings.TrimSpace(i.Title) != "" && !seen[i.Title] {
			out = append(out, i.Title)
			seen[i.Title] = true
		}
	}
	return out
}
func cover(image *audiobookdb.Image) string {
	if image == nil {
		return ""
	}
	u, err := url.Parse(image.URL)
	if err != nil || u.Scheme != "https" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" {
		return ""
	}
	return strings.TrimRight(image.URL, "/") + "/large.jpg"
}
func mapRelease(book audiobookdb.Book, release audiobookdb.Release) (Match, error) {
	if release.Book == nil || release.Book.ID != book.ID {
		return Match{}, audiobookdb.Failure(502, "upstream_identity")
	}
	out := Match{Title: pick(release.Title, book.Title), Subtitle: pick(release.Subtitle, book.Subtitle), Author: names(book.People, "Author"), Narrator: names(release.People, "Narrator"), ISBN: release.ISBN, Genres: titles(book.Genres), Tags: titles(book.Tags)}
	if strings.TrimSpace(out.Title) == "" {
		return out, audiobookdb.Failure(502, "upstream_schema")
	}
	// ABS renders descriptions as HTML. Escaping preserves text and prevents
	// upstream markup from becoming executable content in the reader's browser.
	out.Description = html.EscapeString(book.Description)
	if release.Publisher != nil {
		out.Publisher = release.Publisher.Name
	}
	if release.Language != nil {
		out.Language = release.Language.Name
	}
	date, err := time.Parse(time.RFC3339, release.ReleaseDate)
	if err != nil {
		date, err = time.Parse("2006-01-02", release.ReleaseDate)
	}
	if err == nil && date.Year() > 0 {
		out.PublishedYear = strconv.Itoa(date.Year())
	} else if book.Copyright != nil && *book.Copyright >= 1 && *book.Copyright <= 9999 {
		out.PublishedYear = strconv.FormatInt(*book.Copyright, 10)
	}
	for _, image := range release.Images {
		out.Cover = cover(&image)
		if out.Cover != "" {
			break
		}
	}
	if out.Cover == "" {
		out.Cover = cover(book.CoverImage)
	}
	if release.RuntimeMS != nil && *release.RuntimeMS >= 0 {
		n := *release.RuntimeMS / 60000
		out.Duration = &n
	} else if release.RuntimeSec != nil && *release.RuntimeSec >= 0 {
		n := *release.RuntimeSec / 60
		out.Duration = &n
	}
	for _, e := range release.External {
		if e.Category != nil && strings.EqualFold(e.Category.Title, "audible") && asinPattern.MatchString(e.ItemID) {
			out.ASIN = strings.ToUpper(e.ItemID)
			break
		}
	}
	for _, s := range book.Series {
		if s.Series == nil || strings.TrimSpace(s.Series.Title) == "" {
			continue
		}
		item := Series{Name: s.Series.Title}
		if s.Position != nil {
			item.Sequence = s.Position.Label
		}
		if strings.TrimSpace(item.Sequence) == "" && len(s.Ordinal) > 0 && string(s.Ordinal) != "null" {
			var label string
			if json.Unmarshal(s.Ordinal, &label) == nil {
				item.Sequence = label
			} else {
				var n json.Number
				if json.Unmarshal(s.Ordinal, &n) == nil {
					if _, err := n.Float64(); err == nil {
						item.Sequence = n.String()
					}
				}
			}
		}
		out.Series = append(out.Series, item)
	}
	return out, nil
}
