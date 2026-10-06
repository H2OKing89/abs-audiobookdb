package buildinfo

import (
	_ "embed"
	"runtime/debug"
	"strings"
)

//go:embed VERSION
var version string

// Release builds inject these values; ordinary Go builds use VCS metadata.
var revision = "unknown"
var dirty = "unknown"

type Info struct {
	Version  string `json:"version"`
	Revision string `json:"revision"`
	Dirty    string `json:"dirty"`
}

func Current() Info {
	i := Info{strings.TrimSpace(version), revision, dirty}
	if info, ok := debug.ReadBuildInfo(); ok {
		for _, setting := range info.Settings {
			if setting.Key == "vcs.revision" && i.Revision == "unknown" {
				i.Revision = setting.Value
			}
			if setting.Key == "vcs.modified" && i.Dirty == "unknown" {
				i.Dirty = setting.Value
			}
		}
	}
	return i
}
