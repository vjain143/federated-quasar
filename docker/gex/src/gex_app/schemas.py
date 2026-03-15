from __future__ import annotations

from pydantic import BaseModel

from .utils import env


class RunRequest(BaseModel):
    project_id: str | None = None
    model_selector: str = env("DBT_MODEL_SELECTOR", "").strip() or "*"
    dbt_project_dir: str = env("DBT_PROJECT_DIR", "/app/dbt")
    dbt_profiles_dir: str = env("DBT_PROFILES_DIR", "/app/dbt")
    dbt_timeout_seconds: int = int(env("DBT_RUN_TIMEOUT_SECONDS", "1800"))
    trino_host: str = env("TRINO_HOST", "fq-trino.fq.svc.cluster.local")
    trino_port: int = int(env("TRINO_PORT", "8080"))
    trino_user: str = env("TRINO_USER", "dbt")
    trino_catalog: str = env("TRINO_CATALOG", "hms_db")
    trino_schema: str = env("TRINO_SCHEMA", "fq_dbt")
    dbt_table_name: str = env("DBT_TABLE_NAME", "")
    ingest_openmetadata: bool = True
    om_server_api: str = env("OM_SERVER_API", "http://om-server.openmetadata.svc.cluster.local:8585/api")
    om_admin_email: str = env("OM_ADMIN_EMAIL", "admin@open-metadata.org")
    om_admin_password: str = env("OM_ADMIN_PASSWORD", "admin")
    om_service_name: str = env("OM_SERVICE_NAME", "fq_trino")
    om_trino_username: str = env("OM_TRINO_USERNAME", "openmetadata")
    om_ingest_timeout_seconds: int = int(env("OM_INGEST_TIMEOUT_SECONDS", "1200"))
