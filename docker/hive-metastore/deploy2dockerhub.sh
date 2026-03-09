#!/bin/bash
echo "Log in to Docker Hub"
docker login
echo "Tag the image"
docker tag hive-metastore:4.2.0 vjain143/hive-metastore:4.2.0
echo "Push the image to Docker Hub"
docker push vjain143/hive-metastore:4.2.0
