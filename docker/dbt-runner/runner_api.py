from __future__ import annotations

import base64
import os
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict

import requests
import yaml
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="fq-dbt-runner", version="1.0.0")
_run_lock = threading.Lock()


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _tail(text: str, max_lines: int = 120, max_chars: int = 20000) -> str:
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    clipped = "\n".join(lines)
    if len(clipped) > max_chars:
        clipped = clipped[-max_chars:]
    return clipped


def _run_command(
    command: list[str],
    env: Dict[str, str],
    timeout_seconds: int,
    cwd: str | None = None,
) -> Dict[str, Any]:
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        timeout=timeout_seconds,
        check=False,
    )
    return {
        "command": " ".join(command),
        "returnCode": proc.returncode,
        "stdoutTail": _tail(proc.stdout),
        "stderrTail": _tail(proc.stderr),
    }


def _validate_artifacts(project_dir: Path) -> Dict[str, str]:
    target = project_dir / "target"
    required = {
        "manifest": target / "manifest.json",
        "catalog": target / "catalog.json",
        "runResults": target / "run_results.json",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        raise RuntimeError(f"Missing dbt artifact(s): {', '.join(missing)}")
    return {name: str(path) for name, path in required.items()}


def _login_openmetadata(api_base: str, email: str, password: str) -> str:
    payload = {
        "email": email,
        "password": base64.b64encode(password.encode()).decode(),
    }
    response = requests.post(
        f"{api_base.rstrip('/')}/v1/users/login",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    token = response.json().get("accessToken")
    if not token:
        raise RuntimeError("OpenMetadata login returned no accessToken")
    return token


def _build_trino_ingest_config(request: "RunRequest", jwt_token: str) -> Dict[str, Any]:
    return {
        "source": {
            "type": "trino",
            "serviceName": request.om_service_name,
            "serviceConnection": {
                "config": {
                    "type": "Trino",
                    "hostPort": f"{request.trino_host}:{request.trino_port}",
                    "username": request.om_trino_username,
                    "catalog": request.trino_catalog,
                    "databaseSchema": request.trino_schema,
                    "connectionOptions": {},
                    "connectionArguments": {},
                }
            },
            "sourceConfig": {
                "config": {
                    "type": "DatabaseMetadata",
                    "schemaFilterPattern": {"includes": [request.trino_schema]},
                    "tableFilterPattern": {"includes": [request.dbt_table_name]},
                }
            },
        },
        "sink": {"type": "metadata-rest", "config": {}},
        "workflowConfig": {
            "openMetadataServerConfig": {
                "hostPort": request.om_server_api,
                "authProvider": "openmetadata",
                "securityConfig": {"jwtToken": jwt_token},
            }
        },
    }


def _build_dbt_ingest_config(
    request: "RunRequest",
    jwt_token: str,
    artifacts: Dict[str, str],
) -> Dict[str, Any]:
    return {
        "source": {
            "type": "dbt",
            "serviceName": request.om_service_name,
            "sourceConfig": {
                "config": {
                    "type": "DBT",
                    "dbtConfigSource": {
                        "dbtConfigType": "local",
                        "dbtCatalogFilePath": artifacts["catalog"],
                        "dbtManifestFilePath": artifacts["manifest"],
                        "dbtRunResultsFilePath": artifacts["runResults"],
                    },
                    "dbtUpdateDescriptions": True,
                    "includeTags": True,
                    "dbtClassificationName": "dbtTags",
                    "schemaFilterPattern": {"includes": [request.trino_schema]},
                    "tableFilterPattern": {"includes": [request.dbt_table_name]},
                }
            },
        },
        "sink": {"type": "metadata-rest", "config": {}},
        "workflowConfig": {
            "openMetadataServerConfig": {
                "hostPort": request.om_server_api,
                "authProvider": "openmetadata",
                "securityConfig": {"jwtToken": jwt_token},
            }
        },
    }


def _run_ingest(config: Dict[str, Any], timeout_seconds: int) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as config_file:
        yaml.safe_dump(config, config_file, sort_keys=False)
        config_path = config_file.name

    try:
        return _run_command(
            command=["metadata", "ingest", "-c", config_path],
            env=os.environ.copy(),
            timeout_seconds=timeout_seconds,
        )
    finally:
        try:
            os.remove(config_path)
        except OSError:
            pass


class RunRequest(BaseModel):
    model_selector: str = _env("DBT_MODEL_SELECTOR", "fq_orders")
    dbt_project_dir: str = _env("DBT_PROJECT_DIR", "/app/dbt")
    dbt_profiles_dir: str = _env("DBT_PROFILES_DIR", "/app/dbt")
    dbt_timeout_seconds: int = int(_env("DBT_RUN_TIMEOUT_SECONDS", "1800"))
    trino_host: str = _env("TRINO_HOST", "fq-trino.fq.svc.cluster.local")
    trino_port: int = int(_env("TRINO_PORT", "8080"))
    trino_user: str = _env("TRINO_USER", "dbt")
    trino_catalog: str = _env("TRINO_CATALOG", "hms_db")
    trino_schema: str = _env("TRINO_SCHEMA", "fq_dbt")
    dbt_table_name: str = _env("DBT_TABLE_NAME", "fq_orders_v2")
    ingest_openmetadata: bool = True
    om_server_api: str = _env("OM_SERVER_API", "http://om-server.openmetadata.svc.cluster.local:8585/api")
    om_admin_email: str = _env("OM_ADMIN_EMAIL", "admin@open-metadata.org")
    om_admin_password: str = _env("OM_ADMIN_PASSWORD", "admin")
    om_service_name: str = _env("OM_SERVICE_NAME", "fq_trino")
    om_trino_username: str = _env("OM_TRINO_USERNAME", "openmetadata")
    om_ingest_timeout_seconds: int = int(_env("OM_INGEST_TIMEOUT_SECONDS", "1200"))


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run(request: RunRequest):
    if not _run_lock.acquire(blocking=False):
        return JSONResponse(
            status_code=409,
            content={"status": "busy", "message": "A dbt run is already in progress"},
        )

    run_id = uuid.uuid4().hex[:12]
    started = time.time()
    result: Dict[str, Any] = {
        "status": "failed",
        "runId": run_id,
        "modelSelector": request.model_selector,
        "trinoSchema": request.trino_schema,
        "dbtTableName": request.dbt_table_name,
    }

    try:
        project_dir = Path(request.dbt_project_dir)
        if not project_dir.exists():
            raise RuntimeError(f"dbt project directory not found: {project_dir}")

        dbt_env = os.environ.copy()
        dbt_env.update(
            {
                "DBT_PROJECT_DIR": request.dbt_project_dir,
                "DBT_PROFILES_DIR": request.dbt_profiles_dir,
                "DBT_MODEL_SELECTOR": request.model_selector,
                "TRINO_HOST": request.trino_host,
                "TRINO_PORT": str(request.trino_port),
                "TRINO_USER": request.trino_user,
                "TRINO_CATALOG": request.trino_catalog,
                "TRINO_SCHEMA": request.trino_schema,
            }
        )

        dbt_run = _run_command(
            command=["/app/run-dbt.sh"],
            env=dbt_env,
            timeout_seconds=request.dbt_timeout_seconds,
            cwd="/app",
        )
        result["dbt"] = dbt_run
        if dbt_run["returnCode"] != 0:
            raise RuntimeError("dbt run failed")

        artifacts = _validate_artifacts(project_dir)
        result["artifacts"] = artifacts

        if request.ingest_openmetadata:
            token = _login_openmetadata(
                api_base=request.om_server_api,
                email=request.om_admin_email,
                password=request.om_admin_password,
            )
            result["openmetadataAuth"] = {"authenticated": True}

            trino_ingest = _run_ingest(
                _build_trino_ingest_config(request=request, jwt_token=token),
                timeout_seconds=request.om_ingest_timeout_seconds,
            )
            result["trinoMetadataIngest"] = trino_ingest
            if trino_ingest["returnCode"] != 0:
                raise RuntimeError("Trino metadata ingestion failed")

            dbt_ingest = _run_ingest(
                _build_dbt_ingest_config(request=request, jwt_token=token, artifacts=artifacts),
                timeout_seconds=request.om_ingest_timeout_seconds,
            )
            result["dbtMetadataIngest"] = dbt_ingest
            if dbt_ingest["returnCode"] != 0:
                raise RuntimeError("dbt metadata ingestion failed")

        result["status"] = "success"
        result["durationSeconds"] = round(time.time() - started, 2)
        return result
    except Exception as exc:
        result["error"] = str(exc)
        result["durationSeconds"] = round(time.time() - started, 2)
        return JSONResponse(status_code=500, content=result)
    finally:
        _run_lock.release()
