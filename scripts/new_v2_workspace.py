"""Create a standard MathModelAgent V2 contest workspace skeleton."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


REPORTS = [
    "AGENT_RUNS",
    "INTAKE_GATE",
    "MODEL_CANDIDATES",
    "MODEL_REVIEW_AI",
    "HUMAN_MODEL_REVIEW",
    "MODELING_DECISION",
    "ANALYSIS_MODELING_REPORT",
    "ANALYSIS_GATE",
    "EXPERIMENT_LOG",
    "RESULTS_REPORT",
    "FIGURE_PLAN",
    "FIGURE_AUDIT",
    "CLAIM_TRACE",
    "PAPER_BUILD_REPORT",
    "PAPER_SCORECARD",
    "REVISION_ACTIONS",
    "REVISION_STATUS",
    "METHOD_IMPLEMENTATION_MATRIX",
    "VERIFY_REPORT",
]


def write_file(path: Path, text: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", help="Contest workspace path to create")
    parser.add_argument("--contest", default="待确认")
    parser.add_argument("--engine", default="LaTeX")
    parser.add_argument("--language", default="中文")
    parser.add_argument("--subproblems", default="待确认")
    parser.add_argument("--figure-backend", default="待确认")
    parser.add_argument("--nature", choices=["enabled", "unavailable", "not_requested"], default="not_requested")
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffold files")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    for dirname in ("reports", "results", "code", "code/outputs", "figures", "paper", "source"):
        (workspace / dirname).mkdir(parents=True, exist_ok=True)

    now = datetime.now().isoformat(timespec="seconds")
    created: list[str] = []
    skipped: list[str] = []

    files = {
        "plan.md": f"""# V2 数学建模执行方案

用户偏好：
- 排版引擎：{args.engine}
- 竞赛类型：{args.contest}
- 论文语言：{args.language}
- 子问题数量：{args.subproblems}

workflow:
0. 题面与数据建档 - `mm-problem-intake`
1. 候选模型与评审 - `mm-model-strategy`
2. 实验代码与图表 - `mm-data-experiment`
3. 论文整合与图文论证 - `mm-paper-build`
4. 高分论文对标评审 - `mm-contest-review`
5. 评审问题修订闭环 - `mm-revision-integrator`
6. 最终验收 - `mm-final-verify`

subagent_policy:
- review agents: read-only
- experiment agents: write only task outputs
- final verifier: read all and write verification report

figure_policy:
- 科研绘图后端：{args.figure_backend}
- nature-figure：{args.nature}
- formal_paper_mode：true
- short_report_mode：false
""",
        "todo.md": """# V2 待办事项

- [ ] 0. 题面与数据建档 - `mm-problem-intake`
- [ ] 1. 候选模型与评审 - `mm-model-strategy`
- [ ] 2. 人工确认最终建模路线 - `reports/HUMAN_MODEL_REVIEW.md`
- [ ] 3. 实验代码与图表 - `mm-data-experiment`
- [ ] 4. 论文整合与图文论证 - `mm-paper-build`
- [ ] 5. 高分论文对标评审 - `mm-contest-review`
- [ ] 6. 评审问题修订闭环 - `mm-revision-integrator`
- [ ] 7. 最终验收 - `mm-final-verify`
""",
        "WORKFLOW_STATE.md": f"""# Workflow State

current_stage: initialized
last_updated: {now}
contest: {args.contest}
engine: {args.engine}
language: {args.language}

## Completed Artifacts

## Active Decisions

## Risks

## Subagent Runs

## Next Actions
- Run `mm-problem-intake` after adding problem files under `source/`.
""",
        "PROBLEM_BRIEF.md": "# PROBLEM_BRIEF\n\n待 `mm-problem-intake` 填写。\n",
        "DATA_AUDIT.md": "# DATA_AUDIT\n\n待 `mm-problem-intake` 填写。\n",
    }

    for relative, text in files.items():
        if write_file(workspace / relative, text, args.force):
            created.append(relative)
        else:
            skipped.append(relative)

    for report in REPORTS:
        relative = f"reports/{report}.md"
        if write_file(workspace / relative, f"# {report}\n\nStatus: pending\n", args.force):
            created.append(relative)
        else:
            skipped.append(relative)

    manifest = {"metrics": [], "tables": [], "figures": [], "scripts": []}
    manifest_path = workspace / "results" / "RESULTS_MANIFEST.json"
    if manifest_path.exists() and not args.force:
        skipped.append("results/RESULTS_MANIFEST.json")
    else:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created.append("results/RESULTS_MANIFEST.json")

    print(json.dumps({"workspace": str(workspace), "created": created, "skipped": skipped}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
