#!/bin/bash

NAMESPACE="lab"

echo "Setting the default namespace to $NAMESPACE"
kubectl config set-context --current --namespace=$NAMESPACE
echo "Namespace set successfully."
kubectl apply -k .
kubectl get all -o wide

