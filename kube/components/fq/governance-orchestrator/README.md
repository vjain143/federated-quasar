# fq governance-orchestrator

Runs a standalone UI + API service in namespace `fq` for:

1. dbt execution against Trino
2. metadata ingestion to OpenMetadata
3. run history, sequence view, and logs in a web UI

Service DNS inside cluster:

- `http://fq-governance-orchestrator.fq.svc.cluster.local:8080`

Main endpoints:

- `GET /` (UI)
- `GET /health`
- `GET /api/runs`
- `GET /api/runs/{runId}`
- `POST /api/runs` (async)
- `POST /run` (sync, used by Kestra flow)

Runtime defaults are provided via:

- ConfigMap: `fq-governance-orchestrator-config`
- Secret: `fq-governance-orchestrator-secrets`

## Enterprise scaling notes

Current implementation keeps run history in memory (single replica behavior).
For multi-team, high-scale production environments:

1. Persist runs/logs in PostgreSQL or Elasticsearch.
2. Move execution to a worker queue (Redis/Kafka) with multiple workers.
3. Add SSO (OIDC/SAML) and RBAC at API/UI level.
4. Add rate limits, audit export, and alerting.
