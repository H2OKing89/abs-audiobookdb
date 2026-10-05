// Disposable deployment fixture; this is not a metadata adapter.
package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	listen := flag.String("listen", ":8080", "local listen address")
	cert := flag.String("cert", "", "synthetic certificate")
	key := flag.String("key", "", "synthetic private key")
	upstream := flag.String("upstream", "", "local HTTP fixture for TLS termination")
	probe := flag.String("probe", "", "health URL")
	ca := flag.String("ca", "", "synthetic trusted CA")
	flag.Parse()
	if *probe != "" {
		probeHealth(*probe, *ca)
		return
	}
	var handler http.Handler = http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/healthz" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]int{"uid": os.Getuid(), "gid": os.Getgid()})
	})
	if *upstream != "" {
		u, err := url.Parse(*upstream)
		if err != nil || u.Scheme != "http" || u.Host == "" {
			fail("fixture_upstream_invalid")
		}
		handler = httputil.NewSingleHostReverseProxy(u)
	}
	server := &http.Server{Addr: *listen, Handler: handler, ReadHeaderTimeout: 2 * time.Second,
		TLSConfig: &tls.Config{MinVersion: tls.VersionTLS12}}
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()
	errCh := make(chan error, 1)
	go func() {
		if *cert != "" || *key != "" {
			errCh <- server.ListenAndServeTLS(*cert, *key)
		} else {
			errCh <- server.ListenAndServe()
		}
	}()
	select {
	case <-ctx.Done():
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if server.Shutdown(shutdownCtx) != nil {
			fail("fixture_shutdown_failed")
		}
	case err := <-errCh:
		if err != http.ErrServerClosed {
			fail("fixture_start_failed")
		}
	}
}

func probeHealth(target, caPath string) {
	pool, _ := x509.SystemCertPool()
	if pool == nil {
		pool = x509.NewCertPool()
	}
	if caPath != "" {
		pem, err := os.ReadFile(caPath)
		if err != nil || !pool.AppendCertsFromPEM(pem) {
			fail("probe_trust_failed")
		}
	}
	client := &http.Client{Timeout: 3 * time.Second, Transport: &http.Transport{
		TLSClientConfig: &tls.Config{RootCAs: pool, MinVersion: tls.VersionTLS12}},
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	response, err := client.Get(target)
	if err != nil {
		var hostnameError x509.HostnameError
		var authorityError x509.UnknownAuthorityError
		if errors.As(err, &hostnameError) {
			fail("probe_hostname_failed")
		}
		if errors.As(err, &authorityError) {
			fail("probe_authority_failed")
		}
		fail("probe_transport_failed")
	}
	defer response.Body.Close()
	var identity struct {
		UID int `json:"uid"`
		GID int `json:"gid"`
	}
	if response.StatusCode != 200 || json.NewDecoder(http.MaxBytesReader(nil, response.Body, 4096)).Decode(&identity) != nil || identity.UID != 99 || identity.GID != 100 {
		fail("probe_identity_failed")
	}
	fmt.Println("health_pass uid=99 gid=100")
}

func fail(code string) { fmt.Fprintln(os.Stderr, code); os.Exit(1) }
