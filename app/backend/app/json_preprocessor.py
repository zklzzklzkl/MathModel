from __future__ import annotations

import json
import re
from typing import Any


def sanitize_llm_json(raw: str) -> tuple[str, dict[str, Any]]:
    """Extract and lightly repair a JSON document from LLM output.

    The sanitizer is intentionally conservative: it only removes common wrappers
    and syntax noise, then lets json.loads(strict=False) perform the final parse.
    """
    report: dict[str, Any] = {
        "original_length": len(raw or ""),
        "sanitized_length": 0,
        "actions": [],
        "success": False,
    }
    text = (raw or "").strip()
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
        report["actions"].append("removed_bom")

    fenced = re.search(r"```(?:json|JSON)?\s*(.*?)```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
        report["actions"].append("extracted_markdown_fence")

    extracted = _extract_balanced_json(text)
    if extracted != text:
        text = extracted
        report["actions"].append("extracted_balanced_json")

    without_trailing_commas = _remove_trailing_commas(text)
    if without_trailing_commas != text:
        text = without_trailing_commas
        report["actions"].append("removed_trailing_commas")

    report["sanitized_length"] = len(text)
    return text, report


def loads_sanitized_json(raw: str) -> tuple[Any, dict[str, Any]]:
    text, report = sanitize_llm_json(raw)
    try:
        data = json.loads(text, strict=False)
    except json.JSONDecodeError as exc:
        report["success"] = False
        report["error"] = str(exc)
        report["preview"] = text[:1200]
        raise
    report["success"] = True
    report["top_level_type"] = type(data).__name__
    return data, report


def _extract_balanced_json(text: str) -> str:
    start = min([idx for idx in (text.find("{"), text.find("[")) if idx >= 0], default=-1)
    if start < 0:
        return text.strip()
    opener = text[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return text[start : index + 1].strip()
    return text[start:].strip()


def _remove_trailing_commas(text: str) -> str:
    previous = None
    current = text
    while previous != current:
        previous = current
        current = re.sub(r",(\s*[}\]])", r"\1", current)
    return current
