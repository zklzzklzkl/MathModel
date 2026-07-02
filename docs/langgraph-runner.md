# LangGraph Phase Runner MVP

LangGraph is an optional execution orchestration layer for the MathModel Control Center backend.

The runner is intentionally conservative:

- `dry_run` mode does not call a model;
- `llm_plan` mode may call an OpenAI-compatible provider, but only to generate a structured plan;
- `controlled_apply` mode may write a small allowlisted set of Markdown reports from a validated plan;
- `phase_execute` mode performs a single safe phase pass: provider plan -> file_writes -> controlled apply -> post-audit -> human next action;
- `contest_graph_v0` mode chains the safe phase strategies across Phase 0-6 and pauses at the model-review human gate;
- no Bash execution;
- no automatic edits to `paper/`, `code/`, `figures/`, `results/`, or V2 core artifacts;
- no replacement of V2 skills, local RAG, human gates, or `audit_v2_run.py`.

It prepares a copied run workspace, builds the existing portable phase prompt, runs pre/post audits, writes a run report, and appends Control Center history. In `llm_plan` mode it also writes a provider-generated phase plan for manual review. In `controlled_apply` mode it can turn validated `file_writes` into low-risk report drafts.

## Community Component Reuse

The runner intentionally uses the official LangGraph `StateGraph` surface when optional dependencies are installed. OpenAI-compatible calls stay inside the existing adapter layer. New optional dependencies must go into `app/backend/requirements-langgraph.txt`; the base Control Center dependencies stay unchanged. No third-party framework replaces the current V2 skills, file-based workspace state, audit script, or human gates.

## Optional Install

Base Control Center usage does not require LangGraph.

Install the optional runner dependencies only when needed:

```powershell
cd D:\WorkSpace_MathModel
pip install -r app\backend\requirements-langgraph.txt
```

The base `app/backend/requirements.txt` intentionally stays lightweight.

## Provider Configuration

`llm_plan` supports local dry-run planning and OpenAI-compatible providers.

For DeepSeek-compatible usage:

```powershell
$env:MATHMODEL_LLM_PROVIDER = "deepseek"
$env:MATHMODEL_LLM_BASE_URL = "https://api.deepseek.com"
$env:MATHMODEL_LLM_API_KEY = "<your-key>"
$env:MATHMODEL_LLM_MODEL = "deepseek-chat"
```

For another OpenAI-compatible endpoint:

```powershell
$env:MATHMODEL_LLM_PROVIDER = "openai-compatible"
$env:MATHMODEL_LLM_BASE_URL = "https://your-compatible-endpoint/v1"
$env:MATHMODEL_LLM_API_KEY = "<your-key>"
$env:MATHMODEL_LLM_MODEL = "<model-name>"
```

Optional tuning:

```powershell
$env:MATHMODEL_LLM_TEMPERATURE = "0.2"
$env:MATHMODEL_LLM_MAX_TOKENS = "4096"
```

API keys are required for remote providers and must not be committed.

## API

### Status

```http
GET /api/langgraph/status
```

Returns whether the optional dependency is available:

```json
{
  "available": false,
  "version": null,
  "import_error": "No module named 'langgraph'",
  "note": "Install optional dependencies with: pip install -r app/backend/requirements-langgraph.txt"
}
```

### Dry-Run Phase

```http
POST /api/workspaces/{workspace_id}/langgraph/run
```

Body:

```json
{
  "phase": 1,
  "mode": "dry_run",
  "provider": "none",
  "model": null,
  "copy_workspace": true,
  "run_name": "phase-1-dry-run"
}
```

Outputs in the run workspace:

- `CONTROL_LANGGRAPH_PHASE_<phase>.md`
- `reports/LANGGRAPH_RUN_REPORT.md`

History event appended to the source workspace:

- `langgraph_phase_dry_run`

If LangGraph is not installed, the run endpoint returns `501` with the optional-install command.

### LLM Plan Phase

```http
POST /api/workspaces/{workspace_id}/langgraph/run
```

Body:

```json
{
  "phase": 1,
  "mode": "llm_plan",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "copy_workspace": true,
  "run_name": "phase-1-llm-plan",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

For a no-network test plan, use:

```json
{
  "phase": 1,
  "mode": "llm_plan",
  "provider": "none",
  "copy_workspace": true
}
```

Outputs in the run workspace:

- `CONTROL_LANGGRAPH_PHASE_<phase>.md`
- `reports/LANGGRAPH_PHASE_PLAN.json`
- `reports/LANGGRAPH_PHASE_PLAN.md`
- `reports/LANGGRAPH_RUN_REPORT.md`
- `reports/LANGGRAPH_RAW_MODEL_OUTPUT.md` only when provider output cannot be parsed as a valid plan

History event appended to the source workspace:

- `langgraph_phase_llm_plan`

If a remote provider is selected without `MATHMODEL_LLM_API_KEY`, the run endpoint returns a controlled `400` error.

### Controlled Apply

```http
POST /api/workspaces/{workspace_id}/langgraph/run
```

Body:

```json
{
  "phase": 1,
  "mode": "controlled_apply",
  "provider": "none",
  "copy_workspace": true,
  "run_name": "phase-1-controlled-apply"
}
```

`controlled_apply` first looks for `reports/LANGGRAPH_PHASE_PLAN.json` in the copied run workspace. If the plan contains valid `file_writes`, the runner validates every target before writing anything. If no `file_writes` exist, it produces a plan-only result and writes no phase reports.

Supported phases:

- Phase 1 `mm-model-strategy`
- Phase 4 `mm-contest-review`

Phase 1 allowlist:

- `reports/MODEL_CANDIDATES.md`
- `reports/MODEL_REVIEW_AI.md`
- `reports/FIGURE_PLAN.md`
- `reports/REFINEMENT_LOG.md`

Phase 4 allowlist:

- `reports/PAPER_SCORECARD.md`
- `reports/REVISION_ACTIONS.md`
- `reports/REFINEMENT_LOG.md`

Additional LangGraph infrastructure outputs:

- `CONTROL_LANGGRAPH_PHASE_<phase>.md`
- `reports/LANGGRAPH_RUN_REPORT.md`
- `reports/LANGGRAPH_PHASE_PLAN.json`
- `reports/LANGGRAPH_PHASE_PLAN.md`
- `reports/LANGGRAPH_RAW_MODEL_OUTPUT.md`
- `reports/AGENT_RUNS.md`

Permanent denylist:

- `paper/`
- `code/`
- `figures/`
- `results/`
- `source/`
- `reports/HUMAN_MODEL_REVIEW.md`
- `reports/MODELING_DECISION.md`
- `reports/VERIFY_REPORT.md`
- any absolute path, `..`, symlink escape, or workspace-external path

History event appended to the source workspace:

- `langgraph_phase_controlled_apply`

Possible statuses:

- `APPLY_PLAN_ONLY`: validated plan has no `file_writes`; no phase reports written.
- `APPLY_REJECTED`: at least one write failed allowlist/path/content validation; no phase reports written.
- `APPLY_ROLLED_BACK`: write failure occurred and partial writes were restored/deleted.
- `APPLY_NEEDS_REVIEW`: reports were written, but post-audit still has `HIGH/BLOCKER`.
- `APPLY_READY_FOR_HUMAN_REVIEW`: reports were written and no post-audit `HIGH/BLOCKER` was detected.

Even `APPLY_READY_FOR_HUMAN_REVIEW` is not final PASS. Human gates and `audit_v2_run.py` remain authoritative.

### Single Phase Execute

`phase_execute` is the first usable single-phase executor. It reuses `llm_plan` and `controlled_apply` in one graph pass:

```text
phase prompt -> provider PhasePlan JSON -> file_writes validation -> controlled apply -> post audit -> next human action
```

Supported phases:

- Phase 1 `mm-model-strategy`
- Phase 4 `mm-contest-review`

Unsupported phases return:

```text
PHASE_NOT_SUPPORTED
```

No-network smoke request:

```json
{
  "phase": 1,
  "mode": "phase_execute",
  "provider": "none",
  "copy_workspace": true,
  "run_name": "phase-1-execute-smoke"
}
```

DeepSeek/OpenAI-compatible request:

```json
{
  "phase": 1,
  "mode": "phase_execute",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "copy_workspace": true,
  "run_name": "phase-1-execute-deepseek",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

Provider output must be strict JSON parseable as `PhasePlan` and should include `file_writes` for report drafts. If JSON parsing fails, the runner writes `reports/LANGGRAPH_RAW_MODEL_OUTPUT.md` and no core reports. If any `file_writes` path is illegal, the entire batch is rejected and no core report is written. If writing fails mid-run, already written files are rolled back.

Additional output:

- `reports/LANGGRAPH_APPLY_DIFF.md`

This file summarizes phase, mode, provider, model, files planned, files written, files rejected, rollback status, pre/post audit summary, final status, and next human action.

Phase 1 always stops for human review of `reports/MODEL_CANDIDATES.md`; a person must fill `reports/HUMAN_MODEL_REVIEW.md` and `reports/MODELING_DECISION.md` before data-experiment. Phase 4 always stops for human review of `reports/PAPER_SCORECARD.md` and `reports/REVISION_ACTIONS.md`. The executor never claims final PASS.

### Full Contest Graph v0

`contest_graph_v0` is a safe whole-contest orchestrator. It reuses the existing phase-level runner instead of replacing V2 skills:

```json
{
  "phase": 0,
  "mode": "contest_graph_v0",
  "provider": "none",
  "copy_workspace": true,
  "run_name": "contest-graph-v0-smoke"
}
```

Hybrid phase strategy:

- Phase 0 `mm-problem-intake`: `llm_plan` only.
- Phase 1 `mm-model-strategy`: `phase_execute`, with the existing Phase 1 allowlist only.
- Phase 1 human gate: read-only check of `reports/HUMAN_MODEL_REVIEW.md`.
- Phase 2 `mm-data-experiment`: `llm_plan` only; no Bash, no code/results/figures writes.
- Phase 3 `mm-paper-build`: `llm_plan` only; no paper writes.
- Phase 4 `mm-contest-review`: `phase_execute`, with the existing Phase 4 allowlist only.
- Phase 5 `mm-revision-integrator`: `llm_plan` only; no automatic paper/result edits.
- Phase 6 `mm-final-verify`: audit-only; does not write `reports/VERIFY_REPORT.md` and does not claim final PASS.

Human gate rule:

- If `reports/HUMAN_MODEL_REVIEW.md` is missing or lacks an approval signal such as `approved`, `adopt`, `通过`, `确认`, `同意`, or `采用`, the graph stops with `WAITING_FOR_HUMAN_MODEL_REVIEW`.
- The graph never writes `reports/HUMAN_MODEL_REVIEW.md` or `reports/MODELING_DECISION.md`.
- The graph never proceeds to Phase 2 until that gate is manually approved in the copied run workspace.

Outputs:

- Phase-level outputs from the reused single-phase runner.
- `reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md`

The contest graph response includes:

- `contest_status`
- `completed_phases`
- `paused_at`
- `human_gate_required`
- `human_gate_file`
- `graph_report_path`
- `phase_results`
- `final_audit`

`contest_graph_v0` is deliberately not a full autopilot. It does not execute data experiments, write paper drafts, edit code, generate figures/results, or finalize verification. Those require explicit future approval and narrower safety gates.

### Full Contest Graph v1

`contest_graph_v1` keeps the v0 human-gated graph but upgrades Phase 2 from plan-only to a sandbox executor for copied run workspaces.

```json
{
  "phase": 0,
  "mode": "contest_graph_v1",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "copy_workspace": true,
  "run_name": "contest-graph-v1-phase2-sandbox",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

No-network smoke runs may use `provider: "none"`, but Phase 2 will execute only if the validated PhasePlan contains `commands`.

v1 strategy:

- Phase 0: `llm_plan`.
- Phase 1: `phase_execute`, with the existing Phase 1 allowlist only.
- Human Gate: `reports/HUMAN_MODEL_REVIEW.md` must exist and contain an approval signal.
- Phase 2: sandbox executor.
- Phase 3: `llm_plan`; no `paper/` writes.
- Phase 4: `phase_execute`, with the existing Phase 4 allowlist only.
- Phase 5: `llm_plan`.
- Phase 6: audit-only; no final PASS writing.

Phase 2 command protocol extends `PhasePlan` with `commands`:

```json
{
  "commands": [
    {
      "id": "C1",
      "purpose": "syntax check",
      "command": "python -m py_compile code/solve.py",
      "expected_outputs": []
    },
    {
      "id": "C2",
      "purpose": "run experiment",
      "command": "python code/solve.py",
      "expected_outputs": [
        "results/RESULTS_MANIFEST.json",
        "reports/RESULTS_REPORT.md"
      ]
    }
  ]
}
```

Allowed Phase 2 commands:

- `python <script>.py`, where the script is under `code/` or `tests/`.
- `python -m py_compile <script>.py`, where the script is under `code/` or `tests/`.
- `pytest <tests path>`, scoped to workspace `tests/` only.

Forbidden command patterns include:

- `rm`, `del`, `rmdir`
- `curl`, `wget`
- `powershell -enc`
- `pip install`, `conda install`
- shell metacharacters such as pipes, redirects, `&&`, `||`, and `;`
- commands that target paths outside the run workspace

Allowed Phase 2 writes:

- `code/`
- `code/outputs/`
- `figures/`
- `results/RESULTS_MANIFEST.json`
- `reports/EXPERIMENT_LOG.md`
- `reports/TEMPLATE_ADAPTATION_LOG.md`
- `reports/RESULTS_REPORT.md`
- `reports/FIGURE_PLAN.md`
- `reports/FIGURE_AUDIT.md`
- LangGraph plan/report infrastructure files

Forbidden Phase 2 writes:

- `paper/`
- `source/`
- `reports/HUMAN_MODEL_REVIEW.md`
- `reports/MODELING_DECISION.md`
- `reports/VERIFY_REPORT.md`
- workspace-external paths

If Phase 2 has no `commands`, status is `PHASE2_PLAN_ONLY` and no experiment command runs. If any command is invalid, the whole batch is rejected with `SANDBOX_COMMAND_REJECTED`. If a command writes outside the Phase 2 allowlist, the runner restores the pre-execution workspace snapshot and returns `SANDBOX_WRITE_VIOLATION`.

After command execution, the runner checks `results/RESULTS_MANIFEST.json`. If missing, it writes a minimal empty skeleton:

```json
{
  "metrics": [],
  "tables": [],
  "figures": [],
  "scripts": []
}
```

The response and experiment log mark this as `manifest_created_empty: true`; the runner does not fabricate metrics, tables, figures, or conclusions.

Phase 2 outputs:

- `reports/EXPERIMENT_LOG.md`
- `reports/AGENT_RUNS.md`
- `results/RESULTS_MANIFEST.json`
- optional report/figure/code outputs generated by the allowed command

If Phase 2 command execution fails, or if post-Phase-2 audit reports `HIGH`/`BLOCKER`, the v1 graph stops before Phase 3.

### Full Contest Graph v2

`contest_graph_v2` keeps the v1 Human Gate and Phase 2 sandbox, then upgrades Phase 3 from plan-only to a Paper Draft Sandbox.

```json
{
  "phase": 0,
  "mode": "contest_graph_v2",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "copy_workspace": true,
  "run_name": "contest-graph-v2-paper-draft",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

v2 strategy:

- Phase 0: `llm_plan`.
- Phase 1: `phase_execute`.
- Human Gate: `reports/HUMAN_MODEL_REVIEW.md` must be approved before Phase 2.
- Phase 2: sandbox executor; failure or `HIGH/BLOCKER` audit stops the graph.
- Phase 3: Paper Draft Sandbox.
- Phase 4: `phase_execute` contest review; this step is mandatory after paper drafting.
- Phase 5: `llm_plan`; no automatic paper revision.
- Phase 6: audit-only; does not write `reports/VERIFY_REPORT.md` and does not claim final PASS.

Phase 3 uses `PhasePlan.file_writes`. Provider output should include:

- a draft paper file: `paper/main.tex`, `paper/main.typ`, or `paper/README.md`;
- `reports/CLAIM_TRACE.md`;
- `reports/METHOD_IMPLEMENTATION_MATRIX.md`;
- `reports/PAPER_BUILD_REPORT.md`;
- `next_action` in the PhasePlan.

Allowed Phase 3 writes:

- `paper/main.tex`
- `paper/main.typ`
- `paper/README.md`
- `reports/CLAIM_TRACE.md`
- `reports/METHOD_IMPLEMENTATION_MATRIX.md`
- `reports/PAPER_BUILD_REPORT.md`
- `reports/FIGURE_AUDIT.md`
- LangGraph plan/report/agent log files

Forbidden Phase 3 writes:

- `source/`
- `code/`
- `results/`
- `reports/HUMAN_MODEL_REVIEW.md`
- `reports/MODELING_DECISION.md`
- `reports/VERIFY_REPORT.md`
- workspace-external paths

If any Phase 3 `file_writes` path is illegal, the entire batch is rejected with `PAPER_SANDBOX_REJECTED`. If writing fails mid-batch, already written files are rolled back and status is `PAPER_SANDBOX_ROLLED_BACK`.

Paper draft requirements:

- include abstract or abstract placeholder, problem restatement, symbols, assumptions, model construction, solving and experimental results, sensitivity/error analysis, strengths/weaknesses, and references placeholder;
- clearly mark existing results, missing results, human-confirmation-needed content, and AI-generated draft content;
- do not fabricate data, metrics, figure numbers, citations, or final conclusions.

Evidence trace files:

- `reports/CLAIM_TRACE.md` must include `claim_id`, `paper_section`, `claim_text`, `evidence_source`, `source_quality`, `supporting_artifact`, `risk_note`, and `status`.
- `reports/METHOD_IMPLEMENTATION_MATRIX.md` must include `method`, `implementation_file`, `input_data`, `output_artifacts`, `validation_status`, `related_claims`, and `known_gaps`.
- `reports/PAPER_BUILD_REPORT.md` must include generated paper files, used result artifacts, missing artifacts, claims generated, unresolved risks, and next human actions.

If `results/RESULTS_MANIFEST.json` is missing, empty, or invalid, Phase 3 can write only a risk skeleton and draft placeholder. It must label the situation as `manifest missing or empty` and must not invent results.

If Phase 4 review or its post-audit has `HIGH/BLOCKER`, the contest graph status becomes `REVISION_REQUIRED`. Phase 6 remains audit-only.

## Graph

The graph is:

```text
pre_audit_node
  -> build_prompt_node
  -> provider_plan_node
  -> validate_plan_node
  -> write_plan_node
  -> apply_router_node
  -> controlled_write_node
  -> post_audit_node
  -> write_report_node
  -> append_history_node
```

`dry_run` skips provider execution. `llm_plan` calls the selected adapter, validates strict JSON against `PhasePlan`, and writes plan files only. `controlled_apply` additionally validates optional `file_writes` against the phase allowlist before writing any phase report. `phase_execute` always requests a provider plan and then runs the same controlled apply path.

`contest_graph_v0` sits above this graph and invokes the safe phase strategies in sequence inside one copied run workspace. `contest_graph_v1` uses the same contest-level structure, but replaces Phase 2 plan-only behavior with the Phase 2 sandbox executor. `contest_graph_v2` additionally replaces Phase 3 plan-only behavior with the Paper Draft Sandbox. All contest graph modes record a contest-level report and append a contest-level history event.

## Safety Rules

- Run workspace must be the source workspace or a copy under `source_workspace/runs/`.
- Default behavior copies the workspace before writing anything.
- The runner writes only LangGraph prompt/report/plan files.
- `llm_plan` never edits `paper/`, `code/`, `figures/`, `results/`, or V2 core reports.
- `llm_plan` does not bypass `HUMAN_MODEL_REVIEW.md`.
- `controlled_apply` writes only allowlisted Phase 1 or Phase 4 reports in the copied run workspace.
- `controlled_apply` never writes `HUMAN_MODEL_REVIEW.md`, `MODELING_DECISION.md`, or `VERIFY_REPORT.md`.
- `phase_execute` follows the same allowlists and denylist as `controlled_apply`.
- `contest_graph_v0` follows the same allowlists and denylist as `phase_execute` for Phase 1/4, and uses plan-only or audit-only behavior everywhere else.
- `contest_graph_v1` keeps the same Phase 1/4 allowlists and uses the Phase 2 sandbox allowlist for experiment execution.
- `contest_graph_v2` keeps v1 boundaries and uses the Phase 3 paper sandbox allowlist for paper draft/evidence writes.
- Phase 1 controlled apply stops before human confirmation; a person must review `MODEL_CANDIDATES.md` before data-experiment.
- Phase 2 sandbox execution never bypasses `HUMAN_MODEL_REVIEW.md` and never writes `paper/`, `source/`, `HUMAN_MODEL_REVIEW.md`, `MODELING_DECISION.md`, or `VERIFY_REPORT.md`.
- Phase 3 paper sandbox never writes `code/`, `results/`, `source/`, `HUMAN_MODEL_REVIEW.md`, `MODELING_DECISION.md`, or `VERIFY_REPORT.md`.
- Phase 3 paper sandbox does not compile the paper and does not claim final PASS.
- Completion truth remains `audit_v2_run.py`, V2 gate artifacts, and human confirmation.

## Planned Modes

- More granular human gate records for each transition.
- Multi-model backend comparison (DeepSeek, OpenAI, Claude, Qwen) for each phase.

---

## Contest Graph v3 (Implemented)

`contest_graph_v3` completes the safe closed-loop: the Phase 5 Revision Integrator Sandbox upgrades `llm_plan`-only to controlled revision writes.

```json
{
  "phase": 0,
  "mode": "contest_graph_v3",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "copy_workspace": true,
  "run_name": "contest-graph-v3-full",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

v3 strategy:

- Phase 0: `llm_plan`.
- Phase 1: `phase_execute`.
- Human Gate: `reports/HUMAN_MODEL_REVIEW.md` must be approved before Phase 2.
- Phase 2: sandbox executor; failure or `HIGH/BLOCKER` audit stops the graph.
- Phase 3: Paper Draft Sandbox.
- Phase 4: `phase_execute` contest review; `HIGH/BLOCKER` triggers `REVISION_REQUIRED`.
- **Phase 5: Revision Integrator Sandbox** — reads `REVISION_ACTIONS.md`, performs controlled writes to `paper/` and allowed `reports/`, writes `REVISION_STATUS.md`.
- Phase 6: audit-only; does not write `reports/VERIFY_REPORT.md` and does not claim final PASS.

### Phase 5 Revision Sandbox

Allowed Phase 5 writes:

- `paper/main.tex`, `paper/main.typ`, `paper/README.md`
- `reports/CLAIM_TRACE.md`, `reports/METHOD_IMPLEMENTATION_MATRIX.md`, `reports/PAPER_BUILD_REPORT.md`
- `reports/REVISION_STATUS.md`, `reports/REFINEMENT_LOG.md`
- LangGraph plan/report/agent log files

Forbidden Phase 5 writes:

- `source/`, `code/`, `figures/`, `results/`
- `reports/HUMAN_MODEL_REVIEW.md`, `reports/MODELING_DECISION.md`, `reports/VERIFY_REPORT.md`
- workspace-external paths

Phase 5 rules:

- If `REVISION_ACTIONS.md` is missing, writes only `REVISION_STATUS.md` with `NO_REVISION_ACTIONS`.
- If `REVISION_ACTIONS.md` has BLOCKER/HIGH, can attempt controlled revision of allowed files.
- Must not fabricate experimental results, metrics, or citations.
- Must not upgrade weak claims to strong claims without new evidence.
- Must not delete BLOCKER/HIGH items to pretend resolution.
- Writes `REVISION_STATUS.md` after revision.
- If unresolved BLOCKER/HIGH remain, `contest_status = REVISION_REQUIRED`.
- If no BLOCKER/HIGH, `contest_status = READY_FOR_FINAL_AUDIT`.
- Phase 6 remains audit-only; VERIFY_REPORT.md is never auto-written.

### v3 Completion Rules

- All phases 0–6 must complete without fatal errors.
- Phase 6 audit is recorded but does not claim final PASS.
- Human review is required at every gate.
- `VERIFY_REPORT.md` is never written automatically.
- `HUMAN_MODEL_REVIEW.md` and `MODELING_DECISION.md` remain manual-only.

---

## Benchmark Arena

`scripts/langgraph_benchmark.py` provides batch benchmark runs for contest graph modes. It scans a directory of fixture workspaces, runs each through `contest_graph_v3` (or another mode) with `provider=none`, and produces JSON + Markdown reports.

```powershell
python scripts/langgraph_benchmark.py --root tests/langgraph_benchmark_fixtures
python scripts/langgraph_benchmark.py --root <dir> --mode contest_graph_v3 --provider none
python scripts/langgraph_benchmark.py --root <dir> --json-out bench.json --markdown-out bench.md
```

Outputs per workspace:

- `contest_status`, `completed_phases`, `paused_at`
- Human gate required/approved state
- Per-phase status (sandbox, paper sandbox, revision sandbox)
- Per-phase files written, audit worst severity
- Final audit summary

Reports:

- `reports/LANGGRAPH_BENCHMARK_REPORT.md` — Markdown table per workspace
- `reports/LANGGRAPH_BENCHMARK_REPORT.json` — structured machine-readable format

### Benchmark Fixtures

At minimum:

1. **human_gate_pause** — workspace without `HUMAN_MODEL_REVIEW.md`; contest_graph_v3 must stop at Human Gate.
2. **full_minimal_flow** — workspace with approved gate, `code/solve.py`, all phase adapters; all 0–6 phases complete, no VERIFY_REPORT auto-written.
3. **revision_required** — Phase 4 produces HIGH/BLOCKER; Phase 5 writes `REVISION_STATUS.md` with unresolved flag; contest_status does not claim PASS.

All benchmarks use `provider=none` and do not depend on external APIs.

### Release Stabilization Invariants

Test suite in `tests/test_langgraph_benchmark.py` verifies:

- contest_graph_v3 never writes `VERIFY_REPORT.md`, `MODELING_DECISION.md`, or `HUMAN_MODEL_REVIEW.md`.
- Phase 2 sandbox rejects writes to `paper/`, `source/`, and external paths.
- Phase 3 sandbox rejects writes to `code/`, `results/`, `source/`.
- Phase 5 sandbox rejects writes to `code/`, `results/`, `source/`, `VERIFY_REPORT.md`.
- Phase 6 is audit-only; does not write core reports or claim final PASS.
- `LANGGRAPH_CONTEST_GRAPH_REPORT.md` exists with all required sections.
- `AGENT_RUNS.md` has entries for phases 2, 3, 5.
- History includes a `langgraph_contest_graph_v3` event.
- Benchmark report generation produces valid JSON and Markdown.

### Next Steps

The Benchmark Arena is a foundation. Future work:

- Multi-model comparison (DeepSeek vs OpenAI vs Claude vs Qwen) on the same fixtures.
- Historical contest workspace replay.
- Scorecard-based ranking across model backends.

Do not add `contest_graph_v4` until the Benchmark Arena proves the v3 closed-loop is stable across backends.
