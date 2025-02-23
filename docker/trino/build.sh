#!/bin/bash
echo "Building trino image"
docker build --tag fq-trino:471.0.1 --no-cache .
echo "Image built successfully."

