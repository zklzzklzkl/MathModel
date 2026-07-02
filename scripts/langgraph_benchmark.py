"""Run LangGraph contest_graph_v3 across a directory of benchmark workspace fixtures.

Usage:
    python scripts/langgraph_benchmark.py --root tests/langgraph_benchmark_fixtures
    python scripts/langgraph_benchmark.py --root <dir> --mode contest_graph_v3 --provider none
    python scripts/langgraph_benchmark.py --root <dir> --json-out bench.json --markdown-out bench.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings  # noqa: E402
from app.langgraph_runner import run_langgraph_phase  # noqa: E402


def is_benchmark_workspace(path: Path) -> bool:
    return (path / "PROBLEM_BRIEF.md").is_file() or (path / "WORKFLOW_STATE.md").is_file()


def phase_emoji(status: str | None) -> str:
    if not status:
        return "?"
    status_str = str(status).upper()
    if "SUCCEEDED" in status_str or "PASS" in status_str or "READY" in status_str:
        return "PASS"
    if "FAILED" in status_str or "REJECTED" in status_str or "ROLLED_BACK" in status_str or "BLOCKER" in status_str:
        return "FAIL"
    if "PAUSE" in status_str or "WAITING" in status_str or "NO_REVISION" in status_str:
        return "HOLD"
    if "AUDIT" in status_str or "REVIEW" in status_str or "PLAN_ONLY" in status_str:
        return "INFO"
    return "?"


def build_phase_row(result: dict[str, Any], phase: int) -> dict[str, Any]:
    matches = [p for p in result.get("phase_results", []) if p.get("phase") == phase]
    if not matches:
        return {"phase": phase, "hit": False, "status": "NOT_EXECUTED", "strategy": "none"}
    item = matches[0]
    status = item.get("status") or item.get("sandbox_status") or item.get("paper_sandbox_status") or item.get("revision_sandbox_status") or "UNKNOWN"
    return {
        "phase": phase,
        "hit": True,
        "status": status,
        "strategy": item.get("strategy", "none"),
        "files_written": item.get("files_written") or item.get("paper_files_written") or item.get("revision_files_written") or [],
        "sandbox_status": item.get("sandbox_status"),
        "paper_sandbox_status": item.get("paper_sandbox_status"),
        "revision_sandbox_status": item.get("revision_sandbox_status"),
        "manifest_created_empty": item.get("manifest_created_empty", False),
        "post_audit_worst": (item.get("post_audit") or {}).get("worst_severity", "NONE"),
    }


def run_one(settings: Settings, workspace: Path, mode: str, provider: str) -> dict[str, Any]:
    try:
        result = run_langgraph_phase(
            settings=settings,
            source_workspace=workspace,
            phase=0,
            mode=mode,
            provider=provider,
            model=None,
            copy_workspace=True,
            run_name=f"benchmark-{workspace.name}",
            temperature=0.2,
            max_tokens=4096,
        )
    except Exception as exc:
        return {
            "workspace": str(workspace),
            "workspace_name": workspace.name,
            "error": str(exc),
            "phase_rows": [],
            "contest_status": "BENCHMARK_ERROR",
            "completed_phases": [],
            "paused_at": "error",
            "human_gate_required": False,
            "human_gate_approved": False,
        }
    return {
        "workspace": str(result.get("source_workspace", workspace)),
        "run_workspace": str(result.get("run_workspace", "")),
        "workspace_name": workspace.name,
        "contest_status": result.get("contest_status"),
        "completed_phases": list(result.get("completed_phases", [])),
        "paused_at": result.get("paused_at"),
        "human_gate_required": bool(result.get("human_gate_required", False)),
        "human_gate_approved": bool((result.get("human_gate") or {}).get("approved", False)),
        "final_audit_worst": (result.get("final_audit") or {}).get("worst_severity", "NONE"),
        "phase_rows": [build_phase_row(result, p) for p in range(0, 7)],
        "error": None,
    }


def markdown_report(results: list[dict[str, Any]], root: str) -> str:
    lines = [
        f"# LangGraph Benchmark Report",
        "",
        f"**Root**: `{root}`",
        f"**Workspaces**: {len(results)}",
        "",
        "## Summary",
        "",
    ]
    pass_count = sum(1 for r in results if r.get("contest_status") in ("CONTEST_GRAPH_REVIEW_READY", "READY_FOR_FINAL_AUDIT"))
    fail_count = sum(1 for r in results if "FAILED" in str(r.get("contest_status", "")) or "ERROR" in str(r.get("contest_status", "")))
    hold_count = len(results) - pass_count - fail_count
    lines.append(f"- PASS: {pass_count}  |  HOLD: {hold_count}  |  FAIL: {fail_count}")
    lines.append("")

    for result in results:
        name = result["workspace_name"]
        status = result.get("contest_status") or result.get("error") or "UNKNOWN"
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- Contest status: `{status}`")
        lines.append(f"- Completed phases: {result.get('completed_phases', [])}")
        lines.append(f"- Paused at: {result.get('paused_at') or 'none'}")
        lines.append(f"- Human gate required: {result.get('human_gate_required', False)}")
        lines.append(f"- Human gate approved: {result.get('human_gate_approved', False)}")
        lines.append(f"- Final audit worst: {result.get('final_audit_worst', 'NONE')}")
        if result.get("error"):
            lines.append(f"- Error: {result['error']}")
        lines.append("")
        lines.append("| Phase | Status | Strategy | Sandbox | Paper | Revision | Files | Audit |")
        lines.append("| ---: | --- | --- | --- | --- | --- | --- | --- |")
        for row in result.get("phase_rows", []):
            if not row["hit"] and row["phase"] > max(result.get("completed_phases", [0])):
                lines.append(f"| {row['phase']} | — | — | — | — | — | — | — |")
            else:
                lines.append(
                    f"| {row['phase']} | {phase_emoji(row['status'])} {row['status']} | {row['strategy']} | "
                    f"{row.get('sandbox_status') or '—'} | {row.get('paper_sandbox_status') or '—'} | "
                    f"{row.get('revision_sandbox_status') or '—'} | "
                    f"{len(row.get('files_written', []))} files | "
                    f"{row.get('post_audit_worst', '—')} |"
                )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch LangGraph contest_graph_v3 benchmark runner")
    parser.add_argument("--root", required=True, help="Directory containing benchmark workspace fixtures")
    parser.add_argument("--mode", default="contest_graph_v3", help="LangGraph mode (default: contest_graph_v3)")
    parser.add_argument("--provider", default="none", help="LLM provider (default: none)")
    parser.add_argument("--json-out", help="Output path for JSON report")
    parser.add_argument("--markdown-out", help="Output path for Markdown report")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: root directory does not exist: {root}", file=sys.stderr)
        return 1

    workspaces = sorted(
        [item for item in root.iterdir() if item.is_dir() and is_benchmark_workspace(item)]
    )
    if not workspaces:
        print(f"Error: no benchmark workspaces found in {root}", file=sys.stderr)
        return 1

    settings = Settings(
        mathmodel_root=REPO_ROOT,
        workspace_root=root,
        examples_root=REPO_ROOT / "examples",
        python_executable=sys.executable,
    )

    results: list[dict[str, Any]] = []
    for ws in workspaces:
        print(f"Running {args.mode} on {ws.name} ...", file=sys.stderr)
        result = run_one(settings, ws, args.mode, args.provider)
        results.append(result)
        short_status = result.get("contest_status") or result.get("error") or "?"
        print(f"  -> {short_status}", file=sys.stderr)

    json_text = json.dumps(results, ensure_ascii=False, indent=2, default=str)
    md_text = markdown_report(results, str(root))

    if args.json_out:
        Path(args.json_out).write_text(json_text + "\n", encoding="utf-8")
        print(f"JSON report written to {args.json_out}", file=sys.stderr)
    if args.markdown_out:
        Path(args.markdown_out).write_text(md_text, encoding="utf-8")
        print(f"Markdown report written to {args.markdown_out}", file=sys.stderr)

    print(json_text)
    print(md_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
