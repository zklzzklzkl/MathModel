from __future__ import annotations

from pathlib import Path

from .workspace import PHASES


HARNESS_NOTES = {
    "Manual": "你可以把下面的提示词复制到任意 agent/harness 中执行。",
    "Codex": "在 Codex 中执行时，请保持文件状态为唯一事实来源，完成后报告修改文件和验证命令。",
    "Claude Code": "在 Claude Code 中执行时，请遵守 AGENTS.md/CLAUDE.md，并避免把长状态保存在聊天中。",
    "OpenCode": "在 OpenCode 中执行时，请先读取工作区 artifacts，再按阶段 gate 输出结果。",
}


def build_prompt(workspace: Path, phase_id: int, harness: str) -> str:
    phase = next((item for item in PHASES if item["id"] == phase_id), None)
    if not phase:
        raise ValueError(f"Unknown phase: {phase_id}")
    artifacts = "\n".join(f"- {item}" for item in phase["artifacts"])
    note = HARNESS_NOTES.get(harness, HARNESS_NOTES["Manual"])
    return f"""# MathModelAgent V2.3 Phase {phase_id}: {phase["name"]}

Workspace:
{workspace}

Harness:
{harness}

{note}

Skill:
{phase["skill"]}

Gate:
{phase["gate"]}

Required artifacts for this phase:
{artifacts}

Execution rules:
- Treat workspace files as the source of truth.
- Read existing artifacts before writing anything.
- Keep changes scoped to Phase {phase_id} outputs unless a required upstream artifact is missing.
- Do not claim PASS unless the relevant gate file and audit evidence support it.
- Preserve unrelated user changes and do not delete existing files.
- After completion, report changed files, unresolved BLOCKER/HIGH items, and the exact verification command used.

Recommended verification:
python skills/_references/scripts/audit_v2_run.py --workspace "{workspace}"
"""
