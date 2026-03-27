from __future__ import annotations

import argparse
from pathlib import Path
import sys

from review_studio.bitbucket import publish_to_bitbucket_cloud, render_bitbucket_payload
from review_studio.formatters import render_json, render_markdown
from review_studio.reviewer import review_code, review_diff, review_repo


VALID_PERSONAS = {"architect", "engineer", "test"}
VALID_FORMATS = {"markdown", "json", "bitbucket"}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not getattr(args, "command", None):
        parser.print_help()
        return 1

    if hasattr(args, "persona") and args.persona not in VALID_PERSONAS:
        parser.error(f"persona must be one of {sorted(VALID_PERSONAS)}")
    if hasattr(args, "format") and args.format not in VALID_FORMATS:
        parser.error(f"format must be one of {sorted(VALID_FORMATS)}")

    if args.command == "review-code":
        content = read_code_input(args)
        report = review_code(
            content=content,
            path=args.file,
            language=args.language,
            persona=args.persona,
        )
        return emit_report(report, args.format, args.output)

    if args.command == "review-repo":
        report = review_repo(
            repo_path=args.repo,
            persona=args.persona,
            max_files=args.max_files,
        )
        return emit_report(report, args.format, args.output)

    if args.command == "review-diff":
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")
        report = review_diff(diff_text=diff_text, persona=args.persona)
        return emit_report(report, args.format, args.output)

    if args.command == "publish-bitbucket":
        findings_file = Path(args.findings_file).read_text(encoding="utf-8")
        report = _report_from_payload(findings_file)
        publish_to_bitbucket_cloud(
            report=report,
            workspace=args.workspace,
            repo_slug=args.repo_slug,
            pull_request=args.pull_request,
            api_base_url=args.api_base_url,
        )
        print("Published review comments to Bitbucket Cloud.")
        return 0

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="review-studio")
    subparsers = parser.add_subparsers(dest="command")

    review_code_parser = subparsers.add_parser("review-code", help="Review a file or pasted code")
    review_code_parser.add_argument("--file", help="Path to a file to review")
    review_code_parser.add_argument("--stdin", action="store_true", help="Read code from stdin")
    review_code_parser.add_argument("--language", help="Force language: java, python, kubernetes")
    review_code_parser.add_argument("--persona", default="engineer")
    review_code_parser.add_argument("--format", default="markdown")
    review_code_parser.add_argument("--output", help="Write results to a file")

    review_repo_parser = subparsers.add_parser("review-repo", help="Review a local repository")
    review_repo_parser.add_argument("--repo", required=True, help="Path to a local repository")
    review_repo_parser.add_argument("--persona", default="architect")
    review_repo_parser.add_argument("--max-files", default=200, type=int)
    review_repo_parser.add_argument("--format", default="markdown")
    review_repo_parser.add_argument("--output", help="Write results to a file")

    review_diff_parser = subparsers.add_parser("review-diff", help="Review a unified diff file")
    review_diff_parser.add_argument("--diff-file", required=True)
    review_diff_parser.add_argument("--persona", default="test")
    review_diff_parser.add_argument("--format", default="markdown")
    review_diff_parser.add_argument("--output", help="Write results to a file")

    publish_parser = subparsers.add_parser("publish-bitbucket", help="Publish findings to Bitbucket Cloud")
    publish_parser.add_argument(
        "--findings-file",
        required=True,
        help="File produced by --format json or --format bitbucket",
    )
    publish_parser.add_argument("--workspace", required=True)
    publish_parser.add_argument("--repo-slug", required=True)
    publish_parser.add_argument("--pull-request", required=True, type=int)
    publish_parser.add_argument("--api-base-url", default="https://api.bitbucket.org/2.0")

    return parser


def read_code_input(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.stdin:
        return sys.stdin.read()
    raise SystemExit("Provide --file or --stdin.")


def emit_report(report, output_format: str, output_path: str | None) -> int:
    if output_format == "json":
        rendered = render_json(report)
    elif output_format == "bitbucket":
        rendered = render_bitbucket_payload(report)
    else:
        rendered = render_markdown(report)

    if output_path:
        Path(output_path).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


def _report_from_payload(raw_payload: str):
    import json
    from review_studio.models import Finding, ReviewReport

    payload = json.loads(raw_payload)
    if "findings" in payload:
        findings = [Finding(**finding) for finding in payload["findings"]]
        return ReviewReport(
            persona=payload["persona"],
            scope=payload["scope"],
            summary=payload["summary"],
            findings=findings,
        )

    findings = []
    for item in payload.get("comments", []):
        inline = item.get("inline", {})
        findings.append(
            Finding(
                severity=item.get("severity", "medium"),
                title=item.get("title", "Review finding"),
                comment=item["content"]["raw"],
                category="review",
                language="unknown",
                file_path=inline.get("path"),
                line=inline.get("to"),
            )
        )
    return ReviewReport(
        persona="engineer",
        scope="bitbucket-payload",
        summary=payload.get("summary", "Review findings"),
        findings=findings,
    )


if __name__ == "__main__":
    raise SystemExit(main())
