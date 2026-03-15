# dbt -> Trino -> OpenMetadata Flow

This folder contains OpenMetadata workflow configs and a helper script to run
the full dbt + metadata ingestion flow.

## What it does

1. Runs dbt model(s) against Trino (`fq-trino` service in namespace `fq`).
2. Ingests Trino metadata into OpenMetadata (`fq_trino` service).
3. Ingests dbt artifacts (`manifest`, `catalog`, `run_results`) into
   OpenMetadata to enrich table metadata and lineage.

## Run

From repo root:

```bash
chmod +x kube/components/om/workflows/fq/run-dbt-trino-openmetadata-flow.sh
./kube/components/om/workflows/fq/run-dbt-trino-openmetadata-flow.sh
```

## Defaults

- OpenMetadata namespace: `openmetadata`
- Trino namespace: `fq`
- Trino endpoint: `fq-trino.fq.svc.cluster.local:8080`
- OpenMetadata API endpoint: `http://om-server:8585/api`
- dbt project dir: `kube/components/fq/dbt`

## Override examples

```bash
OM_NAMESPACE=openmetadata \
TRINO_NAMESPACE=fq \
TRINO_SCHEMA=fq_dbt \
DBT_MODEL_SELECTOR=fq_orders \
./kube/components/om/workflows/fq/run-dbt-trino-openmetadata-flow.sh
```

## Optional Trino GRANTs from dbt model

`fq_orders.sql` supports optional post-hooks to apply grants after table creation.
Set these before running the flow if the roles exist in Trino:

```bash
TRINO_READ_ROLE=finance_reader \
TRINO_WRITE_ROLE=finance_writer \
./kube/components/om/workflows/fq/run-dbt-trino-openmetadata-flow.sh
```
