#!/bin/bash
echo "Building superset image"
docker build --tag superset:0.0.1 --no-cache .
echo "Image built successfully."


# Log in to Docker Hub
docker login
# Tag the image
docker tag superset:0.0.1 vjain143/superset:0.0.1
# Push the image to Docker Hub
docker push vjain143/superset:0.0.1

