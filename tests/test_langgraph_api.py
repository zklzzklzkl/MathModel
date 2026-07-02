from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings  # noqa: E402
from app.langgraph_runner import LangGraphUnavailableError  # noqa: E402
from app.model_adapters import ModelAdapterError  # noqa: E402
from app.workspace import encode_workspace_id  # noqa: E402
import app.main as main_module  # noqa: E402


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        mathmodel_root=REPO_ROOT,
        workspace_root=tmp_path / "workspaces",
        examples_root=tmp_path / "examples",
        python_executable=sys.executable,
    )


def make_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspaces" / "case-api"
    (workspace / "reports").mkdir(parents=True)
    (workspace / "WORKFLOW_STATE.md").write_text("# Workflow State\n", encoding="utf-8")
    (workspace / "PROBLEM_BRIEF.md").write_text("# Problem Brief\n", encoding="utf-8")
    return workspace


def test_langgraph_status_endpoint_reports_optional_dependency(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        main_module,
        "langgraph_status",
        lambda: {
            "available": False,
            "version": None,
            "import_error": "No module named 'langgraph'",
            "note": "Install optional dependencies with: pip install -r app/backend/requirements-langgraph.txt",
        },
    )
    client = TestClient(main_module.app)

    response = client.get("/api/langgraph/status")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert "requirements-langgraph.txt" in body["note"]


def test_langgraph_run_endpoint_returns_501_when_dependency_missing(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def raise_unavailable(**_kwargs):
        raise LangGraphUnavailableError(
            "LangGraph is not installed. Install with: pip install -r app/backend/requirements-langgraph.txt"
        )

    monkeypatch.setattr(main_module, "run_langgraph_phase", raise_unavailable)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 1, "mode": "dry_run"},
    )

    assert response.status_code == 501
    assert "requirements-langgraph.txt" in response.json()["detail"]


def test_langgraph_run_endpoint_accepts_llm_plan_mode(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def fake_run_langgraph_phase(**kwargs):
        return {
            "source_workspace": str(workspace),
            "run_workspace": str(workspace / "runs" / "fake-run"),
            "phase": kwargs["phase"],
            "mode": kwargs["mode"],
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "status": "PLAN_READY",
            "prompt_path": str(workspace / "runs" / "fake-run" / "CONTROL_LANGGRAPH_PHASE_1.md"),
            "report_path": str(workspace / "runs" / "fake-run" / "reports" / "LANGGRAPH_RUN_REPORT.md"),
            "pre_audit": {"status": "FAIL"},
            "post_audit": {"status": "FAIL"},
            "issues": [],
            "history": {"event": "langgraph_phase_llm_plan"},
            "phase_plan": {"phase": 1, "phase_name": "model strategy"},
            "provider_error": None,
            "plan_path": str(workspace / "runs" / "fake-run" / "reports" / "LANGGRAPH_PHASE_PLAN.json"),
            "plan_markdown_path": str(workspace / "runs" / "fake-run" / "reports" / "LANGGRAPH_PHASE_PLAN.md"),
            "raw_output_path": None,
        }

    monkeypatch.setattr(main_module, "run_langgraph_phase", fake_run_langgraph_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={
            "phase": 1,
            "mode": "llm_plan",
            "provider": "none",
            "temperature": 0.1,
            "max_tokens": 2048,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "llm_plan"
    assert body["status"] == "PLAN_READY"
    assert body["phase_plan"]["phase"] == 1
    assert body["plan_path"].endswith("LANGGRAPH_PHASE_PLAN.json")


def test_langgraph_run_endpoint_returns_400_for_provider_error(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def raise_provider_error(**_kwargs):
        raise ModelAdapterError("MATHMODEL_LLM_API_KEY is required for OpenAI-compatible providers.")

    monkeypatch.setattr(main_module, "run_langgraph_phase", raise_provider_error)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 1, "mode": "llm_plan", "provider": "deepseek", "model": "deepseek-chat"},
    )

    assert response.status_code == 400
    assert "MATHMODEL_LLM_API_KEY" in response.json()["detail"]


def test_langgraph_run_endpoint_accepts_controlled_apply_mode(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def fake_run_langgraph_phase(**kwargs):
        return {
            "source_workspace": str(workspace),
            "run_workspace": str(workspace / "runs" / "fake-apply"),
            "phase": kwargs["phase"],
            "mode": kwargs["mode"],
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "status": "APPLY_READY_FOR_HUMAN_REVIEW",
            "prompt_path": str(workspace / "runs" / "fake-apply" / "CONTROL_LANGGRAPH_PHASE_1.md"),
            "report_path": str(workspace / "runs" / "fake-apply" / "reports" / "LANGGRAPH_RUN_REPORT.md"),
            "pre_audit": {"status": "FAIL"},
            "post_audit": {"status": "FAIL"},
            "issues": [],
            "history": {"event": "langgraph_phase_controlled_apply"},
            "phase_plan": {"phase": 1, "phase_name": "model strategy"},
            "provider_error": None,
            "plan_path": str(workspace / "runs" / "fake-apply" / "reports" / "LANGGRAPH_PHASE_PLAN.json"),
            "plan_markdown_path": str(workspace / "runs" / "fake-apply" / "reports" / "LANGGRAPH_PHASE_PLAN.md"),
            "raw_output_path": None,
            "files_planned": ["reports/MODEL_CANDIDATES.md"],
            "files_written": ["reports/MODEL_CANDIDATES.md"],
            "files_rejected": [],
            "needs_human": True,
        }

    monkeypatch.setattr(main_module, "run_langgraph_phase", fake_run_langgraph_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 1, "mode": "controlled_apply", "provider": "none"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "controlled_apply"
    assert body["files_written"] == ["reports/MODEL_CANDIDATES.md"]
    assert body["needs_human"] is True


def test_langgraph_run_endpoint_returns_400_for_controlled_apply_bad_phase(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def raise_bad_phase(**_kwargs):
        raise ValueError("controlled_apply only supports phase 1 and phase 4.")

    monkeypatch.setattr(main_module, "run_langgraph_phase", raise_bad_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 2, "mode": "controlled_apply", "provider": "none"},
    )

    assert response.status_code == 400
    assert "phase 1 and phase 4" in response.json()["detail"]


def test_langgraph_run_endpoint_accepts_phase_execute_mode(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def fake_run_langgraph_phase(**kwargs):
        return {
            "source_workspace": str(workspace),
            "run_workspace": str(workspace / "runs" / "fake-execute"),
            "phase": kwargs["phase"],
            "mode": kwargs["mode"],
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "status": "APPLY_PLAN_ONLY",
            "prompt_path": str(workspace / "runs" / "fake-execute" / "CONTROL_LANGGRAPH_PHASE_1.md"),
            "report_path": str(workspace / "runs" / "fake-execute" / "reports" / "LANGGRAPH_RUN_REPORT.md"),
            "pre_audit": {"status": "FAIL"},
            "post_audit": {"status": "FAIL"},
            "issues": [],
            "history": {"event": "langgraph_phase_execute"},
            "phase_plan": {"phase": 1, "phase_name": "model strategy"},
            "provider_error": None,
            "plan_path": str(workspace / "runs" / "fake-execute" / "reports" / "LANGGRAPH_PHASE_PLAN.json"),
            "plan_markdown_path": str(workspace / "runs" / "fake-execute" / "reports" / "LANGGRAPH_PHASE_PLAN.md"),
            "raw_output_path": None,
            "apply_diff_path": str(workspace / "runs" / "fake-execute" / "reports" / "LANGGRAPH_APPLY_DIFF.md"),
            "files_planned": [],
            "files_written": [],
            "files_rejected": [],
            "needs_human": True,
        }

    monkeypatch.setattr(main_module, "run_langgraph_phase", fake_run_langgraph_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 1, "mode": "phase_execute", "provider": "none"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "phase_execute"
    assert body["apply_diff_path"].endswith("LANGGRAPH_APPLY_DIFF.md")
    assert body["needs_human"] is True


def test_langgraph_run_endpoint_returns_400_for_phase_execute_bad_phase(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def raise_bad_phase(**_kwargs):
        raise ValueError("PHASE_NOT_SUPPORTED: phase_execute only supports phase 1 and phase 4.")

    monkeypatch.setattr(main_module, "run_langgraph_phase", raise_bad_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 2, "mode": "phase_execute", "provider": "none"},
    )

    assert response.status_code == 400
    assert "PHASE_NOT_SUPPORTED" in response.json()["detail"]


def test_langgraph_run_endpoint_accepts_contest_graph_v0_mode(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def fake_run_langgraph_phase(**kwargs):
        return {
            "source_workspace": str(workspace),
            "run_workspace": str(workspace / "runs" / "fake-contest"),
            "phase": kwargs["phase"],
            "mode": kwargs["mode"],
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "status": "WAITING_FOR_HUMAN_MODEL_REVIEW",
            "prompt_path": None,
            "report_path": str(workspace / "runs" / "fake-contest" / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"),
            "pre_audit": {"status": "FAIL"},
            "post_audit": {"status": "FAIL"},
            "issues": [],
            "history": {"event": "langgraph_contest_graph_v0"},
            "phase_plan": None,
            "provider_error": None,
            "plan_path": None,
            "plan_markdown_path": None,
            "raw_output_path": None,
            "apply_diff_path": None,
            "files_planned": [],
            "files_written": [],
            "files_rejected": [],
            "needs_human": True,
            "contest_status": "WAITING_FOR_HUMAN_MODEL_REVIEW",
            "completed_phases": [0, 1],
            "paused_at": "phase_1_human_gate",
            "human_gate_required": True,
            "human_gate_file": "reports/HUMAN_MODEL_REVIEW.md",
            "graph_report_path": str(workspace / "runs" / "fake-contest" / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"),
            "phase_results": [{"phase": 0, "mode": "llm_plan"}, {"phase": 1, "mode": "phase_execute"}],
            "final_audit": {},
        }

    monkeypatch.setattr(main_module, "run_langgraph_phase", fake_run_langgraph_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 0, "mode": "contest_graph_v0", "provider": "none"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "contest_graph_v0"
    assert body["contest_status"] == "WAITING_FOR_HUMAN_MODEL_REVIEW"
    assert body["completed_phases"] == [0, 1]
    assert body["paused_at"] == "phase_1_human_gate"
    assert body["human_gate_required"] is True
    assert body["human_gate_file"] == "reports/HUMAN_MODEL_REVIEW.md"
    assert body["graph_report_path"].endswith("LANGGRAPH_CONTEST_GRAPH_REPORT.md")
    assert body["phase_results"][1]["mode"] == "phase_execute"


def test_langgraph_run_endpoint_accepts_contest_graph_v1_mode(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def fake_run_langgraph_phase(**kwargs):
        return {
            "source_workspace": str(workspace),
            "run_workspace": str(workspace / "runs" / "fake-contest-v1"),
            "phase": kwargs["phase"],
            "mode": kwargs["mode"],
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "status": "CONTEST_GRAPH_REVIEW_READY",
            "prompt_path": None,
            "report_path": str(workspace / "runs" / "fake-contest-v1" / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"),
            "pre_audit": {"status": "FAIL"},
            "post_audit": {"status": "FAIL"},
            "issues": [],
            "history": {"event": "langgraph_contest_graph_v1"},
            "phase_plan": None,
            "provider_error": None,
            "plan_path": None,
            "plan_markdown_path": None,
            "raw_output_path": None,
            "apply_diff_path": None,
            "files_planned": [],
            "files_written": [],
            "files_rejected": [],
            "needs_human": True,
            "contest_status": "CONTEST_GRAPH_REVIEW_READY",
            "completed_phases": [0, 1, 2, 3, 4, 5, 6],
            "paused_at": None,
            "human_gate_required": False,
            "human_gate_file": "reports/HUMAN_MODEL_REVIEW.md",
            "graph_report_path": str(workspace / "runs" / "fake-contest-v1" / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"),
            "phase_results": [{"phase": 2, "mode": "phase2_sandbox", "sandbox_status": "SANDBOX_SUCCEEDED"}],
            "final_audit": {},
            "sandbox_commands": [{"id": "C1", "status": "SUCCEEDED"}],
            "sandbox_status": "SANDBOX_SUCCEEDED",
            "manifest_created_empty": False,
        }

    monkeypatch.setattr(main_module, "run_langgraph_phase", fake_run_langgraph_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 0, "mode": "contest_graph_v1", "provider": "none"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "contest_graph_v1"
    assert body["sandbox_status"] == "SANDBOX_SUCCEEDED"
    assert body["sandbox_commands"][0]["status"] == "SUCCEEDED"
    assert body["manifest_created_empty"] is False


def test_langgraph_run_endpoint_accepts_contest_graph_v2_mode(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def fake_run_langgraph_phase(**kwargs):
        return {
            "source_workspace": str(workspace),
            "run_workspace": str(workspace / "runs" / "fake-contest-v2"),
            "phase": kwargs["phase"],
            "mode": kwargs["mode"],
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "status": "CONTEST_GRAPH_REVIEW_READY",
            "prompt_path": None,
            "report_path": str(workspace / "runs" / "fake-contest-v2" / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"),
            "pre_audit": {"status": "PASS"},
            "post_audit": {"status": "PASS"},
            "issues": [],
            "history": {"event": "langgraph_contest_graph_v2"},
            "phase_plan": None,
            "provider_error": None,
            "plan_path": None,
            "plan_markdown_path": None,
            "raw_output_path": None,
            "apply_diff_path": None,
            "files_planned": [],
            "files_written": [],
            "files_rejected": [],
            "needs_human": True,
            "contest_status": "CONTEST_GRAPH_REVIEW_READY",
            "completed_phases": [0, 1, 2, 3, 4, 5, 6],
            "paused_at": None,
            "human_gate_required": False,
            "human_gate_file": "reports/HUMAN_MODEL_REVIEW.md",
            "graph_report_path": str(workspace / "runs" / "fake-contest-v2" / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"),
            "phase_results": [{"phase": 3, "mode": "phase3_paper_sandbox", "paper_sandbox_status": "PAPER_SANDBOX_SUCCEEDED"}],
            "final_audit": {},
            "paper_sandbox_status": "PAPER_SANDBOX_SUCCEEDED",
            "paper_files_written": ["paper/main.tex", "reports/CLAIM_TRACE.md"],
            "claim_trace_path": str(workspace / "runs" / "fake-contest-v2" / "reports" / "CLAIM_TRACE.md"),
            "method_matrix_path": str(workspace / "runs" / "fake-contest-v2" / "reports" / "METHOD_IMPLEMENTATION_MATRIX.md"),
            "paper_build_report_path": str(workspace / "runs" / "fake-contest-v2" / "reports" / "PAPER_BUILD_REPORT.md"),
        }

    monkeypatch.setattr(main_module, "run_langgraph_phase", fake_run_langgraph_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 0, "mode": "contest_graph_v2", "provider": "none"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "contest_graph_v2"
    assert body["paper_sandbox_status"] == "PAPER_SANDBOX_SUCCEEDED"
    assert body["paper_files_written"] == ["paper/main.tex", "reports/CLAIM_TRACE.md"]
    assert body["claim_trace_path"].endswith("CLAIM_TRACE.md")
    assert body["method_matrix_path"].endswith("METHOD_IMPLEMENTATION_MATRIX.md")
    assert body["paper_build_report_path"].endswith("PAPER_BUILD_REPORT.md")


def test_langgraph_run_endpoint_accepts_contest_graph_v3_mode(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)

    def fake_run_langgraph_phase(**kwargs):
        return {
            "source_workspace": str(workspace),
            "run_workspace": str(workspace / "runs" / "fake-contest-v3"),
            "phase": kwargs["phase"],
            "mode": kwargs["mode"],
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "status": "REVISION_REQUIRED",
            "prompt_path": None,
            "report_path": str(workspace / "runs" / "fake-contest-v3" / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"),
            "pre_audit": {"status": "PASS"},
            "post_audit": {"status": "PASS"},
            "issues": [],
            "history": {"event": "langgraph_contest_graph_v3"},
            "phase_plan": None,
            "provider_error": None,
            "plan_path": None,
            "plan_markdown_path": None,
            "raw_output_path": None,
            "apply_diff_path": None,
            "files_planned": [],
            "files_written": [],
            "files_rejected": [],
            "needs_human": True,
            "contest_status": "REVISION_REQUIRED",
            "completed_phases": [0, 1, 2, 3, 4, 5, 6],
            "paused_at": None,
            "human_gate_required": False,
            "human_gate_file": "reports/HUMAN_MODEL_REVIEW.md",
            "graph_report_path": str(workspace / "runs" / "fake-contest-v3" / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"),
            "phase_results": [{"phase": 5, "mode": "phase5_revision_sandbox", "revision_sandbox_status": "REVISION_SANDBOX_SUCCEEDED"}],
            "final_audit": {},
            "revision_sandbox_status": "REVISION_SANDBOX_SUCCEEDED",
            "revision_files_written": ["reports/REVISION_STATUS.md"],
            "revision_status_path": str(workspace / "runs" / "fake-contest-v3" / "reports" / "REVISION_STATUS.md"),
        }

    monkeypatch.setattr(main_module, "run_langgraph_phase", fake_run_langgraph_phase)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/langgraph/run",
        json={"phase": 0, "mode": "contest_graph_v3", "provider": "none"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "contest_graph_v3"
    assert body["revision_sandbox_status"] == "REVISION_SANDBOX_SUCCEEDED"
    assert body["revision_files_written"] == ["reports/REVISION_STATUS.md"]
    assert body["revision_status_path"].endswith("REVISION_STATUS.md")
