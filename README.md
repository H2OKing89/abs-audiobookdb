# abs-audiobookdb

A read-only metadata adapter that lets [Audiobookshelf](https://www.audiobookshelf.org/)
search [AudiobookDB](https://audiobookdb.org/) through a custom book metadata provider.
Written in Go, with Docker deployment for localhost, a shared Docker network, or a
private LAN.

## Features

- Search by title and author, or look up an exact Audible ASIN.
- Return recording-specific matches, including available narrator, language,
  publisher, series, identifier, and cover metadata.
- Validate the caller's AudiobookDB API key on every search, including cached searches.
- Bound request time, upstream calls, concurrency, response size, and cache memory.
- Run directly over HTTP or optional native HTTPS.

The adapter reads upstream metadata. Audiobookshelf handles applying a selected
match to your library. Exact ISBN-only lookup is deferred; available ISBNs are
included in results.

## Quick start with Docker

Requires Docker Compose, an AudiobookDB API key, and an existing Docker network
shared with Audiobookshelf. Images are built from source; no prebuilt image is
published.

For a new checkout:

```bash
git clone https://github.com/H2OKing89/abs-audiobookdb.git
cd abs-audiobookdb
cp .env.example .env
```

Edit `.env`: set `AUDIOBOOKDB_CONTACT` to your real contact email or public HTTPS
contact URL, and `DOCKER_NETWORK` to the network shared with Audiobookshelf.
Then start the adapter and check its health:

```bash
docker compose up -d --build
docker compose exec adapter /adapter health
```

In Audiobookshelf, add a custom **book metadata provider** with:

| Setting | Value |
|---|---|
| Base URL | `http://adapter:8080` |
| Authorization | Your AudiobookDB API key; raw keys or `Bearer <key>` work |

Use the base URL without `/search`. The default Compose configuration exposes the
service only on the shared Docker network. For host or LAN access, add
`compose.host.yaml` and choose the intended bind address. A reverse proxy is not
required.

See the [deployment guide](docs/deployment.md) for native TLS, configuration,
and installation through Unraid Compose Manager.

## Run without Docker

Requires Go 1.25 or newer:

```bash
export AUDIOBOOKDB_CONTACT='operator@example.com' # Replace with your real contact.
export LISTEN_ADDR='127.0.0.1:8080'
go run ./cmd/abs-audiobookdb
curl http://127.0.0.1:8080/health
```

Use a provider URL reachable from Audiobookshelf. Inside an ABS container,
`localhost` refers to that container.

## Project status and development

The MVP passed Go race tests, live upstream read checks, isolated Audiobookshelf
2.37.1 UI checks, and disposable deployment tests on Unraid 7.3.2. See the
[acceptance record](docs/evidence/EVD-017-private-mvp-acceptance.md) for results
and limitations. A permanent Unraid stack and live ABS provider setup remain
operator installation steps.

```bash
go test -race ./...
go vet ./...
go build -trimpath -o bin/abs-audiobookdb ./cmd/abs-audiobookdb
```

Tests use synthetic fixtures and need no API credentials. See
[CONTRIBUTING.md](CONTRIBUTING.md) for checks and pull request guidance, and the
[documentation index](docs/README.md) for architecture, decisions, and evidence.
Keep credentials in ignored local files. Development ABS access settings are
used only by spike tooling; the Go adapter does not load `.env`.

## License

[MIT](LICENSE) covers project-authored source and documentation. Upstream API
access, metadata, and third-party Audiobookshelf assets retain their own terms.
Use your own AudiobookDB account and follow its API requirements.
