# Bounds and credential isolation experiment

Plan: [SPIKE-004](../../docs/spikes/SPIKE-004-bounds-isolation.md). This standalone Go module models a request path against local `httptest` servers. It is not production adapter code and never reads `.env` or calls AudiobookDB.

```sh
cd spikes/SPIKE-004
go test -race -v ./...
```

Tests exercise interleaved two-key cache/singleflight requests, revocation, cancellation ownership, four concurrent upstream calls, four cache entries, ten-call per-work budget, one-second experimental cache TTL, two request attempts, Retry-After, HTTP failures, malformed/oversized responses and safe errors. At most four fixture details are expanded per search.

Every request revalidates authorization before serving cached data. The fixture's `/validate` route is synthetic: no upstream equivalent is assumed. A real authorized validation strategy and its quota cost remain an open design dependency. This experiment can demonstrate isolation mechanics and their cost tradeoff, but cannot prove AudiobookDB revocation detection, full production memory limits or real cold/warm latency.

Run `python3 spikes/SPIKE-004/run_experiment.py` from the repository root to capture race-test output, SHA-256 values and the sentinel scan as evidence. The canceled-waiter test uses a fixture barrier to ensure both callers join the intended flight before cancellation. Proposed cache/flight and retry rules require ADR-002 review before finalization. Production tests must be rerun against the delivered implementation after Gate C.
