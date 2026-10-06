# Spike register

Status: Reviewed for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

Spikes begin after Gate A. Use temporary experiments under spikes/SPIKE-NNN/ and sanitized evidence under docs/evidence/SPIKE-NNN/. Do not promote experiments into production without the finalized design.

| ID | Question | Required outcome | State |
|---|---|---|---|
| [SPIKE-001](SPIKE-001-abs-contract.md) | What does ABS send and accept? | Capture real request, auth shape without values, response acceptance, provider deadline | Partial: isolated capture/deadline and narrator UI passed; real session validation verified separately in SPIKE-006 |
| [SPIKE-002](SPIKE-002-audiobookdb-contract.md) | What does AudiobookDB expose? | Verify search/detail/ID/schema, quota headers, terms | Partial: selected keyed paths passed; broader coverage outside private scope |
| [SPIKE-003](SPIKE-003-edition-mapping.md) | Can mapping preserve editions? | Demonstrate multi-release selection and every edge fixture | Partial: eleven scenarios and two-narrator UI passed; exact ISBN-only lookup deferred |
| [SPIKE-004](SPIKE-004-bounds-isolation.md) | Can the request path stay bounded and isolated? | Measured latency/cost, errors, cancellation and two-key isolation | Partial: earlier race checks pass; final policy in SPIKE-006; actual key never revoked |
| [SPIKE-005](SPIKE-005-deployment.md) | Does deployment work on Unraid? | 99:100 + proxynet + direct HTTP/native TLS including health | Pass: disposable target trial and cleanup; proxy checks are historical extras |

| [SPIKE-006](SPIKE-006-mvp-finalization.md) | Can verified authorization and bounded reads close private MVP planning? | Live session/key rejection, cold/warm cost and final policy tests | Pass: EVD-015/016; exact ISBN/public distribution explicitly deferred |
| [SPIKE-007](SPIKE-007-sustained-memory.md) | Does the 256 MiB container survive sustained large synthetic searches? | Cache turnover, three concurrent searches, warm duration, slow/oversized failures and RSS | Execution evidence recorded separately; no live API traffic |

For every spike, complete the procedure and numeric criteria before execution. A failed spike is useful evidence; document it and revise the plan.

Baseline 1.0 disposition: historical Partial states describe broader original investigations. Their required private MVP findings are reconciled in the [Gate B/C review](../reviews/gate-b-c-private-2026-10-05.md); scoped deferrals do not turn unrun checks into passes.
