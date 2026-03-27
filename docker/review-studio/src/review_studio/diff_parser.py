from __future__ import annotations

from dataclasses import dataclass, field
import re


HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(slots=True)
class DiffLine:
    line_number: int
    content: str


@dataclass(slots=True)
class DiffFile:
    path: str
    added_lines: list[DiffLine] = field(default_factory=list)


def parse_unified_diff(diff_text: str) -> list[DiffFile]:
    files: list[DiffFile] = []
    current_file: DiffFile | None = None
    next_line_number = 0

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ b/"):
            current_file = DiffFile(path=raw_line[6:])
            files.append(current_file)
            continue

        hunk_match = HUNK_RE.match(raw_line)
        if hunk_match:
            next_line_number = int(hunk_match.group(1))
            continue

        if current_file is None:
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            current_file.added_lines.append(
                DiffLine(line_number=next_line_number, content=raw_line[1:])
            )
            next_line_number += 1
            continue

        if raw_line.startswith("-") and not raw_line.startswith("---"):
            continue

        next_line_number += 1

    return [diff_file for diff_file in files if diff_file.added_lines]
