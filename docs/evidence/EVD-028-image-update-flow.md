# Image installation, update and rollback checks

Status: Local and disposable Unraid checks pass; GHCR public pulls pending login  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-028

ADR-008; owner requests implementation of image-based installs and update buttons.

## Source URL or fixture provenance

Original [v0.1.0 release](https://github.com/H2OKing89/abs-audiobookdb/releases/tag/v0.1.0)
and [release/deployment evidence](EVD-025-versioned-release-deployment.md).
Installed Compose Manager wrapper source; official registry:3 test container.
Fixture images extend the installed release with different invented labels;
they do not represent different application versions.

## Captured date and environment

2026-10-05 America/Chicago; local Linux/amd64 Go 1.25.10, pinned Go 1.27.1
Docker builder, Compose 5.6.0. Actual Unraid 7.3.2, Docker 29.5.3, Compose 5.5.0.

## Version, commit or content hash

- Original packaged release: v0.1.0, `59415d679189a7e5ae56ef997e493afc57bd9298`, clean.
- Packaged image: `sha256:e00a4b25e414b5b44a5cdbb76ea3f4d8203286f4441261a9eeb4791c9f48d02f`.
- Installed release base: `sha256:adb0a2e053d9c4b71ff21279da275f005967d1b2ccfc198202ccaa033b924718`.
- Registry fixture digest: `sha256:ddf754342cfc8acc51a56d5d0ab6af06826461864460636d8bd5c546dab2a7b8`.

## Method and reproduction steps

Run `./scripts/ci.sh` and `python3 scripts/publish_image.py 0.1.0 --verify-only`.
Check `docker compose config --format json` for the base, host, TLS and source
overrides, using invented environment values. Extract the Unraid guide's YAML
and substitute invented contact and loopback IP values.

On actual Unraid, create a disposable loopback registry and registered stack.
Push two label-only fixture images to a moving latest tag; keep the first under
an exact tag. Use installed `scripts/compose.sh` with `-c up` and `-c update`,
explicit project/file/stack paths and Build on Update disabled. This is the
Update/Force Update backend. Check image IDs, health, settings and restrictions
after initial install, changed latest, unchanged latest, exact-tag rollback
and return to latest. Remove the temporary stack/registry/images/files. Compare
all pre-existing stack configuration hashes before and after.

## Sanitized artifact path

Publisher regressions under `scripts/`; changed install configurations/guides.
Raw host/test logs and configuration-hash snapshots remain ignored under
`secrets/latest-update-check/`. No private target information is redistributed.

## Claims supported and limitations

Image pulls support the tested update/rollback flow and preserve settings.
Runtime restrictions remain active. Buttons were traced to installed backend
code; no rendered browser click-through or app-store installation is claimed.
Anonymous GHCR access and real registry promotion remain pending a package-write
login/public visibility. The installed adapter was not migrated or updated.

## Observed outcome

Pass: full local CI (26 Python regressions, Go race/vet/build, image identity,
health/shutdown), release artifact/image identity verification, Compose base and
four overrides, guide YAML, actual Unraid initial install, changed latest,
same-image force update, exact-tag rollback and return to latest. Health HTTP
200 and internal health pass throughout; 99:100/read-only/256 MiB retained;
saved settings unchanged. Temporary resources removed; all existing stack
configuration hashes match; live adapter retains its original healthy image.

The first disposable runner stopped at a directory guard: it assumed the
plugin replaced hyphens with underscores. The installed plugin preserved
hyphens. Removed the created temporary metadata and corrected the runner's
guard; the second run passed. The host still reports unsupported swap limits;
configured RAM was verified without claiming a swap guarantee.

## Synthetic or live classification

Synthetic local regressions and fixtures on actual Unraid. No upstream searches,
account writes, provider edits or changes to the persistent adapter.

## Sanitization and redistribution notes

Only invented fixture values and public source/image identifiers are included.
No environment credentials, operator contact or private host addresses appear.
