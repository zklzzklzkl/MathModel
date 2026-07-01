from __future__ import annotations

from pathlib import Path

from .models import HarnessInfo
from .prompts import build_prompt
from .workspace import append_history, copy_workspace_for_run


def harnesses() -> list[HarnessInfo]:
    return [
        HarnessInfo(
            id="Manual",
            label="Manual",
            managed=False,
            available=True,
            note="生成可复制 Prompt，不自动调用任何 harness。",
        ),
        HarnessInfo(
            id="Codex",
            label="Codex",
            managed=False,
            available=True,
            note="首版仅生成 Codex 命令预览和 Prompt，不自动执行。",
        ),
        HarnessInfo(
            id="Claude Code",
            label="Claude Code",
            managed=False,
            available=True,
            note="首版仅生成 Claude Code 命令预览和 Prompt，不自动执行。",
        ),
        HarnessInfo(
            id="OpenCode",
            label="OpenCode",
            managed=False,
            available=True,
            note="首版仅生成 OpenCode 命令预览和 Prompt，不自动执行。",
        ),
    ]


def command_preview(harness: str, run_workspace: Path, prompt_path: Path | None) -> str:
    if harness == "Manual":
        return "Copy the prompt from the UI into your preferred harness."
    if harness == "Codex":
        return f'codex --cd "{run_workspace}"  # then paste {prompt_path.name if prompt_path else "the prompt"}'
    if harness == "Claude Code":
        return f'claude "{prompt_path}"  # review command flags for your local Claude Code setup'
    if harness == "OpenCode":
        return f'opencode --cwd "{run_workspace}"  # then paste {prompt_path.name if prompt_path else "the prompt"}'
    return "Unsupported harness"


def prepare_harness_run(
    source_workspace: Path,
    phase: int,
    harness: str,
    copy_first: bool = True,
    run_name: str | None = None,
    issues: list[dict] | None = None,
) -> dict:
    run_workspace = copy_workspace_for_run(source_workspace, run_name or f"phase-{phase}") if copy_first else source_workspace
    prompt = build_prompt(run_workspace, phase, harness, issues=issues)
    prompt_path: Path | None = None
    if copy_first:
        prompt_path = run_workspace / f"CONTROL_PROMPT_PHASE_{phase}.md"
        prompt_path.write_text(prompt, encoding="utf-8")
    command = command_preview(harness, run_workspace, prompt_path)
    history = append_history(
        source_workspace,
        {
            "event": "harness_prepare",
            "phase": phase,
            "harness": harness,
            "source_workspace": str(source_workspace),
            "run_workspace": str(run_workspace),
            "prompt_path": str(prompt_path) if prompt_path else None,
            "note": "Prepared safe copied run; no harness was executed.",
        },
    )
    return {
        "harness": harness,
        "phase": phase,
        "source_workspace": str(source_workspace),
        "run_workspace": str(run_workspace),
        "copied": copy_first,
        "prompt": prompt,
        "prompt_path": str(prompt_path) if prompt_path else None,
        "command_preview": command,
        "history": history,
    }
