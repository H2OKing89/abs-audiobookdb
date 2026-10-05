# Private adapter deployment

Status: Verified with disposable private deployment  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Configure ABS

Create a custom book metadata provider with the adapter's base URL and the
AudiobookDB key as its Authorization value. Raw keys and `Bearer <key>` work.
Choose this provider in the Match tab: ABS 2.37.1 initially defaults that tab
to Google Books independently of the library's provider. Searches through the
adapter preserve separate narrator/language recordings. ABS cards show
narrators but omit language/subtitle; select a result to inspect language.

## Choose a direct URL

| Layout | Adapter URL / Compose configuration |
| --- | --- |
| Shared Docker network | `http://adapter:8080`; default Compose, `DOCKER_NETWORK` matches ABS |
| ABS on host | `http://127.0.0.1:8080`; add `compose.host.yaml` with default loopback binding |
| Private LAN | `http://<host-lan-address>:8080`; add host override and set `BIND_ADDRESS` explicitly |

For the tested Unraid installation, network `proxynet` already exists. Other
installations select their own network. No reverse proxy is required.

```bash
export DOCKER_NETWORK=proxynet
docker compose -f compose.yaml -f compose.host.yaml up -d --build
docker compose logs --tail=20 adapter
docker compose exec adapter /adapter health
```

This creates a persistent service when you run it. Acceptance trials used
temporary projects and left existing Compose Manager projects untouched.

## Runtime settings

| Variable | Behavior |
| --- | --- |
| `AUDIOBOOKDB_CONTACT` | Required real email/public HTTPS contact in User-Agent |
| `AUDIOBOOKDB_API_KEY` | Optional single-user fallback; used only if Authorization is absent |
| `AUDIOBOOKDB_BASE_URL` | Default `https://audiobookdb.org/api`; verified HTTPS required |
| `LISTEN_ADDR` | Default `:8080` |
| `TLS_CERT_FILE`, `TLS_KEY_FILE` | Both required to enable native HTTPS |
| `HEALTH_CA_FILE` | Additional PEM CA for native-TLS health verification |
| `GOMEMLIMIT` | Container default `192MiB`; Go soft target |

Compose forwards contact by default; explicitly add other runtime settings
when needed. Supply the API key in ABS to avoid duplicate configuration.
Development ABS host/key settings are unused by the adapter.

## Optional native TLS

Supply a PEM certificate/key and its CA as `server.crt`, `server.key`,
`ca.crt` in a directory readable by 99:100. A private key owned by root:100
with mode 0640 was tested; mode 0600 owned by root correctly failed. The
certificate needs the name/address ABS uses and IP SAN `127.0.0.1` for the
built-in health check. ABS must trust its issuer too.

```bash
DOCKER_NETWORK=proxynet TLS_DIRECTORY=/path/to/certificates docker compose -f compose.yaml -f compose.tls.yaml up -d --build
```

Add `compose.host.yaml` for explicit host/LAN publication. Native TLS uses
the same port 8080 and requires TLS 1.2 or newer; use an `https://` provider
URL. Health verifies both CA trust and certificate name. Certificate issuance
and installation into ABS trust stores remain operator configuration.

## Operation and limits

`/health` and `/ready` make no upstream calls. Cache TTL is sixty seconds;
every hit still performs fresh authorization. Failed/partial results are not
cached. Each request has an eight-second deadline, ten-attempt/twelve-cost-unit
ceiling and no retries. Rate limiting/overload returns 503 with safe retry
information; upstream/schema failures return 502. ABS may display an empty
result list for these failures, so inspect adapter status/code logs.

No API/account writes, persistent catalog cache or secret/query logging.
Exact ISBN-only searches return 400; ISBN metadata is still included when
available. The adapter source is MIT licensed. Upstream API access and metadata remain subject to the provider's requirements; publishing this source does not distribute a metadata archive.

## Unraid Compose Manager

The supplied files are standard Docker Compose. To make a persistent installation
appear in Unraid's Compose Manager UI, create a stack using its Add New Stack
workflow and set the project name to `abs-audiobookdb`. Put the source checkout
in persistent storage. If the manager's Compose file lives outside that checkout,
set its `build` context to the checkout's absolute path instead of `.`. The
context must include Dockerfile, `go.mod`, `cmd/` and `internal/`. Copy
`.env.example` to the stack's `.env` and set your contact and the network shared
with ABS.

Add the host/TLS override files only for your chosen layout. Build/start the
stack and select autostart if desired. Standalone `docker compose up` creates
containers but does not itself register a Compose Manager stack. No permanent
stack or live ABS provider was installed by the recorded acceptance trials.
