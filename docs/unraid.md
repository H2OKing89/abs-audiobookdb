# Unraid installation and Community Applications

Status: Template runtime verified; public registry publication and CA review pending
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

## Choose an installation method

Use [Docker Compose](deployment.md) or the [Docker template](../templates/abs-audiobookdb.xml).
Compose Manager builds pinned GitHub source without a registry. The template
installs a versioned image through Unraid's Docker interface. Install one
instance; an existing Compose installation already occupies its configured port.

The template targets `ghcr.io/h2oking89/abs-audiobookdb:0.1.0`. It becomes
installable from that registry after the image is published and made public.
An XML file in this repository does not mean the app is listed in Community
Applications. Check the release notes for current image availability.

The [v0.1.0 release](https://github.com/H2OKing89/abs-audiobookdb/releases/tag/v0.1.0)
includes an installable image archive. Download its archive and `SHA256SUMS`,
verify the archive's SHA-256 value, then load it on Unraid:

```bash
docker load -i abs-audiobookdb-0.1.0-linux-amd64-image.tar.gz
```

For this registry-free method, set the imported template's **Repository** field
to `abs-audiobookdb:0.1.0` before Apply. The same local-image substitution was
tested with the installed Docker Manager. The distributable XML retains its
versioned GHCR reference for future public pulls.

## Docker template settings

Set **Operator contact** to your real email or public HTTPS contact URL. Put
your AudiobookDB API key in ABS's provider Authorization field. Leave the
256 MiB limit, 192 MiB Go target, read-only filesystem, and 99:100 user in place.
No appdata mount is required. This container has no shell or web interface.

For LAN access, choose an unused host port and configure ABS with
`http://<unraid-lan-address>:<port>`. The default bridge port mapping binds all
host interfaces; select exposure appropriate to your private network.
For a shared custom Docker network, select the same network as ABS and use
`http://abs-audiobookdb:8080`. Select **Autostart** in Unraid if desired.

Verify `docker exec abs-audiobookdb /adapter health` and
`docker exec abs-audiobookdb /adapter version` in the Unraid terminal.
See [deployment](deployment.md) for optional native TLS and its certificate mounts.

Before CA listing, an operator can import the XML into
`/boot/config/plugins/dockerMan/templates-user/my-abs-audiobookdb.xml` and
select it in **Docker → Add Container → Template**. Set your contact before
Apply. Do not deploy it alongside the existing Compose service on the same port.

## Community Applications submission

The [official submission guide](https://ca.unraid.net/submit/help) requires
a public repository, an OSI license, valid app XML, and a nonempty repository
profile. This repository supplies MIT `LICENSE`, `ca_profile.xml`, `icon.svg`,
and one app XML under `templates/`.

After publishing the image, verify an anonymous pull from a clean Docker
configuration, then test the template installation. In the
[submission portal](https://ca.unraid.net/submit), enter this repository's URL,
complete **Validate**, **Scan**, and **Submit**, and address reviewer feedback.
Listing remains subject to Unraid review. Support goes to this project's
GitHub issues; no unrelated forum thread is claimed.

The [XML specification](https://ca.unraid.net/submit/help/repository-xml) and
[profile specification](https://ca.unraid.net/submit/help/repository-info-xml)
are the authoritative field references. Local XML and install-policy checks
run through `./scripts/ci.sh`; these do not replace the portal's validation.
