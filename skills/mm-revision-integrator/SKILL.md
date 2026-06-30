---
name: mm-revision-integrator
description: "Mathematical modeling contest V2 revision loop. Use after mm-contest-review when PAPER_SCORECARD or REVISION_ACTIONS contains BLOCKER, HIGH, MEDIUM, weak-claim, figure-audit, or method-implementation issues that must be repaired before final verification."
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Revision Integrator

## Load First

Read:

- `../_references/v2_pipeline_contract.md`
- `../_references/contest_score_rubric.md`
- `../_references/figure_quality_standard.md`
- `../_references/nature_figure_integration_guide.md` when optional `nature-figure` figure actions exist
- `../_references/agent_review_protocol.md`
- `../_references/ars_v2_integration_guide.md` when ARS-origin review findings exist

## Inputs

Require:

- `reports/PAPER_SCORECARD.md`
- `reports/REVISION_ACTIONS.md`
- `reports/METHOD_IMPLEMENTATION_MATRIX.md`
- `reports/FIGURE_AUDIT.md`
- `reports/CLAIM_TRACE.md`
- `paper/`
- `results/RESULTS_MANIFEST.json`

## Required Outputs

- revised paper, figures, code, reports, or manifest entries as needed
- `reports/REVISION_STATUS.md`
- updated `reports/CLAIM_TRACE.md`
- updated `reports/METHOD_IMPLEMENTATION_MATRIX.md`
- updated `reports/FIGURE_AUDIT.md`
- updated `WORKFLOW_STATE.md`

## Procedure

1. Read every `BLOCKER`, `HIGH`, and `MEDIUM` item in `reports/REVISION_ACTIONS.md`.
2. Repair `BLOCKER` and `HIGH` items before final verification. Do not downgrade severity just to pass.
3. Repair `MEDIUM` items when they affect clarity, figure usefulness, method credibility, or judge objections. Otherwise carry them forward with explicit justification.
4. If a promised method was not implemented, either implement it or revise `MODELING_DECISION.md`, `METHOD_IMPLEMENTATION_MATRIX.md`, and the paper wording so the route is honest.
5. If a core claim is weak, either strengthen evidence or rewrite the paper claim as exploratory, limited, or conditional.
6. If inserted figures fail visual audit, regenerate or replace them before final verification.
6a. For `nature-figure`-origin, V2.3 audit, or publication-figure actions, regenerate through the selected backend only, update SVG/PDF/preview exports, refresh source-data references in `RESULTS_MANIFEST.json`, and update the related figure contract in `FIGURE_PLAN.md`.
6b. If an action reports `Pillow` data figures, PNG-only core figures, missing vector export, missing selected-backend script, missing source-data trace, or incomplete `FIGURE_AUDIT.md` columns, repair the artifact and rerun or replicate `../_references/scripts/audit_v2_run.py --workspace <contest-workspace>` before marking it resolved.
7. For ARS-origin findings, treat ARS as reviewer evidence and priority guidance only. Do not let ARS directly override V2 artifacts; apply fixes through the owning V2 stage and record the result in `REVISION_STATUS.md`.
8. Update `REVISION_STATUS.md` with one row per action item.

## Revision Status Format

```markdown
# Revision Status

| Action ID | Severity | Fix Applied | Files Changed | Verification Evidence | Status |
| --- | --- | --- | --- | --- | --- |
```

`Status` must be `resolved`, `carried_with_justification`, or `unresolved`.

Final verification may not return `PASS` while any `BLOCKER` or `HIGH` item is `unresolved` or `carried_with_justification`.

`BLOCKER` or `HIGH` actions from V2.3 automated audit may not be marked `carried_with_justification` unless the user explicitly selected short-report mode or the artifact is documented as a non-paper/non-core figure. Otherwise they must be repaired or the final status remains `CONDITIONAL_PASS`/`FAIL`.
