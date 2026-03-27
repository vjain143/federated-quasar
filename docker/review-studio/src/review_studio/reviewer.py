from __future__ import annotations

from pathlib import Path

from review_studio.diff_parser import parse_unified_diff
from review_studio.languages import detect_language
from review_studio.models import Finding, ReviewReport
from review_studio.rules import review_content, should_scan_path


def review_code(
    *,
    content: str,
    persona: str,
    path: str | None = None,
    language: str | None = None,
) -> ReviewReport:
    resolved_language = language or detect_language(path, content)
    findings = review_content(
        content=content,
        language=resolved_language,
        persona=persona,
        file_path=path,
    )
    summary = build_summary(scope=path or "stdin", findings=findings)
    return ReviewReport(persona=persona, scope=path or "stdin", summary=summary, findings=findings)


def review_repo(
    *,
    repo_path: str,
    persona: str,
    max_files: int = 200,
) -> ReviewReport:
    findings: list[Finding] = []
    repo_root = Path(repo_path)
    scanned = 0

    for path in sorted(repo_root.rglob("*")):
        if scanned >= max_files:
            break
        if not path.is_file() or not should_scan_path(path.relative_to(repo_root)):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        language = detect_language(str(path), content)
        if language not in {"java", "python", "kubernetes"}:
            continue
        scanned += 1
        findings.extend(
            review_content(
                content=content,
                language=language,
                persona=persona,
                file_path=str(path),
            )
        )

    summary = build_summary(scope=repo_path, findings=findings, scanned_files=scanned)
    return ReviewReport(persona=persona, scope=repo_path, summary=summary, findings=findings)


def review_diff(
    *,
    diff_text: str,
    persona: str,
) -> ReviewReport:
    findings: list[Finding] = []
    files = parse_unified_diff(diff_text)
    for diff_file in files:
        snippet = "\n".join(line.content for line in diff_file.added_lines)
        language = detect_language(diff_file.path, snippet)
        if language not in {"java", "python", "kubernetes"}:
            continue
        for diff_line in diff_file.added_lines:
            line_findings = review_content(
                content=diff_line.content,
                language=language,
                persona=persona,
                file_path=diff_file.path,
                line_offset=diff_line.line_number,
            )
            findings.extend(line_findings)

    summary = build_summary(scope="diff", findings=findings, scanned_files=len(files))
    return ReviewReport(persona=persona, scope="diff", summary=summary, findings=findings)


def build_summary(scope: str, findings: list[Finding], scanned_files: int | None = None) -> str:
    if not findings:
        if scanned_files is not None:
            return f"No obvious review findings detected in {scanned_files} scanned files for {scope}."
        return f"No obvious review findings detected for {scope}."

    critical = sum(1 for finding in findings if finding.severity == "critical")
    high = sum(1 for finding in findings if finding.severity == "high")
    medium = sum(1 for finding in findings if finding.severity == "medium")
    low = sum(1 for finding in findings if finding.severity == "low")
    detail = []
    if scanned_files is not None:
        detail.append(f"scanned {scanned_files} files")
    detail.append(f"{critical} critical")
    detail.append(f"{high} high")
    detail.append(f"{medium} medium")
    detail.append(f"{low} low")
    return f"Review summary for {scope}: " + ", ".join(detail) + "."
