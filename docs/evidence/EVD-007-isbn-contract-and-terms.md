# ISBN contract and source-terms review

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-007

SPIKE-002 public contract review for Q-002/003/008.

## Source URL or fixture provenance

- [Public OpenAPI](https://audiobookdb.org/openapi-public.json), SRC-002.
- [API documentation](https://audiobookdb.org/docs), SRC-001.
- [Terms of Service](https://audiobookdb.org/terms), SRC-006.

## Captured date and environment

2026-10-05 UTC. OpenAPI was retrieved directly from the now network-enabled local process; docs/terms were inspected through browser retrieval. Terms page states effective date May 25, 2026.

## Version, commit or content hash

OpenAPI 1.0.0; SHA-256 `1377bdfff99a7775a7071fef7279c56a28bb7430d55ba365a8cfb8628d03fedf`, matching EVD-005. Terms/docs are mutable pages; no byte-level hash was captured.

## Method and reproduction steps

Inspect Release/ReleaseInput and GET release/list/external-resolver parameters in the exact schema hash above. Search declared operations for ISBN support; inspect API docs and terms sections 5–8. No keyed catalog requests or guessed ISBN endpoints were used in this review.

## Sanitized artifact path

This summary; schema bytes were inspected in temporary storage only. No catalog fixture was archived.

## Claims supported and limitations

`Release.isbn` is a nullable string: ISBN exists as edition metadata. No exact-ISBN query/resolver is declared in the inspected schema. Release-list `q` searches title/book title/narrator, not declared ISBN fields; `external` filters require an external category. The generic resolver takes category title and exact item ID. EVD-005's category pattern observation alone cannot prove unsupported behavior. Exact ISBN resolution remains unverified and must not be replaced with a different edition.

Book release summaries declare narrator/publisher/language/images/formatted duration but omit ISBN/external identifiers and numeric runtime. Thus summaries can reduce candidate-fetch work, while final identifier/runtime mapping still requires detail or another verified source. This is a supported design inference, not a measured request budget.

Terms require attribution, refreshed caches and identifying contact; creative-content rights are separate. Broad programmatic/product/output-format restrictions need clarification against the API guide's personal-use allowance before public packaging. This review records that ambiguity rather than inferring permission or legal compatibility. Synthetic fixtures avoid redistributing catalog content; public adapter distribution is still unresolved under Q-008.

## Observed outcome

ISBN storage documented; exact lookup Not verified. Release-summary feasibility partially supported. Terms reviewed; applicability to this adapter remains unresolved. Full SPIKE-002 is Partial.

## Synthetic or live classification

Public source review and schema inspection only; no live ISBN lookup and no terms approval from the provider.

## Sanitization and redistribution notes

Only short source summaries and schema field names retained. No keys, personal data, descriptions, cover art or catalog dumps stored. Do not treat source review as redistribution permission.
