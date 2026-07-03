# AGENTS.md

This file provides guidance to Codex when working in this repository.

## Overview

MathModelAgent V2.6 is a collection of Codex-compatible skills for mathematical modeling contests. It automates and audits the full contest pipeline:

```text
problem analysis -> model design -> coding -> visualization -> paper writing -> review -> revision -> final verification
```

This is not a traditional software project. Most runtime outputs are workspace artifacts: Markdown reports, JSON manifests, Python analysis code, vector figures, LaTeX or Typst papers, and final PDFs.

V2.6 is the active workflow. V1 is archived under `archive/v1/` for historical reference only.

## No Build/Test/Lint Pipeline

There is no single project-wide build or lint command. Verification is mostly workspace-based.

Useful commands:

```bash
# Read-only audit for a V2 workspace
python skills/_references/scripts/audit_v2_run.py --workspace <contest-workspace>

# Batch audit benchmark examples
python scripts/audit_benchmark.py --root examples/2022C

# LangGraph provider-free benchmark arena
python scripts/langgraph_benchmark.py --root tests/langgraph_benchmark_fixtures --mode contest_graph_v3 --provider none

# Real provider Phase 1 planning smoke; key comes from MATHMODEL_LLM_API_KEY
python scripts/real_provider_benchmark.py --workspace examples/2022C/DeepSeekV4Pro_V2.3 --mode llm_plan --phase 1 --provider deepseek --model deepseek-chat

# Multi-provider Phase 1 planning comparison
python scripts/real_provider_compare.py --workspace examples/2022C/DeepSeekV4Pro_V2.3 --mode llm_plan --phase 1 --provider-model deepseek:deepseek-chat --provider-model openai-compatible:<model>

# Create a new V2 workspace skeleton
python scripts/new_v2_workspace.py workspaces/my-contest --contest CUMCM --engine LaTeX --language 中文

# RAG ingestion and query
python scripts/rag_ingest.py --source knowledge/samples --vector-store none
python scripts/rag_query.py "综合评价 权重 稳定性" --library model_methods

# V1 archived paper quality gate, historical only
bash archive/v1/skills/6verity/scripts/writing_check.sh --paper-dir <workspace>/paper
```

## Architecture

### File-based state management

The workspace is the shared memory. Chat history must not hold contest state.

Skills and subagents must hand off structured artifacts through files. Do not pass long raw context between agents when a compact file can be written and cited instead.

### V2.6 Hybrid Workflow

`mm-start-contest-v2` is the orchestrator. It coordinates seven phase skills:

```text
Bootstrap: mm-start-contest-v2      -> create plan, todo, workflow state
Phase 0:  mm-problem-intake         -> problem-analyst + data-auditor
Phase 1:  mm-model-strategy         -> model-strategist + model-reviewer + devils-advocate
Phase 2:  mm-data-experiment        -> experiment-coder + visualization-reviewer
Phase 3:  mm-paper-build            -> paper-writer + claim traceability check
Phase 4:  mm-contest-review         -> contest-reviewer + multi-review panel
Phase 5:  mm-revision-integrator    -> repair BLOCKER/HIGH/MEDIUM issues
Phase 6:  mm-final-verify           -> final-integrator
```

Each phase writes gate artifacts that downstream phases read. Gates produce:

```text
PASS | CONDITIONAL_PASS | FAIL
```

### LangGraph Runtime and Benchmark Arena

LangGraph is an optional orchestration layer. The current alpha runtime is
`contest_graph_v3`: Human Gate, Phase 2 sandbox, Phase 3 paper sandbox,
Phase 4 review, Phase 5 revision sandbox, and Phase 6 audit-only.

Benchmark Arena has three levels:

- `scripts/langgraph_benchmark.py`: provider-free fixture benchmark.
- `scripts/real_provider_benchmark.py`: one real provider Phase 1 `llm_plan` smoke report.
- `scripts/real_provider_compare.py`: deterministic multi-provider Phase 1 planning comparison.

Real provider benchmark commands must not write API keys to reports. They only
read local environment variables, write sanitized reports under
`docs/real_benchmarks/`, and do not run `controlled_apply`, experiments, paper
drafting or final verification.

### Capability Layer

V2.6 includes a local RAG capability layer under `knowledge/` and `skills/_references/`.

Main components:

```text
knowledge/libraries.json
knowledge/samples/
skills/_references/rag_usage_contract.md
skills/_references/problem_type_router.md
skills/_references/model_method_cards.md
skills/_references/anti_template_review.md
skills/_references/judge_skim_review_protocol.md
skills/_references/source_quality_policy.md
skills/_references/figure_evidence_map.md
skills/_references/executable_model_templates.md
skills/_references/evaluator_optimizer_protocol.md
```

RAG is advisory. It may provide candidate evidence, model routes, source notes, code templates, figure patterns and review hints, but it must not directly decide the final answer. Final modeling decisions still require the model strategy gate and human confirmation.

## Skill Layout

- `skills/_references/`: shared contracts, rubrics, agent profiles, model cards, RAG usage rules and quality standards. Do not trigger `_references` as a standalone skill.
- `skills/mm-start-contest-v2/`: V2 orchestrator entry.
- `skills/mm-problem-intake/`: Phase 0, problem and data intake.
- `skills/mm-model-strategy/`: Phase 1, candidate routes, AI review and human model gate.
- `skills/mm-data-experiment/`: Phase 2, code, results, visualization and figure audit.
- `skills/mm-paper-build/`: Phase 3, paper construction, claim trace and method implementation matrix.
- `skills/mm-contest-review/`: Phase 4, high-score review and revision actions.
- `skills/mm-revision-integrator/`: Phase 5, revision loop.
- `skills/mm-final-verify/`: Phase 6, final acceptance.
- `skills/5writing/templates/`: Typst and LaTeX templates for contest papers.
- `skills/doctor/`: environment check and dependency install guidance.
- `skills/typst-author/`: Typst authoring support.
- `archive/v1/`: archived legacy pipeline.

Each V2 skill has a `SKILL.md` and may include `agents/openai.yaml`.

## Required Workspace Artifacts

A V2 contest workspace must contain:

```text
plan.md
todo.md
WORKFLOW_STATE.md
PROBLEM_BRIEF.md
DATA_AUDIT.md
reports/{
  INTAKE_GATE,
  MODEL_CANDIDATES,
  MODEL_REVIEW_AI,
  HUMAN_MODEL_REVIEW,
  MODELING_DECISION,
  ANALYSIS_MODELING_REPORT,
  ANALYSIS_GATE,
  FIGURE_PLAN,
  EXPERIMENT_LOG,
  RESULTS_REPORT,
  FIGURE_AUDIT,
  CLAIM_TRACE,
  METHOD_IMPLEMENTATION_MATRIX,
  PAPER_BUILD_REPORT,
  PAPER_SCORECARD,
  REVISION_ACTIONS,
  REVISION_STATUS,
  VERIFY_REPORT
}.md
results/RESULTS_MANIFEST.json
code/
figures/
paper/
```

The project is complete only when:

```text
VERIFY_REPORT.md = PASS
all score dimensions >= 4, unless justified N/A
no unresolved BLOCKER or HIGH items
FIGURE_AUDIT has no failed inserted figures
METHOD_IMPLEMENTATION_MATRIX has no not_implemented core methods
CLAIM_TRACE has no missing core claims and no weak claims stated as strong
paper compiles cleanly and final PDF opens correctly
```

## Codex Subagent Protocol

Reusable role profiles live in:

```text
skills/_references/agent_profiles/
```

Custom agents use the `mathmodel-*` prefix, for example:

```text
mathmodel-problem-analyst
mathmodel-data-auditor
mathmodel-strategist
mathmodel-reviewer
mathmodel-devils-advocate
mathmodel-experiment-coder
mathmodel-visualization-reviewer
mathmodel-paper-writer
mathmodel-contest-reviewer
mathmodel-final-integrator
```

Key rule: subagents do not own the workflow. The main skill integrates their outputs into durable workspace files.

## Optional Integrations

- ARS, Academic Research Suite: deeper methodology and editorial audits. Set `ARS_ROOT` if available. Advisory only.
- Nature Figure: scientific plotting quality support. Set `NATURE_SKILLS_ROOT` if available. PNG-only or Pillow data figures should not be accepted as core evidence when vector-quality output is required.

Useful checks:

```bash
python skills/_references/scripts/resolve_nature_figure.py --workspace .
python skills/_references/scripts/audit_v2_run.py --workspace <contest-workspace>
```

## Templates

The `skills/5writing/templates/` directory contains contest-specific Typst and LaTeX templates.

Chinese: CUMCM, ChangSanJiao, HuaShuBei, HuaweiBei, HuaZhongBei, MathorCup, APMCM, ShuWeiBei, WuYiBei, DianGongBei, DongSanSheng, Stats, MCM, Default.

English: MCM/ICM, APMCM, Default.

## Safety

Do not commit private contest data, large PDFs, local vector stores, local databases, active workspaces or runtime logs.

Sanitized benchmark reports under `docs/real_benchmarks/` may be committed when
they contain no API keys, no private contest data and no active workspace
payloads.

Local-only paths normally include:

```text
workspaces/
knowledge/raw/
knowledge/.local/
examples/**/source/
examples/**/runs/
**/control-center-history.jsonl
.env
.venv
node_modules/
dist/
```
