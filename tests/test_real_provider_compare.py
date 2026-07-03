from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.real_provider_compare as compare


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    (workspace / "reports").mkdir(parents=True)
    (workspace / "PROBLEM_BRIEF.md").write_text("# Problem\n", encoding="utf-8")
    (workspace / "reports" / "VERIFY_REPORT.md").write_text("verify\n", encoding="utf-8")
    return workspace


def test_parse_provider_specs() -> None:
    assert compare.parse_provider_spec("deepseek:deepseek-chat") == ("deepseek", "deepseek-chat")
    assert compare.parse_provider_spec("openai-compatible:gpt-4.1-mini") == (
        "openai-compatible",
        "gpt-4.1-mini",
    )
    assert compare.parse_provider_spec("none") == ("none", None)


def test_compare_real_providers_writes_ranked_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)

    def fake_run_benchmark(**kwargs: object) -> dict[str, object]:
        provider = str(kwargs["provider"])
        model = kwargs.get("model")
        if provider == "deepseek":
            return {
                "provider": provider,
                "model": model,
                "status": "PLAN_READY",
                "json_valid": True,
                "planned_step_count": 7,
                "rag_query_count": 3,
                "risk_count": 3,
                "human_gate_count": 1,
                "do_not_do": ["do not apply"],
                "source_verify_hash_unchanged": True,
                "secret_hits": [],
                "phase_plan_summary": "good plan",
            }
        return {
            "provider": provider,
            "model": model,
            "status": "BENCHMARK_ERROR",
            "provider_error": "missing api key",
            "json_valid": True,
            "planned_step_count": 0,
            "rag_query_count": 0,
            "risk_count": 0,
            "human_gate_count": 0,
            "do_not_do": [],
            "source_verify_hash_unchanged": True,
            "secret_hits": [],
            "phase_plan_summary": None,
        }

    monkeypatch.setattr(compare.benchmark, "run_benchmark", fake_run_benchmark)

    json_path = tmp_path / "comparison.json"
    md_path = tmp_path / "comparison.md"
    report = compare.run_comparison(
        workspace=workspace,
        specs=["openai-compatible:gpt-test", "deepseek:deepseek-chat"],
        mode="llm_plan",
        phase=1,
        output_dir=tmp_path / "single",
        output_json=json_path,
        output_markdown=md_path,
    )

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["kind"] == "real_provider_comparison"
    assert parsed["results"][0]["provider"] == "deepseek"
    assert parsed["results"][0]["score_total"] > parsed["results"][1]["score_total"]
    assert parsed["results"][1]["status"] == "BENCHMARK_ERROR"
    assert "DeepSeek" in md_path.read_text(encoding="utf-8") or "deepseek" in md_path.read_text(encoding="utf-8")
    assert report["json_valid"] is True


def test_quality_score_penalizes_missing_gate_and_secret_hit() -> None:
    good = compare.score_summary(
        {
            "status": "PLAN_READY",
            "json_valid": True,
            "planned_step_count": 5,
            "rag_query_count": 3,
            "risk_count": 3,
            "human_gate_count": 1,
            "do_not_do": ["no apply"],
            "source_verify_hash_unchanged": True,
            "secret_hits": [],
        }
    )
    weak = compare.score_summary(
        {
            "status": "PLAN_READY",
            "json_valid": True,
            "planned_step_count": 5,
            "rag_query_count": 3,
            "risk_count": 3,
            "human_gate_count": 0,
            "do_not_do": [],
            "source_verify_hash_unchanged": True,
            "secret_hits": [{"path": "x"}],
        }
    )

    assert good["total"] == 100
    assert weak["total"] < good["total"]
    assert "human_gate" in weak["deductions"]
    assert "secret_safety" in weak["deductions"]
