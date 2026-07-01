"""Run the V2 audit across a directory of example contest workspaces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPTS = REPO_ROOT / "skills" / "_references" / "scripts"
sys.path.insert(0, str(AUDIT_SCRIPTS))

import audit_v2_run  # noqa: E402


def is_contest_workspace(path: Path) -> bool:
    has_intake = (path / "PROBLEM_BRIEF.md").is_file() or (path / "DATA_AUDIT.md").is_file()
    return has_intake and (path / "reports").is_dir() and (
        (path / "results" / "RESULTS_MANIFEST.json").is_file()
        or (path / "reports" / "VERIFY_REPORT.md").is_file()
        or (path / "paper").is_dir()
    )


def first_issue_codes(result: dict[str, Any], limit: int) -> str:
    codes = [str(issue.get("code", "")) for issue in result.get("issues", []) if issue.get("code")]
    return ", ".join(codes[:limit])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(REPO_ROOT / "examples" / "2022C"), help="Directory containing example workspaces")
    parser.add_argument("--nature-enabled", choices=["auto", "yes", "no"], default="auto")
    parser.add_argument("--json-out", help="Optional path for the full JSON result")
    parser.add_argument("--markdown-out", help="Optional path for a Markdown summary table")
    parser.add_argument("--issue-limit", type=int, default=5)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspaces = [item for item in sorted(root.iterdir()) if item.is_dir() and is_contest_workspace(item)]
    results = [audit_v2_run.audit_workspace(workspace, args.nature_enabled) for workspace in workspaces]

    lines = [
        f"# Benchmark Audit: {root}",
        "",
        "| Workspace | Status | Worst | Figures | Pages | Claimed PASS | Issues | First issue codes |",
        "| --- | --- | --- | ---: | ---: | --- | ---: | --- |",
    ]
    for result in results:
        summary = result.get("summary", {})
        workspace = Path(str(result.get("workspace", ""))).name
        lines.append(
            "| {workspace} | {status} | {worst} | {figures} | {pages} | {claimed} | {issues} | {codes} |".format(
                workspace=workspace,
                status=result.get("status", "UNKNOWN"),
                worst=result.get("worst_severity", "NONE"),
                figures=summary.get("figures", 0),
                pages=summary.get("paper_pages") or "",
                claimed="yes" if summary.get("pass_claimed") else "no",
                issues=summary.get("issue_count", 0),
                codes=first_issue_codes(result, args.issue_limit),
            )
        )
    markdown = "\n".join(lines) + "\n"
    print(markdown)

    if args.markdown_out:
        Path(args.markdown_out).write_text(markdown, encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0 if all(result.get("status") == "PASS" for result in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
