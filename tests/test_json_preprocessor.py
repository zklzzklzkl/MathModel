from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.json_preprocessor import loads_sanitized_json, sanitize_llm_json


def test_sanitizer_extracts_markdown_fenced_json() -> None:
    raw = "Here is the plan:\n```json\n{\"phase\": 1, \"items\": [1, 2]}\n```"

    data, report = loads_sanitized_json(raw)

    assert data["phase"] == 1
    assert report["success"] is True
    assert "extracted_markdown_fence" in report["actions"]


def test_sanitizer_handles_control_characters_and_trailing_commas() -> None:
    raw = "prefix {\"phase\": 1, \"summary\": \"hello\u0003world\", \"items\": [1,],} suffix"

    data, report = loads_sanitized_json(raw)

    assert data["summary"] == "hello\u0003world"
    assert data["items"] == [1]
    assert "extracted_balanced_json" in report["actions"]
    assert "removed_trailing_commas" in report["actions"]


def test_sanitizer_reports_failure_preview() -> None:
    text, report = sanitize_llm_json("not json")

    assert text == "not json"
    assert report["success"] is False
    with pytest.raises(json.JSONDecodeError):
        loads_sanitized_json("not json")
