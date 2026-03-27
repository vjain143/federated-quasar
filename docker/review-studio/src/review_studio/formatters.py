from __future__ import annotations

import json

from review_studio.models import ReviewReport


def render_markdown(report: ReviewReport) -> str:
    lines = [
        f"# Review Studio Report",
        "",
        f"- Persona: `{report.persona}`",
        f"- Scope: `{report.scope}`",
        f"- Summary: {report.summary}",
        "",
    ]

    findings = report.ordered_findings()
    if not findings:
        lines.append("No findings.")
        return "\n".join(lines) + "\n"

    for index, finding in enumerate(findings, start=1):
        location = ""
        if finding.file_path:
            location = finding.file_path
            if finding.line is not None:
                location = f"{location}:{finding.line}"
        lines.extend(
            [
                f"## {index}. [{finding.severity.upper()}] {finding.title}",
                "",
                f"- Category: `{finding.category}`",
                f"- Language: `{finding.language}`",
                f"- Location: `{location or 'general'}`",
                f"- Comment: {finding.comment}",
            ]
        )
        if finding.suggestion:
            lines.append(f"- Recommendation: {finding.suggestion}")
        lines.append("")

    return "\n".join(lines)


def render_json(report: ReviewReport) -> str:
    return json.dumps(report.to_dict(), indent=2) + "\n"
