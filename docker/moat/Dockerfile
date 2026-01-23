# Set OPA version (can be overridden at build time)
ARG OPA_VERSION=1.12.2

# Use Python base image to support both OPA and moat
FROM python:3.12-slim-bookworm

# Set moat environment variables
ENV CONFIG_FILE_PATH=/app/moat/config/config.yaml
ENV PYTHONPATH=/app/moat/src
ENV FLASK_APP=moat.src.app

# Set working directory for OPA build
WORKDIR /tmp

# Install system dependencies and build tools for OPA
RUN apt-get update && apt-get install -y \
    libexpat1 \
    curl \
    tar \
    gzip \
    git \
    golang-go \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download and build OPA from source
RUN curl -L -o opa-source.tar.gz https://github.com/open-policy-agent/opa/archive/refs/tags/v${OPA_VERSION}.tar.gz \
    && tar -xzf opa-source.tar.gz \
    && cd opa-${OPA_VERSION} \
    && CGO_ENABLED=0 go build -o /usr/local/bin/opa -ldflags="-w -s" -tags netgo ./cmd/opa \
    && chmod 755 /usr/local/bin/opa \
    && cd / \
    && rm -rf /tmp/opa-${OPA_VERSION} /tmp/opa-source.tar.gz

# Remove build dependencies to reduce image size
RUN apt-get update && apt-get remove -y \
    git \
    golang-go \
    build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for OPA config
WORKDIR /config

# Copy OPA configuration files
COPY docker/opa/policy/config.yaml /config/policy/config.yaml
COPY docker/opa/token.txt /config/token.txt

# Copy moat policy files from opa/trino directory
COPY opa/trino/ /config/policy/trino/

# Create persistence directory
RUN mkdir -p /policy/persistence

# Install moat application
# Set working directory for moat
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy moat application code
COPY moat/ /app/moat/

# Copy moat entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Copy moat OPA policies (for moat's own use)
COPY opa/ /app/opa/

# Expose ports: 8181 for OPA, 8000 for moat
EXPOSE 8181 8000

# Default command: start OPA server
# Use a startup script to run both services if needed
# For now, default to OPA (can be overridden in docker-compose)
CMD ["opa", "run", "--server", "--watch", "--format=pretty", "--log-level=debug", "--log-format=json-pretty", "--addr=0.0.0.0:8181", "--set=decision_logs.console=true", "--config-file", "/config/policy/config.yaml", "/config/policy/"]
