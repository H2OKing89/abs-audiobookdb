# Unraid Docker template and Apps publication

Status: Template runtime verified; public registry publication and CA review pending  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

For browser-based installation today, use the [Unraid walkthrough](unraid.md).
This page covers the alternative Docker template method and maintainer tasks
for publishing the app in Community Applications (Unraid Apps).

## Docker template availability

The [template](../templates/abs-audiobookdb.xml) targets
`ghcr.io/h2oking89/abs-audiobookdb:latest`. Installing through this registry
requires the image to be published and public; that step is pending.
An XML file in this repository does not mean the app is listed in Apps.

The [v0.1.0 release](https://github.com/H2OKing89/abs-audiobookdb/releases/tag/v0.1.0)
includes an image archive. For manual installation, download the archive and
`SHA256SUMS`, verify the archive's SHA-256 value, then load it on Unraid:

```bash
docker load -i abs-audiobookdb-0.1.0-linux-amd64-image.tar.gz
```

Import the XML into
`/boot/config/plugins/dockerMan/templates-user/my-abs-audiobookdb.xml` and
select it under **Docker → Add Container → Template**. Set **Repository** to
`abs-audiobookdb:0.1.0` for the loaded local image, and supply **Operator contact**
before applying. This local-image substitution was tested with Docker Manager.

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

After the public image is available, keep **Repository** set to
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

After publishing the image, verify an anonymous pull from a clean Docker
configuration, then test template installation. In the
[submission portal](https://ca.unraid.net/submit), enter this repository's URL,
complete **Validate**, **Scan**, and **Submit**, and address reviewer feedback.
Listing remains subject to Unraid review. Support goes to this project's
GitHub issues.

The [XML specification](https://ca.unraid.net/submit/help/repository-xml) and
[profile specification](https://ca.unraid.net/submit/help/repository-info-xml)
are the authoritative field references. Local checks run through
`./scripts/ci.sh`; these do not replace portal validation.
