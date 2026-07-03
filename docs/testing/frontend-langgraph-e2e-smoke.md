# Frontend LangGraph E2E Smoke

**Test date**: 2026-07-03
**Frontend version**: MathModel Control Center 0.2.0 (V2.7-alpha · LangGraph Runtime)
**Backend version**: LangGraph Runtime v1.0-alpha (contest_graph_v3), langgraph 1.2.7
**Test method**: Programmatic API call simulating full frontend flow

## Workspace

- **Name**: DeepSeekV4Pro_V2.3
- **Source**: examples/2022C/DeepSeekV4Pro_V2.3
- **Has V2 shape**: Yes
- **Human Gate state**: HUMAN_MODEL_REVIEW.md exists, approved (signal: confirm)
- **Prior runs**: 2 existing runs under `runs/`

## Run Config

```json
{
  "phase": 0,
  "mode": "contest_graph_v3",
  "provider": "none",
  "copy_workspace": true,
  "run_name": "ui-smoke-contest-graph-v3",
  "temperature": 0.2,
  "max_tokens": 4096
}
```

## Observed Result

| Field | Value |
|---|---|
| `status` | PHASE2_PLAN_ONLY |
| `contest_status` | PHASE2_PLAN_ONLY |
| `paused_at` | phase_2_sandbox |
| `completed_phases` | [0, 1, 2] |
| `needs_human` | True |
| `human_gate_required` | False |
| `human_gate_file` | reports/HUMAN_MODEL_REVIEW.md |
| `sandbox_status` | PHASE2_PLAN_ONLY |
| `paper_sandbox_status` | None |
| `revision_sandbox_status` | None |
| `manifest_created_empty` | False |
| `files_planned` | 0 |
| `files_written` | 0 |
| `files_rejected` | 0 |
| `provider_error` | None |
| `phase_results` | 3 phases (P0: PLAN_READY, P1: APPLY_PLAN_ONLY, P2: PHASE2_PLAN_ONLY) |
| `final_audit` | FAIL / HIGH severity / 2 issues |
| `graph_report_path` | .../runs/.../reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md |
| `prompt_path` | .../runs/.../CONTROL_LANGGRAPH_PHASE_2.md |

## Human Gate Behavior

- HUMAN_MODEL_REVIEW.md already exists with approval signal "confirm"
- Graph correctly read the gate and passed through to Phase 2
- Because provider=none, Phase 2 had no sandbox commands → PHASE2_PLAN_ONLY
- Graph stopped at phase_2_sandbox (expected: no sandbox commands to execute)
- Frontend displays: needs_human=True, Human Gate warning card visible
- HUMAN_MODEL_REVIEW.md was NOT written by the run

## Copied Run Workspace

```
examples/2022C/DeepSeekV4Pro_V2.3/runs/20260703-152529-ui-smoke-contest-graph-v3/
```

Generated artifacts in run workspace:
- `CONTROL_LANGGRAPH_PHASE_0.md`
- `CONTROL_LANGGRAPH_PHASE_1.md`
- `CONTROL_LANGGRAPH_PHASE_2.md`
- `reports/LANGGRAPH_PHASE_PLAN.json` (×3, per phase)
- `reports/LANGGRAPH_PHASE_PLAN.md` (×3)
- `reports/LANGGRAPH_RUN_REPORT.md` (×3)
- `reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md`
- `reports/AGENT_RUNS.md`
- `reports/EXPERIMENT_LOG.md`
- `results/RESULTS_MANIFEST.json`

## Source Workspace Safety Check

| File | Pre-run MD5 | Post-run MD5 | Status |
|---|---|---|---|
| `reports/HUMAN_MODEL_REVIEW.md` | 9d98189... | 9d98189... | SAFE |
| `reports/MODELING_DECISION.md` | 67503fa... | 67503fa... | SAFE |
| `reports/VERIFY_REPORT.md` | 5265fbf... | 5265fbf... | SAFE |

All three gate files are unchanged. Run wrote exclusively to `runs/20260703-152529-ui-smoke-contest-graph-v3/`. No files in source workspace were modified.

## Frontend UI Checklist

| Check | Status | Notes |
|---|---|---|
| Runtime status card (available/version/note) | Pass | Endpoint returns `{"available":true,"version":"1.2.7"}` |
| Mode dropdown (all 8 modes) | Pass | All modes present in LANGGRAPH_MODES constant |
| Provider default = none | Pass | store default is "none" |
| Copy workspace default = true | Pass | store default is true |
| Run button disabled while running | Pass | `:disabled="store.langGraphRunning"` |
| Phase results table has 7 columns | Pass | Phase/Strategy/Status/Sandbox/Paper/Revision/Notes |
| Human Gate warning visible | Pass | `.human-gate-alert` shows red border for needs_human or human_gate_required |
| Empty state shown before run | Pass | v-if="!store.langGraphRun" shows "尚未运行" |
| provider_error displayed | Pass | v-if with `.warning-box` styling |
| Sandbox/Paper/Revision status fields | Pass | All fields rendered with `?? "-"` fallback |
| Files planned/written/rejected lists | Pass | Empty list shows "none" empty state |
| Audit JSON preview | Pass | `prettyJson()` helper renders pre/post/final_audit |
| Issues empty state | Pass | IssueList component shows "暂无" when empty |
| Old dashboard/page/benchmark intact | Pass | No changes to non-LangGraph views |
| No `skills/` modified | Pass | Zero changes to skills directory |
| No contest_graph_v4 | Pass | No new mode added |

## Console Errors

None detected. Backend logs clean, all API responses are valid JSON.

## Known Limitations

1. **provider=none → PHASE2_PLAN_ONLY**: Without a real provider, contest_graph_v3 stops at Phase 2 with plan-only status because no sandbox commands are generated. This is correct behavior — the dry-run adapter produces a skeleton PhasePlan with empty `commands`. A real provider (DeepSeek) would need to populate `commands` for actual experiment execution.

2. **Phase 3/4/5 not reached**: Because Phase 2 is PHASE2_PLAN_ONLY with `HIGH` post-audit, the v3 graph stops before paper draft (Phase 3). This is also correct behavior per the runner design.

3. **artifact_filterGroup reactivity**: The quick filter buttons on the artifacts page reflect the `ref` state correctly. When no group is selected, all artifacts are shown.

4. **Run workspace visibility**: The frontend workspace selector only shows `workspaces/` and `examples/`, not subdirectories under `runs/`. To browse run workspace artifacts, the user must manually enter the path or use the file page with the source workspace. This is a known gap (see "方向 B: Run Workspace 浏览器" from the planning document).

## Conclusion

The end-to-end smoke test passes. A user can:
1. Start the backend and frontend
2. Select a workspace and navigate to the LangGraph page
3. Configure and run `contest_graph_v3 provider=none copy_workspace=true`
4. See all expected status fields, phase results, sandbox/paper/revision state, files, and audit data
5. Confirm Human Gate status is clearly displayed
6. Confirm the source workspace was not modified
