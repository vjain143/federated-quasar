#!/bin/bash
echo "Building steam-pipe image"
docker build --tag fq-steampipe:0.22.0 --no-cache .
#docker build --debug --tag fq-steampipe:0.22.0 --no-cache .
echo "Image built successfully."


# Log in to Docker Hub
docker login
# Tag the image
docker tag fq-steampipe:0.22.0 vjain143/fq-steampipe:0.22.0
# Push the image to Docker Hub
docker push vjain143/fq-steampipe:0.22.0

