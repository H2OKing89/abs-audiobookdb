# SPIKE-004: Can the request path remain bounded and credential-isolated?

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID and status: SPIKE-004 / Partial

Experimental findings recorded; production implementation is excluded.

## Question and hypothesis

Can the request path remain bounded and credential-isolated? Synthetic transport and two sentinel keys can expose isolation/cancellation defects without consuming live API quota.

## Linked requirements and blocking questions

REQ-008/009; Q-005/006; VER-005/006/007/008; VAL-002/003.

## Environment and versions

Go 1.25.10, Linux/amd64; module and source hashes plus exact UTC timestamps are in EVD-012. Local httptest fixtures model mechanics only. ABS deadline is measured separately in EVD-010 using 2.37.1.

## Inputs and sanitized fixtures

Local HTTP fixtures for 400/401/404/429/500/503, Retry-After, malformed JSON, slow responses and cancellation; two synthetic keys with intentionally different responses.

## Procedure and reproduction commands

1. Use provisional contract/mapping rules in the isolated Go httptest experiment under `spikes/SPIKE-004/`; record Go version and exact commands.
   Execute `go test -race -v ./...` inside `spikes/SPIKE-004/`. Provisional module limits are four concurrent requests, four cache entries, one-second TTL, two HTTP attempts and a two-second shared-work deadline; all callers canceling stops shared work, while one canceled waiter leaves other waiters intact. Every cache hit has synthetic fresh authorization validation. The fixture `/validate` route is not claimed to exist in AudiobookDB; live revocation and validation cost remain separate open questions. The measured isolated ABS timeout will be reconciled independently.
2. Run cold/warm paths and interleaved two-key cache/singleflight requests, revocation, cancellation and each error fixture.
3. Run `go test -race ./...` from the experiment module; scan saved output for sentinel secrets.
4. Measure calls, latency, maximum concurrency and memory; propose final budgets from results, not these experiment caps.

## Pass/fail criteria and numeric thresholds

Zero cross-key responses, races or sentinel leaks; cancellation stops fixture work within 500 ms; at most 4 concurrent calls and 10 returned matches. All listed error cases have explicit expected/actual outcomes. End-to-end latency must fit the measured ABS deadline; memory and retry thresholds require a documented decision before final pass.

## Budget and stop conditions

Zero live upstream calls; at most 100 local requests/case and 120 seconds/case, 1 MiB fixture responses. Experimental retry cap 2 and request cap 10 are temporary measurement bounds. Stop on isolation failure or missing ABS deadline.

## Actual outcomes: Partial

Local Go race tests exercised 32 interleaved two-key requests, warm-cache synthetic revocation, bounded concurrency/cache entries, HTTP failures, Retry-After, malformed/oversized bodies, cancellation ownership and transient-failure refetch. Initial run passed; captured rerun exposed a timing-dependent shared-waiter test failure. The fixture now blocks shared work until the intended flight has both waiters, preserving the failed transcript and recording the corrected rerun (EVD-012).

## Evidence IDs and paths

EVD-012; `docs/evidence/SPIKE-004/bounds-*.json` and associated `race-*.txt` contain exact outcomes, source hashes, Go version, counts and timing. Use `python3 spikes/SPIKE-004/run_experiment.py` to capture a bounded reproduction.

## Expected versus actual differences

Fresh authorization before cache access requires a synthetic `/validate` call for each caller, separate from shared expansion work. No such real upstream endpoint is assumed. Four cache entries demonstrate entry bounds, not a final byte-level memory cap. Fixture latency cannot establish production cold/warm latency.

## Required planning updates

ADR-002 proposes credential partitioning and cancellation ownership but leaves real authorization validation, total cost/deadline and memory budgets unresolved. Reconcile with ABS measured ten-second timeout; final request budgets must include authorization and retries.

## Affected checks and rerun results

VER-005–008 pass for the corrected synthetic prototype only; failed shared-waiter attempt retained. VAL-002/003 Partial: real revocation, authorization cost and end-to-end upstream latency remain unverified.

## Decision and next action

Select an upstream authorization-validation method and final budgets before Gate C; do not treat synthetic revocation or local timings as real API acceptance.

## Baseline 1.0 reconciliation

Private baseline disposition: the earlier fake /validate/two-attempt/shared-flight experiment remains historical. Accepted ADR-002 uses verified /auth/session, bounded serialized results and no cross-request flights/internal retries. EVD-015/016 resolves policy/budget questions; production RSS and full transport tests remain implementation acceptance.
