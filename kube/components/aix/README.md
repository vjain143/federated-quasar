# Authorization Intelligence eXchange (AIX)

`AIX` is the authorization layer for the platform.

It groups together:

- `OPA` as the policy decision point
- `Moat` as the policy intelligence and policy management layer
- `MySQL` as Moat's backing store

## Purpose

Authorization Intelligence eXchange centralizes policy evaluation and policy authoring for data platform access control.

In this repo, the intended model is:

- Trino and other services call OPA for authorization decisions
- Moat owns higher-level policy logic, policy generation, and policy workflows
- OPA executes the published Rego policies
- MySQL stores Moat application data

## Namespace Context

Set your active `kubectl` namespace to `aix` while working on this stack:

```bash
kubectl config set-context --current --namespace=aix
```

## Components

### OPA

OPA is the runtime policy engine in the `aix` Kubernetes stack.

- Folder: `kube/components/aix/kubernetes/opa`
- Service: `opa`
- Namespace: `aix`
- Service type: `NodePort`
- Port: `8181`
- NodePort: `32181`
- Local endpoint: `http://localhost:32181`

Primary use:

- Evaluate Rego policies for Trino authorization
- Pull policy bundles from Moat
- Serve policy decisions via the OPA HTTP API

Key policy path used for Trino:

- `http://localhost:32181/v1/data/trino/allow`

### Moat

Moat is the policy intelligence layer paired with OPA.

Kubernetes resources:

- Folder: `kube/components/aix/kubernetes/moat`
- Service: `moat`
- Namespace: `aix`
- Service type: `NodePort`
- Port: `8000`
- NodePort: `32080`
- Local endpoint: `http://localhost:32080`

Role in AIX:

- Define and manage higher-level authorization logic
- Generate and publish policy bundles for OPA
- Support richer authorization workflows beyond static Rego rules
- Persist policy metadata and application state in MySQL

Implementation source:

- App source: `docker/moat`

### MySQL

MySQL is the data store used by Moat in the same Kubernetes namespace.

- Folder: `kube/components/aix/kubernetes/mysql`
- Service: `mysql`
- Namespace: `aix`
- Service type: `NodePort`
- Port: `3306`
- NodePort: `31306`

## Active Trino Integration

The `fq` Trino stack is configured to use OPA, not Trino's file-based access-control engine.

Active Trino setting:

- [access-control.properties](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/fq/trino/configs/access-control.properties): `access-control.name=opa`

Active OPA endpoints used by Trino:

- `http://opa.aix.svc.cluster.local:8181/v1/data/trino/allow`
- `http://opa.aix.svc.cluster.local:8181/v1/data/trino/rowFilters`
- `http://opa.aix.svc.cluster.local:8181/v1/data/trino/columnMask`

Important implication:

- [rules.json](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/fq/trino/configs/rules.json) is mounted into Trino, but it is not the active authorization source while `access-control.name=opa` is enabled.
- There is no Trino file-based group provider configured in the current `fq` stack.

## Network flow

The intended service-to-service path is:

`Trino -> OPA -> Moat -> MySQL`

The repo now includes explicit `NetworkPolicy` resources for that chain:

- Trino egress allows `fq-trino-coordinator` to call `opa:8181` in namespace `aix`
- OPA ingress allows traffic from `fq-trino-coordinator` to `opa:8181`
- OPA egress allows traffic to `moat:8000`
- Moat ingress allows traffic from `opa` to `moat:8000`
- Moat egress allows traffic to `mysql:3306`
- MySQL ingress allows traffic from `moat` to `mysql:3306`

DNS egress is also allowed for Trino, OPA, and Moat so in-cluster service discovery keeps working.

## Implementation Guide

This is the intended step-by-step implementation path if you want Trino authorization to be managed through Moat and enforced by OPA.

### 1. Deploy the AIX stack

Apply the namespace, Moat, MySQL, OPA, and their network policies:

```bash
kubectl apply -k kube/components/aix/kubernetes
```

Verify:

```bash
kubectl get pods -n aix
kubectl get svc -n aix
kubectl get networkpolicy -n aix
```

### 2. Deploy the `fq` data stack

Apply the full `fq` namespace-scoped stack:

```bash
kubectl apply -k kube/components/fq
```

Verify:

```bash
kubectl get pods -n fq
kubectl get svc -n fq
```

### 3. Confirm Trino is using OPA

Check the mounted Trino access-control settings:

```bash
kubectl exec -n fq deploy/fq-trino-coordinator -- cat etc/trino/access-control.properties
```

You should see:

- `access-control.name=opa`
- OPA URLs pointing at `opa.aix.svc.cluster.local:8181`

### 4. Confirm cross-namespace connectivity

From the Trino coordinator, verify DNS and the OPA policy endpoint:

```bash
kubectl exec -n fq deploy/fq-trino-coordinator -- getent hosts opa.aix.svc.cluster.local
kubectl exec -n fq deploy/fq-trino-coordinator -- curl -sS http://opa.aix.svc.cluster.local:8181/v1/data/trino/allow
```

Expected:

- DNS resolves to the `aix/opa` service IP
- OPA returns JSON such as `{"result":false}`

### 5. Define users and groups in Moat

Moat exposes SCIM endpoints for users and groups:

- `/api/scim/v2/Users`
- `/api/scim/v2/Groups`

In the current local setup, `api.scim.auth_method: none` is configured, so these routes are open for development use.

Example calls:

```bash
curl -s http://localhost:32080/api/scim/v2/ServiceProviderConfig
curl -s http://localhost:32080/api/scim/v2/Groups
curl -s http://localhost:32080/api/scim/v2/Users
```

Implementation model:

- Create users in Moat.
- Create groups in Moat.
- Assign users to groups in Moat.
- Treat Moat as the source of truth for identity metadata used in policy generation.

### 6. Put authorization logic in Rego, not in `rules.json`

Because Trino is using the OPA plugin, your authorization logic should live in the OPA bundle that Moat generates and OPA serves.

That means:

- Use Moat data plus Rego to decide `allow`
- Use Rego to return `rowFilters`
- Use Rego to return `columnMask`

Do not treat Trino's file-based `rules.json` as the primary policy layer in this setup.

### 7. Encode group-based access in Rego

The current sample policy is only a placeholder:

- [policy.rego](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/aix/kubernetes/moat/configs/policy.rego)

It does not yet evaluate users or groups.

The next real implementation step is to make the bundle include:

- principals
- group membership
- resource metadata
- access rules by group

Then write Rego that evaluates:

- which groups the requesting user belongs to
- which operations those groups are allowed to perform
- which rows should be filtered
- which columns should be masked

### 8. Let OPA fetch bundles from Moat

OPA is already configured to pull the `trino` bundle from Moat:

- [config.yaml](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/aix/kubernetes/opa/configs/config.yaml)

The flow is:

1. Moat builds or refreshes the bundle
2. OPA downloads the bundle from Moat
3. Trino queries OPA for decisions

### 9. Validate end to end

Basic health checks:

```bash
curl -s http://localhost:32080/api/scim/v2/Groups
curl -s http://localhost:32181/v1/data/trino/allow
curl -s http://localhost:30080/v1/info
```

Cluster checks:

```bash
kubectl get pods -n aix
kubectl get pods -n fq
```

### 10. Clean up the architecture if you want one source of truth

To reduce confusion, the recommended cleanup is:

- Keep Trino on `access-control.name=opa`
- Keep Moat as the source of users, groups, and policy inputs
- Keep OPA as the decision engine
- Stop relying on file-based Trino `rules.json` for authorization logic

If you want file-based Trino rules instead, that is a different architecture and should be implemented explicitly as a separate export/sync path.

## Current layout

```text
kube/components/aix/
  README.md
  kubernetes/
    aix-platform-namespace.yaml
    kustomization.yaml
    moat/
    mysql/
    opa/
```

## Quick Deploy

Create or update the AIX stack:

```bash
kubectl apply -k kube/components/aix/kubernetes
```

If Trino should use OPA authorization, apply the `fq` manifests as well:

```bash
kubectl apply -k kube/components/fq
```

## Verify

Check the namespace and services:

```bash
kubectl get ns aix
kubectl get svc -n aix
kubectl get networkpolicy -n aix
```

Check the OPA service:

```bash
kubectl get svc -n aix opa
```

Inspect the rendered manifests before applying:

```bash
kubectl kustomize kube/components/aix/kubernetes
kubectl kustomize kube/components/fq
```

Call the OPA API through the NodePort:

```bash
curl -s http://localhost:32181/v1/data/trino/allow
```

## Notes for developers

- The AIX Kubernetes resources run in namespace `aix`, not `default`
- The `fq` Trino resources run in namespace `fq`
- The OPA ingress policy currently allows the `fq-trino-coordinator` path through the configured network policies and verified connectivity
- The OPA bundle config points to Moat at `http://moat:8000/api/v1/opa/`
- `rules.json` is present in the `fq` Trino image config, but it is not the active authorization engine while OPA is enabled
