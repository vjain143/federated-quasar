# Trino Image with Gravitino Connector

This image installs the Gravitino Trino connector from:

`https://github.com/apache/gravitino/releases/download/v1.2.0/gravitino-trino-connector-469-472-1.2.0.tar.gz`

## Build

```bash
cd docker/trino
chmod +x build.sh
./build.sh
```

## Run

```bash
docker run -d --name fq-trino \
  -p 8080:8080 \
  fq-trino:472.1.2
```

## Optional: Override connector URL at build time

```bash
cd docker/trino
CONNECTOR_URL="https://github.com/apache/gravitino/releases/download/v1.2.0/gravitino-trino-connector-469-472-1.2.0.tar.gz" ./build.sh
```
