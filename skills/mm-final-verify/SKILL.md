---
name: mm-final-verify
description: "数学建模竞赛 V2 最终验收阶段。用于检查完整产物、图表插入、结果追踪、论文编译、代码可复现、高分论文评分和提交就绪状态。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Final Verify

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 上游: [[skills/mm-revision-integrator/SKILL|Phase 6 Revise]]（或 [[skills/mm-contest-review/SKILL|Phase 5 Review]] 若无需修订） · 下游: 无（终点） · 共享规范: [[skills/_references/SKILL|_references]]

## Load First

Read:

- `../_references/v2_pipeline_contract.md`
- `../_references/contest_score_rubric.md`
- `../_references/rag_usage_contract.md`
- `../_references/anti_template_review.md`
- `../_references/figure_quality_standard.md`
- `../_references/nature_figure_integration_guide.md` when optional `nature-figure` scientific plotting integration was used
- `../_references/agent_review_protocol.md`
- `../_references/ars_v2_integration_guide.md` when optional ARS integrity checks are available

## Required Output

Write `reports/VERIFY_REPORT.md` with `PASS`, `CONDITIONAL_PASS`, or `FAIL`.

Before writing the final conclusion, run or replicate this read-only audit:

```bash
python ../_references/scripts/audit_v2_run.py --workspace <contest-workspace>
```

If the script path differs because the skill is copied into another root, resolve it relative to the current `skills/_references/scripts/` directory. Copy every `BLOCKER` or `HIGH` finding into `VERIFY_REPORT.md` and `reports/REVISION_ACTIONS.md`; do not return `PASS` while such findings remain unresolved.

## Verification Checklist

Check:

- required V2 files exist
- `reports/AGENT_RUNS.md` exists when subagents or simulated subagents were used
- each `reports/AGENT_RUNS.md` entry records goal, input artifacts, model/reasoning, permission scope, output artifacts, conclusion, and thread/id when native threads are available
- `reports/HUMAN_MODEL_REVIEW.md` records final route approval
- `reports/HUMAN_MODEL_REVIEW.md`, `reports/MODELING_DECISION.md`, and `WORKFLOW_STATE.md` do not contradict each other
- `results/RESULTS_MANIFEST.json` has metrics and figures
- `reports/METHOD_IMPLEMENTATION_MATRIX.md` exists and has no unresolved `not_implemented` core method rows
- `reports/FIGURE_AUDIT.md` exists and inserted paper figures have no `FAIL` status
- if `nature-figure` was used or available for core paper figures, core paper figures have figure contracts, selected-backend scripts, traceable source data, SVG/PDF vector exports when feasible, preview exports, and conclusion-forward captions
- no core data figure relies on `Pillow` as its Nature backend
- `reports/FIGURE_AUDIT.md` uses the V2.3 extended columns when Nature rules are enabled
- every paper figure path resolves
- LaTeX contains `\includegraphics` or Typst contains `#figure(` / `image(`
- `reports/CLAIM_TRACE.md` has no missing core claims and no strongly worded weak core claims
- `reports/PAPER_SCORECARD.md` exists and all critical dimensions are acceptable
- `reports/PAPER_SCORECARD.md` records judge-skim and anti-template findings when those reviews were run
- `reports/REVISION_ACTIONS.md` and `reports/REVISION_STATUS.md` show no unresolved `BLOCKER` or `HIGH` items
- code files compile or have a documented execution method
- paper compiles where the engine is installed
- no final paper text exposes internal workflow file names, agent logs, or unfinished placeholders
- Optional ARS reference integrity check: if ARS is available, load `<ARS_ROOT>/academic-pipeline/agents/integrity_verification_agent.md` as a role prompt. Use only for reference existence, bibliographic accuracy, citation context, and figure/table caption fidelity. Record unverifiable or inaccurate references in `VERIFY_REPORT.md`; convert actionable issues into `REVISION_ACTIONS.md`.
- Optional ARS claim faithfulness check: if ARS is available, load `<ARS_ROOT>/academic-pipeline/agents/claim_ref_alignment_audit_agent.md` as a role prompt, adapted to V2 evidence. Check claim-to-evidence faithfulness against `CLAIM_TRACE.md`, `RESULTS_MANIFEST.json`, figures, code outputs, and `METHOD_IMPLEMENTATION_MATRIX.md`; do not require ARS citation anchors. Rate claims `SUPPORTED`, `UNSUPPORTED`, `AMBIGUOUS`, or `RETRIEVAL_FAILED`, and mark strong conclusions on weak evidence.

If native Codex subagents were unavailable and roles were simulated, `reports/AGENT_RUNS.md` must explicitly say `simulated` and still record the same fields except native thread/id.

## Hard Gates

Return `FAIL` if any condition is true:

- no figures are inserted into the paper
- generated images exist but are unused without justification
- final paper lacks model validation or sensitivity/robustness analysis
- core numerical conclusions are not traceable to results
- paper cannot be found
- human modeling review is missing
- human modeling review still says the route is waiting/unconfirmed while `MODELING_DECISION.md` claims approval
- subagent or simulated-subagent work is claimed but not logged in `reports/AGENT_RUNS.md`
- `METHOD_IMPLEMENTATION_MATRIX.md` is missing or contains `not_implemented` for an approved core method
- the paper claims a method, model, validation, or diagram that code/results/reports did not implement
- `FIGURE_AUDIT.md` is missing, or any inserted figure has failed readability, broken path, garbled labels, square-box text, or unreadable axes
- `PAPER_SCORECARD.md` has any critical dimension below 4 without an accepted contest-specific justification
- `REVISION_ACTIONS.md` contains unresolved `BLOCKER` or `HIGH` items, or `REVISION_STATUS.md` is missing after such actions were created
- a core claim is `missing`, or a `weak` core claim is written as a strong conclusion in the final paper
- generated core figures are unused without a documented paper/appendix reason
- `nature-figure` was used but a core inserted figure lacks selected-backend provenance, source-data traceability, required vector export, or a resolved figure contract
- Nature is available and a core paper data figure is PNG-only, generated with `Pillow`, or missing SVG/PDF export without a documented raster-only exception
- `scripts/audit_v2_run.py` reports any `BLOCKER` or `HIGH` issue
- a formal contest paper with four or more subproblems is shorter than 8 pages without a documented short-report mode or appendix evidence
- a formal contest paper with four or more subproblems is 5 pages or fewer and lacks sufficient formulas, result tables/figures, or validation evidence

Return `CONDITIONAL_PASS` only when all hard gates pass and remaining issues are limited to `MEDIUM`/`LOW` formatting, wording, appendix coverage, or environment issues that do not affect mathematical correctness, evidence traceability, model honesty, or figure readability.

Return `PASS` only when:

- all contest score dimensions are at least 4, or any exception is explicitly justified and accepted in `VERIFY_REPORT.md`
- no unresolved `BLOCKER` or `HIGH` action exists
- inserted figures pass visual/readability audit
- approved methods are implemented or honestly downgraded
- core claims are traceable and worded at the strength supported by evidence
- the PDF or final document has been opened/rendered or otherwise visually checked enough to detect blank pages, garbled figures, and layout failures

## Report Format

```markdown
# Verify Report

结论：PASS / CONDITIONAL_PASS / FAIL

## Evidence Checked
## Hard Gate Results
## File And Figure Integrity
## Claim Trace Results
## Method Implementation Results
## Figure Audit Results
## V2.3 Automated Audit Results
## Score And Revision Gate Results
## Reproducibility Results
## Paper Build Results
## Required Fixes
```

Do not call the project complete unless the report conclusion is `PASS`.
