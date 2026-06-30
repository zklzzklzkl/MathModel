---
name: mm-model-strategy
description: "数学建模竞赛 V2 建模策略阶段。用于生成候选模型路线、公式与算法方案、可视化计划、模型评审和人工确认门禁，避免模板化或不可实现的建模方案。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Model Strategy

## Load First

Read:

- `../_references/v2_pipeline_contract.md`
- `../_references/codex_subagent_protocol.md`
- `../_references/model_method_cards.md`
- `../_references/agent_review_protocol.md`
- `../_references/ars_v2_integration_guide.md` when optional ARS methodology audit is available

## Inputs

Require `PROBLEM_BRIEF.md`, `DATA_AUDIT.md`, `WORKFLOW_STATE.md`, and `reports/INTAKE_GATE.md`.

## Required Outputs

- `reports/MODEL_CANDIDATES.md`
- `reports/MODEL_REVIEW_AI.md`
- `reports/HUMAN_MODEL_REVIEW.md`
- `reports/MODELING_DECISION.md`
- `reports/ANALYSIS_MODELING_REPORT.md`
- `reports/ANALYSIS_GATE.md`
- `reports/FIGURE_PLAN.md`
- updated `WORKFLOW_STATE.md`

## Procedure

1. Generate at least two viable modeling routes for the whole problem set. Include one conservative baseline and one stronger high-score route when data allows.
2. For each subproblem, specify objective, variables, assumptions, equations or algorithm, constraints, solver, validation method, expected figures, expected tables, and failure risks.
3. Run independent AI review when possible:
   - `model-reviewer`: judge correctness, feasibility, data fit, and implementation clarity.
   - `devils-advocate`: identify weak assumptions, template models, missing validation, and likely judge objections.
3a. Optional ARS methodology audit: if ARS is available, load `<ARS_ROOT>/academic-paper-reviewer/agents/methodology_reviewer_agent.md` as a role prompt. Use only for candidate-route audit. Check research-question alignment, research design, sampling/data limitations, method-to-data fit, statistical reporting adequacy, methodological fallacies, results integrity, and reproducibility. Summarize findings into a `Methodology Audit` section of `reports/MODEL_REVIEW_AI.md`; convert any `BLOCKER` or `HIGH` issue into the model review and human confirmation gate.
4. Summarize review findings in `reports/MODEL_REVIEW_AI.md`.
5. Stop for human final review by writing `reports/HUMAN_MODEL_REVIEW.md` as a required gate. If the user has already confirmed a route in chat, record that confirmation explicitly.
6. Write the final accepted route to `reports/MODELING_DECISION.md`.
7. Only then write or update `reports/ANALYSIS_MODELING_REPORT.md`.

## Candidate Route Format

Each route in `reports/MODEL_CANDIDATES.md` must include:

- route name
- applicable problem types
- assumptions
- required fields
- mathematical form
- algorithm steps
- validation and sensitivity plan
- figure/table plan
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
- coding tasks are explicit enough to execute
