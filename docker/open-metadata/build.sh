#!/bin/bash
echo "Building hive-metastore image"
docker build --tag open-metadata:1.0.1 --no-cache .
echo "Image built successfully."


# Log in to Docker Hub
docker login
# Tag the image
docker tag open-metadata:1.0.1 vjain143/open-metadata:1.0.1
# Push the image to Docker Hub
docker push vjain143/open-metadata:1.0.1

