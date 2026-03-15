from __future__ import annotations

from pathlib import Path


_INDEX_HTML_PATH = Path(__file__).resolve().with_name("index.html")
INDEX_HTML = _INDEX_HTML_PATH.read_text(encoding="utf-8")
