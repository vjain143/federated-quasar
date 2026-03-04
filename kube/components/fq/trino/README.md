# fq-trino

`fq-trino` uses password authentication and OPA-backed authorization.

The `fq-trino` resources deploy into the `fq` namespace. OPA is shared from the `aix` namespace.

## Endpoints

- Trino UI: `http://localhost:30080/ui/`
- Trino info API: `http://localhost:30080/v1/info`
- OPA API: `http://localhost:30081`

## Auth flow

- Authentication: `PASSWORD`
- Authorization: Trino `opa` access-control plugin

Trino calls these OPA decisions:

- `http://opa.aix.svc.cluster.local:8181/v1/data/trino/allow`
- `http://opa.aix.svc.cluster.local:8181/v1/data/trino/rowFilters`
- `http://opa.aix.svc.cluster.local:8181/v1/data/trino/columnMask`

## Starter Rego behavior

The sample policy in [policy.rego](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/opa/opa-config/policy.rego) defines:

- `admin` and `trino`: full access
- `analyst` and `readonly`: read-only access
- `service`: read-oriented service access
- Row filter on `iceberg.sales.orders` for analyst users
- Column mask on `iceberg.hr.employees.ssn` for analyst users

## Validate

```bash
kubectl get svc -n fq fq-trino
curl -s http://localhost:30080/v1/info
kubectl get svc -n aix opa
curl -s http://localhost:30081/v1/data/trino/allow
```
