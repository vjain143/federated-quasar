# AGENTS.md - Federated Quasar AI Agent Guidelines

## Architecture Overview
Federated Quasar is a Kubernetes-first data platform with three core domains:
- `fq` namespace: Data execution plane (Trino, GEX, Kestra, dbt)
- `openmetadata` namespace: Metadata plane (OpenMetadata server + ingestion)
- `aix` namespace: Governance plane (Moat policy registry, OPA decision engine)

Core data flow: `dbt/GEX -> Trino -> OpenMetadata -> Moat -> OPA -> Trino authorization`

## Key Components & Patterns
- **Trino**: Query engine with Gravitino connector for unified metadata
- **GEX**: FastAPI-based governance execution engine (see `docker/gex/src/gex_app/`)
- **Moat**: Policy control plane that compiles Rego policies into OPA bundles
- **dbt Models**: Include governance metadata via `tags` and `meta` config (see `kube/components/fq/dbt/models/fq_orders.sql`)

## Deployment & Build Workflows
- Deploy stacks: `kubectl apply -k kube/components/{fq,om,aix}`
- Build images: Run `./build.sh` in `docker/*/build.sh` (e.g., `docker/trino/build.sh`)
- GEX builds from repo root: `docker build -f docker/gex/Dockerfile -t fq-gex:1.0.2 .`
- Java components: Maven-based (see `team-sync-starter/pom.xml` with Javalin, Trino JDBC)

## Governance Conventions
- **dbt Tags**: Use `domain:*`, `classification:*`, `access:*` (e.g., `tags=['domain:enterprise', 'classification:confidential', 'access:finance_reader']`)
- **dbt Meta**: Include `data_domain`, `data_owner_team`, `data_classification`, `contains_pii`, `retention`, `access_policy` with `read_roles`/`write_roles`
- **OPA Policies**: Moat generates Rego modules in packages like `moat.authz.role` (see `docs/moat-policy-creation-mechanisms.md`)

## Integration Points
- Trino authorization: Configured with `access-control.name=opa` to call OPA
- Metadata flow: OpenMetadata ingestion pushes to Moat, which builds bundles for OPA
- Cross-namespace: fq calls openmetadata for metadata, aix for policy decisions

## Reference Files
- `ARCHITECTURE-CONSOLIDATED-L0-L3.md`: Unified architecture design
- `docs/DBT-USER-GUIDE.md`: End-to-end dbt to Trino auth flow
- `kube/components/fq/kustomization.yml`: Core stack manifests
- `docker/trino/Dockerfile`: Custom Trino with Gravitino connector</content>
<parameter name="filePath">/Users/vivek/Lab/GitHub/vjain143/federated-quasar/AGENTS.md
