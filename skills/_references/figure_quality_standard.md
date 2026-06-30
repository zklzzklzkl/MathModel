# Figure Quality Standard

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

## Hard Failures

Reject:

- blank or nearly blank plots
- unreadable tick labels
- garbled labels, mojibake, or square-box glyphs in inserted figures
- screenshots of raw notebook output
- figures with no connection to a paper claim
- debug-only charts inserted into final paper
- low-resolution raster output when vector output is feasible

## Figure Audit Status

Use `reports/FIGURE_AUDIT.md` to classify every paper-intended figure:

- `PASS`: opens correctly, readable, inserted or deliberately assigned to appendix, and supports a paper claim
- `WARN`: usable but has minor polish issues or is not inserted with a documented reason
- `FAIL`: broken, unreadable, garbled, not connected to a claim, or an inserted figure with visible text/rendering defects

Any inserted `FAIL` figure must create a `HIGH` or `BLOCKER` revision action.
