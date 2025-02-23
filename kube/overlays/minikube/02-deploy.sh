#!/bin/bash

NAMESPACE="lab"

# Check if the namespace already exists
kubectl get namespace $NAMESPACE &> /dev/null
EXIT_STATUS=$?  # Store exit status immediately

echo "-----------------------------------------------------------------------------------------------------------------"

# Check if the namespace exists
if [ $EXIT_STATUS -ne 0 ]; then
  echo "Namespace '$NAMESPACE' does not exist. Creating..."
  kubectl create namespace $NAMESPACE
else
  echo "Namespace '$NAMESPACE' already exists. Skipping creation."
fi

echo "-----------------------------------------------------------------------------------------------------------------"

echo "Setting the default namespace to $NAMESPACE"
kubectl config set-context --current --namespace=$NAMESPACE
echo "Namespace $NAMESPACE set successfully."
echo "-----------------------------------------------------------------------------------------------------------------"
#echo "Setting the cluster-admin for namespace to $NAMESPACE"
#kubectl config set-context --current --user=docker-desktop
#echo "cluster-admin set successfully."
#echo "-----------------------------------------------------------------------------------------------------------------"
# kubectl delete job.batch/hive-metastore-init-schema
# echo "Cleaning namespace"
echo "-----------------------------------------------------------------------------------------------------------------"
kubectl apply -k .
echo "--"
echo "Component deployment completed"
echo "-----------------------------------------------------------------------------------------------------------------"
# kubectl apply -k ../../jobs
echo "Job deployment completed"
echo "-----------------------------------------------------------------------------------------------------------------"
kubectl get all -o wide

