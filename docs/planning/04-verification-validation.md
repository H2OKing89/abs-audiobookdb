# Verification and validation matrix

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Execution rules
Checks start Not run; states below reflect recorded evidence. Record actual outcomes, source version, fixture/evidence links, and changes needed. Verification can fail while validation succeeds, or vice versa; preserve both.

| ID | Kind | Check | Evidence / spike | Experiment state |
|---|---|---|---|---|
| VER-001 | Verification | Actual ABS request and response schema | SPIKE-001; EVD-010/011 | Pass: isolated ABS 2.37.1 capture, acceptance and measured deadline |
| VER-002 | Verification | Upstream envelopes, auth, endpoints and role types | SPIKE-002/006; EVD-001/003/005/015 | Pass for selected private paths: search/filter/detail/ASIN/roles and session authorization; broader coverage unrun |
| VER-003 | Verification | Every mapped field, missing values and series sequence | SPIKE-003; EVD-009 | Pass: synthetic field/scenario matrix; production revalidation required |
| VER-004 | Verification | Exact ASIN and ISBN edition resolution | SPIKE-002/003; EVD-005/009 | Partial: live ASIN and fixture identity checks pass; exact ISBN-only lookup deferred in baseline 1.0 |
| VER-005 | Verification | 400/401/404/429/5xx, Retry-After, malformed JSON | SPIKE-004; EVD-012 | Pass: corrected synthetic prototype |
| VER-006 | Verification | Result cache credential isolation; shared flights deferred | SPIKE-004/006; EVD-012/015/016 | Pass: synthetic isolation and fresh-auth ordering; real authorization endpoint verified; actual key never revoked |
| VER-007 | Verification | Bounded fan-out, deadlines and cancellation | SPIKE-004/006; EVD-012/016 | Pass: synthetic final budgets/admission/deadlines/cancellation; historical failed attempt retained |
| VER-008 | Verification | No sentinel key in logs, fixtures or errors | SPIKE-001/004; EVD-010/012 | Pass: saved outcomes, tested errors and isolated ABS logs; source contains test sentinels intentionally |
| VER-009 | Verification | Docker 99:100, proxynet, certificate permissions | SPIKE-005; EVD-013/014 | Pass: disposable trial on Unraid/proxynet, including TLS permissions and cleanup |
| VAL-001 | Validation | ABS user can select intended narrator and edition | SPIKE-001/003; EVD-011 | Pass: both distinct narrator fixtures; other UI distinctions unvalidated |
| VAL-002 | Validation | Key entered only in ABS works, rotation works | SPIKE-001/004/006; EVD-010/012/015/016 | Partial: replacement sentinel and synthetic revocation pass; real /auth/session verified; actual production key revocation not performed |
| VAL-003 | Validation | Warm/cold search completes within ABS deadline | SPIKE-004/006; EVD-010/012/015 | Partial: ten-second ABS deadline measured; bounded live experiment 1.753s cold / 0.260s warm, EVD-015; production unrun |
| VAL-004 | Validation | Direct localhost/Docker/LAN access and native HTTPS usable | SPIKE-005; EVD-013/014; REQ-011 | Partial: direct Docker-network HTTP/native HTTPS passed; selected host/LAN port bindings require deployment validation |

## Fixture set to collect
Known title/author; ambiguous title; multiple recordings; full cast; multiple authors; fractional series; missing cover/ID/duration; unknown identifier; alternate language; different ISBN editions. Use synthetic error fixtures and minimal sanitized upstream responses. Record provenance and redistribution permission; do not archive entire catalogs.

## Final acceptance thresholds
Private baseline 1.0 fixes limits and delivered-code acceptance in [planning 06](06-mvp-plan.md). EVD-015 verifies real authorization and a bounded live cold/warm fixture; EVD-016 verifies selected final policies synthetically. Gate C technical review passes for this private scope. At planning finalization, all production checks were unrun; EVD-017 below now records delivered-code acceptance separately from prior experiment passes.

## Delivered private MVP acceptance (EVD-017)

| Check | Actual outcome | Status |
|---|---|---|
| VER-001/002/003/004 | Production typed search-hit/detail client, complete synthetic mapping, exact-ASIN happy/unknown/invalid identity tests; real title cold/warm and isolated ABS acceptance | Pass for private scope; ISBN deferred |
| VER-005/006/007/008 | Production race checks for failures, rate cooldown/pacing, budgets, bytes, cache TTL/scopes/purge/generation, cancellation, admission and safe logs; warm invalid key rejection | Pass; actual account revocation not performed |
| VER-009 / VAL-004 | Final image on actual Unraid: 99:100, shared network, loopback HTTP and HTTP/native HTTPS LAN ports, trust/SAN/permissions/shutdown | Pass for tested layouts |
| VAL-001 | Isolated ABS selected two narrators/full cast/French recording; cards omit language, inspected in selection form; zero item writes | Pass for invented fixtures |
| VAL-002 | Raw/Bearer and absent-header-only fallback tests; fixture rejection purges warm results, actual invalid key rejected | Pass for configured credential paths; no real key revoked |
| VAL-003 | Delivered live fixture 1.668s cold / 0.229s warm, below eight-second adapter limit | Pass observation; no latency guarantee |

All current results, final image/source hashes, preserved failures and limits:
[delivered acceptance](../evidence/EVD-017-private-mvp-acceptance.md).
Sustained-load RSS and permanent installation are not claimed.

## Subsequent release and installation acceptance

The statement above describes EVD-017's historical scope. EVD-021 records the
later persistent installation. [EVD-025](../evidence/EVD-025-versioned-release-deployment.md)
records published v0.1.0, full local CI, ten Python regressions, 250.631-second
synthetic load with 24.21 MiB peak RSS, FIFO pacing regressions and pinned live
Unraid deployment. Earlier failures remain in EVD-023. Owner reports live ABS
provider setup complete; latest live checks cover health/readiness connectivity,
not a new metadata/UI test.
