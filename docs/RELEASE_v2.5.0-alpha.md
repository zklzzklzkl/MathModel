# MathModelAgent v2.5.0-alpha Release Notes

## Overview

This is the **alpha release** of the LangGraph Runtime at `contest_graph_v3`, the first version to achieve a **complete safe closed-loop** from problem intake through revision to audit-only final verification. It ships with a Benchmark Arena and 13 release stabilization tests.

**Tag**: `v2.5.0-alpha`
**Commit**: `0e184c2`
**Branch**: `codex/control-center-guide-release`
**Test Result**: 112 passed, 1 skipped, 1 warning

## What's New

### contest_graph_v3: Complete Safe Closed-Loop

```
Phase 0  ────────────────── llm_plan / dry-run
Phase 1  ────────────────── phase_execute (model strategy)
  │
  ├─ Human Gate ─────────── HUMAN_MODEL_REVIEW.md (MANDATORY, manual)
  │
Phase 2  ────────────────── Sandbox Executor (python, pytest in run workspace)
Phase 3  ────────────────── Paper Draft Sandbox (paper/ + evidence trace files)
Phase 4  ────────────────── phase_execute (contest review, PAPER_SCORECARD)
Phase 5  ────────────────── Revision Integrator Sandbox (NEW — reads REVISION_ACTIONS.md)
Phase 6  ────────────────── Audit-Only (no VERIFY_REPORT.md, no final PASS claim)
```

### Phase 5 Revision Integrator Sandbox

Phase 5 is upgraded from `llm_plan`-only to a controlled sandbox that:
- Reads `reports/REVISION_ACTIONS.md` and parses BLOCKER/HIGH items
- Performs batch-validated writes to `paper/` and allowed `reports/`
- Writes `reports/REVISION_STATUS.md` with resolution tracking
- Rejects the entire batch if any file_writes path is illegal
- Rolls back partial writes on failure
- Never fabricates results, metrics, or citations
- Never upgrades weak claims to strong
- Never deletes BLOCKER/HIGH items to pretend resolution

Allowed Phase 5 writes: `paper/main.tex`, `paper/main.typ`, `paper/README.md`, `reports/CLAIM_TRACE.md`, `reports/METHOD_IMPLEMENTATION_MATRIX.md`, `reports/PAPER_BUILD_REPORT.md`, `reports/REVISION_STATUS.md`, `reports/REFINEMENT_LOG.md`

Forbidden: `source/`, `code/`, `figures/`, `results/`, `HUMAN_MODEL_REVIEW.md`, `MODELING_DECISION.md`, `VERIFY_REPORT.md`

### Benchmark Arena

`scripts/langgraph_benchmark.py` — batch benchmark runner that:
- Scans a directory of workspace fixtures
- Runs `contest_graph_v3` with `provider=none`
- Collects per-phase sandbox/audit/human-gate status
- Outputs `LANGGRAPH_BENCHMARK_REPORT.md` + `.json`

Three benchmark fixture scenarios:
1. **human_gate_pause** — v3 stops at Human Gate without approval
2. **full_minimal_flow** — all 0-6 phases complete with sandboxes
3. **revision_required** — HIGH items force REVISION_REQUIRED, no PASS claimed

### Release Stabilization (13 tests)

`tests/test_langgraph_benchmark.py` verifies:
- v3 never writes `VERIFY_REPORT.md`, `MODELING_DECISION.md`, `HUMAN_MODEL_REVIEW.md`
- Phase 2/3/5 sandboxes reject forbidden paths with batch rejection
- Phase 6 is audit-only, never claims final PASS
- Contest graph report exists with all required sections
- `AGENT_RUNS.md` has entries for sandbox phases 2, 3, 5
- History includes `langgraph_contest_graph_v3` event
- Benchmark report generation produces valid JSON and Markdown

## Safety Guarantees (All Versions)

- Never auto-writes `VERIFY_REPORT.md`
- Never auto-writes `MODELING_DECISION.md`
- Never auto-writes `HUMAN_MODEL_REVIEW.md`
- Phase 2 sandbox: forbid `paper/`, `source/`, destructive commands, shell pipes
- Phase 3 sandbox: forbid `code/`, `results/`, `source/`
- Phase 5 sandbox: forbid `code/`, `results/`, `source/`, core gate reports
- Phase 6 audit-only: never claims final PASS
- All sandbox execution in copied run workspace only
- All benchmarks use `provider=none`, no external API dependency
- V2 skills, RAG capability layer, human gates, and `audit_v2_run.py` preserved

## Files Changed

| File | Δ | Purpose |
|---|---|---|
| `app/backend/app/langgraph_runner.py` | +640 | Phase 5 sandbox + contest_graph_v3 orchestrator |
| `app/backend/app/langgraph_state.py` | +4 | Revision sandbox fields |
| `app/backend/app/main.py` | +3 | v3 API response mapping |
| `app/backend/app/models.py` | +4 | `contest_graph_v3` mode + revision response fields |
| `scripts/langgraph_benchmark.py` | NEW | Batch benchmark CLI |
| `tests/test_langgraph_benchmark.py` | NEW | 13 benchmark + stabilization tests |
| `CLAUDE.md` | +130/-30 | Updated architecture docs |
| `README.md` | +1 | LangGraph Runtime status line |
| `docs/langgraph-runner.md` | +125/-2 | v3 + Benchmark Arena documentation |
| `docs/testing/langgraph-phase-runner.tdd.md` | +67 | v3 TDD evidence table |

## Backward Compatibility

All existing modes (`dry_run`, `llm_plan`, `controlled_apply`, `phase_execute`, `contest_graph_v0`, `contest_graph_v1`, `contest_graph_v2`) continue to work. `contest_graph_v3` is additive — no breaking changes to models, API, or runtime behavior.

## Known Limitations

- LangGraph optional dependency not installed in CI; tests use fake compiled graph
- No multi-model comparison yet (DeepSeek vs OpenAI vs Claude) — this is the next step
- Paper sandbox does not compile LaTeX/Typst
- No frontend UI for benchmark results
- Workspace copy for run uses filesystem copy, not git worktree isolation

## Next Steps (Roadmap)

1. **Benchmark 02**: Multi-model comparison on the same benchmark fixtures
2. **Benchmark 03**: Historical contest workspace replay
3. **Scorecard-based ranking**: Automated scoring across backends
4. **Real LangGraph integration test**: With optional dependency installed
5. **Frontend benchmark dashboard**: Visual comparison in Control Center

Do NOT add `contest_graph_v4` until Benchmark Arena proves v3 stability across backends.

## Installation

```bash
git checkout v2.5.0-alpha
pip install -r app/backend/requirements.txt
# Optional: pip install -r app/backend/requirements-langgraph.txt
python -m pytest -q
```

## Verification

```bash
python -m pytest -q                                    # 112 passed, 1 skipped, 1 warning
python -m py_compile app/backend/app/langgraph_runner.py  # clean
python -m py_compile scripts/langgraph_benchmark.py       # clean
git diff --check                                       # CRLF warnings only
```
