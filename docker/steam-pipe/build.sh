#!/bin/bash
echo "Building steam-pipe image"
docker build --tag steam-pipe:1.0.0 --no-cache .
echo "Image built successfully."


# Log in to Docker Hub
docker login
# Tag the image
docker tag steam-pipe:1.0.0 vjain143/steam-pipe:1.0.0
# Push the image to Docker Hub
docker push vjain143/steam-pipe:1.0.0

