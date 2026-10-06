# Docker setup and advanced configuration

Status: Source deployments verified; public image publication pending  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

For installation through Unraid's web interface, use the
[Unraid walkthrough](unraid.md). This page is for users comfortable with
Docker commands and those who need additional configuration.

## Docker Compose

Requires Docker Compose, an AudiobookDB API key, and a Docker network shared
with Audiobookshelf. This method pulls a prebuilt image. Public registry
publication is pending; use the [source-build option](#build-directly-from-github)
until anonymous image pulls are verified.

```bash
git clone https://github.com/H2OKing89/abs-audiobookdb.git
cd abs-audiobookdb
cp .env.example .env
```

Edit `.env`: set `AUDIOBOOKDB_CONTACT` to your real contact email or public
HTTPS contact URL, and `DOCKER_NETWORK` to the network used by Audiobookshelf.
Then start the adapter:

```bash
docker compose up -d
docker compose exec adapter /adapter health
```

Follow [Connect Audiobookshelf](audiobookshelf.md), using `http://adapter:8080`
as the provider URL. Put your AudiobookDB API key in the provider's
Authorization field. The default setup is available only on the shared
Docker network; choose a different layout below if needed.

## Choose a direct URL

| Layout | Adapter URL / Compose configuration |
| --- | --- |
| Shared Docker network | `http://adapter:8080`; default Compose, `DOCKER_NETWORK` matches ABS |
| ABS on host | `http://127.0.0.1:8080`; add `compose.host.yaml` with default loopback binding |
| Private LAN | `http://<host-lan-address>:8080`; add host override and set `BIND_ADDRESS` explicitly |

For host or LAN access, add `compose.host.yaml`. Set `BIND_ADDRESS` in `.env`
to `127.0.0.1` for host-only access or your server's private LAN IP for LAN
access. Inside an Audiobookshelf container, `localhost` refers to that
container; use the adapter's network name or the server's LAN IP instead.
No reverse proxy is required.

```bash
docker compose -f compose.yaml -f compose.host.yaml up -d
docker compose logs --tail=20 adapter
docker compose exec adapter /adapter health
```

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
TLS_DIRECTORY=/path/to/certificates docker compose -f compose.yaml -f compose.tls.yaml up -d
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

The [Unraid walkthrough](unraid.md) supplies a complete configuration for the
stack editor. It pulls a prebuilt image and connects through your LAN, without
requiring a source checkout or a shared Docker network.

For a custom installation, combine the runtime settings in `compose.yaml`
with the build settings in `compose.github.yaml` and your chosen network/port
settings. A local source build needs an absolute checkout path if the stack
file is stored elsewhere. Standalone `docker compose up` does not register a
stack in Compose Manager.

## Update or roll back an image install

For Compose Manager installations, use the stack's **Check Updates** then
**Update Stack**, or **Force Update** to pull again. Keep Build on Update
turned off for image installs. From a terminal:

```bash
docker compose pull
docker compose up -d
```

Include the same override files used at installation in both commands.
`latest` follows tested releases; restarting alone is not an update schedule.
To roll back, change the image tag in the configuration to an available exact
version such as `:0.1.0`, then pull/start again. Preserve your other settings.

## Build directly from GitHub

Add `compose.github.yaml` to build the adapter from a tested release's full
commit SHA. Docker fetches the source and builds on the deployment host;
GitHub Actions and a published container image are unnecessary.

```bash
export ADAPTER_VERSION=0.1.0
export ADAPTER_SOURCE_REVISION=$(git rev-list -n 1 v0.1.0)
docker compose -f compose.yaml -f compose.github.yaml up -d --build
```

Add `-f compose.host.yaml` for your selected host/LAN binding, or the native TLS
override for HTTPS. Set contact and network using the same `.env` settings.
`pull_policy: never` avoids a registry lookup for the locally built image.
An existing image can start without fetching GitHub; `--build` fetches source
again when an update is requested.

Keep the stack's contact, network and port settings when updating. A build
pinned to a release stays on that release until you change its SHA/version;
GitHub pushes do not update an installed adapter automatically. Retain the old
image and configuration before changing versions. See [releases](releases.md)
for update and rollback instructions.

## Build local source for development

Add the explicit source override to keep builds separate from normal installs:

```bash
docker compose -f compose.yaml -f compose.source.yaml up -d --build
```

This builds the local checkout as `abs-audiobookdb:development`, with no
registry pull. It uses the base runtime/network settings. Retain this override
in subsequent commands for that installation.

## Run without Docker

Requires Go 1.25 or newer. Replace the example contact with your real contact:

```bash
export AUDIOBOOKDB_CONTACT='operator@example.com'
export LISTEN_ADDR='127.0.0.1:8080'
go run ./cmd/abs-audiobookdb
curl http://127.0.0.1:8080/health
```

Use a provider URL reachable from Audiobookshelf. The Go adapter reads process
environment variables; it does not load `.env` or development ABS credentials.
