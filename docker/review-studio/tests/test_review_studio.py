from __future__ import annotations

import json
import unittest

from review_studio.bitbucket import render_bitbucket_payload
from review_studio.diff_parser import parse_unified_diff
from review_studio.reviewer import review_code, review_diff


class ReviewStudioTests(unittest.TestCase):
    def test_python_mutable_default_is_flagged(self) -> None:
        report = review_code(
            content="def build_cache(items=[]):\n    return items\n",
            persona="engineer",
            path="sample.py",
        )
        self.assertTrue(any(finding.title == "Mutable default argument" for finding in report.findings))

    def test_java_broad_exception_is_flagged(self) -> None:
        report = review_code(
            content="class Demo { void run() { try {} catch (Exception e) {} } }\n",
            persona="architect",
            path="Demo.java",
        )
        self.assertTrue(any(finding.title == "Broad exception boundary" for finding in report.findings))

    def test_kubernetes_missing_controls_is_flagged(self) -> None:
        manifest = (
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "metadata:\n"
            "  name: demo\n"
            "spec:\n"
            "  template:\n"
            "    spec:\n"
            "      containers:\n"
            "        - name: app\n"
            "          image: demo:latest\n"
        )
        report = review_code(content=manifest, persona="architect", path="deploy.yaml")
        titles = {finding.title for finding in report.findings}
        self.assertIn("Workload without resource requests or limits", titles)
        self.assertIn("Unpinned container image tag", titles)

    def test_diff_parser_tracks_added_line_numbers(self) -> None:
        diff = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1,1 +1,3 @@\n"
            " import os\n"
            "+def load(values=[]):\n"
            "+    return values\n"
        )
        parsed = parse_unified_diff(diff)
        self.assertEqual(parsed[0].added_lines[0].line_number, 2)

    def test_bitbucket_payload_renders_comments(self) -> None:
        diff = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+def load(values=[]):\n"
            "+    return values\n"
        )
        report = review_diff(diff_text=diff, persona="engineer")
        payload = json.loads(render_bitbucket_payload(report))
        self.assertIn("summary", payload)
        self.assertTrue(payload["comments"])


if __name__ == "__main__":
    unittest.main()
