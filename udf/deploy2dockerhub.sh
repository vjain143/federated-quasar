#!/bin/bash
echo "Log in to Docker Hub"
docker login
echo "Tag the image"
docker tag fq-trino:472.0.2 vjain143/fq-trino:472.0.2
echo "Push the image to Docker Hub"
docker push vjain143/fq-trino:472.0.2

