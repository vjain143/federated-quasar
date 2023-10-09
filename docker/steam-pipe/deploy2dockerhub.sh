#!/bin/bash
echo "Log in to Docker Hub"
docker login
echo "Tag the image"
docker tag steam-pipe:1.0.0 vjain143/steam-pipe:1.0.0
echo "Push the image to Docker Hub"
docker push vjain143/steam-pipe:1.0.0

