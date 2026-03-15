from __future__ import annotations

from pathlib import Path
from typing import Any

from gex_app.utils import env


def discover_models(project_dir: Path | None = None) -> dict[str, Any]:
    if project_dir is None:
        project_dir = Path(env("DBT_PROJECT_DIR", "/app/dbt"))

    models_root = project_dir / "models"
    if not models_root.exists():
        raise RuntimeError(f"dbt models directory not found: {models_root}")

    models: list[dict[str, str]] = []
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
                "defaultTableName": model_path.stem,
            }
        )

    directories = sorted({model["directory"] for model in models if model["directory"]})
    return {
        "projectDir": str(project_dir),
        "modelsRoot": str(models_root),
        "directories": [""] + directories,
        "models": models,
    }


def resolve_uploaded_project_dir(upload_root: Path) -> Path:
    if (upload_root / "dbt_project.yml").exists():
        return upload_root

    child_dirs = [path for path in upload_root.iterdir() if path.is_dir()]
    for child in child_dirs:
        if (child / "dbt_project.yml").exists():
            return child

    raise RuntimeError("Uploaded folder does not contain dbt_project.yml")
