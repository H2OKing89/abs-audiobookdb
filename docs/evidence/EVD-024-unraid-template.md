# Unraid template and publication requirements

Status: Installed parser and runtime checks passed; registry/CA listing pending  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## ID: EVD-024

ADR-007; audit item 6; owner requests Compose and Unraid app distribution.

## Source URL or fixture provenance

Primary [CA submission guide](https://ca.unraid.net/submit/help),
[app XML reference](https://ca.unraid.net/submit/help/repository-xml), and
[repository profile reference](https://ca.unraid.net/submit/help/repository-info-xml).
Local project-authored template, profile, icon and parser harness.

## Captured date and environment

2026-10-05; actual Unraid 7.3.2 host. Installed Docker Manager's `Helpers.php`
provided `xmlToVar` and `xmlToCommand`; this was not a VM check.

## Version, commit or content hash

Template targets `ghcr.io/h2oking89/abs-audiobookdb:0.1.0`. Source release tag
records template/profile/icon content. Target parser file is the installed host
version; no claim about future Unraid versions is made.

## Method and reproduction steps

Local CI parses XML/SVG and checks version pin, required operator contact,
runtime restrictions and absence of bundled API/development credentials.
Copy `spikes/MVP-001/unraid_template_check.php` to a temporary target path and
pipe the template into `php -d short_open_tag=1 <harness-path>` over SSH.
Optional image argument creates a disposable, network-disabled template-derived
container for health/version/shutdown checks and removes it afterward.

## Sanitized artifact path

[Docker template](../../templates/abs-audiobookdb.xml),
[profile](../../ca_profile.xml), [icon](../../icon.svg),
and [Unraid instructions](../unraid.md).

## Claims supported and limitations

CA expects valid XML, public source, OSI license and repository profile.
This repository supplies those assets. Template installation additionally needs
the declared image to be anonymously pullable. CA Validate/Scan/Submit and review
remain external steps; this record does not claim marketplace listing.

## Observed outcome

Installed parser checks passed: version 2, versioned image, port mapping,
read-only, UID/GID, memory and nonprivileged mode. Initial standalone invocation
failed because its harness omitted the parser's global network map; adding that
synthetic map resolved the harness error. No live container was changed by parsing.
Python template regression tests passed. Registry publication remains pending
package-writing credentials; Docker template pull was not run.

## Synthetic or live classification

Actual target parser with synthetic input; no upstream API calls or ABS changes.

## Sanitization and redistribution notes

No operator contact, credentials, private host names or target addresses are
included in the distributable template/profile. Icon is project-authored SVG.

## Subsequent template runtime verification

The final release image created a disposable container through the installed
Docker Manager parser, with synthetic contact and networking disabled. Creation,
startup, health, version, shutdown and cleanup passed.
[EVD-025](EVD-025-versioned-release-deployment.md) records its exact revision.
Public registry pull and CA listing remain pending.
