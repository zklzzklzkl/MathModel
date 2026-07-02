---
name: mm-data-experiment
description: "数学建模竞赛 V2 实验与可视化阶段。用于根据已确认建模路线编写可复现代码，执行 EDA、各子问题、敏感性分析，生成结果表、图表和 RESULTS_MANIFEST.json。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Data Experiment

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 上游: [[skills/mm-model-strategy/SKILL|Phase 2 Strategy]] · 下游: [[skills/mm-paper-build/SKILL|Phase 4 Paper]] · 共享规范: [[skills/_references/SKILL|_references]]

## Load First

Read:

- `../_references/v2_pipeline_contract.md`
- `../_references/codex_subagent_protocol.md`
- `../_references/rag_usage_contract.md`
- `../_references/source_quality_policy.md`
- `../_references/executable_model_templates.md`
- `../_references/figure_evidence_map.md`
- `../_references/evaluator_optimizer_protocol.md`
- `../_references/figure_quality_standard.md`
- `../_references/nature_figure_integration_guide.md` when optional `nature-figure` scientific plotting integration is available
- `../_references/ars_v2_integration_guide.md` when optional ARS visualization audit is available

## Inputs

Require:

- `PROBLEM_BRIEF.md`
- `DATA_AUDIT.md`
- `reports/MODELING_DECISION.md`
- `reports/ANALYSIS_MODELING_REPORT.md`
- `reports/ANALYSIS_GATE.md`
- `reports/HUMAN_MODEL_REVIEW.md`

Do not proceed if the human modeling review is missing.

## Required Outputs

- `code/`
- `code/outputs/`
- `figures/`
- `reports/EXPERIMENT_LOG.md`
- `reports/TEMPLATE_ADAPTATION_LOG.md` when any `code_templates` hit is used
- `reports/REFINEMENT_LOG.md`
- `reports/RESULTS_REPORT.md`
- `reports/FIGURE_PLAN.md`
- `reports/FIGURE_AUDIT.md`
- `reports/REVISION_ACTIONS.md` when figure failures require repair tracking
- `results/RESULTS_MANIFEST.json`
- updated `WORKFLOW_STATE.md`

## Execution Order

Follow this order:

```text
eda -> ques1 -> ques2 -> ... -> sensitivity_analysis
```

For each step:

1. If local RAG is available, query `code_templates` and `figure_templates` for implementation skeletons, validation patterns, and figure/caption standards. Treat `code_templates` as `B` auxiliary sources under `../_references/source_quality_policy.md`; they provide structure only, not core evidence.
1a. If any `code_templates` hit is used, write or update `reports/TEMPLATE_ADAPTATION_LOG.md` with template source, current data field mapping, template variables replaced, metrics kept, metrics deleted, why the template applies, residual template variable/path/figure names, and status. Code must not retain template field names, template data paths, or template figure names unless they truly exist in the current problem data.
1b. Convert the accepted route's executable template from `../_references/executable_model_templates.md` into concrete code tasks, result tables, validation metrics, and sensitivity outputs.
2. Write or update code.
3. Run syntax checks before execution.
4. Execute on real data.
5. Save outputs and intermediate data.
6. Generate at least one useful table or figure unless the modeling decision explicitly says not applicable.
7. For paper-intended figures, resolve the plotting backend from `plan.md` or the implementation language. If no backend is clear and `nature-figure` is needed for a publication figure, stop before rendering and ask `Python or R?`.
8. When `nature-figure` is available, run or replicate `../_references/scripts/resolve_nature_figure.py --workspace <contest-workspace>` before drawing core paper figures. Record the resolver result in `reports/AGENT_RUNS.md`.
9. When `nature-figure` is enabled, load its manifest, core contract, stance, and exactly one backend fragment through `../_references/nature_figure_integration_guide.md`; generate data figures only with the selected Python scientific plotting backend or R/ggplot2 backend.
10. Do not use `Pillow` as the backend for core data figures such as heatmaps, bar charts, scatter plots, matrices, distributions, model diagnostics, or quantitative panels. `Pillow` is allowed only for non-data process diagrams or raster annotations.
11. Append a manifest entry for every metric, table, and figure.
12. Write a short result narrative in `reports/RESULTS_REPORT.md`.
12a. Run the `RESULTS_REPORT.md` + `FIGURE_PLAN.md` evaluator-optimizer loop from `../_references/evaluator_optimizer_protocol.md` for at most 2 rounds. Each core result must have data, metric, validation, table/figure evidence, and evidence-map binding. Record the loop in `reports/REFINEMENT_LOG.md`.
13. If using subagents, ask `visualization-reviewer` to check figure usefulness and record the review.

For complex data cleaning, modeling code, or repeated figure generation, use `experiment-coder` or the installed `mathmodel-experiment-coder` custom agent. Its write scope is limited to `code/`, `code/outputs/`, `figures/`, `results/`, `reports/EXPERIMENT_LOG.md`, `reports/RESULTS_REPORT.md`, and `reports/FIGURE_PLAN.md`.

Record both native and simulated subagent runs in `reports/AGENT_RUNS.md` using the fields from `../_references/codex_subagent_protocol.md`.

## Manifest Contract

`results/RESULTS_MANIFEST.json` must contain:

```json
{
  "metrics": [],
  "tables": [],
  "figures": [],
  "scripts": []
}
```

Metric entries require `id`, `problem`, `value`, `unit`, `source_file`, `script`, and `description`.

Figure entries require `id`, `path`, `problem`, `source_data`, `script`, `intended_section`, `caption`, and `supports_claim`.

Core figure entries should also record the evidence-map archetype from `../_references/figure_evidence_map.md` when feasible:

```json
{
  "evidence_map_entry": "predicted_vs_actual",
  "required_metrics": ["MAE", "RMSE", "MAPE"],
  "claim_id": "C1"
}
```

When `nature-figure` is enabled for a core paper figure, figure entries also require `backend`, `contract_id`, `export_bundle`, and `audit_status`:

```json
{
  "id": "f1",
  "path": "figures/f1.svg",
  "backend": "Python",
  "contract_id": "F1",
  "export_bundle": {
    "svg": "figures/f1.svg",
    "pdf": "figures/f1.pdf",
    "preview": "figures/f1.png"
  },
  "audit_status": "pending"
}
```

Keep `path` for backward compatibility; use `export_bundle` to make SVG/PDF/preview traceable.

Table entries require `id`, `path`, `problem`, `source_data`, `script`, `intended_section`, and `caption`.

## Figure Requirements

Generate paper-ready figures, not only debug screenshots. Prefer PDF/SVG for vector plots and PNG only when raster is necessary. Every core figure must bind to a claim and a `figure_evidence_map.md` entry in `reports/FIGURE_PLAN.md`.

Each core subproblem should have at least one of:

- distribution or data-quality plot
- model fit or prediction plot
- comparison or ranking plot
- optimization convergence or scheme comparison
- sensitivity or robustness plot
- mechanism/flow diagram from `4drawio` or equivalent non-data figure

Before accepting a generated figure as paper-ready, check against `../_references/figure_quality_standard.md`:

- text labels render correctly, with no square boxes or mojibake for CJK
- axes have units or meaningful labels
- colors remain distinguishable in grayscale print
- captions state the conclusion, not only the chart type

When `nature-figure` is enabled, also require:

- a figure contract in `reports/FIGURE_PLAN.md`
- selected backend recorded as Python or R
- generated SVG and PDF for vector plots, plus TIFF or PNG preview when useful
- source data traceable from `RESULTS_MANIFEST.json`
- statistics or validation notes sufficient for the caption and paper text
- no cross-rendering with the non-selected backend
- no `Pillow` backend for core data figures

Write `reports/FIGURE_AUDIT.md` with the V2.3 extended columns whenever Nature rules are enabled:

```markdown
| Figure | Inserted | Opens | Readable Text | Labels/Units | Backend Match | Vector Export | Source Data Trace | Stats/Legend | Caption Supports Claim | Status | Required Fix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

If any core paper figure is PNG-only, lacks SVG/PDF export, lacks source data, lacks a selected-backend script, or uses `Pillow` for a data figure, create a `HIGH` or `BLOCKER` item in `reports/REVISION_ACTIONS.md` before leaving this stage.

For complex or high-value figures, optionally load `<ARS_ROOT>/academic-paper/agents/visualization_agent.md` as a role prompt. Use only for figure critique and improvement suggestions. Summarize failures into `reports/FIGURE_AUDIT.md`; convert actionable `FAIL` items into `reports/REVISION_ACTIONS.md`.

## Failure Handling

If a script fails, record the error in `reports/EXPERIMENT_LOG.md`, repair the cause, and rerun. Do not silently skip failed sections.
