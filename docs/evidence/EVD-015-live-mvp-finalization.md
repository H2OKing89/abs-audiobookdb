# Live MVP authorization and pipeline checks

Status: Recorded  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## ID: EVD-015

SPIKE-006; Q-002/003/005/006; selected VER-002 and VAL-002/003 subchecks.

## Source URL or fixture provenance

[Public OpenAPI](https://audiobookdb.org/openapi-public.json), [API guide](https://audiobookdb.org/docs), existing ignored key file, synthetic invalid key and the SPIKE-002 title fixture.

## Captured date and environment

2026-10-05 20:05 UTC; Python 3.14.4, direct verified HTTPS from the development machine.

## Version, commit or content hash

OpenAPI 1.0.0, SHA-256 `1377bdfff99a7775a7071fef7279c56a28bb7430d55ba365a8cfb8628d03fedf`; runner SHA-256 in linked JSON. Public default-agent retrieval first returned 403; identifying agent succeeded.

## Method and reproduction steps

Run `PYTHONDONTWRITEBYTECODE=1 python3 spikes/SPIKE-006/finalization_probe.py`. Bounded read-only probes check documented GET `/auth/session`, categories, cold title expansion and authenticated warm reuse. No key generation or real-key revocation.

## Sanitized artifact path

[Live result](SPIKE-006/finalization-20261005T200500289441Z.json).

## Claims supported and limitations

Real key accepted by `/auth/session`; invalid/missing keys rejected. Fresh authorization before every cached response now has a verified real endpoint. Twenty-three external categories contained no ISBN-named category; the unchanged schema declares ISBN metadata, not exact ISBN lookup. ISBN-only MVP lookup is deferred, not universally declared impossible.

## Observed outcome

Pass: 12 requests / 15 documented cost units overall. Cold path selected two books and expanded three releases in 1.753 seconds, seven attempts/nine cost units including auth. Warm reuse after fresh auth took 0.260 seconds and one cost unit. Six-release maximum is an enforced limit selected for MVP, not a measured six-release latency guarantee.

## Synthetic or live classification

Live API responses kept only in memory; synthetic invalid key. No actual account revocation event or production adapter/cache measured.

## Sanitization and redistribution notes

Only statuses, timings, byte sizes and counts saved. Identity payload discarded after checking nonempty ID; no account/catalog text, IDs, key values or headers archived.
