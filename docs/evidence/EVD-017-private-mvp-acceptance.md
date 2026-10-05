# Delivered private MVP acceptance

Status: Pass for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## ID: EVD-017

Delivered implementation against planning 06; REQ-001–011; selected VER-001–009 and VAL-001–004. Gates B/C passed before production code was introduced. Public release remains deferred.

## Source URL or fixture provenance

Own Go implementation and invented SPIKE-003/MVP-001 fixtures. [Pinned API source](https://audiobookdb.org/openapi-public.json) and EVD-005/015 supply upstream contracts; actual digest-pinned ABS 2.37.1 is isolated from the live library. Operator supplied required contact, stored only in ignored local configuration.

## Captured date and environment

2026-10-05 UTC. Go 1.25.10, development Docker 29.8.2; actual Unraid 7.3.2 / Docker 29.5.3 / Compose 5.5.0 on existing proxynet. Browser: cached Playwright Chromium 1217. No Unraid VM.

## Version, commit or content hash

Final image `sha256:0ecc83262330460ec0559e3d5f53f4d77e4fb644c9fa534337637da4c1022074`, retained locally as `abs-audiobookdb:mvp-20261005` and `abs-audiobookdb:private`. Final live/integration/deployment records identify this same image. Go module/source/test/Dockerfile hashes in latest test result; runner hashes in individual records. Test-only refinements followed image trials; production code unchanged.

## Method and reproduction steps

From root: `go test -race -v ./...`, `go vet ./...`, `go build -trimpath -o bin/abs-audiobookdb ./cmd/abs-audiobookdb`, and `docker build -t abs-audiobookdb:mvp-20261005 .`. Run `python3 spikes/MVP-001/integration.py` and `python3 spikes/MVP-001/deployment.py --target <authorized-LAN-SSH-target>`. Live runner requires the ignored key/contact; its README records the bounded post-failure follow-up. Fresh API calls require a newly recorded budget; do not blindly repeat live probes. Compose base and combined host/native TLS configuration passed `config --quiet` with required variables.

## Sanitized artifact path

- [Final race result](MVP-001/tests-20261005T205136857301Z.json) and [vet result](MVP-001/vet-20261005T205136857301Z.json).
- [Final live upstream](MVP-001/live-20261005T204631504433Z.json).
- [Final delivered adapter + ABS UI](MVP-001/integration-20261005T204638674614Z.json).
- [Final actual Unraid trial](MVP-001/deployment-20261005T204638690611Z.json).
- [Independent cleanup/image inventory](MVP-001/inventory-20261005T205021879180Z.json).
- [Initial live schema failure](MVP-001/live-20261005T204318742066Z.json), [initial integration acknowledgement failure](MVP-001/integration-20261005T204117343377Z.json), and earlier successful intermediate test/deployment records in this directory remain historical.

## Claims supported and limitations

Title/author and exact-ASIN implementation, compatible edition metadata, no ISBN guessing, fresh session authorization before cached responses, scoped cache/purge, error translation, fixed budgets/bytes/deadlines/admission/pacing, health and shutdown. Synthetic race tests verify resource mechanics; actual runtime RSS under sustained load was not measured. No service latency guarantee follows one fixture. Real exact ASIN upstream behavior was verified earlier in EVD-005; delivered exact-ASIN happy/unknown/mismatched identity paths are synthetic tests, not a new real-ASIN call.

## Observed outcome

Pass: final production race suite and vet. Live title search returned three matches in 1.668 seconds cold and 0.229 seconds warm; invalid key on the warm query returned 401 in 0.263 seconds. Four adapter searches across the initial failure and follow-up stayed within eighteen documented cost units: prior auth+search cost four inferred from deterministic failing source path, followed by fourteen-unit conservative ceiling. No measured quota-accounting claim.

Isolated ABS rendered/selected Narrator A, Narrator B, Full Cast and a French recording; zero item writes. Its cards omit language/subtitle, so duplicate-narrator language is inspected after selection. Actual Unraid tested 99:100, 256 MiB limit, shared-network HTTP/native TLS, loopback HTTP, and HTTP/HTTPS LAN publication reachable from development machine. Bad trust/SAN and unreadable private key correctly failed. Both processes stopped exit zero in 0.625 seconds. Independent inventory found zero temporary containers/images/directories; the already-removed transfer tag explains a nonzero removal entry.

Failures retained: the initial Go rate test wrongly expected the first key in its second-key fixture; corrected assertion passed (no exact initial source/transcript archived). Initial integration helper attempted JSON decoding of ABS's empty scan acknowledgement; corrected helper passed. Initial real search incorrectly decoded flattened search genres/tags/series as detail objects; separate search-hit DTO and regression fixture fixed the 502. Unraid and isolated integration were rerun with the final image.

## Synthetic or live classification

Production Go + synthetic TLS API/ABS UI fixtures; separately, real read-only AudiobookDB calls and disposable deployment on the actual live Unraid host. No existing ABS/Unraid project configured or live library changed. No real key revoked or upstream/account write performed.

## Sanitization and redistribution notes

Real responses remained in memory. Records contain outcomes/timing/counts/hashes, not catalog/account payloads, contact, headers, keys or LAN host. Development .env/secrets excluded from image. Source/evidence secret scan and relative Markdown link check complete after reconciliation. Existing AGENTS.md preserved. Public distribution/provider clarification remains Q-008.
