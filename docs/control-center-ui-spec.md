# MathModelAgent Control Center UI Spec

Status: draft
Target: harness-agnostic V2.6 workspace control center

## Product Positioning

MathModelAgent Control Center is not a chat-first agent UI. It is a workspace-first control center for running, observing, auditing and recovering MathModelAgent V2.6 contest workflows across multiple harnesses.

The UI must not assume Codex is the only runner. Codex, Claude Code, OpenCode and manual copy-paste execution are all harness options. The stable system boundary is the workspace protocol:

- V2.6 phase artifacts under `plan.md`, `WORKFLOW_STATE.md`, `reports/`, `results/`, `code/`, `figures/` and `paper/`
- phase gates: `PASS`, `CONDITIONAL_PASS`, `FAIL`
- quality gates: no unresolved `BLOCKER` or `HIGH`, traceable figures, clean method matrix, clean final audit
- benchmark evidence from `examples/`

## Design Principles

1. Phase-first, not agent-first.
   The primary tabs are V2 phases, not Modeler/Coder/Writer.

2. Artifact-first, not chat-first.
   Reports, manifests, figures and paper files are first-class UI objects.

3. Audit-first, not completion-claim-first.
   A claimed `PASS` is visually subordinate to `audit_v2_run.py` and unresolved revision actions.

4. Harness-agnostic by default.
   Manual mode must work even when no CLI adapter is installed. Managed Codex, Claude Code or OpenCode execution is an enhancement, not the foundation.

5. Local-file truth.
   UI state is derived from workspace files whenever possible. Chat history and WebSocket messages are status streams, not the source of truth.

## Information Architecture

```text
Control Center
  Workspaces
    Dashboard
    Phase View
    Artifact Viewer
    Run Console
  Benchmark
    Example Results
    Audit Trends
  Templates
    Paper Templates
    Figure Templates
  Settings
    Harnesses
    Paths
    Optional Integrations
```

## Primary Layout

Desktop layout:

```text
+--------------------------------------------------------------------------------+
| Top Bar                                                                        |
| Workspace: 2026-demo  Harness: Manual  Audit: FAIL  Run Actions                |
+----------------------+--------------------------------------+------------------+
| Sidebar              | Main Panel                           | Inspector        |
| Workspaces           | Phase Timeline                       | Gate Summary     |
| - Active             | [0 Intake] [1 Strategy] ... [6 Verify]| - current gate    |
| - Recent             | Selected Phase                       | - blockers/high  |
| Benchmark            | - phase objective                    | - audit status   |
| Templates            | - input artifacts                    | Required Files   |
| Settings             | - output artifacts                   | - present/missing|
|                      | - generated prompt                   | Actions          |
|                      | - report preview                     | - Copy Prompt    |
|                      |                                      | - Run Audit      |
|                      |                                      | - Open Folder    |
+----------------------+--------------------------------------+------------------+
```

Mobile / narrow layout:

```text
Top Bar
Phase Timeline
Main Panel
Inspector Drawer
Bottom Action Bar
```

## Core Pages

### 1. Workspace Dashboard

Purpose: answer "Is this contest workspace healthy, and what should I do next?"

Required widgets:

- Workspace header
  - workspace name
  - absolute path
  - contest type
  - language
  - paper engine
  - selected harness
  - last updated time from `WORKFLOW_STATE.md`

- Phase timeline
  - Phase 0 Intake
  - Phase 1 Strategy
  - Phase 2 Experiment
  - Phase 3 Paper
  - Phase 4 Review
  - Phase 5 Revise
  - Phase 6 Verify

- Gate cards
  - `INTAKE_GATE.md`
  - `ANALYSIS_GATE.md`
  - `PAPER_SCORECARD.md`
  - `REVISION_STATUS.md`
  - `VERIFY_REPORT.md`

- Risk strip
  - unresolved `BLOCKER`
  - unresolved `HIGH`
  - missing required artifacts
  - audit status
  - false PASS warning

- Artifact health
  - manifest schema
  - figure count
  - vector export count
  - paper PDF exists
  - page count

Low-fidelity sketch:

```text
+ Dashboard --------------------------------------------------------------------+
| 2026-demo                         Harness: Manual       Audit: FAIL           |
| Path: <repo>/workspaces/2026-demo                                              |
|                                                                                |
| [0 Intake PASS] [1 Strategy PASS] [2 Experiment WARN] [3 Paper WARN]           |
| [4 Review PASS] [5 Revise PASS] [6 Verify FAIL]                                |
|                                                                                |
| Issues                                                                         |
| [HIGH] manifest_schema_legacy                                                  |
| [HIGH] manifest_figures_missing                                                |
| [HIGH] figure_audit_columns_missing                                            |
|                                                                                |
| Artifacts                                                                      |
| PROBLEM_BRIEF ok | DATA_AUDIT ok | MANIFEST legacy | PAPER 16 pages           |
+--------------------------------------------------------------------------------+
```

### 2. Phase View

Purpose: run or review one phase without losing the file contract.

Each phase view has the same structure:

- Phase summary
- Inputs
- Outputs
- Gate / acceptance rule
- Prompt builder
- Harness runner
- Report preview
- Repair suggestions

Phase artifact mapping:

| Phase | Name | Inputs | Outputs |
| --- | --- | --- | --- |
| 0 | Intake | source files, `plan.md` | `PROBLEM_BRIEF.md`, `DATA_AUDIT.md`, `reports/INTAKE_GATE.md` |
| 1 | Strategy | intake artifacts | `MODEL_CANDIDATES.md`, `MODEL_REVIEW_AI.md`, `HUMAN_MODEL_REVIEW.md`, `MODELING_DECISION.md`, `ANALYSIS_MODELING_REPORT.md`, `ANALYSIS_GATE.md` |
| 2 | Experiment | modeling decision, analysis gate | `code/`, `figures/`, `RESULTS_MANIFEST.json`, `EXPERIMENT_LOG.md`, `RESULTS_REPORT.md`, `FIGURE_PLAN.md`, `FIGURE_AUDIT.md` |
| 3 | Paper | results, figures, templates | `paper/`, `CLAIM_TRACE.md`, `PAPER_BUILD_REPORT.md`, `METHOD_IMPLEMENTATION_MATRIX.md` |
| 4 | Review | paper, trace, figures, manifest | `PAPER_SCORECARD.md`, `REVISION_ACTIONS.md` |
| 5 | Revise | revision actions | updated artifacts, `REVISION_STATUS.md` |
| 6 | Verify | all required artifacts | `VERIFY_REPORT.md`, audit result |

Low-fidelity sketch:

```text
+ Phase View: Phase 2 Experiment ------------------------------------------------+
| Objective: implement approved models and generate traceable results/figures    |
|                                                                                |
| Inputs                         | Outputs                                       |
| [ok] MODELING_DECISION.md      | [ok] code/                                    |
| [ok] ANALYSIS_GATE.md          | [warn] RESULTS_MANIFEST.json legacy schema    |
| [ok] HUMAN_MODEL_REVIEW.md     | [missing] extended FIGURE_AUDIT columns       |
|                                                                                |
| Harness Prompt                                                                  |
| [Manual] [Codex] [Claude Code] [OpenCode]                                      |
| +----------------------------------------------------------------------------+ |
| | Use mm-data-experiment in this workspace...                                | |
| +----------------------------------------------------------------------------+ |
| [Copy Prompt] [Open Workspace] [Run Audit]                                    |
|                                                                                |
| Preview: reports/EXPERIMENT_LOG.md                                            |
+--------------------------------------------------------------------------------+
```

### 3. Artifact Viewer

Purpose: inspect the actual durable files.

Supported panels:

- Markdown preview
- raw text view
- JSON tree for `RESULTS_MANIFEST.json`
- figure gallery
- PDF preview / open path
- code file list
- notebook preview if available

### 4. Run Console

Purpose: generate phase-specific prompts and prepare safe copied runs.

Required actions:

- choose phase
- choose harness
- generate prompt
- copy prompt
- prepare copied run workspace
- show command preview
- record run history in `runs/control-center-history.jsonl`

### 5. Settings

Purpose: configure local paths and optional integrations.

Fields:

- `MATHMODEL_ROOT`
- `WORKSPACE_ROOT`
- `EXAMPLES_ROOT`
- selected harness
- optional `ARS_ROOT`
- optional `NATURE_SKILLS_ROOT`

## Safety Requirements

The UI must not force-add ignored local data.

Normally local-only paths:

```text
workspaces/
examples/**/source/
examples/**/runs/
knowledge/raw/
knowledge/.local/
**/control-center-history.jsonl
.env
.venv
node_modules/
dist/
```

The UI should favor copied run workspaces for managed harness preparation and should not auto-execute external CLIs unless a future version explicitly implements and documents that behavior.
