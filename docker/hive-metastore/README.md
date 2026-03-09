# Hive Metastore Image

This directory builds the `hive-metastore` Docker image used by Federated Quasar.

In this repository, HMS configuration files are mounted directly as concrete files.
The image does not include `gomplate` or startup template rendering.

## Version Matrix

Current baseline:

- Hive Standalone Metastore: `4.2.0`
- Hadoop: `3.4.1`
- Java runtime/build: `21` (Temurin)

These versions are intentionally aligned:

- Hive `4.2.0` is built with Java 21.
- Hive `4.2.0` depends on the Hadoop `3.4.x` line.

## Dependency Model

Runtime dependencies are resolved in a builder stage from [`pom.xml`](./pom.xml) and copied into:

- `${METASTORE_HOME}/lib`

### Why only one location?

To keep image size down and avoid classpath ambiguity, we do **not** copy the same jars into both:

- `${HADOOP_HOME}/share/hadoop/common/lib`
- `${METASTORE_HOME}/lib`

Only `${METASTORE_HOME}/lib` is used for injected runtime jars that are not already present in the base distributions.

Current rule:

- S3/Hadoop AWS jars come from `${HADOOP_HOME}/share/hadoop/tools/lib`
- JDBC jars come from Maven and are copied into `${METASTORE_HOME}/lib`

The Dockerfile copies those jars directly from the builder stage into `${METASTORE_HOME}/lib`.
Do not stage them in a temporary directory in the final image and then copy them again, because that creates another large image layer.

## Classpath Behavior

`HADOOP_CLASSPATH` is set to:

`${HADOOP_HOME}/share/hadoop/tools/lib/*:${METASTORE_HOME}/lib`

This keeps Hadoop tool jars available while ensuring custom/runtime dependencies are loaded from a single place.

## AWS / S3 Notes

- Hadoop `3.4.1` already ships `hadoop-aws` and the AWS SDK bundle under `${HADOOP_HOME}/share/hadoop/tools/lib`.
- Those jars are exposed through `HADOOP_CLASSPATH`.
- Do not add the same S3 jars again through Maven unless you intentionally need a different version and have verified compatibility.

## Monitoring

The image bundles the Prometheus JMX exporter jar at:

- `/opt/monitoring/jmx/jmx_prometheus_javaagent.jar`

Runtime support is controlled through environment variables:

- `JMX_EXPORTER_ENABLE=true`: enable the Prometheus JMX exporter javaagent
- `JMX_EXPORTER_PORT=9404`: Prometheus scrape port
- `JMX_EXPORTER_CONFIG=/opt/hive-metastore/conf/jmx-exporter.yaml`: exporter config file
- `ENABLE_JMX_REMOTE=true`: enable standard remote JMX
- `JMX_PORT=9010`: JMX port
- `JMX_RMI_PORT=9010`: JMX RMI port
- `JMX_HOSTNAME=<hostname>`: optional RMI hostname
- `DT_ONEAGENT_ENABLE=true`: enable Dynatrace OneAgent if the agent library is mounted
- `DT_ONEAGENT_PATH=/opt/dynatrace/oneagent/agent/lib64/liboneagentproc.so`: default OneAgent library path
- `DT_ONEAGENT_OPTIONS=...`: optional OneAgent agentpath arguments

Dynatrace OneAgent is not baked into the image. The image only supports attaching it when the agent library is mounted into the container.

These monitoring agents are not added to [`pom.xml`](./pom.xml):

- JDBC drivers belong in `pom.xml` because they are application runtime jars.
- The Prometheus exporter is a Java agent binary, so it is bundled separately in the image.
- Dynatrace OneAgent is proprietary and environment-specific, so the image only supports attaching a mounted agent library at runtime.

## Size Notes

- The biggest layers are Hadoop itself, the upstream Hive metastore tarball, and injected runtime jars.
- Links do not reduce image size if the same file contents are introduced in separate Docker layers.
- The right optimization is to avoid copying the same jar payload twice in the final stage.
- The Dockerfile also removes non-runtime Hadoop artifacts after extraction:
  `jdiff/`, `sources/`, `*-tests.jar`, `*-test-sources.jar`, native examples, and static `.a` archives.

## Upgrade Checklist

When changing Hive Metastore version:

1. Update `HIVE_METASTORE_VERSION` and `HIVE_METASTORE_URL` in [`Dockerfile`](./Dockerfile).
2. Confirm Java major version compatibility (Hive 4.2.0 -> Java 21).
3. Align Hadoop version (`ARG HADOOP_VERSION` in Dockerfile and `<hadoop.version>` in pom.xml).
4. Build and run smoke checks:
   - Image build succeeds.
   - Metastore starts.
   - MySQL/PostgreSQL connectivity works.
   - S3/MinIO access works (if enabled in your deployment).

## Build

From this directory:

```bash
docker build -t hive-metastore:4.2.0 .
```
