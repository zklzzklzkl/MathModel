# MathModel Control Center

Version: 0.2.0

Local full-stack control center for MathModelAgent V2.6 workspaces.

新手请先读：[MathModel Control Center 小白使用指南](../docs/control-center-beginner-guide.md)

## Overview

The Control Center is a local, manual-first management UI for MathModelAgent contest workspaces.

It does not replace the V2.6 skill workflow. It helps you inspect workspace artifacts, check phase readiness, generate prompts for different harnesses, prepare safe copied runs and organize revision tasks.

```text
Backend: FastAPI on http://127.0.0.1:8000
Frontend: Vue 3 + Vite on http://127.0.0.1:5173
First-class mode: Manual harness
Adapter policy: prepare safe copied runs by default
Source of truth: local V2.6 workspace files
```

## Start

```powershell
cd D:\WorkSpace_MathModel\app
.\start.bat
```

Open:

```text
http://127.0.0.1:5173
```

## Configuration

The backend reads the parent repo by default. Override with `backend\.env`:

```text
MATHMODEL_ROOT=D:\WorkSpace_MathModel
WORKSPACE_ROOT=D:\WorkSpace_MathModel\workspaces
EXAMPLES_ROOT=D:\WorkSpace_MathModel\examples
```

## Implemented Capabilities

### Stage 1 MVP polish

- Create V2.6 workspaces from the UI.
- Read Markdown, JSON, text, image and PDF artifacts.
- Generate phase-specific prompts for Manual, Codex, Claude Code and OpenCode.
- Record prompt, audit, upload and adapter events in `runs/control-center-history.jsonl`.

### Stage 2 workflow control

- Dashboard recommendations from audit issues and missing required artifacts.
- Phase readiness checks for inputs, outputs, gate status and next action.
- Generate revision tasks into `reports/REVISION_ACTIONS_CONTROL.md`.
- Upload problem statements, attachments and data files into `source/`.

### Stage 3 harness adapter layer

- `GET /api/harnesses` reports available adapters.
- `POST /api/workspaces/{id}/harness/prepare` creates a safe copied run workspace by default.
- Prepared runs write `CONTROL_PROMPT_PHASE_<n>.md` into the copied workspace and return a command preview.
- No managed adapter auto-executes a CLI in this version.

## Safety

The repository ignores local contest data and runtime state:

```text
workspaces/
examples/**/source/
examples/**/runs/
**/control-center-history.jsonl
.env
.venv
node_modules/
dist/
```

Do not force-add those paths unless you are intentionally publishing sanitized demo data.

## Manual Harness Flow

1. Select or create a workspace.
2. Upload source files if needed.
3. Review dashboard recommendations and phase readiness.
4. Generate or prepare a prompt for the target harness.
5. Run the prompt manually in Codex, Claude Code, OpenCode or another agent.
6. Return to the UI, refresh, run audit and generate revision tasks if needed.

## V2.6 Phase Mapping

```text
Bootstrap: mm-start-contest-v2
Phase 0:  mm-problem-intake
Phase 1:  mm-model-strategy
Phase 2:  mm-data-experiment
Phase 3:  mm-paper-build
Phase 4:  mm-contest-review
Phase 5:  mm-revision-integrator
Phase 6:  mm-final-verify
```

## Verification

Backend:

```powershell
cd D:\WorkSpace_MathModel\app\backend
python -m py_compile (Get-ChildItem -Path app -Recurse -Filter *.py | ForEach-Object FullName)
python -m pytest tests -q
```

Frontend:

```powershell
cd D:\WorkSpace_MathModel\app\frontend
pnpm build
```
