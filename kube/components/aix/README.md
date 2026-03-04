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

- `http://localhost:32181/v1/data/trino/authz/allow`

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

## Network flow

The intended service-to-service path is:

`Trino -> OPA -> Moat -> MySQL`

The repo now includes explicit `NetworkPolicy` resources for that chain:

- Trino egress allows `trino-coordinator` to call `opa:8181` in namespace `aix`
- OPA ingress allows traffic from `trino-coordinator` to `opa:8181`
- OPA egress allows traffic to `moat:8000`
- Moat ingress allows traffic from `opa` to `moat:8000`
- Moat egress allows traffic to `mysql:3306`
- MySQL ingress allows traffic from `moat` to `mysql:3306`

DNS egress is also allowed for Trino, OPA, and Moat so in-cluster service discovery keeps working.

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

## Deploy

Create or update the AIX stack:

```bash
kubectl apply -k kube/components/aix/kubernetes
```

If Trino should use OPA authorization, apply the Trino manifests as well:

```bash
kubectl apply -k kube/components/trino
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
kubectl kustomize kube/components/trino
```

Call the OPA API through the NodePort:

```bash
curl -s http://localhost:32181/v1/data/trino/authz/allow
```

## Notes for developers

- The AIX Kubernetes resources run in namespace `aix`, not `default`
- The Trino egress policy assumes the Trino coordinator runs in namespace `default`
- If Trino runs in another namespace, update the namespace selector in `kube/components/aix/kubernetes/opa/aix-opa-ingress-network-policy.yaml`
- The OPA bundle config points to Moat at `http://moat:8000/api/v1/opa/`
