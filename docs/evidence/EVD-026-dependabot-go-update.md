# Dependabot PR #1 local validation

Status: Merged after local checks passed  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-026

Owner instruction: merge PR #1 if safe; keep hosted CI disabled.

## Source URL or fixture provenance

[PR #1](https://github.com/H2OKing89/abs-audiobookdb/pull/1) changes only the
Docker builder's Go tag and digest. Reviewed primary
[Go release history](https://go.dev/doc/devel/release) and
[Go 1.27 notes](https://go.dev/doc/go1.27). Tests use project-authored fixtures.

## Captured date and environment

2026-10-05 America/Chicago; load finished 2026-10-06 01:46:22 UTC;
GitHub merge completed 01:47:30 UTC. Local Linux/amd64 Docker host.

## Version, commit or content hash

- PR head: `217eaf7cfa1e2b87da66de7158be3e9361d5acb3`.
- Tested merge candidate: `26a3845e79d343905598ebeb9f05c75848a30056`.
- GitHub merge: `04c0728abd94bf2829cf67493fa3a29b133dd9bd`.
- Both source trees: `7d5a664ee69388e6e56d537299c3b82d6e5dd388`.
- Builder: `golang:1.27.1-bookworm@sha256:69a7b9788769bec032d238959b61854e9ae87f57be9029ec04e9885fabf99195`.
- Tested image: `sha256:ef6dac63ccff77da7cce93f32327739506511465755fb3f030fff02becbf2c99`.

## Method and reproduction steps

Merged the PR into current main in an isolated checkout. Ran `./scripts/ci.sh`
using host Go 1.25.10, including Docker build/metadata/health/shutdown checks.
Inside the proposed digest-pinned Go 1.27.1 builder, ran formatting, module
consistency, `go test -race ./...`, `go vet ./...` and a binary build with
network access disabled. The builder reported Go 1.27.1.

Ran `python3 spikes/MVP-001/load.py --image <tested-image> --warm-seconds 180`.
Checked PR head and main before merging with a matching-head guard. After merge,
compared Git trees and read repository Actions settings again.

## Sanitized artifact path

[Exact synthetic load report](MVP-001/load-20261006T014622844220Z.json).

## Claims supported and limitations

Only the digest-pinned builder changes; production source and runtime limits
are preserved. Both supported source-toolchain checks and proposed-toolchain
checks pass. This verifies the tested local workload, not every deployment.
Published v0.1.0 artifacts remain their original release builds.

## Observed outcome

Pass: full local CI, ten Python regressions, Go 1.25.10 and 1.27.1 race/vet/build,
image metadata, nonroot health and graceful shutdown. Load passed in 250.572s:
24 cold searches, maximum 7.549s; 667 warm searches over 180s, maximum 7.565s;
peak process RSS 28,012,544 bytes (26.71 MiB), no OOM or restart. Cache eviction,
fresh auth, slow/oversized errors, log hygiene and cleanup passed.

PR is merged; GitHub's merged tree exactly matches the tested tree. Actions
permissions still report `enabled: false`. Old billing-blocked CI checks were
not treated as code verification.

## Synthetic or live classification

Local synthetic tests and Docker workload; actual GitHub merge/settings checks.
No live ABS/AudiobookDB traffic or deployment operation.

## Sanitization and redistribution notes

Only invented fixture data, metrics and public source/image hashes are recorded.
No environment files, real credentials or operator contact are included.
