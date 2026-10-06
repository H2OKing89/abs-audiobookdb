# Local CI validation

Status: Pass  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-020

ADR-006; owner requires local CI after pushing the public source.

## Source URL or fixture provenance

The former hosted workflow's checks, Go synthetic tests and local Docker image.
Read-only GitHub Actions settings and workflow/run listings verified the
repository's state before and after the owner-authorized settings change.

## Captured date and environment

2026-10-05, Linux development checkout; Go 1.25.10, Python 3.14.4,
Node.js 24.21.0, Docker 29.8.2, ShellCheck 0.11.0. Starting commit 6e7acbe.
An existing README table-formatting change is preserved.

## Version, commit or content hash

Runtime source is unchanged from starting commit 6e7acbe. Prior acceptance is
recorded in EVD-017, with subsequent source checks recorded in the changelog.
This change moves repository validation tooling and adds a local orchestration
script; it does not change production code.
Built image: sha256:dfccb575b52ea7cebb81289cd72418160ea098711e489fb29d8ca9b3b6ed0ee8.

## Method and reproduction steps

Run `bash -n scripts/ci.sh` and `./scripts/ci.sh` from the repository root.
The script checks syntax/relative links, whitespace, formatting, non-mutating
module consistency, race tests, vet, binary build, Docker build and networkless
container health/graceful exit. Verify no labelled CI container remains.
Use `./scripts/ci.sh --no-docker` only for an explicitly partial check.

Verify hosted execution is disabled with
`gh api repos/H2OKing89/abs-audiobookdb/actions/permissions --jq .enabled`.
The owner-authorized setting change returned false; the existing listed runs
were all completed, so no active run needed cancellation.

## Sanitized artifact path

[CI runner](../../scripts/ci.sh),
[repository checker](../../scripts/check_repository.py), and this record.
Real local configuration, certificates and build outputs remain ignored.

## Claims supported and limitations

GitHub Actions is disabled for the public repository. Hosted workflow and
Dependabot configuration are removed from the working tree; those deletions
reach GitHub with the next source push. Local checks need no real API keys or
live ABS/Unraid service. No hosted check success is claimed.

## Observed outcome

Pass: `./scripts/ci.sh` completed repository syntax/links/JSON checks, whitespace,
formatting, module consistency, race tests (six cached package results), vet,
binary and Docker builds, 99:100 container identity, network-disabled health,
and graceful exit zero. No labelled CI container remained afterward.

`--no-docker` passed from outside the repository directory and explicitly
reported skipped Docker checks. Help returned zero; invalid options and extra
arguments returned two. Bash syntax and ShellCheck passed. Production code,
module files, deployment settings, AGENTS.md and prior evidence are unchanged.
GitHub Actions settings read back as disabled. Source changes remain local
for the next push; no hosted check run or live API test was attempted.

## Synthetic or live classification

Synthetic local Go/container checks and GitHub repository configuration access.
No live upstream API calls, library changes or deployment.

## Sanitization and redistribution notes

The health container has network disabled and a placeholder operator contact.
The script never loads `.env`; Docker context continues to exclude secrets.
Existing acceptance artifacts and historical CI-preparation records are preserved.
