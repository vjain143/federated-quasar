# fq Components

This folder contains the Kubernetes manifests for the `fq` stack.

The stack currently includes:

- `trino`
- `minio`
- `mysql`
- `hms`
- `opa` (shared component used for Trino authorization)

All `fq` resources now target the `fq` namespace.

## NodePort endpoints

These values come from the service manifests under this folder.

| Component | Service | Service Port | NodePort | Local Endpoint | Notes |
| --- | --- | ---: | ---: | --- | --- |
| Trino | `fq-trino` | `8080` | `30080` | `http://localhost:30080` | Trino coordinator UI/API |
| MinIO API | `fq-minio` | `9000` | `30990` | `http://localhost:30990` | S3-compatible API |
| MinIO Console | `fq-minio-console` | `9001` | `30991` | `http://localhost:30991` | Browser admin console |
| MySQL | `fq-mysql` | `3306` | `30336` | `mysql://localhost:30336` | External MySQL access |
| Hive Metastore | `fq-hms` | `9083` | `30983` | `thrift://localhost:30983` | Thrift metastore endpoint |
| OPA | `opa` | `8181` | `30081` | `http://localhost:30081` | Trino authorization policy API |

Although several service ports are named `https` in the manifests, the configured endpoints here are plain TCP/HTTP unless your app layer adds TLS separately.

## Component details

### Trino

- Folder: `kube/components/fq/trino`
- Service: `fq-trino`
- Manifest: `fq-trino-service.yml`
- URL: `http://localhost:30080`
- UI: `http://localhost:30080/ui/`
- Info API: `http://localhost:30080/v1/info`
- Statement API: `http://localhost:30080/v1/statement`

Validate:

```bash
kubectl get svc -n fq fq-trino
curl -s http://localhost:30080/v1/info
```

Authorization:

- Authentication remains password-based.
- Authorization is delegated to OPA through Trino's `opa` access-control plugin.
- OPA policy endpoints:
  - `http://opa.aix.svc.cluster.local:8181/v1/data/trino/allow`
  - `http://opa.aix.svc.cluster.local:8181/v1/data/trino/rowFilters`
  - `http://opa.aix.svc.cluster.local:8181/v1/data/trino/columnMask`

### MinIO

- Folder: `kube/components/fq/minio`
- API service: `fq-minio`
- Console service: `fq-minio-console`
- API endpoint: `http://localhost:30990`
- Console endpoint: `http://localhost:30991`

Validate:

```bash
kubectl get svc -n fq fq-minio fq-minio-console
curl -sI http://localhost:30990
curl -sI http://localhost:30991
```

### MySQL

- Folder: `kube/components/fq/mysql`
- Service: `fq-mysql`
- Host: `localhost`
- Port: `30336`

Connect:

```bash
mysql -h 127.0.0.1 -P 30336 -u root -p
```

Validate:

```bash
kubectl get svc -n fq fq-mysql
```

### Hive Metastore

- Folder: `kube/components/fq/hms`
- Service: `fq-hms`
- Host: `localhost`
- Port: `30983`
- Protocol: `thrift`

Use from clients such as Trino:

```text
thrift://fq-hms:9083
```

Use from outside the cluster through the NodePort:

```text
thrift://localhost:30983
```

Validate:

```bash
kubectl get svc -n fq fq-hms
```

### OPA

- Folder: `kube/components/opa`
- Service: `opa`
- Host: `localhost`
- Port: `30081`
- Base URL: `http://localhost:30081`

This service evaluates Trino authorization decisions for `fq-trino`.

Validate:

```bash
kubectl get svc -n aix opa
curl -s http://localhost:30081/v1/data/trino/allow
```

## Quick checks

List all fq-related services:

```bash
kubectl get svc -n fq | grep -E 'fq-trino|fq-minio|fq-minio-console|fq-mysql|fq-hms'
kubectl get svc -n aix opa
```

Expected mappings:

```text
fq-trino        8080:30080/TCP
fq-minio        9000:30990/TCP
fq-minio-console   9001:30991/TCP
fq-mysql           3306:30336/TCP
fq-hms             9083:30983/TCP
opa             8181:30081/TCP
```

## Source manifests

- `kube/components/fq/trino/fq-trino-service.yml`
- `kube/components/fq/minio/fq-minio-service.yml`
- `kube/components/fq/minio/fq-minio-console-service.yml`
- `kube/components/fq/mysql/fq-mysql-service.yml`
- `kube/components/fq/hms/fq-hms-service.yml`
- `kube/components/opa/opa-service.yml`
