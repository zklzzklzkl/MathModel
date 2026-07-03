# MathModelAgent V2.7-alpha Release Notes

**Date**: 2026-07-03
**Tag**: v2.7-alpha (proposed)

## Release Identity

| Component | Version |
|---|---|
| Project | V2.7-alpha |
| LangGraph Runtime | v1.0-alpha |
| Control Center | v2 |
| Main graph mode | contest_graph_v3 |
| Frontend | Vue 3 + Pinia + TypeScript + Vite |
| Backend | FastAPI |

## Highlights

- **LangGraph Runtime Panel** — full GUI for `contest_graph_v3` with 7 information cards (runtime status, run config, run summary, phase results table, sandbox/paper/revision, files, audit)
- **Run Workspace Browser** — browse, filter, and preview artifacts inside copied run workspaces under `source/runs/`
- **Benchmark Lab** — read-only benchmark report browser with 5 sections (fixture, real_workspace, provider, multi_model, legacy 2022C)
- **Safe provider=none benchmark launcher** — one-click `contest_graph_v3` run with enforced `provider=none`, `copy_workspace=true`; never calls real APIs
- **Benchmark report browser API** — `GET /api/benchmark-reports` + `GET /api/benchmark-reports/{id}` with SHA256-hash IDs and docs-only path safety
- **Run workspace artifact API** — `GET /api/workspaces/{id}/runs` + artifact listing and read endpoints scoped to `source/runs/`
- **Multi-model compare view** — metadata-level comparison table across all discovered benchmark reports
- **Control Center v2 docs** — `docs/frontend-control-center-v2.md` (feature map, safety boundaries) and `docs/frontend-api-contract.md` (18+ endpoints)
- **E2E smoke test report** — `docs/testing/frontend-langgraph-e2e-smoke.md` documenting real contest_graph_v3 run results
- **Security regression tests** — 41 tests across 4 suites covering path traversal, env file exclusion, provider rejection, source workspace immutability

## LangGraph Runtime

`contest_graph_v3` connects all 7 phases through a safe, human-gated execution graph:

| Phase | Behavior |
|---|---|
| 0 (Problem Intake) | `llm_plan` only |
| 1 (Model Strategy) | `phase_execute` with allowlisted Phase 1 report writes |
| Human Gate | Required; graph stops if `HUMAN_MODEL_REVIEW.md` is missing or lacks approval signal |
| 2 (Experiment) | Sandbox executor: only `python code/*.py` and scoped `pytest`, writes restricted to `code/`, `figures/`, `results/`, and allowlisted reports |
| 3 (Paper Draft) | Paper sandbox: writes `paper/` and evidence trace reports only; requires `RESULTS_MANIFEST.json` |
| 4 (Contest Review) | `phase_execute` with allowlisted Phase 4 report writes |
| 5 (Revision) | Revision sandbox: reads `REVISION_ACTIONS.md`, writes revised `paper/` and evidence reports |
| 6 (Final Verify) | Audit-only; never writes `VERIFY_REPORT.md` |

Key invariants:
- Graph never writes `VERIFY_REPORT.md`
- Graph never writes `HUMAN_MODEL_REVIEW.md` or `MODELING_DECISION.md`
- Phase 2 sandbox rejects `rm`, `curl`, `pip install`, shell metacharacters
- Phase 3/5 sandboxes reject writes to `code/`, `results/`, `source/`
- All writes roll back on violation

## Control Center v2

8-page local web console at `http://127.0.0.1:5173`:

| Page | Nav | Purpose |
|---|---|---|
| Overview | Dashboard | Audit strip, phase timeline, recommendations, issues, revision tasks |
| Phase | Gauge | Per-phase I/O artifacts, prompt generation, harness preparation |
| Artifacts | FileText | File index with search and 4 group quick filters |
| Console | TerminalSquare | Prompt generation + run history |
| LangGraph | Workflow | Full LangGraph Runtime Panel (7 cards) |
| Runs | FolderOpen | Run workspace browser (list, filter, preview) |
| Benchmark Lab | BarChart3 | Report browser, multi-model compare, safe launcher, legacy 2022C |
| Settings | Settings | Workspace creation, source upload, health check, harness status |

## Benchmark and Reports

- **provider=none safety baseline**: contest_graph_v3 can run without any external API; all phases execute plan-only where real content generation is expected
- **Benchmark report browser**: auto-discovers reports under `docs/`, `docs/real_benchmarks/`, `docs/benchmarks/`; supports markdown and JSON with summary extraction
- **Multi-model compare**: metadata-level table comparing provider, mode, workspace, category, and size across reports
- **Safe Launcher**: enforced `provider=none` only — `deepseek`, `openai-compatible`, and `copy_workspace=false` are rejected at the API level. **This does not represent real LLM automatic modeling quality.**

## Safety Boundaries

| Boundary | Mechanism |
|---|---|
| No auto-verify | Frontend and backend never write `VERIFY_REPORT.md` |
| Human Gate preserved | `HUMAN_MODEL_REVIEW.md` is a manual-only gate file |
| Safe Launcher enforcement | `POST .../benchmarks/langgraph-safe` rejects `provider != none`, `mode != contest_graph_v3`, `copy_workspace != true` |
| Run artifact isolation | All paths resolved against `source/runs/{name}/` only; `..` and absolute paths rejected |
| Benchmark report isolation | Only `docs/`, `docs/real_benchmarks/`, `docs/benchmarks/`; report IDs are SHA256 hashes |
| No workspace data leak | Benchmark API never returns workspace files |
| No API key management | Frontend has no API key storage, transmission, or prompting UI |

## Validation Commands

```bash
# Frontend
cd app/frontend && pnpm run build

# LangGraph API
python -m pytest tests/test_langgraph_api.py -q

# Benchmark reports API
python -m pytest tests/test_benchmark_reports_api.py -q

# Run workspace artifacts API
python -m pytest tests/test_run_workspace_artifacts_api.py -q

# Safe benchmark launcher API
python -m pytest tests/test_safe_langgraph_benchmark_api.py -q

# Full regression
python -m pytest tests/ -q
```

## Known Limitations

- **No WebSocket or real-time streaming** — polling-based refresh only
- **No full Playwright/Cypress E2E test framework** — manual smoke test documented in `docs/testing/frontend-langgraph-e2e-smoke.md`
- **No real API benchmark launcher** — Safe Launcher is `provider=none` only; real DeepSeek/OpenAI benchmarks must be run via CLI scripts (`scripts/real_provider_benchmark.py`)
- **No automatic Human Gate approval** — `HUMAN_MODEL_REVIEW.md` must be manually created and approved
- **provider=none does not represent real LLM modeling quality** — the dry-run adapter produces skeleton PhasePlans; real modeling strategy requires a provider
- **Benchmark report list requires backend restart** after new reports are added to `docs/`
- **Run workspace IDs are SHA256 hashes** — not human-readable in URLs
- **No API key management UI** — keys must be set via environment variables (`MATHMODEL_LLM_API_KEY`)

## Upgrade Notes

From V2.6 or early V2.7-alpha:

- **Control Center v2** replaces the old `V2.6 workspace shell`. The sidebar now has 7 navigation items (was 6).
- **LangGraph** is the primary `contest_graph_v3` execution interface. The old console/harness prompt generator is still available under "执行".
- **Benchmark Lab** replaces the single-table 2022C benchmark page. Legacy 2022C audit is retained as a sub-card.
- **Runs** page is new — browse copied run workspace artifacts that were previously only accessible via filesystem.
- **No breaking API changes** — all V2.6-era endpoints are preserved.
- **No migration required** — existing workspaces and run history continue to work.
