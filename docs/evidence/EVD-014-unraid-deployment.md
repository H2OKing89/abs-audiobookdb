# Unraid deployment trial

Status: Recorded  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-014

SPIKE-005 target execution; VER-009 and the fixture subset of VAL-004.

## Source URL or fixture provenance

Disposable Go health fixture, scratch image and generated one-day certificates from `spikes/SPIKE-005/`. Existing `proxynet`; no upstream API calls.

## Captured date and environment

2026-10-05 18:18 UTC; Unraid 7.3.2, Docker 29.5.3, Compose 5.5.0. The user supplied a direct LAN SSH target, which worked without the previous Tailscale check. The Compose Manager projects directory was verified read-only at `/boot/config/plugins/compose.manager/projects/`.

## Version, commit or content hash

Static Linux/amd64 binary built locally with Go 1.25.10. Source, module, Dockerfile and runner SHA-256 values are in the inventory artifact; health source hash also matches the target deployment result.

## Method and reproduction steps

Set `SPIKE_UNRAID_SSH_TARGET` to the authorized direct LAN SSH target, then run `python3 spikes/SPIKE-005/deploy_experiment.py --target "$SPIKE_UNRAID_SSH_TARGET"`. Inventory Unraid/Docker/Compose and `proxynet` first. The runner uploads a unique temporary project and synthetic certificates; it never installs the fixture into existing Compose Manager projects.

## Sanitized artifact path

[Target deployment result](SPIKE-005/deployment-20261005T181849981544Z.json); [inventory and cleanup](SPIKE-005/inventory-20261005T182051158542Z.json).

## Claims supported and limitations

Three health requests each passed for HTTP, native HTTPS and generic proxy HTTPS as 99:100 on the actual `proxynet`, including DNS, trusted certificates and hostname validation. Untrusted certificates, wrong hostname and unreadable key were rejected. This proves the disposable fixture works on this Unraid environment; existing SWAG configuration, production adapter and outbound production CA bundle were not tested.

Scope correction (CHANGE-017): the user requires direct localhost/shared Docker/private LAN access. Proxy tests above are historical extra coverage; proxy integration is not a requirement or acceptance blocker. The recorded network-only trial did not exercise host-loopback or LAN port publication.

## Observed outcome

Pass for every defined target-trial criterion. Graceful stop took 0.767 seconds, with all positive exit codes zero. Compose project, negative container, image and remote temporary directory were removed successfully. A read-only follow-up found zero spike containers or fixture images; `proxynet` and Compose Manager directory remained present. Earlier Tailscale failures are preserved in EVD-013 and historical change records.

## Synthetic or live classification

Live Unraid Docker deployment using synthetic health data, certificates and a generic reverse proxy. Not an AudiobookDB or existing SWAG integration test.

## Sanitization and redistribution notes

Only versions, hashes, outcome flags and counts archived. No private target address, production credentials, certificates, headers, environment dumps or catalog contents saved. Generated test keys were removed during cleanup.
