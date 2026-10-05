# Documentation

Status: Current MVP and publication documentation  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

Start with the [project README](../README.md) for installation and
[deployment](deployment.md) for configuration and Unraid Compose Manager.

## Design and planning

- [Scope and requirements](planning/01-scope-requirements.md)
- [Contracts and mapping](planning/02-contracts-mapping.md)
- [Architecture and operations](planning/03-architecture-operations.md)
- [Verification and validation](planning/04-verification-validation.md)
- [Open questions and risks](planning/05-questions-risks.md)
- [MVP plan](planning/06-mvp-plan.md)
- [Sources and evidence](planning/07-source-register.md)
- [Phase gates](planning/08-phase-gates.md)

## Decisions and verification

- [Decision log](decisions/README.md)
- [Spike register](spikes/README.md)
- [Delivered MVP acceptance](evidence/EVD-017-private-mvp-acceptance.md)
- [Public GitHub preparation](evidence/EVD-018-github-readiness.md)
- [Publication privacy review](evidence/EVD-019-publication-history-review.md)
- [Change log](CHANGELOG.md)
- [Reusable templates](templates/README.md)

## Maintaining records

Review the scope and contracts before changing behavior. Update affected
decisions and checks, preserve sanitized evidence and actual outcomes, and
follow the phase gates for contract changes. A blocked or unrun check is never
a pass. Link evidence to the exact claim it supports and record versions,
hashes, and test dates.

Allocate stable IDs (`REQ`, `VER`, `VAL`, `Q`, `RISK`, `ADR`, `SPIKE`, `SRC`,
`EVD`, `CHANGE`); never reuse them. Copy project-local templates for new records.
Keep experiments under `spikes/`, production code under `cmd/` and `internal/`,
and credentials outside Git. See [contributor guidance](../CONTRIBUTING.md).
