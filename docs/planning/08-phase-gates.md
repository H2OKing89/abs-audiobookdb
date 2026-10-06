# Phase gates

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Gate A — planning ready for spikes

- [x] Scope reviewed; proposed requirements accepted as provisional spike criteria; existing deferrals retained.
- [x] Contracts, mapping and uncertainty inventory complete for investigation.
- [x] Spikes have questions, procedures, fixtures and pass/fail criteria.
- [x] Each blocking question assigned a verification path.

See the [Gate A review](../reviews/gate-a-2026-10-05.md). Design acceptance and production authorization remain subject to Gate C.

## Gate B — spike findings reconciled

- [x] All required spikes executed or explicitly scoped out with rationale.
- [x] Actual outcomes and sanitized evidence recorded.
- [x] Differences update requirements, contracts, architecture and tests.
- [x] Affected checks rerun; contradictory claims resolved.
- [x] Decisions record rejected alternatives and consequences.

## Gate C — planning finalized; MVP can start

- [x] Gates A and B passed.
- [x] No unresolved blocking contract, security or deployment questions.
- [x] Measurable acceptance criteria and request budgets fixed.
- [x] MVP scope and sequence agreed.
- [x] Baseline version, date, reviewed document list and decision recorded below.

## Gate record

Gate A Pass for investigation; Gate B and Gate C Pass for private MVP baseline 1.0. See the [scoped technical review](../reviews/gate-b-c-private-2026-10-05.md). User authorization: “do it” after the proposal to resolve remaining questions and finalize the MVP plan. No external provider approval or public-ready status is represented.

Baseline version: 1.0 (private MVP)  
Review date: 2026-10-05  
Reviewer: Codex (technical review)  
Evidence and decisions: EVD-004–016; ADR-001–004  
Deferred items and rationale: exact ISBN-only lookup unsupported by verified contract; cross-request flights deferred; Q-008 provider/public-distribution applicability remains a separate release gate. See planning 06 for full scope and unrun implementation acceptance.

If a finalized contract changes, reopen affected gates and increment the baseline before implementing the changed behavior.

## Public source preparation

ADR-005 records explicit owner authorization for public GitHub source and MIT,
superseding the earlier blanket source-publication deferral. EVD-018 records
local checks. The runtime contract and completed private Gate C review remain
baseline 1.0; no upstream/catalog redistribution or provider approval implied.

## Versioned distribution authorization

ADR-007 records owner-authorized executable/image packaging, local acceptance
and Compose/Unraid support. EVD-025 records published v0.1.0 and actual deployment.
Runtime baseline 1.0 is unchanged; FIFO pacing fixes starvation within existing
limits. Public registry verification passed in EVD-029; CA listing remains
an unfinished submission/review step. Upstream terms applicability and provider
approval are not represented as resolved.
