#!/bin/bash
echo "Building hive-metastore image"
docker build --tag hive-metastore:4.2.0 --no-cache .
echo "Image built successfully."


# Log in to Docker Hub
docker login
# Tag the image
docker tag hive-metastore:4.2.0 vjain143/hive-metastore:4.2.0
# Push the image to Docker Hub
docker push vjain143/hive-metastore:4.2.0
