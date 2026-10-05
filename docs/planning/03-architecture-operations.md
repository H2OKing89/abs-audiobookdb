# Private MVP architecture and operations

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Structure

cmd/abs-audiobookdb and internal/config, server, provider, audiobookdb, cache. Go standard net/http/slog; concrete typed upstream models with small consumer interfaces. No ABS API client in runtime; development .env/key-file helpers remain under spikes.

## Request path

Validate input → select credential → admit bounded request → GET /auth/session → read credential-scoped result cache → search/resolve → select bounded finalists → map complete result → store bounded serialized result. No authorization-result cache or synthetic validation endpoint. Cross-request singleflight is deferred; callers own cancellation.

## Credentials

ADR-001: raw/Bearer Authorization first; optional AUDIOBOOKDB_API_KEY only when header absent. Invalid/malformed supplied key never falls back. Fresh authenticated session read before every result reuse, discard account profile; invalidate credential scope on any observed 401/403. Runtime never reads development ABS host/API credentials or dotenv files. AUDIOBOOKDB_CONTACT is configurable operator email/public URL; never invent an upstream contact.

## Fixed resource policy

| Resource | Limit |
|---|---|
| Total request / upstream attempt | 8 seconds / 2 seconds, including admission/auth/pacing |
| Attempts / documented daily cost | 10 / 12 per request, including auth; no internal retry |
| Upstream concurrency / pace | 4 globally / 4 starts per second |
| Active searches | 3; reject excess 503, no unbounded queue |
| Book candidates / release details | 2 / 6 |
| Outer match envelope | 10 (title path expands at most 6) |
| Auth / other response | 64 KiB / 1 MiB |
| Aggregate response bytes/request | 8 MiB |
| Query string / query or author / headers | 4 KiB / 512 bytes / 8 KiB |
| Serialized result cache | 60-second TTL, 64 entries, 4 MiB counted payload-plus-key bytes |
| Container memory / Go soft target | 256 MiB / GOMEMLIMIT=192MiB |

Limits are enforced ceilings, not guarantees that every upstream request completes. Daily budget is shared with other clients. Cache bytes exclude Go runtime/heap overhead; memory limit is a separate deployment constraint.

## Cache and rate handling

ADR-002: key by nonlogged credential fingerprint plus canonical input; immutable serialized results, copied on return. Sweep expired entries periodically and on access. Generation-based invalidation prevents older work repopulating rejected scopes. Cache complete success/empty results only; no failures. Every warm response includes fresh session authorization (one documented cost unit). On 429 return 503, sanitize Retry-After to bounded integer seconds and suppress calls during that credential cooldown; bounded cooldown state and global pacing. No anonymous downgrade.

## Direct deployment

No reverse proxy dependency. Same-host/network namespace: http://127.0.0.1:8080, with loopback publication for host-local ABS. Shared Docker: http://adapter:8080, no host publication. Private LAN: http://<lan-host>:8080 with explicit intended-interface publication. Inside ABS containers localhost means that container; use service DNS or reachable host address. Network name configurable; target Unraid uses existing proxynet and 99:100. HTTP default :8080; optional native TLS requires both readable cert/key paths, TLS >=1.2 and certificate-verified health. No certificate issuance automation.

## Operations and acceptance

Quota-free health/readiness reflect listener/configuration, not upstream uptime. Shell-independent health subcommand for scratch image; outbound CA bundle required. Graceful shutdown within ten seconds, read-only filesystem/tmpfs where needed, no privileged mode. Logs contain request IDs, status/code/latency/counts only; no keys/headers/profiles/query strings/raw bodies. Existing local/Unraid health fixtures passed direct HTTP/native TLS; EVD-017 now verifies the actual image, cert/CA, shared-network and host/LAN bindings. Sustained-load RSS remains unmeasured.
