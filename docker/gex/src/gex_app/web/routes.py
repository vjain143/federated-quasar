from __future__ import annotations

import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from gex_app import state
from gex_app.schemas import RunRequest
from gex_app.services.pipeline import execute_with_lock, run_async_worker, to_summary
from gex_app.services.projects import discover_models, resolve_uploaded_project_dir
from gex_app.utils import env, now_iso
from gex_app.web.ui import INDEX_HTML

router = APIRouter()


def _busy_response() -> JSONResponse:
    busy = next((run for run in state.list_runs(limit=1) if run.get("status") == "running"), None)
    return JSONResponse(
        status_code=409,
        content={
            "status": "busy",
            "message": "A run is already in progress",
            "activeRunId": busy.get("runId") if busy else None,
        },
    )


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return INDEX_HTML


@router.get("/health")
def health() -> dict[str, Any]:
    active = None
    for run in state.list_runs(limit=1):
        if run.get("status") == "running":
            active = run.get("runId")
    return {"status": "ok", "activeRunId": active}


@router.get("/api/runs")
def list_runs(limit: int = Query(default=25, ge=1, le=200)) -> dict[str, Any]:
    runs = state.list_runs(limit)
    return {"runs": [to_summary(run) for run in runs]}


@router.get("/api/models")
def list_models(project_id: str | None = Query(default=None)) -> Any:
    try:
        if project_id:
            project = state.get_project(project_id)
            if project is None:
                return JSONResponse(status_code=404, content={"error": "project not found"})
            model_data = discover_models(Path(project["projectDir"]))
            model_data["projectId"] = project_id
            return model_data

        model_data = discover_models()
        model_data["projectId"] = None
        return model_data
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@router.get("/api/projects")
def list_projects() -> dict[str, Any]:
    projects = state.list_projects()
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


@router.post("/api/projects/upload")
async def upload_project(files: list[UploadFile] = File(...)) -> Any:
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files uploaded"})

    project_id = uuid.uuid4().hex[:12]
    upload_root = state.project_base_dir / project_id
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

        project_dir = resolve_uploaded_project_dir(upload_root)
        profiles_dir = project_dir if (project_dir / "profiles.yml").exists() else Path(env("DBT_PROFILES_DIR", "/app/dbt"))
        model_data = discover_models(project_dir=project_dir)
        project_name = project_dir.name

        project = {
            "projectId": project_id,
            "projectName": project_name,
            "projectDir": str(project_dir),
            "profilesDir": str(profiles_dir),
            "uploadedAt": now_iso(),
        }
        state.store_project(project)

        return {
            "status": "uploaded",
            "project": project,
            "models": model_data.get("models", []),
            "directories": model_data.get("directories", []),
            "projectId": project_id,
        }
    except Exception as exc:
        shutil.rmtree(upload_root, ignore_errors=True)
        return JSONResponse(status_code=500, content={"error": str(exc)})


@router.get("/api/runs/{run_id}")
def get_run(run_id: str) -> Any:
    run = state.get_run(run_id)
    if run is None:
        return JSONResponse(status_code=404, content={"error": "run not found"})
    return run


@router.post("/api/runs")
def start_run(request: RunRequest) -> JSONResponse:
    if not state.run_lock.acquire(blocking=False):
        return _busy_response()

    run_id = uuid.uuid4().hex[:12]
    started_epoch = time.time()
    run = state.create_run_record(request=request, run_id=run_id)
    state.store_run(run)

    thread = threading.Thread(
        target=run_async_worker,
        args=(run, request, started_epoch),
        daemon=True,
        name=f"run-{run_id}",
    )
    thread.start()
    return JSONResponse(status_code=202, content={"status": "accepted", "runId": run_id})


@router.post("/api/runs/{run_id}/stop")
def stop_run(run_id: str) -> Any:
    run = state.get_run(run_id)
    if run is None:
        return JSONResponse(status_code=404, content={"error": "run not found"})
    accepted = state.request_cancel(run_id)
    return {"status": "stop_requested", "runId": run_id, "accepted": accepted}


@router.post("/run")
def run_sync(request: RunRequest) -> Any:
    if not state.run_lock.acquire(blocking=False):
        return _busy_response()

    run_id = uuid.uuid4().hex[:12]
    started_epoch = time.time()
    run = state.create_run_record(request=request, run_id=run_id)
    state.store_run(run)

    try:
        result = execute_with_lock(run=run, request=request, started_epoch=started_epoch)
        return result
    except Exception:
        failed = state.get_run(run_id) or run
        return JSONResponse(status_code=500, content=failed)
