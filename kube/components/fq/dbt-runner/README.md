# fq dbt-runner (deprecated)

Use `kube/components/fq/governance-orchestrator` instead. This folder is kept only for backward compatibility and is no longer included in the top-level `kube/components/fq/kustomization.yml`.

Runs a standalone `dbt + OpenMetadata ingestion` API service in namespace `fq`.

Service DNS (inside cluster):

- `http://fq-dbt-runner.fq.svc.cluster.local:8080`

Endpoints:

- `GET /health`
- `POST /run`

`POST /run` executes:

1. `dbt run`
2. `dbt test`
3. `dbt docs generate`
4. Trino metadata ingestion to OpenMetadata
5. dbt metadata ingestion to OpenMetadata

The API accepts optional overrides like `model_selector`, `trino_schema`, and `dbt_table_name`.

Runtime defaults are provided via:

- ConfigMap: `fq-dbt-runner-config`
- Secret: `fq-dbt-runner-secrets`

Update those Kubernetes configs when values change; no image rebuild is required for config-only changes.
