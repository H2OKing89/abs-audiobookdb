# AudiobookDB live contract samples

Status: Partial  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-005

SPIKE-002 initial keyed contract samples and author-filter follow-up.

## Source URL or fixture provenance

https://audiobookdb.org/api and https://audiobookdb.org/openapi-public.json. Development key-file path read from ignored `.env`; key values stay in memory. Search fixture: The Martian; known and synthetic unknown ASINs are defined in the spike plan. Returned catalog values are not archived.

## Captured date and environment

2026-10-05T17:04:03 UTC initial success; 17:06:43 UTC follow-up. Python 3.14.4 on the development server through SSH. Local workspace DNS retry at 17:02:40 failed; server execution restored progress without changing local resolver or service configuration.

## Version, commit or content hash

OpenAPI contract 1.0.0; downloaded bytes SHA-256: `1377bdfff99a7775a7071fef7279c56a28bb7430d55ba365a8cfb8628d03fedf`. Follow-up runner SHA-256: `fb9c680b56aa91289062992904639e5a71e12e5ec048db3851758a63b5ce597e`; local and remote copies matched before execution.

## Method and reproduction steps

Run the SSH command in [the probe README](../../spikes/contract-probes/README.md). Initial run used seven API calls (11 documented cost units), plus public schema GET. Follow-up used eight API calls (14 documented cost units), plus public schema GET; it added an author-filtered search derived from an observed `people[].role.name` / `person.name` relationship. Cost figures are request-class estimates, not measured billing deltas. Requests were sequential, bounded and not retried; no writes occurred.

## Sanitized artifact path

- [Local DNS retry](SPIKE-002/probe-20261005T170240195490Z.json).
- [Initial live samples](SPIKE-002/probe-20261005T170403587916Z.json).
- [Author-filter follow-up](SPIKE-002/probe-20261005T170643495260Z.json).

## Claims supported and limitations

Configured keyed reads succeeded with `X-API-Key` and the named default User-Agent. Search returned a bare ten-hit array; the observed author filter returned HTTP 200 and retained the original book. Book detail included one release summary; its detail exposed integer `runtimeLengthMs`/`runtimeLengthSec` and string `duration`, with numeric units consistent in the sample. Role names `Author` and `Narrator` were observed. Release summary contains publisher/language/people/image fields; detail adds external identifiers and numeric runtimes. The known ASIN resolved with `matchedReleaseId` and two release summaries; the unknown returned 404 with `errors[]` and string status. Rate/daily-budget header names were present on API responses.

These are selected samples, not complete mapping/error coverage. No external category title matched the limited ISBN/ISBN-10/ISBN-13 pattern; that does not prove ISBN resolution is unsupported. ISBN edition resolution, missing-value cases, image retrieval, full terms review and budget deltas remain pending. A successful unknown-ASIN 404 is an expected test outcome.

## Observed outcome

SPIKE-002 Partial; sampled search/filter/detail/ASIN subchecks succeeded. Final API request durations ranged from 157 to 303 ms; no adapter pipeline or ABS deadline comparison has been measured.

## Synthetic or live classification

Live keyed API responses; the unknown-ASIN input is synthetic. No generated response replaces a live outcome.

## Sanitization and redistribution notes

Saved output contains schema summaries and limited public control labels, not IDs, descriptions, author names, cover URLs, keys, account data or bodies. Numeric runtime values were reduced to a consistency boolean. Default User-Agent acceptance on this sample does not amend the upstream documentation's contact requirement.
