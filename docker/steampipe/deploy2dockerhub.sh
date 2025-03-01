#!/bin/bash
echo "Log in to Docker Hub"
docker login
echo "Tag the image"
docker tag steampipe:1.0.0 vjain143/steampipe:1.0.0
echo "Push the image to Docker Hub"
docker push vjain143/steampipe:1.0.0

