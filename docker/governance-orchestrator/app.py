from __future__ import annotations

import base64
import copy
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests
import yaml
from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="fq-governance-orchestrator", version="1.0.0")

_run_lock = threading.Lock()
_history_lock = threading.Lock()
_history_limit = int(os.getenv("RUN_HISTORY_LIMIT", "200"))
_runs: Dict[str, Dict[str, Any]] = {}
_run_order: deque[str] = deque()
_project_lock = threading.Lock()
_project_limit = int(os.getenv("PROJECT_UPLOAD_LIMIT", "20"))
_project_base_dir = Path(os.getenv("PROJECT_UPLOAD_ROOT", "/tmp/governance-projects"))
_projects: Dict[str, Dict[str, Any]] = {}
_project_order: deque[str] = deque()
_active_lock = threading.Lock()
_active_run_id: str | None = None
_active_proc: subprocess.Popen[str] | None = None
_cancelled_runs: set[str] = set()


class RunCancelled(Exception):
    pass


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tail(text: str, max_lines: int = 120, max_chars: int = 20000) -> str:
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    clipped = "\n".join(lines)
    if len(clipped) > max_chars:
        clipped = clipped[-max_chars:]
    return clipped


def _store_run(run: Dict[str, Any]) -> None:
    run_id = run["runId"]
    with _history_lock:
        _runs[run_id] = copy.deepcopy(run)
        try:
            _run_order.remove(run_id)
        except ValueError:
            pass
        _run_order.appendleft(run_id)
        while len(_run_order) > _history_limit:
            stale = _run_order.pop()
            _runs.pop(stale, None)


def _get_run(run_id: str) -> Dict[str, Any] | None:
    with _history_lock:
        value = _runs.get(run_id)
        if value is None:
            return None
        return copy.deepcopy(value)


def _list_runs(limit: int) -> list[Dict[str, Any]]:
    with _history_lock:
        run_ids = list(_run_order)[:limit]
        return [copy.deepcopy(_runs[run_id]) for run_id in run_ids if run_id in _runs]


def _discover_models(project_dir: Path | None = None) -> Dict[str, Any]:
    if project_dir is None:
        project_dir = Path(_env("DBT_PROJECT_DIR", "/app/dbt"))
    models_root = project_dir / "models"
    if not models_root.exists():
        raise RuntimeError(f"dbt models directory not found: {models_root}")

    models: list[Dict[str, str]] = []
    for model_path in sorted(models_root.rglob("*.sql")):
        rel_path = model_path.relative_to(models_root)
        if any(part.startswith(".") for part in rel_path.parts):
            continue

        rel_posix = rel_path.as_posix()
        model_dir = rel_path.parent.as_posix()
        if model_dir == ".":
            model_dir = ""

        models.append(
            {
                "name": model_path.stem,
                "file": rel_posix,
                "directory": model_dir,
                "selector": model_path.stem,
                "pathSelector": f"path:models/{rel_posix}",
            }
        )

    directories = sorted({model["directory"] for model in models if model["directory"]})
    return {
        "projectDir": str(project_dir),
        "modelsRoot": str(models_root),
        "directories": [""] + directories,
        "models": models,
    }


def _set_active_process(run_id: str, proc: subprocess.Popen[str]) -> None:
    global _active_proc, _active_run_id
    with _active_lock:
        _active_run_id = run_id
        _active_proc = proc


def _clear_active_process(run_id: str, proc: subprocess.Popen[str]) -> None:
    global _active_proc, _active_run_id
    with _active_lock:
        if _active_run_id == run_id and _active_proc is proc:
            _active_proc = None
            _active_run_id = None


def _is_cancelled(run_id: str) -> bool:
    with _active_lock:
        return run_id in _cancelled_runs


def _request_cancel(run_id: str) -> bool:
    proc: subprocess.Popen[str] | None
    with _active_lock:
        _cancelled_runs.add(run_id)
        proc = _active_proc if _active_run_id == run_id else None
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
        except OSError:
            pass
        return True
    return False


def _clear_cancel(run_id: str) -> None:
    with _active_lock:
        _cancelled_runs.discard(run_id)


def _store_project(project: Dict[str, Any]) -> None:
    project_id = project["projectId"]
    with _project_lock:
        _projects[project_id] = copy.deepcopy(project)
        try:
            _project_order.remove(project_id)
        except ValueError:
            pass
        _project_order.appendleft(project_id)
        while len(_project_order) > _project_limit:
            stale_id = _project_order.pop()
            stale_project = _projects.pop(stale_id, None)
            if stale_project:
                stale_dir = Path(stale_project["projectDir"])
                shutil.rmtree(stale_dir, ignore_errors=True)


def _get_project(project_id: str) -> Dict[str, Any] | None:
    with _project_lock:
        value = _projects.get(project_id)
        if value is None:
            return None
        return copy.deepcopy(value)


def _list_projects() -> list[Dict[str, Any]]:
    with _project_lock:
        return [copy.deepcopy(_projects[project_id]) for project_id in _project_order if project_id in _projects]


def _resolve_uploaded_project_dir(upload_root: Path) -> Path:
    if (upload_root / "dbt_project.yml").exists():
        return upload_root

    child_dirs = [path for path in upload_root.iterdir() if path.is_dir()]
    for child in child_dirs:
        if (child / "dbt_project.yml").exists():
            return child

    raise RuntimeError("Uploaded folder does not contain dbt_project.yml")


def _run_command(
    command: list[str],
    env: Dict[str, str],
    timeout_seconds: int,
    run_id: str,
    cwd: str | None = None,
) -> Dict[str, Any]:
    if _is_cancelled(run_id):
        raise RunCancelled("Run cancelled before command start")

    started = time.time()
    started_at = _now_iso()
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=cwd,
    )
    _set_active_process(run_id=run_id, proc=proc)

    timed_out = False
    cancelled = False
    stdout = ""
    stderr = ""
    try:
        while True:
            if _is_cancelled(run_id):
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
        _clear_active_process(run_id=run_id, proc=proc)

    if timed_out:
        raise RuntimeError(f"Command timed out after {timeout_seconds}s: {' '.join(command)}")
    if cancelled:
        raise RunCancelled("Run cancelled by user")

    finished = time.time()
    return {
        "command": " ".join(command),
        "returnCode": proc.returncode,
        "stdoutTail": _tail(stdout),
        "stderrTail": _tail(stderr),
        "startedAt": started_at,
        "finishedAt": _now_iso(),
        "durationSeconds": round(finished - started, 2),
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


def _run_ingest(config: Dict[str, Any], timeout_seconds: int, run_id: str) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as config_file:
        yaml.safe_dump(config, config_file, sort_keys=False)
        config_path = config_file.name
    try:
        return _run_command(
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


class RunRequest(BaseModel):
    project_id: str | None = None
    model_selector: str = _env("DBT_MODEL_SELECTOR", "fq_orders")
    dbt_project_dir: str = _env("DBT_PROJECT_DIR", "/app/dbt")
    dbt_profiles_dir: str = _env("DBT_PROFILES_DIR", "/app/dbt")
    dbt_timeout_seconds: int = int(_env("DBT_RUN_TIMEOUT_SECONDS", "1800"))
    trino_host: str = _env("TRINO_HOST", "fq-trino.fq.svc.cluster.local")
    trino_port: int = int(_env("TRINO_PORT", "8080"))
    trino_user: str = _env("TRINO_USER", "dbt")
    trino_catalog: str = _env("TRINO_CATALOG", "hms_db")
    trino_schema: str = _env("TRINO_SCHEMA", "fq_dbt")
    dbt_table_name: str = _env("DBT_TABLE_NAME", "fq_orders_as_select")
    ingest_openmetadata: bool = True
    om_server_api: str = _env("OM_SERVER_API", "http://om-server.openmetadata.svc.cluster.local:8585/api")
    om_admin_email: str = _env("OM_ADMIN_EMAIL", "admin@open-metadata.org")
    om_admin_password: str = _env("OM_ADMIN_PASSWORD", "admin")
    om_service_name: str = _env("OM_SERVICE_NAME", "fq_trino")
    om_trino_username: str = _env("OM_TRINO_USERNAME", "openmetadata")
    om_ingest_timeout_seconds: int = int(_env("OM_INGEST_TIMEOUT_SECONDS", "1200"))


def _create_run_record(request: RunRequest, run_id: str) -> Dict[str, Any]:
    return {
        "status": "running",
        "runId": run_id,
        "startedAt": _now_iso(),
        "finishedAt": None,
        "durationSeconds": None,
        "request": request.model_dump(),
        "projectId": request.project_id,
        "modelSelector": request.model_selector,
        "trinoSchema": request.trino_schema,
        "dbtTableName": request.dbt_table_name,
        "steps": [],
    }


def _append_step(run: Dict[str, Any], step: Dict[str, Any]) -> None:
    run["steps"].append(step)
    _store_run(run)


def _mark_run_finished(run: Dict[str, Any], status: str, started_epoch: float, error: str | None = None) -> None:
    run["status"] = status
    run["error"] = error
    run["finishedAt"] = _now_iso()
    run["durationSeconds"] = round(time.time() - started_epoch, 2)
    _clear_cancel(run["runId"])
    _store_run(run)


def _execute_pipeline(run: Dict[str, Any], request: RunRequest, started_epoch: float) -> Dict[str, Any]:
    if request.project_id:
        uploaded_project = _get_project(request.project_id)
        if uploaded_project is None:
            raise RuntimeError(f"Uploaded project not found: {request.project_id}")
        project_dir = Path(uploaded_project["projectDir"])
        profiles_dir = uploaded_project.get("profilesDir", request.dbt_profiles_dir)
    else:
        project_dir = Path(request.dbt_project_dir)
        profiles_dir = request.dbt_profiles_dir

    if not project_dir.exists():
        raise RuntimeError(f"dbt project directory not found: {project_dir}")

    dbt_env = os.environ.copy()
    dbt_env.update(
            {
                "DBT_PROJECT_DIR": str(project_dir),
                "DBT_PROFILES_DIR": str(profiles_dir),
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
        run_id=run["runId"],
        cwd="/app",
    )
    dbt_step = {
        "name": "dbt_run_test_docs",
        "status": "success" if dbt_run["returnCode"] == 0 else "failed",
        **dbt_run,
    }
    _append_step(run, dbt_step)
    run["dbt"] = dbt_run
    if dbt_run["returnCode"] != 0:
        raise RuntimeError("dbt run failed")

    artifacts = _validate_artifacts(project_dir)
    run["artifacts"] = artifacts
    _append_step(
        run,
        {
            "name": "validate_dbt_artifacts",
            "status": "success",
            "startedAt": _now_iso(),
            "finishedAt": _now_iso(),
            "durationSeconds": 0.0,
            "details": artifacts,
        },
    )

    if request.ingest_openmetadata:
        auth_started = time.time()
        token = _login_openmetadata(
            api_base=request.om_server_api,
            email=request.om_admin_email,
            password=request.om_admin_password,
        )
        run["openmetadataAuth"] = {"authenticated": True}
        _append_step(
            run,
            {
                "name": "openmetadata_auth",
                "status": "success",
                "startedAt": _now_iso(),
                "finishedAt": _now_iso(),
                "durationSeconds": round(time.time() - auth_started, 2),
                "details": {"authenticated": True},
            },
        )

        trino_ingest = _run_ingest(
            _build_trino_ingest_config(request=request, jwt_token=token),
            timeout_seconds=request.om_ingest_timeout_seconds,
            run_id=run["runId"],
        )
        trino_step = {
            "name": "trino_metadata_ingest",
            "status": "success" if trino_ingest["returnCode"] == 0 else "failed",
            **trino_ingest,
        }
        _append_step(run, trino_step)
        run["trinoMetadataIngest"] = trino_ingest
        if trino_ingest["returnCode"] != 0:
            raise RuntimeError("Trino metadata ingestion failed")

        dbt_ingest = _run_ingest(
            _build_dbt_ingest_config(request=request, jwt_token=token, artifacts=artifacts),
            timeout_seconds=request.om_ingest_timeout_seconds,
            run_id=run["runId"],
        )
        dbt_ingest_step = {
            "name": "dbt_metadata_ingest",
            "status": "success" if dbt_ingest["returnCode"] == 0 else "failed",
            **dbt_ingest,
        }
        _append_step(run, dbt_ingest_step)
        run["dbtMetadataIngest"] = dbt_ingest
        if dbt_ingest["returnCode"] != 0:
            raise RuntimeError("dbt metadata ingestion failed")

    _mark_run_finished(run, "success", started_epoch)
    return run


def _execute_with_lock(run: Dict[str, Any], request: RunRequest, started_epoch: float) -> Dict[str, Any]:
    try:
        return _execute_pipeline(run=run, request=request, started_epoch=started_epoch)
    except RunCancelled as exc:
        _mark_run_finished(run, "cancelled", started_epoch, str(exc))
        raise
    except Exception as exc:
        _mark_run_finished(run, "failed", started_epoch, str(exc))
        raise
    finally:
        _run_lock.release()


def _run_async_worker(run: Dict[str, Any], request: RunRequest, started_epoch: float) -> None:
    try:
        _execute_with_lock(run=run, request=request, started_epoch=started_epoch)
    except Exception:
        return


def _to_summary(run: Dict[str, Any]) -> Dict[str, Any]:
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


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _INDEX_HTML


@app.get("/health")
def health() -> Dict[str, Any]:
    active = None
    for run in _list_runs(limit=1):
        if run.get("status") == "running":
            active = run.get("runId")
    return {"status": "ok", "activeRunId": active}


@app.get("/api/runs")
def list_runs(limit: int = Query(default=25, ge=1, le=200)) -> Dict[str, Any]:
    runs = _list_runs(limit)
    return {"runs": [_to_summary(run) for run in runs]}


@app.get("/api/models")
def list_models(project_id: str | None = Query(default=None)) -> Dict[str, Any]:
    try:
        if project_id:
            project = _get_project(project_id)
            if project is None:
                return JSONResponse(status_code=404, content={"error": "project not found"})
            model_data = _discover_models(Path(project["projectDir"]))
            model_data["projectId"] = project_id
            return model_data
        model_data = _discover_models()
        model_data["projectId"] = None
        return model_data
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/api/projects")
def list_projects() -> Dict[str, Any]:
    projects = _list_projects()
    return {
        "projects": [
            {
                "projectId": project["projectId"],
                "projectName": project["projectName"],
                "projectDir": project["projectDir"],
                "uploadedAt": project["uploadedAt"],
            }
            for project in projects
        ]
    }


@app.post("/api/projects/upload")
async def upload_project(files: list[UploadFile] = File(...)):
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})

    project_id = uuid.uuid4().hex[:12]
    upload_root = _project_base_dir / project_id
    upload_root.mkdir(parents=True, exist_ok=True)

    try:
        for file in files:
            rel_name = file.filename or ""
            rel_path = Path(rel_name)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                return JSONResponse(status_code=400, content={"error": f"Invalid uploaded path: {rel_name}"})
            target_path = upload_root / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = await file.read()
            target_path.write_bytes(payload)
            await file.close()

        project_dir = _resolve_uploaded_project_dir(upload_root)
        profiles_dir = project_dir if (project_dir / "profiles.yml").exists() else Path(_env("DBT_PROFILES_DIR", "/app/dbt"))
        model_data = _discover_models(project_dir=project_dir)
        project_name = project_dir.name

        _store_project(
            {
                "projectId": project_id,
                "projectName": project_name,
                "projectDir": str(project_dir),
                "profilesDir": str(profiles_dir),
                "uploadedAt": _now_iso(),
            }
        )

        return {
            "status": "uploaded",
            "project": {
                "projectId": project_id,
                "projectName": project_name,
                "projectDir": str(project_dir),
                "profilesDir": str(profiles_dir),
                "uploadedAt": _now_iso(),
            },
            "models": model_data.get("models", []),
            "directories": model_data.get("directories", []),
            "projectId": project_id,
        }
    except Exception as exc:
        shutil.rmtree(upload_root, ignore_errors=True)
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> Dict[str, Any]:
    run = _get_run(run_id)
    if run is None:
        return JSONResponse(status_code=404, content={"error": "run not found"})
    return run


@app.post("/api/runs")
def start_run(request: RunRequest):
    if not _run_lock.acquire(blocking=False):
        busy = next((run for run in _list_runs(limit=1) if run.get("status") == "running"), None)
        return JSONResponse(
            status_code=409,
            content={
                "status": "busy",
                "message": "A run is already in progress",
                "activeRunId": busy.get("runId") if busy else None,
            },
        )

    run_id = uuid.uuid4().hex[:12]
    started_epoch = time.time()
    run = _create_run_record(request=request, run_id=run_id)
    _store_run(run)

    thread = threading.Thread(
        target=_run_async_worker,
        args=(run, request, started_epoch),
        daemon=True,
        name=f"run-{run_id}",
    )
    thread.start()
    return JSONResponse(status_code=202, content={"status": "accepted", "runId": run_id})


@app.post("/api/runs/{run_id}/stop")
def stop_run(run_id: str) -> Dict[str, Any]:
    run = _get_run(run_id)
    if run is None:
        return JSONResponse(status_code=404, content={"error": "run not found"})
    accepted = _request_cancel(run_id)
    return {"status": "stop_requested", "runId": run_id, "accepted": accepted}


@app.post("/run")
def run_sync(request: RunRequest):
    if not _run_lock.acquire(blocking=False):
        busy = next((run for run in _list_runs(limit=1) if run.get("status") == "running"), None)
        return JSONResponse(
            status_code=409,
            content={
                "status": "busy",
                "message": "A run is already in progress",
                "activeRunId": busy.get("runId") if busy else None,
            },
        )

    run_id = uuid.uuid4().hex[:12]
    started_epoch = time.time()
    run = _create_run_record(request=request, run_id=run_id)
    _store_run(run)

    try:
        result = _execute_with_lock(run=run, request=request, started_epoch=started_epoch)
        return result
    except Exception:
        failed = _get_run(run_id) or run
        return JSONResponse(status_code=500, content=failed)


_INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Governance Orchestrator</title>
  <style>
    :root {
      --bg: #0e1528;
      --panel: #121f3c;
      --border: #2a4369;
      --text: #e5e7eb;
      --muted: #94a3b8;
      --accent: #22d3ee;
      --ok: #10b981;
      --fail: #ef4444;
      --running: #f59e0b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--text);
      min-height: 100vh;
      background: radial-gradient(circle at 15% 0%, #173668, var(--bg) 50%);
    }
    .wrap {
      max-width: 1360px;
      margin: 0 auto;
      padding: 20px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 31px;
      letter-spacing: 0.2px;
    }
    .subtitle {
      margin-bottom: 18px;
      color: var(--muted);
    }
    .grid {
      display: grid;
      grid-template-columns: 420px 1fr;
      gap: 16px;
      margin-bottom: 16px;
    }
    .panel {
      background: linear-gradient(180deg, #13274a, var(--panel));
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 10px 28px rgba(0,0,0,0.24);
    }
    .panel h2 {
      margin: 0 0 10px;
      font-size: 16px;
      color: #dbeafe;
    }
    label {
      display: block;
      margin: 10px 0 5px;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    input, select, button, textarea {
      width: 100%;
      border-radius: 8px;
      border: 1px solid #3a5987;
      padding: 10px 12px;
      font-size: 14px;
      color: var(--text);
      background: #0f1b33;
    }
    button {
      border: none;
      cursor: pointer;
      color: #032433;
      background: linear-gradient(90deg, #06b6d4, #67e8f9);
      font-weight: 700;
    }
    button.secondary {
      margin-top: 8px;
      background: linear-gradient(90deg, #0f172a, #1e293b);
      border: 1px solid #3a5987;
      color: #dbeafe;
      font-weight: 600;
    }
    button:disabled {
      opacity: 0.65;
      cursor: not-allowed;
    }
    .spacer { height: 6px; }
    .player-controls {
      display: grid;
      grid-template-columns: repeat(4, minmax(80px, 1fr));
      gap: 8px;
      margin-top: 10px;
      margin-bottom: 8px;
    }
    .control-btn {
      border: 1px solid #3a5987;
      color: #dbeafe;
      background: linear-gradient(90deg, #0f172a, #1e293b);
      font-weight: 700;
    }
    .control-play {
      color: #032433;
      border: none;
      background: linear-gradient(90deg, #06b6d4, #67e8f9);
    }
    .control-stop {
      color: #fee2e2;
      border: 1px solid #7f1d1d;
      background: linear-gradient(90deg, #7f1d1d, #b91c1c);
    }
    .meta {
      color: var(--muted);
      font-size: 12px;
    }
    .history-row {
      border: 1px solid #2f4a73;
      border-radius: 8px;
      background: #0e1c35;
      padding: 10px;
      margin-bottom: 9px;
      cursor: pointer;
    }
    .history-row.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px var(--accent) inset;
    }
    .row-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
    }
    .badge {
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      font-weight: 700;
    }
    .badge.success { background: rgba(16,185,129,.22); color: #6ee7b7; }
    .badge.failed { background: rgba(239,68,68,.22); color: #fca5a5; }
    .badge.running { background: rgba(245,158,11,.22); color: #fcd34d; }
    .badge.cancelled { background: rgba(148,163,184,.25); color: #cbd5e1; }
    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .console-panel {
      padding-top: 12px;
    }
    .console-toolbar {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 10px;
    }
    .console-title {
      margin: 0 0 8px;
      font-size: 14px;
      color: #dbeafe;
    }
    #console-output {
      margin: 0;
      border-radius: 8px;
      border: 1px solid #2f4a73;
      background: #060f20;
      color: #d1d5db;
      font-family: "JetBrains Mono", "Consolas", monospace;
      font-size: 12px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
      height: 380px;
      overflow: auto;
      padding: 12px;
    }
    .model-path {
      margin-top: 6px;
      padding: 8px;
      border: 1px solid #304c77;
      border-radius: 8px;
      background: #0b1830;
      font-size: 12px;
      color: #cbd5e1;
      word-break: break-word;
    }
    @media (max-width: 1024px) {
      .grid { grid-template-columns: 1fr; }
      .console-toolbar { grid-template-columns: 1fr; }
      .player-controls { grid-template-columns: repeat(2, minmax(80px, 1fr)); }
      #console-output { height: 300px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Governance Orchestrator</h1>
    <div class="subtitle">Use music-player style controls: Load, Refresh, Play, Stop. Browse local folder, pick model, run, and monitor bottom console logs.</div>

    <div class="grid">
      <section class="panel">
        <h2>New Execution</h2>
        <form id="run-form">
          <label for="project-select">Project Source</label>
          <select id="project-select"></select>
          <div id="project-path" class="model-path">Using bundled project.</div>

          <label for="project-folder-input">Browse Local Project Folder</label>
          <input id="project-folder-input" type="file" webkitdirectory directory multiple />

          <div class="player-controls">
            <button id="load-project" type="button" class="control-btn">Load</button>
            <button id="refresh-all" type="button" class="control-btn">Refresh</button>
            <button id="play-run" type="submit" class="control-btn control-play">Play</button>
            <button id="stop-run" type="button" class="control-btn control-stop">Stop</button>
          </div>

          <label for="model-directory">Browse Directory</label>
          <select id="model-directory"></select>

          <label for="model-file">Select Model</label>
          <select id="model-file"></select>

          <div id="model-path" class="model-path">No model selected.</div>

          <label for="model_selector">Model Selector (Auto from model selection)</label>
          <input id="model_selector" name="model_selector" value="fq_orders" />

          <label for="trino_schema">Trino Schema</label>
          <input id="trino_schema" name="trino_schema" value="fq_dbt" />

          <label for="dbt_table_name">dbt Table Name</label>
          <input id="dbt_table_name" name="dbt_table_name" value="fq_orders_as_select" />

          <label for="ingest_openmetadata">OpenMetadata Ingest</label>
          <select id="ingest_openmetadata" name="ingest_openmetadata">
            <option value="true" selected>true</option>
            <option value="false">false</option>
          </select>
        </form>

        <label for="cli-command">API Command</label>
        <textarea id="cli-command" rows="8" readonly></textarea>
      </section>

      <section class="panel">
        <div class="toolbar">
          <h2 style="margin:0">Execution History</h2>
          <small id="active-indicator" class="meta">No active run</small>
        </div>
        <div id="history"></div>
      </section>
    </div>

    <section class="panel console-panel">
      <h2 style="margin-bottom:8px">Run Details Console</h2>
      <div class="console-toolbar">
        <div>
          <label for="run-select" style="margin-top:0">Run Selection</label>
          <select id="run-select"></select>
        </div>
        <div>
          <label for="step-select" style="margin-top:0">Details View</label>
          <select id="step-select"></select>
        </div>
      </div>
      <p id="console-title" class="console-title">Select a run to view logs.</p>
      <pre id="console-output">Waiting for run selection...</pre>
    </section>
  </div>

  <script>
    let selectedRunId = null;
    let activeRunId = null;
    let selectedStepKey = "overview";
    let currentRun = null;
    let activeProjectId = "";
    let modelCatalog = [];
    let projectCatalog = [];

    const form = document.getElementById("run-form");
    const playRunButton = document.getElementById("play-run");
    const stopRunButton = document.getElementById("stop-run");
    const loadProjectButton = document.getElementById("load-project");
    const refreshAllButton = document.getElementById("refresh-all");
    const historyEl = document.getElementById("history");
    const activeIndicator = document.getElementById("active-indicator");
    const cliCommand = document.getElementById("cli-command");
    const projectSelect = document.getElementById("project-select");
    const projectPath = document.getElementById("project-path");
    const projectFolderInput = document.getElementById("project-folder-input");
    const modelDirectory = document.getElementById("model-directory");
    const modelFile = document.getElementById("model-file");
    const modelPath = document.getElementById("model-path");
    const modelSelector = document.getElementById("model_selector");
    const runSelect = document.getElementById("run-select");
    const stepSelect = document.getElementById("step-select");
    const consoleTitle = document.getElementById("console-title");
    const consoleOutput = document.getElementById("console-output");

    const statusBadge = (status) => {
      const safe = (status || "unknown").toLowerCase();
      return `<span class="badge ${safe}">${safe}</span>`;
    };

    const buildPayload = () => ({
      project_id: activeProjectId || null,
      model_selector: document.getElementById("model_selector").value.trim(),
      trino_schema: document.getElementById("trino_schema").value.trim(),
      dbt_table_name: document.getElementById("dbt_table_name").value.trim(),
      ingest_openmetadata: document.getElementById("ingest_openmetadata").value === "true"
    });

    const refreshCli = () => {
      const payload = buildPayload();
      cliCommand.value =
`curl -s -X POST http://<service-host>:8080/api/runs \\
  -H 'Content-Type: application/json' \\
  -d '${JSON.stringify(payload, null, 2)}'`;
    };

    const renderProjectOptions = (projects) => {
      projectCatalog = projects || [];
      const options = ["<option value=''>Bundled Project (/app/dbt)</option>"];
      projectCatalog.forEach((project) => {
        options.push(`<option value="${project.projectId}">${project.projectName} (${project.projectId})</option>`);
      });
      projectSelect.innerHTML = options.join("");
      if (activeProjectId && projectCatalog.some((project) => project.projectId === activeProjectId)) {
        projectSelect.value = activeProjectId;
      } else {
        activeProjectId = "";
        projectSelect.value = "";
      }
      if (!activeProjectId) {
        projectPath.textContent = "Using bundled project: /app/dbt";
      } else {
        const selected = projectCatalog.find((project) => project.projectId === activeProjectId);
        projectPath.textContent = selected
          ? `Using uploaded project: ${selected.projectDir}`
          : "Using uploaded project";
      }
    };

    const fetchProjects = async () => {
      const response = await fetch("/api/projects");
      const body = await response.json();
      renderProjectOptions(body.projects || []);
    };

    const renderDirectoryOptions = (directories) => {
      const current = modelDirectory.value || "";
      modelDirectory.innerHTML = directories.map((directory) => {
        const label = directory ? directory : "(root)";
        return `<option value="${directory}">${label}</option>`;
      }).join("");
      modelDirectory.value = directories.includes(current) ? current : "";
    };

    const updateModelSelectorFromChoice = () => {
      const selectedFile = modelFile.value;
      const selectedModel = modelCatalog.find((model) => model.file === selectedFile);
      if (!selectedModel) {
        modelPath.textContent = "No model selected.";
        return;
      }
      modelSelector.value = selectedModel.pathSelector;
      modelPath.textContent = `Selected model: ${selectedModel.file} | selector: ${selectedModel.pathSelector}`;
      refreshCli();
    };

    const renderModelOptions = () => {
      const currentDir = modelDirectory.value || "";
      const models = modelCatalog.filter((model) => (model.directory || "") === currentDir);
      const previous = modelFile.value;
      modelFile.innerHTML = models.map((model) => `<option value="${model.file}">${model.file}</option>`).join("");
      if (!models.length) {
        modelPath.textContent = "No SQL models found in this directory.";
        modelSelector.value = "";
        refreshCli();
        return;
      }
      const nextValue = models.some((model) => model.file === previous) ? previous : models[0].file;
      modelFile.value = nextValue;
      updateModelSelectorFromChoice();
    };

    const fetchModels = async () => {
      const suffix = activeProjectId ? `?project_id=${encodeURIComponent(activeProjectId)}` : "";
      const response = await fetch(`/api/models${suffix}`);
      const body = await response.json();
      if (response.status !== 200) {
        modelCatalog = [];
        modelDirectory.innerHTML = "<option value=''>Error</option>";
        modelFile.innerHTML = "<option value=''>Error</option>";
        modelPath.textContent = body.error || "Failed to load dbt model list.";
        return;
      }
      modelCatalog = body.models || [];
      renderDirectoryOptions(body.directories || [""]);
      renderModelOptions();
    };

    const renderHistory = (runs) => {
      if (!runs.length) {
        historyEl.innerHTML = "<div class='meta'>No executions yet.</div>";
        return;
      }
      historyEl.innerHTML = runs.map((run) => {
        const activeClass = run.runId === selectedRunId ? "active" : "";
        return `
          <div class="history-row ${activeClass}" data-run-id="${run.runId}">
            <div class="row-head">
              <strong>${run.runId}</strong>
              ${statusBadge(run.status)}
            </div>
            <div class="meta">model=${run.modelSelector} table=${run.dbtTableName}</div>
            <div class="meta">steps=${run.stepCount} duration=${run.durationSeconds ?? "-"}s</div>
          </div>
        `;
      }).join("");
    };

    const populateRunSelect = (runs) => {
      const previous = runSelect.value;
      runSelect.innerHTML = runs.map((run) => {
        return `<option value="${run.runId}">${run.runId} | ${run.status} | ${run.modelSelector}</option>`;
      }).join("");
      if (!runs.length) {
        selectedRunId = null;
        activeRunId = null;
        currentRun = null;
        runSelect.innerHTML = "<option value=''>No runs</option>";
        stepSelect.innerHTML = "<option value='overview'>overview</option>";
        consoleTitle.textContent = "Select a run to view logs.";
        consoleOutput.textContent = "Waiting for run selection...";
        return;
      }
      if (selectedRunId && runs.some((run) => run.runId === selectedRunId)) {
        runSelect.value = selectedRunId;
      } else if (previous && runs.some((run) => run.runId === previous)) {
        runSelect.value = previous;
        selectedRunId = previous;
      } else {
        runSelect.value = runs[0].runId;
        selectedRunId = runs[0].runId;
      }
    };

    const renderStepOptions = (run) => {
      const options = [
        { value: "overview", label: "overview" },
        { value: "raw_json", label: "raw_json" }
      ];
      (run.steps || []).forEach((step, idx) => {
        options.push({ value: `step:${idx}`, label: `step ${idx + 1}: ${step.name}` });
      });
      stepSelect.innerHTML = options.map((option) => `<option value="${option.value}">${option.label}</option>`).join("");
      if (!options.some((option) => option.value === selectedStepKey)) {
        selectedStepKey = "overview";
      }
      stepSelect.value = selectedStepKey;
    };

    const renderConsole = () => {
      if (!currentRun) {
        consoleTitle.textContent = "Select a run to view logs.";
        consoleOutput.textContent = "Waiting for run selection...";
        return;
      }
      const run = currentRun;
      const steps = run.steps || [];
      if (selectedStepKey === "raw_json") {
        consoleTitle.textContent = `Run ${run.runId} | raw_json`;
        consoleOutput.textContent = JSON.stringify(run, null, 2);
        return;
      }
      if (selectedStepKey === "overview") {
        const lines = [];
        lines.push(`runId: ${run.runId}`);
        lines.push(`status: ${run.status}`);
        lines.push(`modelSelector: ${run.modelSelector}`);
        lines.push(`table: ${run.dbtTableName}`);
        lines.push(`startedAt: ${run.startedAt || "-"}`);
        lines.push(`finishedAt: ${run.finishedAt || "-"}`);
        lines.push(`durationSeconds: ${run.durationSeconds ?? "-"}`);
        lines.push("");
        lines.push("steps:");
        steps.forEach((step, idx) => {
          lines.push(`${idx + 1}. ${step.name} | status=${step.status} | duration=${step.durationSeconds ?? "-"}s`);
        });
        if (run.error) {
          lines.push("");
          lines.push("error:");
          lines.push(String(run.error));
        }
        consoleTitle.textContent = `Run ${run.runId} | overview`;
        consoleOutput.textContent = lines.join("\\n");
        return;
      }
      const stepIndex = Number(selectedStepKey.split(":")[1]);
      const step = steps[stepIndex];
      if (!step) {
        consoleTitle.textContent = `Run ${run.runId} | step missing`;
        consoleOutput.textContent = "Step not found.";
        return;
      }
      const lines = [];
      lines.push(`runId: ${run.runId}`);
      lines.push(`step: ${step.name}`);
      lines.push(`status: ${step.status}`);
      lines.push(`durationSeconds: ${step.durationSeconds ?? "-"}`);
      lines.push(`startedAt: ${step.startedAt || "-"}`);
      lines.push(`finishedAt: ${step.finishedAt || "-"}`);
      if (step.command) {
        lines.push(`command: ${step.command}`);
      }
      if (step.details) {
        lines.push("");
        lines.push("details:");
        lines.push(JSON.stringify(step.details, null, 2));
      }
      if (step.stdoutTail) {
        lines.push("");
        lines.push("stdout:");
        lines.push(step.stdoutTail);
      }
      if (step.stderrTail) {
        lines.push("");
        lines.push("stderr:");
        lines.push(step.stderrTail);
      }
      consoleTitle.textContent = `Run ${run.runId} | ${step.name}`;
      consoleOutput.textContent = lines.join("\\n");
    };

    const fetchRunDetails = async (runId) => {
      if (!runId) {
        currentRun = null;
        renderConsole();
        return;
      }
      const response = await fetch(`/api/runs/${runId}`);
      if (response.status !== 200) {
        currentRun = null;
        consoleTitle.textContent = `Run ${runId} not found`;
        consoleOutput.textContent = "Run not found.";
        return;
      }
      currentRun = await response.json();
      renderStepOptions(currentRun);
      renderConsole();
    };

    const fetchHistory = async () => {
      const response = await fetch("/api/runs?limit=40");
      const body = await response.json();
      const runs = body.runs || [];
      renderHistory(runs);
      populateRunSelect(runs);
      const active = runs.find((run) => run.status === "running");
      activeRunId = active ? active.runId : null;
      activeIndicator.textContent = active ? `Active run: ${active.runId}` : "No active run";
      if (selectedRunId) {
        await fetchRunDetails(selectedRunId);
      }
    };

    const uploadLocalProject = async () => {
      const files = projectFolderInput.files;
      if (!files || !files.length) {
        alert("Choose a local folder first.");
        return;
      }

      loadProjectButton.disabled = true;
      loadProjectButton.textContent = "Loading...";
      try {
        const payload = new FormData();
        Array.from(files).forEach((file) => {
          const rel = file.webkitRelativePath || file.name;
          payload.append("files", file, rel);
        });

        const response = await fetch("/api/projects/upload", {
          method: "POST",
          body: payload,
        });
        const body = await response.json();
        if (response.status !== 200) {
          alert(body.error || "Project upload failed.");
          return;
        }

        activeProjectId = body.project.projectId;
        projectFolderInput.value = "";
        await fetchProjects();
        projectSelect.value = activeProjectId;
        await fetchModels();
        refreshCli();
      } finally {
        loadProjectButton.disabled = false;
        loadProjectButton.textContent = "Load";
      }
    };

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      playRunButton.disabled = true;
      playRunButton.textContent = "Playing...";
      try {
        const payload = buildPayload();
        const response = await fetch("/api/runs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const body = await response.json();
        if (response.status === 202) {
          selectedRunId = body.runId;
          selectedStepKey = "overview";
        } else {
          alert(body.message || body.error || "Failed to start run.");
        }
        await fetchHistory();
      } finally {
        playRunButton.disabled = false;
        playRunButton.textContent = "Play";
      }
    });

    historyEl.addEventListener("click", async (event) => {
      const target = event.target.closest("[data-run-id]");
      if (!target) {
        return;
      }
      selectedRunId = target.dataset.runId;
      selectedStepKey = "overview";
      runSelect.value = selectedRunId;
      await fetchRunDetails(selectedRunId);
      await fetchHistory();
    });

    runSelect.addEventListener("change", async () => {
      selectedRunId = runSelect.value;
      selectedStepKey = "overview";
      await fetchRunDetails(selectedRunId);
      await fetchHistory();
    });

    stepSelect.addEventListener("change", () => {
      selectedStepKey = stepSelect.value;
      renderConsole();
    });

    projectSelect.addEventListener("change", async () => {
      activeProjectId = projectSelect.value || "";
      await fetchModels();
      refreshCli();
    });

    modelDirectory.addEventListener("change", () => {
      renderModelOptions();
      refreshCli();
    });

    modelFile.addEventListener("change", () => {
      updateModelSelectorFromChoice();
      refreshCli();
    });

    loadProjectButton.addEventListener("click", async () => {
      await uploadLocalProject();
    });

    refreshAllButton.addEventListener("click", async () => {
      await fetchProjects();
      await fetchModels();
      await fetchHistory();
      refreshCli();
    });

    stopRunButton.addEventListener("click", async () => {
      const targetRunId = activeRunId || selectedRunId;
      if (!targetRunId) {
        alert("No run selected to stop.");
        return;
      }
      await fetch(`/api/runs/${targetRunId}/stop`, { method: "POST" });
      await fetchHistory();
      if (selectedRunId) {
        await fetchRunDetails(selectedRunId);
      }
    });

    document.querySelectorAll("input, select").forEach((element) => {
      element.addEventListener("input", refreshCli);
      element.addEventListener("change", refreshCli);
    });

    const bootstrap = async () => {
      refreshCli();
      await fetchProjects();
      await fetchModels();
      await fetchHistory();
      setInterval(fetchHistory, 3000);
    };

    bootstrap();
  </script>
</body>
</html>
"""
