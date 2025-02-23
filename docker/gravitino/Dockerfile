# Use a lightweight Java 11 runtime
FROM openjdk:17-jdk-slim

RUN apt-get update && apt-get install -y wget tar procps bash && rm -rf /var/lib/apt/lists/*

# Set environment variables (Change as needed)
ENV GRAVITINO_VERSION=0.8.0
ENV GRAVITINO_HOME=/opt/gravitino
ENV GRAVITINO_BINARY_URL="https://dlcdn.apache.org/incubator/gravitino/0.8.0-incubating/gravitino-${GRAVITINO_VERSION}-incubating-bin.tar.gz"
ENV GRAVITINO_ICEBERG_URL="https://dlcdn.apache.org/incubator/gravitino/0.8.0-incubating/gravitino-iceberg-rest-server-${GRAVITINO_VERSION}-incubating-bin.tar.gz"



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