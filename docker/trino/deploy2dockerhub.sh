#!/bin/bash
echo "Log in to Docker Hub"
docker login
echo "Tag the image"
docker tag fq-trino:471.0.1 vjain143/fq-trino:471.0.1
echo "Push the image to Docker Hub"
docker push vjain143/fq-trino:471.0.1

