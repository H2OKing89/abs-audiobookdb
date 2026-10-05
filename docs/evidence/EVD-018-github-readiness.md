# Public GitHub source readiness

Status: Pass for local preparation  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-018

ADR-005; authorized public MIT source preparation for H2OKing89/abs-audiobookdb.

## Source URL or fixture provenance

Current Git files/history, owner's public/GitHub account/MIT choices, invented
fixtures and existing sanitized evidence. Official [checkout](https://github.com/actions/checkout)
and [setup-go](https://github.com/actions/setup-go) sources/tags reviewed;
workflow references pinned v7 commits. [actionlint](https://github.com/rhysd/actionlint)
v1.7.12 installed separately for local workflow validation.

## Captured date and environment

2026-10-05, development checkout on Linux. Existing branch main; starting
commit fcaa4d7. Go 1.25.10, Docker 29.8.2, Python/Node from the development host.
GitHub CLI authenticates as the requested owner. No Git remote or target
repository existed at the beginning of this preparation.

## Version, commit or content hash

Checkout v7 SHA 3d3c42e5aac5ba805825da76410c181273ba90b1;
setup-go v7 SHA b7ad1dad31e06c5925ef5d2fc7ad053ef454303e.
Docker build image dfccb575b52ea7cebb81289cd72418160ea098711e489fb29d8ca9b3b6ed0ee8.
Runtime source unchanged during this preparation. Earlier acceptance records
remain historical and bound to their recorded source/image hashes.

## Method and reproduction steps

Run `python3 .github/scripts/check_repository.py`, `go test -race ./...`,
`go vet ./...`, `go build -trimpath -o bin/abs-audiobookdb ./cmd/abs-audiobookdb`,
`go mod tidy` with no module diff, `git diff --check`, and actionlint against
`.github/workflows/ci.yml`. Build Docker and run the workflow's health/shutdown
script with `--network none`. Validate Compose with `.env.example` substitution
and required host/TLS parameters. No API keys are required for these checks.

Review tracked files and every historical blob against the configured ignored
keys, ABS host and contact; report paths/counts only. Also inspect for private-key
and GitHub-token markers. Inspect retained UI screenshots visually; all show
only disposable ABS and invented fixtures. Local certificate/password/API
response dumps must stay outside Git. Git remote targets the owner-selected
account; preparing a remote does not push source.

## Sanitized artifact path

CI workflow, repository-check helper, .env.example, LICENSE and CONTRIBUTING.md
are reviewable source artifacts. Earlier EVD-001–017 and sanitized outputs are
preserved. Current check outcomes below summarize local tool output; no real
account/catalog or credential dump is added.

## Claims supported and limitations

The source tree is prepared for public MIT GitHub publication; standard build
and local equivalents of CI pass. Known configured private values and common
key/token markers were absent from tracked source/history. This is scoped
review, not a guarantee against every possible unknown secret. The upstream
API/data and ABS assets are not relicensed. No provider approval or legal
compatibility claim. GitHub-hosted workflow execution remains unobserved until
source is pushed. No permanent Unraid stack or live ABS provider configured.

## Observed outcome

Pass: known-private-value scan over 175 historical blobs, no credential/env/key
files in history; marker scan of tracked/publishable files; visual synthetic
screenshots; source/JSON/Markdown checks; production race tests (cached packages
reported), vet/build/module consistency; actionlint; Docker build plus health
and graceful exit zero with network disabled, 99:100 and 256 MiB. Original
workflow lint found unused loop variable SC2034; corrected to `_` and reran
successfully. Markdown hard-break whitespace is allowed via .gitattributes.
Example environment templates, source/module files and sanitized evidence
remain eligible for Git; real settings/secrets/build/Node outputs remain ignored.

## Synthetic or live classification

Offline repository/build/fixture checks and read-only GitHub metadata/tag
lookups. No AudiobookDB or live ABS calls were made. Compose Manager source was
read-only inspected to verify its Add New Stack registration workflow.

## Sanitization and redistribution notes

Local contact/API settings remain ignored and excluded from Docker context.
Current setup examples use generic hosts and paths. Historical evidence is
preserved, not rewritten into new passes. Runtime baseline 1.0 remains unchanged;
public source publication explicitly authorized in ADR-005. No catalog archive,
API/account response payloads or real credential material included.
