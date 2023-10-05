#!/bin/bash

# Start Minikube
#minikube start

# Access Minikube VM and create the directory
minikube ssh <<EOF
sudo mkdir -p /data/minio-pv
exit
EOF

# Output success message
echo "The directory /data/minio-pv has been created."

minikube ssh <<EOF
sudo mkdir -p /data/mysql-pv
exit
EOF

# Output success message
echo "The directory /data/mysql-pv has been created."

echo "Minikube setup completed."
