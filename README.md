# Federated Quasar

Federated Quasar is a Kubernetes-first data platform blueprint that combines:

- data execution (`Trino`, `Hive Metastore`, `MinIO`, `Gravitino`)
- metadata management (`OpenMetadata`)
- governance and authorization (`Moat`, `OPA`)
- orchestration + user-facing execution (`Kestra`, `Governance Execution Engine (GEX)`, `dbt`)

The main end-to-end flow in this repo is:

`dbt/GEX -> Trino -> OpenMetadata -> Moat -> OPA -> Trino authorization`

## Repository Structure

### Core stack manifests

- `kube/components/fq`: data/query/orchestration stack in namespace `fq`
- `kube/components/om`: OpenMetadata stack in namespace `openmetadata`
- `kube/components/aix/kubernetes`: governance stack in namespace `aix`

### Runtime images and app code

- `docker/gex`: Governance Execution Engine (UI + API for dbt + metadata ingestion)
- `docker/trino`: custom Trino image with Gravitino connector
- `docker/gravitino`, `docker/hive-metastore`, and other runtime image folders

### Platform docs

- `docs/DBT-USER-GUIDE.md`: full dbt -> Trino -> OpenMetadata -> Moat -> OPA flow
- `docs/EXECUTIVE-README.md`: executive architecture summary
- `docs/EXECUTIVE-FLOW-DECK.md`: presentation-style flow deck
- `kube/components/*/README.md`: per-component operational docs

### Additional component libraries (optional)

The repo also includes reusable/optional component catalogs under:

- `kube/components/data-catalogs`
- `kube/components/data-control`
- `kube/components/data-explorer`
- `kube/components/data-gateway`
- `kube/components/data-observability`
- `kube/components/data-orchestration`
- `kube/components/data-pipe`

These are not all deployed by default in the `fq` stack.

## Active Namespaces and Components

### `fq` namespace (data + execution plane)

From `kube/components/fq/kustomization.yml`:

- `gex` (`fq-gex`)
- `gravitino` (`fq-gravitino`)
- `trino` (`fq-trino`, `fq-trino-coordinator`)
- `hms` (`fq-hms`)
- `minio` (`fq-minio`, `fq-minio-console`)
- `mysql` (`fq-mysql`)
- `kestra` (`fq-kestra`)
- plus supporting configs, policies, service accounts

### `openmetadata` namespace (metadata plane)

From `kube/components/om/kustomization.yml`:

- `om-mysql`
- `om-elasticsearch`
- `om-server`
- `om-ingestion` (Airflow-based ingestion service)

### `aix` namespace (governance + policy plane)

From `kube/components/aix/kubernetes/kustomization.yaml`:

- `mysql` (Moat persistence)
- `moat` (metadata-to-policy + connector UI/API)
- `opa` (policy decision point for Trino)

## Quick Start

### Prerequisites

- Kubernetes cluster (local or remote)
- `kubectl`
- `docker` (if rebuilding local images)

### Deploy core stacks

```bash
kubectl apply -k kube/components/fq
kubectl apply -k kube/components/om
kubectl apply -k kube/components/aix/kubernetes
```

### Verify rollout

```bash
kubectl rollout status deployment/fq-trino-coordinator -n fq
kubectl rollout status deployment/fq-gex -n fq
kubectl rollout status deployment/fq-kestra -n fq
kubectl rollout status deployment/fq-gravitino -n fq
kubectl rollout status deployment/fq-hms -n fq

kubectl rollout status deployment/om-server -n openmetadata
kubectl rollout status deployment/om-airflow -n openmetadata

kubectl rollout status deployment/moat -n aix
kubectl rollout status deployment/opa -n aix
```

## Local Endpoints (NodePort)

### `fq`

- Trino UI/API: `http://localhost:30080`
- GEX UI/API: `http://localhost:30881`
- Kestra UI/API: `http://localhost:30882`
- Gravitino API/UI: `http://localhost:30090`
- Hive Metastore thrift: `thrift://localhost:30983`
- MinIO API: `http://localhost:30990`
- MinIO Console: `http://localhost:30991`
- FQ MySQL: `localhost:30336`

### `openmetadata`

- OpenMetadata API/UI: `http://localhost:30585`
- OpenMetadata Admin: `http://localhost:30586`
- Airflow UI: `http://localhost:30808`
- OM MySQL: `localhost:30306`
- Elasticsearch: `http://localhost:30920`

### `aix`

- Moat API/UI: `http://localhost:32080`
- OPA API: `http://localhost:32181`
- AIX MySQL: `localhost:31306`

## Key Operational Flows

### 1) Data + metadata execution

Use GEX or Kestra to execute dbt against Trino and ingest metadata to OpenMetadata.

- GEX: `kube/components/fq/gex`
- Kestra flow: `kube/components/fq/kestra/flows/fq_dbt_to_openmetadata_sync.yml`

### 2) Metadata to policy

Moat connector syncs OpenMetadata entities into Moat resources/attributes, then publishes OPA bundles.

- Moat connectors UI route: `/connectors`
- OPA pulls bundle from Moat and serves Trino authorization decisions

### 3) Trino authorization

Trino uses OPA plugin endpoints (`allow`, `rowFilters`, `columnMask`) for access control.

## Build Notes

### Rebuild GEX image

```bash
./docker/gex/build.sh
```

### Rebuild Trino image

```bash
cd docker/trino
./build.sh
```

## Troubleshooting

- Check pods by namespace:
  - `kubectl get pods -n fq`
  - `kubectl get pods -n openmetadata`
  - `kubectl get pods -n aix`
- Check service endpoints:
  - `kubectl get svc -n fq`
  - `kubectl get svc -n openmetadata`
  - `kubectl get svc -n aix`
- Tail logs:
  - `kubectl logs -n fq deploy/fq-gex`
  - `kubectl logs -n openmetadata deploy/om-server`
  - `kubectl logs -n aix deploy/moat`
  - `kubectl logs -n aix deploy/opa`

---

For deeper implementation detail, start with:

- `docs/DBT-USER-GUIDE.md`
- `kube/components/fq/README.md`
- `kube/components/aix/kubernetes/moat/README.md`
- `kube/components/aix/kubernetes/opa/README.md`
