from __future__ import annotations

import copy
import os
import shutil
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Any

from .utils import now_iso

run_lock = threading.Lock()
history_lock = threading.Lock()
history_limit = int(os.getenv("RUN_HISTORY_LIMIT", "200"))
runs: dict[str, dict[str, Any]] = {}
run_order: deque[str] = deque()

project_lock = threading.Lock()
project_limit = int(os.getenv("PROJECT_UPLOAD_LIMIT", "20"))
project_base_dir = Path(os.getenv("PROJECT_UPLOAD_ROOT", "/tmp/gex-projects"))
projects: dict[str, dict[str, Any]] = {}
project_order: deque[str] = deque()

active_lock = threading.Lock()
active_run_id: str | None = None
active_proc: subprocess.Popen[str] | None = None
cancelled_runs: set[str] = set()


def store_run(run: dict[str, Any]) -> None:
    run_id = run["runId"]
    with history_lock:
        runs[run_id] = copy.deepcopy(run)
        try:
            run_order.remove(run_id)
        except ValueError:
            pass
        run_order.appendleft(run_id)
        while len(run_order) > history_limit:
            stale = run_order.pop()
            runs.pop(stale, None)


def get_run(run_id: str) -> dict[str, Any] | None:
    with history_lock:
        value = runs.get(run_id)
        if value is None:
            return None
        return copy.deepcopy(value)


def list_runs(limit: int) -> list[dict[str, Any]]:
    with history_lock:
        run_ids = list(run_order)[:limit]
        return [copy.deepcopy(runs[run_id]) for run_id in run_ids if run_id in runs]


def store_project(project: dict[str, Any]) -> None:
    project_id = project["projectId"]
    with project_lock:
        projects[project_id] = copy.deepcopy(project)
        try:
            project_order.remove(project_id)
        except ValueError:
            pass
        project_order.appendleft(project_id)
        while len(project_order) > project_limit:
            stale_id = project_order.pop()
            stale_project = projects.pop(stale_id, None)
            if stale_project:
                stale_dir = Path(stale_project["projectDir"])
                shutil.rmtree(stale_dir, ignore_errors=True)


def get_project(project_id: str) -> dict[str, Any] | None:
    with project_lock:
        value = projects.get(project_id)
        if value is None:
            return None
        return copy.deepcopy(value)


def list_projects() -> list[dict[str, Any]]:
    with project_lock:
        return [copy.deepcopy(projects[project_id]) for project_id in project_order if project_id in projects]


def set_active_process(run_id: str, proc: subprocess.Popen[str]) -> None:
    global active_proc, active_run_id
    with active_lock:
        active_run_id = run_id
        active_proc = proc


def clear_active_process(run_id: str, proc: subprocess.Popen[str]) -> None:
    global active_proc, active_run_id
    with active_lock:
        if active_run_id == run_id and active_proc is proc:
            active_proc = None
            active_run_id = None


def is_cancelled(run_id: str) -> bool:
    with active_lock:
        return run_id in cancelled_runs


def request_cancel(run_id: str) -> bool:
    proc: subprocess.Popen[str] | None
    with active_lock:
        cancelled_runs.add(run_id)
        proc = active_proc if active_run_id == run_id else None
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
        except OSError:
            pass
        return True
    return False


def clear_cancel(run_id: str) -> None:
    with active_lock:
        cancelled_runs.discard(run_id)


def create_run_record(request: Any, run_id: str) -> dict[str, Any]:
    return {
        "status": "running",
        "runId": run_id,
        "startedAt": now_iso(),
        "finishedAt": None,
        "durationSeconds": None,
        "request": request.model_dump(),
        "projectId": request.project_id,
        "modelSelector": request.model_selector,
        "trinoSchema": request.trino_schema,
        "dbtTableName": request.dbt_table_name,
        "steps": [],
    }
