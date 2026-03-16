# Moat Bruno Collection

This Bruno project targets the Moat API running on Kubernetes NodePort.

Default local endpoint:

- `http://localhost:32080`

## Included request groups

- `00 System`: Healthcheck
- `10 OPA`: OPA status update + bundle fetch
- `20 SCIM Discovery`: ServiceProviderConfig, ResourceTypes, Schemas
- `30 SCIM Users`: List, create, update, delete users
- `40 SCIM Groups`: List, create, update, delete groups

## Notes

- OPA endpoints use API-key auth via bearer token.
- In your current deployment, the default key is `bearer-token`.
- SCIM and healthcheck endpoints are configured with `auth_method: none`.
