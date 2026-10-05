# MVP finalization experiment

Plan: [SPIKE-006](../../docs/spikes/SPIKE-006-mvp-finalization.md).

```sh
python3 spikes/SPIKE-006/finalization_probe.py
```

Uses the existing development-only dotenv parser/key-file loader; performs only documented read endpoints and read-only POST search. Account and catalog payloads remain in transient memory. Invalid/missing credentials are deliberate negative checks, with no real-key revocation. Responses, time, attempts and documented cost are bounded before calls. Logs/evidence retain outcomes and counts only.

Cold expansion includes fresh authentication, one search, at most two book reads and six release reads. Warm reuse performs fresh authentication before touching transient data. This does not simulate full production server/cache behavior or an actual account revocation event. Synthetic policy checks are recorded separately.

Final-policy reproduction:

```sh
cd spikes/SPIKE-006/policy
go test -race -v ./...
```

Seven synthetic tests verify combined caps, fresh authorization ordering, byte/entry/TTL cache bounds, isolated buffers, rejection-generation protection and concurrency/cancellation. Live session validation is separate EVD-015 evidence. These experiments do not establish production RSS or an actual real-key revocation event.
