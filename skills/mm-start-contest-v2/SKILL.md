---
name: mm-start-contest-v2
description: "数学建模竞赛 V2 总控入口。用于启动高分论文对标的 Skill + Codex 子代理混合工作流，创建持久化上下文、调度题面拆解、建模评审、代码实验、图表、论文写作和最终验收。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Math Modeling Contest V2 Orchestrator

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 上游: 无（入口点） · 下游调度: [[skills/mm-problem-intake/SKILL|Phase 0 Intake]] → [[skills/mm-model-strategy/SKILL|Phase 1 Strategy]] → [[skills/mm-data-experiment/SKILL|Phase 2 Experiment]] → [[skills/mm-paper-build/SKILL|Phase 3 Paper]] → [[skills/mm-contest-review/SKILL|Phase 4 Review]] → [[skills/mm-revision-integrator/SKILL|Phase 5 Revise]] → [[skills/mm-final-verify/SKILL|Phase 6 Verify]] · 共享规范: [[skills/_references/SKILL|_references]]

Use this skill as the only V2 entrypoint. Keep legacy skills untouched unless the user explicitly asks to run V1.

## Load First

Read these references before starting:

- `../_references/v2_pipeline_contract.md`
- `../_references/codex_subagent_protocol.md`
- `../_references/contest_score_rubric.md`
- `../_references/nature_figure_integration_guide.md` when optional `nature-figure` scientific plotting integration is available
- `../_references/ars_v2_integration_guide.md` when optional ARS deep-review integration is available

Read `../_references/paper_benchmark_profile.md` before writing or reviewing the paper.

## Core Rule

Do not let one long-context chat hold the whole contest state. Persist state to files, hand off only structured artifacts, and use subagents for independent work or review.

Optional ARS review must be summarized into existing V2 artifacts (`MODEL_REVIEW_AI.md`, `FIGURE_AUDIT.md`, `CLAIM_TRACE.md`, `PAPER_SCORECARD.md`, `REVISION_ACTIONS.md`, `VERIFY_REPORT.md`). Do not create ad hoc long ARS transcripts.

V2.3 Nature audit is a hard quality gate when Nature is available for core paper figures. The workflow may continue without Nature when unavailable, but it may not claim Nature-quality figures unless the resolver result, backend, source data, SVG/PDF export bundle, and figure audit are recorded.

## Required Setup

Create or update these files in the contest workspace:

- `plan.md`
- `todo.md`
- `WORKFLOW_STATE.md`
- `PROBLEM_BRIEF.md`
- `DATA_AUDIT.md`
- `reports/AGENT_RUNS.md`
- `reports/MODEL_CANDIDATES.md`
- `reports/MODEL_REVIEW_AI.md`
- `reports/HUMAN_MODEL_REVIEW.md`
- `reports/MODELING_DECISION.md`
- `reports/FIGURE_PLAN.md`
- `reports/FIGURE_AUDIT.md`
- `reports/CLAIM_TRACE.md`
- `reports/PAPER_SCORECARD.md`
- `reports/REVISION_ACTIONS.md`
- `reports/REVISION_STATUS.md`
- `reports/METHOD_IMPLEMENTATION_MATRIX.md`
- `reports/VERIFY_REPORT.md`
- `results/RESULTS_MANIFEST.json`

## Workflow

0. Intake: run `mm-problem-intake`. Spawn or simulate `problem-analyst` and `data-auditor` as independent reviewers when the task is non-trivial.
1. Modeling: run `mm-model-strategy`. Produce at least two candidate routes, then run model review and devil's advocate review. Stop for human final model confirmation before coding.
2. Experiment: run `mm-data-experiment`. Execute `EDA -> ques1 -> ques2 -> ... -> sensitivity_analysis`. After each section, record code, results, figures, and manifest entries.
3. Paper build: run `mm-paper-build`. Write sections after results exist, insert figures near the relevant argument, and maintain claim trace.
4. Contest review: run `mm-contest-review`. Compare against high-score paper standards and request revisions.
5. Revision loop: run `mm-revision-integrator` when `REVISION_ACTIONS.md` contains any `BLOCKER`, `HIGH`, or score-dimension action. Repair or explicitly resolve those items before final verification.
6. Final verification: run `mm-final-verify`. Do not call the work complete until every hard gate and quality gate passes.

## Plan Template

Write `plan.md` with this minimum structure:

```markdown
# V2 数学建模执行方案

用户偏好：
- 排版引擎：<LaTeX / Typst，默认 LaTeX>
- 竞赛类型：<国赛 / 华为杯 / MCM / ...>
- 论文语言：<中文 / 英文>
- 子问题数量：<待确认 / N>

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
- 科研绘图后端：<Python / R / 待确认，默认先记录为待确认>
- nature-figure：<enabled / unavailable / not requested>
- formal_paper_mode：<true，默认正式竞赛论文>
- short_report_mode：<false，只有用户明确要求短报告时才改为 true>
```

## Todo Template

Write `todo.md`:

```markdown
# V2 待办事项

- [ ] 0. 题面与数据建档 - `mm-problem-intake`
- [ ] 1. 候选模型与评审 - `mm-model-strategy`
- [ ] 2. 人工确认最终建模路线 - `reports/HUMAN_MODEL_REVIEW.md`
- [ ] 3. 实验代码与图表 - `mm-data-experiment`
- [ ] 4. 论文整合与图文论证 - `mm-paper-build`
- [ ] 5. 高分论文对标评审 - `mm-contest-review`
- [ ] 6. 评审问题修订闭环 - `mm-revision-integrator`
- [ ] 7. 最终验收 - `mm-final-verify`
```

Update `todo.md` and `WORKFLOW_STATE.md` at every phase boundary.

## Completion Standard

The workflow is not complete if the final paper is text-only, lacks traceable figures, lacks model validation, lacks sensitivity or robustness analysis, cannot map conclusions back to code/results, has unresolved `BLOCKER` or `HIGH` review actions, has failed inserted figures, or claims a stronger model than the code actually implemented.

When `nature-figure` is enabled, the workflow is also incomplete if core paper figures lack a figure contract, selected-backend script, source data, vector export, or conclusion-forward caption unless a contest-specific exception is documented.

For formal contests with four or more subproblems, the workflow is incomplete if the paper is shorter than 8 pages without documented short-report mode or appendix evidence. A 5-page-or-shorter paper with limited formulas, tables, figures, or validation evidence is a hard failure.

Before final completion, run or replicate `../_references/scripts/audit_v2_run.py --workspace <contest-workspace>`. Any `BLOCKER` or `HIGH` result must be routed through `mm-revision-integrator`.
