# Pullable release images and updates through Unraid

Status: Accepted; public registry verification passed  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID and status: ADR-008 / Accepted

## Context and linked requirements

REQ-003/005/011; ADR-007. The owner finds source-build Compose instructions
too complex and requests moving image tags for Unraid's update controls.
The owner chose update buttons, without scheduled automatic installation.

## Decision question

How should normal installations receive tested releases without editing source
commit IDs or version numbers?

## Options and tradeoffs

Source/exact-version pins preserve a known build but need configuration edits
for upgrades. A moving release tag lets a registry pull select the current
tested image while exact tags remain available for rollback.

## Decision and rationale

Default Compose and Unraid templates to `ghcr.io/h2oking89/abs-audiobookdb:latest`.
Move local source builds to an explicit development override; retain advanced
GitHub builds. Keep runtime/network restrictions and direct LAN support.
Install updates through native Docker or Compose Manager controls appropriate
to the installation. Keep Build on Update disabled for image installs.

Build/test/package locally. Publish an immutable exact version first, verify
anonymous access, then promote the same image to latest and verify it again.
Never republish an exact version with different bytes or promote an older
release accidentally. Initial publication uses the original verified v0.1.0
artifact, not a later main build carrying the same version. GitHub Actions stays
disabled. Public pulls passed in EVD-029; image installation guides are available.

## Evidence and source versions

[Distribution checks](../evidence/EVD-028-image-update-flow.md),
[public registry verification](../evidence/EVD-029-registry-publication.md),
[release procedure](../releases.md),
[GitHub registry guidance](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
and [Compose Manager user guide](https://github.com/mstrhakr/compose_plugin/blob/main/docs/user-guide.md).

## Consequences and risks

Public GHCR publication needs a maintainer login with package-write permission
and public visibility. Moving tags require an update action; they do not create
an update schedule. Exact tags permit user rollback. The CA listing still needs
submission/review. Initial release architecture remains linux/amd64.

## Affected documents and tests

Compose configuration, Unraid template checks, local publisher regressions,
installation/release guides and changelog. No metadata/API contract changes.

## Reviewer and date

Owner selected update buttons and instructed implementation, 2026-10-05.

## Supersedes / superseded by

Supersedes ADR-007's version-pinned normal installation defaults and deferral
of latest. Preserves its immutable release artifacts, source pins for advanced
builds, rollback identity and local validation requirements.
