package audiobookdb

import "encoding/json"

type Named struct {
	Name string `json:"name"`
}
type Titled struct {
	Title string `json:"title"`
}
type Image struct {
	URL string `json:"url"`
}
type Person struct {
	Person *Named `json:"person"`
	Role   *Named `json:"role"`
}
type Series struct {
	Series   *Titled `json:"series"`
	Position *struct {
		Label string `json:"label"`
	} `json:"position"`
	Ordinal json.RawMessage `json:"ordinal"`
}
type External struct {
	Category *Titled `json:"category"`
	ItemID   string  `json:"itemId"`
}
type Summary struct {
	ID string `json:"id"`
}

// Search hits have flattened genres/tags/series and are not detail Books.
// Only identity and title are used to select the subsequent detail reads.
type SearchHit struct {
	ID    string `json:"id"`
	Title string `json:"title"`
}
type Book struct {
	ID               string    `json:"id"`
	Title            string    `json:"title"`
	Subtitle         string    `json:"subtitle"`
	Description      string    `json:"description"`
	Copyright        *int64    `json:"copyright"`
	People           []Person  `json:"people"`
	CoverImage       *Image    `json:"coverImage"`
	Genres           []Titled  `json:"genres"`
	Tags             []Titled  `json:"tags"`
	Series           []Series  `json:"series"`
	Releases         []Summary `json:"releases"`
	MatchedReleaseID string    `json:"matchedReleaseId"`
}
type Release struct {
	ID          string     `json:"id"`
	Book        *Summary   `json:"book"`
	Title       string     `json:"title"`
	Subtitle    string     `json:"subtitle"`
	People      []Person   `json:"people"`
	Publisher   *Named     `json:"publisher"`
	Language    *Named     `json:"language"`
	ReleaseDate string     `json:"releaseDate"`
	ISBN        string     `json:"isbn"`
	Images      []Image    `json:"images"`
	External    []External `json:"external"`
	RuntimeMS   *int64     `json:"runtimeLengthMs"`
	RuntimeSec  *int64     `json:"runtimeLengthSec"`
}
