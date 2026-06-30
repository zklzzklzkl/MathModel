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
