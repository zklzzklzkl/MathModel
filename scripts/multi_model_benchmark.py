"""Multi-model comparison benchmark runner.

Runs the same workspace fixtures across multiple model backends and generates
a comparison report. Usage:

    python scripts/multi_model_benchmark.py --root examples/2022C --providers deepseek --model deepseek-chat
    python scripts/multi_model_benchmark.py --root examples/2022C --providers none,dry-run --output compare.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import Settings  # noqa: E402
from app.langgraph_runner import run_langgraph_phase  # noqa: E402
from langgraph_benchmark import (  # type: ignore[import]
    build_phase_row,
    is_benchmark_workspace,
    phase_emoji,
)


PROVIDER_LABELS = {
    "none": "Dry-Run (Plan Only)",
    "dry-run": "Dry-Run (Plan Only)",
    "deepseek": "DeepSeek",
    "openai-compatible": "OpenAI Compatible",
    "claude": "Anthropic Claude (via OpenAI Compatible)",
    "qwen": "Qwen (via OpenAI Compatible)",
}


def run_one_provider(
    settings: Settings,
    workspace: Path,
    provider: str,
    model: str | None,
    mode: str,
) -> dict[str, Any]:
    try:
        result = run_langgraph_phase(
            settings=settings,
            source_workspace=workspace,
            phase=0,
            mode=mode,
            provider=provider,
            model=model,
            copy_workspace=True,
            run_name=f"mm-bench-{workspace.name}-{provider}",
            temperature=0.2,
            max_tokens=4096,
        )
    except Exception as exc:
        return {
            "workspace_name": workspace.name,
            "provider": provider,
            "contest_status": f"ERROR: {exc}",
            "completed_phases": [],
            "paused_at": "error",
            "human_gate_approved": False,
            "phase_rows": [],
            "error": str(exc),
        }
    return {
        "workspace_name": workspace.name,
        "provider": provider,
        "contest_status": result.get("contest_status"),
        "completed_phases": list(result.get("completed_phases", [])),
        "paused_at": result.get("paused_at"),
        "human_gate_approved": bool((result.get("human_gate") or {}).get("approved", False)),
        "final_audit_worst": (result.get("final_audit") or {}).get("worst_severity", "NONE"),
        "phase_rows": [build_phase_row(result, p) for p in range(0, 7)],
        "error": None,
    }


def comparison_markdown(
    results: list[dict[str, Any]],
    root: str,
    providers: list[str],
    mode: str,
) -> str:
    workspaces = sorted({r["workspace_name"] for r in results})
    lines = [
        f"# Multi-Model Benchmark Comparison",
        "",
        f"**Root**: `{root}`",
        f"**Mode**: `{mode}`",
        f"**Providers**: {', '.join(PROVIDER_LABELS.get(p, p) for p in providers)}",
        f"**Workspaces**: {len(workspaces)}",
        f"**Total runs**: {len(results)}",
        "",
        "## Summary",
        "",
    ]

    # Per-workspace summary table
    lines.append("| Workspace | Provider | Status | Phases | Paused At | Audit |")
    lines.append("| --- | --- | --- | ---: | --- | --- |")
    for r in results:
        lines.append(
            f"| {r['workspace_name']} | {PROVIDER_LABELS.get(r['provider'], r['provider'])} "
            f"| {r['contest_status']} | {len(r['completed_phases'])}/7 "
            f"| {r.get('paused_at') or '—'} "
            f"| {r.get('final_audit_worst', '—')} |"
        )

    # Cross-provider comparison per workspace
    for ws_name in workspaces:
        ws_results = [r for r in results if r["workspace_name"] == ws_name]
        lines.append("")
        lines.append(f"## {ws_name}")
        lines.append("")

        for r in ws_results:
            label = PROVIDER_LABELS.get(r["provider"], r["provider"])
            lines.append(f"### {label}")
            lines.append("")
            lines.append(f"- Contest status: `{r['contest_status']}`")
            lines.append(f"- Completed phases: {r['completed_phases']}")
            lines.append(f"- Paused at: {r.get('paused_at') or 'none'}")
            lines.append(f"- Human gate approved: {r.get('human_gate_approved', False)}")
            lines.append(f"- Final audit worst: {r.get('final_audit_worst', 'NONE')}")
            if r.get("error"):
                lines.append(f"- Error: {r['error']}")
            lines.append("")
            lines.append("| Phase | Status | Sandbox | Paper | Revision |")
            lines.append("| ---: | --- | --- | --- | --- |")
            for row in r.get("phase_rows", []):
                if not row["hit"] and row["phase"] > max(r.get("completed_phases", [0])):
                    lines.append(f"| {row['phase']} | — | — | — | — |")
                else:
                    lines.append(
                        f"| {row['phase']} | {phase_emoji(row['status'])} {row['status']} "
                        f"| {row.get('sandbox_status') or '—'} "
                        f"| {row.get('paper_sandbox_status') or '—'} "
                        f"| {row.get('revision_sandbox_status') or '—'} |"
                    )
            lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-model LangGraph benchmark comparison")
    parser.add_argument("--root", required=True, help="Directory containing benchmark workspace fixtures")
    parser.add_argument("--mode", default="contest_graph_v3", help="LangGraph mode")
    parser.add_argument("--providers", default="none", help="Comma-separated provider names (none, dry-run, deepseek, openai-compatible)")
    parser.add_argument("--model", default=None, help="Model name override for all providers")
    parser.add_argument("--output", help="Output path for comparison Markdown report")
    parser.add_argument("--json-out", help="Output path for JSON results")
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

    providers = [p.strip() for p in args.providers.split(",")]

    settings = Settings(
        mathmodel_root=REPO_ROOT,
        workspace_root=root,
        examples_root=REPO_ROOT / "examples",
        python_executable=sys.executable,
    )

    all_results: list[dict[str, Any]] = []
    for ws in workspaces:
        for provider in providers:
            model = args.model
            if provider in ("deepseek",) and not model:
                model = "deepseek-chat"
            print(f"Running {args.mode} on {ws.name} with {provider} (model={model or 'auto'}) ...", file=sys.stderr)
            result = run_one_provider(settings, ws, provider, model, args.mode)
            all_results.append(result)
            short_status = result.get("contest_status") or result.get("error") or "?"
            print(f"  -> [{provider}] {short_status}", file=sys.stderr)

    md_text = comparison_markdown(all_results, str(root), providers, args.mode)
    json_text = json.dumps(all_results, ensure_ascii=False, indent=2, default=str)

    if args.json_out:
        Path(args.json_out).write_text(json_text + "\n", encoding="utf-8")
        print(f"JSON written to {args.json_out}", file=sys.stderr)
    if args.output:
        Path(args.output).write_text(md_text, encoding="utf-8")
        print(f"Markdown written to {args.output}", file=sys.stderr)

    print(json_text)
    print(md_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
