#!/bin/bash
echo "Building trino image"
docker build --tag fq-gravitino:0.8.0 --no-cache .
echo "Image built successfully."

