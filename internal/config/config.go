package config

import (
	"errors"
	"net"
	"net/mail"
	"net/url"
	"os"
	"strings"
	"unicode"
)

type Config struct {
	Listen, BaseURL, Contact, APIKey, CertFile, KeyFile, HealthCA string
}

// Load reads process configuration only. Development dotenv and ABS credentials
// are deliberately outside the adapter's runtime configuration.
func Load(get func(string) string) (Config, error) {
	c := Config{Listen: get("LISTEN_ADDR"), BaseURL: get("AUDIOBOOKDB_BASE_URL"), Contact: get("AUDIOBOOKDB_CONTACT"), APIKey: get("AUDIOBOOKDB_API_KEY"), CertFile: get("TLS_CERT_FILE"), KeyFile: get("TLS_KEY_FILE"), HealthCA: get("HEALTH_CA_FILE")}
	if c.Listen == "" {
		c.Listen = ":8080"
	}
	if c.BaseURL == "" {
		c.BaseURL = "https://audiobookdb.org/api"
	}
	if _, _, err := net.SplitHostPort(c.Listen); err != nil {
		return c, errors.New("invalid listen address")
	}
	u, err := url.Parse(c.BaseURL)
	if err != nil || u.Scheme != "https" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" {
		return c, errors.New("upstream requires an HTTPS base URL")
	}
	c.BaseURL = strings.TrimRight(c.BaseURL, "/")
	if c.Contact == "" || len(c.Contact) > 254 || strings.IndexFunc(c.Contact, func(r rune) bool { return unicode.IsSpace(r) || unicode.IsControl(r) || r == '(' || r == ')' }) >= 0 {
		return c, errors.New("operator contact is required")
	}
	contactURL, _ := url.Parse(c.Contact)
	address, emailErr := mail.ParseAddress(c.Contact)
	validEmail := emailErr == nil && address.Address == c.Contact && address.Name == ""
	if !validEmail && (contactURL == nil || contactURL.Scheme != "https" || contactURL.Hostname() == "" || contactURL.User != nil) {
		return c, errors.New("contact must be an email or public HTTPS URL")
	}
	if !ValidKey(c.APIKey) && c.APIKey != "" {
		return c, errors.New("invalid fallback key")
	}
	if (c.CertFile == "") != (c.KeyFile == "") {
		return c, errors.New("both TLS certificate and key are required")
	}
	for _, path := range []string{c.CertFile, c.KeyFile, c.HealthCA} {
		if path == "" {
			continue
		}
		f, err := os.Open(path)
		if err != nil {
			return c, errors.New("TLS file is unreadable")
		}
		f.Close()
	}
	return c, nil
}

func ValidKey(key string) bool {
	return key != "" && len(key) <= 4096 && strings.IndexFunc(key, func(r rune) bool { return r <= 32 || r >= 127 }) < 0
}
