# Publication history and README review

Status: Pass for local publication preparation  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-019

Expanded privacy review before the first public source push; ADR-005.

## Source URL or fixture provenance

Local Git objects, current source and ignored development configuration.
Read-only GitHub repository/ref and authenticated-owner metadata checks.
The owner requested a professional README and chose the simplest history
cleanup option after being offered a clean initial commit or sanitized history.

## Captured date and environment

2026-10-05, Linux development checkout. Starting public branch tip f981092;
three commits reachable from main. Two local agent checkpoint refs contain
additional experiment snapshots and are outside the branch publication path.
The public GitHub repository existed but had no branches or tags.

## Version, commit or content hash

Original main history: dbd9668, fcaa4d7, f981092. Original Git objects were saved
in a verified, ignored local bundle before replacing main with a parentless
publication commit. Older evidence hashes and commit references continue to
identify their actual historical inputs, retained in that backup.

## Method and reproduction steps

Enumerate historical blobs with `git rev-list --objects main` and
`git rev-list --objects --all`, reading blobs with `git cat-file`. Compare
configured credentials, ABS host, contact and original author emails in memory;
report only paths and counts. Check common token/private-key markers and
private IP/checkout references. Review author/committer attribution separately.

Use `git ls-remote --heads --tags origin` to check whether history is already
published. Save and verify the original history with `git bundle create` and
`git bundle verify`. Build a new initial commit from the reviewed current tree;
use the authenticated owner's GitHub no-reply email for author and committer.
Check the new main history and run
`python3 .github/scripts/check_repository.py` plus `git diff --check`.
Compare runtime, AGENTS.md and existing evidence blobs with the original tip.

## Sanitized artifact path

[README](../../README.md), [documentation index](../README.md), and this record.
The original bundle is stored under ignored `secrets/history-backups/` with
owner-only permissions. It is a local recovery artifact, excluded from Git and
the Docker build context; local checkpoint refs are not pushed.

## Claims supported and limitations

No configured API key, live ABS host or contact was detected in historical
file contents. The broader review found three machine-specific references in
main's old blobs: an Unraid LAN SSH target, a personal browser-cache path and a
development SSH/checkout example. The three original commits also used a
personal email for attribution. These findings expand EVD-018's configured-value
review; they do not indicate leaked API credentials.

The new publication history contains the current generic examples and no
original private attribution. This review covers known values and common
patterns; it cannot rule out every unknown secret. Original local checkpoint
objects and the recovery bundle retain history and must remain local.

## Observed outcome

Pass: 200 original historical blobs reviewed, including 186 reachable from the
original main; three machine-reference blobs on main and six across all refs.
No configured credential or common token/private-key marker detected.
The original-history bundle verified successfully, contains the original main
and checkpoint refs, and is ignored with permissions 0600 in a 0700 directory.

The new main contains one parentless commit; all 173 reachable file blobs and
the commit metadata passed the expanded publication scan. Both author and
committer use the owner's GitHub no-reply address; configuration is repository
local. Credential, certificate and build-output paths are absent from the tree.
Repository checks pass for 176 files and 124 relative links, including
Python/JavaScript syntax and JSON validation; `git diff --check` passes.
Comparing against original f981092 changes only README, the new docs index,
this evidence record and the changelog. Runtime, AGENTS.md and all existing
evidence artifacts are unchanged. Remote branches and tags remain empty.

The README now leads with supported features, Docker setup, ABS provider
configuration, local Go usage, tested status and licensing. Historical planning
navigation remains available in the documentation index. The duplicate
CHANGE-023 publication entry is corrected to CHANGE-024; no IDs are reused.

## Synthetic or live classification

Offline Git/source/documentation checks and read-only GitHub metadata queries.
No live AudiobookDB or ABS requests, deployment or source push.

## Sanitization and redistribution notes

Runtime code and historical test artifacts are unchanged. Existing failures
remain recorded; no runtime tests are represented as rerun for this documentation
change. GitHub-hosted CI execution remains unobserved until source is pushed.
