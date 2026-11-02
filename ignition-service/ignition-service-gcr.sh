#!/bin/bash

# check file execution permissions
if [[ ! -x $0 ]]; then
    echo "making the script executable..."
    chmod +x $0
    exec $0 "$@"
fi
set -e

# Define Ignition Maker image
IMAGE_NAME="ignition-maker"
PROJECT_ID="$(gcloud config get-value project)"
REGION="us-central1"
REPOSITORY="ignition-repo"
GCR_HOSTNAME="${REGION}-docker.pkg.dev"

# Build and push image to Google Artifact Registry
docker build -t "${GCR_HOSTNAME}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest" .
gcloud auth configure-docker "${GCR_HOSTNAME}" --quiet
docker push "${GCR_HOSTNAME}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest"

echo "Ignition Maker image built and pushed successfully!"


# # Deploy image to Google Compute Engine VM
# echo "Deploying Ignition Maker to ${VM_NAME}..."

# gcloud compute ssh "${VM_NAME}" --zone="${VM_ZONE}" --command="
#     set -e

#     sudo docker pull ${IMAGE_URI}

#     sudo docker rm -f ignition-maker 2>/dev/null || true

#     sudo docker run -d \
#         --name ignition-maker \
#         --restart unless-stopped \
#         -p 127.0.0.1:8088:8088 \
#         -e ACCEPT_IGNITION_EULA=Y \
#         -e IGNITION_EDITION=maker \
#         -v ignition_data:/usr/local/bin/ignition/data \
#         ${IMAGE_URI}
# "

# echo "Ignition Maker deployed successfully!"