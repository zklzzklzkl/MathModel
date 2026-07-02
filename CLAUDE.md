# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP.md]]
> **V1 工作流已归档** → [[archive/v1/README|V1 归档说明]]

## Overview

This is a collection of **Claude Code skills** (not a traditional software project) that automate the full math modeling contest pipeline: problem analysis → model design → coding → visualization → paper writing → verification.

**V2.5** is the active workflow: V2's hybrid Skill + Codex subagent pipeline (high-score paper oriented) plus a local RAG **capability layer** that supplies problem-type routing, model cards, code/figure templates, and review rubrics to each phase.

## No Build/Test/Lint Pipeline for Skills

The skill layer has no build/lint. Artifacts are markdown reports, PDF figures, LaTeX/Typst papers, and Python analysis code produced during a contest run. The only verifiable entry points are the audit scripts, the RAG scripts, the `app/` backend, and the `tests/` suite (see Commands).

Python >= 3.11 required for the backend (`app/backend/pyproject.toml`).

## Commands

```bash
# V2.5 read-only workspace audit (the primary "test" of a contest run)
python skills/_references/scripts/audit_v2_run.py --workspace <contest-workspace>

# Batch-audit benchmark example runs
python scripts/audit_benchmark.py --root examples/2022C

# Create a new V2 contest workspace skeleton
python scripts/new_v2_workspace.py workspaces/my-contest --contest CUMCM --engine LaTeX --language 中文

# RAG capability layer (V2.5) — ingest sources into the 8 libraries, then query
python scripts/rag_ingest.py --source <dir> --library <library_name>
python scripts/rag_ingest.py --source <dir> --library <name> --embedding-mode dense
python scripts/rag_query.py --query "<query>" --libraries <names>
python scripts/rag_query.py --query "<query>" --libraries <names> --json --core-only

# Import external reference material (e.g., zhanwen/MathModel checkout)
python scripts/import_zhanwen_mathmodel.py --source <checkout> --dest knowledge/raw

# Local experience memory — capture / brief / distill across runs
python scripts/memory_log.py --workspace <path> --stage <stage>
python scripts/memory_brief.py --workspace <path>
python scripts/memory_distill.py --workspace <path> --output <dir>

# Nature Figure availability check (optional integration)
python skills/_references/scripts/resolve_nature_figure.py --workspace .
```

### pytest (tests/ + app/backend)

`pytest.ini` adds `app/backend` to `pythonpath`. Run from repo root:

```bash
pytest                                                # whole suite
pytest tests/test_rag_scripts.py                      # CLI smoke tests for rag_ingest, rag_query
pytest tests/test_rag_scripts.py::test_name           # single test
pytest tests/test_memory_scripts.py                   # CLI smoke tests for memory scripts
pytest tests/test_rag_source_quality.py               # source quality normalization logic
pytest tests/test_model_adapters.py                   # backend model adapters (DryRunAdapter)
pytest tests/test_langgraph_runner.py                 # LangGraph runner: all 7 modes, controlled apply, sandbox
pytest tests/test_langgraph_api.py                    # FastAPI TestClient for LangGraph endpoints
```

Tests mix unit tests (pytest fixtures) and CLI smoke tests (subprocess calls). The backend API tests use `FastAPI TestClient`.

### Control Center (app/ — FastAPI + Vue 3/Vite)

Local management console. Manual-first, harness-agnostic (Manual / Codex / Claude Code / OpenCode). Managed execution operates on a workspace **copy**, never the original workspace.

**Backend** (`app/backend/app/`): FastAPI app with ~20 endpoints across 12 modules:
- `main.py` — app factory, CORS, all route registrations
- `models.py` — Pydantic request/response schemas for all endpoints
- `config.py` — settings from `.env` (mathmodel_root, workspace_root, examples_root)
- `workspace.py` — workspace discovery, artifact listing, safe path resolution, copy-for-run
- `runner.py` — subprocess wrappers for audit/benchmark/scaffold scripts
- `harness.py` — 4 harness adapters (Manual, Codex, Claude Code, OpenCode), currently prompt-generation only
- `langgraph_runner.py` — LangGraph phase runner with 7 modes (dry_run, llm_plan, controlled_apply, phase_execute, contest_graph_v0/v1/v2)
- `langgraph_state.py` — TypedDict state for LangGraph workflow
- `model_adapters.py` — DryRunAdapter + OpenAICompatibleAdapter for LLM provider calls
- `phase_plan.py` — Pydantic model for structured phase plans
- `prompts.py` — builds portable phase prompts from workspace context + audit issues

Python >= 3.11. Dependencies: fastapi, uvicorn[standard], pydantic, python-multipart. Optional LangGraph deps (`requirements-langgraph.txt`): langgraph, langchain-core, openai.

**Frontend** (`app/frontend/src/`): Single-page Vue 3 app (no vue-router, views switched via reactive `ref` in `App.vue`). Uses Pinia for state management, lucide-vue-next for icons, TypeScript throughout. Package manager: pnpm 11.7+.

```powershell
cd app
.\start.bat          # boots backend + frontend
# frontend: http://127.0.0.1:5173
```

Beginner guide: `docs/control-center-beginner-guide.md`. LangGraph runner docs: `docs/langgraph-runner.md`.

## Architecture

See [[FILE_RELATIONSHIP_MAP.md]] for the complete file dependency graph.

### File-based state management (CRITICAL)

The workspace is the shared memory. Chat history must NOT hold contest state. Skills hand off structured artifacts — never pass long raw context between agents when a compact file can be written instead.

### V2.5 Hybrid Workflow

Seven stages (Phase 0–6) orchestrated by `mm-start-contest-v2`, each backed by RAG capability files from `skills/_references/`:

```
Phase 0: mm-problem-intake     → problem-analyst + data-auditor   (+ RAG 题库)        Gate: INTAKE_GATE.md
Phase 1: mm-model-strategy     → model-reviewer + devils-advocate (+ 路由器/模型卡/反模板)  Gate: HUMAN_MODEL_REVIEW.md (MANDATORY human confirm)
Phase 2: mm-data-experiment    → experiment-coder + visualization-reviewer                Gate: RESULTS_MANIFEST.json, FIGURE_AUDIT.md
Phase 3: mm-paper-build        → paper-writer + claim-trace        (+ 优秀论文/表达模板)   Gate: CLAIM_TRACE.md, METHOD_IMPLEMENTATION_MATRIX.md
Phase 4: mm-contest-review     → contest-reviewer + multi-panel    (+ 评审库/judge-skim)   Gate: PAPER_SCORECARD.md (all dims >= 4)
Phase 5: mm-revision-integrator → repair BLOCKER/HIGH/MEDIUM/LOW                          Gate: REVISION_STATUS.md
Phase 6: mm-final-verify       → final-integrator                                          Gate: VERIFY_REPORT.md = PASS
```

Gates produce `PASS | CONDITIONAL_PASS | FAIL`. Each phase writes specific gate artifacts that downstream phases read.

### RAG Capability Layer (V2.5)

Eight local libraries (ChromaDB + SQLite ledger in `knowledge/.local/`, BAAI/bge-m3 embedding, BM25+dense hybrid) configured in `knowledge/libraries.json`. Samples and source notes live in `knowledge/samples/` and `knowledge/source_notes/`.

Source quality policy (`skills/_references/source_quality_policy.md`) grades sources S/A/B/C/D and restricts usage by quality tier.

Capability files in `skills/_references/` consume them:

| Capability file | Used by |
|-----------------|---------|
| `problem_type_router.md` | intake, model-strategy |
| `model_method_cards.md` | model-strategy |
| `anti_template_review.md` | model-strategy, contest-review |
| `judge_skim_review_protocol.md` | contest-review |
| `rag_usage_contract.md` | all phases (citation + trust rules) |

**RAG never returns final conclusions** — it returns hit documents, source path, confidence, applicable phase, recommended usage, and risk/forbidden notes. See `skills/_references/rag_usage_contract.md`.

## Skill Layout

- `skills/_references/` — Shared knowledge base + capability layer. All skills read from here on demand. Contains pipeline contracts, scoring rubrics, agent profiles, figure standards, source quality policy, evaluator-optimizer protocol, executable model templates, and figure evidence maps. Do NOT trigger `_references` standalone.
- `skills/mm-start-contest-v2/` … `skills/mm-final-verify/` — V2 pipeline skills (8 total)
- `skills/5writing/templates/` — LaTeX + Typst templates for 17 contest types (zh/ and en/), the only resource inherited from V1
- `skills/doctor/` — Environment dependency check and install
- `archive/v1/` — V1 legacy linear pipeline (0problem-triage → 6verity), reference only

Each V2 skill has a `SKILL.md` (workflow, gates, required artifacts) and optionally `agents/openai.yaml` (subagent config).

## Required Workspace Artifacts (V2)

```
plan.md, todo.md, WORKFLOW_STATE.md, PROBLEM_BRIEF.md, DATA_AUDIT.md
reports/{INTAKE_GATE, MODEL_CANDIDATES, MODEL_REVIEW_AI, HUMAN_MODEL_REVIEW,
  MODELING_DECISION, ANALYSIS_MODELING_REPORT, ANALYSIS_GATE, EXPERIMENT_LOG,
  RESULTS_REPORT, FIGURE_PLAN, FIGURE_AUDIT, CLAIM_TRACE, PAPER_BUILD_REPORT,
  PAPER_SCORECARD, REVISION_ACTIONS, REVISION_STATUS,
  METHOD_IMPLEMENTATION_MATRIX, VERIFY_REPORT}.md
results/RESULTS_MANIFEST.json
code/  figures/  paper/
```

**Project is complete** only when `VERIFY_REPORT.md = PASS` AND all of: every score dimension >= 4 (or justified N/A); no unresolved BLOCKER/HIGH in `REVISION_ACTIONS.md`; `FIGURE_AUDIT.md` clean for inserted figures; `METHOD_IMPLEMENTATION_MATRIX.md` has no `not_implemented` core methods; `CLAIM_TRACE.md` has no `missing` core claims and no weak claims stated as strong; paper compiles cleanly with no blank pages.

## Codex Subagent Protocol

10 reusable agent role profiles in `skills/_references/agent_profiles/`. Installed custom agents use `mathmodel-*` prefix (e.g., `mathmodel-experiment-coder`). If custom agents aren't hot-loaded, use built-in Codex agents with matching `agent_profiles/` prompts.

Key convention: **Subagents do not own the workflow** — the main skill integrates their results into durable files.

## Optional Integrations (advisory, never hard dependencies)

- **ARS** (Academic Research Suite): deeper audits via `methodology_reviewer_agent`, `editorial_synthesizer_agent`, etc. Set `ARS_ROOT` env var.
- **Nature Figure V2.3**: scientific plotting quality gate via `Yuan1z0825/nature-skills`. Set `NATURE_SKILLS_ROOT` env var. PNG-only or Pillow data figures must not be accepted as Nature-quality core evidence.

## Project-Specific Config

- **AGENTS.md** — Codex-oriented variant of this file (older, V2.3 references). Prefer CLAUDE.md for Claude Code sessions.
- **.claude/settings.local.json** — pre-approves `cp -r`/`rm -rf` commands to sync the 8 V2 skills from the repo into `~/.claude/skills/`. Paths use Windows-style backslashes; Bash `tr '/' '\\\\'` for path conversion is also pre-approved.
- **pytest.ini** — adds `app/backend` to `pythonpath`.
- **app/backend/pyproject.toml** — backend project metadata (Python >= 3.11, fastapi, uvicorn, pydantic deps).

## Templates

`skills/5writing/templates/` holds contest-specific LaTeX and Typst templates. Chinese (zh/): CUMCM, ChangSanJiao, HuaShuBei, HuaweiBei, HuaZhongBei, MathorCup, APMCM, ShuWeiBei, WuYiBei, DianGongBei, DongSanSheng, Stats, MCM, Default. English (en/): MCM/ICM, APMCM, Default. Each has both Typst and LaTeX variants.
