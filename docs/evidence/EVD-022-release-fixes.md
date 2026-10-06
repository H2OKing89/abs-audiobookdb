# Cooldown, CI and build identity verification

Status: Candidate checks passed; final tagged artifacts verified by release script  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-022

Audit items 1, 2 and 4; ADR-007.

## Source URL or fixture provenance

Project-authored Go and Python regression fixtures. Retry-After formats follow
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3).

## Captured date and environment

2026-10-05 local development host; Go 1.25.10; Docker with pinned Go builder.
No actual upstream requests or credentials are required.

## Version, commit or content hash

Candidate version 0.1.0, base commit
`59600e06d717aa1a08801bd94bec3f8702b1dde0`, honestly marked dirty.
Candidate image `sha256:0cca7660c03670e68b41dcb416a0d71aa4828f2a902e299e8c8a5aa52f3b2706`.
Final clean revision/image identity belongs to the versioned release assets.

## Method and reproduction steps

Run `./scripts/ci.sh`. Numeric delay, all three HTTP date forms, past/malformed
values, zero, huge numbers and the 300-second bound have Go coverage. Tests
verify exact cooldown expiry and credential isolation. Python discovery runs
all script regression tests, including the six previously omitted link tests.
Container checks compare CLI build identity and OCI labels, then exercise
health and graceful shutdown with networking disabled.

## Sanitized artifact path

Regression tests under `internal/audiobookdb/`, `internal/buildinfo/`, and
`scripts/test_*.py`. Release assets include `version.json`, `image-id.txt`,
`load.json`, and `SHA256SUMS`; see [release procedure](../releases.md).

## Claims supported and limitations

Cooldown now honors HTTP-date Retry-After while preserving the existing 1–300
second policy. The exact cap no longer rounds to 301 seconds. Local CI runs
Python tests. Version and source identity do not require runtime configuration.
No hosted CI, live quota test, API stability guarantee or registry pull is claimed.

## Observed outcome

Targeted Go race tests and full candidate local CI passed. After adding Unraid
policy tests, Python discovery passed ten tests. Clean release packaging reruns
the complete suite and synthetic load before producing uploadable artifacts.

## Synthetic or live classification

Synthetic, offline checks plus local Docker builds; zero live API traffic.

## Sanitization and redistribution notes

Only invented credentials/contact values appear in fixtures. Release packaging
includes adapter MIT and Go BSD notices; no environment files enter the image.
