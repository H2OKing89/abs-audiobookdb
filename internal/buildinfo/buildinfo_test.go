package buildinfo

import (
	"encoding/json"
	"regexp"
	"testing"
)

func TestReleaseMetadata(t *testing.T) {
	if !regexp.MustCompile(`^\d+\.\d+\.\d+$`).MatchString(Current().Version) {
		t.Fatal("release version is not a three-component version")
	}
	previousRevision, previousDirty := revision, dirty
	defer func() { revision, dirty = previousRevision, previousDirty }()
	revision, dirty = "0123456789012345678901234567890123456789", "false"
	i := Current()
	if i.Revision != revision || i.Dirty != "false" {
		t.Fatal("injected release metadata was lost")
	}
	data, err := json.Marshal(i)
	if err != nil || !json.Valid(data) {
		t.Fatal("metadata is not valid JSON")
	}
}
