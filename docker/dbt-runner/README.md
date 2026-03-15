# dbt Runner Image (deprecated)

Use `docker/governance-orchestrator` instead. This image remains for backward compatibility.

This image packages the `fq` dbt project and exposes an HTTP API that:

1. runs dbt against Trino
2. ingests Trino metadata to OpenMetadata
3. ingests dbt metadata to OpenMetadata

## Build

From repo root:

```bash
./docker/dbt-runner/build.sh
```

Default image tag:

- `fq-dbt-runner:1.0.0`

Override tag:

```bash
IMAGE_TAG=my-registry.example.com/fq-dbt-runner:1.0.0 ./docker/dbt-runner/build.sh
```

## Included paths

- dbt project: `/app/dbt`
- dbt script: `/app/run-dbt.sh`
- API app: `/app/runner_api.py`

## Runtime API

- `GET /health`
- `POST /run`

Example:

```bash
curl -s -X POST http://localhost:8080/run \
  -H 'Content-Type: application/json' \
  -d '{
    "model_selector": "fq_orders",
    "trino_schema": "fq_dbt",
    "dbt_table_name": "fq_orders_v2",
    "ingest_openmetadata": true
  }' | python3 -m json.tool
```

## Runtime env vars

- `DBT_PROJECT_DIR` (default `/app/dbt`)
- `DBT_PROFILES_DIR` (default `/app/dbt`)
- `DBT_MODEL_SELECTOR` (default `fq_orders`)
- `TRINO_HOST`, `TRINO_PORT`, `TRINO_USER`, `TRINO_CATALOG`, `TRINO_SCHEMA`
- `DBT_TABLE_NAME`
- `OM_SERVER_API`, `OM_ADMIN_EMAIL`, `OM_ADMIN_PASSWORD`
- `OM_SERVICE_NAME`, `OM_TRINO_USERNAME`

In Kubernetes, these are set through `fq-dbt-runner-config` (ConfigMap) and
`fq-dbt-runner-secrets` (Secret).
