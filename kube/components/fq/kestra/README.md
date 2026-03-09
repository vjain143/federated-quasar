# fq Kestra

This component deploys Kestra in namespace `fq` and preloads a flow that:

1. runs dbt against `fq-trino`
2. ingests Trino metadata into OpenMetadata
3. ingests dbt artifacts into OpenMetadata

## Resources in this folder

- `fq-kestra-service-account.yml`: runtime identity for Kestra
- `fq-kestra-role.yml`: permissions to create/read/delete execution pods
- `fq-kestra-role-binding.yml`: binds role to the service account
- `fq-kestra-deployment.yml`: Kestra standalone server deployment
- `fq-kestra-service.yml`: NodePort service for Kestra UI/API (`30882`)
- `flows/fq_dbt_to_openmetadata_sync.yml`: preloaded flow for dbt + OpenMetadata sync

## Deploy

```bash
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

Check execution logs in Kestra, then verify table and metadata:

```bash
kubectl exec -n fq deploy/fq-trino-coordinator -- trino --server localhost:8080 --user dbt --execute "SHOW TABLES FROM hms_db.fq_dbt"
```

Expected table:

- `fq_orders`

OpenMetadata validation (UI/API):

- service: `fq_trino`
- table FQN: `fq_trino.hms_db.fq_dbt.fq_orders`

## Notes

- The flow runs in a temporary pod using image `openmetadata/ingestion:1.11.3`.
- It installs `dbt-trino` at runtime inside that execution pod.
- Trino OPA policy must allow dbt operations (`CREATE TABLE`, `SELECT`, etc.).
