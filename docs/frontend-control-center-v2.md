# MathModel Control Center v2

**Version**: V2.7-alpha
**Frontend version**: 0.2.0
**LangGraph Runtime**: v1.0-alpha

## Purpose

Control Center v2 is the local full-stack web console for MathModelAgent V2.7-alpha. It provides a GUI for workspace inspection, LangGraph Runtime phase execution, copied run workspace artifact browsing, and benchmark report viewing.

It is **not** a cloud service. Everything runs locally at `http://127.0.0.1:5173` (frontend) and `http://127.0.0.1:8000` (backend).

## Feature Map

| Page | Nav Icon | Purpose |
|---|---|---|
| Overview | Dashboard | Audit status strip, phase timeline, recommendations, issues, revision tasks |
| Phase | Gauge | Per-phase input/output artifacts, prompt generation, harness preparation |
| Artifacts | FileText | Workspace file index with search and quick filter groups (Core Gates, LangGraph Reports, Evidence, Review) |
| Console | TerminalSquare | Manual harness prompt generation + run history |
| LangGraph | Workflow | Runtime status, run config form, run summary, 7-column phase results table, sandbox/paper/revision status cards, files lists, audit JSON preview |
| Runs | FolderOpen | Run workspace browser: list copied runs under `source/runs/`, browse artifacts with filters, preview markdown/JSON/image/PDF |
| Benchmark Lab | BarChart3 | Report browser (read-only) for fixture, real_workspace, provider, and multi_model reports; category/provider filters; multi-model metadata comparison table; safe provider=none launcher; legacy 2022C audit table |
| Settings | Settings | New workspace creation, source file upload, backend health check, harness adapter status |

## LangGraph Runtime Panel

The LangGraph page provides a full interface to the LangGraph Phase Runner:

- **Runtime Status card**: `available`, version, `import_error`, note
- **Run Config card**: mode dropdown (all 8 modes), phase (P0-P6), provider, model, copy_workspace checkbox, run_name, temperature, max_tokens
- **Run Summary card**: `status`, `contest_status`, `mode`, `provider`, `model`, `run_workspace`, `completed_phases`, `paused_at`, `needs_human`, `human_gate_required`, `human_gate_file`
- **Phase Results table**: 7 columns (Phase, Strategy, Status, Sandbox, Paper, Revision, Notes)
- **Sandbox · Paper · Revision card**: `sandbox_status`, `paper_sandbox_status`, `revision_sandbox_status`, manifest flags, path chips for claim_trace, method_matrix, paper_build_report, revision_status
- **Files card**: `files_planned`, `files_written`, `files_rejected`, report paths
- **Audit card**: `pre_audit`, `post_audit`, `final_audit` JSON previews, issues list

Default configuration: `contest_graph_v3`, `provider=none`, `copy_workspace=true`.

## Run Workspace Browser

The Runs page allows users to browse LangGraph outputs that land in copied run workspaces under `source/runs/`:

- **Run Workspace List**: reverse-chronological list with LG/AR/PP badges (LangGraph report, Agent Runs, Phase Plan)
- **Run Artifact List**: scoped file listing with quick filter groups (LangGraph, Evidence, Review, Paper)
- **Run Artifact Preview**: markdown renderer, JSON/text viewer, image preview, PDF iframe

All read paths are restricted to `runs/{run_name}/` only. Path traversal (`..`) and absolute paths are rejected by the backend.

## Benchmark Lab

The Benchmark page is a read-only report browser:

- **Overview**: total reports count, breakdown by category (fixture, real_workspace, provider, multi_model)
- **Report List**: filterable by category and provider, click to select
- **Report Preview**: markdown-rendered or JSON-prettified with summary fields
- **Multi-Model Compare**: metadata-level comparison table (Report, Provider, Mode, Workspace, Category, Size)
- **Safe Benchmark Launcher**: provider=none only, contest_graph_v3 only, copy_workspace=true enforced
- **Legacy 2022C Audit**: classic per-workspace status/worst/figures/pages/issues table

## Safety Boundaries

Control Center v2 enforces these safety rules at the backend API level:

| Boundary | Mechanism |
|---|---|
| Human Gate not bypassed | Frontend never writes `HUMAN_MODEL_REVIEW.md` or `MODELING_DECISION.md` |
| No auto-verify | Frontend never writes `VERIFY_REPORT.md` |
| Safe launcher | `POST /api/workspaces/{id}/benchmarks/langgraph-safe` rejects `provider != none`, `mode != contest_graph_v3`, `copy_workspace != true` |
| Run artifact isolation | Run artifact API resolves against `source/runs/{name}/` only; `..` rejected |
| Benchmark report isolation | Report API only scans `docs/`, `docs/real_benchmarks/`, `docs/benchmarks/`; report IDs are SHA256 hashes, not client paths |
| No workspace data leak | Benchmark API does not read `workspaces/` or private files |
| No API key management | No API key storage, transmission, or prompting in the frontend |

## How to Run Locally

```powershell
# Backend
cd app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (separate terminal)
cd app/frontend
pnpm install
pnpm run dev
```

Open `http://127.0.0.1:5173`.

## Validation Commands

```bash
# Frontend build (vue-tsc + vite)
cd app/frontend && pnpm run build

# Backend tests (all suites)
python -m pytest tests/test_langgraph_api.py -q
python -m pytest tests/test_benchmark_reports_api.py -q
python -m pytest tests/test_run_workspace_artifacts_api.py -q
python -m pytest tests/test_safe_langgraph_benchmark_api.py -q
```

## Known Limitations

- No WebSocket or real-time streaming
- No real API benchmark launcher (only provider=none safe baseline)
- No automatic Human Gate approval
- No full Playwright/Cypress E2E test framework; manual smoke test documented at `docs/testing/frontend-langgraph-e2e-smoke.md`
- Provider model selector does not store API keys (keys must be set via environment variables)
- Benchmark report list requires a backend restart after new reports are added to `docs/`
- Run workspace IDs are SHA256 hashes, not human-readable in URLs
