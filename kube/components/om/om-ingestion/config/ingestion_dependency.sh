#!/bin/bash
set -e

echo "Starting Airflow with OpenMetadata ingestion dependencies..."

# Migrate database schema (required for Airflow 3.x)
airflow db migrate || true

# Create admin user if it doesn't exist
airflow users create \
    --username "${AIRFLOW_ADMIN_USER:-admin}" \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password "${AIRFLOW_ADMIN_PASSWORD:-admin}" || true

# Function to handle shutdown
cleanup() {
    echo "Shutting down Airflow..."
    kill $SCHEDULER_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start Airflow scheduler in background
echo "Starting Airflow scheduler..."
airflow scheduler &
SCHEDULER_PID=$!

# Wait a moment for scheduler to start
sleep 5

# Start Airflow API server (replaces webserver in Airflow 3.x)
echo "Starting Airflow API server on port 8080..."
exec airflow api-server --port 8080
