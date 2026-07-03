# LangGraph Real Workspace Benchmark: DeepSeekV4Pro_V2.3

- Created UTC: `2026-07-03T04:17:08.890157+00:00`
- Mode: `contest_graph_v3`
- Provider: `none`
- Model: `none`
- Source workspace: `D:\WorkSpace_MathModel\examples\2022C\DeepSeekV4Pro_V2.3`
- Copied run workspace: `D:\WorkSpace_MathModel\examples\2022C\DeepSeekV4Pro_V2.3\runs\20260703-121706-real-benchmark-DeepSeekV4Pro_V2.3`
- Run workspace under source `runs/`: `True`

## Outcome

- Contest status: `PHASE2_PLAN_ONLY`
- Runner status: `PHASE2_PLAN_ONLY`
- Completed phases: `[0, 1, 2]`
- Paused at: `phase_2_sandbox`
- Human gate required: `False`
- Human gate approved: `True`
- Final audit worst severity: `HIGH`
- Source `reports/VERIFY_REPORT.md` unchanged: `True`
- Run `reports/VERIFY_REPORT.md` exists: `True`

## Phase Table

| Phase | Status | Strategy | Sandbox | Paper | Revision | Files | Audit |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 0 | PASS `PLAN_READY` | `llm_plan_only` | `-` | `-` | `-` | 0 | `HIGH` |
| 1 | INFO `APPLY_PLAN_ONLY` | `phase_execute_allowlisted_reports` | `-` | `-` | `-` | 0 | `HIGH` |
| 2 | INFO `PHASE2_PLAN_ONLY` | `phase2_sandbox_executor` | `PHASE2_PLAN_ONLY` | `-` | `-` | 0 | `HIGH` |
| 3 | NOT_EXECUTED | none | - | - | - | 0 | - |
| 4 | NOT_EXECUTED | none | - | - | - | 0 | - |
| 5 | NOT_EXECUTED | none | - | - | - | 0 | - |
| 6 | NOT_EXECUTED | none | - | - | - | 0 | - |

## Safety Notes

- This is a real workspace benchmark against `examples/2022C/DeepSeekV4Pro_V2.3`.
- `provider=none` was used, so no DeepSeek/OpenAI/Claude API call was made.
- The source workspace `reports/VERIFY_REPORT.md` hash was checked before and after the run.
- The run used a copied workspace under the source workspace `runs/` directory.
- If the run stops at `PHASE2_PLAN_ONLY`, that is recorded as the truthful safety-baseline result, not patched over.

## Conclusion

provider=none safety baseline on a real workspace; this records real orchestration/audit behavior and is not evidence of a real LLM fully executing the contest workflow.
