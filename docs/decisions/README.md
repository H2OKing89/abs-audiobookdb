# Decision log

Status: Reviewed for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

Copy [decision template](../templates/decision.md) to ADR-NNN-topic.md. Separate user requirements from technical proposals. Proposed records are not accepted decisions.

| ID | Topic | Status |
|---|---|---|
| [ADR-001](ADR-001-credentials.md) | Credential forwarding and fresh real authorization | Accepted for private MVP |
| [ADR-002](ADR-002-credential-cache.md) | Authenticated bounded result cache; flights deferred | Accepted for private MVP |
| [ADR-003](ADR-003-deployment-transports.md) | Direct localhost/Docker/LAN and optional native TLS | Accepted for private MVP |
| [ADR-004](ADR-004-release-mapping.md) | Bounded release mapping; exact ISBN deferred | Accepted for private MVP |
| [ADR-005](ADR-005-public-source.md) | Authorized public MIT source; no metadata archive | Accepted |
| [ADR-006](ADR-006-local-ci.md) | Local CI; GitHub Actions disabled | Accepted |
| [ADR-007](ADR-007-versioned-distribution.md) | Versioned local releases; Compose and Unraid template/store distribution | Accepted; registry/listing verification separate |
| [ADR-008](ADR-008-moving-image-tags.md) | Pullable latest release channel and updates through Unraid | Accepted; public registry verification pending |
