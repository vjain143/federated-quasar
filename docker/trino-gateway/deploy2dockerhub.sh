#!/bin/bash
echo "Log in to Docker Hub"
docker login
echo "Tag the image"
docker tag fq-trino-gateway:1.15.0 vjain143/fq-trino-gateway:1.15.0
echo "Push the image to Docker Hub"
docker push vjain143/fq-trino-gateway:1.15.0

