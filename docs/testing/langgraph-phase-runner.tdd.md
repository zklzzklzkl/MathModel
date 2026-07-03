# TDD Evidence: LangGraph Phase Runner MVP

## Source Plan

Derived from the user request to add an optional LangGraph dry-run phase runner under `app/backend` without changing V2 skills, RAG, audit, workspace, or prompt systems.

## User Journeys

- As a Control Center user, I want `/api/langgraph/status` to report whether LangGraph is installed, so the base backend can start even without optional dependencies.
- As a phase-runner caller, I want a clear controlled error when LangGraph is missing, so setup problems do not crash the app.
- As a future provider-adapter developer, I want dry-run graph state, prompt, pre/post audit, report, and history written in a copied run workspace, so provider execution can be added later safely.

## RED Evidence

Command:

```powershell
python -m pytest tests\test_langgraph_runner.py -q
```

Initial result:

```text
ImportError: cannot import name 'langgraph_runner' from 'app'
```

This was expected because the runner module did not exist yet.

## GREEN Evidence

Commands:

```powershell
python -m pytest -q
$files = @(Get-ChildItem app\backend\app -Filter *.py | ForEach-Object { $_.FullName }) + @(Get-ChildItem scripts -Filter *.py | ForEach-Object { $_.FullName }) + @((Resolve-Path skills\_references\scripts\audit_v2_run.py).Path); python -m py_compile @files
```

Results:

```text
21 passed, 1 skipped, 1 warning
py_compile passed
```

The skipped test is the optional installed-LangGraph dry-run integration check; the current environment reports `No module named 'langgraph'`.

## API Smoke

A temporary uvicorn process was started and stopped. Checked:

```text
health True
langgraph_available False
langgraph_note Install optional dependencies with: pip install -r app/backend/requirements-langgraph.txt
```

## Test Specification

| # | What is guaranteed | Test file or command | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | LangGraph status does not crash when optional dependency is missing. | `tests/test_langgraph_runner.py::test_langgraph_status_without_install_does_not_crash` | unit | PASS |
| 2 | Running without LangGraph raises a clear setup error. | `tests/test_langgraph_runner.py::test_run_langgraph_phase_without_install_has_clear_error` | unit | PASS |
| 3 | Status API returns optional dependency guidance. | `tests/test_langgraph_api.py::test_langgraph_status_endpoint_reports_optional_dependency` | API | PASS |
| 4 | Run API returns 501 when LangGraph is missing. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_returns_501_when_dependency_missing` | API | PASS |
| 5 | If LangGraph is installed, dry-run writes prompt/report/history in copied run workspace. | `tests/test_langgraph_runner.py::test_langgraph_dry_run_writes_reports_and_history` | integration | SKIPPED in current env |
| 6 | Run workspace path escape is rejected without needing LangGraph installed. | `tests/test_langgraph_runner.py::test_langgraph_dry_run_rejects_run_workspace_escape` | unit | PASS |

## Known Gaps

- Real LangGraph dry-run execution was not run in this environment because the optional dependency is not installed.
- Real installed-LangGraph `llm_plan` execution was not run in this environment because the optional dependency is not installed.
- `managed_apply` is intentionally not implemented.
- No frontend UI was added in this MVP.

---

# TDD Evidence: LangGraph LLM Plan Provider Adapter

## Source Plan

Derived from the user request to add `llm_plan` as a provider-backed planning mode while preserving dry-run, V2 skills, RAG, Control Center, audit scripts, and human gates.

## User Journeys

- As a provider-adapter developer, I want a small adapter interface with dry-run and OpenAI-compatible implementations, so DeepSeek can be wired without making OpenAI SDK a base dependency.
- As a Control Center caller, I want `llm_plan` to produce structured PhasePlan files in a copied run workspace, so I can review a plan before any execution.
- As a safety reviewer, I want invalid provider output to be captured as raw output with `PLAN_PARSE_FAILED`, so bad JSON is not treated as an actionable plan.

## RED Evidence

Command:

```powershell
python -m pytest tests/test_model_adapters.py tests/test_langgraph_runner.py tests/test_langgraph_api.py -q
```

Initial result:

```text
ModuleNotFoundError: No module named 'app.model_adapters'
```

This was expected because the model adapter layer and PhasePlan schema did not exist yet.

## GREEN Evidence

Command:

```powershell
python -m pytest tests/test_model_adapters.py tests/test_langgraph_runner.py tests/test_langgraph_api.py -q
```

Result:

```text
11 passed, 1 skipped, 1 warning
```

The skipped test is the installed-LangGraph dry-run integration check; `llm_plan` file output is covered with a fake compiled graph so it does not require optional LangGraph in this environment.

## Test Specification

| # | What is guaranteed | Test file or command | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | DryRunAdapter returns JSON that validates as PhasePlan. | `tests/test_model_adapters.py::test_dry_run_adapter_returns_parseable_phase_plan` | unit | PASS |
| 2 | OpenAI-compatible providers fail clearly when API key is missing and do not expose a key. | `tests/test_model_adapters.py::test_openai_compatible_adapter_requires_api_key` | unit | PASS |
| 3 | API accepts `mode="llm_plan"` and returns new plan fields. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_accepts_llm_plan_mode` | API | PASS |
| 4 | `llm_plan` with provider `none` writes JSON plan, Markdown plan, run report, and history without a real provider. | `tests/test_langgraph_runner.py::test_langgraph_llm_plan_with_none_provider_writes_plan_files` | integration | PASS |
| 5 | Invalid provider JSON writes raw output and returns `PLAN_PARSE_FAILED`. | `tests/test_langgraph_runner.py::test_langgraph_llm_plan_invalid_json_writes_raw_output` | integration | PASS |
| 6 | Provider adapter errors return HTTP 400 instead of crashing the backend. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_returns_400_for_provider_error` | API | PASS |

---

# TDD Evidence: LangGraph Controlled Apply

## Source Plan

Derived from the user request to add `controlled_apply` for Phase 1 and Phase 4 report-only writes with strict allowlists, rollback, audit, history, and no human-gate bypass.

## User Journeys

- As a Control Center caller, I want Phase 1 controlled apply to write only model-strategy draft reports, so I can review candidates without automatically approving a route.
- As a contest reviewer, I want Phase 4 controlled apply to write only scorecard/action reports, so revision stays traceable and human-reviewed.
- As a safety reviewer, I want illegal paths to reject the whole batch and write no core files, so model output cannot escape the run workspace or bypass gates.

## RED Evidence

Command:

```powershell
python -m pytest tests/test_langgraph_runner.py tests/test_langgraph_api.py -q
```

Initial result:

```text
18 failed, 7 passed, 1 skipped, 1 warning
AttributeError: module 'app.langgraph_runner' has no attribute 'apply_router_node'
AttributeError: module 'app.langgraph_runner' has no attribute 'allowed_apply_paths'
ValueError: LangGraph Phase Runner supports mode='dry_run' or mode='llm_plan'.
```

This was expected because controlled apply nodes, allowlist helpers, schema fields, and API mode support did not exist yet.

## GREEN Evidence

Command:

```powershell
python -m pytest tests/test_langgraph_runner.py tests/test_langgraph_api.py -q
```

Result:

```text
25 passed, 1 skipped, 1 warning
```

The skipped test is the installed-LangGraph dry-run integration check; controlled apply uses a fake compiled graph in tests, so it is covered without optional LangGraph installed.

## Test Specification

| # | What is guaranteed | Test file or command | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | Phase 1 and Phase 4 allowlists are exact and other phases have no apply paths. | `tests/test_langgraph_runner.py::test_allowed_apply_paths_are_phase_specific` | unit | PASS |
| 2 | Forbidden paths including paper, parent traversal, absolute path, human gate, modeling decision, verify report are rejected. | `tests/test_langgraph_runner.py::test_validate_apply_path_rejects_forbidden_targets` | unit | PASS |
| 3 | Phase 1 controlled apply writes only allowed model-strategy reports and does not write human gate files. | `tests/test_langgraph_runner.py::test_controlled_apply_phase1_writes_allowed_reports_and_logs` | integration | PASS |
| 4 | Phase 4 controlled apply writes only allowed contest-review reports. | `tests/test_langgraph_runner.py::test_controlled_apply_phase4_writes_allowed_reports` | integration | PASS |
| 5 | Mixed illegal writes reject the whole batch and write no core reports. | `tests/test_langgraph_runner.py::test_controlled_apply_rejects_mixed_illegal_writes_without_core_changes` | integration | PASS |
| 6 | Missing `file_writes` produces plan-only output and writes no core reports. | `tests/test_langgraph_runner.py::test_controlled_apply_without_file_writes_is_plan_only` | integration | PASS |
| 7 | Simulated write failure rolls back partial core writes. | `tests/test_langgraph_runner.py::test_controlled_apply_rolls_back_after_write_failure` | integration | PASS |
| 8 | API accepts `mode="controlled_apply"` and returns files/needs_human fields. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_accepts_controlled_apply_mode` | API | PASS |
| 9 | API returns controlled 400 for unsupported controlled_apply phases. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_returns_400_for_controlled_apply_bad_phase` | API | PASS |

---

# TDD Evidence: LangGraph Single Phase Executor v1

## Source Plan

Derived from the user request to add `phase_execute` as a single-phase executor that reuses `llm_plan`, `PhasePlan`, `file_writes`, `controlled_apply`, audit, history, `AGENT_RUNS.md`, and `LANGGRAPH_RUN_REPORT.md`.

## User Journeys

- As a model-strategy user, I want Phase 1 to run from prompt to plan to controlled report drafts in one call, so I can review candidate routes faster.
- As a contest-review user, I want Phase 4 to run from prompt to scorecard/action drafts in one call, so I can review revision work faster.
- As a safety reviewer, I want `phase_execute` to keep the same allowlist, rollback, audit, and human gate boundaries as controlled apply.

## RED Evidence

Command:

```powershell
python -m pytest tests/test_langgraph_runner.py tests/test_langgraph_api.py -q
```

Initial result:

```text
7 failed, 25 passed, 1 skipped, 1 warning
ValueError: LangGraph Phase Runner supports mode='dry_run', mode='llm_plan', or mode='controlled_apply'.
422 Unprocessable Entity
```

This was expected because `phase_execute`, `apply_diff_path`, and `LANGGRAPH_APPLY_DIFF.md` were not implemented yet.

## GREEN Evidence

Command:

```powershell
python -m pytest tests/test_langgraph_runner.py tests/test_langgraph_api.py -q
```

Result:

```text
32 passed, 1 skipped, 1 warning
```

The skipped test is the installed-LangGraph dry-run integration check; `phase_execute` is covered through the fake compiled graph path.

## Test Specification

| # | What is guaranteed | Test file or command | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | `phase_execute` with provider `none` generates plan-only output plus apply diff and reports. | `tests/test_langgraph_runner.py::test_phase_execute_with_none_provider_generates_plan_only_and_apply_diff` | integration | PASS |
| 2 | Phase 1 provider file_writes are applied through the existing allowlist and do not write human gate files. | `tests/test_langgraph_runner.py::test_phase_execute_phase1_provider_file_writes_are_applied` | integration | PASS |
| 3 | Phase 4 provider file_writes are applied only to scorecard/action reports and do not create final PASS. | `tests/test_langgraph_runner.py::test_phase_execute_phase4_provider_file_writes_are_applied` | integration | PASS |
| 4 | Mixed legal and illegal file_writes reject the whole batch. | `tests/test_langgraph_runner.py::test_phase_execute_rejects_mixed_legal_and_illegal_writes` | integration | PASS |
| 5 | Unsupported phases return `PHASE_NOT_SUPPORTED`. | `tests/test_langgraph_runner.py::test_phase_execute_unsupported_phase_is_rejected` | unit | PASS |
| 6 | API accepts `mode="phase_execute"` and returns `apply_diff_path`. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_accepts_phase_execute_mode` | API | PASS |
| 7 | API returns controlled 400 for unsupported phase_execute phases. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_returns_400_for_phase_execute_bad_phase` | API | PASS |

---

# TDD Evidence: LangGraph Contest Graph v1 Phase 2 Sandbox

## Source Plan

Derived from the user goal objective file requesting `contest_graph_v1`, with Phase 2 `mm-data-experiment` upgraded from plan-only behavior to a copied-workspace sandbox executor and a minimal benchmark smoke fixture in tests.

## User Journeys

- As a contest graph caller, I want `contest_graph_v1` to pause at the Phase 1 human model gate, so experiments cannot start before human approval.
- As an experiment runner, I want Phase 2 to execute only safe Python commands in the copied run workspace, so model routes can produce manifest/report evidence without arbitrary shell access.
- As a safety reviewer, I want illegal commands and paths rejected before execution, so provider output cannot run installers, network fetches, destructive commands, or write forbidden V2 gate files.
- As an auditor, I want `RESULTS_MANIFEST.json`, `EXPERIMENT_LOG.md`, `AGENT_RUNS.md`, and post-audit status recorded, so the experiment loop is traceable.

## RED Evidence

Command:

```powershell
python -m pytest tests\test_langgraph_runner.py tests\test_langgraph_api.py -q
```

Initial result:

```text
16 failed, 37 passed, 1 skipped, 1 warning
AttributeError: module 'app.langgraph_runner' has no attribute 'validate_phase2_commands'
AttributeError: module 'app.langgraph_runner' has no attribute 'run_phase2_sandbox_executor'
ValueError: LangGraph Phase Runner supports mode='dry_run', mode='llm_plan', mode='controlled_apply', mode='phase_execute', or mode='contest_graph_v0'.
422 Unprocessable Entity
```

This was expected because Phase 2 sandbox helpers, `commands` schema, `contest_graph_v1`, and API fields did not exist yet.

## GREEN Evidence

Command:

```powershell
python -m pytest tests\test_langgraph_runner.py tests\test_langgraph_api.py -q
```

Result:

```text
56 passed, 1 skipped, 1 warning
```

The skipped test is the installed-LangGraph dry-run integration check. v1 uses fake graph/provider paths plus real local Python subprocess execution for Phase 2 sandbox smoke coverage.

## Test Specification

| # | What is guaranteed | Test file or command | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | Phase 2 command validator accepts `python -m py_compile code/solve.py` and `python code/solve.py`. | `tests/test_langgraph_runner.py::test_validate_phase2_commands_accepts_safe_python_commands` | unit | PASS |
| 2 | Destructive, network, installer, encoded PowerShell, traversal, and shell-pipe commands are rejected. | `tests/test_langgraph_runner.py::test_validate_phase2_commands_rejects_forbidden_commands` | unit | PASS |
| 3 | Forbidden expected outputs such as `paper/main.tex` are rejected before execution. | `tests/test_langgraph_runner.py::test_validate_phase2_commands_rejects_forbidden_expected_outputs` | unit | PASS |
| 4 | Phase 2 sandbox executes py_compile and a simple Python experiment, producing manifest, results report, experiment log, and workspace history. | `tests/test_langgraph_runner.py::test_phase2_sandbox_executes_python_and_records_manifest_and_logs` | integration | PASS |
| 5 | Missing `RESULTS_MANIFEST.json` creates a minimal empty skeleton and marks `manifest_created_empty`. | `tests/test_langgraph_runner.py::test_phase2_sandbox_creates_empty_manifest_when_missing` | integration | PASS |
| 6 | Phase 2 with no commands is plan-only and does not write experiment log. | `tests/test_langgraph_runner.py::test_phase2_sandbox_without_commands_is_plan_only` | integration | PASS |
| 7 | Illegal Phase 2 command returns `SANDBOX_COMMAND_REJECTED` without execution. | `tests/test_langgraph_runner.py::test_phase2_sandbox_rejects_illegal_command_without_execution` | integration | PASS |
| 8 | Phase 2 sandbox refuses to run directly in the source workspace and requires a copied run workspace. | `tests/test_langgraph_runner.py::test_phase2_sandbox_requires_copied_run_workspace` | unit | PASS |
| 9 | A script that writes forbidden runtime paths such as `paper/main.tex` is detected and rolled back. | `tests/test_langgraph_runner.py::test_phase2_sandbox_rolls_back_forbidden_runtime_write` | integration | PASS |
| 10 | `contest_graph_v1` still pauses at missing human model review and does not enter Phase 2. | `tests/test_langgraph_runner.py::test_contest_graph_v1_pauses_at_human_gate_without_phase2` | integration | PASS |
| 11 | Approved human gate lets v1 run Phase 2 sandbox and continue when audit is clean. | `tests/test_langgraph_runner.py::test_contest_graph_v1_runs_phase2_sandbox_after_gate` | integration | PASS |
| 12 | Rejected Phase 2 command stops v1 before Phase 3. | `tests/test_langgraph_runner.py::test_contest_graph_v1_stops_when_phase2_command_is_rejected` | integration | PASS |
| 13 | API accepts `mode="contest_graph_v1"` and returns sandbox fields. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_accepts_contest_graph_v1_mode` | API | PASS |

## Known Gaps

- The sandbox is command- and path-restricted and runs without a shell, but it is not a kernel/container sandbox.
- `contest_graph_v1` does not write paper drafts, does not bypass human gates, and does not claim final PASS.

## Final Validation

Commands:

```powershell
python -m pytest -q
python -m py_compile app\backend\app\langgraph_runner.py app\backend\app\langgraph_state.py app\backend\app\model_adapters.py app\backend\app\phase_plan.py app\backend\app\models.py app\backend\app\main.py
git diff --check
```

Results:

```text
74 passed, 1 skipped, 1 warning
py_compile passed
git diff --check passed with CRLF warnings only
```

---

# TDD Evidence: LangGraph Contest Graph v2 Phase 3 Paper Sandbox

## Source Plan

Derived from the user request to add `contest_graph_v2`, upgrading Phase 3 from plan-only behavior to a copied-workspace Paper Draft Sandbox with evidence trace files.

## User Journeys

- As a contest graph caller, I want `contest_graph_v2` to preserve the Phase 1 Human Gate and Phase 2 sandbox gate, so paper drafting cannot start before modeling and experiments are ready.
- As a paper drafter, I want Phase 3 to write only paper draft and evidence trace files, so draft generation remains reviewable and cannot mutate code/results/gates.
- As a reviewer, I want claim trace, method implementation matrix, and paper build report generated or safely skeletonized, so every draft claim has an explicit risk/evidence status.
- As a safety reviewer, I want illegal Phase 3 paths and mid-write failures to reject or rollback, so provider output cannot bypass V2 artifacts or final verification.

## RED Evidence

Command:

```powershell
python -m pytest tests\test_langgraph_runner.py tests\test_langgraph_api.py -q
```

Initial result:

```text
14 failed, 56 passed, 1 skipped, 1 warning
AttributeError: module 'app.langgraph_runner' has no attribute 'validate_phase3_writes'
AttributeError: module 'app.langgraph_runner' has no attribute 'run_phase3_paper_sandbox'
ValueError: LangGraph Phase Runner supports mode='dry_run', mode='llm_plan', mode='controlled_apply', mode='phase_execute', mode='contest_graph_v0', or mode='contest_graph_v1'.
422 Unprocessable Entity
```

This was expected because Phase 3 paper sandbox helpers, `contest_graph_v2`, and API fields did not exist yet.

## GREEN Evidence

Command:

```powershell
python -m pytest tests\test_langgraph_runner.py tests\test_langgraph_api.py -q
```

Result:

```text
70 passed, 1 skipped, 1 warning
```

## Test Specification

| # | What is guaranteed | Test file or command | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | Phase 3 validator accepts only paper and evidence trace allowlist paths. | `tests/test_langgraph_runner.py::test_validate_phase3_writes_accepts_allowed_paper_and_evidence_paths` | unit | PASS |
| 2 | Phase 3 validator rejects `code/`, `results/`, `source/`, `VERIFY_REPORT.md`, and path traversal. | `tests/test_langgraph_runner.py::test_validate_phase3_writes_rejects_forbidden_paths` | unit | PASS |
| 3 | Phase 3 paper sandbox writes paper draft, claim trace, method matrix, paper build report, and history. | `tests/test_langgraph_runner.py::test_phase3_paper_sandbox_writes_allowed_files_and_evidence` | integration | PASS |
| 4 | Illegal Phase 3 batch rejects without writing draft files. | `tests/test_langgraph_runner.py::test_phase3_paper_sandbox_rejects_illegal_batch_without_writes` | integration | PASS |
| 5 | Mid-write failure rolls back Phase 3 paper draft writes. | `tests/test_langgraph_runner.py::test_phase3_paper_sandbox_rolls_back_on_write_failure` | integration | PASS |
| 6 | Missing manifest produces a risk skeleton and does not fabricate result text. | `tests/test_langgraph_runner.py::test_phase3_paper_sandbox_missing_manifest_writes_risk_skeleton_not_fake_results` | integration | PASS |
| 7 | `contest_graph_v2` pauses at missing Human Gate and does not enter Phase 2/3. | `tests/test_langgraph_runner.py::test_contest_graph_v2_pauses_at_human_gate_without_phase2_or_phase3` | integration | PASS |
| 8 | `contest_graph_v2` runs Phase 2, then Phase 3, then mandatory Phase 4 review, then Phase 6 audit-only when clean. | `tests/test_langgraph_runner.py::test_contest_graph_v2_runs_phase3_then_phase4_review_and_audit_only_phase6` | integration | PASS |
| 9 | Phase 4 HIGH/BLOCKER after paper drafting becomes `REVISION_REQUIRED`. | `tests/test_langgraph_runner.py::test_contest_graph_v2_marks_revision_required_after_phase4_high` | integration | PASS |
| 10 | API accepts `mode="contest_graph_v2"` and returns paper sandbox fields. | `tests/test_langgraph_api.py::test_langgraph_run_endpoint_accepts_contest_graph_v2_mode` | API | PASS |

## Known Gaps

- Phase 3 writes draft/evidence files only; it does not compile LaTeX/Typst.
- `contest_graph_v2` still does not write `VERIFY_REPORT.md`, bypass `HUMAN_MODEL_REVIEW.md`, or claim final PASS.

## Final Validation

Commands:

```powershell
python -m pytest -q
python -m py_compile app\backend\app\langgraph_runner.py app\backend\app\langgraph_state.py app\backend\app\model_adapters.py app\backend\app\phase_plan.py app\backend\app\models.py app\backend\app\main.py
git diff --check
```

Results:

```text
88 passed, 1 skipped, 1 warning
py_compile passed
git diff --check passed with CRLF warnings only
```

---

# TDD Evidence: LangGraph Contest Graph v3 (Revision Integrator Sandbox + Benchmark Arena)

## Source Plan

Derived from user request to upgrade Phase 5 from `llm_plan`-only to Revision Integrator Sandbox, add mini benchmark fixtures, and verify all release stabilization invariants for contest_graph_v3.

## GREEN Evidence

Command:

```powershell
python -m pytest tests/test_langgraph_runner.py tests/test_langgraph_benchmark.py tests/test_langgraph_api.py -q
```

Results:

```text
112 passed, 1 skipped, 1 warning
py_compile passed
git diff --check passed with CRLF warnings only
```

## Test Specification

### contest_graph_v3 (langgraph_runner.py)

| # | What is guaranteed | Test | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | Phase 5 write validation accepts allowed revision paths. | `test_validate_phase5_writes_accepts_allowed_revision_paths` | unit | PASS |
| 2 | Phase 5 write validation rejects forbidden paths (code, results, source, VERIFY_REPORT, etc.). | `test_validate_phase5_writes_rejects_forbidden_paths` (8 params) | unit | PASS |
| 3 | Missing REVISION_ACTIONS.md — writes status only, does not modify paper. | `test_phase5_revision_sandbox_missing_actions_writes_status_only` | integration | PASS |
| 4 | REVISION_ACTIONS.md present — writes revision status and allowed files. | `test_phase5_revision_sandbox_writes_revision_status_and_allowed_files` | integration | PASS |
| 5 | Illegal batch with forbidden paths — whole batch rejected. | `test_phase5_revision_sandbox_rejects_illegal_batch_without_writes` | integration | PASS |
| 6 | Write failure mid-batch — rollback, no partial writes. | `test_phase5_revision_sandbox_rolls_back_on_write_failure` | integration | PASS |
| 7 | contest_graph_v3 pauses at human gate. | `test_contest_graph_v3_pauses_at_human_gate_without_phase2_or_revision` | integration | PASS |
| 8 | contest_graph_v3 full smoke: all phases 0-6, includes revision. | `test_contest_graph_v3_revision_smoke_runs_to_phase6_audit_only` | integration | PASS |
| 9 | contest_graph_v3 with missing revision actions still reaches audit-only Phase 6. | `test_contest_graph_v3_missing_revision_actions_still_reaches_audit_only` | integration | PASS |

### Benchmark Fixtures (test_langgraph_benchmark.py)

| # | What is guaranteed | Test | Type | Result |
| --- | --- | --- | --- | --- |
| 10 | benchmark_01: v3 stops at Human Gate without approved review. | `test_benchmark_01_human_gate_pause` | integration | PASS |
| 11 | benchmark_02: full minimal flow completes all phases with all sandboxes. | `test_benchmark_02_full_minimal_flow` | integration | PASS |
| 12 | benchmark_03: Phase 4 HIGH forces REVISION_REQUIRED, no PASS claimed. | `test_benchmark_03_revision_required` | integration | PASS |

### Release Stabilization

| # | What is guaranteed | Test | Type | Result |
| --- | --- | --- | --- | --- |
| 13 | v3 never writes VERIFY_REPORT.md. | `test_stabilization_v3_never_writes_verify_report` | integration | PASS |
| 14 | v3 never auto-writes HUMAN_MODEL_REVIEW.md or MODELING_DECISION.md. | `test_stabilization_v3_never_writes_human_gate_files` | integration | PASS |
| 15 | Phase 2 sandbox rejects paper/source writes. | `test_stabilization_phase2_rejects_paper_and_source` | integration | PASS |
| 16 | Phase 3 sandbox rejects code/results writes. | `test_stabilization_phase3_rejects_code_and_results` | integration | PASS |
| 17 | Phase 5 validate rejects VERIFY_REPORT.md path. | `test_stabilization_phase5_rejects_verify_report` | unit | PASS |
| 18 | Phase 6 is audit-only, never writes VERIFY_REPORT.md. | `test_stabilization_phase6_never_writes_verify` | integration | PASS |
| 19 | Contest graph report exists with all required sections. | `test_stabilization_graph_report_exists` | integration | PASS |
| 20 | AGENT_RUNS.md has entries for sandbox phases 2, 3, 5. | `test_stabilization_agent_runs_has_phase2_3_5` | integration | PASS |
| 21 | History includes a langgraph_contest_graph_v3 event. | `test_stabilization_history_has_v3_event` | integration | PASS |
| 22 | Benchmark report generation produces valid JSON and Markdown. | `test_stabilization_benchmark_report_generation` | integration | PASS |

## Scripts

- `scripts/langgraph_benchmark.py` — batch benchmark runner, compiles and passes test assertion.

---

# TDD Evidence: Real Provider Benchmark Stabilization

## Source Plan

Derived from user request to stabilize real API benchmark reports, repair the
DeepSeek Phase 1 `llm_plan` report path, and make provider benchmarks repeatable
without leaking secrets.

## RED Evidence

Command:

```powershell
python -m pytest tests/test_real_provider_benchmark.py -q
```

Initial result:

```text
ModuleNotFoundError: No module named 'scripts.real_provider_benchmark'
```

This was expected because the dedicated real provider benchmark entry point did
not exist yet.

## GREEN Evidence

Command:

```powershell
python -m pytest tests/test_real_provider_benchmark.py -q
```

Result:

```text
4 passed
```

## Test Specification

| # | What is guaranteed | Test | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | JSON reports escape Chinese text, newlines, and control-character edges, then round-trip through `json.loads`. | `test_safe_json_report_escapes_control_characters` | unit | PASS |
| 2 | Simulated `PLAN_READY` provider run writes summary fields for phase, provider, model, planned steps, RAG queries, risks, human gate, and unchanged source verify hash. | `test_run_benchmark_plan_ready_writes_summary_without_secret` | integration | PASS |
| 3 | Provider failures produce a structured benchmark report instead of crashing. | `test_run_benchmark_provider_error_writes_report` | integration | PASS |
| 4 | Existing copied run workspaces can regenerate official JSON/Markdown reports without another API call. | `test_report_from_existing_run_workspace` | integration | PASS |

## Real Report Repair

Command:

```powershell
python scripts/real_provider_benchmark.py --workspace examples/2022C/DeepSeekV4Pro_V2.3 --mode llm_plan --phase 1 --provider deepseek --model deepseek-chat --from-run-workspace examples/2022C/DeepSeekV4Pro_V2.3/runs/20260703-122255-deepseek-llm-plan-phase1-DeepSeekV4Pro_V2.3 --json-out docs/real_benchmarks/LANGGRAPH_DEEPSEEK_LLM_PLAN_PHASE1_DeepSeekV4Pro_V2.3.json --markdown-out docs/real_benchmarks/LANGGRAPH_DEEPSEEK_LLM_PLAN_PHASE1_DeepSeekV4Pro_V2.3.md
```

Result:

- Status: `PLAN_READY`
- Planned steps: 7
- RAG queries: 3
- Risks: 3
- Human gates: 1
- Source `reports/VERIFY_REPORT.md` hash unchanged: true
- Secret hits: 0

## Known Gaps

- No fresh API call was made during this repair because `MATHMODEL_LLM_API_KEY`
  was not set in the current shell.
- Future multi-model comparison should reuse `scripts/real_provider_benchmark.py`
  rather than hand-building reports.

---

# TDD Evidence: Real Provider Comparison MVP

## Source Plan

Derived from the next-step plan to move from one-off DeepSeek Phase 1 reports
to a repeatable multi-provider comparison surface while keeping all real API
calls outside unit tests.

## RED Evidence

Command:

```powershell
python -m pytest tests/test_real_provider_compare.py -q
```

Initial result:

```text
ModuleNotFoundError: No module named 'scripts.real_provider_compare'
```

## GREEN Evidence

Command:

```powershell
python -m pytest tests/test_real_provider_compare.py -q
```

Result:

```text
3 passed
```

## Test Specification

| # | What is guaranteed | Test | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | Provider/model specs parse consistently, including provider-only specs. | `test_parse_provider_specs` | unit | PASS |
| 2 | Multiple simulated providers produce a ranked JSON/Markdown comparison report without real API calls. | `test_compare_real_providers_writes_ranked_reports` | integration | PASS |
| 3 | The deterministic smoke score penalizes missing human gates and secret hits. | `test_quality_score_penalizes_missing_gate_and_secret_hit` | unit | PASS |

## Known Gaps

- The comparison score is a structural PhasePlan smoke score, not a final paper
  quality score.
- Real provider execution still requires local environment keys and should be
  run only after rotating any key that was previously pasted into chat.
