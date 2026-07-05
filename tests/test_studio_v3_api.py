from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings  # noqa: E402
import app.main as main_module  # noqa: E402


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        mathmodel_root=REPO_ROOT,
        workspace_root=tmp_path / "workspaces",
        examples_root=tmp_path / "examples",
        python_executable=sys.executable,
    )


def make_client(tmp_path: Path, monkeypatch) -> TestClient:
    settings = make_settings(tmp_path)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setenv("MATHMODEL_STUDIO_DB", str(tmp_path / "studio.sqlite3"))
    monkeypatch.setenv("MATHMODEL_TEMPLATE_PACK_ROOT", str(tmp_path / "template_packs"))
    return TestClient(main_module.app)


def make_template_zip() -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "template.json",
            json.dumps(
                {
                    "id": "cumcm-standard-latex",
                    "name": "CUMCM Standard LaTeX",
                    "contest": "cumcm",
                    "language": "zh",
                    "engine": "latex",
                    "main_file": "main.tex",
                    "description": "Contest paper template.",
                    "required_files": ["main.tex", "cumcmthesis.cls"],
                    "preview_file": "",
                },
                ensure_ascii=False,
            ),
        )
        archive.writestr("main.tex", "\\documentclass{cumcmthesis}\\begin{document}Hi\\end{document}")
        archive.writestr("cumcmthesis.cls", "\\NeedsTeXFormat{LaTeX2e}")
    payload.seek(0)
    return payload.read()


def test_studio_project_run_events_and_gate_write_v2_artifacts(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/projects",
        json={"name": "国赛 C 题", "domain": "math_modeling", "contest": "CUMCM"},
    )

    assert response.status_code == 200
    project = response.json()
    workspace = Path(project["workspace_path"])
    assert (workspace / "reports").is_dir()
    projects = client.get("/api/projects")
    assert projects.status_code == 200
    assert any(item["id"] == project["id"] for item in projects.json()["projects"])

    upload = client.post(
        f"/api/projects/{project['id']}/files",
        files=[("files", ("problem.pdf", b"problem statement", "application/pdf"))],
    )
    assert upload.status_code == 200
    assert upload.json()["saved"] == ["source/problem.pdf"]

    file_index = client.get(f"/api/projects/{project['id']}/files")
    assert file_index.status_code == 200
    indexed_files = file_index.json()["files"]
    assert any(item["path"] == "source/problem.pdf" and item["type"] == "source" for item in indexed_files)

    response = client.post("/api/runs", json={"project_id": project["id"], "driver": "langgraph"})

    assert response.status_code == 200
    run = response.json()
    assert run["driver"] == "langgraph"
    assert run["status"] in {"paused", "running", "completed"}
    run_detail = client.get(f"/api/runs/{run['id']}")
    assert run_detail.status_code == 200
    assert run_detail.json()["id"] == run["id"]

    canceled = client.post(f"/api/runs/{run['id']}/cancel")
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "canceled"

    resumed = client.post(f"/api/runs/{run['id']}/resume")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "running"

    events = client.get(f"/api/runs/{run['id']}/events").json()["events"]
    assert events
    assert events[0]["run_id"] == run["id"]
    assert any(event["type"] == "human_gate_required" for event in events)

    stream = client.get(f"/api/runs/{run['id']}/events/stream?replay_only=1")
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "event: run_event" in stream.text

    gate = client.get(f"/api/gates/{run['id']}/current").json()
    assert gate["type"] == "human_model_review"
    assert gate["status"] == "required"
    previews = {item["path"]: item for item in gate["artifact_previews"]}
    assert set(previews) == {
        "reports/MODEL_CANDIDATES.md",
        "reports/MODEL_REVIEW_AI.md",
        "reports/FIGURE_PLAN.md",
    }
    assert "Route A" in previews["reports/MODEL_CANDIDATES.md"]["content"]
    assert "risk" in previews["reports/MODEL_REVIEW_AI.md"]["content"].lower()
    assert "figure" in previews["reports/FIGURE_PLAN.md"]["content"].lower()
    for relative in previews:
        assert (workspace / relative).is_file()

    response = client.post(
        f"/api/gates/{run['id']}/{gate['id']}/submit",
        json={
            "decision": "approved",
            "selected_route": "方案 A",
            "human_notes": "批准方案 A，保留风险记录。",
            "ai_notes": "建议补充灵敏度分析。",
        },
    )

    assert response.status_code == 200
    assert response.json()["approved"] is True
    review = workspace / "reports" / "HUMAN_MODEL_REVIEW.md"
    decision = workspace / "reports" / "MODELING_DECISION.md"
    assert "approved" in review.read_text(encoding="utf-8")
    assert "方案 A" in decision.read_text(encoding="utf-8")

    artifact = client.get(
        f"/api/projects/{project['id']}/artifacts/read",
        params={"path": "reports/MODELING_DECISION.md"},
    )
    assert artifact.status_code == 200
    body = artifact.json()
    assert body["path"] == "reports/MODELING_DECISION.md"
    assert body["type"] == "report"
    assert "approved" in body["content"]

    unsafe_artifact = client.get(
        f"/api/projects/{project['id']}/artifacts/read",
        params={"path": "../.env"},
    )
    assert unsafe_artifact.status_code == 400


def test_model_config_exposes_stage_defaults_and_accepts_updates(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)

    response = client.get("/api/models/config")

    assert response.status_code == 200
    config = response.json()
    stages = {stage["stage"]: stage for stage in config["stages"]}
    assert stages["model_strategy"]["temperature"] == 0.5
    assert stages["code_generation"]["temperature"] == 0.15
    assert stages["debug"]["temperature"] == 0.05

    response = client.put(
        "/api/models/config",
        json={
            "preset": "award",
            "providers": [{"id": "deepseek", "label": "DeepSeek", "enabled": True, "api_key_status": "detected"}],
            "stages": [
                {
                    "stage": "paper_writing",
                    "provider": "deepseek",
                    "model": "deepseek-chat",
                    "temperature": 0.42,
                    "max_tokens": 8192,
                    "timeout_sec": 600,
                    "retry_count": 2,
                    "context_budget": 24000,
                    "parallel_agents": 1,
                }
            ],
        },
    )

    assert response.status_code == 200
    updated = {stage["stage"]: stage for stage in response.json()["stages"]}
    assert updated["paper_writing"]["temperature"] == 0.42
    assert updated["paper_writing"]["model"] == "deepseek-chat"

    none_check = client.post("/api/models/test-connection", json={"provider": "none"})
    assert none_check.status_code == 200
    assert none_check.json()["ok"] is True
    assert none_check.json()["latency_ms"] == 0

    missing_key = client.post("/api/models/test-connection", json={"provider": "deepseek"})
    assert missing_key.status_code == 200
    assert missing_key.json()["ok"] is False

    openai_no_url = client.post("/api/models/test-connection", json={"provider": "openai-compatible"})
    assert openai_no_url.status_code == 200
    assert openai_no_url.json()["ok"] is False
    assert "base_url" in openai_no_url.json()["message"]


def test_template_pack_upload_preview_download_and_delete(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    zip_bytes = make_template_zip()

    response = client.post(
        "/api/templates/upload",
        files={"file": ("cumcm-template.zip", zip_bytes, "application/zip")},
    )

    assert response.status_code == 200
    template = response.json()
    assert template["id"] == "cumcm-standard-latex"
    assert template["contest"] == "cumcm"
    assert template["main_file"] == "main.tex"
    assert template["warnings"] == []

    templates = client.get("/api/templates").json()["templates"]
    assert any(item["id"] == "cumcm-standard-latex" for item in templates)

    preview = client.get("/api/templates/cumcm-standard-latex/preview")
    assert preview.status_code == 200
    assert "documentclass" in preview.json()["content"]

    download = client.get("/api/templates/cumcm-standard-latex/download")
    assert download.status_code == 200
    assert download.headers["content-type"] in {"application/zip", "application/x-zip-compressed"}

    delete_response = client.delete("/api/templates/cumcm-standard-latex")
    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True


def test_builtin_templates_can_be_imported_from_existing_skill_library(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)

    response = client.post("/api/templates/import-builtin")

    assert response.status_code == 200
    result = response.json()
    assert result["imported_count"] >= 10
    assert any(item["contest"] == "cumcm" and item["engine"] == "latex" for item in result["templates"])

    templates = client.get("/api/templates").json()["templates"]
    cumcm = next(item for item in templates if item["contest"] == "cumcm" and item["engine"] == "latex")
    preview = client.get(f"/api/templates/{cumcm['id']}/preview")
    assert preview.status_code == 200
    assert "\\documentclass" in preview.json()["content"] or "#import" in preview.json()["content"]


def test_template_upload_rejects_zip_without_main_file(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("notes.txt", "missing template")
    payload.seek(0)

    response = client.post(
        "/api/templates/upload",
        files={"file": ("bad.zip", payload.read(), "application/zip")},
    )

    assert response.status_code == 400
    assert "main.tex or main.typ" in response.json()["detail"]


def test_template_metadata_cannot_write_outside_template_root(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "template.json",
            json.dumps(
                {
                    "id": "../escape-template",
                    "name": "Unsafe Template",
                    "contest": "../escape-contest",
                    "main_file": "main.tex",
                    "preview_file": "../preview.pdf",
                    "required_files": ["main.tex", "../escape.sty"],
                }
            ),
        )
        archive.writestr("main.tex", "\\documentclass{article}\\begin{document}x\\end{document}")
    payload.seek(0)

    response = client.post(
        "/api/templates/upload",
        files={"file": ("unsafe-template.zip", payload, "application/zip")},
    )

    assert response.status_code == 400
    assert "unsafe" in response.json()["detail"].lower()
    assert not (tmp_path / "templates" / "escape-contest").exists()
    assert not (tmp_path / "escape-contest").exists()
