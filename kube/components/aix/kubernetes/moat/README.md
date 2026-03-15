# AIX Moat

Namespace context:

```bash
kubectl config set-context --current --namespace=aix
```

Folder: `kube/components/aix/kubernetes/moat`

Purpose:

- Runs the Moat API and worker for policy management.
- Publishes policy bundles for OPA.
- Uses MySQL in the same namespace for storage.

Resources in this folder:

- `aix-moat-deployment.yaml`: Deploys the Moat pod with `init-db`, `api`, and `worker` containers.
- `aix-moat-service.yaml`: Exposes the Moat API on port `8000` as a `NodePort`.
- `aix-moat-secret.yaml`: Provides runtime secrets for the Moat app.
- `aix-moat-ingress-network-policy.yaml`: Allows OPA to reach the Moat API.
- `aix-moat-egress-network-policy.yaml`: Allows Moat to reach DNS and MySQL.
- `configs/config.yaml`: Application config mounted into the pod.
- `configs/policy.rego`: Static policy content mounted for bundle generation.
- `kustomization.yaml`: Builds the component and generates configmaps.

Connector UI:

- UI route: `/connectors`
- API prefix: `/api/v1/connectors`
- Runtime connector YAML location (in pod): `/opt/moat/runtime/connectors`
- OpenMetadata actions provided:
  - connection/auth test
  - metadata preview and mapping to Moat resources
  - metadata sync into `resources` + `resource_attributes`
- Network policy includes egress to OpenMetadata (`app=openmetadata`, TCP `8585`) so the UI/API can call OpenMetadata endpoints.
- Predefined connector files are seeded at pod startup from `configs/connectors/*.yaml` into `/opt/moat/runtime/connectors` and appear automatically in the UI selector.
