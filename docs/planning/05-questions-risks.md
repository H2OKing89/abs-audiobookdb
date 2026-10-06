# Questions, decisions and remaining release risks

Status: Finalized for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## MVP question dispositions

| ID | Disposition for baseline 1.0 | Evidence / decision |
|---|---|---|
| Q-001 | Resolved for isolated ABS 2.37.1 contract; deployment files not compared byte-for-byte | EVD-010/011 |
| Q-002 | Exact ISBN-only lookup deferred; ISBN metadata retained, no title fallback | EVD-007/015; ADR-004 |
| Q-003 | Release summaries select candidates; bounded detail reads provide final runtime/IDs | EVD-005/015; ADR-004 |
| Q-004 | Delivered isolated ABS narrator/full-cast/French selection passed; language absent from card, inspect selection form | EVD-009/011/017 |
| Q-005 | Fresh real /auth/session before every hit, purge rejection, no auth cache | EVD-015/016; ADR-001/002 |
| Q-006 | Eight-second total, fixed attempt/cost limits, zero retry, atomic selected results | EVD-015/016; private MVP plan |
| Q-007 | Optional direct native TLS included; no proxy dependency | EVD-014; ADR-003 |
| Q-008 | Public MIT source preparation authorized; no catalog distribution or provider approval implied; upstream applicability question remains documented | ADR-005; EVD-007/018; SRC-001/006 |
| Q-009 | Reviewed listed community providers: no AudiobookDB entry observed; AudioSilo is a different backend. User-requested private adapter proceeds; not a claim of global absence | SRC-004/005 |

## Risk dispositions

| ID | Risk and response | State |
|---|---|---|
| RISK-001 | Conversation-derived claims replaced by scoped evidence and explicit deferrals | Managed for private scope |
| RISK-002 | Fresh authorization, scoped caches, purge/generation tests; delivered race/live invalid-key checks passed | Verified EVD-017; actual revocation not performed |
| RISK-003 | Fixed deadlines/cost/concurrency/bytes; single live sample below deadline | EVD-017/025 pass for tested workloads; final 250.631s synthetic load peaks at 24.21 MiB RSS; no general latency/memory guarantee |
| RISK-004 | No ISBN guessing, exact ASIN identity, stable release selection | Delivered exact-identity tests and live title reads pass EVD-017 |
| RISK-005 | UID99:GID100 cert access and negative permissions pass on target fixture | Delivered target mounts passed EVD-017; each installation supplies its own certs |
| RISK-006 | ABS masks provider failures; adapter preserves own HTTP/code/log distinction | Observed, documented compatibility limitation |

## Release boundary

The user now authorizes a public MIT source repository (ADR-005), superseding the earlier blanket source-publication deferral. Runtime contract baseline 1.0 is unchanged. Source licensing does not cover upstream services/data, and no metadata archive is included. Provider approval or legal compatibility is not claimed. Attribution/contact and data freshness are recorded; use only synthetic repository fixtures. The current API guide describes personal-project access while terms contain broader restrictions; the discrepancy is preserved, not silently resolved.

ADR-007 additionally records owner-authorized executable/image packaging and
Compose/Unraid support. EVD-025 records v0.1.0 publication and target checks.
Public GHCR access and CA listing remain pending separate steps; the release
archive supports manual image installation.
