# Unraid Docker template and Apps publication

Status: Template runtime and public image verified; CA review pending  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

For browser-based installation today, use the [Unraid walkthrough](unraid.md).
This page covers the alternative Docker template method and maintainer tasks
for publishing the app in Community Applications (Unraid Apps).

## Docker template availability

The [template](../templates/abs-audiobookdb.xml) targets
`ghcr.io/h2oking89/abs-audiobookdb:latest`. The image is public and can be pulled
without a registry login.
An XML file in this repository does not mean the app is listed in Apps.

For manual template installation, import the XML into
`/boot/config/plugins/dockerMan/templates-user/my-abs-audiobookdb.xml`, select
it under **Docker → Add Container → Template**, and supply **Operator contact**
before applying. Keep the default public Repository value.

### Optional offline archive installation

The [v0.1.0 release](https://github.com/H2OKing89/abs-audiobookdb/releases/tag/v0.1.0)
also includes an image archive. For offline installation, download the archive and
`SHA256SUMS`, verify the archive's SHA-256 value, then load it on Unraid:

```bash
docker load -i abs-audiobookdb-0.1.0-linux-amd64-image.tar.gz
```

Import the XML as above and set **Repository** to `abs-audiobookdb:0.1.0`
for the loaded local image. This local-image substitution was tested with
Docker Manager.

## Template configuration

Put your real email or public HTTPS contact URL in **Operator contact** and
your AudiobookDB API key in Audiobookshelf's provider Authorization field.
Keep the 256 MiB limit, 192 MiB Go target, read-only filesystem, and 99:100 user.
No appdata mount is required; the container has no shell or web interface.

For LAN access, choose an unused host port and use
`http://<unraid-lan-address>:<port>` in Audiobookshelf. The default bridge port
mapping binds all host interfaces. For a shared custom Docker network, select
the same network as Audiobookshelf and use `http://abs-audiobookdb:8080`.
Enable **Autostart** if desired. Install one instance; do not use a port already
occupied by a Compose installation.

Verify `docker exec abs-audiobookdb /adapter health` and
`docker exec abs-audiobookdb /adapter version` in the Unraid terminal.
See [advanced deployment](deployment.md) for native TLS.

## Updates through Unraid's Docker page

Keep **Repository** set to
`ghcr.io/h2oking89/abs-audiobookdb:latest`. Use **Check for Updates** and the
container's **Update** action. **Force Update** downloads/reapplies the image
when you want to pull again. Your saved container settings are retained.

To roll back, edit **Repository** to an available exact tag such as
`ghcr.io/h2oking89/abs-audiobookdb:0.1.0` and apply. A manually loaded local image
has no registry updates until Repository is switched to the public image.
For Compose installations, use Compose Manager's stack update controls instead.

## Community Applications submission

The [official submission guide](https://ca.unraid.net/submit/help) requires
a public repository, an OSI license, valid app XML, and a nonempty repository
profile. This repository supplies MIT `LICENSE`, `ca_profile.xml`, `icon.svg`,
and the app XML under `templates/`.

[Public image verification](evidence/EVD-029-registry-publication.md) passed
on local Docker and actual Unraid. Test a fresh template installation before
submission. In the
[submission portal](https://ca.unraid.net/submit), enter this repository's URL,
complete **Validate**, **Scan**, and **Submit**, and address reviewer feedback.
Listing remains subject to Unraid review. Support goes to this project's
GitHub issues.

The [XML specification](https://ca.unraid.net/submit/help/repository-xml) and
[profile specification](https://ca.unraid.net/submit/help/repository-info-xml)
are the authoritative field references. Local checks run through
`./scripts/ci.sh`; these do not replace portal validation.
