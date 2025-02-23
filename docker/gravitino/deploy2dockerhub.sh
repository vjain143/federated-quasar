#!/bin/bash
echo "Log in to Docker Hub"
docker login
echo "Tag the image"
docker tag fq-gravitino:0.8.0 vjain143/fq-gravitino:0.8.0
echo "Push the image to Docker Hub"
docker push vjain143/fq-gravitino:0.8.0

