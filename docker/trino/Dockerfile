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
