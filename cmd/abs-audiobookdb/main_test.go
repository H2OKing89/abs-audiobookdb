package main

import (
	"encoding/pem"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestHealthTrustAndStatus(t *testing.T) {
	status := 200
	up := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/health" {
			t.Error("wrong health path")
		}
		w.WriteHeader(status)
	}))
	defer up.Close()
	cert := filepath.Join(t.TempDir(), "ca.crt")
	if err := os.WriteFile(cert, pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: up.Certificate().Raw}), 0600); err != nil {
		t.Fatal(err)
	}
	values := map[string]string{"LISTEN_ADDR": strings.TrimPrefix(up.URL, "https://"), "TLS_CERT_FILE": "configured"}
	get := func(s string) string { return values[s] }
	if err := health(get); err == nil {
		t.Fatal("untrusted certificate accepted")
	}
	values["HEALTH_CA_FILE"] = cert
	if err := health(get); err != nil {
		t.Fatal(err)
	}
	status = 503
	if err := health(get); err == nil {
		t.Fatal("unhealthy status accepted")
	}
	values["LISTEN_ADDR"] = strings.Replace(values["LISTEN_ADDR"], "127.0.0.1", "localhost", 1)
	status = 200
	if err := health(get); err == nil {
		t.Fatal("SAN mismatch accepted")
	}
}
