


# Build and run docker file locally 

docker build -t ignition-maker:v1 .

docker run -d --name ignition-maker -p 8090:8088 -e ACCEPT_IGNITION_EULA=Y ignition-maker:v1



./ignition-service-gcr.sh








# Ignition Maker — Google Cloud Deployment

Deploy an Ignition Maker Edition Docker image from a local Windows/VS Code environment to a Google Compute Engine VM. Develop Perspective projects against the running cloud gateway.

## Architecture

```text
Windows PC (VS Code + Docker Desktop)
    → Build Docker image
    → Push to Google Artifact Registry
    → Pull image on Compute Engine (Ubuntu + Docker Compose)
    → Ignition Maker gateway (persistent Docker volume)
    → Cloud SQL PostgreSQL (private network)
```

## Prerequisites

- Google Cloud project with billing enabled; Compute Engine, Artifact Registry, and Cloud SQL APIs enabled.
- Google Cloud CLI (`gcloud`) and Docker Desktop installed locally.
- Ubuntu Compute Engine VM (start with `e2-medium`, 4 GB RAM), Docker Engine and Compose plugin installed.
- Artifact Registry Docker repository, e.g. `ignition-repo` in `us-central1`.
- VM service account with Artifact Registry Reader access and working Docker registry authentication.
- Ignition Maker Edition license and compliance with its personal/noncommercial terms.
- Optional: Cloud SQL PostgreSQL with private connectivity from the VM.

## 1. Build and push locally

Run from VS Code terminal (Bash/WSL; replace placeholders):

```bash
PROJECT_ID="your-gcp-project"
REGION="us-central1"
REPO="ignition-repo"
IMAGE="ignition-maker"
TAG="v1"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:${TAG}"

gcloud auth login
gcloud config set project "$PROJECT_ID"
gcloud auth configure-docker "${REGION}-docker.pkg.dev"

docker build --platform linux/amd64 -t "$IMAGE_URI" .
docker push "$IMAGE_URI"
```

The local `Dockerfile` should be based on a compatible official Ignition image. Store license keys and passwords outside the image. A gateway backup can initialize a **new** data volume; it will not overwrite an already-initialized gateway on later image deployments.

## 2. Connect to the VM

```bash
gcloud compute ssh ignition-portfolio-vm --zone=us-central1-a --project="$PROJECT_ID"
```

For routine file editing and Docker management, use **VS Code Remote - SSH**. `gcloud compute config-ssh` can create SSH config entries for VS Code when using standard SSH connectivity.

## 3. Pull and run on the VM

On the VM, create `/opt/ignition-portfolio/compose.yaml`:

```yaml
services:
  ignition:
    image: ${IMAGE_URI}
    container_name: ignition-portfolio
    restart: unless-stopped
    ports:
      - "127.0.0.1:8088:8088"
    environment:
      ACCEPT_IGNITION_EULA: "Y"
      IGNITION_EDITION: maker
      IGNITION_LICENSE_KEY: ${IGNITION_LICENSE_KEY}
      GATEWAY_ADMIN_USERNAME: admin
      GATEWAY_ADMIN_PASSWORD: ${GATEWAY_ADMIN_PASSWORD}
    volumes:
      - ignition_data:/usr/local/bin/ignition/data

volumes:
  ignition_data:
```

Create `/opt/ignition-portfolio/.env` with restricted permissions (`chmod 600 .env`):

```dotenv
IMAGE_URI=us-central1-docker.pkg.dev/your-gcp-project/ignition-repo/ignition-maker:v1
IGNITION_LICENSE_KEY=replace-with-your-license-key
GATEWAY_ADMIN_PASSWORD=replace-with-strong-password
```

Then deploy:

```bash
cd /opt/ignition-portfolio
gcloud auth configure-docker us-central1-docker.pkg.dev
docker compose pull
docker compose up -d
docker compose ps
docker logs -f ignition-portfolio
```

> Ensure the VM's Docker credential helper can authenticate to Artifact Registry using its service account. Keep `.env` out of Git; Secret Manager is preferable for long-term use.

## 4. Open Ignition securely from Windows

From a **local** PowerShell terminal, keep this SSH tunnel running:

```powershell
gcloud compute ssh ignition-portfolio-vm `
  --zone=us-central1-a `
  --project=your-gcp-project `
  -- -N -L 8090:localhost:8088
```

Open **http://localhost:8090** in a local browser. Install Ignition Designer Launcher on Windows and connect it to the tunneled gateway. Your project edits are saved on the cloud gateway, not in the local Docker image.

Do **not** expose gateway port 8088 publicly. For portfolio visitors, use a separately secured HTTPS reverse proxy (for example, Caddy), with appropriate gateway administration and Designer restrictions.

## 5. Subsequent deployments

1. Make Dockerfile/module/infrastructure changes locally.
2. Build and push a **new image tag** (e.g. `v2`).
3. Update `IMAGE_URI` in the VM's `.env`.
4. On the VM run:

```bash
cd /opt/ignition-portfolio
docker compose pull
docker compose up -d
docker compose ps
```

The named `ignition_data` volume survives container recreation. **New images do not automatically replace Perspective projects in an existing gateway volume.** Develop projects using remote Designer, or use a separate controlled import/restore workflow.

## 6. Daily workflow

- **VS Code Remote SSH:** Manage VM files, Compose configuration, and logs.
- **Ignition Designer (Windows):** Build Perspective views, tags, scripts, and named queries directly on the cloud gateway.
- **Browser via SSH tunnel:** Administer and test the gateway.
- **Cloud SQL:** Configure the PostgreSQL connection inside Ignition, using private networking and secure credentials.
- **Backups:** Regularly export Ignition gateway backups and retain copies off the VM. A persistent volume is not a backup.

## Useful commands (on VM)

```bash
docker ps
docker logs --tail 100 ignition-portfolio
docker compose restart
docker stats
```

## Cost starting point

Use a single `e2-medium` VM (2 shared vCPU, 4 GB RAM) with a 30 GB disk. Monitor memory/CPU usage. Cloud SQL can cost more than the VM; confirm actual prices in Google Cloud's pricing calculator.
