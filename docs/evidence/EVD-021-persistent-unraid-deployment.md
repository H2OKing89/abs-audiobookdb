# Persistent Unraid deployment from GitHub

Status: Pass for installation and connectivity  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-021

REQ-003/005/011; ADR-003/005/006. Owner authorized persistent deployment
using source pulled from the public GitHub repository.

## Source URL or fixture provenance

https://github.com/H2OKing89/abs-audiobookdb, branch main. Source fetched by
Docker BuildKit on the actual Unraid host. Installed Compose Manager source
was inspected to verify registration, autostart and Build on Update behavior.

## Captured date and environment

2026-10-05, actual Unraid host via owner-authorized direct LAN SSH.
Unraid 7.3.2; Docker 29.5.3; Docker Compose 5.5.0; existing shared network proxynet.
The existing ABS container runs on the same network. No VM was created.

## Version, commit or content hash

GitHub source commit: 59600e06d717aa1a08801bd94bec3f8702b1dde0.
Built image: sha256:5358bea3c039d8847e43b91a5106fa9b099a9f2fe6b91c4d800081041c4e27f3.
Stack: abs-audiobookdb; container: abs-audiobookdb-adapter-1.
Build logs showed the Git remote and resolved main commit before compilation.

## Method and reproduction steps

Register a new stack through the installed plugin's `StackInfo::createNew`
factory, preserving existing stacks. Configure the base Compose settings with
GitHub build context, locally built image and `pull_policy: never`. Publish
port 8080 on the selected private LAN interface, retain shared-network alias
adapter and add Unraid management/WebUI labels. Store only operator contact
and network/bind settings in the stack's restricted local `.env`.

Enable stack autostart and Build on Update. Execute the plugin's Update wrapper
with explicit Compose files, env file, stack path, workdir and `--build`.
Verify container health, runtime restrictions, stack discovery/settings and
successful plugin result. GET `/health` and `/ready` from the development host;
GET `http://adapter:8080/health` from the actual ABS container using Node fetch.
Compare hashes of existing stack Compose/environment/identity/autostart files
against the pre-installation snapshot.

## Sanitized artifact path

[GitHub build override](../../compose.github.yaml) and
[deployment instructions](../deployment.md). Target-specific configuration
remains on Unraid; the local inventory snapshot is ignored under secrets/.
This record excludes private addresses, contact values and credentials.

## Claims supported and limitations

Permanent stack is registered for Compose Manager discovery, running and
healthy. Autostart and Build on Update are enabled. The Update backend fetched
GitHub main and built successfully. Private LAN and actual ABS-container
connectivity pass; existing stack files are unchanged.

No live ABS provider or library setting was changed, no AudiobookDB search
was made, and no account/API key was installed on Unraid. Health checks use
no upstream quota. Host reboot and rendered Compose Manager UI interaction
were not tested; registration was verified through the plugin's stack model.
Source updates occur when Update/build is requested, not automatically on push.

## Observed outcome

Pass: initial GitHub fetch/build and startup; Docker health healthy; LAN
health/readiness and ABS-container health HTTP 200; project/management labels;
99:100 identity, read-only root, 256 MiB configured RAM limit, shared network
alias, private LAN-only binding and unless-stopped restart policy. Compose
Manager reported successful Update, lists the stack, and reads autostart/build
settings as enabled. Existing stack configuration hashes match the baseline.

The first wrapper invocation supplied explicit files plus `-d`, which discovers
the same files again; validation rejected duplicate security options before
startup. Corrected invocation uses `-w` for workdir, and the build/start passed.
Docker emitted a host swap-limit capability warning; no swap-limit guarantee
is claimed. Actual RAM configuration was verified. Source/Compose/documentation
checks pass; no production source was changed by this deployment.

## Synthetic or live classification

Actual persistent Unraid installation and live ABS-container connectivity;
health-only HTTP reads. Earlier synthetic runtime tests remain EVD-020 evidence.

## Sanitization and redistribution notes

Only the owner's contact setting was copied from ignored development settings.
ABS credentials and AudiobookDB keys were not transferred. Public documentation
uses generic bindings; target LAN settings remain local. GitHub Actions remains
disabled, and build execution occurred entirely on Unraid.
