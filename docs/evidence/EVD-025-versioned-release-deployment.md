# Versioned release and live Unraid deployment

Status: Release published and live deployment verified; registry/CA listing pending  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-025

ADR-007; audit items 1, 2, 4, 5 and 6. Owner reports ABS provider setup complete;
that report is distinct from the connectivity checks below.

## Source URL or fixture provenance

[v0.1.0 release](https://github.com/H2OKing89/abs-audiobookdb/releases/tag/v0.1.0).
Project-authored regressions and synthetic HTTPS fixtures; actual Unraid host
and existing ABS container for health-only verification.

## Captured date and environment

2026-10-05 America/Chicago; load captured 2026-10-06 01:13:53 UTC.
Local Go 1.25.10; actual Unraid 7.3.2, Docker 29.5.3, Compose 5.5.0.
No VM was created.

## Version, commit or content hash

- Release: `v0.1.0`, revision `59415d679189a7e5ae56ef997e493afc57bd9298`, dirty false.
- Packaged image: `sha256:e00a4b25e414b5b44a5cdbb76ea3f4d8203286f4441261a9eeb4791c9f48d02f`.
- Unraid source-built image: `sha256:adb0a2e053d9c4b71ff21279da275f005967d1b2ccfc198202ccaa033b924718`.
- Both binaries: SHA-256 `6e7a8be727fa8908db648f948e1870c1772509b40759bf07f08826362357e60b`.

Image layers differ; executable bytes match. Published `SHA256SUMS` identifies
each downloadable artifact.

## Method and reproduction steps

Run the clean tagged [release script](../../scripts/release.sh): local CI,
large cold reads, three-minute warm load, packaging and checksums. Publish the
specific reviewed tag and artifacts. Download reports and archive anonymously
and compare hashes.

Save the prior target image/configuration. Build from the exact release SHA,
then update the registered Compose Manager stack using its Update backend.
Inspect version, restrictions, labels, restart/OOM state, autostart/build settings
and environment. Check health/readiness from the LAN and actual ABS container.

## Sanitized artifact path

Release assets: `load.json`, `version.json`, `image-id.txt`, `SHA256SUMS`, Linux
binary, image archive and MIT/Go BSD notices. Failed candidates remain linked
in [EVD-023](EVD-023-sustained-memory.md). Host backups stay ignored in `secrets/`.

## Claims supported and limitations

Published artifacts identify tested source; the persistent Unraid stack runs that
SHA. The template can install a loaded local image. Default GHCR pulls need
publication credentials; CA validation/submission/review remains external.
No reboot, live metadata search or provider configuration change was performed.

## Observed outcome

Pass: full local CI, ten Python regressions, Go race/vet, image metadata,
health/shutdown, checksums and anonymous downloads. Final load: **250.631s**;
24 cold queries, maximum 7.561s; **667** warm searches over 180s, maximum 7.559s;
peak RSS **24.21 MiB** under 256 MiB, no OOM/restart. Eviction, fresh auth,
slow/oversized failures, health, sentinel hygiene and cleanup passed.

Actual Unraid: correct version/revision; healthy; 99:100; read-only; 256 MiB;
capabilities dropped; no-new-privileges; unless-stopped; Compose Manager label;
autostart and Build on Update enabled. LAN and ABS-container health/ready returned
200. Environment bytes and other-stack configuration hashes were unchanged.
Saved rollback image passed isolated startup/health/shutdown and remains tagged.
Template-derived disposable creation/start/health/version/shutdown/cleanup passed.
Temporary files/containers were removed. GitHub Actions remains disabled.

Target Docker reports unsupported swap-limit capabilities; configured RAM was
verified, while swap-limit behavior is not guaranteed on that host.

## Synthetic or live classification

Synthetic load/regressions; actual Unraid deployment and ABS-container health.
Zero live AudiobookDB calls for this release.

## Sanitization and redistribution notes

No keys, operator contact, target addresses or environment files are published.
Image contains executable, public trust roots and licenses; fixtures are invented.
