#!/bin/bash
echo "Building dbt image"
docker build --tag dbt:0.21.0 --no-cache .
echo "Image built successfully."

