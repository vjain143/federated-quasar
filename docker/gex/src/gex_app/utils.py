from __future__ import annotations

import os
from datetime import datetime, timezone


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def tail(text: str, max_lines: int = 120, max_chars: int = 20000) -> str:
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    clipped = "\n".join(lines)
    if len(clipped) > max_chars:
        clipped = clipped[-max_chars:]
    return clipped
