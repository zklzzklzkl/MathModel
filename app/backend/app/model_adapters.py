from __future__ import annotations

import json
import os
import re
from typing import Any


class ModelAdapterError(RuntimeError):
    """Raised when a model provider cannot generate a plan safely."""


class BaseModelAdapter:
    provider: str

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        raise NotImplementedError


def _phase_from_prompt(prompt: str) -> int:
    match = re.search(r"Phase\s+(\d+)", prompt, flags=re.IGNORECASE)
    if not match:
        return 0
    value = int(match.group(1))
    return max(0, min(6, value))


def _first_env(*names: str) -> tuple[str | None, str | None]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value, name
    return None, None


def provider_config_status(provider: str | None = None, model: str | None = None) -> dict[str, Any]:
    resolved = (provider or os.getenv("MATHMODEL_LLM_PROVIDER") or "none").strip().lower()
    if resolved in {"dry-run", "dry_run"}:
        resolved = "none"
    api_key, api_key_source = _api_key_for_provider(resolved)
    base_url = _base_url_for_provider(resolved)
    resolved_model = model or _model_for_provider(resolved)
    return {
        "provider": resolved,
        "model": resolved_model,
        "base_url": base_url,
        "api_key_present": bool(api_key),
        "api_key_source": api_key_source,
        "accepted_api_key_vars": _accepted_api_key_vars(resolved),
        "accepted_model_vars": _accepted_model_vars(resolved),
        "accepted_base_url_vars": _accepted_base_url_vars(resolved),
    }


def _accepted_api_key_vars(provider: str) -> list[str]:
    if provider == "deepseek":
        return ["MATHMODEL_LLM_API_KEY", "DEEPSEEK_API_KEY"]
    if provider == "openai-compatible":
        return ["MATHMODEL_LLM_API_KEY", "OPENAI_API_KEY"]
    return ["MATHMODEL_LLM_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY"]


def _accepted_model_vars(provider: str) -> list[str]:
    if provider == "deepseek":
        return ["MATHMODEL_LLM_MODEL", "DEEPSEEK_MODEL"]
    if provider == "openai-compatible":
        return ["MATHMODEL_LLM_MODEL", "OPENAI_MODEL"]
    return ["MATHMODEL_LLM_MODEL", "DEEPSEEK_MODEL", "OPENAI_MODEL"]


def _accepted_base_url_vars(provider: str) -> list[str]:
    if provider == "deepseek":
        return ["MATHMODEL_LLM_BASE_URL", "DEEPSEEK_BASE_URL"]
    if provider == "openai-compatible":
        return ["MATHMODEL_LLM_BASE_URL", "OPENAI_BASE_URL"]
    return ["MATHMODEL_LLM_BASE_URL", "DEEPSEEK_BASE_URL", "OPENAI_BASE_URL"]


def _api_key_for_provider(provider: str) -> tuple[str | None, str | None]:
    if provider == "deepseek":
        return _first_env("MATHMODEL_LLM_API_KEY", "DEEPSEEK_API_KEY")
    if provider == "openai-compatible":
        return _first_env("MATHMODEL_LLM_API_KEY", "OPENAI_API_KEY")
    return _first_env("MATHMODEL_LLM_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY")


def _base_url_for_provider(provider: str) -> str | None:
    if provider == "deepseek":
        value, _ = _first_env("MATHMODEL_LLM_BASE_URL", "DEEPSEEK_BASE_URL")
        return value or "https://api.deepseek.com"
    if provider == "openai-compatible":
        value, _ = _first_env("MATHMODEL_LLM_BASE_URL", "OPENAI_BASE_URL")
        return value
    value, _ = _first_env("MATHMODEL_LLM_BASE_URL", "DEEPSEEK_BASE_URL", "OPENAI_BASE_URL")
    return value


def _model_for_provider(provider: str) -> str | None:
    if provider == "deepseek":
        value, _ = _first_env("MATHMODEL_LLM_MODEL", "DEEPSEEK_MODEL")
        return value or "deepseek-chat"
    if provider == "openai-compatible":
        value, _ = _first_env("MATHMODEL_LLM_MODEL", "OPENAI_MODEL")
        return value
    value, _ = _first_env("MATHMODEL_LLM_MODEL", "DEEPSEEK_MODEL", "OPENAI_MODEL")
    return value


class DryRunAdapter(BaseModelAdapter):
    provider = "none"

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        phase = _phase_from_prompt(prompt)
        plan = {
            "phase": phase,
            "phase_name": f"Phase {phase} planning dry-run",
            "summary": "Dry-run provider generated a structural phase plan without calling an external model.",
            "required_inputs": ["Existing V2 workspace artifacts", "Current audit issues"],
            "required_outputs": [
                f"CONTROL_LANGGRAPH_PHASE_{phase}.md",
                "reports/LANGGRAPH_PHASE_PLAN.json",
                "reports/LANGGRAPH_PHASE_PLAN.md",
                "reports/LANGGRAPH_RUN_REPORT.md",
            ],
            "planned_steps": [
                {
                    "id": "step-1",
                    "title": "Read current phase context",
                    "description": "Inspect required inputs, gate files, and audit issues before proposing any work.",
                    "reads": ["PROBLEM_BRIEF.md", "DATA_AUDIT.md", "reports/"],
                    "writes": ["reports/LANGGRAPH_PHASE_PLAN.json", "reports/LANGGRAPH_PHASE_PLAN.md"],
                    "checks": ["All proposed writes remain limited to LangGraph planning artifacts."],
                    "requires_human": False,
                },
                {
                    "id": "step-2",
                    "title": "Preserve human gates",
                    "description": "Keep V2 human confirmation gates as mandatory before downstream execution.",
                    "reads": ["reports/HUMAN_MODEL_REVIEW.md"],
                    "writes": [],
                    "checks": ["Do not bypass HUMAN_MODEL_REVIEW.md."],
                    "requires_human": True,
                },
            ],
            "rag_queries": [
                {
                    "library": "常规模型库",
                    "query": f"Phase {phase} recommended model planning references",
                    "core_only": True,
                    "reason": "Use S/A-quality evidence for core modeling decisions.",
                }
            ],
            "source_quality_requirements": [
                "S/A sources only for core modeling evidence.",
                "B sources are advisory only.",
                "C/D sources must not become core evidence.",
            ],
            "human_gates": [
                {
                    "gate_file": "reports/HUMAN_MODEL_REVIEW.md",
                    "required": True,
                    "reason": "V2 workflow requires human confirmation before coding or downstream execution.",
                }
            ],
            "risk_register": [
                {
                    "severity": "HIGH",
                    "risk": "A generated plan could suggest editing core artifacts too early.",
                    "mitigation": "Treat this plan as advisory; do not apply changes without a separate reviewed execution step.",
                }
            ],
            "expected_artifacts": [
                f"CONTROL_LANGGRAPH_PHASE_{phase}.md",
                "reports/LANGGRAPH_PHASE_PLAN.json",
                "reports/LANGGRAPH_PHASE_PLAN.md",
            ],
            "do_not_do": ["paper/", "code/", "figures/", "results/", "managed_apply", "Bash execution"],
            "next_action": "Review the generated plan, then run the relevant V2 skill or harness manually.",
        }
        return json.dumps(plan, ensure_ascii=False)


class OpenAICompatibleAdapter(BaseModelAdapter):
    def __init__(self, provider: str = "openai-compatible", base_url: str | None = None) -> None:
        self.provider = provider
        env_provider = os.getenv("MATHMODEL_LLM_PROVIDER")
        if env_provider and provider in {"", "env"}:
            self.provider = env_provider
        self.base_url = base_url or _base_url_for_provider(self.provider)

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        api_key, source = _api_key_for_provider(self.provider)
        if not api_key:
            accepted = ", ".join(_accepted_api_key_vars(self.provider))
            raise ModelAdapterError(f"API key is required for {self.provider}. Set one of: {accepted}.")

        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - depends on optional package state
            raise ModelAdapterError(
                "The openai package is not installed. Install optional dependencies with: "
                "pip install -r app/backend/requirements-langgraph.txt"
            ) from exc

        resolved_model = model or _model_for_provider(self.provider)
        if not resolved_model:
            accepted = ", ".join(_accepted_model_vars(self.provider))
            raise ModelAdapterError(f"Model is required for {self.provider}. Set request.model or one of: {accepted}.")

        resolved_temperature = _env_float("MATHMODEL_LLM_TEMPERATURE", temperature)
        resolved_max_tokens = _env_int("MATHMODEL_LLM_MAX_TOKENS", max_tokens)
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = OpenAI(**client_kwargs)
        try:
            response = client.chat.completions.create(
                model=resolved_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You generate strict JSON only. Do not use Markdown fences. "
                            "Do not propose automatic file edits or Bash execution."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=resolved_temperature,
                max_tokens=resolved_max_tokens,
            )
        except Exception as exc:  # pragma: no cover - network/provider dependent
            raise ModelAdapterError(
                f"{self.provider} provider request failed with key source {source}: {_safe_error_message(str(exc))}"
            ) from exc
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise ModelAdapterError(f"{self.provider} provider returned empty content.")
        return content


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        raise ModelAdapterError(f"{name} must be a number.")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise ModelAdapterError(f"{name} must be an integer.")


def _safe_error_message(message: str) -> str:
    for name in ["MATHMODEL_LLM_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY"]:
        api_key = os.getenv(name)
        if api_key:
            message = message.replace(api_key, "[redacted]")
    return message


def get_model_adapter(provider: str | None) -> BaseModelAdapter:
    resolved = (provider or os.getenv("MATHMODEL_LLM_PROVIDER") or "none").strip().lower()
    if resolved in {"none", "dry-run", "dry_run"}:
        return DryRunAdapter()
    if resolved in {"openai-compatible", "deepseek"}:
        return OpenAICompatibleAdapter(provider=resolved)
    raise ModelAdapterError(
        f"Unsupported provider '{provider}'. Use one of: none, dry-run, openai-compatible, deepseek."
    )
