#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

IMAGE_TAG="${IMAGE_TAG:-fq-dbt-runner:1.0.0}"

echo "Building ${IMAGE_TAG} from ${REPO_ROOT}"
docker build -f "${SCRIPT_DIR}/Dockerfile" -t "${IMAGE_TAG}" "${REPO_ROOT}"
echo "Built ${IMAGE_TAG}"
