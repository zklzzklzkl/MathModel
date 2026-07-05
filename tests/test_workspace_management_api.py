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


def make_workspace(root: Path, name: str = "case") -> Path:
    workspace = root / name
    (workspace / "reports").mkdir(parents=True)
    (workspace / "WORKFLOW_STATE.md").write_text("# Workflow\n", encoding="utf-8")
    (workspace / "PROBLEM_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    return workspace


def test_workspace_activity_returns_chat_messages(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(settings.workspace_root)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        main_module,
        "run_audit",
        lambda *_args, **_kwargs: {
            "result": {"status": "FAIL", "worst_severity": "HIGH", "issues": [{"severity": "HIGH", "code": "figure_file_missing", "message": "Figure missing."}]},
            "stdout": "",
            "stderr": "",
            "returncode": 1,
        },
    )
    client = TestClient(main_module.app)

    response = client.get(f"/api/workspaces/{encode_workspace_id(workspace)}/activity")

    assert response.status_code == 200
    body = response.json()
    assert body["summary_status"] == "FAIL"
    assert body["primary_blocker"]["title"] == "figure_file_missing"
    assert any(item["kind"] == "recommendation" for item in body["messages"])


def test_archive_and_restore_workspace_under_workspace_root(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(settings.workspace_root, "to-archive")
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    client = TestClient(main_module.app)

    response = client.post(f"/api/workspaces/{encode_workspace_id(workspace)}/archive")

    assert response.status_code == 200
    archived = Path(response.json()["destination"])
    assert archived.is_dir()
    assert ".archive" in archived.parts
    assert not workspace.exists()

    response = client.post(f"/api/workspaces/{encode_workspace_id(archived)}/restore")

    assert response.status_code == 200
    assert workspace.is_dir()
    assert response.json()["workspace"]["archived"] is False


def test_examples_workspace_cannot_be_archived(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(settings.examples_root, "example-case")
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    client = TestClient(main_module.app)

    response = client.post(f"/api/workspaces/{encode_workspace_id(workspace)}/archive")

    assert response.status_code == 403
    assert "read-only" in response.json()["detail"]


def test_run_workspace_archive_moves_run_out_of_active_list(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(settings.workspace_root)
    run = make_workspace(workspace / "runs", "20260704-demo")
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    client = TestClient(main_module.app)

    runs = client.get(f"/api/workspaces/{encode_workspace_id(workspace)}/runs").json()
    run_id = runs[0]["id"]
    response = client.request(
        "DELETE",
        f"/api/workspaces/{encode_workspace_id(workspace)}/runs/{run_id}?permanent=false",
    )

    assert response.status_code == 200
    archived = Path(response.json()["destination"])
    assert archived.is_dir()
    assert not run.exists()

    runs_after = client.get(f"/api/workspaces/{encode_workspace_id(workspace)}/runs").json()
    assert all(item["name"] != "20260704-demo" for item in runs_after)


def test_run_workspace_permanent_delete_requires_exact_confirm_name(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    workspace = make_workspace(settings.workspace_root)
    run = make_workspace(workspace / "runs", "20260704-delete-me")
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    client = TestClient(main_module.app)

    run_id = client.get(f"/api/workspaces/{encode_workspace_id(workspace)}/runs").json()[0]["id"]
    response = client.request(
        "DELETE",
        f"/api/workspaces/{encode_workspace_id(workspace)}/runs/{run_id}?permanent=true&confirm_name=wrong",
    )

    assert response.status_code == 400
    assert run.is_dir()

    response = client.request(
        "DELETE",
        f"/api/workspaces/{encode_workspace_id(workspace)}/runs/{run_id}?permanent=true&confirm_name=20260704-delete-me",
    )

    assert response.status_code == 200
    assert not run.exists()
