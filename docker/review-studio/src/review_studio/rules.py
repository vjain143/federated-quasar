from __future__ import annotations

from pathlib import Path
import re

from review_studio.models import Finding
from review_studio.personas import render_comment


SKIP_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "node_modules",
    "target",
    "dist",
    "build",
    "__pycache__",
}


def generic_findings(
    *,
    content: str,
    language: str,
    persona: str,
    file_path: str | None,
    line_offset: int = 1,
) -> list[Finding]:
    findings: list[Finding] = []
    lines = content.splitlines()

    if len(lines) > 700:
        findings.append(
            make_finding(
                persona=persona,
                severity="medium",
                title="Oversized file",
                why_it_matters=(
                    "the file has grown large enough that review depth, ownership clarity, "
                    "and safe change velocity will degrade"
                ),
                recommendation="Split the file by responsibility before more behavior accretes here.",
                category="maintainability",
                language=language,
                file_path=file_path,
                line=1,
            )
        )

    for index, line in enumerate(lines, start=line_offset):
        upper = line.upper()
        if "TODO" in upper or "FIXME" in upper or "HACK" in upper:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="low",
                    title="Deferred production concern left in code",
                    why_it_matters=(
                        "the current change leaves an acknowledged gap in a path that may "
                        "later be treated as complete"
                    ),
                    recommendation="Resolve the issue or convert it into a tracked backlog item outside the code path.",
                    category="maintainability",
                    language=language,
                    file_path=file_path,
                    line=index,
                )
            )
        if re.search(r"(api[_-]?key|secret|password)\s*[:=]\s*[\"'][^\"']+[\"']", line, re.IGNORECASE):
            findings.append(
                make_finding(
                    persona=persona,
                    severity="critical",
                    title="Hard-coded credential pattern",
                    why_it_matters=(
                        "embedded credentials create immediate secret sprawl and incident-response exposure"
                    ),
                    recommendation="Move the secret to a secure runtime source and reference it indirectly.",
                    category="security",
                    language=language,
                    file_path=file_path,
                    line=index,
                )
            )

    return findings


def java_findings(
    *,
    content: str,
    persona: str,
    file_path: str | None,
    line_offset: int = 1,
) -> list[Finding]:
    findings = generic_findings(
        content=content,
        language="java",
        persona=persona,
        file_path=file_path,
        line_offset=line_offset,
    )
    lines = content.splitlines()
    for index, line in enumerate(lines, start=line_offset):
        stripped = line.strip()
        if re.search(r"catch\s*\(\s*(Exception|Throwable)\b", line):
            findings.append(
                make_finding(
                    persona=persona,
                    severity="high",
                    title="Broad exception boundary",
                    why_it_matters=(
                        "catching the top-level exception type collapses failure semantics and "
                        "makes recovery logic and observability less trustworthy"
                    ),
                    recommendation="Catch the expected exception types and preserve domain context in the error path.",
                    category="correctness",
                    language="java",
                    file_path=file_path,
                    line=index,
                )
            )
        if "System.out." in line or "System.err." in line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="medium",
                    title="Console logging in application path",
                    why_it_matters=(
                        "console prints bypass structured logging strategy and age badly in enterprise operations"
                    ),
                    recommendation="Use the project logging facade with actionable context fields.",
                    category="operations",
                    language="java",
                    file_path=file_path,
                    line=index,
                )
            )
        if "new Thread(" in line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="high",
                    title="Ad hoc thread creation",
                    why_it_matters=(
                        "raw thread management introduces lifecycle, shutdown, and observability risks"
                    ),
                    recommendation="Use a managed executor with explicit shutdown and ownership.",
                    category="concurrency",
                    language="java",
                    file_path=file_path,
                    line=index,
                )
            )
        if "==" in line and '"' in line and ".equals(" not in line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="medium",
                    title="Suspicious reference equality check",
                    why_it_matters=(
                        "string comparison by reference is a classic correctness defect that slips through review"
                    ),
                    recommendation="Use `.equals(...)` or `Objects.equals(...)` for value comparison.",
                    category="correctness",
                    language="java",
                    file_path=file_path,
                    line=index,
                )
            )
        if stripped.startswith("public static") and any(token in line for token in ("List<", "Map<", "Set<")) and "final" not in line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="medium",
                    title="Public mutable static state",
                    why_it_matters=(
                        "shared mutable state creates hidden coupling and unpredictable cross-request behavior"
                    ),
                    recommendation="Hide the state behind an immutable view or controlled accessor.",
                    category="architecture",
                    language="java",
                    file_path=file_path,
                    line=index,
                )
            )
    return findings


def python_findings(
    *,
    content: str,
    persona: str,
    file_path: str | None,
    line_offset: int = 1,
) -> list[Finding]:
    findings = generic_findings(
        content=content,
        language="python",
        persona=persona,
        file_path=file_path,
        line_offset=line_offset,
    )
    lines = content.splitlines()
    for index, line in enumerate(lines, start=line_offset):
        stripped = line.strip()
        if stripped == "except:":
            findings.append(
                make_finding(
                    persona=persona,
                    severity="high",
                    title="Bare exception handler",
                    why_it_matters=(
                        "the code will swallow interruption and termination signals together with genuine failures"
                    ),
                    recommendation="Catch the specific exception classes you expect and preserve failure intent.",
                    category="correctness",
                    language="python",
                    file_path=file_path,
                    line=index,
                )
            )
        if re.search(r"except\s+Exception\s*:\s*pass\b", stripped):
            findings.append(
                make_finding(
                    persona=persona,
                    severity="high",
                    title="Exception swallowed without signal",
                    why_it_matters=(
                        "production failures will disappear silently and force operators to debug symptoms instead of causes"
                    ),
                    recommendation="Log structured context or return an explicit failure signal.",
                    category="operations",
                    language="python",
                    file_path=file_path,
                    line=index,
                )
            )
        if re.search(r"def\s+\w+\([^)]*=\s*\[\]", line) or re.search(r"def\s+\w+\([^)]*=\s*\{\}", line):
            findings.append(
                make_finding(
                    persona=persona,
                    severity="high",
                    title="Mutable default argument",
                    why_it_matters=(
                        "default mutable state persists across calls and causes hard-to-reproduce behavior"
                    ),
                    recommendation="Default to `None` and allocate the collection inside the function body.",
                    category="correctness",
                    language="python",
                    file_path=file_path,
                    line=index,
                )
            )
        if "yaml.load(" in line and "SafeLoader" not in line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="high",
                    title="Unsafe YAML loading",
                    why_it_matters=(
                        "generic YAML deserialization can execute or instantiate unsafe content"
                    ),
                    recommendation="Use `yaml.safe_load(...)` unless there is a strong controlled-data justification.",
                    category="security",
                    language="python",
                    file_path=file_path,
                    line=index,
                )
            )
        if "shell=True" in line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="critical",
                    title="Shell execution with interpolation risk",
                    why_it_matters=(
                        "shell invocation expands the attack surface and is hard to harden if any input becomes user-controlled"
                    ),
                    recommendation="Use argument lists with `shell=False` and validate inputs explicitly.",
                    category="security",
                    language="python",
                    file_path=file_path,
                    line=index,
                )
            )
        if re.search(r"requests\.(get|post|put|delete)\(", line) and "timeout=" not in line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="medium",
                    title="Network call without timeout",
                    why_it_matters=(
                        "unbounded waits couple application health to remote latency and failure behavior"
                    ),
                    recommendation="Set explicit connect and read timeouts that match the service contract.",
                    category="reliability",
                    language="python",
                    file_path=file_path,
                    line=index,
                )
            )
        if stripped.startswith("print("):
            findings.append(
                make_finding(
                    persona=persona,
                    severity="low",
                    title="Print statement in runtime path",
                    why_it_matters=(
                        "prints do not scale into searchable operational telemetry"
                    ),
                    recommendation="Route the event through a structured logger instead.",
                    category="operations",
                    language="python",
                    file_path=file_path,
                    line=index,
                )
            )
    return findings


def kubernetes_findings(
    *,
    content: str,
    persona: str,
    file_path: str | None,
    line_offset: int = 1,
) -> list[Finding]:
    findings = generic_findings(
        content=content,
        language="kubernetes",
        persona=persona,
        file_path=file_path,
        line_offset=line_offset,
    )
    lowered = content.lower()
    lines = content.splitlines()

    def first_line_with(pattern: str) -> int:
        for idx, line in enumerate(lines, start=line_offset):
            if pattern in line.lower():
                return idx
        return 1

    if "kind: deployment" in lowered or "kind: statefulset" in lowered or "kind: daemonset" in lowered:
        if "resources:" not in lowered:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="high",
                    title="Workload without resource requests or limits",
                    why_it_matters=(
                        "the scheduler and runtime cannot make predictable placement or eviction decisions"
                    ),
                    recommendation="Define CPU and memory requests and limits for each container.",
                    category="operations",
                    language="kubernetes",
                    file_path=file_path,
                    line=first_line_with("kind:"),
                )
            )
        if "readinessprobe:" not in lowered:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="medium",
                    title="Missing readiness probe",
                    why_it_matters=(
                        "traffic may reach a pod before the application is actually ready to serve"
                    ),
                    recommendation="Add a readiness probe aligned with the app startup contract.",
                    category="reliability",
                    language="kubernetes",
                    file_path=file_path,
                    line=first_line_with("containers:"),
                )
            )
        if "livenessprobe:" not in lowered:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="medium",
                    title="Missing liveness probe",
                    why_it_matters=(
                        "the platform has no signal to recover a wedged process automatically"
                    ),
                    recommendation="Add a liveness probe with thresholds that match recovery expectations.",
                    category="reliability",
                    language="kubernetes",
                    file_path=file_path,
                    line=first_line_with("containers:"),
                )
            )
        if "securitycontext:" not in lowered:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="medium",
                    title="Missing security context",
                    why_it_matters=(
                        "container hardening defaults remain ambiguous and harder to govern consistently"
                    ),
                    recommendation="Define pod or container security context, including non-root intent where possible.",
                    category="security",
                    language="kubernetes",
                    file_path=file_path,
                    line=first_line_with("containers:"),
                )
            )

    for index, line in enumerate(lines, start=line_offset):
        lowered_line = line.lower()
        if "image:" in lowered_line and ":latest" in lowered_line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="high",
                    title="Unpinned container image tag",
                    why_it_matters=(
                        "rollouts become non-reproducible and incident rollback becomes materially harder"
                    ),
                    recommendation="Pin to an immutable version or digest.",
                    category="release",
                    language="kubernetes",
                    file_path=file_path,
                    line=index,
                )
            )
        if "privileged: true" in lowered_line:
            findings.append(
                make_finding(
                    persona=persona,
                    severity="critical",
                    title="Privileged container",
                    why_it_matters=(
                        "this materially expands the blast radius of a container escape or workload compromise"
                    ),
                    recommendation="Avoid privileged mode or document and isolate the exception rigorously.",
                    category="security",
                    language="kubernetes",
                    file_path=file_path,
                    line=index,
                )
            )

    return findings


def review_content(
    *,
    content: str,
    language: str,
    persona: str,
    file_path: str | None,
    line_offset: int = 1,
) -> list[Finding]:
    if language == "java":
        return java_findings(content=content, persona=persona, file_path=file_path, line_offset=line_offset)
    if language == "python":
        return python_findings(content=content, persona=persona, file_path=file_path, line_offset=line_offset)
    if language == "kubernetes":
        return kubernetes_findings(content=content, persona=persona, file_path=file_path, line_offset=line_offset)
    return generic_findings(content=content, language=language, persona=persona, file_path=file_path, line_offset=line_offset)


def should_scan_path(path: Path) -> bool:
    return not any(part in SKIP_DIRS for part in path.parts)


def make_finding(
    *,
    persona: str,
    severity: str,
    title: str,
    why_it_matters: str,
    recommendation: str,
    category: str,
    language: str,
    file_path: str | None,
    line: int | None,
) -> Finding:
    return Finding(
        severity=severity,
        title=title,
        comment=render_comment(
            persona=persona,
            severity=severity,
            title=title,
            why_it_matters=why_it_matters,
            recommendation=recommendation,
        ),
        suggestion=recommendation,
        category=category,
        language=language,
        file_path=file_path,
        line=line,
    )
