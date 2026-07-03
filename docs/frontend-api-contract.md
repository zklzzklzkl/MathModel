# Frontend API Contract

Control Center v2 frontend depends on these FastAPI endpoints. All endpoints are read-only unless marked `POST`.

---

## Workspace

### `GET /api/workspaces`
- **Purpose**: List all discovered workspaces (from `workspaces/` and `examples/`)
- **Frontend consumer**: Sidebar workspace selector, `store.initialize()`
- **Security**: Returns only workspace metadata (id, name, path, source), no file contents

### `GET /api/workspaces/{workspace_id}/summary`
- **Purpose**: Full workspace audit summary: status, worst_severity, phases, manifest, paper, issues, recommendations
- **Frontend consumer**: Dashboard overview page, phase page
- **Security**: Runs `audit_v2_run.py` read-only

### `GET /api/workspaces/{workspace_id}/artifacts`
- **Purpose**: List all files inside the workspace with type, exists, required flags
- **Frontend consumer**: Artifacts page with quick filters

### `GET /api/workspaces/{workspace_id}/artifact?path=...`
- **Purpose**: Read a single file from the workspace (markdown content, JSON data, or type info)
- **Frontend consumer**: Artifact preview panel
- **Security**: `path` must be relative, no `..`, no workspace escape

### `GET /api/workspaces/{workspace_id}/raw?path=...`
- **Purpose**: Serve raw file bytes for images, PDFs
- **Frontend consumer**: Image preview, PDF iframe
- **Security**: Same path restrictions as `/artifact`

---

## LangGraph Runtime

### `GET /api/langgraph/status`
- **Purpose**: Check if LangGraph optional dependency is installed and available
- **Frontend consumer**: LangGraph page Runtime Status card, `store.loadLangGraphStatus()`
- **Security**: Read-only, returns version and import status

### `POST /api/workspaces/{workspace_id}/langgraph/run`
- **Purpose**: Execute a LangGraph phase run (dry_run, llm_plan, controlled_apply, phase_execute, contest_graph_v0..v3)
- **Frontend consumer**: LangGraph page Run Config card, `store.runLangGraph()`
- **Security**: Optional LangGraph dependency; `copy_workspace=true` copies to `runs/` first; allowlist restricts `controlled_apply` writes; sandbox restricts Phase 2/3/5 writes; Phase 6 is audit-only

---

## Run Workspace Browser

### `GET /api/workspaces/{workspace_id}/runs`
- **Purpose**: List copied run workspaces under `source/runs/` with langgraph_report/agent_runs/phase_plan flags
- **Frontend consumer**: Runs page Run Workspace List, `store.loadRunWorkspaces()`
- **Security**: Only scans `source/runs/` subdirectories; run IDs are SHA256 hashes of directory names

### `GET /api/workspaces/{workspace_id}/runs/{run_id}/artifacts`
- **Purpose**: List files inside a specific run workspace (reports, code, figures, results)
- **Frontend consumer**: Runs page Run Artifact List
- **Security**: Resolves `run_id` via SHA256 hash lookup; only returns files with safe extensions (.md, .json, .txt, .tex, .typ, .py, .png, .jpg, .pdf, .svg, .csv)

### `GET /api/workspaces/{workspace_id}/runs/{run_id}/artifact?path=...`
- **Purpose**: Read a single file from the run workspace
- **Frontend consumer**: Runs page Run Artifact Preview
- **Security**: `path` must be relative, no `..`, no escape from run workspace root

### `GET /api/workspaces/{workspace_id}/runs/{run_id}/raw?path=...`
- **Purpose**: Serve raw file bytes from run workspace (images, PDFs)
- **Frontend consumer**: Run artifact image/PDF preview
- **Security**: Same path restrictions as `/artifact`

---

## Benchmark Report Browser

### `GET /api/benchmark/2022C`
- **Purpose**: Run `audit_benchmark.py` against `examples/2022C/` and return per-workspace audit results
- **Frontend consumer**: Benchmark Lab Legacy 2022C card, `store.loadBenchmark()`
- **Security**: Read-only audit against `examples/2022C/`

### `GET /api/benchmark-reports`
- **Purpose**: List discoverable benchmark reports under `docs/`, `docs/real_benchmarks/`, `docs/benchmarks/`
- **Frontend consumer**: Benchmark Lab report list, `store.loadBenchmarkReports()`
- **Security**: Only scans whitelist directories; only collects files matching `LANGGRAPH_*`, `MULTI_MODEL_*` patterns; report IDs are SHA256 hashes of relative paths

### `GET /api/benchmark-reports/{report_id}`
- **Purpose**: Read a single benchmark report (markdown or JSON) with extracted summary
- **Frontend consumer**: Benchmark Lab report preview
- **Security**: `report_id` is a SHA256 hash resolved against the current scan list, not a filesystem path; file must be within allowed directories

### `POST /api/workspaces/{workspace_id}/benchmarks/langgraph-safe`
- **Purpose**: Run a safe `contest_graph_v3` with `provider=none`, `copy_workspace=true`
- **Frontend consumer**: Benchmark Lab Safe Launcher card, `store.runSafeLangGraphBenchmark()`
- **Security**: Rejects `provider != none` (400), rejects `mode != contest_graph_v3` (400), rejects `copy_workspace != true` (400); runs in copied workspace only; does not write source workspace gate files

---

## Harness Utilities

### `GET /api/harnesses`
- **Purpose**: List available harness adapters (Manual, Codex, Claude Code, OpenCode)
- **Frontend consumer**: Sidebar harness selector, console page

### `POST /api/workspaces/{workspace_id}/prompt`
- **Purpose**: Generate a portable phase prompt for the given phase and harness
- **Frontend consumer**: Phase page, console page, `store.generatePrompt()`

### `POST /api/workspaces/{workspace_id}/harness/prepare`
- **Purpose**: Prepare a copied run workspace and generate a run command preview
- **Frontend consumer**: Console page, `store.prepareHarness()`

### `GET /api/workspaces/{workspace_id}/runs/history`
- **Purpose**: Read run history from `control-center-history.jsonl`
- **Frontend consumer**: Console page history panel

---

## Shared Security Patterns

All path-accepting endpoints enforce:

1. **Relative paths only** — absolute paths rejected
2. **No `..` traversal** — parent directory references rejected
3. **Workspace containment** — resolved path must be within the workspace root
4. **Extension whitelist** — run artifact listing only returns safe file types
5. **SHA256 hash IDs** — benchmark report and run workspace IDs are hashes, not filesystem paths

All POST endpoints that modify files:

1. Write to `runs/` copies by default (`copy_workspace=true`)
2. Are restricted by phase-specific allowlists (`controlled_apply`, sandbox writes)
3. Roll back on failure (sandbox write violations)
4. Never write `HUMAN_MODEL_REVIEW.md`, `MODELING_DECISION.md`, or `VERIFY_REPORT.md`
