# Synthetic mapping fixture preparation

Status: Prepared  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-008

SPIKE-003 fixture preparation only.

## Source URL or fixture provenance

All values invented locally. Field shapes follow OpenAPI 1.0.0 and EVD-005/006 source findings; no live catalog payload was copied. Schema hash is embedded in the fixture file.

## Captured date and environment

2026-10-05 UTC; local JSON authoring. No upstream calls or ABS settings changes.

## Version, commit or content hash

OpenAPI SHA-256: `1377bdfff99a7775a7071fef7279c56a28bb7430d55ba365a8cfb8628d03fedf`. Prepared fixture SHA-256: `c6cad1001f58b3ecff377a958508e718fe400a51ae6564635a3e871fcc697d72`. Record a fresh hash at each future execution because scenarios may evolve.

## Method and reproduction steps

Inspect `python3 -m json.tool spikes/SPIKE-003/fixtures.json`. Review the linked expected properties before implementing an experimental mapper. The experiment command and rounding/fallback/ordering policies must be specified before claiming results.

## Sanitized artifact path

[Fixtures](../../spikes/SPIKE-003/fixtures.json) and [reproduction notes](../../spikes/SPIKE-003/README.md).

## Claims supported and limitations

Eleven scenarios cover every listed verification-matrix category plus duplicate release IDs. They include two recordings, full cast, contributor multiplicity, zero/fractional series, absent fields, unknown identifiers, alternate language and different ISBN editions. The ISBN-selection scenario is conditional; it does not establish upstream lookup support. Expected properties are draft acceptance criteria, not tested output.

## Observed outcome

Fixture JSON prepared and structurally checked. No mapping execution or UI acceptance occurred; VER-003/004 and VAL-001 remain Not run.

## Synthetic or live classification

Entirely synthetic inputs and expectations.

## Sanitization and redistribution notes

Reserved `.invalid` cover URLs, invented names and local synthetic IDs only. No real descriptions, contributor names, IDs, credentials or artwork are redistributed.
