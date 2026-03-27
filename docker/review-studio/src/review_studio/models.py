from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass(slots=True)
class Finding:
    severity: str
    title: str
    comment: str
    category: str
    language: str
    file_path: str | None = None
    line: int | None = None
    suggestion: str | None = None

    def sort_key(self) -> tuple[int, str, int]:
        return (
            SEVERITY_ORDER.get(self.severity, 99),
            self.file_path or "",
            self.line or 0,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReviewReport:
    persona: str
    scope: str
    summary: str
    findings: list[Finding] = field(default_factory=list)

    def ordered_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda finding: finding.sort_key())

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona": self.persona,
            "scope": self.scope,
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.ordered_findings()],
        }
