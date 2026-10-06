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
defaults and the advanced GitHub Compose version together. Released Git tags
and exact image tags are immutable. Normal Compose and Unraid installs use
`latest`, which moves only after a tested release is publicly verified.
This initial packaged release supports linux/amd64.

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
# Merge the reviewed release PR first, then push its specific tag.
git push origin v0.1.0
gh release create v0.1.0 --verify-tag --title 'v0.1.0' \
  --notes-file docs/release-notes/0.1.0.md dist/v0.1.0/*
```

For GHCR, sign Docker in locally with a classic token carrying `write:packages`:

```bash
docker login ghcr.io -u H2OKing89
python3 scripts/publish_image.py 0.1.0 --verify-only
python3 scripts/publish_image.py 0.1.0
```

Enter the token at Docker's password prompt; never put it in Git or a command
argument. The publisher checks artifact checksums, the immutable Git tag,
clean build identity, exact image ID and passing load report. It publishes the
exact version first, refuses to replace a different existing version image,
and requires an anonymous version pull before promoting `latest`. It verifies
an anonymous `latest` pull too and refuses promotion of an older release.

On first publication GHCR creates a private package. Set its visibility to
**Public** in the [package settings](https://github.com/users/H2OKing89/packages/container/abs-audiobookdb/settings),
then rerun the publisher. **Changing visibility is a one-time step per package**;
future version tags in this package remain public. Docker login is reused until
its credentials expire or are removed. Each release still needs local checks,
packaging and publication; a Git push alone does not publish an image.
An existing matching exact version is reused; the
script does not overwrite it. A failed public check leaves `latest` unchanged.
The image's OCI source label connects it to this repository.

GitHub's [registry guide](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
documents classic-token scopes, public anonymous access and initial private
visibility. Building and publishing happen locally; GitHub Actions stays disabled.
Only announce image installs after both tags pass anonymous pulls.

## Update and roll back

For registry installs, use the Unraid Docker **Update** / **Force Update**
controls or Compose Manager's **Check Updates → Update Stack** / **Force Update**.
Leave Build on Update disabled and keep `:latest` to receive tested releases.
Users choose when to install; no update scheduler is included. In plain Compose,
run `docker compose pull` then `docker compose up -d` with the same overrides.

To roll back, edit the image or Repository field to an available exact tag,
such as `ghcr.io/h2oking89/abs-audiobookdb:0.1.0`, and apply/pull/start again.
Keep contact, network, ports and ABS provider settings. Select `:latest` again
when ready to return to the current release channel.

For GitHub source builds, set `ADAPTER_SOURCE_REVISION` to the full SHA behind
the tested release and `ADAPTER_VERSION` to its version. The same SHA selects
source and labels the image. Run Compose with `--build`, or **Update** with
**Build on Update** enabled in Compose Manager.

Before updating, retain the prior image and stack configuration. Roll back
using its saved image or its exact source SHA/version and the same configuration.
Check version, health, readiness, and ABS-container connectivity afterward.
The adapter stores no persistent catalog data; keep operator configuration
and ABS's provider settings separate from source updates.
