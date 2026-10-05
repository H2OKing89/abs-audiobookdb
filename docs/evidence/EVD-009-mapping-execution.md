# Synthetic edition mapping

Status: Recorded  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-009

SPIKE evidence; linked checks remain limited to the classification below.

## Source URL or fixture provenance

Invented fixtures from SPIKE-003; no captured catalog payloads.

## Captured date and environment

2026-10-05 18:05 UTC on the local development machine; Python 3.

## Version, commit or content hash

Fixture and experiment SHA-256 values are in the linked result. ABS target 2.37.1; upstream schema 1.0.0.

## Method and reproduction steps

Run `python3 spikes/SPIKE-003/experiment.py`. Eleven scenarios execute three times each; explicit known-field values, fallback, rounding and unknown identifiers are checked.

## Sanitized artifact path

[Mapping result](SPIKE-003/mapping-20261005T180506796865Z.json); [earlier result](SPIKE-003/mapping-20261005T173721481143Z.json).

## Claims supported and limitations

Preserves two recordings, full cast, contributor order, language variants, fractional/string-zero series, missing fields and release identity. ISBN is fixture filtering only, not proof of an upstream resolver. Proposed mapping rules need ADR-004 review.

## Observed outcome

Pass for all eleven synthetic scenarios and additional boundaries. A whitespace-only release title exposed a fallback gap during review; corrected and rerun successfully.

## Synthetic or live classification

Synthetic standalone experiment; no live network, production adapter or UI acceptance claim.

## Sanitization and redistribution notes

Only invented data and safe outcome summaries saved; no credentials or upstream text redistributed.
