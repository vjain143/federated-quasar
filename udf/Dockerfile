FROM trinodb/trino:472

# Create plugin directory
RUN mkdir -p /usr/lib/trino/plugin/redact-udf

# Copy the UDF jar into the plugin directory
COPY trino-redact-udf/target/trino-redact-udf-1.0.0-SNAPSHOT.jar /usr/lib/trino/plugin/redact-udf/