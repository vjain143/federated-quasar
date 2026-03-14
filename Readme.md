# Building a Trino + Gravitino Stack with Dynamic Catalogs (Gravitino 1.2.0)

This README is written as a Medium-style implementation journal for the work completed on **March 14, 2026**, upgrading and wiring Trino with the newly released **Gravitino 1.2.0** (released on **March 13, 2026**).

The goal was practical:

1. Build a Trino image that includes the Gravitino connector.
2. Build and deploy Gravitino `1.2.0`.
3. Deploy both to Kubernetes.
4. Verify connectivity.
5. Create catalogs from SQL through Trino using Gravitino.

## Why this change matters

Running Trino with externalized catalog governance through Gravitino gives you a cleaner control plane for catalog management. Instead of baking static catalog files for every source, you can create and manage catalogs through API and SQL workflows.

In this setup:

- Trino runs as query engine (`472`).
- Gravitino runs as metadata/catalog service (`1.2.0`).
- Trino uses the Gravitino connector to communicate with Gravitino.
- Dynamic catalog management is enabled on Trino coordinator.

## Architecture used

- Namespace: `fq`
- Trino coordinator deployment: `fq-trino-coordinator`
- Trino worker statefulset: `fq-trino-worker`
- Gravitino deployment: `gravitino`
- Gravitino service port: `8090`
- Trino service port: `8080`

---

## 1) Trino image with Gravitino connector

Connector artifact used:

`https://github.com/apache/gravitino/releases/download/v1.2.0/gravitino-trino-connector-469-472-1.2.0.tar.gz`

### `docker/trino/Dockerfile`

```dockerfile
ARG TRINO_VERSION=472
ARG GRAVITINO_CONNECTOR_URL=https://github.com/apache/gravitino/releases/download/v1.2.0/gravitino-trino-connector-469-472-1.2.0.tar.gz

FROM alpine:3.21 AS connector
ARG GRAVITINO_CONNECTOR_URL
RUN apk add --no-cache curl tar gzip
RUN mkdir -p /opt/gravitino && \
    curl -fL "${GRAVITINO_CONNECTOR_URL}" -o /tmp/gravitino-connector.tar.gz && \
    tar -xzf /tmp/gravitino-connector.tar.gz -C /opt/gravitino --strip-components=1 && \
    rm -f /tmp/gravitino-connector.tar.gz

FROM trinodb/trino:${TRINO_VERSION}
ENV TRINO_PLUGIN_DIR=/usr/lib/trino/plugin
USER root

RUN mkdir -p "${TRINO_PLUGIN_DIR}/gravitino"
COPY --from=connector /opt/gravitino/ "${TRINO_PLUGIN_DIR}/gravitino/"

COPY gravitino.properties /etc/trino/catalog/gravitino.properties

USER trino
```

### `docker/trino/build.sh`

```bash
#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-fq-trino}"
IMAGE_TAG="${IMAGE_TAG:-472.1.2}"
CONNECTOR_URL="${CONNECTOR_URL:-https://github.com/apache/gravitino/releases/download/v1.2.0/gravitino-trino-connector-469-472-1.2.0.tar.gz}"

echo "Building ${IMAGE_NAME}:${IMAGE_TAG}"
docker build \
  --build-arg GRAVITINO_CONNECTOR_URL="${CONNECTOR_URL}" \
  --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
  .
echo "Built ${IMAGE_NAME}:${IMAGE_TAG}"
```

Build command:

```bash
cd docker/trino
./build.sh
```

---

## 2) Gravitino 1.2.0 image

### `docker/gravitino/Dockerfile`

```dockerfile
# Use a maintained Java 17 runtime
FROM eclipse-temurin:17-jdk-jammy

RUN apt-get update && apt-get install -y wget tar procps bash && rm -rf /var/lib/apt/lists/*

# Set environment variables (Change as needed)
ENV GRAVITINO_VERSION=1.2.0
ENV GRAVITINO_HOME=/opt/gravitino
ENV GRAVITINO_BINARY_URL="https://github.com/apache/gravitino/releases/download/v1.2.0/gravitino-${GRAVITINO_VERSION}-bin.tar.gz"
ENV GRAVITINO_ICEBERG_URL="https://github.com/apache/gravitino/releases/download/v1.2.0/gravitino-iceberg-rest-server-${GRAVITINO_VERSION}-bin.tar.gz"



# Install dependencies
RUN apt-get update && apt-get install -y wget tar && rm -rf /var/lib/apt/lists/*

# Create directory for Gravitino
RUN mkdir -p $GRAVITINO_HOME

RUN mkdir -p $GRAVITINO_HOME/logs \
    chmod 777 $GRAVITINO_HOME/logs

# Select which version to download based on environment
# Default to main Gravitino
ARG GRAVITINO_TYPE=binary
RUN if [ "$GRAVITINO_TYPE" = "binary" ]; then \
       wget -O /tmp/gravitino.tar.gz $GRAVITINO_BINARY_URL; \
    else \
       wget -O /tmp/gravitino.tar.gz $GRAVITINO_ICEBERG_URL; \
    fi && \
    tar -xzf /tmp/gravitino.tar.gz -C $GRAVITINO_HOME --strip-components=1 && \
    rm /tmp/gravitino.tar.gz

# Set working directory
WORKDIR $GRAVITINO_HOME

# Expose default Gravitino port
EXPOSE 8090

# Start Gravitino
CMD ["./bin/gravitino-server", "start"]
```

### `docker/gravitino/build.sh`

```bash
#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-fq-gravitino}"
IMAGE_TAG="${IMAGE_TAG:-1.2.0}"

echo "Building Gravitino image ${IMAGE_NAME}:${IMAGE_TAG}"
docker build --tag "${IMAGE_NAME}:${IMAGE_TAG}" --no-cache .
echo "Image built successfully."
```

Build command:

```bash
cd docker/gravitino
./build.sh
```

---

## 3) Kubernetes deployments used

### `kube/components/data-catalogs/gravitino/gravitino-deployment.yml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gravitino
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gravitino
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: gravitino
    spec:
      containers:
      - name: gravitino
        image: fq-gravitino:1.2.0
        env:
          - name: METADATA_STORE_TYPE
            value: "jdbc"
          - name: METADATA_STORE_JDBC_URL
            value: "jdbc:mysql://mysql:3306/gravitino_db?useSSL=false&serverTimezone=UTC"
          - name: METADATA_STORE_JDBC_USER
            value: "gravitino"
          - name: METADATA_STORE_JDBC_PASSWORD
            value: "password"
          - name: MINIO_ROOT_USER
            value: minio
          - name: MINIO_ROOT_PASSWORD
            value: minio123

          # Default Catalog Configuration (Iceberg)
          - name: CATALOG_DEFAULT.name
            value: "default_iceberg"
          - name: CATALOG_DEFAULT.type
            value: "iceberg"
          - name: CATALOG_DEFAULT.warehouse
            value: "s3://gravitino-iceberg/"
          - name: CATALOG_DEFAULT.catalog-impl
            value: "org.apache.iceberg.jdbc.JdbcCatalog"
          - name: CATALOG_DEFAULT.uri
            value: "jdbc:mysql://mysql:3306/gravitino"
        ports: 
          - containerPort: 8090
        #command: ["/bin/sh", "-c", "sleep 600"]
        command: [ "/bin/sh", "-c" ]
        args:
          - |            
            export JAVA_OPTS="-Dcom.sun.management.jmxremote.port=9999 -XX:+UnlockExperimentalVMOptions -XX:-UseContainerSupport -Dcom.sun.management.jmxremote=false -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false"
            export JAVA_TOOL_OPTIONS="-Djdk.internal.platform.cgroupv2.disable=true"
            /opt/gravitino/bin/gravitino.sh run
        imagePullPolicy: IfNotPresent
```

### `kube/components/fq/trino/fq-trino-deployment.yml` (coordinator)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fq-trino-coordinator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fq-trino-coordinator
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: fq-trino-coordinator
    spec:
      containers:
      - image: fq-trino:472.1.2
        imagePullPolicy: IfNotPresent
        name: trino
        ports:
          - containerPort: 8080
        env:
          - name: API_MODEL
            value: "gpt-3.5-turbo-16k"
          - name: API_KEY
            value: ""
          - name: API_ENDPOINT
            value: ""
          - name: MYSQL_ROOT_USER
            value: root
          - name: MYSQL_ROOT_PASSWORD
            value: password
          - name: MINIO_ROOT_USER
            value: minio
          - name: MINIO_ROOT_PASSWORD
            value: minio123
        command: ["/usr/lib/trino/bin/run-trino"]
        args: ["-v"]
        volumeMounts:
          # trino config files
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/config.properties
            subPath: config.properties.coordinator
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/jvm.config
            subPath: jvm.config
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/node.properties
            subPath: node.properties
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/password-authenticator.properties
            subPath: password-authenticator.properties
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/password.db
            subPath: password.db
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/access-control.properties
            subPath: access-control.properties
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/rules.json
            subPath: rules.json
          # trino datasource config files
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/gravitino.properties
            subPath: gravitino.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/hms_db.properties
            subPath: hms_db.properties
          #- name: trino-datasource-configmap-volume
           # mountPath: etc/trino/catalog/llm.properties
           # subPath: llm.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/iceberg.properties
            subPath: iceberg.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/minio.properties
            subPath: minio.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/steampipe_db.properties
            subPath: steampipe_db.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/nessie.properties
            subPath: nessie.properties
          #- name: trino-datasource-configmap-volume
          #  mountPath: etc/trino/catalog/trino.properties
          #  subPath: trino.properties
      volumes:
        - name: fq-trino-configs-volume
          configMap:
            name: fq-trino-configs
        - name: fq-trino-datasource-configs-volume
          configMap:
            name: fq-trino-datasource-configs
```

### `kube/components/fq/trino/fq-trino-statefulset.yml` (worker)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: fq-trino-worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fq-trino-worker
  template:
    metadata:
      labels:
        app: fq-trino-worker
    spec:
      containers:
      - image: fq-trino:472.1.2
        imagePullPolicy: IfNotPresent
        name: trino
        ports:
          - containerPort: 8080
        env:
          - name: API_MODEL
            value: "gpt-3.5-turbo-16k"
          - name: API_KEY
            value: ""
          - name: API_ENDPOINT
            value: ""
          - name: MYSQL_ROOT_USER
            value: root
          - name: MYSQL_ROOT_PASSWORD
            value: password
          - name: MINIO_ROOT_USER
            value: minio
          - name: MINIO_ROOT_PASSWORD
            value: minio123
        command: ["/usr/lib/trino/bin/run-trino"]
        args: ["-v"]
        volumeMounts:
          # trino config files
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/config.properties
            subPath: config.properties.worker
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/jvm.config
            subPath: jvm.config
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/node.properties
            subPath: node.properties
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/password-authenticator.properties
            subPath: password-authenticator.properties
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/password.db
            subPath: password.db
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/access-control.properties
            subPath: access-control.properties
          - name: fq-trino-configs-volume
            mountPath: /etc/trino/rules.json
            subPath: rules.json
          # trino datasource config files
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/gravitino.properties
            subPath: gravitino.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/hms_db.properties
            subPath: hms_db.properties
         # - name: trino-datasource-configmap-volume
         #   mountPath: etc/trino/catalog/llm.properties
         #   subPath: llm.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/iceberg.properties
            subPath: iceberg.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/minio.properties
            subPath: minio.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/steampipe_db.properties
            subPath: steampipe_db.properties
          - name: fq-trino-datasource-configs-volume
            mountPath: /etc/trino/catalog/nessie.properties
            subPath: nessie.properties
          #- name: trino-datasource-configmap-volume
          #  mountPath: etc/trino/catalog/trino.properties
          #  subPath: trino.properties
      volumes:
        - name: fq-trino-configs-volume
          configMap:
            name: fq-trino-configs
        - name: fq-trino-datasource-configs-volume
          configMap:
            name: fq-trino-datasource-configs
  volumeClaimTemplates:
    - metadata:
        name: fq-trino-tmp-data
      spec:
        storageClassName: manual
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 1Gi
```

### `kube/components/fq/trino/kustomization.yml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: fq

resources:
  - fq-trino-deployment.yml
  - fq-trino-egress-network-policy.yml
  - fq-trino-ingress-network-policy.yml
  - fq-trino-service.yml
  - fq-trino-statefulset.yml
configMapGenerator:
  - name: fq-trino-configs
    files:
      - configs/config.properties.coordinator
      - configs/config.properties.worker
      - configs/node.properties
      - configs/jvm.config
      - password.db
      - configs/password-authenticator.properties
      - configs/access-control.properties
      - configs/rules.json
  - name: fq-trino-datasource-configs
    files:
      - configs/gravitino.properties
      - configs/hms_db.properties
      - configs/iceberg.properties
      - configs/minio.properties
      - configs/steampipe_db.properties
      - configs/nessie.properties
```

---

## 4) Trino configuration that made dynamic catalog creation work

### `config.properties.coordinator`

```properties
coordinator=true
node-scheduler.include-coordinator=true
http-server.http.port=8080
query.max-memory=5GB
query.max-memory-per-node=1GB
discovery.uri=http://fq-trino:8080
http-server.authentication.type=PASSWORD
internal-communication.shared-secret=fq-trino-shared-secret-2026
# Dynamic catalog
catalog.management=dynamic
catalog.store=file
catalog.prune.update-interval=5s
```

### `config.properties.worker`

```properties
coordinator=false
http-server.http.port=8080
query.max-memory=5GB
query.max-memory-per-node=1GB
discovery.uri=http://fq-trino:8080
internal-communication.shared-secret=fq-trino-shared-secret-2026
```

### `node.properties`

```properties
node.environment=dev
node.id=ffffffff-ffff-ffff-ffff-ffffffffffff
node.data-dir=/data/trino
```

### `jvm.config`

```properties
-server
-agentpath:/usr/lib/trino/bin/libjvmkill.so
-XX:InitialRAMPercentage=80
-XX:MaxRAMPercentage=80
-XX:G1HeapRegionSize=32M
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:+ExitOnOutOfMemoryError
-XX:-OmitStackTraceInFastThrow
-XX:ReservedCodeCacheSize=256M
-XX:PerMethodRecompilationCutoff=10000
-XX:PerBytecodeRecompilationCutoff=10000
-Djdk.attach.allowAttachSelf=true
-Djdk.nio.maxCachedBufferSize=2000000
-Dfile.encoding=UTF-8
-XX:+EnableDynamicAgentLoading
-Djava.security.manager=allow
```

### `password-authenticator.properties`

```properties
password-authenticator.name=file
file.password-file=/etc/trino/password.db
```

### `access-control.properties`

```properties
access-control.name=opa
opa.policy.uri=http://opa.aix.svc.cluster.local:8181/v1/data/trino/allow
opa.log-requests=false
opa.log-responses=false
opa.allow-permission-management-operations=false
```

### `rules.json`

```json
{
  "catalogs": [
    {
      "catalog": ".*",
      "allow": "all"
    }
  ],
  "queries": [
    {
      "allow": ["execute", "view", "kill"]
    }
  ],
  "system_information": [
    {
      "user": ".*",
      "allow": ["read", "write"]
    }
  ],
  "catalog_session_properties": [
    {
      "catalog": ".*",
      "property": ".*",
      "allow": true
    }
  ],
  "system_session_properties": [
    {
      "property": ".*",
      "allow": true
    }
  ]
}
```

### `gravitino.properties`

```properties
connector.name=gravitino
gravitino.uri=http://gravitino:8090
gravitino.metalake=metalake
```

---

## 5) Deployment commands used

```bash
kubectl create namespace fq --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace=fq

kubectl apply -k kube/components/data-catalogs/gravitino
kubectl apply -k kube/components/fq/trino

kubectl get pods -n fq
```

---

## 6) Connectivity and SQL tests

### Create metalake first

If you hit this error:

`Create catalog failed. Metalake metalake not exists`

Create the metalake through Gravitino API:

```bash
kubectl port-forward -n fq svc/gravitino 30090:8090
```

```bash
curl -X POST http://127.0.0.1:30090/api/metalakes \
  -H "Content-Type: application/json" \
  -d '{"name":"metalake"}'
```

### Verify from Trino

```bash
kubectl port-forward -n fq svc/fq-trino 8080:8080
```

```sql
SHOW CATALOGS;
SHOW SCHEMAS FROM gravitino;
```

### Create a new catalog dynamically with SQL

```sql
CALL gravitino.system.create_catalog(
  'gt_hive_new',
  'hive',
  map(
    array['metastore.uris'],
    array['thrift://fq-hms:9083']
  )
);
```

Validate:

```sql
SELECT * FROM gravitino.system.catalog WHERE name = 'gt_hive_new';
```

---

## 7) What changed today (summary)

- Upgraded and pinned Gravitino to `1.2.0`.
- Integrated Trino connector bundle `469-472-1.2.0` into custom Trino image.
- Updated Trino and Gravitino deployment images.
- Enabled dynamic catalog management on Trino coordinator.
- Fixed runtime-critical config points (mount paths, node data dir, authenticator file path, shared secret, JVM flags).
- Verified end-to-end dynamic catalog creation through SQL.

This setup is now ready for adding more catalogs through SQL/API without rebuilding Trino images for every catalog change.
