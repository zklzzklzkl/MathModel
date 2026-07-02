---
name: mm-model-strategy
description: "数学建模竞赛 V2 建模策略阶段。用于生成候选模型路线、公式与算法方案、可视化计划、模型评审和人工确认门禁，避免模板化或不可实现的建模方案。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Model Strategy

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 上游: [[skills/mm-problem-intake/SKILL|Phase 1 Intake]] · 下游: [[skills/mm-data-experiment/SKILL|Phase 3 Experiment]] · 共享规范: [[skills/_references/SKILL|_references]]

## Load First

Read:

- `../_references/v2_pipeline_contract.md`
- `../_references/codex_subagent_protocol.md`
- `../_references/rag_usage_contract.md`
- `../_references/source_quality_policy.md`
- `../_references/problem_type_router.md`
- `../_references/model_method_cards.md`
- `../_references/executable_model_templates.md`
- `../_references/figure_evidence_map.md`
- `../_references/evaluator_optimizer_protocol.md`
- `../_references/anti_template_review.md`
- `../_references/agent_review_protocol.md`
- `../_references/nature_figure_integration_guide.md` when optional `nature-figure` scientific plotting integration is available
- `../_references/ars_v2_integration_guide.md` when optional ARS methodology audit is available

## Inputs

Require `PROBLEM_BRIEF.md`, `DATA_AUDIT.md`, `WORKFLOW_STATE.md`, and `reports/INTAKE_GATE.md`.

## Required Outputs

- `reports/MODEL_CANDIDATES.md`
- `reports/MODEL_REVIEW_AI.md`
- `reports/REFINEMENT_LOG.md`
- `reports/HUMAN_MODEL_REVIEW.md`
- `reports/MODELING_DECISION.md`
- `reports/ANALYSIS_MODELING_REPORT.md`
- `reports/ANALYSIS_GATE.md`
- `reports/FIGURE_PLAN.md`
- updated `WORKFLOW_STATE.md`

## Procedure

1. Run the problem-type router from `../_references/problem_type_router.md`. Support mixed types; do not force a single label when the task is prediction + optimization, evaluation + allocation, mechanism + simulation, etc.
2. If local RAG is available, query `model_methods`, `excellent_papers`, and `figure_templates` for sourced model cards, high-score structure cues, and figure evidence. For core modeling evidence, use only `S/A` hits from `../_references/source_quality_policy.md`; `B` hits may guide templates and checks only, and `C/D` hits may only create risk notes or revision actions. Record source quality and allowed use in `MODEL_CANDIDATES.md`.
3. Generate at least two viable modeling routes for the whole problem set. Include one conservative baseline and one stronger high-score route when data allows.
4. For each subproblem, specify objective, variables, assumptions, equations or algorithm, constraints, solver, validation method, expected figures, expected tables, and failure risks.
4a. For each route, cite an executable template from `../_references/executable_model_templates.md` or explain why no executable template applies. A route that only names a model without variables, objective, constraints/algorithm, validation, and result-table plan is incomplete.
4b. For each route, run the anti-template review from `../_references/anti_template_review.md`; explicitly answer why the selected model is better than a simpler baseline, whether the data supports it, and how it answers the original question.
4c. For each core expected figure, write a figure evidence contract draft in `reports/FIGURE_PLAN.md` using `../_references/figure_evidence_map.md`: claim id, figure archetype, required data, required metrics, axes/units, intended section, core figure status, failure signals, and supported claim. If `nature-figure` is available, follow `../_references/nature_figure_integration_guide.md`.
5. Run independent AI review when possible:
   - `model-reviewer`: judge correctness, feasibility, data fit, and implementation clarity.
   - `devils-advocate`: identify weak assumptions, template models, missing validation, and likely judge objections.
5a. Optional ARS methodology audit: if ARS is available, load `<ARS_ROOT>/academic-paper-reviewer/agents/methodology_reviewer_agent.md` as a role prompt. Use only for candidate-route audit. Check research-question alignment, research design, sampling/data limitations, method-to-data fit, statistical reporting adequacy, methodological fallacies, results integrity, and reproducibility. Summarize findings into a `Methodology Audit` section of `reports/MODEL_REVIEW_AI.md`; convert any `BLOCKER` or `HIGH` issue into the model review and human confirmation gate.
6. Run the `MODEL_CANDIDATES.md` evaluator-optimizer loop from `../_references/evaluator_optimizer_protocol.md` for at most 2 rounds. Check model fit, source quality, anti-template review, executable template reference, validation plan, and figure evidence plan. Write every round to `reports/REFINEMENT_LOG.md`.
7. Summarize review findings in `reports/MODEL_REVIEW_AI.md`, including the anti-template review table and any residual risks from the refinement loop.
8. Stop for human final review by writing `reports/HUMAN_MODEL_REVIEW.md` as a required gate. If the user has already confirmed a route in chat, record that confirmation explicitly.
9. Write the final accepted route to `reports/MODELING_DECISION.md`.
10. Only then write or update `reports/ANALYSIS_MODELING_REPORT.md`.

## Candidate Route Format

Each route in `reports/MODEL_CANDIDATES.md` must include:

- route name
- applicable problem types
- assumptions
- required fields
- mathematical form
- algorithm steps
- validation and sensitivity plan
- executable template reference or non-applicability reason
- figure/table plan
- figure contract draft for each core paper-intended figure
- local RAG evidence used, with source path, confidence, source quality, allowed use, and whether it can be core evidence
- anti-template review verdict
- advantages
- risks
- reason to adopt or reject

## Gate

`reports/ANALYSIS_GATE.md` must be `PASS`, `CONDITIONAL_PASS`, or `FAIL`.

`PASS` requires:

- human modeling decision exists
- formulas or algorithm steps are implementable
- every subproblem has validation
- every subproblem has planned figure/table evidence
- every accepted route cites an executable template or explains why none applies
- no core modeling route relies on `B/C/D` RAG evidence
- `reports/REFINEMENT_LOG.md` records the model-candidate loop or states why it was not run
- coding tasks are explicit enough to execute
