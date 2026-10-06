# Contributing

Read [Repository Guidelines](AGENTS.md) and the
[current contracts](docs/planning/02-contracts-mapping.md) before changing the
adapter. Runtime code lives in `cmd/` and `internal/`; experimental tooling
and invented fixtures live in `spikes/`. Current source licensing is MIT.

## Run checks

Run local CI before opening a pull request. Requires Bash, Git, Go 1.25 or
newer, a C compiler for race tests, Python 3, Node.js, and Docker:

```bash
./scripts/ci.sh
```

The runner checks documentation links, Python/JavaScript syntax, JSON,
Go formatting, module consistency, race tests, vet, the binary build, and
Docker health/shutdown with network access disabled. It removes its temporary
container and keeps the local build/image for reuse. It does not rewrite source
or module files; fix formatting with `gofmt -w cmd internal` when needed.

Use `./scripts/ci.sh --no-docker` when Docker is unavailable, and state that
container checks were skipped in the PR. Go tests use synthetic local HTTPS
servers and need no API keys, ABS, Unraid or `.env`. There is no coverage quota.
GitHub Actions is disabled; PR validation is reported from local runs.

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
