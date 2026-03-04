# AIX MySQL

Namespace context:

```bash
kubectl config set-context --current --namespace=aix
```

Folder: `kube/components/aix/kubernetes/mysql`

Purpose:

- Runs the MySQL database used by Moat.

Resources in this folder:

- `aix-mysql-deployment.yaml`: Deploys the MySQL instance.
- `aix-mysql-service.yaml`: Exposes MySQL on port `3306` as a `NodePort`.
- `aix-mysql-secret.yaml`: Stores database credentials and bootstrap values.
- `aix-mysql-ingress-network-policy.yaml`: Allows only Moat to connect to MySQL.
- `aix-mysql-egress-network-policy.yaml`: Denies outbound traffic from MySQL.
- `kustomization.yaml`: Builds the component.
