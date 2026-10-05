# Published contract review

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-001

Published-source evidence for SPIKE-001/002, distinct from runtime observations.

## Source URL or fixture provenance

- SRC-001: https://audiobookdb.org/docs
- SRC-002: https://audiobookdb.org/openapi-public.json
- SRC-003: https://raw.githubusercontent.com/advplyr/audiobookshelf/master/custom-metadata-provider-specification.yaml

## Captured date and environment

2026-10-05 UTC; browser retrieval succeeded. Workspace Python requests failed DNS resolution.

## Version, commit or content hash

Published ABS provider schema: 0.1.0. AudiobookDB OpenAPI: 3.1.0; contract version: 1.0.0. Browser retrieval did not provide a pinned Git commit or byte-level hash. Installed ABS version remains unknown. The runner hashes the public OpenAPI when direct retrieval succeeds.

## Method and reproduction steps

Read the three public sources and inspect schema fields and documented request behavior. Reopen these URLs to reproduce; mutable URLs may change. Run the local contract runner once network access is available for direct hash capture and live checks.

## Sanitized artifact path

This record contains only public contract summaries; no raw API/catalog response or private endpoint is stored.

## Claims supported and limitations

ABS schema declares GET `/search`, required `query`, optional `author`, an Authorization API-key header, and a `matches` array. `title` is required; `publishedYear` and series `sequence` are strings; series entries use `series`; duration is integer minutes. Its parameters do not declare ISBN, mediaType or ASIN. Their runtime handling and the client deadline remain unknown.

AudiobookDB docs require `X-API-Key` and an identifying User-Agent for registered callers. Search accepts `q`, `type`, and structured filters, returns a bare array capped at ten hits per collection, and has no pagination. Detail endpoints return work/recording data; external ASIN resolution can include `matchedReleaseId`. Image storage URLs need a derivative suffix. Errors have `errors[]`; quota headers distinguish rate and daily cost. Docs require attribution and restrict catalog redistribution; they do not establish permission to publish captured descriptions or cover art.

OpenAPI declares `/audiobooks/external/{category}/{itemId}`; omitted book `include` requests all relations. These source statements do not prove current keyed API responses, edition mapping or installed-version compatibility. Full terms review remains pending.

## Observed outcome

Source review succeeded. VER-001/002 are not passed; live probes are independently recorded in EVD-002/003.

## Synthetic or live classification

Live public-document retrieval; no authenticated API or ABS runtime observation.

## Sanitization and redistribution notes

No secrets, hostnames, account data, catalog descriptions or cover art captured. Store future catalog fixtures only after confirming applicable redistribution permission; prefer synthetic fixtures and schema summaries.
