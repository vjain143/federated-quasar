#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-fq-gravitino}"
IMAGE_TAG="${IMAGE_TAG:-1.2.0}"
DOCKERHUB_REPO="${DOCKERHUB_REPO:-vjain143/fq-gravitino}"

echo "Log in to Docker Hub"
docker login
echo "Tag the image"
docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${DOCKERHUB_REPO}:${IMAGE_TAG}"
echo "Push the image to Docker Hub"
docker push "${DOCKERHUB_REPO}:${IMAGE_TAG}"
