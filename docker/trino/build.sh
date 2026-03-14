#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-fq-trino}"
IMAGE_TAG="${IMAGE_TAG:-472.1.2}"
CONNECTOR_URL="${CONNECTOR_URL:-https://github.com/apache/gravitino/releases/download/v1.2.0/gravitino-trino-connector-469-472-1.2.0.tar.gz}"

echo "Building ${IMAGE_NAME}:${IMAGE_TAG}"
docker build \
  --build-arg GRAVITINO_CONNECTOR_URL="${CONNECTOR_URL}" \
  --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
  .
echo "Built ${IMAGE_NAME}:${IMAGE_TAG}"
