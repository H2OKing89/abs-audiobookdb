package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"abs-audiobookdb/internal/audiobookdb"
	"abs-audiobookdb/internal/config"
	"abs-audiobookdb/internal/provider"
	"abs-audiobookdb/internal/server"
)

func health(get func(string) string) error {
	address := get("LISTEN_ADDR")
	if address == "" {
		address = ":8080"
	}
	host, port, err := net.SplitHostPort(address)
	if err != nil {
		return errors.New("health configuration")
	}
	if host == "" || host == "0.0.0.0" || host == "::" {
		host = "127.0.0.1"
	}
	scheme := "http"
	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.Proxy = nil
	if get("TLS_CERT_FILE") != "" {
		scheme = "https"
		roots, err := x509.SystemCertPool()
		if err != nil {
			roots = x509.NewCertPool()
		}
		if ca := get("HEALTH_CA_FILE"); ca != "" {
			data, err := os.ReadFile(ca)
			if err != nil || !roots.AppendCertsFromPEM(data) {
				return errors.New("health trust")
			}
		}
		transport.TLSClientConfig = &tls.Config{RootCAs: roots, MinVersion: tls.VersionTLS12}
	}
	client := http.Client{Transport: transport, Timeout: 2 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	defer client.CloseIdleConnections()
	resp, err := client.Get(scheme + "://" + net.JoinHostPort(host, port) + "/health")
	if err != nil {
		return errors.New("health unavailable")
	}
	resp.Body.Close()
	if resp.StatusCode != 200 {
		return errors.New("health unavailable")
	}
	return nil
}
func run() error {
	if len(os.Args) > 1 {
		if len(os.Args) == 2 && os.Args[1] == "health" {
			return health(os.Getenv)
		}
		return errors.New("unknown command")
	}
	cfg, err := config.Load(os.Getenv)
	if err != nil {
		return err
	}
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	client := audiobookdb.New(cfg.BaseURL, cfg.Contact, nil)
	defer client.Close()
	p := provider.New(client)
	handler := server.New(p, cfg.APIKey, logger)
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	go p.Sweep(ctx)
	httpServer := &http.Server{Handler: handler, ReadHeaderTimeout: 2 * time.Second, ReadTimeout: 3 * time.Second, WriteTimeout: 9 * time.Second, IdleTimeout: 30 * time.Second, MaxHeaderBytes: 8 << 10, TLSConfig: &tls.Config{MinVersion: tls.VersionTLS12}, ErrorLog: slog.NewLogLogger(slog.NewTextHandler(os.Stderr, nil), slog.LevelError)}
	listener, err := net.Listen("tcp", cfg.Listen)
	if err != nil {
		return errors.New("listener unavailable")
	}
	if cfg.CertFile != "" {
		cert, err := tls.LoadX509KeyPair(cfg.CertFile, cfg.KeyFile)
		if err != nil {
			listener.Close()
			return errors.New("invalid TLS key pair")
		}
		httpServer.TLSConfig.Certificates = []tls.Certificate{cert}
		listener = tls.NewListener(listener, httpServer.TLSConfig)
	}
	done := make(chan error, 1)
	go func() { done <- httpServer.Serve(listener) }()
	logger.Info("started", "version", "0.1", "tls", cfg.CertFile != "")
	select {
	case err := <-done:
		if !errors.Is(err, http.ErrServerClosed) {
			return errors.New("server unavailable")
		}
	case <-ctx.Done():
		handler.Stop()
		shutdown, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := httpServer.Shutdown(shutdown); err != nil {
			httpServer.Close()
			return errors.New("shutdown deadline")
		}
		<-done
	}
	return nil
}
func main() {
	if err := run(); err != nil {
		slog.Error("adapter stopped", "reason", strings.TrimSpace(err.Error()))
		os.Exit(1)
	}
}
