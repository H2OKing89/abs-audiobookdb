# Private MVP Gate B/C review

Status: Reviewed for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## Review ID, baseline and reviewer

Gate B/C technical review, private baseline 1.0; reviewer Codex, 2026-10-05. User instructed “do it” after the proposal to resolve remaining API/cache questions and finalize the MVP plan. Decisions were completed within that authorization; no external approval or public-release permission is claimed.

## Documents and versions reviewed

Current planning 01–08, accepted ADR-001–004, SPIKE-001–006 dispositions and EVD-004–016. Original baseline 0.1 evidence/failures remain historical. Current private scope excludes exact ISBN-only lookup, reverse-proxy dependency, public distribution and cross-request singleflight.

## Verification: criteria / expected / actual / evidence / status

| Criterion | Actual | Status |
|---|---|---|
| Required private contract/identity paths evidenced | Actual ABS capture/deadline, selected upstream reads, real auth session accepts valid/rejects invalid and missing key | Pass, scoped EVD-010/015 |
| Mapping and credential policies reconciled | Eleven mapping scenarios, narrator UI, accepted bounded identity rules, fresh auth and cache byte/generation tests | Pass, scoped EVD-009/011/016 |
| Fixed resource/partial-failure policy | Eight-second total, ten attempts/twelve cost units, bounded bytes/admission/cache and zero internal retries; selected failures abort | Pass for specification; production enforcement unrun |
| Target deployment feasibility | Disposable Unraid 99:100/proxynet/direct HTTP/native TLS and permission/shutdown checks | Pass EVD-014; actual adapter/host bindings unrun |
| Contradictory proposals removed or scoped | Synthetic /validate and earlier TTL/retry/flight proposals superseded; exact ISBN and public terms deferred with rationale | Pass for private scope |

## Validation: user scenario / expected / actual / evidence / status

Two intended narrator fixtures selectable in isolated ABS without metadata writes (EVD-011). Live bounded two-book/three-release pipeline: 1.753 seconds, seven attempts/nine cost units; authenticated warm reuse: 0.260 seconds/one cost unit (EVD-015). These are experiment outcomes, not delivered-MVP acceptance. Host-loopback/LAN publication, language/full-cast rendered UI and actual adapter deployment stay required implementation checks.

## Contradictions and blocking issues

No unresolved technical contract/security/deployment question blocks the scoped private MVP design. Exact ISBN lookup is deferred rather than guessed; result cache revalidates via real /auth/session; direct native TLS is included. Q-008 remains a public-release blocker: no provider clarification or licensing approval obtained. This review makes no legal-compliance determination. Operator contact remains a runtime value to supply, not an invented default.

## Changes required and linked decisions

ADR-001 fixes incoming/fallback key handling/contact; ADR-002 fixes real revalidation and four-MiB serialized cache with generation protection; ADR-003 fixes direct HTTP/native TLS deployment; ADR-004 fixes deterministic release selection/ASIN and ISBN deferral. Fixed implementation acceptance and budgets in planning 06. Update current registers; preserve original evidence.

## Retest results

Live finalization probe passed twelve attempts/fifteen cost units overall. Seven final policy race tests passed in 1.146 seconds, peak upstream four; source hashes/transcript EVD-016. Documentation links/source hash checks run after reconciliation. No production test, real key revocation, RSS or binding pass is fabricated.

## Gate outcome: Pass for private MVP

Gate B passes because required experiment findings are reconciled or explicitly scoped/deferred. Gate C passes for private baseline 1.0 with fixed requirements, acceptance policy, budgets and implementation sequence under the user’s instruction. Production implementation may begin under this baseline; completed-MVP/public-release status is not implied.

## Finalization record and deferred items

Baseline 1.0, 2026-10-05; reviewed by Codex. Deferred: exact ISBN-only resolver, cross-request singleflight, local-token mode, public distribution/provider clarification, automatic certificates, UI/database/sync/upstream edits/LLM/metrics. Next: build and validate the actual Go adapter against planning 06. Changes affecting this baseline reopen the relevant gate; never modify AGENTS.md merely to align it with new files.
