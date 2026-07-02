---
name: mm-problem-intake
description: "数学建模竞赛 V2 题面与数据建档阶段。用于读取赛题、附件和资源，拆解子问题，审计数据风险，建立可恢复上下文，并为后续建模与代码阶段提供结构化输入。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# Problem Intake

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 上游: [[skills/mm-start-contest-v2/SKILL|V2 总控]] · 下游: [[skills/mm-model-strategy/SKILL|Phase 2 Strategy]] · 共享规范: [[skills/_references/SKILL|_references]]

## Load First

Read:

- `../_references/v2_pipeline_contract.md`
- `../_references/codex_subagent_protocol.md`
- `../_references/rag_usage_contract.md`
- `../_references/source_quality_policy.md`
- `../_references/problem_type_router.md`

## Required Outputs

Create or update:

- `PROBLEM_BRIEF.md`
- `DATA_AUDIT.md`
- `WORKFLOW_STATE.md`
- `reports/AGENT_RUNS.md`
- `reports/INTAKE_GATE.md`

## Procedure

1. Inventory all provided problem statements, PDFs, DOCX files, spreadsheets, CSV files, images, and downloaded resources.
2. Extract the exact contest title, background, top-level questions, attachment descriptions, submission requirements, and known constraints.
3. Treat only explicitly numbered top-level questions as `ques1`, `ques2`, etc. Do not inflate small details into fake subproblems.
4. If local RAG is available, query `cumcm_problems` or `mcm_icm_problems` for similar task wording, attachment patterns, and hidden scoring cues. Record only sourced hits using `../_references/rag_usage_contract.md` and `../_references/source_quality_policy.md`; core problem facts should come from the current files or `S` official sources, not unsourced memory.
5. Audit each data file for rows, columns, field meaning, units, missing values, abnormal values, duplicate records, encodings, and whether it can support each subproblem.
6. Record ambiguities and risks in `WORKFLOW_STATE.md`; mark any unreadable or semantically unclear data as `HIGH` risk.
7. If using Codex subagents, run `problem-analyst` and `data-auditor` independently, then summarize their outputs into `reports/AGENT_RUNS.md`.

## PROBLEM_BRIEF.md Structure

```markdown
# Problem Brief

## Contest And Task
## Source Files
## Top-Level Questions
## Inputs And Outputs
## Constraints And Evaluation
## Dependencies Between Questions
## Ambiguities And Risks
## Next Modeling Needs
## Local RAG Evidence Used
```

## DATA_AUDIT.md Structure

```markdown
# Data Audit

## File Inventory
## Table And Field Summary
## Missing / Abnormal / Duplicate Data
## Unit And Encoding Issues
## Usable Variables By Question
## Derived Variables Needed
## Blocking Risks
```

## Gate

Write `reports/INTAKE_GATE.md` with `PASS`, `CONDITIONAL_PASS`, or `FAIL`.

Do not proceed to modeling on `FAIL`. On `CONDITIONAL_PASS`, list exactly what the model strategy stage must handle.
