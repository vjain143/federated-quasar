# AIX OPA

Namespace context:

```bash
kubectl config set-context --current --namespace=aix
```

Folder: `kube/components/aix/kubernetes/opa`

Purpose:

- Runs OPA as the policy decision point.
- Serves authorization responses to Trino.
- Pulls policy bundles from Moat.

Resources in this folder:

- `aix-opa-deployment.yaml`: Deploys the OPA server.
- `aix-opa-service.yaml`: Exposes OPA on port `8181` as a `NodePort`.
- `aix-opa-ingress-network-policy.yaml`: Allows Trino to call OPA.
- `aix-opa-egress-network-policy.yaml`: Allows OPA to reach DNS and Moat.
- `configs/config.yaml`: OPA bundle and service configuration.
- `kustomization.yaml`: Builds the component and generates the OPA configmap.
