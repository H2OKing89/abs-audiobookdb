# Isolated ABS integration

Status: Recorded  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-010

SPIKE evidence; linked checks remain limited to the classification below.

## Source URL or fixture provenance

Disposable ABS and locally generated provider/audio fixtures; real development settings are excluded.

## Captured date and environment

2026-10-05 18:00 UTC; local Docker 29.8.2, ABS 2.37.1.

## Version, commit or content hash

ABS image digest `sha256:581d68b2a6fc7ebf58d81c878a9f387cbbc0d88ac9d37b298b9cee10168af85b`.

## Method and reproduction steps

Run `python3 spikes/SPIKE-001/live_experiment.py`; thirteen bounded local searches. Add `--keep-for-ui` only for browser testing; send a line to complete cleanup.

## Sanitized artifact path

[Latest integration](SPIKE-001/integration-20261005T180032628585Z.json); [initial API/browser lab](SPIKE-001/integration-20261005T175901724340Z.json); [failed internal-network preparation](SPIKE-001/integration-20261005T175936724499Z.json).

## Claims supported and limitations

Actual raw Authorization forwarding and GET query/author/mediaType observed. Supplied ISBN was not forwarded by the interactive controller. Delays 1/5 seconds return matches; delay 11 stops at 10.004 seconds. Provider errors and malformed envelopes become HTTP 200 empty results in ABS.

## Observed outcome

Pass, including replacement-provider key forwarding and previous-key rejection. Rotation is modeled by creating a replacement ABS provider; no real AudiobookDB revocation claim. Failed internal-network preparation is preserved; all created resources were cleaned up.

## Synthetic or live classification

Live isolated ABS with synthetic provider, credentials and data; not the existing ABS deployment or upstream API.

## Sanitization and redistribution notes

Captures store header equality booleans, not values. Generated password/token/sentinels absent from saved results and checked ABS logs. Dedicated bridge is not an egress firewall.
