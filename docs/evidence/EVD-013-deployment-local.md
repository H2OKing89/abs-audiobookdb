# Disposable deployment prerequisite

Status: Recorded  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 0.1 (not finalized)

## ID: EVD-013

SPIKE evidence; linked checks remain limited to the classification below.

## Source URL or fixture provenance

SPIKE-005 scratch image containing only a local health fixture; one-day synthetic self-signed certificates.

## Captured date and environment

2026-10-05 18:03 UTC; local Docker 29.8.2 and Compose 5.6.0.

## Version, commit or content hash

Health source SHA-256 recorded in the deployment result; static Linux Go binary, scratch base and USER 99:100.

## Method and reproduction steps

Run `python3 spikes/SPIKE-005/deploy_experiment.py --local`. Target command is `python3 spikes/SPIKE-005/deploy_experiment.py --target root@unraid` after Tailscale SSH authentication; it uses a unique temporary project and existing proxynet.

## Sanitized artifact path

[Local deployment result](SPIKE-005/deployment-20261005T180315968160Z.json).

## Claims supported and limitations

Local HTTP, native HTTPS and generic terminating-proxy HTTPS each pass three health requests as 99:100. Trust and hostname rejection, unreadable-key startup failure, read-only containers and graceful stop verified. This does not prove Unraid/proxynet or existing SWAG compatibility.

Scope correction (CHANGE-017): proxy checks are preserved as historical extra coverage. Direct localhost/shared Docker/private LAN deployment is the required scope; proxy integration is not an acceptance dependency.

## Observed outcome

Local fixture Pass; graceful stop 0.220 seconds, all positive exit codes zero, all containers/image/network removed. Target inventory stopped at required Tailscale SSH authentication; no remote deployment or Compose Manager changes performed.

Subsequent direct LAN access and successful Unraid execution are recorded separately in [EVD-014](EVD-014-unraid-deployment.md); this record preserves the earlier local-only outcome and access block.

## Synthetic or live classification

Local Docker experiment; Unraid target checks blocked by authentication, not passed.

## Sanitization and redistribution notes

Certificates/keys are generated for the experiment and deleted. No production certificates, .env, keys, Docker environment dumps or authenticated headers collected.
