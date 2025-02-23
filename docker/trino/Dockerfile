# Use the official Trino image as the base
FROM trinodb/trino:471

# Set environment variables
ENV GRAVITINO_VERSION=0.8.0-incubating
ENV GRAVITINO_CONNECTOR_URL="https://dlcdn.apache.org/incubator/gravitino/${GRAVITINO_VERSION}/gravitino-trino-connector-${GRAVITINO_VERSION}.tar.gz"
#https://dlcdn.apache.org/incubator/gravitino/0.8.0-incubating/gravitino-trino-connector-0.8.0-incubating.tar.gz
ENV TRINO_PLUGIN_DIR=/usr/lib/trino/plugin

# Install wget and extract the Gravitino connector
USER root

# Create Gravitino plugin directory
RUN mkdir -p ${TRINO_PLUGIN_DIR}/gravitino

# Copy the Gravitino-Trino connector from the local machine into the Trino image
COPY gravitino-trino-connector-0.8.0-incubating/ ${TRINO_PLUGIN_DIR}/gravitino

# Copy the Gravitino catalog configuration
#COPY gravitino.properties /etc/trino/catalog/

# Set Trino user back for security
USER trino