from __future__ import annotations

import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from review_studio.models import ReviewReport


def render_bitbucket_payload(report: ReviewReport) -> str:
    payload = {
        "summary": report.summary,
        "comments": [],
    }
    for finding in report.ordered_findings():
        comment = {
            "content": {"raw": finding.comment},
            "severity": finding.severity,
            "title": finding.title,
        }
        if finding.file_path and finding.line is not None:
            comment["inline"] = {"path": finding.file_path, "to": finding.line}
        payload["comments"].append(comment)
    return json.dumps(payload, indent=2) + "\n"


def publish_to_bitbucket_cloud(
    *,
    report: ReviewReport,
    workspace: str,
    repo_slug: str,
    pull_request: int,
    api_base_url: str = "https://api.bitbucket.org/2.0",
) -> list[str]:
    username = os.environ.get("BITBUCKET_USERNAME")
    password = os.environ.get("BITBUCKET_APP_PASSWORD")
    if not username or not password:
        raise ValueError("BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD must be set.")

    auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    endpoint = f"{api_base_url}/repositories/{workspace}/{repo_slug}/pullrequests/{pull_request}/comments"
    responses: list[str] = []

    summary_body = {
        "content": {"raw": report.summary},
    }
    responses.append(_post_comment(endpoint, summary_body, auth))

    for finding in report.ordered_findings():
        body = {"content": {"raw": finding.comment}}
        if finding.file_path and finding.line is not None:
            body["inline"] = {"path": finding.file_path, "to": finding.line}
        responses.append(_post_comment(endpoint, body, auth))

    return responses


def _post_comment(endpoint: str, body: dict[str, object], auth: str) -> str:
    request = Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return payload
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Bitbucket request failed with {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Bitbucket request failed: {error}") from error
