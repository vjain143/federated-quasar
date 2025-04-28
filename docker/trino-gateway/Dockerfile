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

RUN curl -L -o /opt/trino-gateway/h2.jar https://repo1.maven.org/maven2/com/h2database/h2/2.1.214/h2-2.1.214.jar

# Set entry point for the application
#ENTRYPOINT ["java", "-XX:MinRAMPercentage=50", "-XX:MaxRAMPercentage=80", "-jar", "gateway-ha.jar", "config.yaml"]

ENTRYPOINT ["java", "-cp", "/opt/jars/*:trino-gateway.jar", "-jar", "gateway-ha.jar", "/etc/trino-gateway/config.yaml"]