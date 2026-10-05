# SPIKE-005: Does deployment work on the target Unraid environment?

Status: Pass
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID and status: SPIKE-005 / Pass

Experimental findings recorded; production implementation is excluded.

## Question and hypothesis

Does deployment work on the target Unraid environment? An isolated test container should serve direct HTTP and native HTTPS as 99:100 on proxynet. User clarified direct localhost/shared Docker/private LAN deployment; reverse-proxy coverage is extra historical evidence, outside required scope.

## Linked requirements and blocking questions

REQ-002/003/005/011; Q-007; VER-009; VAL-004.

## Environment and versions

Local Docker 29.8.2/Compose 5.6.0 prerequisite in EVD-013. Target Unraid 7.3.2, Docker 29.5.3, Compose 5.5.0 and existing bridge `proxynet` verified in EVD-014. Static Linux/amd64 health fixture built with Go 1.25.10; exact timestamps/source hashes recorded separately for each environment.

## Inputs and sanitized fixtures

Target Unraid/Docker versions; isolated throwaway health server/image; proxynet; test certificates readable by 99:100; deliberately unreadable certificate fixture.

## Procedure and reproduction commands

1. Inventory target versions/network read-only and select a disposable container name.
2. Run `python3 spikes/SPIKE-005/deploy_experiment.py --local` for a local prerequisite check. Set `SPIKE_UNRAID_SSH_TARGET` to the authorized direct LAN SSH target, then run `python3 spikes/SPIKE-005/deploy_experiment.py --target "$SPIKE_UNRAID_SSH_TARGET"`. Use existing `proxynet` and an isolated temporary Compose project, never existing Compose Manager projects or production adapter code.
3. Verify UID:GID, network DNS, direct HTTP and certificate-verified native HTTPS health. The unchanged historical runner also exercises a generic proxy to reproduce prior evidence; that check is not required product acceptance.
4. Check expected unreadable-certificate startup failure and graceful shutdown, then remove only spike-created artifacts.

## Pass/fail criteria and numeric thresholds

Observed identity exactly 99:100; 3 successful direct HTTP/native HTTPS health requests per mode; valid TLS trust and hostname; unreadable certificate produces a clear failure without secrets; shutdown within 10 seconds. Native TLS MVP timing is a separate scope decision. Host-loopback/LAN port publication requires delivered-deployment validation; the original trial used container DNS without published ports.

## Budget and stop conditions

Historical runner: zero upstream API calls; at most 4 disposable container startup attempts and 3 running containers simultaneously, 30 health requests and 10 minutes execution. Stop positive containers before the unreadable-key attempt. No privileged mode or existing project/network/container configuration changes. A local prerequisite cannot establish target Unraid/proxynet behavior. Record any target-access dependency as blocked.

## Actual outcomes: Pass

Local Docker/Compose prerequisite passed: HTTP, native HTTPS and generic terminating-proxy HTTPS each passed three health requests as 99:100; invalid trust/hostname and unreadable-key failures were verified. Graceful stop took 0.220 seconds with all positive exit codes zero. All local fixture containers, image and network were removed (EVD-013).

The hostname route previously required Tailscale authentication; the user-supplied direct LAN target worked. Unraid/Docker/Compose versions, `proxynet` and `/boot/config/plugins/compose.manager/projects/` were verified read-only. The temporary target project passed three health requests per transport as 99:100, untrusted/wrong-host certificate rejection and unreadable-key startup rejection. Graceful stop took 0.767 seconds; all positive exit codes were zero (EVD-014).

Target project, negative container, image and temporary directory were removed. Follow-up found zero spike containers or fixture images; existing network/projects were retained. Previously recorded generic proxy tests remain extra coverage and are not a required user workflow.

## Evidence IDs and paths

EVD-013 local prerequisite; EVD-014 target inventory/execution/cleanup. Target result: `docs/evidence/SPIKE-005/deployment-20261005T181849981544Z.json`.

## Expected versus actual differences

Target execution verifies Unraid/proxynet permissions independently of local prerequisites. Native TLS works in both fixtures; initial MVP sequencing remains Q-007. User clarification removes the assistant-added reverse-proxy acceptance dependency; existing proxy results are preserved without changing what was tested.

## Required planning updates

Align ADR-003/REQ-011 with direct localhost/Docker/LAN access and configurable network names. Keep initial native-TLS MVP sequencing open; document listener/port bindings for the selected layout.

## Affected checks and rerun results

VER-009 Pass for the defined target trial. VAL-004 Partial: direct Docker-network HTTP/native HTTPS passes; host-loopback/LAN port bindings require deployment validation. No reverse-proxy integration check is required.

## Decision and next action

Target trial complete and cleaned up. Review ADR-003/Q-007 and validate direct provider URLs/bindings in the delivered adapter; no proxy integration is needed.

## Baseline 1.0 reconciliation

Private baseline disposition: optional direct native TLS included (ADR-003); proxy work excluded. Delivered adapter still needs direct loopback/LAN binding checks, CA bundle and memory-limit verification.
