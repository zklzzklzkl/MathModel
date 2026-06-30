---
name: mm-data-experiment
description: "数学建模竞赛 V2 实验与可视化阶段。用于根据已确认建模路线编写可复现代码，执行 EDA、各子问题、敏感性分析，生成结果表、图表和 RESULTS_MANIFEST.json。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Data Experiment

## Load First

Read:

- `../_references/v2_pipeline_contract.md`
- `../_references/codex_subagent_protocol.md`
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

1. Write or update code.
2. Run syntax checks before execution.
3. Execute on real data.
4. Save outputs and intermediate data.
5. Generate at least one useful table or figure unless the modeling decision explicitly says not applicable.
6. For paper-intended figures, resolve the plotting backend from `plan.md` or the implementation language. If no backend is clear and `nature-figure` is needed for a publication figure, stop before rendering and ask `Python or R?`.
7. When `nature-figure` is enabled, load its manifest, core contract, stance, and exactly one backend fragment through `../_references/nature_figure_integration_guide.md`; generate figures only with the selected backend.
8. Append a manifest entry for every metric, table, and figure.
9. Write a short result narrative in `reports/RESULTS_REPORT.md`.
10. If using subagents, ask `visualization-reviewer` to check figure usefulness and record the review.

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

Table entries require `id`, `path`, `problem`, `source_data`, `script`, `intended_section`, and `caption`.

## Figure Requirements

Generate paper-ready figures, not only debug screenshots. Prefer PDF/SVG for vector plots and PNG only when raster is necessary.

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

For complex or high-value figures, optionally load `<ARS_ROOT>/academic-paper/agents/visualization_agent.md` as a role prompt. Use only for figure critique and improvement suggestions. Summarize failures into `reports/FIGURE_AUDIT.md`; convert actionable `FAIL` items into `reports/REVISION_ACTIONS.md`.

## Failure Handling

If a script fails, record the error in `reports/EXPERIMENT_LOG.md`, repair the cause, and rerun. Do not silently skip failed sections.
