# Evaluator-Optimizer Protocol

This protocol borrows the workflow pattern of generator -> evaluator -> refiner, but keeps MathModel V2 file-based and harness-neutral.

## Core Contract

For selected artifacts, run a small refinement loop:

1. `generator`: writes the first version of the artifact.
2. `evaluator`: checks it against explicit criteria and returns actionable feedback.
3. `refiner`: applies fixes, downgrades claims, or records residual risk.
4. `reports/REFINEMENT_LOG.md`: records each round, score, feedback, changes, stop reason, and remaining risks.

The loop does not require a new runtime, API, or agent framework. It can be run by Codex, Claude Code, OpenCode, or a manual harness as long as files are updated.

## Refinement Log Format

```markdown
# Refinement Log

| Artifact | Round | Generator Output | Evaluator Verdict | Required Fixes | Refiner Changes | Stop Reason | Residual Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
```

Evaluator verdict:

- `EXCELLENT`: ready; no meaningful issue.
- `GOOD`: acceptable; no `HIGH`/`BLOCKER`.
- `NEEDS_REFINEMENT`: actionable `MEDIUM`/`HIGH` issues exist.
- `FAIL`: core correctness, traceability, or feasibility issue.

## Enabled Loops

### `reports/MODEL_CANDIDATES.md`

- Max rounds: 2.
- Must check: problem-type fit, source quality, baseline, advanced route, anti-template review, executable template reference, validation plan, figure evidence plan.
- Stop: `GOOD` or better and no `HIGH/BLOCKER`, or max rounds with residual risk recorded.
- `C/D` core evidence is `FAIL`; `B` core evidence is at least `HIGH`.

### `reports/RESULTS_REPORT.md` + `reports/FIGURE_PLAN.md`

- Max rounds: 2.
- Must check: each core result has data source, metric, validation, figure/table evidence, and figure evidence-map binding.
- Stop: `GOOD` or better and no unaddressed core result gap.
- Missing test metric for prediction or missing constraint check for optimization is at least `HIGH`.

### Paper Draft

- Max rounds: 3.
- Must check: scorecard dimensions, judge skim, claim trace, method implementation matrix, figure insertion, wording strength.
- Stop: `GOOD` or better with no `HIGH/BLOCKER`, or max rounds with residual risks routed to `REVISION_ACTIONS.md`.

## Actionable Feedback Rule

Evaluator feedback must name:

- artifact section or file;
- issue severity;
- why it matters for contest score;
- exact required fix;
- verification evidence needed after repair.

Vague comments like "make it better" are invalid.

## Stop Conditions

Stop the loop when either condition is true:

1. `GOOD` or `EXCELLENT`, no `HIGH/BLOCKER`, and all hard fields exist.
2. Max rounds reached. In this case, write the stop reason and residual risks in `REFINEMENT_LOG.md`; convert any `HIGH/BLOCKER` residual risk into `REVISION_ACTIONS.md`.

## Memory Hook

When a route is rejected, experiment fails, validation fails, figure evidence fails, or review action is resolved, log an event through:

```bash
python scripts/memory_log.py --event-type <type> --summary "<short lesson>"
```

After final review, run:

```bash
python scripts/memory_distill.py --workspace <contest-workspace>
```
