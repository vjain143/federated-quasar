from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import requests
import yaml

from gex_app import state
from gex_app.schemas import RunRequest
from gex_app.utils import now_iso, tail


class RunCancelled(Exception):
    pass


def run_command(
    command: list[str],
    env: dict[str, str],
    timeout_seconds: int,
    run_id: str,
    cwd: str | None = None,
) -> dict[str, Any]:
    if state.is_cancelled(run_id):
        raise RunCancelled("Run cancelled before command start")

    started = time.time()
    started_at = now_iso()
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=cwd,
    )
    state.set_active_process(run_id=run_id, proc=proc)

    timed_out = False
    cancelled = False
    stdout = ""
    stderr = ""

    try:
        while True:
            if state.is_cancelled(run_id):
                cancelled = True
                try:
                    proc.terminate()
                except OSError:
                    pass

            elapsed = time.time() - started
            if elapsed > timeout_seconds:
                timed_out = True
                try:
                    proc.terminate()
                except OSError:
                    pass

            try:
                stdout, stderr = proc.communicate(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                continue
    finally:
        state.clear_active_process(run_id=run_id, proc=proc)

    if timed_out:
        raise RuntimeError(f"Command timed out after {timeout_seconds}s: {' '.join(command)}")
    if cancelled:
        raise RunCancelled("Run cancelled by user")

    finished = time.time()
    return {
        "command": " ".join(command),
        "returnCode": proc.returncode,
        "stdoutTail": tail(stdout),
        "stderrTail": tail(stderr),
        "startedAt": started_at,
        "finishedAt": now_iso(),
        "durationSeconds": round(finished - started, 2),
    }


def validate_artifacts(project_dir: Path) -> dict[str, str]:
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


def login_openmetadata(api_base: str, email: str, password: str) -> str:
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


def safe_load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        return {}
    return value


def selector_matches_model(request_selector: str, node: dict[str, Any]) -> bool:
    selector = request_selector.strip()
    if not selector:
        return False
    if selector in {"*", "all", "ALL"}:
        return True

    name = str(node.get("name", "")).strip()
    alias = str(node.get("alias", "")).strip()
    unique_id = str(node.get("unique_id", "")).strip()
    original_file_path = str(node.get("original_file_path", "")).strip().lstrip("./")
    model_path = str(node.get("path", "")).strip().lstrip("./")

    if selector.startswith("path:"):
        expected = selector[len("path:") :].strip().lstrip("./")
        candidates = [original_file_path, model_path]
        return any(candidate == expected or candidate.endswith(expected) for candidate in candidates if candidate)

    return selector in {name, alias, unique_id}


def resolve_table_filter_includes(request: RunRequest, artifacts: dict[str, str]) -> list[str] | None:
    includes: list[str] = []
    explicit_table = request.dbt_table_name.strip()
    if explicit_table:
        includes.append(explicit_table)

    try:
        manifest = safe_load_json(artifacts["manifest"])
    except Exception:
        return includes or None

    nodes = manifest.get("nodes", {})
    if not isinstance(nodes, dict):
        return includes or None

    for node in nodes.values():
        if not isinstance(node, dict):
            continue
        if node.get("resource_type") != "model":
            continue
        if str(node.get("schema", "")).strip() != request.trino_schema:
            continue
        if not selector_matches_model(request.model_selector, node):
            continue
        alias = str(node.get("alias") or node.get("name") or "").strip()
        if alias and alias not in includes:
            includes.append(alias)

    return includes or None


def build_trino_ingest_config(
    request: RunRequest,
    jwt_token: str,
    table_filter_includes: list[str] | None,
) -> dict[str, Any]:
    source_config: dict[str, Any] = {
        "type": "DatabaseMetadata",
        "schemaFilterPattern": {"includes": [request.trino_schema]},
    }
    if table_filter_includes:
        source_config["tableFilterPattern"] = {"includes": table_filter_includes}

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
            "sourceConfig": {"config": source_config},
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


def build_dbt_ingest_config(
    request: RunRequest,
    jwt_token: str,
    artifacts: dict[str, str],
    table_filter_includes: list[str] | None,
) -> dict[str, Any]:
    source_config: dict[str, Any] = {
        "type": "DBT",
        "dbtConfigSource": {
            "dbtConfigType": "local",
            "dbtCatalogFilePath": artifacts["catalog"],
            "dbtManifestFilePath": artifacts["manifest"],
            "dbtRunResultsFilePath": artifacts["runResults"],
        },
        "dbtUpdateDescriptions": True,
        "dbtUpdateOwners": True,
        "includeTags": True,
        "dbtClassificationName": "dbtTags",
        "schemaFilterPattern": {"includes": [request.trino_schema]},
    }
    if table_filter_includes:
        source_config["tableFilterPattern"] = {"includes": table_filter_includes}

    return {
        "source": {
            "type": "dbt",
            "serviceName": request.om_service_name,
            "sourceConfig": {"config": source_config},
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


def run_ingest(config: dict[str, Any], timeout_seconds: int, run_id: str) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as config_file:
        yaml.safe_dump(config, config_file, sort_keys=False)
        config_path = config_file.name
    try:
        return run_command(
            command=["metadata", "ingest", "-c", config_path],
            env=os.environ.copy(),
            timeout_seconds=timeout_seconds,
            run_id=run_id,
        )
    finally:
        try:
            os.remove(config_path)
        except OSError:
            pass


def append_step(run: dict[str, Any], step: dict[str, Any]) -> None:
    run["steps"].append(step)
    state.store_run(run)


def mark_run_finished(run: dict[str, Any], status: str, started_epoch: float, error: str | None = None) -> None:
    run["status"] = status
    run["error"] = error
    run["finishedAt"] = now_iso()
    run["durationSeconds"] = round(time.time() - started_epoch, 2)
    state.clear_cancel(run["runId"])
    state.store_run(run)


def execute_pipeline(run: dict[str, Any], request: RunRequest, started_epoch: float) -> dict[str, Any]:
    if request.project_id:
        uploaded_project = state.get_project(request.project_id)
        if uploaded_project is None:
            raise RuntimeError(f"Uploaded project not found: {request.project_id}")
        project_dir = Path(uploaded_project["projectDir"])
        profiles_dir = uploaded_project.get("profilesDir", request.dbt_profiles_dir)
    else:
        project_dir = Path(request.dbt_project_dir)
        profiles_dir = request.dbt_profiles_dir

    if not project_dir.exists():
        raise RuntimeError(f"dbt project directory not found: {project_dir}")
    model_selector = request.model_selector.strip() or "*"
    request.model_selector = model_selector
    run["modelSelector"] = model_selector
    if isinstance(run.get("request"), dict):
        run["request"]["model_selector"] = model_selector
    state.store_run(run)

    dbt_env = os.environ.copy()
    dbt_env.update(
        {
            "DBT_PROJECT_DIR": str(project_dir),
            "DBT_PROFILES_DIR": str(profiles_dir),
            "DBT_MODEL_SELECTOR": model_selector,
            "TRINO_HOST": request.trino_host,
            "TRINO_PORT": str(request.trino_port),
            "TRINO_USER": request.trino_user,
            "TRINO_CATALOG": request.trino_catalog,
            "TRINO_SCHEMA": request.trino_schema,
        }
    )

    dbt_run = run_command(
        command=["/app/run-dbt.sh"],
        env=dbt_env,
        timeout_seconds=request.dbt_timeout_seconds,
        run_id=run["runId"],
        cwd="/app",
    )
    dbt_step = {
        "name": "dbt_run_test_docs",
        "status": "success" if dbt_run["returnCode"] == 0 else "failed",
        **dbt_run,
    }
    append_step(run, dbt_step)
    run["dbt"] = dbt_run
    if dbt_run["returnCode"] != 0:
        raise RuntimeError("dbt run failed")

    artifacts = validate_artifacts(project_dir)
    run["artifacts"] = artifacts
    resolved_table_filters = resolve_table_filter_includes(request=request, artifacts=artifacts)
    run["resolvedDbtTableFilters"] = resolved_table_filters or []
    append_step(
        run,
        {
            "name": "validate_dbt_artifacts",
            "status": "success",
            "startedAt": now_iso(),
            "finishedAt": now_iso(),
            "durationSeconds": 0.0,
            "details": {
                **artifacts,
                "resolvedTableFilterIncludes": resolved_table_filters or [],
            },
        },
    )

    if request.ingest_openmetadata:
        auth_started = time.time()
        token = login_openmetadata(
            api_base=request.om_server_api,
            email=request.om_admin_email,
            password=request.om_admin_password,
        )
        run["openmetadataAuth"] = {"authenticated": True}
        append_step(
            run,
            {
                "name": "openmetadata_auth",
                "status": "success",
                "startedAt": now_iso(),
                "finishedAt": now_iso(),
                "durationSeconds": round(time.time() - auth_started, 2),
                "details": {"authenticated": True},
            },
        )

        trino_ingest = run_ingest(
            build_trino_ingest_config(
                request=request,
                jwt_token=token,
                table_filter_includes=resolved_table_filters,
            ),
            timeout_seconds=request.om_ingest_timeout_seconds,
            run_id=run["runId"],
        )
        trino_step = {
            "name": "trino_metadata_ingest",
            "status": "success" if trino_ingest["returnCode"] == 0 else "failed",
            **trino_ingest,
        }
        append_step(run, trino_step)
        run["trinoMetadataIngest"] = trino_ingest
        if trino_ingest["returnCode"] != 0:
            raise RuntimeError("Trino metadata ingestion failed")

        dbt_ingest = run_ingest(
            build_dbt_ingest_config(
                request=request,
                jwt_token=token,
                artifacts=artifacts,
                table_filter_includes=resolved_table_filters,
            ),
            timeout_seconds=request.om_ingest_timeout_seconds,
            run_id=run["runId"],
        )
        dbt_ingest_step = {
            "name": "dbt_metadata_ingest",
            "status": "success" if dbt_ingest["returnCode"] == 0 else "failed",
            **dbt_ingest,
        }
        append_step(run, dbt_ingest_step)
        run["dbtMetadataIngest"] = dbt_ingest
        if dbt_ingest["returnCode"] != 0:
            raise RuntimeError("dbt metadata ingestion failed")

    mark_run_finished(run, "success", started_epoch)
    return run


def execute_with_lock(run: dict[str, Any], request: RunRequest, started_epoch: float) -> dict[str, Any]:
    try:
        return execute_pipeline(run=run, request=request, started_epoch=started_epoch)
    except RunCancelled as exc:
        mark_run_finished(run, "cancelled", started_epoch, str(exc))
        raise
    except Exception as exc:
        mark_run_finished(run, "failed", started_epoch, str(exc))
        raise
    finally:
        state.run_lock.release()


def run_async_worker(run: dict[str, Any], request: RunRequest, started_epoch: float) -> None:
    try:
        execute_with_lock(run=run, request=request, started_epoch=started_epoch)
    except Exception:
        return


def to_summary(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "runId": run.get("runId"),
        "projectId": run.get("projectId"),
        "status": run.get("status"),
        "modelSelector": run.get("modelSelector"),
        "trinoSchema": run.get("trinoSchema"),
        "dbtTableName": run.get("dbtTableName"),
        "startedAt": run.get("startedAt"),
        "finishedAt": run.get("finishedAt"),
        "durationSeconds": run.get("durationSeconds"),
        "stepCount": len(run.get("steps", [])),
        "error": run.get("error"),
    }
