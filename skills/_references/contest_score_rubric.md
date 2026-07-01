# Contest Score Rubric

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 被 [[skills/mm-contest-review/SKILL|Phase 5 Review]] 和 [[skills/mm-final-verify/SKILL|Phase 7 Verify]] 直接引用

Use this rubric for high-score-oriented math modeling review.

## Score Dimensions

Score each dimension from 0 to 5.

| Dimension | 5-point standard |
| --- | --- |
| Problem understanding | top-level questions, constraints, and evaluation are accurately captured |
| Data understanding | files, fields, units, missing values, and derived variables are clear |
| Modeling fit | method matches data and question type; no template stuffing |
| Mathematical rigor | variables, formulas, objectives, constraints, and assumptions are explicit |
| Implementation | code is reproducible and aligned with the modeling report |
| Result validity | outputs include checks, error analysis, sensitivity, or robustness |
| Visualization | figures and tables support reasoning and are inserted in the paper |
| Writing structure | paper reads like a complete contest paper, not a work log |
| Claim traceability | key claims map to manifest results, figures, or model decisions |
| Submission readiness | final files compile/open and contain no placeholders or internal notes |

## Rating Meaning

- `5`: strong high-score standard
- `4`: acceptable contest standard
- `3`: usable but visibly weak
- `2`: likely significant score loss
- `1`: mostly missing or unreliable
- `0`: absent

For V2 final verification, treat all score dimensions as critical unless the contest task makes a dimension genuinely not applicable and the verifier records the reason. Any applicable dimension below 4 requires revision before final verification and must create an item in `reports/REVISION_ACTIONS.md`.

`PASS` requires no unresolved `BLOCKER` or `HIGH` revision actions. A scorecard with a dimension below 4 may be `CONDITIONAL_PASS` or `FAIL`, but it may not be a clean final `PASS`.

## Hard Fail Conditions

Fail the review if:

- the final paper has no figures
- figures exist but are not inserted in the paper
- code results are missing or cannot be tied to paper claims
- no model validation or sensitivity analysis exists
- the selected model route was never reviewed and approved
- the paper contains obvious internal workflow artifacts
- conclusions rely on invented or untraceable numbers
