#!/bin/bash
echo "Building hive-metastore image"
docker build --tag kestra:0.13.1 --no-cache .
echo "Image built successfully."


# Log in to Docker Hub
#docker login
# Tag the image
#docker tag kestra:0.13.1 vjain143/kestra:0.13.1
# Push the image to Docker Hub
#docker push vjain143/kestra:0.13.1

