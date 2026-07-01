# CLAUDE.md

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP.md]]
>
> **V1 工作流已归档** → [[archive/v1/README|V1 归档说明]]

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a collection of **Claude Code skills** (not a traditional software project) that automate the full math modeling contest pipeline: problem analysis → model design → coding → visualization → paper writing → verification.

**V2** (hybrid Skill + Codex subagent, high-score paper oriented) is the primary workflow.

## No Build/Test/Lint Pipeline

This project has no build, test, or lint commands. Every artifact is a markdown report, a PDF figure, a LaTeX/Typst paper, or Python analysis code generated during a contest workflow run.

## Architecture

See [[FILE_RELATIONSHIP_MAP.md]] for complete file dependency graph and execution logic.

### File-based state management (CRITICAL)

The workspace is the shared memory. Chat history must NOT hold contest state. Skills hand off structured artifacts — never pass long raw context between agents when a compact file can be written instead.

### V2 Hybrid Workflow

Eight phases orchestrated by `mm-start-contest-v2`:

```
Phase 0: mm-problem-intake     → problem-analyst + data-auditor (read-only subagents)
Phase 1: mm-model-strategy     → model-reviewer + devils-advocate (HUMAN_MODEL_REVIEW.md gate)
Phase 2: mm-data-experiment    → experiment-coder + visualization-reviewer
Phase 3: mm-paper-build        → paper-writer + claim-trace
Phase 4: mm-contest-review     → contest-reviewer + multi-review-panel
Phase 5: mm-revision-integrator → repair BLOCKER/HIGH items
Phase 6: mm-final-verify       → final-integrator
```

Each phase writes specific gate artifacts (`INTAKE_GATE.md`, `ANALYSIS_GATE.md`, etc.) that downstream phases read. Gates produce `PASS | CONDITIONAL_PASS | FAIL`.

## Skill Layout

- `skills/_references/` — Shared knowledge base. All skills read from here on demand. Contains pipeline contracts, scoring rubrics, agent profiles, figure standards. Do NOT trigger `_references` as a standalone skill.
- `skills/mm-start-contest-v2/` through `skills/mm-final-verify/` — V2 pipeline skills (8 total)
- `skills/5writing/templates/` — LaTeX and Typst templates for ~17 contest types (zh/ and en/), the only resource inherited from V1
- `skills/doctor/` — Environment dependency check and install
- `archive/v1/` — **V1 legacy pipeline** (linear: 0problem-triage → 6verity), preserved for reference only

Each V2 skill has a `SKILL.md` (workflow, gates, required artifacts) and optionally `agents/openai.yaml` (subagent configuration).

## Required Workspace Artifacts (V2)

A V2 contest workspace must contain:

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

The project is complete only when `VERIFY_REPORT.md = PASS` and all score dimensions >= 4, no unresolved BLOCKER/HIGH items, figure audit clean, and all core methods implemented.

## Codex Subagent Protocol

10 reusable agent role profiles in `skills/_references/agent_profiles/`. Installed custom agents use `mathmodel-*` prefix (e.g., `mathmodel-experiment-coder`). If custom agents aren't hot-loaded, use built-in Codex agents with matching `agent_profiles/` prompts.

Key convention: Subagents do not own the workflow — the main skill integrates their results into durable files.

## Optional Integrations

- **ARS** (Academic Research Suite): Deeper audits via `methodology_reviewer_agent`, `editorial_synthesizer_agent`, etc. Set `ARS_ROOT` env var. Advisory only — never a hard dependency.
- **Nature Figure**: Scientific plotting enhancement via `Yuan1z0825/nature-skills`. Set `NATURE_SKILLS_ROOT` env var. Check availability with `python skills/_references/scripts/resolve_nature_figure.py --workspace .`

## Templates

The `5writing/templates/` directory holds contest-specific LaTeX and Typst templates. Chinese contests: CUMCM, ChangSanJiao, HuaShuBei, HuaweiBei, HuaZhongBei, MathorCup, APMCM, ShuWeiBei, WuYiBei, DianGongBei, DongSanSheng, Stats, MCM, Default. English contests: MCM/ICM, APMCM, Default. Each has both LaTeX and Typst variants.
