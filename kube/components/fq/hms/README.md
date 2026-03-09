# FQ HMS

Namespace context:

```bash
kubectl config set-context --current --namespace=fq
```

Folder: `kube/components/fq/hms`

Purpose:

- Runs the Hive Metastore service for the `fq` data stack.
- Uses `fq-mysql` for metadata storage.
- Uses `fq-minio` as the S3-compatible object store backend.

Resources in this folder:

- `fq-hms-deployment.yml`: Deploys the Hive Metastore pod.
- `fq-hms-service.yml`: Exposes HMS on port `9083` as a `NodePort`.
- `fq-hms-egress-network-policy.yml`: Controls outbound traffic for HMS-related pods.
- `fq-hms-ingress-network-policy.yml`: Controls inbound traffic for HMS-related pods.
- `configs/core-site.xml`: Hadoop S3/MinIO configuration.
- `configs/metastore-site.xml`: Hive Metastore JDBC and service configuration.
- `configs/metastore-log4j2.properties`: Hive Metastore logging configuration.
- `configs/jmx-exporter.yaml`: Prometheus JMX exporter configuration.
- `kustomization.yml`: Builds the component and generates the HMS configmap.

Operational notes:

- The deployment uses `/opt/hive-metastore/bin/entrypoint.sh` so monitoring hooks from the image are applied.
- `startupProbe`, `readinessProbe`, and `livenessProbe` use TCP checks on the HMS Thrift port `9083`.
- Prometheus JMX exporter and remote JMX are disabled by default and can be enabled through env vars in the deployment.
- Dynatrace OneAgent is only attached if its shared library is mounted into the container and `DT_ONEAGENT_ENABLE=true`.
