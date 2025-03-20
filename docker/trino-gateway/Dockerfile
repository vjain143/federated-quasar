FROM openjdk:23-ea-18-jdk-oraclelinux8

# Install curl using microdnf and create necessary directories
RUN \
microdnf install -y curl && \
mkdir -p /opt/trino-gateway && \
curl -L -o /opt/trino-gateway/gateway-ha.jar \
https://repo1.maven.org/maven2/io/trino/gateway/gateway-ha/15/gateway-ha-15-jar-with-dependencies.jar && \
microdnf clean all

# Copy configuration file
#COPY config.yaml /opt/trino-gateway/config.yaml

# Set working directory
WORKDIR /opt/trino-gateway

# Set entry point for the application
ENTRYPOINT ["java", "-XX:MinRAMPercentage=50", "-XX:MaxRAMPercentage=80", "-jar", "gateway-ha.jar", "config.yaml"]