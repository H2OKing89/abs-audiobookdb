# Direct local, Docker and LAN deployment

Status: Accepted for private MVP  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (private MVP)

## ID and status: ADR-003 / Accepted for private MVP

Final private MVP decision under the user’s instruction to complete planning.

## Context and linked requirements

REQ-002/003/005/011; Q-007. The user clarified direct localhost, shared Docker-network or private LAN deployment. Reverse-proxy/SWAG integration was an assistant-added assumption and is excluded from required scope. The target Unraid installation uses 99:100 and existing proxynet; other installations choose their network name.

## Decision question

How should direct provider URLs, network bindings and optional native TLS be configured?

## Options and tradeoffs

Shared Docker networking uses service DNS without host port publication. Host-local access uses a loopback listener/binding; private LAN access uses a reachable host address and an explicit LAN binding when containerized. Native HTTPS adds certificate/trust configuration independently of these layouts.

## Decision and rationale

Honor the user's direct deployment scope. Propose HTTP default on 8080, configurable Docker network, shell-independent health probing, nonprivileged 99:100 and graceful shutdown. Optional native HTTPS is included in the private MVP as direct adapter TLS. Document localhost namespace behavior and URL/port-binding examples. Existing proxy experiments remain historical extra coverage; no proxy setup or integration test is required for acceptance.

## Evidence and source versions

EVD-013 local prerequisite; EVD-014 target Unraid 7.3.2/Docker 29.5.3/Compose 5.5.0. HTTP/native/generic proxy health passes as 99:100 on proxynet; invalid trust/hostname and unreadable key rejected. Target graceful stop 0.767 seconds; cleanup verified. Direct LAN SSH resolved the earlier Tailscale access block.

## Consequences and risks

Direct Docker-network HTTP/native HTTPS passes on Unraid/proxynet. Host-loopback and LAN port publication, production certificate mounts and outbound production CA-bundle behavior require validation in the delivered deployment. Native TLS sequencing is resolved by including the optional mode in baseline 1.0. Historical proxy tests do not create a product dependency.

## Affected documents and tests

SPIKE-005; deployment constraints; REQ-011; VER-009 Pass and VAL-004 Partial. Next: implement direct access bindings and revalidate the delivered adapter against baseline 1.0. Reverse-proxy integration does not block acceptance.

## Reviewer and date

Codex technical review under user finalization instruction, 2026-10-05.

## Supersedes / superseded by

None.
