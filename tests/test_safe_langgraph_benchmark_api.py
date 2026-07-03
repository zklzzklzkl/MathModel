"""Safe LangGraph benchmark launcher API tests."""
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

WSID = "RDpcV29ya1NwYWNlX01hdGhNb2RlbFxleGFtcGxlc1wyMDIyQ1xEZWVwU2Vla1Y0UHJvX1YyLjM"
FOO_ID = "RDpcV29ya1NwYWNlX01hdGhNb2RlbFx3b3Jrc3BhY2VzXGRlbW8"


def _safe_post(payload: dict):
    return client.post(
        f"/api/workspaces/{WSID}/benchmarks/langgraph-safe",
        headers={"Content-Type": "application/json"},
        content=json.dumps(payload),
    )


def test_safe_run_none_works():
    resp = _safe_post({
        "mode": "contest_graph_v3",
        "provider": "none",
        "copy_workspace": True,
        "run_name": "test-safe-smoke",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data.get("available")


def test_deepseek_rejected():
    resp = _safe_post({
        "mode": "contest_graph_v3",
        "provider": "deepseek",
        "copy_workspace": True,
    })
    assert resp.status_code in (400, 422)


def test_openai_rejected():
    resp = _safe_post({
        "mode": "contest_graph_v3",
        "provider": "openai-compatible",
        "copy_workspace": True,
    })
    assert resp.status_code in (400, 422)


def test_copy_workspace_false_rejected():
    resp = _safe_post({
        "mode": "contest_graph_v3",
        "provider": "none",
        "copy_workspace": False,
    })
    assert resp.status_code == 400


def test_source_workspace_safety():
    """Source workspace gate files must not be modified."""
    ws = Path("D:/WorkSpace_MathModel/examples/2022C/DeepSeekV4Pro_V2.3")
    before_human = (ws / "reports" / "HUMAN_MODEL_REVIEW.md").read_bytes() if (ws / "reports" / "HUMAN_MODEL_REVIEW.md").is_file() else b""
    before_model = (ws / "reports" / "MODELING_DECISION.md").read_bytes() if (ws / "reports" / "MODELING_DECISION.md").is_file() else b""
    before_verify = (ws / "reports" / "VERIFY_REPORT.md").read_bytes() if (ws / "reports" / "VERIFY_REPORT.md").is_file() else b""

    resp = _safe_post({
        "mode": "contest_graph_v3",
        "provider": "none",
        "copy_workspace": True,
        "run_name": "test-safe-safety-check",
    })
    assert resp.status_code == 200

    after_human = (ws / "reports" / "HUMAN_MODEL_REVIEW.md").read_bytes() if (ws / "reports" / "HUMAN_MODEL_REVIEW.md").is_file() else b""
    after_model = (ws / "reports" / "MODELING_DECISION.md").read_bytes() if (ws / "reports" / "MODELING_DECISION.md").is_file() else b""
    after_verify = (ws / "reports" / "VERIFY_REPORT.md").read_bytes() if (ws / "reports" / "VERIFY_REPORT.md").is_file() else b""
    assert before_human == after_human, "HUMAN_MODEL_REVIEW.md was modified"
    assert before_model == after_model, "MODELING_DECISION.md was modified"
    assert before_verify == after_verify, "VERIFY_REPORT.md was modified"
