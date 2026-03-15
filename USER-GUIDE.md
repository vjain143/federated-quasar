# USER GUIDE: dbt -> Trino -> OpenMetadata -> Moat -> OPA

This guide documents the full flow you asked for:

1. create sample SQL and finalize it  
2. create dbt model  
3. provide metadata in dbt model  
4. define Kestra flow to invoke dbt model  
5. run the model (UI or Kestra flow)  
6. validate table creation in Trino  
7. validate metadata in OpenMetadata  
8. validate Moat can pull metadata  
9. validate metadata becomes policy input  
10. validate Trino uses that policy path

## Architecture (important for step 10)

In this repo, bundle flow is:

- `OpenMetadata -> Moat -> OPA -> Trino authorization decisions`
- Trino does **not** pull bundles directly.
- OPA pulls bundle from Moat; Trino calls OPA (`access-control.name=opa`).

## Prerequisites

Run from repo root:

```bash
cd /Users/vivek/Lab/GitHub/federated-quasar
```

Deploy stacks (if not already deployed):

```bash
kubectl apply -k kube/components/fq
kubectl apply -k kube/components/om
kubectl apply -k kube/components/aix/kubernetes
```

Wait for readiness:

```bash
kubectl rollout status deployment/fq-trino-coordinator -n fq
kubectl rollout status deployment/om-server -n openmetadata
kubectl rollout status deployment/om-airflow -n openmetadata
kubectl rollout status deployment/fq-gex -n fq
kubectl rollout status deployment/fq-kestra -n fq
kubectl rollout status deployment/moat -n aix
kubectl rollout status deployment/opa -n aix
kubectl rollout status deployment/mysql -n aix
```

## 1) Create sample SQL and finalize it

Use this sample SQL body for orders:

```sql
select
  1 as order_id,
  'enterprise' as business_domain,
  'confidential' as sensitivity_tier,
  current_timestamp as created_at
```

## 2) Create dbt model

Create/update:

- `kube/components/fq/dbt/models/fq_orders.sql`
- `kube/components/fq/dbt/dbt_project.yml`
- `kube/components/fq/dbt/profiles.yml`
- `kube/components/fq/dbt/models/schema.yml`

The model is already present in this repo at:

- `kube/components/fq/dbt/models/fq_orders.sql`

## 3) Provide all metadata in the dbt model

Final model shape (already set in repo) should include `tags` + `meta`:

```sql
{{ config(
    materialized='table',
    alias='fq_orders_as_select',
    tags=[
      'domain:enterprise',
      'classification:confidential',
      'access:finance_reader',
      'access:finance_writer'
    ],
    meta={
      'data_domain': 'enterprise',
      'data_owner_team': 'finance-analytics',
      'data_classification': 'confidential',
      'contains_pii': false,
      'retention': 'P90D',
      'access_policy': {
        'read_roles': ['finance_reader'],
        'write_roles': ['finance_writer'],
        'purpose': 'finance reporting'
      }
    }
) }}

select
  1 as order_id,
  'enterprise' as business_domain,
  'confidential' as sensitivity_tier,
  current_timestamp as created_at
```

## 4) Define Kestra flow to invoke this dbt model

Flow file:

- `kube/components/fq/kestra/flows/fq_dbt_to_openmetadata_sync.yml`

This flow already does:

- HTTP call from Kestra to `fq-gex`
- dbt run/test/docs against Trino (inside gex)
- Trino metadata ingestion into OpenMetadata (inside gex)
- dbt metadata ingestion into OpenMetadata (inside gex)
- run history + logs visible in GEX UI

Build the Governance Execution Engine (GEX) image first (version-pinned):

```bash
./docker/gex/build.sh
```

Deploy GEX and Kestra:

```bash
kubectl apply -k kube/components/fq/gex
kubectl rollout status deployment/fq-gex -n fq

kubectl apply -k kube/components/fq/kestra
kubectl rollout status deployment/fq-kestra -n fq
```

Optional: open GEX UI locally:

```bash
kubectl port-forward -n fq svc/fq-gex 38080:8080
```

Then open:

- `http://localhost:38080`

## 5) Run the model

Option A (UI-first): run from GEX UI.

1. Open `http://localhost:38080`
2. Fill `model_selector`, `trino_schema`, `dbt_table_name`
3. Click `Start Pipeline Run`
4. Watch step sequence + logs in the right panel

Option B: run through Kestra flow.

Trigger via API:

```bash
curl -s -X POST \
  http://localhost:30882/api/v1/executions/fq.orchestration/fq_dbt_to_openmetadata_sync
```

Monitor in UI:

- `http://localhost:30882`
- Namespace: `fq.orchestration`
- Flow: `fq_dbt_to_openmetadata_sync`

## 6) Validate table has been created

```bash
kubectl exec -n fq deploy/fq-trino-coordinator -- \
  trino --server localhost:8080 --user dbt \
  --execute "SHOW TABLES FROM hms_db.fq_dbt"

kubectl exec -n fq deploy/fq-trino-coordinator -- \
  trino --server localhost:8080 --user dbt \
  --execute "SELECT * FROM hms_db.fq_dbt.fq_orders_as_select"
```

Expected table: `fq_orders_as_select`

## 7) Validate metadata in OpenMetadata for that table

Get OpenMetadata token:

```bash
OM_PASSWORD_B64="$(printf 'admin' | base64)"
OM_TOKEN="$(
  curl -s -X POST http://localhost:30585/api/v1/users/login \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"admin@open-metadata.org\",\"password\":\"${OM_PASSWORD_B64}\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["accessToken"])'
)"
```

Read table metadata:

```bash
TABLE_FQN_ENC="$(
  python3 -c "import urllib.parse; print(urllib.parse.quote('fq_trino.hms_db.fq_dbt.fq_orders_as_select', safe=''))"
)"

curl -s \
  -H "Authorization: Bearer ${OM_TOKEN}" \
  "http://localhost:30585/api/v1/tables/name/${TABLE_FQN_ENC}?fields=tags,description,owner" \
  | python3 -m json.tool
```

Expected tags include:

- `dbtTags.domain:enterprise`
- `dbtTags.classification:confidential`
- `dbtTags.access:finance_reader`
- `dbtTags.access:finance_writer`

## 8) Validate Moat is able to pull that metadata

Run OpenMetadata sync through Moat Connector API (OpenMetadata -> Moat DB):

```bash
curl -s -X POST \
  http://localhost:32080/api/v1/connectors/openmetadata/sync \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "openmetadata-default.yaml",
    "table_fqn": "fq_trino.hms_db.fq_dbt.fq_orders_as_select"
  }' | python3 -m json.tool
```

Validate Moat DB rows:

```bash
kubectl exec -n aix deploy/mysql -- \
  mysql -uroot -pchange-me-root -e "
    USE moat;
    SELECT fq_name, attribute_key, attribute_value
    FROM resource_attributes
    WHERE fq_name = 'hms_db.fq_dbt.fq_orders_as_select'
    ORDER BY attribute_key, attribute_value;
  "
```

## 9) Validate metadata is able to create policy input

Download the Moat bundle and inspect `data.json`:

```bash
TMP_DIR="$(mktemp -d)"
curl -s -H "Authorization: Bearer bearer-token" \
  http://localhost:32080/api/v1/opa/bundle/trino \
  -o "${TMP_DIR}/bundle.tar.gz"
tar -xzf "${TMP_DIR}/bundle.tar.gz" -C "${TMP_DIR}"
python3 -c "import json, pathlib; d=json.loads(pathlib.Path('${TMP_DIR}/data.json').read_text()); print(d['trino']['data_objects'].get('hms_db.fq_dbt.fq_orders_as_select'))"
```

Expected value contains metadata-derived attributes such as:

- `access::finance_reader`
- `access::finance_writer`
- `classification::confidential`
- `domain::enterprise`

## 10) Validate Trino is using the bundle path (via OPA)

Again, Trino does not pull bundle directly. Validate the real chain:

1. OPA has bundle data.
2. Trino queries OPA for authorization.

Check OPA data:

```bash
curl -s http://localhost:32181/v1/data/trino | \
  python3 -c "import json,sys; r=json.load(sys.stdin)['result']; print(r['data_objects'].get('hms_db.fq_dbt.fq_orders_as_select'))"
```

Run Trino query:

```bash
kubectl exec -n fq deploy/fq-trino-coordinator -- \
  trino --server localhost:8080 --user dbt \
  --execute "SELECT * FROM hms_db.fq_dbt.fq_orders_as_select"
```

Confirm OPA authorization calls and bundle activation in logs:

```bash
kubectl logs -n aix deploy/opa --tail=300 | grep -E "v1/data/trino/allow|Bundle loaded and activated successfully"
```

If you see `v1/data/trino/allow` requests plus bundle activation lines, Trino is using OPA decisions backed by Moat bundle data.

## Production note

The GEX UI currently stores execution history in memory. For enterprise multi-replica scale, externalize history/log state to persistent storage and add centralized authn/authz.
