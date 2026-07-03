"""Compare multiple provider/model pairs on one LangGraph planning benchmark."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.real_provider_benchmark as benchmark  # noqa: E402

DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "real_benchmarks"


def parse_provider_spec(spec: str) -> tuple[str, str | None]:
    text = spec.strip()
    if not text:
        raise ValueError("Provider spec cannot be empty.")
    if ":" not in text:
        return text, None
    provider, model = text.split(":", 1)
    provider = provider.strip()
    model = model.strip()
    if not provider:
        raise ValueError(f"Invalid provider spec: {spec}")
    return provider, model or None


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "provider"


def score_summary(summary: dict[str, Any]) -> dict[str, Any]:
    deductions: list[str] = []
    total = 0

    if summary.get("status") == "PLAN_READY" and summary.get("json_valid"):
        total += 20
    else:
        deductions.append("schema_or_status")

    planned_steps = int(summary.get("planned_step_count") or 0)
    total += min(planned_steps, 5) * 3
    if planned_steps < 5:
        deductions.append("planned_steps")

    rag_queries = int(summary.get("rag_query_count") or 0)
    total += min(rag_queries, 3) * 5
    if rag_queries < 3:
        deductions.append("rag_queries")

    risk_count = int(summary.get("risk_count") or 0)
    total += min(risk_count, 3) * 5
    if risk_count < 3:
        deductions.append("risk_register")

    if int(summary.get("human_gate_count") or 0) > 0:
        total += 15
    else:
        deductions.append("human_gate")

    if summary.get("do_not_do"):
        total += 10
    else:
        deductions.append("safety_boundaries")

    if summary.get("source_verify_hash_unchanged") is True:
        total += 5
    else:
        deductions.append("source_integrity")

    if not summary.get("secret_hits"):
        total += 5
    else:
        deductions.append("secret_safety")

    return {"total": total, "deductions": deductions}


def _result_row(summary: dict[str, Any], json_path: Path, markdown_path: Path) -> dict[str, Any]:
    score = score_summary(summary)
    return {
        "provider": summary.get("provider"),
        "model": summary.get("model"),
        "status": summary.get("status"),
        "provider_error": summary.get("provider_error"),
        "score_total": score["total"],
        "score_deductions": score["deductions"],
        "planned_step_count": summary.get("planned_step_count", 0),
        "rag_query_count": summary.get("rag_query_count", 0),
        "risk_count": summary.get("risk_count", 0),
        "human_gate_count": summary.get("human_gate_count", 0),
        "source_verify_hash_unchanged": summary.get("source_verify_hash_unchanged"),
        "secret_hit_count": len(summary.get("secret_hits", [])),
        "phase_plan_summary": summary.get("phase_plan_summary"),
        "single_json_report": str(json_path.resolve()),
        "single_markdown_report": str(markdown_path.resolve()),
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# LangGraph Real Provider Comparison",
        "",
        f"- Workspace: `{report.get('workspace')}`",
        f"- Mode: `{report.get('mode')}`",
        f"- Phase: `{report.get('phase')}`",
        f"- Providers: {len(report.get('results', []))}",
        "",
        "## Ranking",
        "",
        "| Rank | Provider | Model | Status | Score | Steps | RAG | Risks | Human Gate | Secret Hits |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(report.get("results", []), start=1):
        lines.append(
            f"| {index} | {row.get('provider')} | {row.get('model') or 'default'} | "
            f"{row.get('status')} | {row.get('score_total')} | "
            f"{row.get('planned_step_count', 0)} | {row.get('rag_query_count', 0)} | "
            f"{row.get('risk_count', 0)} | {row.get('human_gate_count', 0)} | "
            f"{row.get('secret_hit_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Scores are deterministic smoke-test scores, not final paper-quality grades.",
            "- A high score only means the Phase 1 plan is structurally complete and safe.",
            "- This comparison does not run controlled_apply, experiments, paper drafting, or final verification.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reports(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    safe_report = benchmark.sanitize_json_value(benchmark.redact_secrets(report))
    json_text = json.dumps(safe_report, ensure_ascii=False, indent=2, default=str)
    json.loads(json_text)
    json_path.write_text(json_text + "\n", encoding="utf-8")
    json.loads(json_path.read_text(encoding="utf-8"))
    markdown_path.write_text(markdown_report(safe_report), encoding="utf-8")


def run_comparison(
    *,
    workspace: Path,
    specs: list[str],
    mode: str,
    phase: int,
    output_dir: Path,
    output_json: Path | None = None,
    output_markdown: Path | None = None,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    if not specs:
        raise ValueError("At least one provider spec is required.")
    output_dir = output_dir.resolve()
    single_dir = output_dir / "single"
    single_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for spec in specs:
        provider, model = parse_provider_spec(spec)
        stem = f"{_safe_stem(provider)}_{_safe_stem(model or 'default')}_phase{phase}_{_safe_stem(workspace.name)}"
        single_json = single_dir / f"{stem}.json"
        single_md = single_dir / f"{stem}.md"
        summary = benchmark.run_benchmark(
            workspace=workspace,
            mode=mode,
            phase=phase,
            provider=provider,
            model=model,
            output_json=single_json,
            output_markdown=single_md,
            run_name=f"compare-{provider}-{model or 'default'}-phase{phase}-{workspace.name}",
        )
        rows.append(_result_row(summary, single_json, single_md))

    rows.sort(key=lambda item: (-int(item.get("score_total") or 0), str(item.get("provider") or "")))
    report = {
        "kind": "real_provider_comparison",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace": str(workspace),
        "mode": mode,
        "phase": phase,
        "provider_specs": specs,
        "results": rows,
        "json_valid": True,
        "scope_note": (
            "Phase planning comparison only. This does not run controlled_apply, experiments, "
            "paper drafting, revision integration, or final verification."
        ),
    }

    if output_json is None:
        output_json = output_dir / f"LANGGRAPH_PROVIDER_COMPARISON_PHASE{phase}_{_safe_stem(workspace.name)}.json"
    if output_markdown is None:
        output_markdown = output_dir / f"LANGGRAPH_PROVIDER_COMPARISON_PHASE{phase}_{_safe_stem(workspace.name)}.md"
    write_reports(report, output_json, output_markdown)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare real provider PhasePlan quality on one workspace")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--mode", default="llm_plan")
    parser.add_argument("--phase", type=int, default=1)
    parser.add_argument(
        "--provider-model",
        action="append",
        dest="provider_models",
        help="Provider/model spec like deepseek:deepseek-chat. Repeat for multiple models.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    args = parser.parse_args()

    specs = args.provider_models or ["deepseek:deepseek-chat"]
    try:
        report = run_comparison(
            workspace=Path(args.workspace),
            specs=specs,
            mode=args.mode,
            phase=args.phase,
            output_dir=Path(args.output_dir),
            output_json=Path(args.json_out) if args.json_out else None,
            output_markdown=Path(args.markdown_out) if args.markdown_out else None,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
