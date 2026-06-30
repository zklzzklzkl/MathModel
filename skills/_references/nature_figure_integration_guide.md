# Nature Figure Integration Guide

Use this guide when MathModelAgent V2 wants publication-grade scientific plotting with `nature-skills` while keeping the V2 workflow owner, artifacts, and gates unchanged.

## Role

`nature-figure` is an optional figure-generation and figure-audit layer. It never owns the contest workflow and never bypasses:

- `reports/FIGURE_PLAN.md`
- `results/RESULTS_MANIFEST.json`
- `reports/FIGURE_AUDIT.md`
- `reports/CLAIM_TRACE.md`
- `reports/REVISION_ACTIONS.md`
- `reports/VERIFY_REPORT.md`

Use it to improve figure contracts, panel logic, backend discipline, export quality, and publication-style QA. Summarize its results into existing V2 artifacts instead of creating long standalone transcripts.

## Availability And Path Resolution

Resolve `NATURE_SKILLS_ROOT` with `scripts/resolve_nature_figure.py` in this order:

1. Environment variable `NATURE_SKILLS_ROOT`
2. `<contest-workspace>/nature-skills`
3. `<contest-workspace>/../nature-skills`
4. `%USERPROFILE%\Downloads\Compressed\nature-skills-main\nature-skills-main`
5. `%USERPROFILE%\.codex\skills` when `nature-figure` is installed as a normal Codex skill
6. `%USERPROFILE%\.codex\skills\nature-figure` or a direct `nature-figure` skill directory

Supported layouts are:

```text
<NATURE_SKILLS_ROOT>/
  skills/nature-figure/SKILL.md
  skills/nature-figure/manifest.yaml
  skills/nature-figure/static/core/contract.md
  skills/nature-figure/static/core/stance.md
  skills/nature-figure/static/fragments/backend/python.md
  skills/nature-figure/static/fragments/backend/r.md
  skills/nature-figure/references/

%USERPROFILE%/.codex/skills/
  nature-figure/SKILL.md
  nature-figure/manifest.yaml
  nature-figure/static/core/contract.md
  nature-figure/static/core/stance.md
  nature-figure/static/fragments/backend/python.md
  nature-figure/static/fragments/backend/r.md

<direct nature-figure directory>/
  SKILL.md
  manifest.yaml
  static/core/contract.md
  static/core/stance.md
  static/fragments/backend/python.md
  static/fragments/backend/r.md
```

The resolver output must be recorded when Nature rules are used: `available`, `layout`, `root`, `nature_figure`, `required_files_missing`, and `checked`.

When `nature-figure` is unavailable, continue the normal V2 workflow and record that the enhancement was skipped in `reports/FIGURE_AUDIT.md` or the current stage report. Do not fail solely because `nature-skills` is missing.

## Files To Load

When enabled, read:

1. `skills/nature-figure/manifest.yaml`
2. `skills/nature-figure/static/core/contract.md`
3. `skills/nature-figure/static/core/stance.md`
4. exactly one backend fragment:
   - `skills/nature-figure/static/fragments/backend/python.md`
   - `skills/nature-figure/static/fragments/backend/r.md`

Read on-demand references only when needed:

- `references/figure-contract.md`: convert a planned figure into core conclusion, evidence hierarchy, panel map, and reviewer-risk checks.
- `references/backend-selection.md`: recommend Python or R when the user asks for a recommendation.
- `references/api.md`: Python palette, helper, and validation patterns.
- `references/common-patterns.md`, `references/chart-types.md`, or `references/tutorials.md`: Python layout/chart recipes.
- `references/r-workflow.md` or `references/r-template-index.md`: R workflows and template adaptation.
- `references/qa-contract.md`: final delivery, revision, or journal-style QA.
- `references/figure-legend-conventions.md`: conclusion-forward legends and source-data notes.

Do not load or copy `assets/` by default. Use bundled assets only as private pattern references for a concrete figure task, and do not expose private paths or template identifiers in paper text or reports.

## Backend Gate

Record the plotting backend in `plan.md`:

```markdown
- 科研绘图后端：<Python / R / 待确认>
```

Resolve the backend before generating publication-intended figures:

- Use `Python` when the user chooses Python, when the implementation is clearly Python-based, or when the user explicitly accepts the orchestrator recommendation.
- Use `R` when the user chooses R or provides an R-first workflow/template.
- If neither is clear, stop before publication figure generation and ask the user: `Python or R?`

After the backend is selected, use only that backend for drawing, previewing, exporting, and visual QA. If the selected runtime or packages are missing, report the blocker and do not cross-render with the other language.

`Pillow` is not a Nature data-figure backend. It may be used for non-data process diagrams or simple raster annotations, but it does not satisfy the Nature contract for heatmaps, bar charts, scatter plots, matrices, distributions, model diagnostics, or quantitative panels.

## Figure Contract Fields

For every paper-intended core figure, add these fields to `reports/FIGURE_PLAN.md`:

```markdown
## <figure_id>

- core_conclusion:
- figure_archetype: quantitative grid / schematic-led composite / image plate + quant / asymmetric mixed-modality figure
- backend: Python / R
- final_size:
- panel_map:
  - a:
  - b:
  - c:
- evidence_hierarchy:
  - hero_evidence:
  - validation_evidence:
  - controls_or_robustness:
- statistics_needed:
- source_data_needed:
- export_formats: SVG, PDF, and TIFF or PNG preview
- reviewer_risks:
- intended_section:
- supports_claim:
```

Map the same figure into `results/RESULTS_MANIFEST.json`. Each figure entry must still contain the normal V2 fields: `id`, `path`, `problem`, `source_data`, `script`, `intended_section`, `caption`, and `supports_claim`.

When Nature rules are enabled for a core paper figure, also add:

```json
{
  "backend": "Python or R",
  "contract_id": "figure id in FIGURE_PLAN.md",
  "export_bundle": {
    "svg": "figures/<id>.svg",
    "pdf": "figures/<id>.pdf",
    "preview": "figures/<id>.png"
  },
  "audit_status": "pending | PASS | WARN | FAIL"
}
```

Keep `path` as the canonical inserted or preferred figure path for backward compatibility. `export_bundle` records alternate exports and must include SVG/PDF for vector-feasible core figures.

## Stage Integration

### `mm-model-strategy`

Add a figure contract draft for each candidate route and each major subproblem. The contract may be provisional, but it must state the expected claim and figure type before coding.

### `mm-data-experiment`

Use the selected backend to generate publication-intended figures. Prefer vector output (`SVG` and `PDF`) and include a raster preview only for inspection or raster-native content. Update `FIGURE_PLAN.md`, `RESULTS_MANIFEST.json`, and `RESULTS_REPORT.md` after each generated figure.

When Nature is available and a figure is a core paper data figure, missing SVG/PDF vector export, missing source data, missing selected-backend script, or a Pillow data-figure backend is at least a `HIGH` issue and must be written into `REVISION_ACTIONS.md`.

### `mm-paper-build`

Insert figures near the claim they support. Captions should state the conclusion, not only the chart type. Core paper figures must have a `CLAIM_TRACE.md` row.

### `mm-contest-review`

Use the QA checks from `nature-figure/references/qa-contract.md` to strengthen `FIGURE_AUDIT.md`, especially final size, editable text, color/gray safety, source-data traceability, statistics, and export bundle completeness.

### `mm-revision-integrator`

For failed figure actions, regenerate the figure through the selected backend, update manifests and paper references, then mark the action resolved only with file-level evidence.

### `mm-final-verify`

Treat inserted figures as failing when they break either the V2 hard-failure rules or the enabled nature-figure QA checks. Do not return `PASS` when core figures lack traceable source data, selected-backend scripts, or readable inserted exports.

Run or replicate `scripts/audit_v2_run.py --workspace <contest-workspace>` before writing the final conclusion. Any `BLOCKER` or `HIGH` issue from the audit must be copied into `VERIFY_REPORT.md` and `REVISION_ACTIONS.md`; `PASS` is forbidden until those issues are resolved or honestly downgraded with file-level evidence.

## Audit Mapping

Use this extended table when `nature-figure` is enabled:

```markdown
| Figure | Inserted | Opens | Readable Text | Labels/Units | Backend Match | Vector Export | Source Data Trace | Stats/Legend | Caption Supports Claim | Status | Required Fix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

Severity defaults:

- `BLOCKER`: inserted figure is broken, blank, unreadable, garbled, or contradicts the paper claim.
- `HIGH`: core figure lacks source data, backend script, caption support, readable labels, or required export format.
- `MEDIUM`: figure is usable but misses polish, optional export, or non-core QA detail.
- `LOW`: minor style consistency issue.

## Logging

When `nature-figure` rules are used, append a compact entry to `reports/AGENT_RUNS.md` or the current stage report:

```markdown
## <timestamp> nature-figure

- goal:
- loaded files:
- backend:
- input artifacts:
- output artifacts:
- conclusion:
- thread/id: rule-integration
```

Keep logs compact. Do not paste long `nature-figure` references into V2 reports.
