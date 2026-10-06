# Public registry publication

Status: Version image uploaded; public visibility and latest promotion pending  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-029

ADR-008; owner completed the required local GHCR Docker login to continue
publication and complete PR #3.

## Source URL or fixture provenance

Original [v0.1.0 release](https://github.com/H2OKing89/abs-audiobookdb/releases/tag/v0.1.0),
[release checks](EVD-025-versioned-release-deployment.md),
and [local publisher](../../scripts/publish_image.py).
GitHub [visibility instructions](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility#configuring-visibility-of-packages-for-your-personal-account).

## Captured date and environment

2026-10-05 America/Chicago, local Linux/amd64 Docker host and actual GHCR.

## Version, commit or content hash

- Version: 0.1.0, revision `59415d679189a7e5ae56ef997e493afc57bd9298`, clean.
- Image ID: `sha256:e00a4b25e414b5b44a5cdbb76ea3f4d8203286f4441261a9eeb4791c9f48d02f`.
- Registry digest: `sha256:48285e1c765ed8b92289991670da02b1c6ab2c13d3108f9c69cff200543d9138`.
- Exact reference: `ghcr.io/h2oking89/abs-audiobookdb:0.1.0`.

## Method and reproduction steps

Run `python3 scripts/publish_image.py 0.1.0` after local Docker login. The
publisher checks archived artifacts, load acceptance, clean tagged source,
executable identity and OCI metadata. It checks remote exact-tag identity
before promoting latest and uses a fresh empty Docker config for anonymous
pull verification. Read package visibility through GitHub's authenticated API
without printing credentials.

## Sanitized artifact path

The version image is uploaded under the exact reference above. Build/load
artifacts remain the unchanged GitHub release assets. Credentials remain in
Docker's configuration outside this repository and are not redistributed.

## Claims supported and limitations

Authenticated version publication passed and preserves the original tested
image. The registry package initially remains private; public pulls, latest
promotion, and installation from public GHCR are not yet verified. PR #3 stays
draft pending those checks. No persistent Unraid deployment was updated.

## Observed outcome

Pass: archive/identity/load verification, initial exact-version push and
authenticated pull with the expected image ID. GitHub package API reports
one version and private visibility. Anonymous pull fails as expected for the
private package; publisher stops before changing latest. Owner was directed
to Package settings → Change visibility → Public. GitHub Actions remains disabled.

## Synthetic or live classification

Actual GHCR publication and authenticated/anonymous read checks. No upstream
metadata traffic or application/account writes.

## Sanitization and redistribution notes

Only public image/source identities and publication outcomes are recorded.
No tokens, Authorization values, operator contact or host settings are included.
