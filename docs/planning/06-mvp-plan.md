# Private MVP implementation plan

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Preconditions

Gate C technical review passes for private baseline 1.0. The user instructed completion of the recommended next steps. This authorizes the evidence-supported private MVP; public publishing/provider approval is not implied.

## MVP scope

Go ABS custom metadata provider: GET /search, direct title/author search and exact Audible ASIN, one mapped result per selected release, fresh upstream authorization, bounded ephemeral result cache, safe errors, local health/readiness and graceful shutdown. Direct HTTP by default; optional native TLS included. Localhost/shared Docker/private LAN layouts; configurable network with proxynet on the target Unraid installation; 99:100 container identity. Runtime must not read development ABS host/API settings or `.env`.

## Fixed limits

Eight seconds total including admission/auth/pacing/mapping; two seconds per upstream attempt; at most ten attempts/twelve documented cost units per request. No internal retry; preserve safe Retry-After and credential cooldown on 429, returning 503. Four global concurrent upstream calls, paced to four starts/second; at most three active searches and reject excess with 503. Two book candidates/six release detail reads, at most ten output matches. One MiB/upstream or mapped response, 64 KiB auth response, eight MiB aggregate response bytes/request, four KiB search query string, 512-byte query/author fields, eight KiB request headers. Cache: sixty-second TTL, 64 entries, four MiB counted payload-plus-key bytes. Container memory 256 MiB and GOMEMLIMIT=192MiB; cache bytes are not an RSS guarantee.

## Credential and configuration contract

Incoming raw/Bearer Authorization wins; optional AUDIOBOOKDB_API_KEY only when absent. Invalid supplied key never falls back. GET /auth/session before any cached response; discard identity and purge rejected scope. AUDIOBOOKDB_CONTACT supplies a real operator email or public contact URL; meaningful User-Agent identifies app/version/contact. Listen address defaults to :8080. Native TLS requires both readable cert/key paths and certificate-verified health checks. No automatic certificate issuance or proxy setup.

## Increments

1. Bootstrap Go configuration/server/health/shutdown.
2. Typed HTTPS client, real session validation, global admission/pacing and unified budget.
3. Search/ASIN pipeline and deterministic edition mapping.
4. Bounded serialized result cache, purge/generation handling and race tests.
5. Scratch-compatible image with CA bundle, 99:100 Compose and direct URL/binding examples.
6. Isolated ABS integration plus delivered-adapter trial on Unraid; preserve evidence and cleanup.

## Acceptance before declaring MVP complete

Run production go test -race ./... and meaningful schema/identifier/error/cache/budget/cancellation tests. Verify cold/warm reads through actual adapter, invalid-key warm-cache rejection, no secret output and graceful shutdown. Isolated ABS must render/select two narrator recordings without changing the live library. Test direct shared-network, host-loopback and target LAN port bindings, optional native TLS and 99:100. A bounded live follow-up may use at most four searches/twenty documented cost units after operator contact is provided; no production-key revocation or API writes. One observed latency sample is not a service-level guarantee.

## Explicit deferrals

Exact ISBN lookup until a supported resolver is verified; cross-request singleflight; separate local-token authentication; UI/database/sync/upstream edits/LLM matching/automatic certificates/metrics. Public distribution and any licensing applicability clarification remain a later release gate (Q-008). Synthetic fixtures only in repository; no catalog dumps or real account/credential data.

## Definition of done

Delivered implementation meets the fixed private scope and records actual acceptance outcomes. Planning gate passage is not an implementation pass. Public-ready status requires separate provider-terms and release review.

## Delivered outcome: 2026-10-05

Private MVP implementation completed and checked in EVD-017. Production race
suite/vet, actual AudiobookDB cold/warm and invalid-key reads, isolated ABS
narrator/full-cast/language selection, and final image on actual Unraid passed.
Direct shared-network, loopback HTTP and HTTP/native TLS LAN bindings verified;
temporary trials removed. Operator supplied contact locally. Actual key
revocation, sustained-load RSS and permanent live-library installation were
not performed; public release/ISBN/singleflight deferrals remain unchanged.

See [acceptance](../evidence/EVD-017-private-mvp-acceptance.md) and
[deployment instructions](../deployment.md).

## Publication update: 2026-10-05

The owner requests public GitHub source preparation under H2OKing89 and chooses
MIT (ADR-005). This supersedes earlier source-publication deferral while
preserving runtime baseline 1.0. Credentials, account responses and catalog
archives are excluded. EVD-018 records repository readiness; public source
licensing does not represent upstream provider approval or data licensing.
