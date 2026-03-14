#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-fq-trino}"
IMAGE_TAG="${IMAGE_TAG:-472.1.2}"
DOCKERHUB_REPO="${DOCKERHUB_REPO:-vjain143/fq-trino}"

echo "Log in to Docker Hub"
docker login
echo "Tagging image ${IMAGE_NAME}:${IMAGE_TAG} as ${DOCKERHUB_REPO}:${IMAGE_TAG}"
docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${DOCKERHUB_REPO}:${IMAGE_TAG}"
echo "Pushing ${DOCKERHUB_REPO}:${IMAGE_TAG}"
docker push "${DOCKERHUB_REPO}:${IMAGE_TAG}"
