# Install on Unraid using your browser

Status: Public image verified; Apps listing pending  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

This guide uses **Compose Manager Plus** in Unraid's web interface. You paste
one configuration and change two values. No terminal commands, downloaded
image archives, or source checkout are needed.

The image is public; no GitHub account or registry login is required.

The adapter is not in Unraid Apps yet. If it is already running on your server,
skip installation and [connect Audiobookshelf](audiobookshelf.md).

## Before you start

Have Audiobookshelf running and your AudiobookDB API key ready. Find your
Unraid server's local IP address, such as `192.168.1.20`. You can find it under
Unraid's **Settings → Network Settings**.

Your server needs internet access to download the image. The `latest` tag
receives tested releases, so you can install updates using the same settings.

## 1. Open Compose Manager

In Unraid's **Apps** tab, search for **Compose Manager Plus** and install the
plugin if you do not already have it. Open **Docker → Compose**; some layouts
show **Compose** as its own tab.

Click **Add New Stack** (or **Add Stack**), name it `abs-audiobookdb`, and
create it. A stack is simply a saved configuration for this container.

## 2. Paste the configuration

Open **Edit Stack → Compose** (or **Compose File**). Replace the editor's
contents with everything in this box:

```yaml
services:
  adapter:
    image: ghcr.io/h2oking89/abs-audiobookdb:latest
    pull_policy: always
    user: "99:100"
    environment:
      AUDIOBOOKDB_CONTACT: "YOUR_EMAIL_ADDRESS"
      GOMEMLIMIT: "192MiB"
    ports:
      - "YOUR_UNRAID_IP:8080:8080"
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 256m
    stop_grace_period: 10s
    restart: unless-stopped
    labels:
      net.unraid.docker.managed: "composeman"
      net.unraid.docker.icon: "https://raw.githubusercontent.com/H2OKing89/abs-audiobookdb/main/icon.svg"
```

Change these **two values**, keeping the quotation marks:

| Find | Replace with |
| --- | --- |
| `YOUR_EMAIL_ADDRESS` | Your real contact email, or a public HTTPS contact URL. This is sent to AudiobookDB with API requests. |
| `YOUR_UNRAID_IP` | Your server's local IP address; for example, `192.168.1.20`. |

Your AudiobookDB API key goes into Audiobookshelf in step 4.

## 3. Save and start

Save the configuration. Leave **Rebuild Images on Update** / **Build on Update**
disabled: this installation downloads a ready-built image. Close the editor,
choose **Compose Up**, and confirm if asked. Once running, enable the stack's
**Autostart** toggle so it starts with your Unraid array.

Open `http://YOUR_UNRAID_IP:8080/health` in your browser, replacing the IP as
above. You should see `{"status":"ok"}`. This is a
status page; the searches happen inside Audiobookshelf.

## 4. Connect Audiobookshelf

Follow [Connect Audiobookshelf](audiobookshelf.md). For this installation,
the provider URL is `http://YOUR_UNRAID_IP:8080`, with your IP substituted.
Leave `/health` off the provider URL.

## Install an update

In Compose Manager, select the stack's **Check for Updates** / **Check Updates**
action, then **Update** / **Update Stack** when a new image is available. To
pull again regardless of the update indicator, choose **Force Update**.
Unraid downloads the image and recreates the container with your saved settings.

Leave `:latest` in place; you do not need to edit a version number. Updates
install when you choose an update action. Autostart does not schedule updates.

To return to an earlier release, edit the image line to an available exact
version, such as `ghcr.io/h2oking89/abs-audiobookdb:0.1.0`, save, and run
**Compose Up**. Keep your contact and port settings. Restore `:latest` when
ready to receive newer releases again.

An older installation with a `build:` section is a source build. Back up its
configuration and switch that stack to the image-based example above. Remove the build section, disable Build on Update, and preserve
your contact, network and port choices. The native Docker **Force Update**
control is for Docker-template installations; use the stack controls for Compose.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Cannot find the adapter in Apps | Install Compose Manager Plus and follow this guide. The adapter's own listing is pending. |
| Image pull fails | Check internet access and that the image name and tag match the example. No registry login is required. |
| Error says a port is already allocated | Change the first `8080` in the port line to an unused port, such as `8081`. Save and run Compose Up again. Use that port in the health and provider URLs. |
| Container exits with a contact error | Check that you replaced `YOUR_EMAIL_ADDRESS` with your real email or HTTPS contact URL. |
| Browser cannot open the health page | Confirm the stack is running and the IP and port match the configuration. Open the container's logs in Unraid's Docker page for errors. |
| Health works but a search fails | Follow [Audiobookshelf troubleshooting](audiobookshelf.md#troubleshooting). Health checks only confirm the adapter is running. |

This example uses your private LAN address. Keep it on your private network;
port forwarding on your router is unnecessary.

## Other installation methods

For shared Docker networking, HTTPS, or installation outside Unraid, see
[advanced deployment settings](deployment.md). The [Docker template and Apps
submission guide](community-applications.md) covers the alternative template
method and its current publication requirements.

Button names vary by plugin version. See the plugin's
[installation instructions](https://github.com/mstrhakr/compose_plugin#installation)
and [user guide](https://github.com/mstrhakr/compose_plugin/blob/main/docs/user-guide.md)
for its current interface.
