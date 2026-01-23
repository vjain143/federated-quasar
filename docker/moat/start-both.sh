#!/bin/bash
set -e

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $OPA_PID $MOAT_PID 2>/dev/null || true
    wait
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start OPA server in the background
echo "Starting OPA server on port 8181..."
opa run \
    --server \
    --watch \
    --format=pretty \
    --log-level=debug \
    --log-format=json-pretty \
    --addr=0.0.0.0:8181 \
    --set=decision_logs.console=true \
    --config-file /config/policy/config.yaml \
    /config/policy/ &
OPA_PID=$!

# Wait a moment for OPA to start
sleep 2

# Start moat server in the background
echo "Starting moat server on port 8000..."
cd /app
/app/entrypoint.sh start-server &
MOAT_PID=$!

# Wait for both processes
wait $OPA_PID $MOAT_PID
