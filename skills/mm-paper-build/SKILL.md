---
name: mm-paper-build
description: "数学建模竞赛 V2 论文构建阶段。用于根据实验结果、图表、模型报告和高分论文标准撰写 LaTeX/Typst 论文，插入图表，维护结论追踪并避免纯文字稿。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Paper Build

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 上游: [[skills/mm-data-experiment/SKILL|Phase 3 Experiment]] · 下游: [[skills/mm-contest-review/SKILL|Phase 5 Review]] · 共享规范: [[skills/_references/SKILL|_references]]

## Load First

Read:

- `../_references/v2_pipeline_contract.md`
- `../_references/rag_usage_contract.md`
- `../_references/paper_benchmark_profile.md`
- `../_references/figure_quality_standard.md`
- `../_references/nature_figure_integration_guide.md` when optional `nature-figure` scientific plotting integration is available
- `../_references/ars_v2_integration_guide.md` when optional ARS writing audit is available

## Inputs

Require:

- `reports/ANALYSIS_MODELING_REPORT.md`
- `reports/MODELING_DECISION.md`
- `reports/RESULTS_REPORT.md`
- `reports/FIGURE_PLAN.md`
- `results/RESULTS_MANIFEST.json`
- `figures/`

## Required Outputs

- `paper/`
- `reports/CLAIM_TRACE.md`
- `reports/METHOD_IMPLEMENTATION_MATRIX.md`
- `reports/PAPER_BUILD_REPORT.md`
- updated `WORKFLOW_STATE.md`

## Hard Rules

- Do not produce a text-only paper.
- For formal contest submission, default to LaTeX or Typst. ReportLab/Markdown PDF is a preview artifact unless the user explicitly requested short-report mode.
- Do not invent numbers, tables, or figure conclusions.
- Insert figures near the section where they support reasoning.
- Every inserted figure must have a caption and surrounding explanation.
- Every key claim must map to a manifest metric, table, figure, or modeling decision.
- Do not mention workflow internals such as `reports/`, `WORKFLOW_STATE.md`, or agent names in the final paper.
- Do not claim a stronger method than the code/results actually implemented.
- For non-trivial contests, include one non-data figure such as a technical route, modeling framework, mechanism diagram, or algorithm flowchart unless `PAPER_BUILD_REPORT.md` gives a contest-specific exception.
- If an approved high-score method is downgraded during implementation, update the paper wording and `METHOD_IMPLEMENTATION_MATRIX.md`; do not leave the old method promise implicit.
- Generated figures should use CJK-compatible fonts; matplotlib default DejaVu Sans can produce square boxes for Chinese labels. Check labels before inserting.
- For a formal contest with four or more subproblems, a paper under 8 pages is a `HIGH` compression risk unless appendices and dense evidence justify it; 5 pages or fewer with limited formulas/figures is a `BLOCKER` unless the user explicitly requested short-report mode.
- Each major subproblem must include method definition, formula or algorithm explanation, result table or figure, validation/sensitivity when applicable, and limitations. Missing any element prevents a high score for paper structure, rigor, or validation.

## Writing Flow

1. Confirm engine from `plan.md`; default to LaTeX if missing. Use Typst when the plan or contest template prefers Typst.
2. Choose the closest existing template from legacy `5writing/templates/` when available.
3. If local RAG is available, query `paper_expression`, `excellent_papers`, and `figure_templates` for sourced expression patterns, structure cues, and caption standards. Record use in `reports/PAPER_BUILD_REPORT.md`; do not expose RAG, reports, or skill names in the final paper text.
4. Build a section outline from the contest type and number of subproblems.
5. Build `reports/METHOD_IMPLEMENTATION_MATRIX.md` by comparing `MODELING_DECISION.md`, code scripts, result files, `RESULTS_MANIFEST.json`, and planned paper claims.
5a. Optional ARS argument-chain check: if ARS is available, load `<ARS_ROOT>/academic-paper/agents/argument_builder_agent.md` as a role prompt. Use only for Claim-Evidence-Reasoning review. For each planned core claim, verify the chain `claim -> evidence (manifest/table/figure/model decision) -> reasoning`. If reasoning is missing or implicit, add an explicit reasoning sentence or downgrade the claim wording before drafting.
6. Draft each problem section only after its result entries exist.
7. Insert figures and tables according to `reports/FIGURE_PLAN.md`. Insert every core figure needed for the argument; list any unused paper-intended figure with a reason in `PAPER_BUILD_REPORT.md`.
7a. When `nature-figure` is enabled, use only figures with a completed figure contract, selected-backend script, traceable source data, SVG/PDF export, and a conclusion-forward caption for core paper claims. A PNG-only core data figure or `Pillow` data figure must create a `HIGH`/`BLOCKER` revision item instead of being silently inserted.
8. Add a technical route or modeling framework figure for non-trivial contests.
9. Write abstract last, using final methods and numeric results.
9a. Optional ARS bilingual abstract: if ARS is available and the contest template allows an English abstract, the paper language is English, the contest is MCM/ICM-style, or the user explicitly requested bilingual output, load `<ARS_ROOT>/academic-paper/agents/abstract_bilingual_agent.md` as a role prompt. Generate a non-mechanical bilingual abstract using Background, Purpose, Method, Findings, and Implications. For Chinese national-style templates, do not add an English abstract by default.
10. Fill `reports/CLAIM_TRACE.md` with claim strength, not only source existence.
11. Write `reports/PAPER_BUILD_REPORT.md` summarizing files created, figures inserted, figure omissions, method downgrades, local RAG evidence used, and unresolved issues.

## Method Implementation Matrix

Write:

```markdown
# Method Implementation Matrix

| Problem | Approved Method | Implemented In Code/Results | Paper Wording | Status | Action |
| --- | --- | --- | --- | --- | --- |
```

`Status` must be:

- `implemented`: approved route is implemented and paper wording matches it
- `downgraded_with_disclosure`: a simpler method was used and the paper/decision files honestly disclose it
- `not_implemented`: approved method is missing and not honestly downgraded
- `not_applicable`: approved method no longer applies with a stated reason

No paper may be treated as final while any core row is `not_implemented`.

## Claim Trace Format

```markdown
# Claim Trace

| Claim | Paper Section | Evidence Type | Evidence ID/File | Strength | Paper Wording Check |
| --- | --- | --- | --- | --- | --- |
```

`Strength` must be `strong`, `acceptable`, `weak`, or `missing`.

- `strong`: directly supported by code/result/table/figure and validation
- `acceptable`: supported, but with limited data, assumptions, or modest validation
- `weak`: traceable source exists, but evidence is too limited for a strong conclusion
- `missing`: no reliable source

For `weak` core claims, the paper wording must be cautious (`exploratory`, `limited sample`, `conditional`, or equivalent). No final paper may pass with `missing` core claims or strongly worded `weak` core claims.

## Minimum Paper Evidence

The paper must contain:

- data preprocessing evidence
- model construction evidence
- result table or numeric summary
- at least one figure per major subproblem or a documented exception
- at least one non-data method/process figure for non-trivial contests
- validation, sensitivity, or robustness analysis
- model strengths, weaknesses, and improvement discussion
- for core paper-intended figures, a traceable contract linking conclusion, panel evidence, source data, script, caption, and claim

For formal multi-question contest papers, `reports/PAPER_BUILD_REPORT.md` must also state:

- final engine: LaTeX / Typst / preview-only
- page count or expected page count
- number of inserted figures and tables
- whether any core figure is PNG-only or lacks SVG/PDF export
- whether the output is formal submission or short-report mode
