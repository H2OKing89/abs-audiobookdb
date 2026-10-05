# Release mapping and bounded identifier scope

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## ID and status: ADR-004 / Accepted for private MVP

Exact ISBN lookup is explicitly outside initial implementation, while release ISBN metadata remains mapped.

## Context and linked requirements

REQ-007/010; Q-002/003/004. ABS interactive calls send title/author, not ISBN/ASIN fields.

## Decision question

Which identifiers and mapping rules can be implemented from verified contracts?

## Options and tradeoffs

Guessing ISBN routes or substituting titles can select the wrong edition. One work-level match collapses distinct recordings. Bounded release expansion retains identity without fetching whole catalogs.

## Decision and rationale

Support title/author and exact Audible ASIN via declared resolver and matchedReleaseId; missing matchedReleaseId is an upstream fault. Explicit or recognizable ISBN-only input returns unsupported-input 400, with no silent title fallback. Copy available release ISBN as metadata. One match per selected release; deduplicate only identical release IDs. Select at most two book candidates and six release finalists, round-robin across books; stable exact-title priority and upstream order on ties. Preserve narrator/language; keep IDs internally. Release nonempty title/subtitle overrides book; ordered unique contributors; release year/image falls back to book; runtime floors numeric units to minutes; series labels remain strings; missing optional fields omitted.

## Evidence and source versions

EVD-005 known/unknown ASIN; EVD-007/015 unchanged exact-ISBN contract gap; EVD-009 eleven mapping scenarios; EVD-011 two-narrator UI; EVD-015 bounded live expansion.

## Consequences and risks

Returns selected candidates, not every recording in the catalog. Up to six returned matches in this initial path (ten is the outer envelope cap). Any failed selected read aborts with an error; do not return silently incomplete results. Resolver 404 alone maps to an empty match result. Same-narrator/language UI cases require production acceptance; do not invent identifiers or edit upstream data.

## Affected documents and tests

Contracts; SPIKE-002/003/006; VER-003/004; VAL-001; production mapper/resolver/budget fixtures.

## Reviewer and date

Codex technical review under user finalization instruction, 2026-10-05.

## Supersedes / superseded by

Revises this record’s proposed ISBN/ranking rules; older conditional fixtures retained.
