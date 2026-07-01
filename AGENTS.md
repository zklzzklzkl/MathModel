# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Overview

This is a collection of **Codex skills** (not a traditional software project) that automate the full math modeling contest pipeline: problem analysis → model design → coding → visualization → paper writing → verification.

Two workflows exist in the repository history: **V2** (hybrid Skill + Codex subagent, high-score paper oriented) and **V1** (legacy linear pipeline). V2 is the active workflow; V1 is archived under `archive/v1/` for reference only.

## No Build/Test/Lint Pipeline

This project has no build, test, or lint commands. Every artifact is a markdown report, a PDF figure, a LaTeX/Typst paper, or Python analysis code generated during a contest workflow run. The only verifiable entry is:

```bash
# V2.3 read-only workspace audit
python skills/_references/scripts/audit_v2_run.py --workspace <contest-workspace>

# Benchmark all 2022C example runs
python scripts/audit_benchmark.py --root examples/2022C

# V1 archived paper quality gate
bash archive/v1/skills/6verity/scripts/writing_check.sh --paper-dir <workspace>/paper
```

## Architecture

### File-based state management (CRITICAL)

The workspace is the shared memory. Chat history must NOT hold contest state. Skills hand off structured artifacts — never pass long raw context between agents when a compact file can be written instead.

### V2 Hybrid Workflow (primary)

Seven stages, numbered Phase 0 through Phase 6, are orchestrated by `mm-start-contest-v2`:

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

### V1 Legacy Pipeline

Archived linear flow: `archive/v1/skills/0problem-triage → ... → archive/v1/skills/6verity`

### Key differences V2 vs V1

- V1 auto-proceeds; V2 has mandatory human confirmation gate before coding
- V2 scores against 10-dimension contest rubric (0-5); V1 has no scoring
- V2 enforces claim traceability and figure audits; V1 does not
- V2 uses independent subagent review panels; V1 uses self-review

## Skill Layout

- `skills/_references/` — Shared knowledge base. All skills read from here on demand. Contains pipeline contracts, scoring rubrics, agent profiles, modeling norms, figure standards. Do NOT trigger `_references` as a standalone skill.
- `archive/v1/skills/0problem-triage/` through `archive/v1/skills/6verity/` — archived V1 pipeline skills
- `skills/mm-start-contest-v2/` through `skills/mm-revision-integrator/` — V2 pipeline skills
- `skills/5writing/templates/` — LaTeX and Typst templates for ~17 contest types (zh/ and en/)
- `skills/doctor/` — Environment dependency check and install
- `scripts/audit_benchmark.py` — batch V2.3 audit runner for example workspaces
- `scripts/new_v2_workspace.py` — creates the standard V2 contest workspace skeleton
- `archive/v1/skills/6verity/scripts/writing_check.sh` — archived V1 paper quality verification script

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
- **Nature Figure V2.3**: Scientific plotting hard gate via `Yuan1z0825/nature-skills`. Set `NATURE_SKILLS_ROOT` env var or use the downloaded checkout. Check availability with `python skills/_references/scripts/resolve_nature_figure.py --workspace .`; audit a run with `python skills/_references/scripts/audit_v2_run.py --workspace <contest-workspace>`. PNG-only or Pillow data figures must not be accepted as Nature-quality core evidence.

## Templates

The `5writing/templates/` directory holds contest-specific LaTeX and Typst templates. Chinese contests: CUMCM, ChangSanJiao, HuaShuBei, HuaweiBei, HuaZhongBei, MathorCup, APMCM, ShuWeiBei, WuYiBei, DianGongBei, DongSanSheng, Stats, MCM, Default. English contests: MCM/ICM, APMCM, Default. Each has both LaTeX and Typst variants.
