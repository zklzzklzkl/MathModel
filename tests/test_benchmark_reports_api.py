"""Read-only benchmark report browser API tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402

client = TestClient(app)


def test_list_reports_returns_200():
    resp = client.get("/api/benchmark-reports")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for item in data:
        assert "id" in item
        assert "title" in item
        assert "path" in item
        assert item["type"] in ("markdown", "json")
        assert "category" in item


def test_list_reports_are_under_docs():
    resp = client.get("/api/benchmark-reports")
    data = resp.json()
    for item in data:
        path = item["path"]
        assert path.startswith("docs/"), f"Report path must be under docs/: {path}"
        assert "workspaces/" not in path
        assert ".env" not in path
        assert "source/" not in path
        assert "knowledge/raw/" not in path


def test_no_path_traversal_via_report_id():
    """report_id is a SHA256 hash, not a filesystem path. ../ cannot resolve."""
    resp = client.get("/api/benchmark-reports/%2e%2e%2f.env")
    assert resp.status_code in (404, 403)

    resp = client.get("/api/benchmark-reports/..%2F.env")
    assert resp.status_code in (404, 403)


def test_no_workspace_data_leaked():
    """Benchmark reports must not include workspace files."""
    resp = client.get("/api/benchmark-reports")
    data = resp.json()
    for item in data:
        path = item["path"]
        assert "workspaces" not in path.lower()
        assert "knowledge" not in path.lower()


def test_read_markdown_report():
    resp = client.get("/api/benchmark-reports")
    data = resp.json()
    md_items = [item for item in data if item["type"] == "markdown"]
    if not md_items:
        return
    report_id = md_items[0]["id"]
    resp = client.get(f"/api/benchmark-reports/{report_id}")
    assert resp.status_code == 200
    read = resp.json()
    assert read["id"] == report_id
    assert read["type"] == "markdown"
    assert isinstance(read["content"], str)
    assert len(read["content"]) > 0
    assert read["data"] is None


def test_read_json_report():
    resp = client.get("/api/benchmark-reports")
    data = resp.json()
    json_items = [item for item in data if item["type"] == "json"]
    if not json_items:
        return
    report_id = json_items[0]["id"]
    resp = client.get(f"/api/benchmark-reports/{report_id}")
    assert resp.status_code == 200
    read = resp.json()
    assert read["id"] == report_id
    assert read["type"] == "json"
    assert isinstance(read["content"], str)
    if isinstance(read["content"], str):
        try:
            json.loads(read["content"])
        except json.JSONDecodeError as exc:
            raise AssertionError(f"JSON report content is invalid: {exc}") from exc
    assert isinstance(read["summary"], dict)


def test_nonexistent_report_returns_404():
    resp = client.get("/api/benchmark-reports/nonexistent123")
    assert resp.status_code == 404


def test_path_traversal_rejected():
    resp = client.get("/api/benchmark-reports/../foo")
    assert resp.status_code in (404, 403)


def test_api_is_read_only():
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        resp = getattr(client, method.lower())("/api/benchmark-reports")
        assert resp.status_code in (405, 404, 403), f"{method} should be rejected"


def test_legacy_benchmark_still_works():
    resp = client.get("/api/benchmark/2022C")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data


def test_no_env_file_in_reports():
    """Ensure no .env or private files appear in report list."""
    resp = client.get("/api/benchmark-reports")
    data = resp.json()
    for item in data:
        assert ".env" not in item["path"]
        assert "hackingtosh" not in item["path"].lower()
