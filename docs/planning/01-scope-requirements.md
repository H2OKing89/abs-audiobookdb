# Scope and requirements

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Goal
Provide edition-aware AudiobookDB metadata through the ABS custom-provider interface, with direct localhost, shared Docker-network or private LAN access and a simple Unraid deployment.

## Requirements
| ID | Requirement | State | Acceptance evidence |
|---|---|---|---|
| REQ-001 | Implement the service in Go | Locked by user | Build and runtime check |
| REQ-002 | Unraid container runs as UID:GID 99:100 | Locked by user | Container identity and permissions spike |
| REQ-003 | Support a configurable shared Docker network; use existing external proxynet for the target Unraid installation | User-clarified deployment scope | ABS/container DNS connectivity |
| REQ-004 | Accept AudiobookDB key from ABS authorization configuration and forward as upstream key | User-requested design | Captured sanitized header behavior + isolation test |
| REQ-005 | Support direct inbound HTTP and native HTTPS; optional native TLS included in the private MVP | Finalized within user instruction | Direct HTTP and native TLS checks |
| REQ-006 | Complete planning → spikes → revisions → finalization before MVP | Locked by user | Phase-gate records |
| REQ-007 | Preserve distinct recordings as separate matches | Accepted for private MVP | Multi-release fixture and ABS selection |
| REQ-008 | Never log/store secrets in evidence or logs | Accepted for private MVP | Sentinel-secret scan |
| REQ-009 | Bound request work, latency, concurrency and cache size | Accepted for private MVP | Budget/cancellation/load checks |
| REQ-010 | Return compatible ABS metadata and distinguish no-match from failure | Accepted for private MVP | Contract and end-to-end checks |
| REQ-011 | Support direct localhost, shared Docker-network or private LAN deployment without a reverse proxy dependency | User-clarified scope | Provider URL, listener and port-binding validation for the selected layout |

## Initial scope
Title/author search, identifier resolution when verified, release expansion, mapping, deterministic ranking, fresh authenticated short-lived result caching, cancellation, error translation, health, Docker deployment and documentation.

## Deferred
Exact ISBN lookup (metadata still mapped), cross-request singleflight, separate local-token mode, database, UI, synchronization, upstream edits, LLM matching, automatic certificate issuance, Prometheus metrics and metadata archive distribution. Public MIT source preparation is separately authorized in ADR-005.

## Deployment scope

Users configure an ABS provider URL pointing directly to the adapter. Examples: `http://127.0.0.1:8080` when ABS shares the host network, `http://adapter:8080` on a shared Docker network, or `http://<lan-host>:8080` over a private LAN. A Docker network name is installation-specific; `proxynet` is the verified Unraid test network. SWAG/reverse-proxy setup, public hosting and proxy TLS are outside the required workflow.

## Acceptance scenario
Configure one provider in ABS with a direct adapter URL, enter a key there, search a known title, select the intended narrator/edition, and receive correct metadata with no duplicated key configuration required. Confirm connectivity for the chosen local/Docker/LAN layout; the target Unraid installation uses proxynet and 99:100.

## Delivered acceptance

[EVD-017](../evidence/EVD-017-private-mvp-acceptance.md) records actual implementation checks against the private requirements, including production race tests, live title search and invalid-key rejection, isolated ABS selection, and direct final-image deployment on the actual Unraid host. The trial was disposable; no permanent live ABS provider was configured.
