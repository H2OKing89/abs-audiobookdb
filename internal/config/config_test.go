package config

import (
	"path/filepath"
	"testing"
)

func TestRuntimeConfig(t *testing.T) {
	values := map[string]string{"AUDIOBOOKDB_CONTACT": "operator@example.invalid", "AUDIOBOOKSHELF_HOST": "ignored", "AUDIOBOOKSHELF_API_KEY": "ignored"}
	get := func(s string) string { return values[s] }
	c, err := Load(get)
	if err != nil || c.Listen != ":8080" || c.BaseURL != "https://audiobookdb.org/api" || c.APIKey != "" {
		t.Fatal("defaults or development isolation")
	}
	for _, input := range []struct{ name, value string }{{"AUDIOBOOKDB_CONTACT", ""}, {"AUDIOBOOKDB_CONTACT", "operator\r\n@example.invalid"}, {"AUDIOBOOKDB_BASE_URL", "http://example.invalid"}, {"AUDIOBOOKDB_BASE_URL", "https://user:password@example.invalid"}, {"TLS_CERT_FILE", "missing"}, {"AUDIOBOOKDB_API_KEY", "two words"}} {
		old := values[input.name]
		values[input.name] = input.value
		if _, err := Load(get); err == nil {
			t.Errorf("accepted invalid %s", input.name)
		}
		values[input.name] = old
	}
	missing := t.TempDir()
	values["TLS_CERT_FILE"] = filepath.Join(missing, "cert.pem")
	values["TLS_KEY_FILE"] = filepath.Join(missing, "key.pem")
	if _, err := Load(get); err == nil || err.Error() != "TLS file is unreadable" {
		t.Errorf("expected unreadable TLS files, got %v", err)
	}
	delete(values, "TLS_CERT_FILE")
	delete(values, "TLS_KEY_FILE")
}
