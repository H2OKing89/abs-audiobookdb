# SPIKE-002: What does AudiobookDB expose under the supplied key?

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID and status: SPIKE-002 / Partial

Planned experiment; production implementation is excluded.

## Question and hypothesis

What does AudiobookDB expose under the supplied key? Named User-Agent and X-API-Key requests should support bounded search, book/release detail and external-ID resolution.

## Linked requirements and blocking questions

REQ-004, REQ-007/010; Q-002/003/008; VER-002.

## Environment and versions

Record execution UTC timestamp, runtime/tool versions, relevant source hashes and installed ABS version when available. Current public source versions are ABS provider 0.1.0 and AudiobookDB API 1.0.0; these do not identify the installed server version.

## Inputs and sanitized fixtures

Public OpenAPI and API docs; search title The Martian; one returned book and up to two associated releases; documented ASIN B00B5HZGUG and synthetic unknown ASIN B000000000. Keep payloads in memory and save schema summaries only.

## Procedure and reproduction commands

1. Review SRC-001/002 authentication, search shape, relevant endpoints and usage terms.
2. Run `python3 spikes/contract-probes/probe.py audiobookdb`. Fetch and hash the public schema, search once, optionally search once with an author filter derived from returned data, fetch one book and at most two releases, inspect roles/categories, then resolve known/unknown ASINs.
3. Compare schema summaries, nullability, role names, identifier scope, envelopes and safe rate-header names with the public schema. Do not assume absent fields never exist.
4. Check ISBN support in external categories and schema before making any ISBN-specific request. The initial runner does not guess an ISBN endpoint.

## Pass/fail criteria and numeric thresholds

All successful search/detail responses are JSON with the documented envelope; search yields 1–10 hits; one book and at least one release are inspected. Known resolver returns book plus matchedReleaseId; synthetic unknown returns 404 with errors[]. Author filter, role names, quota headers and ISBN support must be individually recorded or explicitly unresolved. No account/catalog mutation.

## Budget and stop conditions

At most 10 authenticated requests and 20 documented daily cost units; sequential requests with at least 250 ms spacing, 10 seconds/request, 1 MiB/API response and 2 MiB/schema. No retries. Stop on 401/403/429, transport failure or exhausted budget. Do not intentionally exhaust quota.

## Actual outcomes: Partial

Initial public schema GET failed workspace DNS (EVD-003). The 17:02:40 retry with updated configured key-file paths also failed DNS.

Existing SSH access enabled successful runs at 17:04:03 and 17:06:43 UTC (EVD-005). Follow-up performed eight keyed API calls (14 documented cost units), plus public schema GET. Search, observed-author filtering, one book/release detail, roles, external categories and known/unknown ASIN resolution returned expected statuses. Author filtering retained the original book; numeric runtime units were consistent; known ASIN included matchedReleaseId; unknown returned 404/errors[]. OpenAPI 1.0.0 hash is recorded in EVD-005. No ISBN-like category title matched the limited pattern; ISBN edition resolution remains unresolved. Full terms and edge-fixture coverage remain pending.

Direct local schema inspection reproduced the EVD-005 hash. Nullable Release.isbn exists, but no exact ISBN lookup is declared. Release summaries omit numeric runtime/ISBN/external identifiers, so their use for candidate selection cannot replace all detail reads. API docs and terms were reviewed; broad adapter/product/output-format applicability remains open (EVD-007). No additional keyed API request occurred in this review.

## Evidence IDs and paths

EVD-001 source review; EVD-003 initial blocked runner; EVD-005 local retry and successful SSH runs; EVD-007 ISBN/schema/terms review; `docs/evidence/SPIKE-002/`.

## Expected versus actual differences

Public docs describe a bare search array and no search pagination; response details require live verification.

## Required planning updates

Reconcile contract/mapping and Q-002/003/008. Attribution and redistribution conditions must be reflected before packaging public fixtures.

## Affected checks and rerun results

VER-002 Partial: selected keyed samples passed; complete schema/error/missing-value/identifier coverage remains pending. VER-003/004 and validation checks have not passed.

## Decision and next action

Clarify exact ISBN support and API terms applicability; cover missing-value/identifier edges using the synthetic SPIKE-003 fixtures. Do not guess ISBN endpoints, silently substitute editions or archive catalog fixtures. Preserve initial failures and partial classifications.

## Baseline 1.0 reconciliation

Private baseline disposition: required search/detail/ASIN/session paths verified; exact ISBN explicitly deferred with unsupported-input behavior. Public terms question remains a separate release gate. Latest live evidence EVD-015.
