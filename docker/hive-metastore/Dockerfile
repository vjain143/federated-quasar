FROM maven:3.9.9-eclipse-temurin-21 AS deps
WORKDIR /build
COPY pom.xml /build/pom.xml
# Resolve runtime jars once in a throwaway stage; only jars are copied to final image.
RUN mvn -B -q -DskipTests dependency:copy-dependencies -DincludeScope=runtime -DoutputDirectory=/build/deps

FROM eclipse-temurin:21-jre-jammy
LABEL maintainer="Vivek Jain"
LABEL hive-metastore-version="4.2.0"
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# Hive 4.2.0 aligns with Hadoop 3.4.x and Java 21.
ARG HADOOP_VERSION=3.4.1
ARG HIVE_METASTORE_VERSION=4.2.0
ARG HIVE_METASTORE_URL=http://apache.uvigo.es/hive/hive-standalone-metastore-4.2.0/hive-standalone-metastore-4.2.0-bin.tar.gz
ARG JMX_EXPORTER_VERSION=1.0.1

RUN apt-get update && \
    apt-get install -y curl --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Bundle the Prometheus JMX exporter jar so metrics can be enabled at runtime.
RUN mkdir -p /opt/monitoring/jmx && \
    curl -sfSL https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/${JMX_EXPORTER_VERSION}/jmx_prometheus_javaagent-${JMX_EXPORTER_VERSION}.jar \
      -o /opt/monitoring/jmx/jmx_prometheus_javaagent-${JMX_EXPORTER_VERSION}.jar && \
    ln -sf /opt/monitoring/jmx/jmx_prometheus_javaagent-${JMX_EXPORTER_VERSION}.jar /opt/monitoring/jmx/jmx_prometheus_javaagent.jar

# Set Hadoop/HiveMetastore variables and Classpath
ENV HADOOP_HOME="/opt/hadoop"
ENV METASTORE_HOME="/opt/hive-metastore"
# Keep Hadoop tool jars + metastore libs on classpath.
# S3 support comes from Hadoop's bundled tools jars; only JDBC jars are injected below.
ENV HADOOP_CLASSPATH="${HADOOP_HOME}/share/hadoop/tools/lib/*:${METASTORE_HOME}/lib"
ENV PATH="${HADOOP_HOME}/bin:${METASTORE_HOME}/lib/:${HADOOP_HOME}/share/hadoop/tools/lib/:${PATH}"

# Download and extract the Hadoop binary package.
# Remove non-runtime Hadoop artifacts such as source/test jars, jdiff files,
# native examples, and static archives to keep the image smaller.
RUN curl -s https://archive.apache.org/dist/hadoop/core/hadoop-$HADOOP_VERSION/hadoop-$HADOOP_VERSION.tar.gz \
        | tar xz -C /opt/  \
        && ln -s ${HADOOP_HOME}-$HADOOP_VERSION ${HADOOP_HOME} \
        && rm -r ${HADOOP_HOME}/share/doc \
        && find ${HADOOP_HOME} \( \
          -path '*/jdiff/*' -o \
          -path '*/sources/*' -o \
          -name '*-tests.jar' -o \
          -name '*-test-sources.jar' -o \
          -path "${HADOOP_HOME}/lib/native/examples/*" -o \
          -name '*.a' \
        \) -delete

# Download and install the standalone metastore binary
# (Standalone Metastore is available after 3.0.0 version)
RUN curl -s ${HIVE_METASTORE_URL} \
        | tar xz -C /opt/ \
        && ln -s /opt/apache-hive-metastore-${HIVE_METASTORE_VERSION}-bin ${METASTORE_HOME}

# Copy resolved runtime jars straight into the final lib directory.
# Avoid staging them in a temp directory first, which creates an extra large layer.
COPY --from=deps --chmod=0644 /build/deps/ /opt/hive-metastore/lib/

COPY entrypoint.sh ${METASTORE_HOME}/bin/
RUN chmod 775 ${METASTORE_HOME}/bin/entrypoint.sh

# Metastore URI Port
EXPOSE 9083

WORKDIR ${METASTORE_HOME}

CMD ["bin/entrypoint.sh"]
