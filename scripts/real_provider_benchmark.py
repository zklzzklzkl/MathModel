"""Run a single real-provider LangGraph benchmark and write safe reports.

This script is intentionally narrower than ``scripts/langgraph_benchmark.py``:
it targets one real workspace and one provider-backed mode, then writes a
machine-readable JSON report and a compact Markdown report. It never records
API keys or full environment data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings  # noqa: E402
from app.langgraph_runner import run_langgraph_phase  # noqa: E402

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
REAL_PROVIDER_MODES = {"llm_plan"}
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "real_benchmarks"


def _escape_control(match: re.Match[str]) -> str:
    return f"\\u{ord(match.group(0)):04x}"


def sanitize_json_value(value: Any) -> Any:
    """Return a JSON-safe copy with non-whitespace control chars made visible."""
    if isinstance(value, str):
        return CONTROL_CHARS.sub(_escape_control, value)
    if isinstance(value, dict):
        return {str(k): sanitize_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _known_secrets() -> list[str]:
    secrets: list[str] = []
    for name in ("MATHMODEL_LLM_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        value = os.environ.get(name)
        if value and len(value) >= 8:
            secrets.append(value)
    return secrets


def redact_secrets(value: Any, secrets: list[str] | None = None) -> Any:
    secrets = secrets if secrets is not None else _known_secrets()
    if isinstance(value, str):
        text = value
        for secret in secrets:
            text = text.replace(secret, "[REDACTED_SECRET]")
        return text
    if isinstance(value, dict):
        return {str(k): redact_secrets(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item, secrets) for item in value]
    if isinstance(value, tuple):
        return [redact_secrets(item, secrets) for item in value]
    return value


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _audit_result(audit: Any) -> dict[str, Any]:
    if not isinstance(audit, dict):
        return {"status": None, "worst_severity": None, "issue_count": 0}
    result = audit.get("result") if isinstance(audit.get("result"), dict) else audit
    issues = result.get("issues", []) if isinstance(result, dict) else []
    return {
        "status": result.get("status") if isinstance(result, dict) else None,
        "worst_severity": result.get("worst_severity") if isinstance(result, dict) else None,
        "issue_count": len(issues) if isinstance(issues, list) else 0,
    }


def _safe_list(plan: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = plan.get(key, [])
    return value if isinstance(value, list) else []


def _relative_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _scan_files_for_secret(paths: list[Path], secrets: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if not secrets:
        return hits
    seen: set[Path] = set()
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        count = sum(1 for secret in secrets if secret and secret in text)
        if count:
            hits.append({"path": str(resolved), "secret_count": count})
    return hits


def _langgraph_output_paths(run_workspace: Path, phase: int) -> list[Path]:
    return [
        run_workspace / f"CONTROL_LANGGRAPH_PHASE_{phase}.md",
        run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md",
        run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json",
        run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.md",
        run_workspace / "reports" / "LANGGRAPH_RAW_MODEL_OUTPUT.md",
    ]


def _default_output_paths(workspace: Path, mode: str, phase: int, provider: str) -> tuple[Path, Path]:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", workspace.name)
    safe_provider = re.sub(r"[^A-Za-z0-9_.-]+", "_", provider.upper())
    safe_mode = re.sub(r"[^A-Za-z0-9_.-]+", "_", mode.upper())
    stem = f"LANGGRAPH_{safe_provider}_{safe_mode}_PHASE{phase}_{safe_name}"
    return DEFAULT_OUTPUT_DIR / f"{stem}.json", DEFAULT_OUTPUT_DIR / f"{stem}.md"


def _phase_plan_from_run_workspace(run_workspace: Path) -> dict[str, Any] | None:
    plan_path = run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json"
    if not plan_path.is_file():
        return None
    return json.loads(plan_path.read_text(encoding="utf-8"))


def _summary_from_result(
    *,
    workspace: Path,
    result: dict[str, Any],
    mode: str,
    phase: int,
    provider: str,
    model: str | None,
    verify_hash_before: str | None,
    verify_hash_after: str | None,
    provider_error: str | None = None,
) -> dict[str, Any]:
    run_workspace = Path(str(result.get("run_workspace") or "")).resolve() if result.get("run_workspace") else None
    phase_plan = result.get("phase_plan") if isinstance(result.get("phase_plan"), dict) else {}
    pre_audit = _audit_result(result.get("pre_audit"))
    post_audit = _audit_result(result.get("post_audit"))
    issues = result.get("issues", [])
    issue_count = len(issues) if isinstance(issues, list) else post_audit["issue_count"]

    summary = {
        "kind": "real_provider_benchmark",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_workspace": str(workspace.resolve()),
        "run_workspace": str(run_workspace) if run_workspace else None,
        "run_workspace_under_source_runs": (
            _relative_under(run_workspace, workspace / "runs") if run_workspace else False
        ),
        "mode": mode,
        "phase": phase,
        "provider": provider,
        "model": model,
        "status": result.get("status", "UNKNOWN"),
        "provider_error": provider_error or result.get("provider_error"),
        "prompt_path": result.get("prompt_path"),
        "plan_path": result.get("plan_path"),
        "plan_markdown_path": result.get("plan_markdown_path"),
        "raw_output_path": result.get("raw_output_path"),
        "report_path": result.get("report_path"),
        "pre_audit_status": pre_audit["status"],
        "pre_audit_worst": pre_audit["worst_severity"],
        "post_audit_status": post_audit["status"],
        "post_audit_worst": post_audit["worst_severity"],
        "issue_count": issue_count,
        "source_verify_hash_before": verify_hash_before,
        "source_verify_hash_after": verify_hash_after,
        "source_verify_hash_unchanged": verify_hash_before == verify_hash_after,
        "phase_plan_summary": phase_plan.get("summary"),
        "phase_name": phase_plan.get("phase_name"),
        "planned_step_count": len(_safe_list(phase_plan, "planned_steps")),
        "rag_query_count": len(_safe_list(phase_plan, "rag_queries")),
        "risk_count": len(_safe_list(phase_plan, "risk_register")),
        "human_gate_count": len(_safe_list(phase_plan, "human_gates")),
        "expected_artifacts": phase_plan.get("expected_artifacts", []),
        "do_not_do": phase_plan.get("do_not_do", []),
        "next_action": phase_plan.get("next_action"),
        "planned_steps": _safe_list(phase_plan, "planned_steps"),
        "rag_queries": _safe_list(phase_plan, "rag_queries"),
        "risk_register": _safe_list(phase_plan, "risk_register"),
        "human_gates": _safe_list(phase_plan, "human_gates"),
        "verify_report_auto_written": False,
        "scope_note": (
            "Real provider benchmark for planning only. It does not run controlled_apply, "
            "does not edit paper/code/results, and does not claim final PASS."
        ),
        "secret_hits": [],
        "json_valid": False,
    }
    verify_path = workspace / "reports" / "VERIFY_REPORT.md"
    if run_workspace:
        run_verify = run_workspace / "reports" / "VERIFY_REPORT.md"
        summary["verify_report_auto_written"] = run_verify.is_file() and sha256_file(run_verify) != verify_hash_before
    summary["source_verify_report_path"] = str(verify_path.resolve())
    return summary


def _summary_from_existing_run(
    *,
    workspace: Path,
    run_workspace: Path,
    mode: str,
    phase: int,
    provider: str,
    model: str | None,
    verify_hash_before: str | None,
    verify_hash_after: str | None,
) -> dict[str, Any]:
    phase_plan = _phase_plan_from_run_workspace(run_workspace) or {}
    result = {
        "source_workspace": str(workspace.resolve()),
        "run_workspace": str(run_workspace.resolve()),
        "mode": mode,
        "phase": phase,
        "provider": provider,
        "model": model,
        "status": "PLAN_READY" if phase_plan else "PLAN_MISSING",
        "provider_error": None if phase_plan else "Existing run workspace has no LANGGRAPH_PHASE_PLAN.json.",
        "phase_plan": phase_plan,
        "prompt_path": str((run_workspace / f"CONTROL_LANGGRAPH_PHASE_{phase}.md").resolve()),
        "plan_path": str((run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json").resolve()),
        "plan_markdown_path": str((run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.md").resolve()),
        "report_path": str((run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md").resolve()),
    }
    return _summary_from_result(
        workspace=workspace,
        result=result,
        mode=mode,
        phase=phase,
        provider=provider,
        model=model,
        verify_hash_before=verify_hash_before,
        verify_hash_after=verify_hash_after,
    )


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# LangGraph Real Provider Benchmark",
        "",
        f"- Workspace: `{summary.get('source_workspace')}`",
        f"- Run workspace: `{summary.get('run_workspace')}`",
        f"- Mode: `{summary.get('mode')}`",
        f"- Phase: `{summary.get('phase')}`",
        f"- Provider: `{summary.get('provider')}`",
        f"- Model: `{summary.get('model') or 'default'}`",
        f"- Status: `{summary.get('status')}`",
        f"- Provider error: `{summary.get('provider_error') or 'none'}`",
        f"- Source VERIFY_REPORT hash unchanged: `{summary.get('source_verify_hash_unchanged')}`",
        f"- Secret hits: `{len(summary.get('secret_hits', []))}`",
        "",
        "## Phase Plan Summary",
        "",
        f"- Phase name: {summary.get('phase_name') or 'none'}",
        f"- Summary: {summary.get('phase_plan_summary') or 'none'}",
        f"- Planned steps: {summary.get('planned_step_count', 0)}",
        f"- RAG queries: {summary.get('rag_query_count', 0)}",
        f"- Risk items: {summary.get('risk_count', 0)}",
        f"- Human gates: {summary.get('human_gate_count', 0)}",
        f"- Next action: {summary.get('next_action') or 'none'}",
        "",
        "## Planned Steps",
        "",
        "| ID | Title | Requires Human |",
        "| --- | --- | --- |",
    ]
    for step in summary.get("planned_steps", []):
        lines.append(
            f"| {step.get('id', '')} | {step.get('title', '')} | {step.get('requires_human', False)} |"
        )
    if not summary.get("planned_steps"):
        lines.append("| none | none | false |")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- This benchmark does not run controlled_apply.",
            "- This benchmark does not edit paper, code, results, figures, or source data.",
            "- This benchmark does not claim final PASS.",
            "- API keys are read only from environment variables and are not written to reports.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reports(summary: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    safe_summary = sanitize_json_value(redact_secrets(summary))
    json_text = json.dumps(safe_summary, ensure_ascii=False, indent=2, default=str)
    json.loads(json_text)
    json_path.write_text(json_text + "\n", encoding="utf-8")
    # Validate the bytes as they landed on disk.
    json.loads(json_path.read_text(encoding="utf-8"))
    markdown_path.write_text(markdown_report(safe_summary), encoding="utf-8")


def run_benchmark(
    *,
    workspace: Path,
    mode: str,
    phase: int,
    provider: str,
    model: str | None,
    output_json: Path | None = None,
    output_markdown: Path | None = None,
    run_name: str | None = None,
    from_run_workspace: Path | None = None,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    if mode not in REAL_PROVIDER_MODES:
        raise ValueError(f"Unsupported real provider benchmark mode: {mode}")
    if phase < 0 or phase > 6:
        raise ValueError("phase must be between 0 and 6")
    if not workspace.is_dir():
        raise FileNotFoundError(f"Workspace does not exist: {workspace}")

    json_path, markdown_path = _default_output_paths(workspace, mode, phase, provider)
    if output_json:
        json_path = output_json
    if output_markdown:
        markdown_path = output_markdown

    verify_path = workspace / "reports" / "VERIFY_REPORT.md"
    verify_hash_before = sha256_file(verify_path)
    secrets = _known_secrets()
    provider_error: str | None = None

    if from_run_workspace:
        run_workspace = from_run_workspace.resolve()
        summary = _summary_from_existing_run(
            workspace=workspace,
            run_workspace=run_workspace,
            mode=mode,
            phase=phase,
            provider=provider,
            model=model,
            verify_hash_before=verify_hash_before,
            verify_hash_after=sha256_file(verify_path),
        )
    else:
        settings = Settings(
            mathmodel_root=REPO_ROOT,
            workspace_root=workspace.parent,
            examples_root=REPO_ROOT / "examples",
            python_executable=sys.executable,
        )
        try:
            result = run_langgraph_phase(
                settings=settings,
                source_workspace=workspace,
                phase=phase,
                mode=mode,
                provider=provider,
                model=model,
                copy_workspace=True,
                run_name=run_name or f"real-benchmark-{provider}-{mode}-phase{phase}-{workspace.name}",
                temperature=0.2,
                max_tokens=4096,
            )
        except Exception as exc:  # Keep benchmark reporting stable even if provider fails.
            provider_error = str(exc)
            result = {
                "source_workspace": str(workspace),
                "run_workspace": None,
                "mode": mode,
                "phase": phase,
                "provider": provider,
                "model": model,
                "status": "BENCHMARK_ERROR",
                "provider_error": provider_error,
                "phase_plan": {},
            }
        summary = _summary_from_result(
            workspace=workspace,
            result=result,
            mode=mode,
            phase=phase,
            provider=provider,
            model=model,
            verify_hash_before=verify_hash_before,
            verify_hash_after=sha256_file(verify_path),
            provider_error=provider_error,
        )

    scan_paths = [json_path, markdown_path]
    run_workspace_value = summary.get("run_workspace")
    if run_workspace_value:
        scan_paths.extend(_langgraph_output_paths(Path(str(run_workspace_value)), phase))
    summary["secret_hits"] = _scan_files_for_secret(scan_paths, secrets)
    summary["json_valid"] = True
    summary = sanitize_json_value(redact_secrets(summary, secrets))
    write_reports(summary, json_path, markdown_path)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Single-workspace real provider LangGraph benchmark")
    parser.add_argument("--workspace", required=True, help="Workspace to benchmark")
    parser.add_argument("--mode", default="llm_plan", choices=sorted(REAL_PROVIDER_MODES))
    parser.add_argument("--phase", type=int, default=1)
    parser.add_argument("--provider", default="deepseek")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--run-name")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument(
        "--from-run-workspace",
        help="Regenerate report from an existing copied run workspace without calling the provider",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace)
    output_dir = Path(args.output_dir)
    default_json, default_md = _default_output_paths(workspace, args.mode, args.phase, args.provider)
    if not args.json_out:
        default_json = output_dir / default_json.name
    if not args.markdown_out:
        default_md = output_dir / default_md.name

    try:
        summary = run_benchmark(
            workspace=workspace,
            mode=args.mode,
            phase=args.phase,
            provider=args.provider,
            model=args.model,
            output_json=Path(args.json_out) if args.json_out else default_json,
            output_markdown=Path(args.markdown_out) if args.markdown_out else default_md,
            run_name=args.run_name,
            from_run_workspace=Path(args.from_run_workspace) if args.from_run_workspace else None,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
