from __future__ import annotations

from pathlib import Path


JAVA_EXTENSIONS = {".java"}
PYTHON_EXTENSIONS = {".py"}
KUBERNETES_EXTENSIONS = {".yaml", ".yml"}


def detect_language(path: str | None, content: str) -> str:
    if path:
        suffix = Path(path).suffix.lower()
        if suffix in JAVA_EXTENSIONS:
            return "java"
        if suffix in PYTHON_EXTENSIONS:
            return "python"
        if suffix in KUBERNETES_EXTENSIONS and looks_like_kubernetes(content):
            return "kubernetes"
        if suffix in KUBERNETES_EXTENSIONS:
            return "yaml"

    stripped = content.strip()
    if "apiVersion:" in content and "kind:" in content:
        return "kubernetes"
    if "public class " in content or "package " in content:
        return "java"
    if stripped.startswith("def ") or stripped.startswith("import ") or "except:" in content:
        return "python"
    if ":" in content:
        return "yaml"
    return "text"


def looks_like_kubernetes(content: str) -> bool:
    lowered = content.lower()
    return "apiversion:" in lowered and "kind:" in lowered
