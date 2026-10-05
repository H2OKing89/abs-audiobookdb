# Source and evidence register

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Sources to verify
Published SRC-001–003 were reviewed on 2026-10-05 (EVD-001). Source review does not establish runtime compatibility; other URLs remain verification targets.

| ID | Source | Claim area | Verified date/version | State |
|---|---|---|---|---|
| SRC-001 | https://audiobookdb.org/docs | Auth, quotas, images, terms | 2026-10-05; mutable page | Reviewed; selected live samples verified; complete compatibility pending |
| SRC-002 | https://audiobookdb.org/openapi-public.json | Upstream schema and endpoints | 2026-10-05; contract 1.0.0; SHA-256 in EVD-005 | Published schema reviewed; selected live API samples verified |
| SRC-003 | https://github.com/advplyr/audiobookshelf/blob/master/custom-metadata-provider-specification.yaml | ABS schema | 2026-10-05; schema 0.1.0; v2.37.1 source/image in EVD-006/010 | Source, isolated capture/deadline and narrator UI verified; deployed-file comparison excluded |
| SRC-004 | https://github.com/audiobookshelf/audiobookshelf-docs/blob/master/docs/documentation/community/community-providers.md | Existing integrations | 2026-10-05; mutable page | Reviewed; no AudiobookDB entry observed in this list |
| SRC-005 | https://github.com/KodeStar/audiosilo-meta | Compatibility reference | 2026-10-05; mutable page | Reviewed; serves a different metadata backend, not assumed interchangeable |
| SRC-006 | https://audiobookdb.org/terms | Attribution, caching, access and redistribution | 2026-10-05 review; effective May 25, 2026 | Reviewed; adapter applicability unresolved |

## Evidence register
| ID | Record | Outcome |
|---|---|---|
| EVD-001 | [Published contracts](../evidence/EVD-001-published-contract-review.md) | Source review only; runtime unverified |
| EVD-002 | [ABS readiness](../evidence/EVD-002-abs-readiness.md) | Blocked by DNS; no HTTP response |
| EVD-003 | [AudiobookDB readiness](../evidence/EVD-003-audiobookdb-readiness.md) | Blocked by DNS; no authenticated API call |
| EVD-004 | [ABS live access](../evidence/EVD-004-abs-live-access.md) | Readiness passed via SSH; provider behavior pending |
| EVD-005 | [AudiobookDB live contract](../evidence/EVD-005-audiobookdb-live-contract.md) | Selected keyed samples passed via SSH; full coverage pending |
| EVD-006 | [ABS pinned source](../evidence/EVD-006-abs-pinned-source.md) | Eight source-component groups passed; later integration recorded in EVD-010/011 |
| EVD-007 | [ISBN contract and terms](../evidence/EVD-007-isbn-contract-and-terms.md) | ISBN metadata documented; exact lookup and terms applicability unresolved |
| EVD-008 | [Synthetic mapping fixtures](../evidence/EVD-008-synthetic-mapping-fixtures.md) | Original eleven-scenario preparation; later execution in EVD-009/011 |
| EVD-009 | [Mapping execution](../evidence/EVD-009-mapping-execution.md) | Eleven synthetic scenarios pass; exact ISBN conditional |
| EVD-010 | [Isolated ABS integration](../evidence/EVD-010-abs-isolated-integration.md) | Capture, timing, error masking and replacement sentinel pass |
| EVD-011 | [ABS UI selection](../evidence/EVD-011-abs-ui-selection.md) | Both narrator variants selectable; no item writes |
| EVD-012 | [Bounds and isolation](../evidence/EVD-012-bounds-isolation.md) | Corrected earlier race tests pass; final policy in EVD-015/016; failure retained |
| EVD-013 | [Local deployment prerequisite](../evidence/EVD-013-deployment-local.md) | Local 99:100/HTTP/TLS passed; historical target access block resolved in EVD-014 |
| EVD-014 | [Unraid deployment](../evidence/EVD-014-unraid-deployment.md) | Target 99:100/proxynet/direct HTTP/native TLS and cleanup passed; proxy checks historical extras |
| EVD-015 | [Live MVP authorization/pipeline](../evidence/EVD-015-live-mvp-finalization.md) | Real session validation and bounded cold/warm paths pass; ISBN deferred |
| EVD-016 | [Final policy race checks](../evidence/EVD-016-final-policy-checks.md) | Seven synthetic policy tests pass, including byte bounds and rejection-generation protection |
| EVD-017 | [Delivered private MVP](../evidence/EVD-017-private-mvp-acceptance.md) | Production race/vet, live title cold/warm/invalid key, isolated ABS UI and final image on actual Unraid passed; failures and deferrals retained |
| EVD-018 | [Public GitHub source readiness](../evidence/EVD-018-github-readiness.md) | Local repository/history privacy, offline CI equivalents, license/configuration and publication scope reviewed; remote CI execution not yet observed |

Each record needs source, captured timestamp, version/hash when available, sanitized artifact path, supported claims, method, limitations and reproduction steps. Source changes require checking affected claims; do not blanket-mark a document verified.
