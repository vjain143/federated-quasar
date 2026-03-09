#!/bin/bash

function log () {
    level=$1
    message=$2
    echo $(date  '+%d-%m-%Y %H:%M:%S') [${level}]  ${message}
}

HIVE_CONF_DIR="${METASTORE_HOME}/conf"
HIVE_START_CMD="${HIVE_START_CMD:-/opt/hive-metastore/bin/start-metastore}"

JAVA_AGENT_OPTS=""

if [ "${JMX_EXPORTER_ENABLE:-false}" = "true" ]; then
  JMX_EXPORTER_JAR="${JMX_EXPORTER_JAR:-/opt/monitoring/jmx/jmx_prometheus_javaagent.jar}"
  JMX_EXPORTER_PORT="${JMX_EXPORTER_PORT:-9404}"
  JMX_EXPORTER_CONFIG="${JMX_EXPORTER_CONFIG:-${HIVE_CONF_DIR}/jmx-exporter.yaml}"

  if [ -f "${JMX_EXPORTER_JAR}" ] && [ -f "${JMX_EXPORTER_CONFIG}" ]; then
    JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -javaagent:${JMX_EXPORTER_JAR}=${JMX_EXPORTER_PORT}:${JMX_EXPORTER_CONFIG}"
    log "INFO" "Enabled Prometheus JMX exporter on port ${JMX_EXPORTER_PORT}"
  else
    log "WARN" "Skipping Prometheus JMX exporter. Missing jar or config file."
  fi
fi

if [ "${ENABLE_JMX_REMOTE:-false}" = "true" ]; then
  JMX_PORT="${JMX_PORT:-9010}"
  JMX_RMI_PORT="${JMX_RMI_PORT:-${JMX_PORT}}"
  JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -Dcom.sun.management.jmxremote=true"
  JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -Dcom.sun.management.jmxremote.port=${JMX_PORT}"
  JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -Dcom.sun.management.jmxremote.rmi.port=${JMX_RMI_PORT}"
  JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -Dcom.sun.management.jmxremote.local.only=false"
  JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -Dcom.sun.management.jmxremote.authenticate=false"
  JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -Dcom.sun.management.jmxremote.ssl=false"

  if [ -n "${JMX_HOSTNAME:-}" ]; then
    JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -Djava.rmi.server.hostname=${JMX_HOSTNAME}"
  fi

  log "INFO" "Enabled remote JMX on port ${JMX_PORT}"
fi

if [ "${DT_ONEAGENT_ENABLE:-false}" = "true" ]; then
  DT_ONEAGENT_PATH="${DT_ONEAGENT_PATH:-/opt/dynatrace/oneagent/agent/lib64/liboneagentproc.so}"

  if [ -f "${DT_ONEAGENT_PATH}" ]; then
    if [ -n "${DT_ONEAGENT_OPTIONS:-}" ]; then
      JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -agentpath:${DT_ONEAGENT_PATH}=${DT_ONEAGENT_OPTIONS}"
    else
      JAVA_AGENT_OPTS="${JAVA_AGENT_OPTS} -agentpath:${DT_ONEAGENT_PATH}"
    fi
    log "INFO" "Enabled Dynatrace OneAgent from ${DT_ONEAGENT_PATH}"
  else
    log "WARN" "Skipping Dynatrace OneAgent. Agent library not found at ${DT_ONEAGENT_PATH}"
  fi
fi

export HADOOP_CLIENT_OPTS="${JAVA_AGENT_OPTS} ${HADOOP_CLIENT_OPTS}"

log "INFO" "Starting Hive Metastore service. Command: ${HIVE_START_CMD}"

exec "$HIVE_START_CMD" "$@"
