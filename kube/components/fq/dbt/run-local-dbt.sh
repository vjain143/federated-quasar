#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

ask_yes_no() {
  local prompt="$1"
  local default_answer="${2:-y}"
  local choice

  while true; do
    if [[ "${default_answer}" == "y" ]]; then
      read -r -p "${prompt} [Y/n]: " choice
      choice="${choice:-Y}"
    else
      read -r -p "${prompt} [y/N]: " choice
      choice="${choice:-N}"
    fi

    case "${choice}" in
      [Yy]|[Yy][Ee][Ss]) return 0 ;;
      [Nn]|[Nn][Oo]) return 1 ;;
      *) echo "Please answer yes or no." ;;
    esac
  done
}

activate_venv() {
  if [[ -f ".venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
    return 0
  fi
  return 1
}

echo "Local dbt runner"
echo "Project: ${SCRIPT_DIR}"

if ask_yes_no "Create or refresh .venv and install dbt dependencies?" "n"; then
  python3 -m venv .venv
  activate_venv
  pip install --upgrade pip
  pip install dbt-core dbt-trino
elif ask_yes_no "Activate existing .venv (if present)?" "y"; then
  if ! activate_venv; then
    echo ".venv not found. Continue without virtualenv."
  fi
fi

if ! command -v dbt >/dev/null 2>&1; then
  echo "dbt is not installed or not in PATH." >&2
  echo "Run again and choose dependency installation, or install manually." >&2
  exit 1
fi

export DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-${SCRIPT_DIR}}"
export TRINO_HOST="${TRINO_HOST:-localhost}"
export TRINO_PORT="${TRINO_PORT:-30080}"
export TRINO_USER="${TRINO_USER:-dbt}"
export TRINO_CATALOG="${TRINO_CATALOG:-hms_db}"
export TRINO_SCHEMA="${TRINO_SCHEMA:-fq_dbt}"

MODEL_SELECTOR="${DBT_MODEL_SELECTOR:-fq_orders_summary}"

echo
echo "Using environment:"
echo "  DBT_PROFILES_DIR=${DBT_PROFILES_DIR}"
echo "  TRINO_HOST=${TRINO_HOST}"
echo "  TRINO_PORT=${TRINO_PORT}"
echo "  TRINO_USER=${TRINO_USER}"
echo "  TRINO_CATALOG=${TRINO_CATALOG}"
echo "  TRINO_SCHEMA=${TRINO_SCHEMA}"
echo "  DBT_MODEL_SELECTOR=${MODEL_SELECTOR}"
echo

if ask_yes_no "Run dbt debug?" "y"; then
  dbt debug
fi

if ask_yes_no "Run dbt model selector '${MODEL_SELECTOR}'?" "y"; then
  dbt run --select "${MODEL_SELECTOR}"
fi

if ask_yes_no "Run dbt tests for selector '${MODEL_SELECTOR}'?" "y"; then
  dbt test --select "${MODEL_SELECTOR}"
fi

if ask_yes_no "Generate dbt docs?" "n"; then
  dbt docs generate
fi

echo
echo "Done."
