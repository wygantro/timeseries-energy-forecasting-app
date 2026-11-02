# Ignition Maker — Google Cloud VM Setup

Quick reference for hosting the Ignition Maker Edition portfolio on a Google Compute Engine VM using Docker, Artifact Registry, a custom domain, and Caddy HTTPS.

## 1. Create the Google Cloud VM

In **Compute Engine → VM instances**, create a VM with:

| Setting | Value |
| --- | --- |
| Name | `ignition-portfolio-vm` |
| Zone | `us-central1-a` |
| OS | Ubuntu 24.04 LTS |
| Machine type | `e2-medium` (4 GB RAM) |
| Boot disk | 30 GB standard persistent disk |
| External IP | Reserved static IPv4 (`ignition-portfolio-ip`) |
| Firewall | Allow HTTP (80) and HTTPS (443) |

Current project: `ignition-portfolio-513416`  
Current reserved IP: `34.135.101.215`  
Domain: `rmw-ignition.com`

> These are environment-specific values. Confirm the static IP and project ID if recreating the VM. Compute, disk, IP, and other services may incur separate charges.

## 2. Point the domain to the VM

In **Squarespace → Domain → DNS settings**, create/update the apex record:

| Type | Host | Value |
| --- | --- | --- |
| A | `@` | `34.135.101.215` |

Keep existing Squarespace domain-connect and email TXT/CNAME records. DNS propagation may take time.

Optional check from Windows PowerShell:

```powershell
nslookup rmw-ignition.com
```

## 3. Install Docker on the VM

Open **Google Cloud Console → Compute Engine → VM instances → SSH** and run:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo docker --version
sudo systemctl status docker --no-pager
```

Confirm Docker reports `active (running)`.

## 4. Pull the Ignition image from Artifact Registry

The image is built and pushed from the local development machine. The VM only needs to **pull** it.

```bash
# If required, configure root's Docker credential helper:
sudo gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

sudo docker pull \
  us-central1-docker.pkg.dev/ignition-portfolio-513416/ignition-repo/ignition-maker:latest
```

The VM's service account needs permission to read Artifact Registry images (for example, **Artifact Registry Reader**) and suitable access scopes. If pulls fail, check those permissions and authentication.

## 5. Start Ignition Maker

```bash
sudo docker run -d \
  --name ignition-maker \
  --restart unless-stopped \
  -p 127.0.0.1:8088:8088 \
  -e ACCEPT_IGNITION_EULA=Y \
  -e IGNITION_EDITION=maker \
  -v ignition_data:/usr/local/bin/ignition/data \
  us-central1-docker.pkg.dev/ignition-portfolio-513416/ignition-repo/ignition-maker:latest
```

The named Docker volume `ignition_data` preserves Gateway configuration and projects across container replacements. **Back up this volume/Gateway before major updates or VM deletion**; a volume is not a backup.

Check startup:

```bash
sudo docker ps
sudo docker logs --tail 50 ignition-maker
curl -I http://127.0.0.1:8088
```

A `302` redirect to `/welcome` is normal before initial Gateway commissioning.

> Port 8088 is bound to localhost only. Do not expose it directly to the internet.

## 6. Install and configure Caddy (HTTPS)

```bash
sudo apt install -y caddy nano
sudo systemctl status caddy --no-pager
sudo nano /etc/caddy/Caddyfile
```

Replace the Caddyfile contents with:

```caddyfile
rmw-ignition.com {
    reverse_proxy 127.0.0.1:8088
}
```

Save in Nano: **Ctrl+O**, **Enter**, **Ctrl+X**.

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager
```

Caddy automatically obtains and renews HTTPS certificates when DNS points to the VM and inbound ports **80/443** are reachable. Visit `https://rmw-ignition.com` and complete Ignition's initial Gateway commissioning over HTTPS.

Secure the Gateway administrator account with a strong unique password; review public administrative access and any authentication/public-address settings for your deployment.

## 7. Future image updates

From the **local development machine**, use the repository's deployment script (if configured) to build, push, and redeploy the image. The basic flow is:

1. Build the Docker image for `linux/amd64`.
2. Push the new image to `us-central1-docker.pkg.dev/ignition-portfolio-513416/ignition-repo/ignition-maker:latest`.
3. SSH into the VM, pull the updated image, and replace the container **using the same `ignition_data` volume**.
4. Verify `sudo docker ps`, Gateway logs, and the HTTPS site.

**Do not delete the persistent volume during redeployment.** Back up the Gateway before changes. Note that rebuilding the image does not by itself update an already-running container.

## 8. Changing the domain later

1. Point the new domain's DNS **A `@`** record to the VM's reserved static IP.
2. Change the domain in `/etc/caddy/Caddyfile` (or temporarily list both domains).
3. Validate and reload Caddy.
4. Test HTTPS and update any Ignition public-address, Perspective, or authentication redirect settings that use the old domain.

To serve both domains temporarily:

```caddyfile
rmw-ignition.com, new-domain.com {
    reverse_proxy 127.0.0.1:8088
}
```

## Useful commands

```bash
sudo docker ps                           # Running containers
sudo docker logs --tail 100 ignition-maker # Recent Gateway logs
sudo docker restart ignition-maker       # Restart Gateway container
sudo systemctl status docker --no-pager  # Docker status
sudo systemctl status caddy --no-pager   # Caddy status
sudo journalctl -u caddy -n 50 --no-pager # HTTPS / proxy troubleshooting
curl -I http://127.0.0.1:8088            # Local Gateway response
```

## Notes

- Ignition Maker Edition has license restrictions; confirm that the intended public portfolio use complies with its terms.
- Keep ports **80/443** open for Caddy, and keep Ignition's **8088** private.
- A static external IP avoids DNS changes when the VM restarts, but it must remain reserved/attached appropriately.
- This README documents the setup performed in November 2026; versions and cloud UI labels may change.
