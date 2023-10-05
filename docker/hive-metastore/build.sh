#!/bin/bash
echo "Building hive-metastore image"
docker build --tag hive-metastore:3.0.0 --no-cache .
echo "Image built successfully."

