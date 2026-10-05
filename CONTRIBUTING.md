# Contributing

Read [Repository Guidelines](AGENTS.md) and the
[current contracts](docs/planning/02-contracts-mapping.md) before changing the
adapter. Runtime code lives in `cmd/` and `internal/`; experimental tooling
and invented fixtures live in `spikes/`. Current source licensing is MIT.

## Run checks

Use Go 1.25 or newer and Docker for container checks:

```bash
gofmt -w cmd internal
go test -race ./...
go vet ./...
go build -trimpath -o bin/abs-audiobookdb ./cmd/abs-audiobookdb
docker build -t abs-audiobookdb:private .
```

Go tests use synthetic local HTTPS servers and do not need API keys, ABS,
Unraid or `.env`. GitHub CI also checks formatting, Python/JavaScript syntax,
module consistency and the Docker health command. There is no coverage quota.

## Changes and pull requests

Use concise, imperative commits. Explain the behavior changed, reproduction
steps and validation in the PR; link affected requirement/decision/evidence IDs
when applicable. Include screenshots for meaningful UI workflow findings.
Update `docs/CHANGELOG.md` when contracts, planning or deployment change.
Preserve observed failures and distinguish synthetic tests from real API checks.

Contract changes reopen affected planning gates before changing runtime
behavior. Public source publication is authorized; it does not change the
read-only API contract or imply provider approval.

## Fixtures and credentials

Keep `.env`, credentials and local certificates ignored. Never include keys,
Authorization headers, account payloads, private hosts or catalog dumps in PRs
or issues. Use invented fixtures and sanitized result records; retain existing
evidence links. Copy `.env.example` for Compose configuration.

Live spike runners are opt-in tools. Record a budget and stop conditions
before executing them, and do not run them in CI. They can create temporary
containers and local evidence; target deployment requires authorized SSH access.
