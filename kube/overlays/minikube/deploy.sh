#!/bin/bash

NAMESPACE="lab"

# Check if the namespace already exists
kubectl get namespace $NAMESPACE &> /dev/null
echo "-----------------------------------------------------------------------------------------------------------------"
# $? will be 0 if the namespace exists, 1 otherwise
if [ $? -eq 1 ]; then
  echo "Namespace '$NAMESPACE' does not exist. Creating..."
  kubectl create namespace $NAMESPACE
else
  echo "Namespace '$NAMESPACE' already exists. Skipping creation."
fi

echo "-----------------------------------------------------------------------------------------------------------------"

echo "Setting the default namespace to $NAMESPACE"
kubectl config set-context --current --namespace=$NAMESPACE
echo "Namespace set successfully."
echo "-----------------------------------------------------------------------------------------------------------------"
kubectl delete job.batch/hive-metastore-init-schema
echo "Cleaning namespace"
echo "-----------------------------------------------------------------------------------------------------------------"
kubectl apply -k .
echo "Component deployment completed"
echo "-----------------------------------------------------------------------------------------------------------------"
kubectl apply -k ../../jobs
echo "Job deployment completed"
echo "-----------------------------------------------------------------------------------------------------------------"
kubectl get all -o wide

