from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[3]


def configure_env(tmp_path: Path) -> None:
    os.environ["MATHMODEL_ROOT"] = str(REPO_ROOT)
    os.environ["WORKSPACE_ROOT"] = str(tmp_path / "workspaces")
    os.environ["EXAMPLES_ROOT"] = str(REPO_ROOT / "examples")


def test_health_reports_scripts(tmp_path: Path) -> None:
    configure_env(tmp_path)
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["scripts"]["audit"]["exists"] is True
    assert body["scripts"]["scaffold"]["exists"] is True


def test_create_workspace_and_read_artifact(tmp_path: Path) -> None:
    configure_env(tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/workspaces",
        json={
            "name": "demo",
            "contest": "CUMCM",
            "engine": "LaTeX",
            "language": "中文",
            "subproblems": "3",
            "figure_backend": "matplotlib",
            "nature": "not_requested",
        },
    )

    assert response.status_code == 200
    workspace_id = response.json()["workspace"]["id"]
    artifact = client.get(f"/api/workspaces/{workspace_id}/artifact", params={"path": "WORKFLOW_STATE.md"})
    assert artifact.status_code == 200
    assert artifact.json()["exists"] is True
    assert "current_stage" in artifact.json()["content"]

    duplicate = client.post("/api/workspaces", json={"name": "demo"})
    assert duplicate.status_code == 409


def test_prompt_and_audit_for_created_workspace(tmp_path: Path) -> None:
    configure_env(tmp_path)
    client = TestClient(app)
    created = client.post("/api/workspaces", json={"name": "audit-demo"})
    workspace_id = created.json()["workspace"]["id"]

    prompt = client.post(f"/api/workspaces/{workspace_id}/prompt", json={"phase": 2, "harness": "Manual"})
    assert prompt.status_code == 200
    assert "mm-data-experiment" in prompt.json()["prompt"]

    audit = client.post(f"/api/workspaces/{workspace_id}/audit")
    assert audit.status_code == 200
    assert "result" in audit.json()

    history = client.get(f"/api/workspaces/{workspace_id}/runs/history")
    assert history.status_code == 200
    assert any(item["event"] == "prompt_generated" for item in history.json())


def test_workspace_list_includes_created_workspace(tmp_path: Path) -> None:
    configure_env(tmp_path)
    client = TestClient(app)
    client.post("/api/workspaces", json={"name": "listed"})

    response = client.get("/api/workspaces")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert "listed" in names


def test_upload_source_and_revision_tasks(tmp_path: Path) -> None:
    configure_env(tmp_path)
    client = TestClient(app)
    created = client.post("/api/workspaces", json={"name": "upload-demo"})
    workspace_id = created.json()["workspace"]["id"]

    upload = client.post(
        f"/api/workspaces/{workspace_id}/source-files",
        files={"files": ("problem.txt", b"problem statement", "text/plain")},
    )
    assert upload.status_code == 200
    assert upload.json()["saved"] == ["source/problem.txt"]

    tasks = client.post(f"/api/workspaces/{workspace_id}/revision-tasks")
    assert tasks.status_code == 200
    assert "tasks" in tasks.json()
    written_path = tasks.json()["written_path"]
    assert written_path and Path(written_path).is_file()


def test_harness_prepare_creates_safe_copy(tmp_path: Path) -> None:
    configure_env(tmp_path)
    client = TestClient(app)
    created = client.post("/api/workspaces", json={"name": "adapter-demo"})
    workspace_id = created.json()["workspace"]["id"]

    harnesses = client.get("/api/harnesses")
    assert harnesses.status_code == 200
    assert {item["id"] for item in harnesses.json()} >= {"Manual", "Codex", "Claude Code", "OpenCode"}

    prepared = client.post(
        f"/api/workspaces/{workspace_id}/harness/prepare",
        json={"phase": 2, "harness": "Manual", "copy_workspace": True, "run_name": "safe"},
    )
    assert prepared.status_code == 200
    body = prepared.json()
    assert body["copied"] is True
    assert Path(body["run_workspace"]).is_dir()
    assert Path(body["prompt_path"]).is_file()
    assert "mm-data-experiment" in body["prompt"]
