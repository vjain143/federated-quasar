# FQ MySQL

Namespace context:

```bash
kubectl config set-context --current --namespace=fq
```

Folder: `kube/components/fq/mysql`

Purpose:

- Runs the MySQL instance used by the `fq` stack.

Resources in this folder:

- `fq-mysql-deployment.yml`: Deploys the MySQL server.
- `fq-mysql-service.yml`: Exposes MySQL on port `3306`.
- `fq-mysql-pv.yml`: Defines the persistent volume for MySQL data.
- `fq-mysql-pvc.yml`: Claims the MySQL storage volume.
- `fq-mysql-egress-network-policy.yml`: Controls outbound traffic for MySQL-related pods.
- `fq-mysql-ingress-network-policy.yml`: Controls inbound traffic for MySQL-related pods.
- `kustomization.yml`: Builds the component.
