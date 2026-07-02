from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.model_adapters import DryRunAdapter, ModelAdapterError, OpenAICompatibleAdapter  # noqa: E402
from app.phase_plan import PhasePlan  # noqa: E402


def test_dry_run_adapter_returns_parseable_phase_plan() -> None:
    raw = DryRunAdapter().generate("Plan phase 1", model=None)

    plan = PhasePlan.model_validate(json.loads(raw))

    assert plan.phase == 1
    assert plan.phase_name
    assert plan.planned_steps
    assert plan.human_gates
    assert "paper/" in plan.do_not_do


def test_openai_compatible_adapter_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MATHMODEL_LLM_API_KEY", raising=False)

    adapter = OpenAICompatibleAdapter(provider="deepseek")

    with pytest.raises(ModelAdapterError) as exc:
        adapter.generate("{}", model="deepseek-chat")

    message = str(exc.value)
    assert "MATHMODEL_LLM_API_KEY" in message
    assert "sk-" not in message
