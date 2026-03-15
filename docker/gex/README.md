# Governance Execution Engine (GEX) Image

This image packages the `fq` dbt project and exposes a UI + API service that:

1. runs dbt against Trino
2. ingests Trino metadata to OpenMetadata
3. ingests dbt metadata to OpenMetadata
4. keeps in-memory run history, step sequence, and logs

## Build

From repo root:

```bash
./docker/gex/build.sh
```

Default image tag:

- `fq-gex:1.0.2`

Override tag:

```bash
IMAGE_TAG=my-registry.example.com/fq-gex:1.0.2 ./docker/gex/build.sh
```

## Endpoints

- `GET /` (UI)
- `GET /health`
- `GET /api/runs`
- `GET /api/runs/{runId}`
- `POST /api/runs` (async run trigger)
- `POST /api/runs/{runId}/stop`
- `GET /api/projects`
- `POST /api/projects/upload` (upload local dbt project folder from UI)
- `POST /run` (sync compatibility endpoint for Kestra)

## Code layout

- `app.py`: thin entrypoint for uvicorn
- `src/gex_app/main.py`: FastAPI app assembly
- `src/gex_app/web/`: API routes and UI assets
- `src/gex_app/services/`: execution and ingestion workflows
- `src/gex_app/state.py`: in-memory run/project state
- `src/gex_app/schemas.py`: request models

## Runtime env vars

- `DBT_PROJECT_DIR` (default `/app/dbt`)
- `DBT_PROFILES_DIR` (default `/app/dbt`)
- `DBT_MODEL_SELECTOR` (optional; default `*` to run all models with dependency order)
- `TRINO_HOST`, `TRINO_PORT`, `TRINO_USER`, `TRINO_CATALOG`, `TRINO_SCHEMA`
- `DBT_TABLE_NAME` (optional table filter override; leave empty to auto-resolve from selected model)
- `OM_SERVER_API`, `OM_ADMIN_EMAIL`, `OM_ADMIN_PASSWORD`
- `OM_SERVICE_NAME`, `OM_TRINO_USERNAME`
- `RUN_HISTORY_LIMIT` (default `200`)

## Scale note

This image provides in-memory run history for a single app instance.
For large-scale multi-instance production, move run history/log storage to an external datastore.
