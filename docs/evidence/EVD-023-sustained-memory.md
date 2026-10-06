# Sustained synthetic memory results

Status: Pass for measured candidate workload  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (limits unchanged)

## ID: EVD-023

SPIKE-007; audit item 5; delivered image memory acceptance.

## Source URL or fixture provenance

Invented titles, authors, recordings and padded JSON from
`spikes/MVP-001/load_upstream.py`; no catalog copies or real credentials.

## Captured date and environment

2026-10-05 local Docker host; Python runner; temporary Python 3.10 HTTPS fixture;
adapter 99:100, read-only, 256 MiB hard limit, swap disabled, GOMEMLIMIT 192 MiB.

## Version, commit or content hash

Version 0.1.0 candidate image/source fields and runner SHA-256 are in the JSON
artifact. Candidate is explicitly dirty. The final release script reruns this
experiment on the clean tagged image and uploads its own report.

## Method and reproduction steps

Follow [SPIKE-007](../spikes/SPIKE-007-sustained-memory.md). Run
`python3 spikes/MVP-001/load.py --image abs-audiobookdb:local-ci` after local CI.
Sample RSS and process high-water mark at 100 ms intervals while checking
large cold reads, eviction, fresh authorization, sustained warm traffic, slow
upstream and both upstream/mapped size failures.

## Sanitized artifact path

- [Passed candidate run](MVP-001/load-20261006T005859906791Z.json)
- [Initial port preparation failure](MVP-001/load-20261006T005450991634Z.json)
- [Initial fixture TLS startup failure](MVP-001/load-20261006T005518891180Z.json)

## Claims supported and limitations

This workload stayed under the limit without OOM, restart or leaked sentinel.
Process RSS excludes some cgroup charges; the test does not establish live
upstream latency or all deployment memory needs. A disposable bridge and
synthetic configured endpoint isolate requests; no egress firewall is claimed.

## Observed outcome

Pass: 132.614 seconds; 24 cold searches at three concurrent, each with eight
900 KiB detail bodies and six recordings. Maximum cold response 7.550 seconds.
Evicted query needed ten calls; warm hit needed one fresh auth call. Three warm
workers completed 224 searches over 60 seconds. Peak process RSS **26,243,072
bytes (25.03 MiB)**; OOM false, restarts zero. Slow response returned 504;
oversized upstream and mapped output returned 502. Health and cleanup passed.

Initial runner failures are retained: internal networks disabled published
ports, then the fixture certificate omitted loopback SAN. Both were corrected
before the successful run; failed runs had no acceptance checks and cleaned up.

## Synthetic or live classification

Local synthetic container experiment; zero live ABS/AudiobookDB traffic.

## Sanitization and redistribution notes

Evidence contains only timing/count/memory fields, hashes and synthetic failures.
Temporary certificates, containers and network were removed.
