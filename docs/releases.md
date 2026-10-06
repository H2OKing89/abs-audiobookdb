# Versioned local releases

Status: Initial development release process  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## Version policy

Start with **v0.1.0**. Under [Semantic Versioning](https://semver.org/), major
zero means initial development; its FAQ recommends 0.1.0 as the starting
version. Use 0.1.1 for compatible fixes and 0.2.0 for new capabilities or
contract changes. Planning baseline 1.0 is a separate document baseline.

`internal/buildinfo/VERSION` is the canonical source version. Update Dockerfile
defaults, the GitHub Compose version, and the Unraid template together. Released
tags and versioned images are immutable. Defer `latest` until an explicit
update policy exists. This initial packaged release supports linux/amd64.

## Build and verify locally

Review and commit changes, run local CI, and create the version tag at that
tested commit. The release script requires a clean checkout and matching tag;
it reruns CI and the synthetic memory experiment with three minutes of warm
traffic after the large cold reads before packaging anything.

```bash
./scripts/ci.sh
git tag -a v0.1.0 -m 'Initial development release v0.1.0'
./scripts/release.sh
```

Artifacts under ignored `dist/v0.1.0/` include a Linux binary, load report,
image archive, build identity, licenses, and SHA-256 checksums. The archive
can be installed with `docker load -i <image.tar.gz>` without a registry.
`/adapter version` reports version, full revision and dirty state; startup
logs and OCI labels also identify the build. Development builds may report
`unknown` when source revision information is unavailable.

## Publish without hosted CI

Push the reviewed branch and its specific tag, then upload validated artifacts
to a GitHub release. No GitHub Actions workflow is required.

```bash
git push origin main v0.1.0
gh release create v0.1.0 --verify-tag --title 'v0.1.0' \
  --notes-file docs/release-notes/0.1.0.md dist/v0.1.0/*
```

For GHCR, use a local registry login with package-writing permission, tag the
validated image `ghcr.io/h2oking89/abs-audiobookdb:0.1.0`, and push it. Keep
credentials out of files committed here and use `--password-stdin`. Make the
package public and verify anonymous pull before announcing template support.
GitHub's [registry guide](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
documents token requirements and the initial private visibility.

## Update and roll back

For GitHub source builds, set `ADAPTER_SOURCE_REVISION` to the full SHA behind
the tested release and `ADAPTER_VERSION` to its version. The same SHA selects
source and labels the image. Run Compose with `--build`, or **Update** with
**Build on Update** enabled in Compose Manager.

Before updating, retain the prior image and stack configuration. Roll back
using its saved image or its exact source SHA/version and the same configuration.
Check version, health, readiness, and ABS-container connectivity afterward.
The adapter stores no persistent catalog data; keep operator configuration
and ABS's provider settings separate from source updates.
