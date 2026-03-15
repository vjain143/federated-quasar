# fq Kestra

This component deploys Kestra in namespace `fq` and preloads a flow that:

1. calls `fq-governance-orchestrator` over HTTP
2. runs dbt against `fq-trino`
3. ingests Trino + dbt metadata into OpenMetadata

## Resources in this folder

- `fq-kestra-service-account.yml`: runtime identity for Kestra
- `fq-kestra-role.yml`: permissions to create/read/delete execution pods
- `fq-kestra-role-binding.yml`: binds role to the service account
- `fq-kestra-deployment.yml`: Kestra standalone server deployment
- `fq-kestra-service.yml`: NodePort service for Kestra UI/API (`30882`)
- `flows/fq_dbt_to_openmetadata_sync.yml`: preloaded flow for dbt + OpenMetadata sync

## Build governance orchestrator image

The governance orchestrator deployment expects this image tag:

- `fq-governance-orchestrator:1.0.2`

Build it from repo root:

```bash
./docker/governance-orchestrator/build.sh
```

## Deploy governance orchestrator + Kestra

```bash
kubectl apply -k kube/components/fq/governance-orchestrator
kubectl rollout status deployment/fq-governance-orchestrator -n fq

kubectl apply -k kube/components/fq/kestra
kubectl rollout status deployment/fq-kestra -n fq
```

Open UI:

- `http://localhost:30882`

## Run the flow

Use API trigger:

```bash
curl -X POST http://localhost:30882/api/v1/executions/fq.orchestration/fq_dbt_to_openmetadata_sync
```

Or run from UI:

- Namespace: `fq.orchestration`
- Flow: `fq_dbt_to_openmetadata_sync`

## Validate

Check execution logs in Kestra, then verify table creation:

```bash
kubectl exec -n fq deploy/fq-trino-coordinator -- trino --server localhost:8080 --user dbt --execute "SHOW TABLES FROM hms_db.fq_dbt"
```

Expected table:

- `fq_orders_as_select`

OpenMetadata validation:

- table FQN: `fq_trino.hms_db.fq_dbt.fq_orders_as_select`
- expected dbt tags: `domain:enterprise`, `classification:confidential`, `access:finance_reader`, `access:finance_writer`

## Notes

- Flow task type is `io.kestra.plugin.core.http.Request` (core plugin).
- Kestra no longer needs Docker socket access for this flow.
- dbt + metadata ingestion run inside `fq-governance-orchestrator:1.0.2`.
- Trino OPA policy must allow dbt operations (`CREATE TABLE`, `SELECT`, etc.).
