from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.real_provider_benchmark as bench


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    (workspace / "reports").mkdir(parents=True)
    (workspace / "PROBLEM_BRIEF.md").write_text("# Problem\n", encoding="utf-8")
    (workspace / "reports" / "VERIFY_REPORT.md").write_text("old verify\n", encoding="utf-8")
    return workspace


def test_safe_json_report_escapes_control_characters(tmp_path: Path) -> None:
    summary = {
        "kind": "real_provider_benchmark",
        "phase_plan_summary": "中文 line\nwith control \x01 and tab\t",
        "planned_steps": [{"id": "s1", "title": "标题\x02", "description": "ok"}],
    }
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"

    bench.write_reports(summary, json_path, md_path)

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["phase_plan_summary"].startswith("中文")
    assert "\\u0001" in parsed["phase_plan_summary"]
    assert "\\u0002" in parsed["planned_steps"][0]["title"]
    assert "# LangGraph Real Provider Benchmark" in md_path.read_text(encoding="utf-8")


def test_run_benchmark_plan_ready_writes_summary_without_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    run_workspace = workspace / "runs" / "run-1"
    (run_workspace / "reports").mkdir(parents=True)
    (run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json").write_text("{}", encoding="utf-8")
    (run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md").write_text("no secrets\n", encoding="utf-8")

    def fake_run_langgraph_phase(**_: object) -> dict[str, object]:
        return {
            "source_workspace": str(workspace),
            "run_workspace": str(run_workspace),
            "mode": "llm_plan",
            "phase": 1,
            "provider": "deepseek",
            "model": "deepseek-chat",
            "status": "PLAN_READY",
            "provider_error": None,
            "phase_plan": {
                "phase": 1,
                "phase_name": "model strategy",
                "summary": "choose route\nsafely",
                "planned_steps": [
                    {"id": "step-1", "title": "read", "description": "read brief"}
                ],
                "rag_queries": [
                    {"library": "model_methods", "query": "评价模型", "core_only": True, "reason": "route"}
                ],
                "risk_register": [
                    {"severity": "HIGH", "risk": "template pollution", "mitigation": "adaptation log"}
                ],
                "human_gates": [
                    {"gate_file": "reports/HUMAN_MODEL_REVIEW.md", "required": True, "reason": "approve"}
                ],
                "expected_artifacts": ["reports/MODEL_CANDIDATES.md"],
                "do_not_do": ["do not apply"],
                "next_action": "review plan",
            },
            "pre_audit": {"result": {"status": "FAIL", "worst_severity": "HIGH", "issues": [{}]}},
            "post_audit": {"result": {"status": "FAIL", "worst_severity": "HIGH", "issues": [{}]}},
            "prompt_path": str(run_workspace / "CONTROL_LANGGRAPH_PHASE_1.md"),
            "plan_path": str(run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json"),
            "plan_markdown_path": str(run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.md"),
            "report_path": str(run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md"),
        }

    monkeypatch.setattr(bench, "run_langgraph_phase", fake_run_langgraph_phase)
    monkeypatch.setenv("MATHMODEL_LLM_API_KEY", "unit-test-secret-value")

    json_path = tmp_path / "out.json"
    md_path = tmp_path / "out.md"
    summary = bench.run_benchmark(
        workspace=workspace,
        mode="llm_plan",
        phase=1,
        provider="deepseek",
        model="deepseek-chat",
        output_json=json_path,
        output_markdown=md_path,
        run_name="test-run",
    )

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["status"] == "PLAN_READY"
    assert parsed["planned_step_count"] == 1
    assert parsed["rag_query_count"] == 1
    assert parsed["risk_count"] == 1
    assert parsed["human_gate_count"] == 1
    assert parsed["source_verify_hash_before"] == parsed["source_verify_hash_after"]
    assert parsed["secret_hits"] == []
    assert "unit-test-secret-value" not in json_path.read_text(encoding="utf-8")
    assert "unit-test-secret-value" not in md_path.read_text(encoding="utf-8")
    assert summary["json_valid"] is True


def test_run_benchmark_provider_error_writes_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)

    def fake_run_langgraph_phase(**_: object) -> dict[str, object]:
        raise RuntimeError("provider request failed")

    monkeypatch.setattr(bench, "run_langgraph_phase", fake_run_langgraph_phase)

    json_path = tmp_path / "error.json"
    md_path = tmp_path / "error.md"
    summary = bench.run_benchmark(
        workspace=workspace,
        mode="llm_plan",
        phase=1,
        provider="deepseek",
        model="deepseek-chat",
        output_json=json_path,
        output_markdown=md_path,
        run_name="error-run",
    )

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["status"] == "BENCHMARK_ERROR"
    assert "provider request failed" in parsed["provider_error"]
    assert parsed["json_valid"] is True
    assert summary["source_verify_hash_before"] == summary["source_verify_hash_after"]


def test_report_from_existing_run_workspace(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    run_workspace = workspace / "runs" / "existing"
    (run_workspace / "reports").mkdir(parents=True)
    (run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json").write_text(
        json.dumps(
            {
                "phase": 1,
                "phase_name": "strategy",
                "summary": "phase summary",
                "planned_steps": [{"id": "a", "title": "A", "description": "B"}],
                "rag_queries": [],
                "risk_register": [],
                "human_gates": [],
                "expected_artifacts": [],
                "do_not_do": [],
                "next_action": "next",
            }
        ),
        encoding="utf-8",
    )

    json_path = tmp_path / "existing.json"
    md_path = tmp_path / "existing.md"
    summary = bench.run_benchmark(
        workspace=workspace,
        mode="llm_plan",
        phase=1,
        provider="deepseek",
        model="deepseek-chat",
        output_json=json_path,
        output_markdown=md_path,
        from_run_workspace=run_workspace,
    )

    assert summary["status"] == "PLAN_READY"
    assert summary["run_workspace"] == str(run_workspace.resolve())
    assert json.loads(json_path.read_text(encoding="utf-8"))["phase_plan_summary"] == "phase summary"
