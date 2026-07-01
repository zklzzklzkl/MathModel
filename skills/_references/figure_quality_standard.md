# Figure Quality Standard

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 被 [[skills/mm-data-experiment/SKILL|Phase 3 Experiment]] [[skills/mm-paper-build/SKILL|Phase 4 Paper]] [[skills/mm-contest-review/SKILL|Phase 5 Review]] [[skills/mm-revision-integrator/SKILL|Phase 6 Revise]] [[skills/mm-final-verify/SKILL|Phase 7 Verify]] 直接引用

Use this standard for math modeling plots and paper figures.

## Required Metadata

Every paper-intended figure must have:

- file path
- source data
- generating script or tool
- related problem
- intended paper section
- caption
- claim it supports

Record this in `reports/FIGURE_PLAN.md` and `results/RESULTS_MANIFEST.json`.

When `nature-figure` integration is enabled, core paper figures should also record:

- core conclusion
- figure archetype
- selected backend
- selected-backend script
- panel map
- evidence hierarchy
- statistics needed
- source data needed
- export bundle with SVG/PDF and a raster preview when feasible
- reviewer risks

## Good Figure Types

Use figures that reveal model evidence:

- data distribution, box plot, missingness, trend, correlation
- predicted vs actual comparison
- residual or error distribution
- ranking/bar comparison
- heatmap or spatial distribution
- optimization convergence
- sensitivity curve
- robustness comparison
- model/process flow diagram

## Quality Checks

Before accepting a figure:

- axes have units or meaningful labels
- legend is readable
- colors are distinguishable in print
- caption states the conclusion, not only the chart type
- figure is referenced in the corresponding section
- figure does not duplicate a table without adding insight
- figure file opens correctly
- CJK labels render as real text, not square boxes or mojibake
- inserted paper figures remain readable after PDF/Typst/LaTeX compilation
- if `nature-figure` is enabled, selected-backend provenance, editable vector text where feasible, source-data traceability, and export bundle completeness are documented

## Hard Failures

Reject:

- blank or nearly blank plots
- unreadable tick labels
- garbled labels, mojibake, or square-box glyphs in inserted figures
- screenshots of raw notebook output
- figures with no connection to a paper claim
- debug-only charts inserted into final paper
- low-resolution raster output when vector output is feasible
- cross-rendered publication figures that were drawn, previewed, or exported with a backend different from the selected `nature-figure` backend
- core data figures generated with `Pillow` when `nature-figure` is available; Pillow is acceptable only for non-data diagrams or raster annotations
- Nature-enabled core figures with no SVG/PDF export bundle, no source-data trace, no selected-backend script, or no figure contract

## Figure Audit Status

Use `reports/FIGURE_AUDIT.md` to classify every paper-intended figure:

- `PASS`: opens correctly, readable, inserted or deliberately assigned to appendix, and supports a paper claim
- `WARN`: usable but has minor polish issues or is not inserted with a documented reason
- `FAIL`: broken, unreadable, garbled, not connected to a claim, or an inserted figure with visible text/rendering defects

Any inserted `FAIL` figure must create a `HIGH` or `BLOCKER` revision action.

When `nature-figure` is enabled, `reports/FIGURE_AUDIT.md` must use this extended table:

```markdown
| Figure | Inserted | Opens | Readable Text | Labels/Units | Backend Match | Vector Export | Source Data Trace | Stats/Legend | Caption Supports Claim | Status | Required Fix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

For V2.3 final verification, run or replicate `scripts/audit_v2_run.py --workspace <contest-workspace>`. Any `HIGH` or `BLOCKER` issue from that audit must become a revision action before the run can be marked complete.
