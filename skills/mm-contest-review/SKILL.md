---
name: mm-contest-review
description: "数学建模竞赛 V2 高分论文对标评审阶段。用于按高分论文标准审查模型、实验、图表、论文结构、结论追踪和可提交性，并给出修改清单。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Contest Review

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 上游: [[skills/mm-paper-build/SKILL|Phase 4 Paper]] · 下游: [[skills/mm-revision-integrator/SKILL|Phase 6 Revise]] · 共享规范: [[skills/_references/SKILL|_references]]

## Load First

Read:

- `../_references/contest_score_rubric.md`
- `../_references/paper_benchmark_profile.md`
- `../_references/agent_review_protocol.md`
- `../_references/figure_quality_standard.md`
- `../_references/nature_figure_integration_guide.md` when optional `nature-figure` scientific plotting integration is available
- `../_references/ars_v2_integration_guide.md` when optional ARS editorial synthesis is available

## Inputs

Review all current artifacts, especially:

- `PROBLEM_BRIEF.md`
- `DATA_AUDIT.md`
- `reports/MODELING_DECISION.md`
- `reports/RESULTS_REPORT.md`
- `reports/FIGURE_PLAN.md`
- `reports/FIGURE_AUDIT.md`
- `reports/METHOD_IMPLEMENTATION_MATRIX.md`
- `reports/CLAIM_TRACE.md`
- `paper/`
- `results/RESULTS_MANIFEST.json`

## Required Outputs

- `reports/PAPER_SCORECARD.md`
- `reports/REVISION_ACTIONS.md`
- `reports/FIGURE_AUDIT.md`
- updated `WORKFLOW_STATE.md`

## Review Panels

Use independent subagents when possible:

- `contest-reviewer`: scoring and judge perspective
- `devils-advocate`: weaknesses and likely objections
- `visualization-reviewer`: figure/table adequacy
- `paper-writer` or `final-integrator`: structure and prose coherence
- `model-reviewer` or `final-integrator`: approved-route versus implemented-method consistency

After independent panels complete, optionally load `<ARS_ROOT>/academic-paper-reviewer/agents/editorial_synthesizer_agent.md` as a role prompt. Use only to synthesize panel findings. Build a synthesis matrix, resolve precedence by severity (`BLOCKER > HIGH > MEDIUM > LOW`), and append an `Editorial Decision Letter` plus `Revision Roadmap` to `reports/PAPER_SCORECARD.md`. The synthesizer must not fabricate findings; every actionable point must trace to a specific panel report and be represented in `reports/REVISION_ACTIONS.md`.

If subagents are unavailable, simulate the panels sequentially and record that in `reports/AGENT_RUNS.md`.

Whether panels are native Codex subagents or simulated roles, log the same metadata: goal, inputs, model/reasoning, permission scope, outputs, conclusion, and thread/id when available.

## Scorecard

Score these dimensions from 0 to 5:

- problem understanding
- modeling originality and fit
- mathematical rigor
- data processing
- code/result reproducibility
- visualization quality
- paper structure
- claim evidence
- validation and sensitivity
- final submission readiness

For any dimension below 4, create an action item in `reports/REVISION_ACTIONS.md` and do not mark the review as full `PASS`.

Conclusion rules:

- `PASS`: every dimension is 4 or 5, no `BLOCKER`/`HIGH` actions remain, figure audit has no failed inserted figures, Nature/V2.3 audit has no `HIGH`/`BLOCKER` issue, and method implementation matrix has no `not_implemented` core rows.
- `CONDITIONAL_PASS`: no fatal correctness issue, but at least one `MEDIUM` or justified score weakness remains.
- `FAIL`: any hard failure, unimplemented approved core method, missing core evidence, or judge-facing defect that would likely cause major score loss.

## Revision Action Contract

Write `reports/REVISION_ACTIONS.md` as a table with these fields:

```markdown
# Revision Actions

| ID | Issue | Severity | Source Panel | Required Fix | Scope | Status |
| --- | --- | --- | --- | --- | --- | --- |
```

Severity must be `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`.

Default status is `unresolved`. `mm-revision-integrator` must later update resolution evidence in `REVISION_STATUS.md`.

Assign severity as follows:

- `BLOCKER`: correctness, traceability, compilation, missing core paper, or impossible-to-submit issue
- `HIGH`: likely meaningful score loss, including weak core claims stated strongly, failed inserted figures, missing route diagram in a complex problem, missing required p/error/validation evidence, or approved method not implemented
- `MEDIUM`: clarity, justification, appendix coverage, or non-core robustness gaps
- `LOW`: polish

## Figure Audit

Write or update `reports/FIGURE_AUDIT.md`:

```markdown
# Figure Audit

| Figure | Inserted | Opens | Readable Text | Labels/Units | Backend Match | Vector Export | Source Data Trace | Stats/Legend | Caption Supports Claim | Status | Required Fix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

Rules:

- Inserted figures with garbled text, square-box labels, unreadable ticks, or broken paths are `FAIL` and create a `HIGH` or `BLOCKER` action.
- Core generated figures that are not inserted must have a justification or appendix plan.
- A paper with no technical route, modeling framework, mechanism, or algorithm flow figure in a non-trivial contest must receive a `HIGH` action.
- When `nature-figure` is enabled, also audit figure contract presence, backend match, editable SVG/PDF text where applicable, source-data traceability, statistics/legend sufficiency, and export bundle completeness. Missing core source data, missing selected-backend script, or missing vector export is at least `HIGH` unless documented as not applicable.
- Core data figures generated with `Pillow` are at least `HIGH` when Nature is available. `Pillow` is acceptable only for non-data diagrams or raster annotations.
- Core figures that are PNG-only when SVG/PDF export is feasible are at least `HIGH`.
- `reports/FIGURE_AUDIT.md` missing the V2.3 extended columns is itself a `HIGH` issue when Nature rules are enabled.

## Paper Density Review

For formal contests with four or more subproblems:

- Fewer than 8 final PDF pages is a `HIGH` risk unless `PAPER_BUILD_REPORT.md` documents short-report mode or unusually dense appendix coverage.
- Five pages or fewer with limited formulas, tables, or figure evidence is a `BLOCKER` for full `PASS`.
- Each major subproblem must include method definition, formula/algorithm explanation, result table or figure, validation/sensitivity where applicable, and limitation wording. Missing any element should reduce the relevant score dimension below 4 and create a revision action.

## Method Implementation Review

Review `reports/METHOD_IMPLEMENTATION_MATRIX.md` against code, results, and paper wording.

- Any `not_implemented` core row is at least `HIGH`.
- Any paper claim that names a method not implemented in code/results is at least `HIGH`.
- If a route was downgraded honestly and the paper wording is cautious, mark it as a limitation rather than a blocker.

## Claim Strength Review

Review `reports/CLAIM_TRACE.md` for `weak` or `missing` core claims.

- `missing` core claims are hard failures.
- `weak` core claims stated as strong conclusions are `HIGH`.
- `weak` core claims stated cautiously may remain `MEDIUM` or lower depending on contest importance.

## Hard Failures

Mark review as `FAIL` if:

- final paper has no figures
- core claims cannot be traced
- model route was never reviewed or approved
- code results do not match paper claims
- sensitivity/validation is missing without justification
- figures exist only as files but are not inserted in the paper
- inserted figures are unreadable or visibly garbled
- approved model route is materially different from implemented code/results without disclosure
- `CLAIM_TRACE.md` has missing core claims or strongly worded weak core claims
