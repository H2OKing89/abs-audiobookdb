# SPIKE-003: Can mapping preserve distinct recordings and edge cases?

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID and status: SPIKE-003 / Partial

Experimental findings recorded; production implementation is excluded.

## Question and hypothesis

Can mapping preserve distinct recordings and edge cases? One match per release preserves narrator/language/identifier identity without silently substituting editions.

## Linked requirements and blocking questions

REQ-007/010; Q-002/004; VER-003/004; VAL-001.

## Environment and versions

Python 3.14.4 on the development machine; execution UTC timestamps and fixture/source hashes in EVD-009. Reviewed upstream schema 1.0.0 and ABS provider schema 0.1.0; rendered integration uses digest-pinned ABS 2.37.1 (EVD-011).

## Inputs and sanitized fixtures

The fixture categories in the verification matrix; two releases of one work; synthetic missing/null fields, fractional series and unknown identifiers. Obtain minimal live shapes from SPIKE-002, without archiving catalog text or cover art.

## Procedure and reproduction commands

1. After SPIKE-001/002 resolve core schemas, create synthetic fixtures for every matrix category.
2. Build an isolated mapping experiment under `spikes/SPIKE-003/`; document its actual command before execution.
   Run `python3 spikes/SPIKE-003/experiment.py`. Provisional experiment rules: release title/subtitle override nonempty book values; book Author and release Narrator names retain order, deduplicated and joined with comma-space; release year falls back to book copyright; release image falls back to book cover, with `/large.jpg`; runtime floors numeric milliseconds/seconds to integer minutes; series position label falls back to ordinal and remains a string; missing optional data is omitted. Exact fixture identifiers select only their own release; no title fallback. These are investigation choices, not finalized production decisions.
3. Compare every proposed ABS field, edition identity, tie ordering, units and missing-value behavior.
4. Exercise the two-release fixture in the isolated ABS setup; record UI selection separately.

## Pass/fail criteria and numeric thresholds

All listed fixture categories and mapping rows have explicit outcomes; zero duplicate release IDs or silent identifier substitutions; identical input/order produces identical output on 3 runs. UI acceptance requires selecting both editions without writing library metadata.

## Budget and stop conditions

Zero live upstream calls by default; any additional fixture collection gets a separately documented budget of at most 6 reads/12 cost units. At most 3 mapping runs per fixture. Stop if schema or redistribution permission is unresolved.

## Actual outcomes: Partial

Eleven invented scenarios passed on three deterministic runs each, with explicit supported-field values, missing-field omissions, duplicate-release elimination, unknown-identifier rejection, fallback, duration rounding and string series labels (EVD-009). Review found a whitespace-only title fallback gap; corrected and rerun. Both narrator variants were selectable in isolated ABS without metadata writes (EVD-011). Exact ISBN upstream support and same-narrator language UI distinctions remain unverified.

## Evidence IDs and paths

EVD-008 original fixture preparation; EVD-009 mapping execution; EVD-011 rendered narrator selection. Latest mapping result: `docs/evidence/SPIKE-003/mapping-20261005T180506796865Z.json`.

## Expected versus actual differences

Conditional ISBN fixture selection passes but does not establish an upstream ISBN resolver. ABS removes extra release IDs, so identity is retained only internally; supported narrator/language/identifier metadata supplies user-visible distinctions.

## Required planning updates

Review provisional field fallbacks, contributor ordering, integer-minute rounding and deterministic ties in ADR-004. Keep exact ISBN blocked until supported lookup evidence or an explicit scope decision exists.

## Affected checks and rerun results

VER-003 Pass for the synthetic mapped-field matrix; delivered implementation requires revalidation. VER-004 Partial: exact fixture filtering and live ASIN sample pass, upstream ISBN unresolved. VAL-001 Pass for the two-narrator fixture; language-only/full-cast UI coverage remains outstanding.

## Decision and next action

Review ADR-004 and resolve Q-002 without silent title fallback. Add targeted UI cases for editions that share narrators before treating every edition distinction as validated.

## Baseline 1.0 reconciliation

Private baseline disposition: accepted ADR-004 mapping/selection rules supported by EVD-009/011/015. Exact ISBN-only lookup deferred; language/full-cast delivered UI checks remain implementation acceptance.
