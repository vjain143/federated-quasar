#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${DBT_PROJECT_DIR:-/app/dbt}"
PROFILES_DIR="${DBT_PROFILES_DIR:-${PROJECT_DIR}}"
MODEL_SELECTOR="${DBT_MODEL_SELECTOR:-}"

if [[ ! -d "${PROJECT_DIR}" ]]; then
  echo "dbt project directory not found: ${PROJECT_DIR}" >&2
  exit 1
fi
case "${MODEL_SELECTOR}" in
  ""|"*"|"all"|"ALL")
    dbt run --project-dir "${PROJECT_DIR}" --profiles-dir "${PROFILES_DIR}" --no-partial-parse
    ;;
  *)
    dbt run --project-dir "${PROJECT_DIR}" --profiles-dir "${PROFILES_DIR}" --no-partial-parse --select "${MODEL_SELECTOR}"
    ;;
esac

dbt test --project-dir "${PROJECT_DIR}" --profiles-dir "${PROFILES_DIR}" --no-partial-parse
dbt docs generate --project-dir "${PROJECT_DIR}" --profiles-dir "${PROFILES_DIR}" --no-partial-parse
