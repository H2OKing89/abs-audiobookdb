# Run CI locally

Status: Accepted  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID and status: ADR-006 / Accepted

## Context and linked requirements

After the first source push, the owner requires local CI because GitHub-hosted
execution is unavailable. Publication and MIT licensing remain authorized.

## Decision question

How should contributors run the repository's existing verification checks?

## Options and tradeoffs

Hosted Actions cannot meet the owner's requirement. A local script preserves
the same checks without provisioning a persistent runner or deployment.

## Decision and rationale

Use `./scripts/ci.sh` for repository syntax/links, formatting, module consistency,
race tests, vet, binary build and container health/shutdown. Docker is included
by default; `--no-docker` explicitly reports skipped container checks.
Disable GitHub Actions and remove the hosted workflow and Dependabot schedules.
Keep GitHub issue and PR templates. Contributors report local outcomes in PRs.

## Evidence and source versions

[EVD-020](../evidence/EVD-020-local-ci.md) records local runner execution and
GitHub Actions settings verification. Earlier hosted-CI preparation remains
historical evidence.

## Consequences and risks

Contributors need local tooling. GitHub supplies no automated check result;
reviewers must read the reported validation. No API credentials or live service
access are required. The script removes only its temporary test container.

## Affected documents and tests

Local scripts, README, CONTRIBUTING, PR template, decisions and changelog.
Adapter runtime and deployment configuration are unchanged.

## Reviewer and date

Owner's explicit local-CI instruction, 2026-10-05.

## Supersedes / superseded by

Supersedes ADR-005's hosted-CI implementation choice only. Source licensing,
read-only behavior and preserved acceptance evidence remain unchanged.
