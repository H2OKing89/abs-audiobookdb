# Bounds and credential isolation

Status: Recorded  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-012

SPIKE evidence; linked checks remain limited to the classification below.

## Source URL or fixture provenance

Local Go httptest servers, synthetic keys and tenant-specific fixtures in SPIKE-004.

## Captured date and environment

2026-10-05 UTC; exact Go version and recorded timestamp are in the linked result.

## Version, commit or content hash

SHA-256 values of module, implementation and tests are recorded with race-test evidence.

## Method and reproduction steps

Run `python3 spikes/SPIKE-004/run_experiment.py`. It executes `go test -race -v ./...`, caps runtime/output and scans output for both synthetic keys before saving.

## Sanitized artifact path

[Corrected race result](SPIKE-004/bounds-20261005T180705662455Z.json) and [transcript](SPIKE-004/race-20261005T180705662455Z.txt); [failed attempt](SPIKE-004/bounds-20261005T180510305224Z.json) and [failed transcript](SPIKE-004/race-20261005T180510305224Z.txt).

## Claims supported and limitations

Tests demonstrate two-key cache/flight partitioning, warm-cache rejection after synthetic revocation, bounded concurrency/cache entries, cancellation ownership, safe errors, Retry-After and failure refetch. The synthetic `/validate` endpoint has no established upstream equivalent. Byte-level memory and real cold/warm latency remain unmeasured.

## Observed outcome

Initial run passed. Review corrected a failure-channel issue; captured rerun then failed because the intended second waiter was not observed joining. Synchronization had polled any flight and relied on short fixture timing. Added a barrier for the intended shared flight; corrected rerun passed in 2.410 seconds. Thirty-two interleaved requests made two lookup/eight detail calls, peak concurrency four, elapsed 45.007 ms. Both failed and successful transcripts are retained; no live upstream calls.

## Synthetic or live classification

Synthetic Go prototype only; delivered production implementation requires its own verification.

## Sanitization and redistribution notes

Error fixtures intentionally include synthetic keys in upstream bodies; no sentinel occurs in archived output. No real credentials loaded.
