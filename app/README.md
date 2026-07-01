# MathModel Control Center

Version: 0.2.0

Local full-stack control center for MathModelAgent V2.3 workspaces.

新手请先读：[MathModel Control Center 小白使用指南](../docs/control-center-beginner-guide.md)

- Backend: FastAPI on `http://127.0.0.1:8000`
- Frontend: Vue 3 + Vite on `http://127.0.0.1:5173`
- First-class mode: Manual harness
- Adapter policy: prepare safe copied runs; do not auto-execute Codex, Claude Code, or OpenCode
- Source of truth: local V2.3 workspace files

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

Stage 1 MVP polish:

- Create V2.3 workspaces from the UI.
- Read Markdown, JSON, text, image, and PDF artifacts.
- Generate phase-specific prompts for Manual, Codex, Claude Code, and OpenCode.
- Record prompt/audit/upload/adapter events in `runs/control-center-history.jsonl`.

Stage 2 workflow control:

- Dashboard recommendations from audit issues and missing required artifacts.
- Phase readiness checks for inputs, outputs, gate status, and next action.
- Generate revision tasks into `reports/REVISION_ACTIONS_CONTROL.md`.
- Upload problem statements, attachments, and data files into `source/`.

Stage 3 harness adapter layer:

- `GET /api/harnesses` reports available adapters.
- `POST /api/workspaces/{id}/harness/prepare` creates a safe copied run workspace by default.
- Prepared runs write `CONTROL_PROMPT_PHASE_<n>.md` into the copied workspace and return a command preview.
- No managed adapter auto-executes a CLI in this version.

## Safety

The repository ignores local contest data and runtime state:

- `workspaces/`
- `examples/**/source/`
- `examples/**/runs/`
- `**/control-center-history.jsonl`
- `.env`, `.venv`, `node_modules`, `dist`

Do not force-add those paths unless you are intentionally publishing sanitized demo data.

## Manual Harness Flow

1. Select or create a workspace.
2. Upload source files if needed.
3. Review dashboard recommendations and phase readiness.
4. Generate or prepare a prompt for the target harness.
5. Run the prompt manually in Codex, Claude Code, OpenCode, or another agent.
6. Return to the UI, refresh, run audit, and generate revision tasks if needed.

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
