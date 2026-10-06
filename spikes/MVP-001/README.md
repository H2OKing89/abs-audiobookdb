# Delivered private MVP acceptance

Status: Pass  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

Implements acceptance from [the finalized plan](../../docs/planning/06-mvp-plan.md).
Fixture code is development tooling; no ABS host/key enters the production image.

Reproduce production checks with `go test -race -v ./...` and
`go vet ./...` from the root. Build with
`docker build -t abs-audiobookdb:mvp-20261005 .`.

`python3 spikes/MVP-001/integration.py` creates isolated TLS upstream,
delivered adapter and ABS containers, checks cache reauthorization/rejection,
and exercises the rendered match UI with invented records. It deletes its
containers/network/certificates afterward. No live ABS library is used.

The UI check resolves `playwright` and its installed Chromium by default.
Set `SPIKE_PLAYWRIGHT_PACKAGE` to an alternate package path and
`SPIKE_BROWSER_EXECUTABLE` to an alternate browser executable when needed.
Temporary context files follow Python's `TMPDIR` setting.

`python3 spikes/MVP-001/deployment.py --target root@<unraid-lan-address>` transfers
the built image into a disposable target project on existing `proxynet`,
tests HTTP/native TLS and explicit loopback/LAN binding, then removes only
its project/image/temporary directory. No reverse proxy is involved.

`python3 spikes/MVP-001/live_probe.py` makes at most four local adapter
searches, at most twenty documented upstream cost units in total: title cold,
title warm, exact known ASIN and synthetic invalid key against the warm query.
It stops on unexpected authentication/rate/transport failure. No retries,
key revocation, account writes or saved catalog/account content. Requires
contact plus the existing ignored development key file. No live API activity
occurs in tests/integration/deployment fixtures.

Store sanitized actual results under `docs/evidence/MVP-001/`; EVD-017
records delivered implementation outcomes and retained failures.

`python3 spikes/MVP-001/load.py --image abs-audiobookdb:local-ci` reproduces
[SPIKE-007](../../docs/spikes/SPIKE-007-sustained-memory.md): large-response/cache
turnover, three-worker sustained searches, RSS sampling and failure bounds.
It uses an isolated synthetic upstream and no live API credentials.

The first live search exposed flattened search genres/tags/series being decoded
as detail objects; a distinct search-hit DTO and regression fixture corrected
it. The initial auth+search used four documented units (inferred from the
failed source path). The three-request follow-up used
`--remaining-after-schema-failure` to skip a further real ASIN call: at most
four searches and eighteen cost units across both attempts. Exact ASIN is
verified in production synthetic tests and earlier upstream evidence.
