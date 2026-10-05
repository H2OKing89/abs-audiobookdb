# SPIKE-001: What does the installed ABS send and accept?

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID and status: SPIKE-001 / Partial

Planned experiment; production implementation is excluded.

## Question and hypothesis

What does the installed ABS send and accept? The published custom-provider contract can guide the installed-version probe, but runtime request/auth/deadline behavior needs separate evidence.

## Linked requirements and blocking questions

REQ-004, REQ-010; Q-001; VER-001; VAL-001/002.

## Environment and versions

Record execution UTC timestamp, runtime/tool versions, relevant source hashes and installed ABS version when available. Current public source versions are ABS provider 0.1.0 and AudiobookDB API 1.0.0; these do not identify the installed server version.

## Inputs and sanitized fixtures

ABS host and key from local development configuration; synthetic provider key SPIKE-ABS-SENTINEL; a synthetic title with two narrator variants. No library metadata updates.

## Procedure and reproduction commands

1. Run `python3 spikes/contract-probes/probe.py abs` to check HTTPS access, installed version if exposed, and authenticated read access.
2. Compare the installed-version provider implementation with SRC-003; record exact version/hash and parameter, authorization, error and timeout behavior.
   Run `node spikes/SPIKE-001/source-contract-check.js` to exercise the pinned adapter with synthetic dependencies. This subcheck has zero ABS/API requests, one public source fetch capped at 512 KiB/ten seconds, and eight bounded source check groups; it does not measure actual Axios timeouts or validate the UI.
3. On an isolated test ABS instance, configure a disposable capture provider using only the sentinel key. Search the synthetic title, return two synthetic matches, and observe display/selection without saving metadata.
4. Probe delays of 1, 5 and 11 seconds once each to bracket the client deadline. Check replacement-key forwarding and rejection of the previous synthetic key. Remove only the disposable configuration created by this spike.
Steps 2–4 require a version-matched source and isolated test setup; the initial runner does not configure providers or trigger searches.

Isolated execution: `python3 spikes/SPIKE-001/live_experiment.py --keep-for-ui`. It creates two labeled disposable containers and a dedicated bridge network, binds API ports to loopback, uses generated local admin credentials, and mounts synthetic audio/configuration under `/tmp`. It never reads development `.env` keys or touches live ABS. Thirteen local searches cover a normal response, delays 1/5/11 seconds, six HTTP errors, malformed envelope, replacement key and old-key rejection. Browser searches are budgeted separately at four attempts per browser run; incomplete preparation runs are preserved. The browser intercepts default-provider searches before selecting the local fixture. The bridge is not an egress firewall. Delay budget is 17 seconds served; total API run limit is ten minutes plus UI work. The earlier six-search cap is superseded for expanded local-only coverage. Cleanup removes only spike-created containers/network/data. The image is digest-pinned.

## Pass/fail criteria and numeric thresholds

Readiness: HTTPS and authenticated read both return 200 with JSON. Full contract pass: one captured request, both synthetic matches selectable, exact header behavior recorded without values, and a deadline bracket of at most 10 seconds. Source review alone is partial, never a runtime pass.

## Budget and stop conditions

Runner: at most 2 GETs, 10 seconds/request, 1 MiB/response, no retries. Capture phase: at most 13 searches and 17 seconds total server delay. Stop on auth, transport, or rate-limit failure; never modify the existing provider or library.

## Actual outcomes: Partial

Initial DNS failures and later same-host SSH access are retained in EVD-002/004. Live development ABS reports 2.37.1. Pinned source checks passed (EVD-006).

Disposable ABS 2.37.1 captured raw Authorization equality and GET query/author/mediaType; supplied ISBN was omitted by the interactive controller. Two synthetic matches survived. The latest 1/5/11-second tests returned at 1.006/5.010/10.004 seconds; the last returned empty results. HTTP 400/401/404/429/500/503 and malformed success also became HTTP 200 empty results (EVD-010).

Replacement-provider key forwarding worked, and the old sentinel was rejected. Browser selection of both narrator editions passed without item writes (EVD-011). Earlier selector/default-provider failures and an internal-network preparation failure are preserved. All created containers, networks and generated credentials were removed. No existing ABS settings were changed.

## Evidence IDs and paths

EVD-001/002/004/006 source/readiness findings; EVD-010 isolated integration; EVD-011 browser selection. Exact artifacts are linked from those records under `docs/evidence/SPIKE-001/`.

## Expected versus actual differences

The interactive controller forwards no ISBN/ASIN. ABS catches provider errors/timeouts as empty HTTP 200 results. Match defaults to Google Books, so the successful browser explicitly selects the fixture and intercepts unrelated searches. Dedicated bridge networking permits loopback publishing but is not an egress firewall; the failed internal-network setup is retained.

## Required planning updates

Record observed interactive contract and measured deadline; keep identifier-only routing separate. Document ABS failure masking and the default-provider UI choice. Preserve source-only limitations for sanitizer and untested version deployments.

## Affected checks and rerun results

VER-001 Pass for the isolated version-matched request/acceptance/deadline checks. VAL-001 Pass for two distinct narrator fixtures. VAL-002 Partial: sentinel forwarding/replacement verified, real upstream revocation strategy unresolved.

## Decision and next action

Use observed ten-second ABS deadline to constrain the proposed adapter budget. Reconcile ADR-002/004 and remaining identifier/authorization findings before Gate C; do not change live providers or libraries.

## Baseline 1.0 reconciliation

Private baseline disposition: contract/timeout/two-narrator criteria pass in EVD-010/011; real authorization mechanism resolved in EVD-015. Production integration remains an implementation acceptance check.
