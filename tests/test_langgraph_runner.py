from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings  # noqa: E402
from app.workspace import copy_workspace_for_run, read_history  # noqa: E402
from app import langgraph_runner  # noqa: E402


class FakeCompiledGraph:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def invoke(self, state: langgraph_runner.MathModelGraphState) -> langgraph_runner.MathModelGraphState:
        for node in [
            langgraph_runner.pre_audit_node(self.settings),
            langgraph_runner.build_prompt_node(),
            langgraph_runner.provider_plan_node(),
            langgraph_runner.validate_plan_node(),
            langgraph_runner.write_plan_node(),
            langgraph_runner.apply_router_node(),
            langgraph_runner.controlled_write_node(),
            langgraph_runner.post_audit_node(self.settings),
            langgraph_runner.write_report_node(),
            langgraph_runner.append_history_node(),
        ]:
            state = node(state)
        return state


def install_fake_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(langgraph_runner, "langgraph_available", lambda: True)
    monkeypatch.setattr(langgraph_runner, "_build_graph", lambda settings: FakeCompiledGraph(settings))


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        mathmodel_root=REPO_ROOT,
        workspace_root=tmp_path / "workspaces",
        examples_root=tmp_path / "examples",
        python_executable=sys.executable,
    )


def make_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspaces" / "case-a"
    (workspace / "reports").mkdir(parents=True)
    (workspace / "results").mkdir()
    (workspace / "paper").mkdir()
    (workspace / "source").mkdir()
    (workspace / "WORKFLOW_STATE.md").write_text("# Workflow State\n", encoding="utf-8")
    (workspace / "PROBLEM_BRIEF.md").write_text("# Problem Brief\n", encoding="utf-8")
    (workspace / "DATA_AUDIT.md").write_text("# Data Audit\n", encoding="utf-8")
    (workspace / "reports" / "INTAKE_GATE.md").write_text("PASS\n", encoding="utf-8")
    (workspace / "reports" / "FIGURE_PLAN.md").write_text("# Figure Plan\n", encoding="utf-8")
    (workspace / "reports" / "FIGURE_AUDIT.md").write_text("# Figure Audit\n", encoding="utf-8")
    (workspace / "reports" / "VERIFY_REPORT.md").write_text("Conclusion: PENDING\n", encoding="utf-8")
    (workspace / "results" / "RESULTS_MANIFEST.json").write_text(
        json.dumps({"metrics": [], "tables": [], "figures": [], "scripts": []}),
        encoding="utf-8",
    )
    return workspace


def test_langgraph_status_without_install_does_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(langgraph_runner, "_StateGraph", None)
    monkeypatch.setattr(langgraph_runner, "_LANGGRAPH_IMPORT_ERROR", "No module named 'langgraph'")

    status = langgraph_runner.langgraph_status()

    assert status["available"] is False
    assert "requirements-langgraph.txt" in status["note"]
    assert status["import_error"]


def test_run_langgraph_phase_without_install_has_clear_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(langgraph_runner, "_StateGraph", None)
    monkeypatch.setattr(langgraph_runner, "_LANGGRAPH_IMPORT_ERROR", "No module named 'langgraph'")
    workspace = make_workspace(tmp_path)

    with pytest.raises(langgraph_runner.LangGraphUnavailableError) as exc:
        langgraph_runner.run_langgraph_phase(
            settings=make_settings(tmp_path),
            source_workspace=workspace,
            phase=1,
            mode="dry_run",
            provider="none",
            model=None,
        )

    assert "requirements-langgraph.txt" in str(exc.value)


@pytest.mark.skipif(not langgraph_runner.langgraph_available(), reason="optional LangGraph dependency is not installed")
def test_langgraph_dry_run_writes_reports_and_history(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="dry_run",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="lg-test",
    )

    run_workspace = Path(result["run_workspace"])
    prompt_path = Path(result["prompt_path"])
    report_path = Path(result["report_path"])
    control_path = run_workspace / "CONTROL_LANGGRAPH_PHASE_1.md"

    assert run_workspace.is_dir()
    assert run_workspace.resolve().relative_to((workspace / "runs").resolve())
    assert control_path.is_file()
    assert prompt_path == control_path
    assert report_path == run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md"
    assert report_path.is_file()
    assert result["pre_audit"]
    assert result["post_audit"]
    assert result["status"] == "dry_run_complete"
    assert result["history"]["event"] == "langgraph_phase_dry_run"
    assert any(item["event"] == "langgraph_phase_dry_run" for item in read_history(workspace))


def test_langgraph_dry_run_rejects_run_workspace_escape(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    outside = tmp_path / "outside-run"
    outside.mkdir()

    state: langgraph_runner.MathModelGraphState = {
        "source_workspace": str(workspace),
        "run_workspace": str(outside),
        "phase": 1,
        "mode": "dry_run",
        "provider": "none",
        "model": None,
        "prompt": "",
        "prompt_path": None,
        "pre_audit": {},
        "post_audit": {},
        "issues": [],
        "created_files": [],
        "updated_files": [],
        "needs_human": False,
        "status": "initialized",
        "stop_reason": None,
        "report_path": None,
    }

    with pytest.raises(ValueError):
        langgraph_runner.assert_run_workspace_allowed(state)


def test_langgraph_llm_plan_with_none_provider_writes_plan_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="llm_plan",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="lg-plan-test",
    )

    run_workspace = Path(result["run_workspace"])
    plan_path = run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json"
    plan_markdown_path = run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.md"
    report_path = run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md"
    forbidden_dirs = ["paper", "code", "figures", "results"]

    assert result["status"] == "PLAN_READY"
    assert result["phase_plan"]["phase"] == 1
    assert Path(result["plan_path"]) == plan_path
    assert Path(result["plan_markdown_path"]) == plan_markdown_path
    assert result["raw_output_path"] is None
    assert plan_path.is_file()
    assert plan_markdown_path.is_file()
    assert report_path.is_file()
    assert result["history"]["event"] == "langgraph_phase_llm_plan"
    assert any(item["event"] == "langgraph_phase_llm_plan" for item in read_history(workspace))
    assert all(not path.startswith(tuple(f"{folder}/" for folder in forbidden_dirs)) for path in result["created_files"])
    assert all(not path.startswith(tuple(f"{folder}/" for folder in forbidden_dirs)) for path in result["updated_files"])


def test_langgraph_llm_plan_invalid_json_writes_raw_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    class BadAdapter:
        provider = "none"

        def generate(self, *_args, **_kwargs) -> str:
            return "not valid json"

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: BadAdapter())

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="llm_plan",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="lg-bad-json-test",
    )

    raw_output_path = Path(result["raw_output_path"])

    assert result["status"] == "PLAN_PARSE_FAILED"
    assert result["provider_error"]
    assert result["phase_plan"] is None
    assert result["plan_path"] is None
    assert raw_output_path.name == "LANGGRAPH_RAW_MODEL_OUTPUT.md"
    assert raw_output_path.is_file()
    assert "not valid json" in raw_output_path.read_text(encoding="utf-8")


def make_phase_plan(phase: int, file_writes: list[dict]) -> dict:
    return {
        "phase": phase,
        "phase_name": f"Phase {phase}",
        "summary": "Controlled apply test plan.",
        "required_inputs": ["PROBLEM_BRIEF.md"],
        "required_outputs": [item["path"] for item in file_writes],
        "planned_steps": [
            {
                "id": "s1",
                "title": "write reports",
                "description": "write allowed controlled reports",
                "reads": ["PROBLEM_BRIEF.md"],
                "writes": [item["path"] for item in file_writes],
                "checks": ["allowlist"],
                "requires_human": True,
            }
        ],
        "rag_queries": [],
        "source_quality_requirements": ["S/A for core evidence"],
        "human_gates": [
            {
                "gate_file": "reports/HUMAN_MODEL_REVIEW.md",
                "required": True,
                "reason": "Human review remains mandatory.",
            }
        ],
        "risk_register": [],
        "expected_artifacts": [item["path"] for item in file_writes],
        "do_not_do": ["paper/", "code/", "figures/", "results/"],
        "next_action": "Human review required.",
        "file_writes": file_writes,
    }


def write_existing_plan(workspace: Path, phase: int, file_writes: list[dict]) -> None:
    plan_path = workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json"
    plan_path.write_text(json.dumps(make_phase_plan(phase, file_writes), ensure_ascii=False), encoding="utf-8")


def test_allowed_apply_paths_are_phase_specific() -> None:
    assert langgraph_runner.allowed_apply_paths(1) == {
        "reports/MODEL_CANDIDATES.md",
        "reports/MODEL_REVIEW_AI.md",
        "reports/FIGURE_PLAN.md",
        "reports/REFINEMENT_LOG.md",
    }
    assert langgraph_runner.allowed_apply_paths(4) == {
        "reports/PAPER_SCORECARD.md",
        "reports/REVISION_ACTIONS.md",
        "reports/REFINEMENT_LOG.md",
    }
    assert langgraph_runner.allowed_apply_paths(2) == set()


@pytest.mark.parametrize(
    "bad_path",
    [
        "paper/main.tex",
        "../outside.md",
        "C:/tmp/outside.md",
        "reports/HUMAN_MODEL_REVIEW.md",
        "reports/MODELING_DECISION.md",
        "reports/VERIFY_REPORT.md",
        "reports/ANALYSIS_GATE.md",
    ],
)
def test_validate_apply_path_rejects_forbidden_targets(tmp_path: Path, bad_path: str) -> None:
    workspace = make_workspace(tmp_path)

    with pytest.raises(ValueError):
        langgraph_runner.validate_apply_path(workspace, bad_path, 1)


def test_validate_apply_path_accepts_allowed_phase_targets(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)

    target = langgraph_runner.validate_apply_path(workspace, "reports/MODEL_CANDIDATES.md", 1)

    assert target == workspace / "reports" / "MODEL_CANDIDATES.md"


def test_controlled_apply_phase1_writes_allowed_reports_and_logs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    write_existing_plan(
        workspace,
        1,
        [
            {"path": "reports/MODEL_CANDIDATES.md", "purpose": "candidates", "content": "# Candidates\n"},
            {"path": "reports/MODEL_REVIEW_AI.md", "purpose": "review", "content": "# Review\n"},
            {"path": "reports/FIGURE_PLAN.md", "purpose": "figures", "content": "# Figure Plan\n"},
            {"path": "reports/REFINEMENT_LOG.md", "purpose": "refinement", "content": "# Refinement\n"},
        ],
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="controlled_apply",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="apply-phase1",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["status"] in {"APPLY_READY_FOR_HUMAN_REVIEW", "APPLY_NEEDS_REVIEW"}
    assert result["needs_human"] is True
    assert len(result["files_written"]) == 4
    assert result["files_rejected"] == []
    assert (run_workspace / "reports" / "MODEL_CANDIDATES.md").read_text(encoding="utf-8") == "# Candidates\n"
    assert not (run_workspace / "reports" / "HUMAN_MODEL_REVIEW.md").exists()
    assert not (run_workspace / "reports" / "MODELING_DECISION.md").exists()
    assert (run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md").is_file()
    assert (run_workspace / "reports" / "AGENT_RUNS.md").is_file()
    assert result["history"]["event"] == "langgraph_phase_controlled_apply"
    assert any(item["event"] == "langgraph_phase_controlled_apply" for item in read_history(workspace))


def test_controlled_apply_phase4_writes_allowed_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    write_existing_plan(
        workspace,
        4,
        [
            {"path": "reports/PAPER_SCORECARD.md", "purpose": "score", "content": "# Scorecard\n"},
            {"path": "reports/REVISION_ACTIONS.md", "purpose": "actions", "content": "# Actions\n"},
            {"path": "reports/REFINEMENT_LOG.md", "purpose": "refinement", "content": "# Refinement\n"},
        ],
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=4,
        mode="controlled_apply",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="apply-phase4",
    )

    run_workspace = Path(result["run_workspace"])

    assert len(result["files_written"]) == 3
    assert (run_workspace / "reports" / "PAPER_SCORECARD.md").read_text(encoding="utf-8") == "# Scorecard\n"
    assert (run_workspace / "reports" / "REVISION_ACTIONS.md").read_text(encoding="utf-8") == "# Actions\n"


def test_controlled_apply_rejects_mixed_illegal_writes_without_core_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    write_existing_plan(
        workspace,
        1,
        [
            {"path": "reports/MODEL_CANDIDATES.md", "purpose": "candidates", "content": "# Candidates\n"},
            {"path": "paper/main.tex", "purpose": "forbidden", "content": "bad"},
        ],
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="controlled_apply",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="apply-reject",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["status"] == "APPLY_REJECTED"
    assert result["files_written"] == []
    assert result["files_rejected"]
    assert not (run_workspace / "reports" / "MODEL_CANDIDATES.md").exists()
    assert (run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md").is_file()


def test_controlled_apply_without_file_writes_is_plan_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="controlled_apply",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="apply-plan-only",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["status"] == "APPLY_PLAN_ONLY"
    assert result["files_planned"] == []
    assert result["files_written"] == []
    assert not (run_workspace / "reports" / "MODEL_CANDIDATES.md").exists()
    assert (run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md").is_file()


def test_controlled_apply_rolls_back_after_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    write_existing_plan(
        workspace,
        1,
        [
            {"path": "reports/MODEL_CANDIDATES.md", "purpose": "candidates", "content": "# New\n"},
            {"path": "reports/MODEL_REVIEW_AI.md", "purpose": "review", "content": "# Review\n"},
        ],
    )
    original_writer = langgraph_runner._write_text_tracked
    calls = {"count": 0}

    def flaky_writer(state, path, text):
        if path.name in {"MODEL_CANDIDATES.md", "MODEL_REVIEW_AI.md"}:
            calls["count"] += 1
        if path.name == "MODEL_REVIEW_AI.md":
            raise OSError("simulated write failure")
        return original_writer(state, path, text)

    monkeypatch.setattr(langgraph_runner, "_write_text_tracked", flaky_writer)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="controlled_apply",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="apply-rollback",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["status"] == "APPLY_ROLLED_BACK"
    assert "simulated write failure" in result["apply_error"]
    assert not (run_workspace / "reports" / "MODEL_CANDIDATES.md").exists()


def test_phase_execute_with_none_provider_generates_plan_only_and_apply_diff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="phase_execute",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="execute-plan-only",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["status"] == "APPLY_PLAN_ONLY"
    assert result["needs_human"] is True
    assert result["files_written"] == []
    assert (run_workspace / "reports" / "LANGGRAPH_PHASE_PLAN.json").is_file()
    assert (run_workspace / "reports" / "LANGGRAPH_APPLY_DIFF.md").is_file()
    assert (run_workspace / "reports" / "LANGGRAPH_RUN_REPORT.md").is_file()


def test_phase_execute_phase1_provider_file_writes_are_applied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    class PhaseExecuteAdapter:
        provider = "none"

        def generate(self, *_args, **_kwargs) -> str:
            return json.dumps(
                make_phase_plan(
                    1,
                    [
                        {
                            "path": "reports/MODEL_CANDIDATES.md",
                            "purpose": "candidate routes",
                            "content": "# Model Candidates\n",
                        }
                    ],
                ),
                ensure_ascii=False,
            )

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: PhaseExecuteAdapter())

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="phase_execute",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="execute-phase1",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["status"] in {"APPLY_READY_FOR_HUMAN_REVIEW", "APPLY_NEEDS_REVIEW"}
    assert result["files_written"] == ["reports/MODEL_CANDIDATES.md"]
    assert (run_workspace / "reports" / "MODEL_CANDIDATES.md").read_text(encoding="utf-8") == "# Model Candidates\n"
    assert not (run_workspace / "reports" / "HUMAN_MODEL_REVIEW.md").exists()
    assert result["apply_diff_path"].endswith("LANGGRAPH_APPLY_DIFF.md")


def test_phase_execute_phase4_provider_file_writes_are_applied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    class PhaseExecuteAdapter:
        provider = "none"

        def generate(self, *_args, **_kwargs) -> str:
            return json.dumps(
                make_phase_plan(
                    4,
                    [
                        {"path": "reports/PAPER_SCORECARD.md", "purpose": "scorecard", "content": "# Scorecard\n"},
                        {"path": "reports/REVISION_ACTIONS.md", "purpose": "actions", "content": "# Actions\n"},
                    ],
                ),
                ensure_ascii=False,
            )

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: PhaseExecuteAdapter())

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=4,
        mode="phase_execute",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="execute-phase4",
    )

    run_workspace = Path(result["run_workspace"])

    assert set(result["files_written"]) == {"reports/PAPER_SCORECARD.md", "reports/REVISION_ACTIONS.md"}
    assert not (run_workspace / "reports" / "VERIFY_REPORT.md").read_text(encoding="utf-8").startswith("PASS")
    assert (run_workspace / "reports" / "LANGGRAPH_APPLY_DIFF.md").is_file()


def test_phase_execute_rejects_mixed_legal_and_illegal_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    class BadPathAdapter:
        provider = "none"

        def generate(self, *_args, **_kwargs) -> str:
            return json.dumps(
                make_phase_plan(
                    1,
                    [
                        {"path": "reports/MODEL_CANDIDATES.md", "purpose": "ok", "content": "# OK\n"},
                        {"path": "reports/HUMAN_MODEL_REVIEW.md", "purpose": "forbidden", "content": "# Bad\n"},
                    ],
                ),
                ensure_ascii=False,
            )

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: BadPathAdapter())

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=1,
        mode="phase_execute",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="execute-reject",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["status"] == "APPLY_REJECTED"
    assert result["files_written"] == []
    assert result["files_rejected"]
    assert not (run_workspace / "reports" / "MODEL_CANDIDATES.md").exists()
    assert (run_workspace / "reports" / "LANGGRAPH_APPLY_DIFF.md").is_file()


def test_phase_execute_unsupported_phase_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_graph(monkeypatch)
    workspace = make_workspace(tmp_path)

    with pytest.raises(ValueError) as exc:
        langgraph_runner.run_langgraph_phase(
            settings=make_settings(tmp_path),
            source_workspace=workspace,
            phase=2,
            mode="phase_execute",
            provider="none",
            model=None,
            copy_workspace=True,
        )

    assert "PHASE_NOT_SUPPORTED" in str(exc.value)


def test_check_human_model_gate_missing_and_approved(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)

    missing = langgraph_runner.check_human_model_gate(workspace)

    assert missing["approved"] is False
    assert missing["exists"] is False
    assert missing["gate_file"] == "reports/HUMAN_MODEL_REVIEW.md"

    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("确认采用第一条路线\n", encoding="utf-8")

    approved = langgraph_runner.check_human_model_gate(workspace)

    assert approved["approved"] is True
    assert approved["exists"] is True


def test_contest_graph_v0_pauses_after_phase1_when_human_gate_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v0",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-graph-pause",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["status"] == "WAITING_FOR_HUMAN_MODEL_REVIEW"
    assert result["contest_status"] == "WAITING_FOR_HUMAN_MODEL_REVIEW"
    assert result["paused_at"] == "phase_1_human_gate"
    assert result["human_gate_required"] is True
    assert result["human_gate_file"] == "reports/HUMAN_MODEL_REVIEW.md"
    assert result["completed_phases"] == [0, 1]
    assert [item["phase"] for item in result["phase_results"]] == [0, 1]
    assert (run_workspace / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md").is_file()
    assert not (run_workspace / "reports" / "MODELING_DECISION.md").exists()
    assert not (run_workspace / "CONTROL_LANGGRAPH_PHASE_2.md").exists()
    assert result["history"]["event"] == "langgraph_contest_graph_v0"
    assert any(item["event"] == "langgraph_contest_graph_v0" for item in read_history(workspace))


def test_contest_graph_v0_with_approved_gate_reaches_phase6_audit_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved: adopt route A\n", encoding="utf-8")

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v0",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-graph-full",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["contest_status"] == "CONTEST_GRAPH_REVIEW_READY"
    assert result["completed_phases"] == [0, 1, 2, 3, 4, 5, 6]
    assert result["paused_at"] is None
    assert result["final_audit"]
    assert (run_workspace / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md").is_file()
    assert (run_workspace / "CONTROL_LANGGRAPH_PHASE_2.md").is_file()
    assert not (run_workspace / "reports" / "MODELING_DECISION.md").exists()
    assert (run_workspace / "reports" / "VERIFY_REPORT.md").read_text(encoding="utf-8") == "Conclusion: PENDING\n"
    assert all(
        not path.startswith(("paper/", "code/", "figures/", "results/"))
        for path in result["created_files"] + result["updated_files"]
    )


def test_contest_graph_v0_reuses_phase_execute_allowlist_for_phase1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("通过，确认采用\n", encoding="utf-8")

    class ContestAdapter:
        provider = "none"

        def generate(self, prompt, *_args, **_kwargs) -> str:
            match = __import__("re").search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            if phase == 1:
                return json.dumps(
                    make_phase_plan(
                        1,
                        [
                            {
                                "path": "reports/MODEL_CANDIDATES.md",
                                "purpose": "candidate routes",
                                "content": "# Contest Model Candidates\n",
                            }
                        ],
                    ),
                    ensure_ascii=False,
                )
            if phase == 4:
                return json.dumps(
                    make_phase_plan(
                        4,
                        [
                            {
                                "path": "reports/PAPER_SCORECARD.md",
                                "purpose": "scorecard",
                                "content": "# Contest Scorecard\n",
                            }
                        ],
                    ),
                    ensure_ascii=False,
                )
            return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: ContestAdapter())

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v0",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-graph-writes",
    )

    run_workspace = Path(result["run_workspace"])
    phase1 = next(item for item in result["phase_results"] if item["phase"] == 1)
    phase4 = next(item for item in result["phase_results"] if item["phase"] == 4)

    assert "reports/MODEL_CANDIDATES.md" in phase1["files_written"]
    assert "reports/PAPER_SCORECARD.md" in phase4["files_written"]
    assert (run_workspace / "reports" / "MODEL_CANDIDATES.md").read_text(encoding="utf-8") == "# Contest Model Candidates\n"
    assert (run_workspace / "reports" / "PAPER_SCORECARD.md").read_text(encoding="utf-8") == "# Contest Scorecard\n"
    assert not (run_workspace / "reports" / "HUMAN_MODEL_REVIEW.md").read_text(encoding="utf-8").startswith("#")


def test_validate_phase2_commands_accepts_safe_python_commands(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text("print('ok')\n", encoding="utf-8")

    commands = [
        {
            "id": "C1",
            "purpose": "syntax",
            "command": "python -m py_compile code/solve.py",
            "expected_outputs": [],
        },
        {
            "id": "C2",
            "purpose": "run",
            "command": "python code/solve.py",
            "expected_outputs": ["results/RESULTS_MANIFEST.json", "reports/RESULTS_REPORT.md"],
        },
    ]

    validated = langgraph_runner.validate_phase2_commands(workspace, commands)

    assert [item["id"] for item in validated] == ["C1", "C2"]


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf paper",
        "del reports/VERIFY_REPORT.md",
        "curl https://example.com/script.py",
        "pip install pandas",
        "powershell -enc bad",
        "python ../outside.py",
        "python code/solve.py | powershell -enc bad",
    ],
)
def test_validate_phase2_commands_rejects_forbidden_commands(tmp_path: Path, command: str) -> None:
    workspace = make_workspace(tmp_path)
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text("print('ok')\n", encoding="utf-8")

    with pytest.raises(ValueError):
        langgraph_runner.validate_phase2_commands(
            workspace,
            [{"id": "BAD", "purpose": "bad", "command": command, "expected_outputs": []}],
        )


def test_validate_phase2_commands_rejects_forbidden_expected_outputs(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text("print('ok')\n", encoding="utf-8")

    with pytest.raises(ValueError):
        langgraph_runner.validate_phase2_commands(
            workspace,
            [
                {
                    "id": "BAD",
                    "purpose": "bad output",
                    "command": "python code/solve.py",
                    "expected_outputs": ["paper/main.tex"],
                }
            ],
        )


def test_phase2_sandbox_executes_python_and_records_manifest_and_logs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "\n".join(
            [
                "import json",
                "from pathlib import Path",
                "Path('results').mkdir(exist_ok=True)",
                "Path('reports').mkdir(exist_ok=True)",
                "Path('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [{'name': 'demo', 'value': 1}], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}), encoding='utf-8')",
                "Path('reports/RESULTS_REPORT.md').write_text('# Results\\n', encoding='utf-8')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    run_workspace = copy_workspace_for_run(workspace, "phase2-direct-run")
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=2,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(2, [])
    state["phase_plan"]["commands"] = [
        {
            "id": "C1",
            "purpose": "syntax",
            "command": "python -m py_compile code/solve.py",
            "expected_outputs": [],
        },
        {
            "id": "C2",
            "purpose": "run experiment",
            "command": "python code/solve.py",
            "expected_outputs": ["results/RESULTS_MANIFEST.json", "reports/RESULTS_REPORT.md"],
        },
    ]

    result = langgraph_runner.run_phase2_sandbox_executor(settings, state)

    assert result["sandbox_status"] == "SANDBOX_SUCCEEDED"
    assert result["manifest_created_empty"] is False
    assert (run_workspace / "results" / "RESULTS_MANIFEST.json").is_file()
    assert (run_workspace / "reports" / "RESULTS_REPORT.md").is_file()
    assert (run_workspace / "reports" / "EXPERIMENT_LOG.md").is_file()
    assert "python code/solve.py" in (run_workspace / "reports" / "EXPERIMENT_LOG.md").read_text(encoding="utf-8")
    assert any(item["event"] == "langgraph_phase2_sandbox" for item in read_history(workspace))


def test_phase2_sandbox_creates_empty_manifest_when_missing(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "results" / "RESULTS_MANIFEST.json").unlink()
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text("print('no manifest')\n", encoding="utf-8")
    run_workspace = copy_workspace_for_run(workspace, "phase2-empty-manifest")
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=2,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(2, [])
    state["phase_plan"]["commands"] = [
        {"id": "C1", "purpose": "run", "command": "python code/solve.py", "expected_outputs": []}
    ]

    result = langgraph_runner.run_phase2_sandbox_executor(settings, state)

    manifest = json.loads((run_workspace / "results" / "RESULTS_MANIFEST.json").read_text(encoding="utf-8"))
    assert result["sandbox_status"] == "SANDBOX_SUCCEEDED"
    assert result["manifest_created_empty"] is True
    assert manifest == {"metrics": [], "tables": [], "figures": [], "scripts": []}


def test_phase2_sandbox_without_commands_is_plan_only(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    run_workspace = copy_workspace_for_run(workspace, "phase2-plan-only")
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=2,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(2, [])

    result = langgraph_runner.run_phase2_sandbox_executor(settings, state)

    assert result["sandbox_status"] == "PHASE2_PLAN_ONLY"
    assert result["sandbox_commands"] == []
    assert not (run_workspace / "reports" / "EXPERIMENT_LOG.md").exists()


def test_phase2_sandbox_rejects_illegal_command_without_execution(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text("print('should not run')\n", encoding="utf-8")
    run_workspace = copy_workspace_for_run(workspace, "phase2-reject")
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=2,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(2, [])
    state["phase_plan"]["commands"] = [
        {"id": "BAD", "purpose": "bad", "command": "python ../outside.py", "expected_outputs": []}
    ]

    result = langgraph_runner.run_phase2_sandbox_executor(settings, state)

    assert result["sandbox_status"] == "SANDBOX_COMMAND_REJECTED"
    assert result["sandbox_commands"][0]["status"] == "REJECTED"
    assert not (run_workspace / "reports" / "EXPERIMENT_LOG.md").exists()


def test_phase2_sandbox_requires_copied_run_workspace(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=workspace,
        phase=2,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(2, [])
    state["phase_plan"]["commands"] = [
        {"id": "C1", "purpose": "run", "command": "python code/solve.py", "expected_outputs": []}
    ]

    with pytest.raises(ValueError, match="copied run workspace"):
        langgraph_runner.run_phase2_sandbox_executor(settings, state)


def test_phase2_sandbox_rolls_back_forbidden_runtime_write(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "from pathlib import Path\nPath('paper').mkdir(exist_ok=True)\nPath('paper/main.tex').write_text('bad', encoding='utf-8')\n",
        encoding="utf-8",
    )
    run_workspace = copy_workspace_for_run(workspace, "phase2-runtime-violation")
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=2,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(2, [])
    state["phase_plan"]["commands"] = [
        {"id": "C1", "purpose": "bad write", "command": "python code/solve.py", "expected_outputs": []}
    ]

    result = langgraph_runner.run_phase2_sandbox_executor(settings, state)

    assert result["sandbox_status"] == "SANDBOX_WRITE_VIOLATION"
    assert "paper/main.tex" in result["forbidden_changes"]
    assert not (run_workspace / "paper" / "main.tex").exists()


def test_contest_graph_v1_pauses_at_human_gate_without_phase2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v1-pause",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["contest_status"] == "WAITING_FOR_HUMAN_MODEL_REVIEW"
    assert result["completed_phases"] == [0, 1]
    assert not (run_workspace / "CONTROL_LANGGRAPH_PHASE_2.md").exists()


def test_contest_graph_v1_runs_phase2_sandbox_after_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('reports').mkdir(exist_ok=True)\nPath('results').mkdir(exist_ok=True)\nPath('reports/RESULTS_REPORT.md').write_text('# OK\\n', encoding='utf-8')\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}), encoding='utf-8')\n",
        encoding="utf-8",
    )

    class ContestV1Adapter:
        provider = "none"

        def generate(self, prompt, *_args, **_kwargs) -> str:
            match = __import__("re").search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            plan = make_phase_plan(phase, [])
            if phase == 2:
                plan["commands"] = [
                    {"id": "C1", "purpose": "syntax", "command": "python -m py_compile code/solve.py", "expected_outputs": []},
                    {"id": "C2", "purpose": "run", "command": "python code/solve.py", "expected_outputs": ["results/RESULTS_MANIFEST.json", "reports/RESULTS_REPORT.md"]},
                ]
            return json.dumps(plan, ensure_ascii=False)

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: ContestV1Adapter())
    monkeypatch.setattr(
        langgraph_runner,
        "run_audit",
        lambda _settings, _workspace, **_kwargs: {
            "result": {"status": "PASS", "worst_severity": "NONE", "issues": []},
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        },
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v1-run",
    )

    run_workspace = Path(result["run_workspace"])
    phase2 = next(item for item in result["phase_results"] if item["phase"] == 2)

    assert phase2["sandbox_status"] == "SANDBOX_SUCCEEDED"
    assert result["contest_status"] == "CONTEST_GRAPH_REVIEW_READY"
    assert (run_workspace / "reports" / "EXPERIMENT_LOG.md").is_file()
    assert (run_workspace / "reports" / "RESULTS_REPORT.md").is_file()
    assert (run_workspace / "results" / "RESULTS_MANIFEST.json").is_file()
    assert not (run_workspace / "paper").joinpath("main.tex").exists()


def test_contest_graph_v1_stops_when_phase2_command_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text("print('ok')\n", encoding="utf-8")

    class BadCommandAdapter:
        provider = "none"

        def generate(self, prompt, *_args, **_kwargs) -> str:
            match = __import__("re").search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            plan = make_phase_plan(phase, [])
            if phase == 2:
                plan["commands"] = [
                    {"id": "BAD", "purpose": "network", "command": "curl https://example.com", "expected_outputs": []}
                ]
            return json.dumps(plan, ensure_ascii=False)

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: BadCommandAdapter())

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v1",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v1-reject",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["contest_status"] == "SANDBOX_COMMAND_REJECTED"
    assert result["paused_at"] == "phase_2_sandbox"
    assert result["completed_phases"] == [0, 1, 2]
    assert not (run_workspace / "CONTROL_LANGGRAPH_PHASE_3.md").exists()


def make_phase3_writes() -> list[dict]:
    return [
        {
            "path": "paper/main.tex",
            "purpose": "paper draft",
            "content": "\n".join(
                [
                    "% AI generated draft. Human confirmation required.",
                    "\\section{摘要}",
                    "AI生成草稿：基于已有结果撰写摘要占位。缺失结果必须保留风险提示。",
                    "\\section{问题重述}",
                    "待人工确认：问题背景和子问题描述。",
                    "\\section{符号说明}",
                    "已有结果：引用 RESULTS_MANIFEST 中登记的变量和指标。",
                    "\\section{模型假设}",
                    "待人工确认：模型假设不得作为事实。",
                    "\\section{模型建立}",
                    "AI生成草稿：描述已确认模型路线。",
                    "\\section{求解与实验结果}",
                    "已有结果来自 reports/RESULTS_REPORT.md；缺失结果不得编造。",
                    "\\section{灵敏度或误差分析}",
                    "缺失结果：若无误差指标，仅写风险提示。",
                    "\\section{优缺点分析}",
                    "待人工确认：优缺点需要人工复核。",
                    "\\section{参考文献}",
                    "参考文献占位，禁止编造引用。",
                ]
            )
            + "\n",
        },
        {
            "path": "reports/CLAIM_TRACE.md",
            "purpose": "claim trace",
            "content": "| claim_id | paper_section | claim_text | evidence_source | source_quality | supporting_artifact | risk_note | status |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| C1 | 求解与实验结果 | 示例结果已生成 | local artifact | B | reports/RESULTS_REPORT.md | 人工复核 | DRAFT |\n",
        },
        {
            "path": "reports/METHOD_IMPLEMENTATION_MATRIX.md",
            "purpose": "method matrix",
            "content": "| method | implementation_file | input_data | output_artifacts | validation_status | related_claims | known_gaps |\n| --- | --- | --- | --- | --- | --- | --- |\n| demo | code/solve.py | source data | results/RESULTS_MANIFEST.json | DRAFT | C1 | 人工复核 |\n",
        },
        {
            "path": "reports/PAPER_BUILD_REPORT.md",
            "purpose": "paper build report",
            "content": "# Paper Build Report\n\n## generated paper files\n- paper/main.tex\n\n## used result artifacts\n- reports/RESULTS_REPORT.md\n\n## missing artifacts\n- none\n\n## claims generated\n- C1\n\n## unresolved risks\n- Human review required.\n\n## next human actions\n- Review draft and run Phase 4 contest review.\n",
        },
    ]


def prepare_phase3_workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "RESULTS_REPORT.md").write_text("# Results\n\nmetric=1\n", encoding="utf-8")
    (workspace / "reports" / "FIGURE_PLAN.md").write_text("# Figure Plan\n", encoding="utf-8")
    (workspace / "reports" / "FIGURE_AUDIT.md").write_text("# Figure Audit\n", encoding="utf-8")
    (workspace / "results" / "RESULTS_MANIFEST.json").write_text(
        json.dumps({"metrics": [{"name": "demo", "value": 1}], "tables": [], "figures": [], "scripts": ["code/solve.py"]}),
        encoding="utf-8",
    )
    return workspace, copy_workspace_for_run(workspace, "phase3-paper")


def test_validate_phase3_writes_accepts_allowed_paper_and_evidence_paths(tmp_path: Path) -> None:
    _workspace, run_workspace = prepare_phase3_workspace(tmp_path)

    validated = langgraph_runner.validate_phase3_writes(run_workspace, make_phase3_writes())

    assert [item["path"] for item in validated] == [
        "paper/main.tex",
        "reports/CLAIM_TRACE.md",
        "reports/METHOD_IMPLEMENTATION_MATRIX.md",
        "reports/PAPER_BUILD_REPORT.md",
    ]


@pytest.mark.parametrize(
    "bad_path",
    [
        "code/solve.py",
        "results/RESULTS_MANIFEST.json",
        "source/data.csv",
        "reports/VERIFY_REPORT.md",
        "../outside.md",
    ],
)
def test_validate_phase3_writes_rejects_forbidden_paths(tmp_path: Path, bad_path: str) -> None:
    _workspace, run_workspace = prepare_phase3_workspace(tmp_path)
    writes = make_phase3_writes()
    writes.append({"path": bad_path, "purpose": "bad", "content": "bad"})

    with pytest.raises(ValueError):
        langgraph_runner.validate_phase3_writes(run_workspace, writes)


def test_phase3_paper_sandbox_writes_allowed_files_and_evidence(tmp_path: Path) -> None:
    workspace, run_workspace = prepare_phase3_workspace(tmp_path)
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=3,
        mode="contest_graph_v2",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(3, make_phase3_writes())

    result = langgraph_runner.run_phase3_paper_sandbox(state)

    assert result["paper_sandbox_status"] == "PAPER_SANDBOX_SUCCEEDED"
    assert set(result["paper_files_written"]) >= {
        "paper/main.tex",
        "reports/CLAIM_TRACE.md",
        "reports/METHOD_IMPLEMENTATION_MATRIX.md",
        "reports/PAPER_BUILD_REPORT.md",
    }
    assert Path(result["claim_trace_path"]).name == "CLAIM_TRACE.md"
    assert Path(result["method_matrix_path"]).name == "METHOD_IMPLEMENTATION_MATRIX.md"
    assert Path(result["paper_build_report_path"]).name == "PAPER_BUILD_REPORT.md"
    assert "禁止编造引用" in (run_workspace / "paper" / "main.tex").read_text(encoding="utf-8")
    assert any(item["event"] == "langgraph_phase3_paper_sandbox" for item in read_history(workspace))


def test_phase3_paper_sandbox_rejects_illegal_batch_without_writes(tmp_path: Path) -> None:
    workspace, run_workspace = prepare_phase3_workspace(tmp_path)
    writes = make_phase3_writes()
    writes.append({"path": "code/bad.py", "purpose": "bad", "content": "bad"})
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=3,
        mode="contest_graph_v2",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(3, writes)

    result = langgraph_runner.run_phase3_paper_sandbox(state)

    assert result["paper_sandbox_status"] == "PAPER_SANDBOX_REJECTED"
    assert result["paper_files_written"] == []
    assert not (run_workspace / "paper" / "main.tex").exists()


def test_phase3_paper_sandbox_rolls_back_on_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace, run_workspace = prepare_phase3_workspace(tmp_path)
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=3,
        mode="contest_graph_v2",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(3, make_phase3_writes())
    original_writer = langgraph_runner._write_text_tracked

    def flaky_writer(state_arg, path, text):
        if path.name == "CLAIM_TRACE.md":
            raise OSError("simulated phase3 write failure")
        return original_writer(state_arg, path, text)

    monkeypatch.setattr(langgraph_runner, "_write_text_tracked", flaky_writer)

    result = langgraph_runner.run_phase3_paper_sandbox(state)

    assert result["paper_sandbox_status"] == "PAPER_SANDBOX_ROLLED_BACK"
    assert not (run_workspace / "paper" / "main.tex").exists()
    assert "simulated phase3 write failure" in result["paper_sandbox_error"]


def test_phase3_paper_sandbox_missing_manifest_writes_risk_skeleton_not_fake_results(tmp_path: Path) -> None:
    workspace, run_workspace = prepare_phase3_workspace(tmp_path)
    (run_workspace / "results" / "RESULTS_MANIFEST.json").unlink()
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=3,
        mode="contest_graph_v2",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(3, [])

    result = langgraph_runner.run_phase3_paper_sandbox(state)

    assert result["paper_sandbox_status"] == "PAPER_SANDBOX_SUCCEEDED"
    report = (run_workspace / "reports" / "PAPER_BUILD_REPORT.md").read_text(encoding="utf-8")
    paper = (run_workspace / "paper" / "README.md").read_text(encoding="utf-8")
    assert "manifest missing or empty" in report
    assert "Missing results" in paper
    assert "metric=1" not in paper


def test_contest_graph_v2_pauses_at_human_gate_without_phase2_or_phase3(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v2",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v2-pause",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["contest_status"] == "WAITING_FOR_HUMAN_MODEL_REVIEW"
    assert result["completed_phases"] == [0, 1]
    assert not (run_workspace / "CONTROL_LANGGRAPH_PHASE_2.md").exists()
    assert not (run_workspace / "CONTROL_LANGGRAPH_PHASE_3.md").exists()


def test_contest_graph_v2_runs_phase3_then_phase4_review_and_audit_only_phase6(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('reports').mkdir(exist_ok=True)\nPath('results').mkdir(exist_ok=True)\nPath('reports/RESULTS_REPORT.md').write_text('# OK\\n', encoding='utf-8')\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [{'name':'demo','value':1}], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}), encoding='utf-8')\n",
        encoding="utf-8",
    )

    class ContestV2Adapter:
        provider = "none"

        def generate(self, prompt, *_args, **_kwargs) -> str:
            match = __import__("re").search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            if phase == 2:
                plan = make_phase_plan(2, [])
                plan["commands"] = [
                    {"id": "C1", "purpose": "syntax", "command": "python -m py_compile code/solve.py", "expected_outputs": []},
                    {"id": "C2", "purpose": "run", "command": "python code/solve.py", "expected_outputs": ["results/RESULTS_MANIFEST.json", "reports/RESULTS_REPORT.md"]},
                ]
                return json.dumps(plan, ensure_ascii=False)
            if phase == 3:
                return json.dumps(make_phase_plan(3, make_phase3_writes()), ensure_ascii=False)
            if phase == 4:
                return json.dumps(
                    make_phase_plan(
                        4,
                        [
                            {"path": "reports/PAPER_SCORECARD.md", "purpose": "scorecard", "content": "# Scorecard\n"},
                            {"path": "reports/REVISION_ACTIONS.md", "purpose": "actions", "content": "# Actions\n"},
                            {"path": "reports/REFINEMENT_LOG.md", "purpose": "refinement", "content": "# Refinement\n"},
                        ],
                    ),
                    ensure_ascii=False,
                )
            return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: ContestV2Adapter())
    monkeypatch.setattr(
        langgraph_runner,
        "run_audit",
        lambda _settings, _workspace, **_kwargs: {
            "result": {"status": "PASS", "worst_severity": "NONE", "issues": []},
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        },
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v2",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v2-run",
    )

    run_workspace = Path(result["run_workspace"])
    phase3 = next(item for item in result["phase_results"] if item["phase"] == 3)
    phase4 = next(item for item in result["phase_results"] if item["phase"] == 4)
    phase6 = next(item for item in result["phase_results"] if item["phase"] == 6)

    assert phase3["paper_sandbox_status"] == "PAPER_SANDBOX_SUCCEEDED"
    assert "paper/main.tex" in phase3["paper_files_written"]
    assert "reports/PAPER_SCORECARD.md" in phase4["files_written"]
    assert phase6["strategy"] == "audit_only"
    assert result["completed_phases"] == [0, 1, 2, 3, 4, 5, 6]
    assert result["contest_status"] == "CONTEST_GRAPH_REVIEW_READY"
    assert (run_workspace / "paper" / "main.tex").is_file()
    assert (run_workspace / "reports" / "CLAIM_TRACE.md").is_file()
    assert (run_workspace / "reports" / "METHOD_IMPLEMENTATION_MATRIX.md").is_file()
    assert (run_workspace / "reports" / "PAPER_BUILD_REPORT.md").is_file()
    assert (run_workspace / "reports" / "VERIFY_REPORT.md").read_text(encoding="utf-8") == "Conclusion: PENDING\n"


def test_contest_graph_v2_marks_revision_required_after_phase4_high(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('reports').mkdir(exist_ok=True)\nPath('results').mkdir(exist_ok=True)\nPath('reports/RESULTS_REPORT.md').write_text('# OK\\n', encoding='utf-8')\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}), encoding='utf-8')\n",
        encoding="utf-8",
    )

    class RevisionAdapter:
        provider = "none"

        def generate(self, prompt, *_args, **_kwargs) -> str:
            match = __import__("re").search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            if phase == 2:
                plan = make_phase_plan(2, [])
                plan["commands"] = [{"id": "C1", "purpose": "run", "command": "python code/solve.py", "expected_outputs": []}]
                return json.dumps(plan, ensure_ascii=False)
            if phase == 3:
                return json.dumps(make_phase_plan(3, make_phase3_writes()), ensure_ascii=False)
            if phase == 4:
                return json.dumps(
                    make_phase_plan(4, [{"path": "reports/PAPER_SCORECARD.md", "purpose": "scorecard", "content": "# Scorecard\n"}]),
                    ensure_ascii=False,
                )
            return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)

    audit_calls = {"count": 0}

    def fake_audit(_settings, _workspace, **_kwargs):
        audit_calls["count"] += 1
        if audit_calls["count"] >= 8:
            return {
                "result": {
                    "status": "FAIL",
                    "worst_severity": "HIGH",
                    "issues": [{"severity": "HIGH", "code": "paper-score", "message": "needs revision"}],
                },
                "stdout": "",
                "stderr": "",
                "returncode": 1,
            }
        return {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0}

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: RevisionAdapter())
    monkeypatch.setattr(langgraph_runner, "run_audit", fake_audit)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v2",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v2-revision",
    )

    assert result["contest_status"] == "REVISION_REQUIRED"
    assert result["paused_at"] == "phase_4_review"


def make_phase5_writes() -> list[dict]:
    return [
        {
            "path": "paper/main.tex",
            "purpose": "revise paper wording",
            "content": "# Revised draft\n\nWeak claim remains marked as draft; no new metrics are introduced.\n",
        },
        {
            "path": "reports/CLAIM_TRACE.md",
            "purpose": "update claim trace",
            "content": "| claim_id | paper_section | claim_text | evidence_source | source_quality | supporting_artifact | risk_note | status |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| C1 | Results | Weak claim kept conservative | reports/RESULTS_REPORT.md | B | reports/RESULTS_REPORT.md | Human review required | REVISED_DRAFT |\n",
        },
        {
            "path": "reports/METHOD_IMPLEMENTATION_MATRIX.md",
            "purpose": "update method matrix",
            "content": "| method | implementation_file | input_data | output_artifacts | validation_status | related_claims | known_gaps |\n| --- | --- | --- | --- | --- | --- | --- |\n| demo | code/solve.py | source data | results/RESULTS_MANIFEST.json | NEEDS_HUMAN_REVIEW | C1 | verify method/result mapping |\n",
        },
        {
            "path": "reports/PAPER_BUILD_REPORT.md",
            "purpose": "update build report",
            "content": "# Paper Build Report\n\n## generated paper files\n- paper/main.tex\n\n## used result artifacts\n- reports/RESULTS_REPORT.md\n\n## missing artifacts\n- none\n\n## claims generated\n- C1\n\n## unresolved risks\n- Human review remains required.\n\n## next human actions\n- Review revision status and run final audit-only check.\n",
        },
        {
            "path": "reports/REVISION_STATUS.md",
            "purpose": "revision status",
            "content": "# Revision Status\n\n- revision_actions_exists: true\n- blocker_high_count: 1\n- unresolved_blocker_high: true\n- next_action: Human reviewer must confirm whether HIGH issue is resolved.\n",
        },
        {
            "path": "reports/REFINEMENT_LOG.md",
            "purpose": "refinement log",
            "content": "# Refinement Log\n\n- Kept claims conservative; did not fabricate metrics.\n",
        },
    ]


def prepare_phase5_workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace, run_workspace = prepare_phase3_workspace(tmp_path)
    (run_workspace / "paper" / "main.tex").write_text("# Draft\n\nOriginal weak claim.\n", encoding="utf-8")
    (run_workspace / "reports" / "PAPER_SCORECARD.md").write_text("# Scorecard\n\nHIGH: weak evidence.\n", encoding="utf-8")
    (run_workspace / "reports" / "REVISION_ACTIONS.md").write_text(
        "# Revision Actions\n\n- HIGH: weaken unsupported claim and update claim trace.\n",
        encoding="utf-8",
    )
    return workspace, run_workspace


def test_validate_phase5_writes_accepts_allowed_revision_paths(tmp_path: Path) -> None:
    _workspace, run_workspace = prepare_phase5_workspace(tmp_path)

    validated = langgraph_runner.validate_phase5_writes(run_workspace, make_phase5_writes())

    assert [item["path"] for item in validated] == [
        "paper/main.tex",
        "reports/CLAIM_TRACE.md",
        "reports/METHOD_IMPLEMENTATION_MATRIX.md",
        "reports/PAPER_BUILD_REPORT.md",
        "reports/REVISION_STATUS.md",
        "reports/REFINEMENT_LOG.md",
    ]


@pytest.mark.parametrize(
    "bad_path",
    [
        "code/solve.py",
        "results/RESULTS_MANIFEST.json",
        "source/data.csv",
        "figures/chart.png",
        "reports/VERIFY_REPORT.md",
        "reports/HUMAN_MODEL_REVIEW.md",
        "reports/MODELING_DECISION.md",
        "../outside.md",
    ],
)
def test_validate_phase5_writes_rejects_forbidden_paths(tmp_path: Path, bad_path: str) -> None:
    _workspace, run_workspace = prepare_phase5_workspace(tmp_path)
    writes = make_phase5_writes()
    writes.append({"path": bad_path, "purpose": "bad", "content": "bad"})

    with pytest.raises(ValueError):
        langgraph_runner.validate_phase5_writes(run_workspace, writes)


def test_phase5_revision_sandbox_missing_actions_writes_status_only(tmp_path: Path) -> None:
    workspace, run_workspace = prepare_phase5_workspace(tmp_path)
    (run_workspace / "reports" / "REVISION_ACTIONS.md").unlink()
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=5,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(5, make_phase5_writes())

    result = langgraph_runner.run_phase5_revision_sandbox(state)

    assert result["revision_sandbox_status"] == "NO_REVISION_ACTIONS"
    assert result["revision_files_written"] == ["reports/REVISION_STATUS.md"]
    assert (run_workspace / "reports" / "REVISION_STATUS.md").is_file()
    assert (run_workspace / "paper" / "main.tex").read_text(encoding="utf-8") == "# Draft\n\nOriginal weak claim.\n"


def test_phase5_revision_sandbox_writes_revision_status_and_allowed_files(tmp_path: Path) -> None:
    workspace, run_workspace = prepare_phase5_workspace(tmp_path)
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=5,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(5, make_phase5_writes())

    result = langgraph_runner.run_phase5_revision_sandbox(state)

    assert result["revision_sandbox_status"] == "REVISION_SANDBOX_SUCCEEDED"
    assert "paper/main.tex" in result["revision_files_written"]
    assert "reports/REVISION_STATUS.md" in result["revision_files_written"]
    assert Path(result["revision_status_path"]).name == "REVISION_STATUS.md"
    assert "no new metrics" in (run_workspace / "paper" / "main.tex").read_text(encoding="utf-8")
    assert not (run_workspace / "reports" / "HUMAN_MODEL_REVIEW.md").exists()


def test_phase5_revision_sandbox_rejects_illegal_batch_without_writes(tmp_path: Path) -> None:
    workspace, run_workspace = prepare_phase5_workspace(tmp_path)
    writes = make_phase5_writes()
    writes.append({"path": "code/bad.py", "purpose": "bad", "content": "bad"})
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=5,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(5, writes)

    result = langgraph_runner.run_phase5_revision_sandbox(state)

    assert result["revision_sandbox_status"] == "REVISION_SANDBOX_REJECTED"
    assert result["revision_files_written"] == []
    assert "Original weak claim" in (run_workspace / "paper" / "main.tex").read_text(encoding="utf-8")


def test_phase5_revision_sandbox_rolls_back_on_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace, run_workspace = prepare_phase5_workspace(tmp_path)
    state = langgraph_runner._initial_state(
        source_workspace=workspace,
        run_workspace=run_workspace,
        phase=5,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        temperature=0.2,
        max_tokens=4096,
    )
    state["phase_plan"] = make_phase_plan(5, make_phase5_writes())
    original_writer = langgraph_runner._write_text_tracked

    def flaky_writer(state_arg, path, text):
        if path.name == "REVISION_STATUS.md":
            raise OSError("simulated phase5 write failure")
        return original_writer(state_arg, path, text)

    monkeypatch.setattr(langgraph_runner, "_write_text_tracked", flaky_writer)

    result = langgraph_runner.run_phase5_revision_sandbox(state)

    assert result["revision_sandbox_status"] == "REVISION_SANDBOX_ROLLED_BACK"
    assert "simulated phase5 write failure" in result["revision_sandbox_error"]
    assert (run_workspace / "paper" / "main.tex").read_text(encoding="utf-8") == "# Draft\n\nOriginal weak claim.\n"


def test_contest_graph_v3_pauses_at_human_gate_without_phase2_or_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v3-pause",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["contest_status"] == "WAITING_FOR_HUMAN_MODEL_REVIEW"
    assert result["completed_phases"] == [0, 1]
    assert not (run_workspace / "CONTROL_LANGGRAPH_PHASE_2.md").exists()
    assert not (run_workspace / "CONTROL_LANGGRAPH_PHASE_5.md").exists()


def test_contest_graph_v3_revision_smoke_runs_to_phase6_audit_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('reports').mkdir(exist_ok=True)\nPath('results').mkdir(exist_ok=True)\nPath('reports/RESULTS_REPORT.md').write_text('# OK\\n', encoding='utf-8')\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [{'name':'demo','value':1}], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}), encoding='utf-8')\n",
        encoding="utf-8",
    )

    class ContestV3Adapter:
        provider = "none"

        def generate(self, prompt, *_args, **_kwargs) -> str:
            match = __import__("re").search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            if phase == 2:
                plan = make_phase_plan(2, [])
                plan["commands"] = [
                    {"id": "C1", "purpose": "syntax", "command": "python -m py_compile code/solve.py", "expected_outputs": []},
                    {"id": "C2", "purpose": "run", "command": "python code/solve.py", "expected_outputs": ["results/RESULTS_MANIFEST.json", "reports/RESULTS_REPORT.md"]},
                ]
                return json.dumps(plan, ensure_ascii=False)
            if phase == 3:
                return json.dumps(make_phase_plan(3, make_phase3_writes()), ensure_ascii=False)
            if phase == 4:
                return json.dumps(
                    make_phase_plan(
                        4,
                        [
                            {"path": "reports/PAPER_SCORECARD.md", "purpose": "scorecard", "content": "# Scorecard\n\nHIGH: weak claim.\n"},
                            {"path": "reports/REVISION_ACTIONS.md", "purpose": "actions", "content": "# Actions\n\n- HIGH: revise weak claim.\n"},
                            {"path": "reports/REFINEMENT_LOG.md", "purpose": "refinement", "content": "# Refinement\n"},
                        ],
                    ),
                    ensure_ascii=False,
                )
            if phase == 5:
                return json.dumps(make_phase_plan(5, make_phase5_writes()), ensure_ascii=False)
            return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: ContestV3Adapter())
    monkeypatch.setattr(
        langgraph_runner,
        "run_audit",
        lambda _settings, _workspace, **_kwargs: {
            "result": {"status": "PASS", "worst_severity": "NONE", "issues": []},
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        },
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v3-smoke",
    )

    run_workspace = Path(result["run_workspace"])
    phase5 = next(item for item in result["phase_results"] if item["phase"] == 5)
    phase6 = next(item for item in result["phase_results"] if item["phase"] == 6)

    assert result["completed_phases"] == [0, 1, 2, 3, 4, 5, 6]
    assert result["contest_status"] == "REVISION_REQUIRED"
    assert phase5["revision_sandbox_status"] == "REVISION_SANDBOX_SUCCEEDED"
    assert "reports/REVISION_STATUS.md" in phase5["revision_files_written"]
    assert phase6["strategy"] == "audit_only"
    assert (run_workspace / "reports" / "REVISION_STATUS.md").is_file()
    assert (run_workspace / "reports" / "VERIFY_REPORT.md").read_text(encoding="utf-8") == "Conclusion: PENDING\n"
    assert result["revision_sandbox_status"] == "REVISION_SANDBOX_SUCCEEDED"


def test_contest_graph_v3_missing_revision_actions_still_reaches_audit_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('reports').mkdir(exist_ok=True)\nPath('results').mkdir(exist_ok=True)\nPath('reports/RESULTS_REPORT.md').write_text('# OK\\n', encoding='utf-8')\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}), encoding='utf-8')\n",
        encoding="utf-8",
    )

    class NoRevisionActionsAdapter:
        provider = "none"

        def generate(self, prompt, *_args, **_kwargs) -> str:
            match = __import__("re").search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            if phase == 2:
                plan = make_phase_plan(2, [])
                plan["commands"] = [{"id": "C1", "purpose": "run", "command": "python code/solve.py", "expected_outputs": []}]
                return json.dumps(plan, ensure_ascii=False)
            if phase == 3:
                return json.dumps(make_phase_plan(3, make_phase3_writes()), ensure_ascii=False)
            if phase == 4:
                return json.dumps(
                    make_phase_plan(4, [{"path": "reports/PAPER_SCORECARD.md", "purpose": "scorecard", "content": "# Scorecard\n"}]),
                    ensure_ascii=False,
                )
            if phase == 5:
                return json.dumps(make_phase_plan(5, make_phase5_writes()), ensure_ascii=False)
            return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: NoRevisionActionsAdapter())
    monkeypatch.setattr(
        langgraph_runner,
        "run_audit",
        lambda _settings, _workspace, **_kwargs: {
            "result": {"status": "PASS", "worst_severity": "NONE", "issues": []},
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        },
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="contest-v3-no-actions",
    )

    phase5 = next(item for item in result["phase_results"] if item["phase"] == 5)
    phase6 = next(item for item in result["phase_results"] if item["phase"] == 6)

    assert phase5["revision_sandbox_status"] == "NO_REVISION_ACTIONS"
    assert phase6["strategy"] == "audit_only"
    assert result["contest_status"] == "NO_REVISION_ACTIONS"
