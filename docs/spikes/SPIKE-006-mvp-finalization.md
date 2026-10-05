# SPIKE-006: Can verified authorization and bounded reads close MVP planning?

Status: Pass  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID and status: SPIKE-006 / Pass

Investigative code only; no production adapter or account changes.

## Question and hypothesis

Can documented GET `/auth/session` reject invalid/missing API keys before cached data is served, and can bounded title expansion fit below ABS's measured ten-second deadline?

## Linked requirements and blocking questions

REQ-004/007/008/009/010; Q-002/003/005/006/008/009; VER-002/004/006/007/008; VAL-002/003.

## Environment and versions

Reviewed OpenAPI 1.0.0, SHA-256 `1377bdfff99a7775a7071fef7279c56a28bb7430d55ba365a8cfb8628d03fedf`. Record actual runtime, dates and runner hashes. Public schema retrieval initially returned 403 with a default Python agent; identifying agent succeeded without a proxy.

## Inputs and sanitized fixtures

Existing ignored AudiobookDB credential file; synthetic invalid key; missing-key request; title fixture used by SPIKE-002. Keep account/catalog responses only in transient memory. No key generation, rotation, revocation, writes or guessed endpoints.

## Procedure and reproduction commands

1. Run `python3 spikes/SPIKE-006/finalization_probe.py` from the repository root.
2. Verify real-key GET `/auth/session` returns JSON identity; verify synthetic-invalid and absent keys return 401. Expected negative checks are the sole exceptions to stopping on authentication errors.
3. Inspect external category titles/regexes in memory for ISBN support, without guessing a resolver route.
4. Authenticate, perform one title search, fetch at most two books and six distinct release details. Cap calls and documented cost before dispatch; measure cold path including auth and a warm in-memory reuse preceded by fresh auth. No catalog/account values saved.
5. Reconcile cache/revocation, identifier deferrals and final limits; test matching synthetic policies and review direct deployment scope before finalization.

## Pass/fail criteria and numeric thresholds

Real key 200 with identity; invalid/missing keys 401; cold and warm fixture paths finish in eight seconds each. At most ten upstream attempts/twelve cost units per production-like cold path, four concurrent upstream calls, six detail expansions, ten output matches. These become enforced MVP limits, not a promise that every catalog lookup succeeds.

## Budget and stop conditions

At most sixteen live API attempts/twenty documented cost units overall, no retries; at least 250 ms spacing, two-second/request timeout within eight-second path deadline, 1 MiB response and 64 KiB auth response. Stop on unexpected 401/403/429, transport failure, malformed/oversized data or exhausted budget. Public sources do not consume keyed API budget. No actual key is revoked to demonstrate the invalid-key path.

## Actual outcomes: Pass

EVD-015: real auth 200, invalid/missing 401, zero ISBN-named categories, cold 1.753 seconds/seven attempts/nine cost units; warm 0.260 seconds/one cost unit. Overall twelve attempts/fifteen cost units. EVD-016: seven policy race tests pass in 1.146 seconds, covering byte/entry/TTL/admission/budget and rejection-generation rules. No real key revoked.

## Evidence IDs and paths

EVD-015 live probe; EVD-016 final policy tests; exact paths linked from evidence records.

## Expected versus actual differences

The earlier synthetic `/validate` endpoint is not a real API contract. Only verified `/auth/session` may replace it. Missing ISBN lookup is a scope deferral, not proof that no private capability exists.

## Required planning updates

Finalize credential policy, mapping/identifier scope, budgets, native TLS sequence and private MVP acceptance. Keep public redistribution/provider terms clarification separately open; do not infer external approval.

## Affected checks and rerun results

Record actual outcomes and affected synthetic-policy reruns; no fabricated pass for revoked production keys or unrun deployment modes.

## Decision and next action

Private baseline 1.0 finalized from these findings; delivered implementation must revalidate the policies. Public distribution remains deferred.
