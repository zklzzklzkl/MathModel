# V2 Pipeline Contract

This contract is the source of truth for the MathModelAgent V2 skill workflow.

## Architecture

V2 uses a hybrid design:

- Skills define workflow, gates, required artifacts, and quality standards.
- Codex subagents perform independent analysis, implementation, review, or verification.
- The workspace files are the shared memory. Chat history is not the shared memory.

Do not pass long raw context between agents when a compact artifact can be written instead.

## Required Workspace Artifacts

```text
plan.md
todo.md
WORKFLOW_STATE.md
PROBLEM_BRIEF.md
DATA_AUDIT.md
reports/
  AGENT_RUNS.md
  INTAKE_GATE.md
  MODEL_CANDIDATES.md
  MODEL_REVIEW_AI.md
  HUMAN_MODEL_REVIEW.md
  MODELING_DECISION.md
  ANALYSIS_MODELING_REPORT.md
  ANALYSIS_GATE.md
  EXPERIMENT_LOG.md
  RESULTS_REPORT.md
  FIGURE_PLAN.md
  FIGURE_AUDIT.md
  CLAIM_TRACE.md
  PAPER_BUILD_REPORT.md
  PAPER_SCORECARD.md
  REVISION_ACTIONS.md
  REVISION_STATUS.md
  METHOD_IMPLEMENTATION_MATRIX.md
  VERIFY_REPORT.md
results/
  RESULTS_MANIFEST.json
code/
code/outputs/
figures/
paper/
```

Create missing directories as needed.

## Stage Gates

Each stage must end with a clear state update:

- `PASS`: next stage may proceed.
- `CONDITIONAL_PASS`: next stage may proceed only with listed risks carried forward.
- `FAIL`: stop and repair before proceeding.

Hard stops:

- Missing `PROBLEM_BRIEF.md` or `DATA_AUDIT.md`: stop before modeling.
- Missing `HUMAN_MODEL_REVIEW.md`: stop before coding.
- Missing `RESULTS_MANIFEST.json`: stop before writing.
- No usable figures: stop before final paper.
- Missing claim trace: stop before final verification.
- Missing method implementation matrix: stop before contest review.
- Any approved model route that is not implemented, downgraded, or explicitly justified: stop before final verification.
- Any unresolved `BLOCKER` or `HIGH` item in `REVISION_ACTIONS.md`: stop before final verification.
- Any inserted paper figure with unreadable labels, garbled text, or failed visual audit: stop before final verification.

## WORKFLOW_STATE.md Minimum Fields

```markdown
# Workflow State

current_stage:
last_updated:
contest:
engine:
language:

## Completed Artifacts
## Active Decisions
## Risks
## Subagent Runs
## Next Actions
```

## Agent Handoff Rule

Every handoff between stages must be file-based:

- problem understanding -> `PROBLEM_BRIEF.md`
- data understanding -> `DATA_AUDIT.md`
- model choices -> `MODELING_DECISION.md`
- model route implementation -> `METHOD_IMPLEMENTATION_MATRIX.md`
- code results -> `RESULTS_MANIFEST.json` and `RESULTS_REPORT.md`
- figures -> `FIGURE_PLAN.md` and `FIGURE_AUDIT.md`
- paper claims -> `CLAIM_TRACE.md`
- review -> `PAPER_SCORECARD.md` and `REVISION_ACTIONS.md`
- revision loop -> `REVISION_STATUS.md`

## Completion Definition

The project is complete only when `reports/VERIFY_REPORT.md` says `PASS` and the checked evidence proves that the final paper is visual, traceable, reproducible, aligned with the approved model, and free of unresolved high-severity review actions.

`PASS` is not allowed when:

- any contest score dimension is below 4 without an accepted, contest-specific justification
- `REVISION_ACTIONS.md` contains unresolved `BLOCKER` or `HIGH` items
- `FIGURE_AUDIT.md` contains failed checks for inserted figures
- `METHOD_IMPLEMENTATION_MATRIX.md` shows a route promise that was not implemented or honestly downgraded
- a core claim is only weakly supported and the paper still states it as a strong conclusion
