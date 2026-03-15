# fq dbt -> Trino -> OpenMetadata -> Moat

This folder contains a minimal dbt project that materializes a table in
`fq-trino`, then publishes metadata to OpenMetadata.

## One-command run

If your OpenMetadata is deployed in namespace `openmetadata` and Trino in `fq`,
run the end-to-end flow script:

```bash
./kube/components/om/workflows/fq/run-dbt-trino-openmetadata-flow.sh
```

This executes dbt, ingests Trino metadata, and ingests dbt metadata.

## What this flow does

1. dbt runs a model against Trino (`hms_db.fq_dbt.fq_orders_as_select`).
2. OpenMetadata ingests Trino metadata (service + database/schema/table).
3. OpenMetadata ingests dbt artifacts (`manifest.json`, `catalog.json`,
   `run_results.json`) and enriches the same table metadata.
4. Moat can read metadata/attributes from OpenMetadata and use them as policy
   input (next step in your architecture).

## Prerequisites

- `fq-trino` is running in namespace `fq`.
- `om-server` and `om-airflow` are running in namespace `openmetadata`.
- OPA policy must allow dbt DDL operations in Trino.

If you want to run dbt inside `om-airflow` (recommended for direct artifact
ingestion), install the adapter once:

```bash
kubectl exec -n openmetadata deploy/om-airflow -- /home/airflow/.local/bin/pip install dbt-trino
```

## Step 1: Prepare local dbt runtime

```bash
cd kube/components/fq/dbt
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install dbt-core dbt-trino
```

## Step 2: Export dbt profile env vars

`profiles.yml` in this folder expects these env vars:

```bash
export DBT_PROFILES_DIR="$(pwd)"
export TRINO_HOST=localhost
export TRINO_PORT=30080
export TRINO_USER=dbt
export TRINO_CATALOG=hms_db
export TRINO_SCHEMA=fq_dbt
```

## Step 3: Create schema in Trino (once)

```bash
kubectl exec -n fq deploy/fq-trino-coordinator -- \
  trino --server localhost:8080 --user "${TRINO_USER}" \
  --execute "CREATE SCHEMA IF NOT EXISTS hms_db.fq_dbt"
```

## Step 4: Run dbt model

```bash
dbt debug
dbt run --select fq_orders
dbt test
dbt docs generate
```

Expected table:

- `hms_db.fq_dbt.fq_orders_as_select`

## Step 5: Ingest Trino metadata into OpenMetadata

Create an OpenMetadata JWT token (admin user):

```bash
export OM_JWT_TOKEN="$(
kubectl exec -n fq deploy/om-airflow -- sh -lc 'python - <<'"'"'PY'"'"'
import base64, requests
r = requests.post(
  "http://om-server:8585/api/v1/users/login",
  json={"email":"admin@open-metadata.org","password":base64.b64encode(b"admin").decode()},
  timeout=20,
)
r.raise_for_status()
print(r.json()["accessToken"])
PY'
)"
```

Copy and run the Trino ingestion workflow in `om-airflow`:

```bash
OM_AIRFLOW_POD="$(kubectl get pod -n fq -l app=om-airflow -o jsonpath='{.items[0].metadata.name}')"
kubectl cp kube/components/om/workflows/fq/trino-metadata.yaml "fq/${OM_AIRFLOW_POD}:/tmp/trino-metadata.yaml"
kubectl exec -n fq "${OM_AIRFLOW_POD}" -- sh -lc "sed -i 's|<OM_JWT_TOKEN>|${OM_JWT_TOKEN}|g' /tmp/trino-metadata.yaml"
kubectl exec -n fq "${OM_AIRFLOW_POD}" -- metadata ingest -c /tmp/trino-metadata.yaml
```

## Step 6: Ingest dbt artifacts into OpenMetadata

Copy dbt artifacts into `om-airflow` and run dbt ingestion:

```bash
kubectl exec -n fq "${OM_AIRFLOW_POD}" -- mkdir -p /tmp/fq-dbt-project/target
kubectl cp target/manifest.json "fq/${OM_AIRFLOW_POD}:/tmp/fq-dbt-project/target/manifest.json"
kubectl cp target/catalog.json "fq/${OM_AIRFLOW_POD}:/tmp/fq-dbt-project/target/catalog.json"
kubectl cp target/run_results.json "fq/${OM_AIRFLOW_POD}:/tmp/fq-dbt-project/target/run_results.json"

kubectl cp kube/components/om/workflows/fq/dbt-metadata.yaml "fq/${OM_AIRFLOW_POD}:/tmp/dbt-metadata.yaml"
kubectl exec -n fq "${OM_AIRFLOW_POD}" -- sh -lc "sed -i 's|<OM_JWT_TOKEN>|${OM_JWT_TOKEN}|g' /tmp/dbt-metadata.yaml"
kubectl exec -n fq "${OM_AIRFLOW_POD}" -- metadata ingest -c /tmp/dbt-metadata.yaml
```

## Step 7: Validate in OpenMetadata

Open OpenMetadata:

- `http://localhost:30585`

Check:

- Database Service: `fq_trino`
- Table: `hms_db.fq_dbt.fq_orders`
- dbt metadata attached to the same table (description / tests / model linkage)

## Step 8: Moat integration (next step)

Use OpenMetadata table attributes/tags as policy input in Moat. Typical pattern:

1. Pull OpenMetadata entities + tags into Moat resource attributes.
2. Map those attributes to policy conditions (`data_sensitivity`, domain, owner).
3. Evaluate access in OPA for Trino requests.
