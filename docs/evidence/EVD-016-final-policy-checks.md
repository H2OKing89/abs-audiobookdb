# Final policy race checks

Status: Recorded  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## ID: EVD-016

SPIKE-006; cache, deadline and budget policies for baseline 1.0.

## Source URL or fixture provenance

Own synthetic callback/byte fixtures in `spikes/SPIKE-006/policy/`; real authorization contract verified separately in EVD-015.

## Captured date and environment

2026-10-05 20:13 UTC; Go 1.25.10 on Linux/amd64.

## Version, commit or content hash

Module and source hashes in linked result; historical SPIKE-004 source/results remain unchanged.

## Method and reproduction steps

Run `go test -race -v ./...` inside `spikes/SPIKE-006/policy/`.

## Sanitized artifact path

[Policy result](SPIKE-006/policy-20261005T201310033877Z.json) and [transcript](SPIKE-006/policy-20261005T201310033877Z.txt).

## Claims supported and limitations

Tests cover ten attempts/twelve cost units including auth; fresh authorization before warm hits; two-key and returned-buffer isolation; invalidation generation prevents older work repopulating a rejected cache; 64 entries/four MiB payload-and-key bytes, sixty-second TTL; four upstream/eight active caps; cancellation and configured deadlines; oversized/error responses not cached. These are prototype mechanics, not production RSS or real-key revocation claims.

## Observed outcome

Seven race tests passed in 1.146 seconds; peak upstream four. Entries/bytes were bounded and expired entries swept. Real cold/warm timings remain the single EVD-015 fixture observation.

## Synthetic or live classification

Synthetic standalone Go experiment; no real API calls or credentials.

## Sanitization and redistribution notes

Invented key strings never written to test output; byte fixtures contain no real catalog/account data.
