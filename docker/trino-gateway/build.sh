#!/bin/bash
echo "Building trino image"
docker build --tag fq-trino-gateway:0.8.0 --no-cache .
echo "Image built successfully."

