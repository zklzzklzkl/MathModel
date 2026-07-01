# MathModelAgent Control Center UI Spec

Status: draft
Target: harness-agnostic V2.3 workspace control center

## Product Positioning

MathModelAgent Control Center is not a chat-first agent UI. It is a workspace-first control center for running, observing, auditing, and recovering MathModelAgent V2.3 contest workflows across multiple harnesses.

The UI must not assume Codex is the only runner. Codex, Claude Code, OpenCode, Pi, and manual copy-paste execution are all harness options. The stable system boundary is the workspace protocol:

- V2.3 phase artifacts under `plan.md`, `WORKFLOW_STATE.md`, `reports/`, `results/`, `code/`, `figures/`, and `paper/`
- phase gates: `PASS`, `CONDITIONAL_PASS`, `FAIL`
- quality gates: no unresolved `BLOCKER` or `HIGH`, traceable figures, clean method matrix, clean final audit
- benchmark evidence from `examples/2022C`

## Design Principles

1. Phase-first, not agent-first.
   The primary tabs are V2 phases, not Modeler/Coder/Writer.

2. Artifact-first, not chat-first.
   Reports, manifests, figures, and paper files are first-class UI objects.

3. Audit-first, not completion-claim-first.
   A claimed `PASS` is visually subordinate to `audit_v2_run.py` and unresolved revision actions.

4. Harness-agnostic by default.
   Manual mode must work even when no CLI adapter is installed. Managed Codex/Claude/OpenCode execution is an enhancement, not the foundation.

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
    2022C Results
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
| Workspace: 2022C/DeepSeekV4Pro_V2.3  Harness: Manual  Audit: FAIL  Run Actions |
+----------------------+--------------------------------------+------------------+
| Sidebar              | Main Panel                           | Inspector        |
|                      |                                      |                  |
| Workspaces           | Phase Timeline                       | Gate Summary     |
| - Active             | [0 Intake] [1 Strategy] ... [6 Verify]| - current gate    |
| - Recent             |                                      | - blockers/high  |
|                      | Selected Phase                       | - audit status   |
| Benchmark            | - phase objective                    |                  |
| Templates            | - input artifacts                    | Required Files   |
| Settings             | - output artifacts                   | - present/missing|
|                      | - generated prompt                   |                  |
|                      | - report preview                     | Actions          |
|                      |                                      | - Copy Prompt    |
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
| 2022C / DeepSeekV4Pro_V2.3       Harness: Manual       Audit: FAIL             |
| Path: D:\WorkSpace_MathModel\examples\2022C\DeepSeekV4Pro_V2.3                |
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
| [ok] MODELING_DECISION.md      | [ok] code/                                   |
| [ok] ANALYSIS_GATE.md          | [warn] RESULTS_MANIFEST.json legacy schema   |
| [ok] HUMAN_MODEL_REVIEW.md     | [missing] extended FIGURE_AUDIT columns      |
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

Artifact status badges:

- `present`
- `missing`
- `stale`
- `schema-invalid`
- `audit-failed`
- `not-used-in-paper`
- `paper-inserted`

### 4. Run Console

Purpose: generate and track harness-specific execution.

Run modes:

| Mode | Behavior | Compatibility |
| --- | --- | --- |
| Manual | Generate prompt, user copies to any harness | best |
| Assisted | Generate command and arguments, user confirms outside UI | medium |
| Managed | Backend invokes harness CLI/API and streams logs | harness-specific |

Harness selector:

- Manual
- Codex
- Claude Code
- OpenCode
- Pi

Manual mode requirements:

- always available
- no API key required
- no CLI discovery required
- produces copyable prompt
- watches workspace files for changes after execution

Managed mode requirements:

- adapter availability check
- explicit command preview
- run cancellation
- stdout/stderr capture
- no hidden mutation outside the selected workspace

### 5. Benchmark View

Purpose: make quality improvement measurable.

Inputs:

- `examples/2022C/BENCHMARK.md`
- `scripts/audit_benchmark.py`
- latest generated JSON/Markdown audit output

Table columns:

- workspace
- model / version
- status
- worst severity
- issue count
- claimed PASS
- paper pages
- figure count
- first issue codes

Low-fidelity sketch:

```text
+ Benchmark: 2022C -------------------------------------------------------------+
| [Run Benchmark] [Save Results]                                                |
|                                                                                |
| Workspace              Status  Worst    Claimed PASS  Issues  Pages  Figures  |
| ChatGPTHigh_V2.2       FAIL    BLOCKER  yes           9       5      7        |
| DeepSeekV4Pro_V2.1     FAIL    BLOCKER  yes           23      21     20       |
| DeepSeekV4Pro_V2.3     FAIL    HIGH     no            3       16     0        |
|                                                                                |
| Selected issue: manifest_schema_legacy                                        |
+--------------------------------------------------------------------------------+
```

## Component Model

Reusable components:

- `WorkspaceSelector`
- `HarnessSelector`
- `PhaseTimeline`
- `GateCard`
- `RiskStrip`
- `ArtifactList`
- `ArtifactViewer`
- `PromptPanel`
- `AuditResultPanel`
- `RevisionActionsPanel`
- `FigureGallery`
- `BenchmarkTable`
- `RunConsole`
- `ServiceStatus`

Components to adapt from the external MathModelAgent UI:

| External component | Reuse as | Required changes |
| --- | --- | --- |
| `TaskWebSocket` | task update stream | keep transport, generalize message types |
| `useTaskStore` | workspace/run store | replace agent filters with phase/artifact state |
| `FilesSheet` / file APIs | artifact browser | use V2 workspace paths and artifact metadata |
| `NotebookArea` | code execution preview | treat as optional artifact, not core truth |
| `ChatArea` | status and notes stream | move out of primary layout |
| `ServiceStatus` | backend/harness status | add harness adapter availability |

Components not to reuse as primary UI:

- marketing home page
- Modeler/Coder/Writer tab layout
- four-agent-only workflow assumptions

## Data Model

Workspace summary response:

```json
{
  "workspace_id": "2022C/DeepSeekV4Pro_V2.3",
  "path": "D:/WorkSpace_MathModel/examples/2022C/DeepSeekV4Pro_V2.3",
  "protocol": "v2.3",
  "current_phase": "verify",
  "harness": "manual",
  "last_updated": "2026-07-01T15:49:25",
  "phases": [
    {
      "id": "intake",
      "index": 0,
      "label": "Intake",
      "status": "PASS",
      "gate_file": "reports/INTAKE_GATE.md"
    }
  ],
  "risks": {
    "blocker": 0,
    "high": 3,
    "false_pass": false
  },
  "audit": {
    "status": "FAIL",
    "worst_severity": "HIGH",
    "issue_count": 3
  }
}
```

Artifact response:

```json
{
  "path": "reports/VERIFY_REPORT.md",
  "kind": "markdown",
  "phase": "verify",
  "exists": true,
  "status": "present",
  "updated_at": "2026-07-01T15:49:25"
}
```

Run prompt response:

```json
{
  "phase": "experiment",
  "harness": "manual",
  "mode": "copy_prompt",
  "prompt": "Use mm-data-experiment in workspace ...",
  "required_inputs": ["reports/MODELING_DECISION.md"],
  "expected_outputs": ["results/RESULTS_MANIFEST.json"]
}
```

## Visual System

Tone:

- operational
- dense but readable
- contest-workbench feel
- no marketing hero as the first screen

Layout rules:

- avoid nested cards
- use full-width panels and restrained repeated cards
- prefer tables for artifact lists and benchmark results
- use compact status badges for phase and gate state
- keep chat/status stream secondary

Color semantics:

- `PASS`: green
- `CONDITIONAL_PASS`: amber
- `FAIL`: red
- `BLOCKER`: red
- `HIGH`: orange/red
- `MEDIUM`: amber
- `LOW`: gray/blue
- `missing`: gray
- `stale`: purple or amber

## MVP Scope

MVP should be read-mostly and harness-agnostic.

### MVP 1: Static Mock

- build front-end layout with mock data from `examples/2022C`
- no backend integration required
- show dashboard, phase view, artifact viewer, benchmark table
- demonstrate Manual harness prompt panel

Acceptance:

- a user can understand why each benchmark workspace fails
- phase tabs map to V2.3 artifacts
- chat is not the primary surface

### MVP 2: Local Backend Read API

- list workspaces
- read artifact status
- run `audit_v2_run.py`
- run `audit_benchmark.py`
- create workspace via `new_v2_workspace.py`
- serve artifact content and static files

Acceptance:

- no LLM required
- no harness CLI required
- dashboard reflects real files

### MVP 3: Manual Harness Mode

- generate prompts for each phase
- copy prompt to clipboard
- watch workspace for expected output changes
- show "ready for next phase" when gate files update

Acceptance:

- works with Codex, Claude Code, OpenCode, or any text-based harness
- no harness-specific automation needed

### MVP 4: Assisted Harness Adapters

- Codex command preview
- Claude Code command preview
- OpenCode command preview
- adapter availability checks

Acceptance:

- user can choose a harness without changing workspace protocol
- command is visible before execution

## Migration Plan From External MathModelAgent

Phase A: Copy nothing yet.

- keep external project as reference
- document reusable components
- finalize this UI spec

Phase B: Prototype front-end only.

- create `app/frontend`
- reuse component ideas, not workflow assumptions
- mock data from `examples/2022C`

Phase C: Add read-only backend.

- create `app/backend`
- implement workspace scan, artifact read, audit run
- use FastAPI/WebSocket patterns from external project

Phase D: Add task creation.

- wrap `scripts/new_v2_workspace.py`
- upload source files
- expose workspace path and generated phase prompts

Phase E: Add optional harness adapters.

- start with Manual
- then Codex, Claude Code, OpenCode

## Open Decisions

- Should the app live under `app/` or a separate sibling repo?
- Should benchmark workspaces be editable from UI, or read-only by default?
- Should managed harness execution be allowed to mutate the workspace directly, or should it require a per-run copy?
- Should figure-template previews be part of MVP 1 or deferred?
- Should the first prototype use Vue to reuse external components, or React for a cleaner rewrite?

## Recommended Next Step

Build MVP 1 as a static front-end prototype with mock data. Do not wire LLMs or harness execution yet. The prototype should prove the information architecture:

1. Workspace Dashboard
2. Phase View
3. Artifact Viewer
4. Benchmark View

Only after the layout feels right should backend and harness adapters be added.

## Prototype

MVP 1 static prototype:

- `prototypes/control-center/index.html`
- `prototypes/control-center/README.md`

The prototype uses mock data from `examples/2022C` and is intentionally backend-free.
