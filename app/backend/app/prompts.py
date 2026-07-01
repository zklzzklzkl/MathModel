from __future__ import annotations

from pathlib import Path

from .workspace import PHASES


HARNESS_NOTES = {
    "Manual": "你可以把下面的提示词复制到任意 agent/harness 中执行。",
    "Codex": "在 Codex 中执行时，请保持文件状态为唯一事实来源，完成后报告修改文件和验证命令。",
    "Claude Code": "在 Claude Code 中执行时，请遵守 AGENTS.md/CLAUDE.md，并避免把长状态保存在聊天中。",
    "OpenCode": "在 OpenCode 中执行时，请先读取工作区 artifacts，再按阶段 gate 输出结果。",
}

PHASE_GUIDANCE = {
    0: {
        "focus": "完成题面、附件、字段、缺失值、可建模性和风险建档。",
        "must": [
            "不要开始建模或写代码。",
            "必须输出 PROBLEM_BRIEF.md、DATA_AUDIT.md 和 INTAKE_GATE.md。",
            "INTAKE_GATE 只能基于题面和附件事实给出 PASS/CONDITIONAL_PASS/FAIL。",
        ],
    },
    1: {
        "focus": "提出候选模型、反驳风险、最终路线和人工确认材料。",
        "must": [
            "编码前必须完成 HUMAN_MODEL_REVIEW.md。",
            "必须说明每个子问题的模型、公式、数据需求和评分风险。",
            "不要自动进入实验阶段，除非人工确认已经写入 gate artifact。",
        ],
    },
    2: {
        "focus": "实现已确认模型，生成可追踪结果、图表和 RESULTS_MANIFEST。",
        "must": [
            "RESULTS_MANIFEST.json 必须是对象结构：metrics/tables/figures/scripts。",
            "核心图表必须进入 manifest.figures，并能追溯到 source data 与代码。",
            "不要把 PNG-only 或未登记图表当作最终证据。",
        ],
    },
    3: {
        "focus": "构建论文、插入图表，并建立 claim trace 和 method matrix。",
        "must": [
            "每个核心结论必须能追溯到 code/results/figures。",
            "FIGURE_AUDIT.md 必须明确图表状态、来源和论文位置。",
            "不要用论文文字替代缺失的实验或图表证据。",
        ],
    },
    4: {
        "focus": "按竞赛高分论文标准独立审查并生成修订清单。",
        "must": [
            "必须按 BLOCKER/HIGH/MEDIUM/LOW 分级。",
            "PAPER_SCORECARD 的所有维度低于 4 都要有可执行修复建议。",
            "不要把作者自称 PASS 作为审查依据。",
        ],
    },
    5: {
        "focus": "只修复审查中的 BLOCKER/HIGH 项，并保留修订闭环。",
        "must": [
            "优先处理会阻断最终 PASS 的问题。",
            "修订必须回写 REVISION_STATUS.md。",
            "修改论文、图表或代码后必须更新 claim trace 或 method matrix。",
        ],
    },
    6: {
        "focus": "最终验收完整产物，确认是否真正达到 PASS。",
        "must": [
            "VERIFY_REPORT.md = PASS 才算完成。",
            "所有评分维度必须 >= 4。",
            "不得存在未解决 BLOCKER/HIGH、图表审计失败或核心方法未实现。",
        ],
    },
}


def build_prompt(workspace: Path, phase_id: int, harness: str, issues: list[dict] | None = None) -> str:
    phase = next((item for item in PHASES if item["id"] == phase_id), None)
    if not phase:
        raise ValueError(f"Unknown phase: {phase_id}")
    artifacts = "\n".join(f"- {item}" for item in phase["artifacts"])
    note = HARNESS_NOTES.get(harness, HARNESS_NOTES["Manual"])
    guidance = PHASE_GUIDANCE[phase_id]
    must = "\n".join(f"- {item}" for item in guidance["must"])
    issue_lines = ""
    if issues:
        selected = issues[:8]
        issue_lines = "\n".join(
            f"- [{item.get('severity', 'INFO')}] {item.get('code', 'issue')}: {item.get('message', item.get('evidence', ''))}"
            for item in selected
        )
    else:
        issue_lines = "- 当前没有传入审计 issue；请先读取 gate artifacts。"
    return f"""# MathModelAgent V2.3 Phase {phase_id}: {phase["name"]}

Workspace:
{workspace}

Harness:
{harness}

{note}

Skill:
{phase["skill"]}

Phase focus:
{guidance["focus"]}

Hard requirements:
{must}

Gate:
{phase["gate"]}

Required artifacts for this phase:
{artifacts}

Current audit issues:
{issue_lines}

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
