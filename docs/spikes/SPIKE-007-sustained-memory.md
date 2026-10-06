# Sustained adapter memory and large-response verification

Status: Ready for isolated execution  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (limits unchanged)

## ID: SPIKE-007

RISK-003; owner requests sustained-load validation before the first versioned release.

## Question and scope

Does the delivered image remain healthy below its 256 MiB memory limit during
large cold responses, cache turnover, sustained warm searches and upstream failures?
Use only invented local fixtures on a disposable Docker bridge; live API budget is zero.

## Method and reproduction

Build the candidate with `./scripts/ci.sh`, then run
`python3 spikes/MVP-001/load.py --image abs-audiobookdb:local-ci`.
Requires Docker, Python 3, OpenSSL, and readable host `/proc` process statistics.
The fixture uses the existing Python 3.10 slim image; it creates TLS certificates,
two temporary containers and a bridge network, and removes them afterward.
Host-facing fixture ports bind only loopback. The adapter's upstream is the
synthetic TLS server; this is endpoint isolation, not an egress firewall.

Exercise 24 cold queries, three concurrently, with eight 900 KiB detail responses
and six mapped recordings per query. Confirm cache eviction by refetch counts
and fresh authorization on a warm hit. Run three warm workers for 60 seconds;
then check slow upstream, oversized upstream and oversized mapped output failures.
Sample process RSS/high-water mark every 100 ms; check health, OOM and restart state.

## Pass/fail and stop conditions

All selected cold/warm results must be complete, below the eight-second deadline
with 0.5-second measurement tolerance. Expected slow/size failures must return
504/502; unexpected status, missing measurement, OOM, restart, leaked sentinel
or failed cleanup is a failure or incomplete result. Observe RSS below 256 MiB.
Stop on the first unexpected result. Preserve failures and sanitized JSON evidence.

## Results and limits

Execution records belong in `docs/evidence/MVP-001/load-*.json`; EVD-023 will
summarize results. Synthetic observations do not guarantee live latency or RAM
use, and process RSS does not include every cgroup memory charge.
