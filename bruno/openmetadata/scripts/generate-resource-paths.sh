#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_FILE="${PROJECT_ROOT}/resources/resource-paths.csv"

REPO_ROOT="${1:-/tmp/OpenMetadata-sdk-src}"
SERVICE_ROOT_REL="openmetadata-sdk/src/main/java/org/openmetadata/sdk/services"
SERVICE_ROOT="${REPO_ROOT}/${SERVICE_ROOT_REL}"

if [[ ! -d "${SERVICE_ROOT}" ]]; then
  rm -rf "${REPO_ROOT}"
  git clone --depth 1 --filter=blob:none --sparse https://github.com/open-metadata/OpenMetadata.git "${REPO_ROOT}"
  git -C "${REPO_ROOT}" sparse-checkout set "${SERVICE_ROOT_REL}"
fi

TMP_FILE="$(mktemp)"
{
  echo "service_class,resource_path,sdk_source_file"
  grep -R --line-number 'super(.*"/v1/' "${SERVICE_ROOT}" \
    | sed "s#^${REPO_ROOT}/##" \
    | awk -F: '{
        file=$1
        split($0,a,"\"")
        path=a[2]
        class=file
        sub(/^.*\//,"",class)
        sub(/\.java$/,"",class)
        print class "," path "," file
      }' \
    | sort
} > "${TMP_FILE}"

mv "${TMP_FILE}" "${OUTPUT_FILE}"
echo "Wrote ${OUTPUT_FILE}"
