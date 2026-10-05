# Final private MVP contracts and mapping

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Evidence and scope

EVD-001–016 distinguish historical failures, sources, synthetic fixtures and actual runtime observations. Private baseline 1.0 covers the verified paths below; no assertion of complete upstream API coverage. OpenAPI 1.0.0 hash is fixed in EVD-015.

## ABS contract

GET /search returns {"matches":[...]}. Interactive ABS 2.37.1 sends query/author/mediaType with configured raw Authorization, omitting explicit ISBN/ASIN. Its roughly ten-second timeout is measured; adapter total deadline is eight seconds. Provider errors/timeouts become empty HTTP 200 results inside ABS; adapter errors remain distinguishable in its own status/code/log counters. Extra release IDs are discarded by ABS. publishedYear is string, duration integer minutes, series name/sequence strings.

## Upstream reads

GET /auth/session with X-API-Key before every search/cache response; accept only 200 JSON identity with nonempty string ID, then discard profile. Verified invalid/missing keys return 401. POST /search uses books type and optional person/Author filters. GET /books/{id} supplies work and release summaries; GET /releases/{id} supplies numeric runtime/identifiers. GET /audiobooks/external/audible/{ASIN} yields work with matchedReleaseId; fetch exactly that release. Resolver 404 is empty success; missing/mismatched identity is 502. HTTPS verification, meaningful application/version/contact User-Agent, no redirects or write endpoints.

## Input and identifier rules

Raw or Bearer key; optional fallback only if Authorization is absent (ADR-001). Title query requires at least three characters unless a nonempty author filter is supplied. Normalize whitespace and bound query/author to 512 bytes. mediaType absent/book accepted; unsupported media type 400. Explicit asin and recognizable pasted ASIN route to exact lookup; invalid format or conflicting identifiers 400. Explicit/recognizable ISBN-only input is unsupported 400, never title fallback; returned release ISBN remains available metadata. Unknown extra parameters ignored. Canonical cache input includes mode/query/author/identifier, not credentials.

## Mapped fields

| ABS field | Final rule |
|---|---|
| title/subtitle | Nonempty release override, then book |
| author/narrator | Ordered exact-name deduplication of Book Author / Release Narrator relations, comma-space joined |
| publisher/language | Release object name |
| publishedYear | Valid release date year, then integer book copyright, rendered string |
| description | Book description; protect HTML rendering in implementation |
| cover | First usable release image, then book cover, with /large.jpg derivative |
| isbn/asin | Release identifiers; exact ASIN request preserves requested verified ASIN |
| genres/tags | Ordered unique book collection titles |
| series | Membership name; string position label then ordinal, including zero/fractional values |
| duration | Nonnegative numeric milliseconds/seconds floored to minutes |

Omit unavailable optional values. Invalid required schema or inconsistent release/work identity is an upstream fault. Do not invent missing identifiers or numeric duration from formatted text.

## Candidate and failure policy

Select at most two books and six release finalists round-robin across selected books; keep stable exact-title priority and upstream order for ties. Deduplicate identical release IDs only; preserve narrator/language variants. Result envelope outer cap ten, with at most six expansions on this MVP title path. Fixed candidate selection is documented bounded search, not complete catalog enumeration. Any selected detail failure aborts the request; no silently incomplete arrays. Success/unknown exact identifier: 200 matches array. Input/unsupported ISBN: 400; invalid credential: 401; malformed/upstream fault: 502; overload/rate limit: 503 with sanitized Retry-After; deadline/cancellation: 504. No internal retry or raw upstream error bodies.

## Verification required in delivered code

Use synthetic missing/null/type-error cases, exact resolver identity, complete mapping and error/cancellation/cache tests. Re-run isolated ABS rendering for multiple narrators/full cast and language variants; do not label unrun production checks Pass.
