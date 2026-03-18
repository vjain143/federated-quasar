# Gravitino for the Next-Generation Agentic World

> "Manage your data and AI assets seamlessly with our flexible, unified governance framework and lakehouse federation capabilities."

Source: https://gravitino.apache.org

## Why Gravitino Matters Now

In AI-first and agent-driven platforms, metadata is no longer support infrastructure; it is core platform infrastructure.

When autonomous agents discover data, generate plans, and execute cross-system actions, fragmented metadata becomes a hard blocker:

- each engine has different catalog semantics
- governance becomes inconsistent
- ownership and lineage context drift across systems
- automation loses determinism

Apache Gravitino addresses this by making metadata architecture centralized and engine-independent.

## Core Abstractions

Use this mental model for Unified Metadata Fabric (UMF):

| Gravitino Concept | Practical Equivalent |
| --- | --- |
| Metalake / Namespace | Cloud account or environment boundary |
| Catalog | Data service boundary |
| Schema | Logical namespace |
| Table | Governed dataset object |

Recommended metalakes/environments for production:

- `prod`
- `uat`
- `dev`
- `sandbox`

## Main Focus in an Agentic World

Gravitino's strategic role is to provide:

- unified metadata and governance control plane
- federation across lakehouse engines and catalog backends
- a consistent metadata contract for human users and AI agents

This enables:

- centralized policy and metadata definitions
- interchangeable compute engines (Trino, Spark, Flink, etc.)
- safer autonomous workflows over data and AI assets

## Architecture Pattern

Production architecture should be service-oriented:

1. Dedicated Gravitino metadata service
2. Durable relational metadata store (MySQL/PostgreSQL)
3. Federated catalog integrations
4. Multiple engines consuming the same metadata layer

This repo implements that model with a separate `umf` namespace and dedicated infrastructure.

## UMF Stack in This Repository

Location: `kube/components/umf`

Deployed components:

- `umf-mysql`: dedicated MySQL instance for Gravitino metadata
- `umf-gravitino`: dedicated Gravitino deployment

## Deploy

```bash
kubectl apply -k kube/components/umf
```

## Verify

```bash
kubectl rollout status deployment/umf-mysql -n umf
kubectl rollout status deployment/umf-gravitino -n umf
kubectl get svc -n umf umf-mysql umf-gravitino
```

## Local Endpoints

- `umf-gravitino`: `http://localhost:30190`
- `umf-mysql`: `localhost:30406`
