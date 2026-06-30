# ARS V2 Integration Guide

Use this guide when a math modeling V2 skill wants optional Academic Research Suite (ARS) depth without making ARS a hard dependency.

## Availability And Path Resolution

ARS is optional. Resolve `ARS_ROOT` in this order:

1. `<current skills root>/academic-research-suite/ars`
2. `C:\Users\zklzk\.claude\skills\academic-research-suite\ars`

If neither path exists, skip ARS enhancement and continue the normal V2.1 workflow.

Do not copy ARS agent content into V2 skills. Load only the specific ARS agent file needed for the current audit, use it as a role prompt, and summarize the result into the named V2 artifact.

## Agent Map

| V2 stage | ARS agent file | Purpose | Output artifact |
| --- | --- | --- | --- |
| `mm-model-strategy` | `academic-paper-reviewer/agents/methodology_reviewer_agent.md` | Candidate-route methodology audit | `reports/MODEL_REVIEW_AI.md` |
| `mm-data-experiment` | `academic-paper/agents/visualization_agent.md` | Publication-quality figure critique for complex figures | `reports/FIGURE_AUDIT.md`, `reports/REVISION_ACTIONS.md` |
| `mm-paper-build` | `academic-paper/agents/argument_builder_agent.md` | Claim-Evidence-Reasoning chain check | `reports/CLAIM_TRACE.md`, `reports/PAPER_BUILD_REPORT.md` |
| `mm-paper-build` | `academic-paper/agents/abstract_bilingual_agent.md` | Optional bilingual abstract only when allowed | `paper/`, `reports/PAPER_BUILD_REPORT.md` |
| `mm-contest-review` | `academic-paper-reviewer/agents/editorial_synthesizer_agent.md` | Synthesize independent review panels | `reports/PAPER_SCORECARD.md`, `reports/REVISION_ACTIONS.md` |
| `mm-final-verify` | `academic-pipeline/agents/integrity_verification_agent.md` | Reference existence and citation integrity check | `reports/VERIFY_REPORT.md`, `reports/REVISION_ACTIONS.md` |
| `mm-final-verify` | `academic-pipeline/agents/claim_ref_alignment_audit_agent.md` | Adapted claim-to-evidence faithfulness check | `reports/VERIFY_REPORT.md`, `reports/REVISION_ACTIONS.md` |

## V2.1 Boundaries

- ARS is an audit and synthesis layer, not the workflow owner.
- ARS findings must enter existing V2 artifacts; do not create ad hoc long reports.
- Actionable ARS findings must be converted to `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW` rows in `reports/REVISION_ACTIONS.md`.
- ARS may not bypass `mm-revision-integrator`, `METHOD_IMPLEMENTATION_MATRIX.md`, `FIGURE_AUDIT.md`, or `CLAIM_TRACE.md`.
- Do not paste long raw ARS output into reports. Summarize conclusions, evidence, severity, and required fix.

## AGENT_RUNS.md Logging

When ARS is used, append one run entry:

```markdown
## <timestamp> ars:<agent-name>

- goal:
- input artifacts:
- agent file:
- permission scope: read-only audit unless the current V2 stage already owns writes
- output artifacts:
- conclusion:
- thread/id: ars-role-prompt
```

Use a native subagent id instead of `ars-role-prompt` when one exists.

## Bilingual Abstract Rule

Only use `abstract_bilingual_agent.md` when the contest template allows an English abstract, the paper language is English, the contest is MCM/ICM-style, or the user explicitly requests bilingual output. For Chinese national-style templates, do not add an English abstract by default.
