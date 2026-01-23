# OpenMetadata Kubernetes Deployment Configuration

This directory contains the Kubernetes deployment files and configuration for OpenMetadata.

## Files

- **om-server-deployment.yaml** - Kubernetes Deployment manifest for OpenMetadata server
  - Uses minimal environment variables (only critical overridable values)
  - Mounts configuration from ConfigMap at `/opt/openmetadata/conf`
  - Mounts logs volume at `/opt/openmetadata/logs`

- **openmetadata.yml** - OpenMetadata server configuration file
  - Complete server configuration with environment variable substitution
  - All settings support override via environment variables using `${VAR_NAME:-default_value}` syntax
  - Should be converted to ConfigMap before deployment

- **create-configmap.sh** - Helper script to create ConfigMap from configuration
  - Creates Kubernetes ConfigMap from `openmetadata.yml`
  - ConfigMap named `om-server-config` will be used by deployment

## Quick Start

### 1. Create ConfigMap from configuration file
```bash
cd /path/to/this/directory

# Using the script
./create-configmap.sh

# Or manually with kubectl
kubectl create configmap om-server-config \
  --from-file=openmetadata.yml \
  --namespace=default
```

### 2. Deploy OpenMetadata
```bash
kubectl apply -f om-server-deployment.yaml
```

## Configuration Overrides

You can override configuration values via environment variables in the deployment:

```yaml
env:
  - name: DB_HOST
    value: "om-mysql"
  - name: LOG_LEVEL
    value: "DEBUG"
  # Add more overrides as needed
```

All values in `openmetadata.yml` that use `${VAR_NAME:-default}` syntax can be overridden.

## Environment Variables

### Critical Variables (overridable in deployment)
- `DB_HOST` - Database hostname
- `DB_PORT` - Database port
- `DB_USER` - Database user
- `DB_USER_PASSWORD` - Database password
- `ELASTICSEARCH_HOST` - Elasticsearch hostname
- `ELASTICSEARCH_PORT` - Elasticsearch port
- `PIPELINE_SERVICE_CLIENT_ENDPOINT` - Airflow/Pipeline service endpoint
- `SERVER_HOST_API_URL` - OpenMetadata API URL
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc)
- `OPENMETADATA_CLUSTER_NAME` - Cluster identifier

### All Other Variables
Defined in `openmetadata.yml` and can be overridden via environment variables using the pattern `${VAR_NAME:-default_value}`.

## ConfigMap Details

The ConfigMap will contain the `openmetadata.yml` file which is mounted as:
- **Mount Path**: `/opt/openmetadata/conf`
- **Config File**: `/opt/openmetadata/conf/openmetadata.yml`

The OpenMetadata container expects the configuration at this location and will automatically parse environment variables at startup.

## Logs Volume

Logs are stored in a PersistentVolume mounted at `/opt/openmetadata/logs`:
- Operation logs: `openmetadata-operations.log`
- Main logs: `openmetadata.log`
- Audit logs: `audit.log`

Ensure the PVC `om-server-logs-pvc` exists before deploying.
