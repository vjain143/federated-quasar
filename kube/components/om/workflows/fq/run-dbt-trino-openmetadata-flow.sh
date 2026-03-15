#!/usr/bin/env bash
set -euo pipefail

# Namespaces
OM_NAMESPACE="${OM_NAMESPACE:-openmetadata}"
TRINO_NAMESPACE="${TRINO_NAMESPACE:-fq}"

# dbt / Trino settings
TRINO_HOST="${TRINO_HOST:-fq-trino.fq.svc.cluster.local}"
TRINO_PORT="${TRINO_PORT:-8080}"
TRINO_USER="${TRINO_USER:-dbt}"
TRINO_CATALOG="${TRINO_CATALOG:-hms_db}"
TRINO_SCHEMA="${TRINO_SCHEMA:-fq_dbt}"
TRINO_READ_ROLE="${TRINO_READ_ROLE:-}"
TRINO_WRITE_ROLE="${TRINO_WRITE_ROLE:-}"
DBT_PROJECT_DIR="${DBT_PROJECT_DIR:-kube/components/fq/dbt}"
DBT_MODEL_SELECTOR="${DBT_MODEL_SELECTOR:-fq_orders}"
DBT_TABLE_NAME="${DBT_TABLE_NAME:-fq_orders_v2}"

# OpenMetadata settings
OM_SERVER_API="${OM_SERVER_API:-http://om-server:8585/api}"
OM_ADMIN_EMAIL="${OM_ADMIN_EMAIL:-admin@open-metadata.org}"
OM_ADMIN_PASSWORD="${OM_ADMIN_PASSWORD:-admin}"

WORKFLOW_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRINO_WORKFLOW_TEMPLATE="${WORKFLOW_DIR}/trino-metadata.yaml"
DBT_WORKFLOW_TEMPLATE="${WORKFLOW_DIR}/dbt-metadata.yaml"

for bin in kubectl sed; do
  if ! command -v "${bin}" >/dev/null 2>&1; then
    echo "Missing required binary: ${bin}" >&2
    exit 1
  fi
done

if [[ ! -d "${DBT_PROJECT_DIR}" ]]; then
  echo "dbt project not found: ${DBT_PROJECT_DIR}" >&2
  exit 1
fi

if [[ ! -f "${TRINO_WORKFLOW_TEMPLATE}" || ! -f "${DBT_WORKFLOW_TEMPLATE}" ]]; then
  echo "Workflow templates not found in ${WORKFLOW_DIR}" >&2
  exit 1
fi

echo "Locating OpenMetadata Airflow pod in namespace ${OM_NAMESPACE}..."
OM_AIRFLOW_POD="$(
  kubectl get pod -n "${OM_NAMESPACE}" -l app=om-airflow -o jsonpath='{.items[0].metadata.name}'
)"
if [[ -z "${OM_AIRFLOW_POD}" ]]; then
  echo "No om-airflow pod found in namespace ${OM_NAMESPACE}" >&2
  exit 1
fi

echo "Preparing isolated dbt runtime in ${OM_AIRFLOW_POD}..."
kubectl exec -n "${OM_NAMESPACE}" "${OM_AIRFLOW_POD}" -- bash -lc '
  set -euo pipefail
  if [[ ! -x /tmp/dbt-venv/bin/dbt ]]; then
    python -m venv /tmp/dbt-venv
    /tmp/dbt-venv/bin/pip install --upgrade pip
    /tmp/dbt-venv/bin/pip install dbt-trino
  fi
'

echo "Creating Trino schema ${TRINO_CATALOG}.${TRINO_SCHEMA}..."
kubectl exec -n "${TRINO_NAMESPACE}" deploy/fq-trino-coordinator -- \
  trino --server localhost:8080 --user "${TRINO_USER}" \
  --execute "CREATE SCHEMA IF NOT EXISTS ${TRINO_CATALOG}.${TRINO_SCHEMA}"

echo "Copying dbt project into Airflow pod..."
kubectl exec -n "${OM_NAMESPACE}" "${OM_AIRFLOW_POD}" -- rm -rf /tmp/fq-dbt-project
kubectl cp "${DBT_PROJECT_DIR}" "${OM_NAMESPACE}/${OM_AIRFLOW_POD}:/tmp/fq-dbt-project"

echo "Running dbt debug/run/test/docs against Trino..."
kubectl exec -n "${OM_NAMESPACE}" "${OM_AIRFLOW_POD}" -- bash -lc "
  set -euo pipefail
  export PATH=\"\$PATH:/home/airflow/.local/bin\"
  export DBT_PROFILES_DIR=/tmp/fq-dbt-project
  export TRINO_HOST='${TRINO_HOST}'
  export TRINO_PORT='${TRINO_PORT}'
  export TRINO_USER='${TRINO_USER}'
  export TRINO_CATALOG='${TRINO_CATALOG}'
  export TRINO_SCHEMA='${TRINO_SCHEMA}'
  export TRINO_READ_ROLE='${TRINO_READ_ROLE}'
  export TRINO_WRITE_ROLE='${TRINO_WRITE_ROLE}'
  cd /tmp/fq-dbt-project
  /tmp/dbt-venv/bin/dbt debug
  /tmp/dbt-venv/bin/dbt run --select '${DBT_MODEL_SELECTOR}'
  /tmp/dbt-venv/bin/dbt test
  /tmp/dbt-venv/bin/dbt docs generate
"

echo "Requesting OpenMetadata JWT token from ${OM_SERVER_API}..."
OM_JWT_TOKEN="$(
  kubectl exec -n "${OM_NAMESPACE}" "${OM_AIRFLOW_POD}" -- bash -lc "
export OM_SERVER_API='${OM_SERVER_API}'
export OM_ADMIN_EMAIL='${OM_ADMIN_EMAIL}'
export OM_ADMIN_PASSWORD='${OM_ADMIN_PASSWORD}'
python - <<'PY'
import base64
import os
import requests

resp = requests.post(
    os.environ['OM_SERVER_API'] + '/v1/users/login',
    json={
        'email': os.environ['OM_ADMIN_EMAIL'],
        'password': base64.b64encode(os.environ['OM_ADMIN_PASSWORD'].encode()).decode(),
    },
    timeout=30,
)
resp.raise_for_status()
print(resp.json()['accessToken'])
PY
"
)"

if [[ -z "${OM_JWT_TOKEN}" ]]; then
  echo "Failed to generate OpenMetadata JWT token" >&2
  exit 1
fi

echo "Copying ingestion workflows into pod..."
kubectl cp "${TRINO_WORKFLOW_TEMPLATE}" "${OM_NAMESPACE}/${OM_AIRFLOW_POD}:/tmp/trino-metadata.yaml"
kubectl cp "${DBT_WORKFLOW_TEMPLATE}" "${OM_NAMESPACE}/${OM_AIRFLOW_POD}:/tmp/dbt-metadata.yaml"

kubectl exec -n "${OM_NAMESPACE}" "${OM_AIRFLOW_POD}" -- sh -lc "
  sed -i 's|<OM_JWT_TOKEN>|${OM_JWT_TOKEN}|g' /tmp/trino-metadata.yaml
  sed -i 's|<OM_JWT_TOKEN>|${OM_JWT_TOKEN}|g' /tmp/dbt-metadata.yaml
"

echo "Running OpenMetadata Trino metadata ingestion..."
kubectl exec -n "${OM_NAMESPACE}" "${OM_AIRFLOW_POD}" -- sh -lc \
  "metadata ingest -c /tmp/trino-metadata.yaml"

echo "Running OpenMetadata dbt metadata ingestion..."
kubectl exec -n "${OM_NAMESPACE}" "${OM_AIRFLOW_POD}" -- sh -lc \
  "metadata ingest -c /tmp/dbt-metadata.yaml"

echo "Flow completed."
echo "OpenMetadata UI: http://localhost:30585"
echo "Expected entity: fq_trino.hms_db.${TRINO_SCHEMA}.${DBT_TABLE_NAME}"
