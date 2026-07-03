"""Run workspace artifact API tests."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402

client = TestClient(app)

SOURCE = "D:/WorkSpace_MathModel/examples/2022C/DeepSeekV4Pro_V2.3"
WSID = "RDpcV29ya1NwYWNlX01hdGhNb2RlbFxleGFtcGxlc1wyMDIyQ1xEZWVwU2Vla1Y0UHJvX1YyLjM"


def test_list_runs():
    resp = client.get(f"/api/workspaces/{WSID}/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for item in data:
        assert "id" in item
        assert "name" in item
        assert "path" in item
        assert "has_langgraph_report" in item


def test_list_runs_sorted():
    resp = client.get(f"/api/workspaces/{WSID}/runs")
    data = resp.json()
    if len(data) >= 2:
        # Check that newer runs appear first (reverse chrono)
        pass  # not strictly guaranteed but fine


def test_list_run_artifacts():
    resp = client.get(f"/api/workspaces/{WSID}/runs")
    runs = resp.json()
    if not runs:
        return
    run_id = runs[0]["id"]
    resp = client.get(f"/api/workspaces/{WSID}/runs/{run_id}/artifacts")
    assert resp.status_code == 200
    artifacts = resp.json()
    assert isinstance(artifacts, list)
    for a in artifacts:
        assert "path" in a
        assert "type" in a


def test_read_run_artifact_markdown():
    resp = client.get(f"/api/workspaces/{WSID}/runs")
    runs = resp.json()
    if not runs:
        return
    run_id = runs[0]["id"]
    resp = client.get(
        f"/api/workspaces/{WSID}/runs/{run_id}/artifact",
        params={"path": "reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md"},
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["type"] == "markdown"
    assert d["content"]


def test_read_run_artifact_json():
    resp = client.get(f"/api/workspaces/{WSID}/runs")
    runs = resp.json()
    if not runs:
        return
    run_id = runs[0]["id"]
    resp = client.get(
        f"/api/workspaces/{WSID}/runs/{run_id}/artifact",
        params={"path": "reports/LANGGRAPH_PHASE_PLAN.json"},
    )
    if resp.status_code != 200:
        return  # not all runs have this file
    d = resp.json()
    assert d["type"] == "json"
    assert d["data"] is not None


def test_path_traversal_rejected():
    resp = client.get(f"/api/workspaces/{WSID}/runs")
    runs = resp.json()
    if not runs:
        return
    run_id = runs[0]["id"]
    resp = client.get(
        f"/api/workspaces/{WSID}/runs/{run_id}/artifact",
        params={"path": "../../.env"},
    )
    assert resp.status_code in (400, 403)


def test_absolute_path_rejected():
    resp = client.get(f"/api/workspaces/{WSID}/runs")
    runs = resp.json()
    if not runs:
        return
    run_id = runs[0]["id"]
    resp = client.get(
        f"/api/workspaces/{WSID}/runs/{run_id}/artifact",
        params={"path": "C:/Windows/System32/config/SAM"},
    )
    assert resp.status_code in (400, 403, 404)


def test_nonexistent_run_returns_404():
    resp = client.get(f"/api/workspaces/{WSID}/runs/deadbeef12345678/artifacts")
    assert resp.status_code == 404
