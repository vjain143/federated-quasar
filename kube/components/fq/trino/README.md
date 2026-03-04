# FQ Trino

Namespace context:

```bash
kubectl config set-context --current --namespace=fq
```

Folder: `kube/components/fq/trino`

Purpose:

- Runs the `fq` Trino coordinator and worker.
- Uses OPA from the `aix` namespace for authorization.
- Connects to `fq-hms`, `fq-minio`, and `fq-mysql`.

Resources in this folder:

- `fq-trino-deployment.yml`: Deploys the Trino coordinator.
- `fq-trino-statefulset.yml`: Deploys the Trino worker.
- `fq-trino-service.yml`: Exposes the Trino coordinator on port `8080`.
- `fq-trino-egress-network-policy.yml`: Controls outbound traffic from Trino-related pods.
- `fq-trino-ingress-network-policy.yml`: Controls inbound traffic to Trino-related pods.
- `fq-git-sync-policy-updater-deployment.yml`: Optional sidecar deployment for applying policy manifests from git.
- `fq-git-sync-policy-updater-service-account.yaml`: Service account and RBAC for the optional policy updater.
- `configs/`: Trino server, access-control, and catalog configuration files.
- `password.db`: Password authenticator backing file.
- `kustomization.yml`: Builds the component and generates Trino configmaps.
