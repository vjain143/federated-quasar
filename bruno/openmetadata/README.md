# OpenMetadata Bruno Project

This Bruno project is structured for long-term maintainability and separation of responsibilities.

## Structure

- `environments/`
  - Runtime variables (`base_url`, `jwt_token`, paging/query defaults, and payload placeholders)
- `00-auth/`
  - Login/auth requests
- `01-generic-resource/`
  - Generic CRUD requests that work with any OpenMetadata resource path
- `10-governance/`, `20-data-assets/`, `30-teams/`, `40-services/`
  - Curated resource-specific list requests
- `resources/resource-paths.csv`
  - Canonical SDK-derived map of resource base paths from:
    - OpenMetadata docs: `v1.12.x` metadata standard APIs
    - OpenMetadata SDK services source tree
- `scripts/generate-resource-paths.sh`
  - Regenerates `resources/resource-paths.csv` from `openmetadata-sdk/src/main/java/org/openmetadata/sdk/services`

## Quick Start

1. Open this folder in Bruno.
2. Select environment `local`.
3. Run `00-auth/Login`.
4. Copy token to `jwt_token` in environment.
5. Run any request.

## Generic Resource Requests

In `01-generic-resource`, set:

- `resource_path` (example: `/v1/users`, `/v1/tables`, `/v1/classifications`)
- `entity_id` or `entity_name` as needed

Use `resources/resource-paths.csv` to pick valid paths.

## Refresh Resource Map

Run:

`./scripts/generate-resource-paths.sh`

Optional input:

- `./scripts/generate-resource-paths.sh /path/to/OpenMetadata`

If no path is passed, the script uses a sparse clone in `/tmp/OpenMetadata-sdk-src`.
