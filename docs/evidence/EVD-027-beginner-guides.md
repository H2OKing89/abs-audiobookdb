# Beginner installation guide checks

Status: Local configuration and health checks pass; new rendered UI walkthrough not run  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-027

Owner requested simpler README and guides for people unfamiliar with a CLI.

## Source URL or fixture provenance

Project release and previous [deployment evidence](EVD-025-versioned-release-deployment.md).
Reviewed Compose Manager Plus [installation instructions](https://github.com/mstrhakr/compose_plugin#installation),
[user guide](https://github.com/mstrhakr/compose_plugin/blob/main/docs/user-guide.md),
and editor source for button names. Reviewed Audiobookshelf v2.37.1 provider
form and Match components, and its [official provider guide](https://github.com/audiobookshelf/audiobookshelf-docs/blob/master/docs/documentation/community/community-providers.md).

## Captured date and environment

2026-10-05 America/Chicago; local Linux/amd64, Docker Compose 5.6.0.

## Version, commit or content hash

Example pins v0.1.0 source `59415d679189a7e5ae56ef997e493afc57bd9298`.
Local smoke uses its existing released image; reported revision matches and
dirty state is false. Documentation changes follow main `ff61368`.

## Method and reproduction steps

The earlier source-build draft of [the Unraid guide](../unraid.md) was checked
before the owner selected moving image tags. Its YAML remains in the ignored
local validation file; these results do not validate the later image-pull draft.
Substitute an
invented contact and loopback port `127.0.0.1:18086:8080`. Run Compose `config
--format json`; compare source pin and runtime restrictions. Start a disposable
project with `up -d --no-build`, check the HTTP health response, version and
container restrictions, then run `down`. Run repository checks and diff checks.

## Sanitized artifact path

Updated README, [Unraid walkthrough](../unraid.md), [provider guide](../audiobookshelf.md),
[advanced deployment](../deployment.md), and [template publication guide](../community-applications.md).
Temporary validation files remain ignored under `bin/`.

## Claims supported and limitations

The pasted example is valid with its two substitutions. Released runtime
starts with its restrictions and returns the health response shown in the
guide. A new Unraid browser installation and live metadata search were not
performed; interface steps were checked against upstream documentation/source.
Source build verification remains EVD-025. No public registry or Apps listing
availability is newly claimed.

## Observed outcome

Pass: release pin, Compose syntax, 99:100, read-only root, 256 MiB limit,
192 MiB Go target, dropped capabilities, no-new-privileges, restart policy,
loopback binding, health HTTP 200 `{"status":"ok"}`, version and cleanup.
An initial validation assertion assumed the memory field was a JSON number;
Compose emits a string. Converting it to an integer passes without changing
the example. Repository syntax/link checks and `git diff --check` pass.

## Synthetic or live classification

Disposable local Docker checks; no actual Unraid or upstream API operations.

## Sanitization and redistribution notes

Only invented contact/IP examples and public release identifiers are included.
No credentials or target configuration were read or published.
