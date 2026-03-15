#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

OM_SERVER_API="${OM_SERVER_API:-http://localhost:30585/api}"
OM_ADMIN_EMAIL="${OM_ADMIN_EMAIL:-admin@open-metadata.org}"
OM_ADMIN_PASSWORD="${OM_ADMIN_PASSWORD:-admin}"
OM_TABLE_FQN="${OM_TABLE_FQN:-fq_trino.hms_db.fq_dbt.fq_orders_v2}"

AIX_NAMESPACE="${AIX_NAMESPACE:-aix}"
MYSQL_DEPLOYMENT="${MYSQL_DEPLOYMENT:-mysql}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-change-me-root}"
MOAT_PLATFORM="${MOAT_PLATFORM:-trino}"
INGESTION_PROCESS_ID="${INGESTION_PROCESS_ID:-1001}"

export OM_SERVER_API
export OM_ADMIN_EMAIL
export OM_ADMIN_PASSWORD
export OM_TABLE_FQN
export MOAT_PLATFORM
export INGESTION_PROCESS_ID

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Missing python runtime: ${PYTHON_BIN}" >&2
  exit 1
fi

TMP_SQL_B64="$(mktemp)"
"${PYTHON_BIN}" > "${TMP_SQL_B64}" <<'PY'
import base64
import json
import os
import urllib.parse
import urllib.request

om_server_api = os.environ["OM_SERVER_API"].rstrip("/")
om_admin_email = os.environ["OM_ADMIN_EMAIL"]
om_admin_password = os.environ["OM_ADMIN_PASSWORD"]
om_table_fqn = os.environ["OM_TABLE_FQN"]
moat_platform = os.environ["MOAT_PLATFORM"]
ingestion_process_id = int(os.environ["INGESTION_PROCESS_ID"])

def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "''")

# 1) Login to OpenMetadata
login_payload = json.dumps(
    {
        "email": om_admin_email,
        "password": base64.b64encode(om_admin_password.encode()).decode(),
    }
).encode()
login_req = urllib.request.Request(
    om_server_api + "/v1/users/login",
    data=login_payload,
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(login_req, timeout=30) as resp:
    token = json.loads(resp.read().decode())["accessToken"]

# 2) Pull table metadata
table_url = (
    om_server_api
    + "/v1/tables/name/"
    + urllib.parse.quote(om_table_fqn, safe="")
    + "?fields=tags"
)
table_req = urllib.request.Request(
    table_url,
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(table_req, timeout=30) as resp:
    table = json.loads(resp.read().decode())

# 3) Build Moat resource key (drop OpenMetadata service prefix)
parts = om_table_fqn.split(".")
if len(parts) < 4:
    raise ValueError(f"Unexpected OpenMetadata table FQN: {om_table_fqn}")
moat_fqn = ".".join(parts[1:])

# 4) Convert tags into (attribute_key, attribute_value)
attrs = []
for tag_obj in table.get("tags", []):
    tag_fqn = tag_obj.get("tagFQN", "")
    normalized = tag_fqn.split(".", 1)[1] if "." in tag_fqn else tag_fqn
    if ":" in normalized:
        k, v = normalized.split(":", 1)
    else:
        k, v = "tag", normalized
    if k and v:
        attrs.append((k.strip(), v.strip()))

# Stable dedupe while preserving order
seen = set()
deduped = []
for item in attrs:
    if item not in seen:
        deduped.append(item)
        seen.add(item)

value_rows = ",".join(
    [
        f"('{esc(moat_fqn)}','{esc(k)}','{esc(v)}',{ingestion_process_id},1)"
        for k, v in deduped
    ]
)

sql_lines = [
    "USE moat;",
    f"DELETE FROM resource_attributes WHERE fq_name = '{esc(moat_fqn)}';",
    f"DELETE FROM resources WHERE fq_name = '{esc(moat_fqn)}';",
    (
        "INSERT INTO resources "
        "(fq_name, platform, object_type, ingestion_process_id, active) VALUES "
        f"('{esc(moat_fqn)}','{esc(moat_platform)}','table',{ingestion_process_id},1);"
    ),
]
if value_rows:
    sql_lines.append(
        "INSERT INTO resource_attributes "
        "(fq_name, attribute_key, attribute_value, ingestion_process_id, active) VALUES "
        + value_rows
        + ";"
    )

sql = "\n".join(sql_lines) + "\n"
print(base64.b64encode(sql.encode()).decode())
PY

SQL_B64="$(cat "${TMP_SQL_B64}")"
rm -f "${TMP_SQL_B64}"

echo "Syncing OpenMetadata table '${OM_TABLE_FQN}' into Moat DB..."
kubectl exec -n "${AIX_NAMESPACE}" deploy/"${MYSQL_DEPLOYMENT}" -- sh -lc \
  "echo '${SQL_B64}' | base64 -d > /tmp/moat_sync.sql && mysql -uroot -p'${MYSQL_ROOT_PASSWORD}' < /tmp/moat_sync.sql && rm -f /tmp/moat_sync.sql"

echo "Sync complete."
echo "Synced Moat resource FQN: ${OM_TABLE_FQN#*.}"
