# Versioned releases and Unraid distribution

Status: Accepted  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID and status: ADR-007 / Accepted

## Context and linked requirements

The owner requests a tested release, traceable builds, sustained memory checks,
and support for both Docker Compose and Unraid's app template/store. ABS provider
setup is reported complete by the owner. Existing read-only contracts remain.

## Decision question

How should users install and update a known, verified build without hosted CI?

## Options and tradeoffs

Tracking main provides new source but no tested release boundary. Versioned
source works without a registry; Docker templates require a public pullable image.

## Decision and rationale

Begin with v0.1.0, following SemVer initial-development guidance. Embed version,
revision and dirty state, add OCI metadata, pin GitHub builds to full source SHA,
and retain prior artifacts for rollback. Use local CI and a reproducible synthetic
memory experiment to package linux/amd64 binaries and images. Prepare a versioned
GHCR template, root CA profile and project icon; registry publication and CA
approval must be verified separately. Keep hosted GitHub Actions disabled.

## Evidence and source versions

[Release procedure](../releases.md), [Unraid guide](../unraid.md),
[SemVer](https://semver.org/), and
[official CA submission requirements](https://ca.unraid.net/submit/help).
The [sustained-memory plan](../spikes/SPIKE-007-sustained-memory.md) defines
synthetic acceptance independently of live-provider functionality.

## Consequences and risks

Major zero does not promise a stable API. The template cannot pull until registry
publication succeeds. Local load evidence does not establish all production
workloads. CA review and operator-installed certificates remain external steps.

## Affected documents and tests

Build identity, local CI, packaging, Compose, Unraid XML, release/deployment
guides and regression checks. No runtime budget or metadata contract changes.

## Reviewer and date

Owner's explicit requests for audit items 1, 2, 4, 5 and 6, 2026-10-05.

## Supersedes / superseded by

Extends ADR-005's public source decision to versioned binary/image packaging.
Preserves ADR-006's local CI requirement.

Normal installation defaults and the initial latest deferral are superseded
by [ADR-008](ADR-008-moving-image-tags.md); immutable artifacts and advanced
source-build pins remain in effect.
