# Agent Review Protocol

Use this protocol for model, paper, figure, and final reviews.

## Review Output Format

```markdown
# <Review Name>

结论：PASS / CONDITIONAL_PASS / FAIL

## Strengths
## Blocking Issues
## Score Or Severity
## Required Fixes
## Evidence Reviewed
```

## Severity

- `BLOCKER`: must fix before next stage
- `HIGH`: likely hurts correctness or score
- `MEDIUM`: weakens clarity or persuasiveness
- `LOW`: polish

## Review Rules

- Cite concrete files or sections.
- Separate "missing evidence" from "weak writing".
- Prefer fixable actions over vague criticism.
- Do not approve models that code cannot implement.
- Do not approve papers whose figures and claims cannot be traced.

## Model Review Questions

- Does each subproblem have a clear objective?
- Are variables and constraints explicit?
- Is the method appropriate for data scale and type?
- Is there a baseline?
- Is validation planned?
- Are figures/tables planned?
- Could a coder implement it without guessing?

## Paper Review Questions

- Does the paper answer every top-level question?
- Are figures/tables integrated into the argument?
- Are quantitative claims traceable?
- Is the abstract specific?
- Are limitations honest and not fatal?
- Does the structure resemble a polished contest submission?
