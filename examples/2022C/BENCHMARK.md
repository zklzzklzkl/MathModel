# 2022C Benchmark

This folder is the regression benchmark for MathModelAgent V2.3. Every model run uses the same 2022 C problem and attachment set, so changes to skills, audit scripts, figure policy, or paper gates can be compared against a stable task.

## How To Run

From the repository root:

```powershell
python scripts/audit_benchmark.py --root examples/2022C
```

The command exits with code `2` when any workspace fails the V2.3 audit. That is expected while the benchmark contains known-failing historical runs.

To save machine-readable output:

```powershell
python scripts/audit_benchmark.py --root examples/2022C --json-out examples/2022C/audit-results.json --markdown-out examples/2022C/audit-results.md
```

## Current Baseline

Baseline generated on 2026-07-01 with `scripts/audit_benchmark.py`.

| Workspace | Status | Worst | Figures | Pages | Claimed PASS | Issues | First issue codes |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| ChatGPTHigh_V2.2 | FAIL | BLOCKER | 7 | 5 | yes | 9 | figure_audit_columns_missing, figure_file_missing |
| DeepSeekV4Pro_V2.1 | FAIL | BLOCKER | 20 | 21 | yes | 23 | figure_audit_columns_missing, manifest_figure_contract_incomplete |
| DeepSeekV4Pro_V2.3 | FAIL | HIGH | 0 | 16 | no | 3 | manifest_schema_legacy, manifest_figures_missing, figure_audit_columns_missing |

## Interpretation

- `ChatGPTHigh_V2.2` is the historical weak baseline. It claims PASS but has broken manifest figure paths, a 5-page formal paper, and missing V2.3/Nature figure audit columns.
- `DeepSeekV4Pro_V2.1` has a longer paper and richer figures, but still claims PASS despite unresolved high-severity actions and incomplete V2.3 figure contracts.
- `DeepSeekV4Pro_V2.3` no longer crashes the audit. It now exposes the main remaining gap: the manifest is still legacy list-shaped and does not trace figures through `manifest.figures`.

## Promotion Rule

A skill or workflow change improves the benchmark only if it reduces false PASS behavior or closes a V2.3 audit issue without weakening the hard gates. A workspace should not be marked as final PASS until:

- `audit_v2_run.py` returns `PASS`
- `VERIFY_REPORT.md` and `PAPER_SCORECARD.md` agree with the audit result
- `RESULTS_MANIFEST.json` uses the object schema with `metrics`, `tables`, `figures`, and `scripts`
- core paper figures have source data, script, backend, contract id, SVG/PDF export bundle, and an extended `FIGURE_AUDIT.md` row
