# Disposable deployment fixture

Plan: [SPIKE-005](../../docs/spikes/SPIKE-005-deployment.md). The standalone Go health server tests container identity and verified TLS; it contains no adapter endpoints or credentials and never reads `.env`.

```sh
python3 spikes/SPIKE-005/deploy_experiment.py --local
python3 spikes/SPIKE-005/deploy_experiment.py --target "$SPIKE_UNRAID_SSH_TARGET"
```

Requires local Go, Docker, OpenSSL and Python; target execution additionally requires authenticated SSH, Docker Compose and existing `proxynet`. Set `SPIKE_UNRAID_SSH_TARGET` to the authorized direct LAN SSH target before the target command; the hostname route can invoke Tailscale authentication. The runner builds a static Linux binary locally, uploads only its disposable build context and synthetic certificates, and creates a unique temporary Compose project. It does not install anything into existing Compose Manager projects. Compose Manager's project directory is inventoried read-only separately.

The historical runner serves HTTP, native HTTPS and a generic HTTPS proxy as `99:100`; it is retained unchanged to reproduce saved evidence. The proxy is extra experiment coverage, excluded from product requirements and acceptance. Required deployment scope is direct localhost, shared Docker-network or private LAN access. Generated certificates cover unique fixture DNS names; probes verify trust and hostname. A fourth startup attempt uses an unreadable key.

Results record safe check outcomes and cleanup. Container/image/project names are generated; cleanup removes only those resources and the temporary directory. Local results use a new dedicated network and cannot establish Unraid or `proxynet` behavior. The separate target trial passed on Unraid 7.3.2 (EVD-014). No host ports are published.
