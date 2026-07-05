from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings  # noqa: E402
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
    workspace = tmp_path / "workspaces" / "case-gate"
    (workspace / "reports").mkdir(parents=True)
    (workspace / "WORKFLOW_STATE.md").write_text("# Workflow\n", encoding="utf-8")
    (workspace / "PROBLEM_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (workspace / "reports" / "MODEL_CANDIDATES.md").write_text("# Candidates\n\nUse baseline + robust model.\n", encoding="utf-8")
    (workspace / "reports" / "MODEL_REVIEW_AI.md").write_text("# Review\n\nHIGH: validation is weak.\n", encoding="utf-8")
    (workspace / "reports" / "FIGURE_PLAN.md").write_text("# Figures\n\nClaim -> Figure.\n", encoding="utf-8")
    return workspace


def test_human_gate_summary_surfaces_risks(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    client = TestClient(main_module.app)

    response = client.get(f"/api/workspaces/{encode_workspace_id(workspace)}/human-gate/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is False
    assert body["approved"] is False
    assert "Candidates" in body["model_candidates_excerpt"]
    assert any("HIGH" in item for item in body["risks"])


def test_human_gate_chat_does_not_write_review_file(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    client = TestClient(main_module.app)

    response = client.post(
        f"/api/workspaces/{encode_workspace_id(workspace)}/human-gate/chat",
        json={"question": "这个模型路线有什么风险？"},
    )

    assert response.status_code == 200
    assert "不会替你自动批准" in response.json()["answer"]
    assert not (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").exists()


def test_human_gate_review_writes_approval_only_on_explicit_approved(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    client = TestClient(main_module.app)

    response = client.put(
        f"/api/workspaces/{encode_workspace_id(workspace)}/human-gate/review",
        json={"decision": "needs_revision", "human_notes": "先补 baseline 对比。", "ai_notes": "建议保守。"},
    )

    assert response.status_code == 200
    text = (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").read_text(encoding="utf-8")
    assert "needs_revision" in text
    assert "approved" not in text.split("## Decision", 1)[1].split("##", 1)[0]

    response = client.put(
        f"/api/workspaces/{encode_workspace_id(workspace)}/human-gate/review",
        json={"decision": "approved", "human_notes": "同意采用当前路线。", "ai_notes": "风险已记录。"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["approved"] is True
    text = (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").read_text(encoding="utf-8")
    assert "approved" in text
