# FQ MinIO

Namespace context:

```bash
kubectl config set-context --current --namespace=fq
```

Folder: `kube/components/fq/minio`

Purpose:

- Runs the object store used by the `fq` stack.
- Serves both the S3-compatible API and the admin console.

Resources in this folder:

- `fq-minio-deployment.yml`: Deploys the MinIO server.
- `fq-minio-service.yml`: Exposes the MinIO API on port `9000`.
- `fq-minio-console-service.yml`: Exposes the MinIO console on port `9001`.
- `fq-minio-pv.yml`: Defines the persistent volume for MinIO data.
- `fq-minio-pvc.yml`: Claims the MinIO storage volume.
- `fq-minio-egress-network-policy.yml`: Controls outbound traffic for MinIO-related pods.
- `fq-minio-ingress-network-policy.yml`: Controls inbound traffic for MinIO-related pods.
- `kustomization.yml`: Builds the component.
