#!/bin/bash
echo "Building trino image"
docker build --tag fq-trino:472.0.2 --no-cache .
echo "Image built successfully."

