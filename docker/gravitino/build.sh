#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-fq-gravitino}"
IMAGE_TAG="${IMAGE_TAG:-1.2.0}"

echo "Building Gravitino image ${IMAGE_NAME}:${IMAGE_TAG}"
docker build --tag "${IMAGE_NAME}:${IMAGE_TAG}" --no-cache .
echo "Image built successfully."
