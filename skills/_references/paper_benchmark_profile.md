# High-Score Paper Benchmark Profile

This profile captures the target shape for V2 outputs.

## Observed Gap From Weak Output

A weak generated paper often has:

- mostly text
- no embedded figures
- few or no tables
- short length
- no real model validation
- no sensitivity analysis
- no trace from conclusions to code or data
- generic method descriptions

V2 must explicitly prevent these failures.

## Target Paper Signals

A high-score-style paper should show:

- complete contest structure
- clear problem decomposition
- substantial data preprocessing and diagnostics
- mathematically explicit models
- tables of parameters, metrics, or ranked results
- multiple figures integrated into the argument
- validation, sensitivity, or robustness analysis
- concise but specific model evaluation
- well-numbered formulas, tables, and figures
- final conclusions tied to quantitative evidence

## Minimum Practical Targets

These are not universal contest rules, but they are useful V2 quality floors:

- one or more meaningful figures for EDA or preprocessing
- one or more figures/tables for each major subproblem unless justified
- one sensitivity, robustness, or validation section
- one explicit model evaluation/improvement section
- all important numbers traceable to `RESULTS_MANIFEST.json`
- no final paper that is only plain prose

## Writing Style

Write as a contest paper, not as an AI execution diary.

Avoid:

- "we used an agent"
- "the code generated"
- internal paths
- generic filler such as "the model is good"
- unsupported "as shown in the figure" without interpretation

Prefer:

- concrete variable definitions
- explicit formulas
- concise result interpretation
- figure-by-figure evidence
- honest discussion of limitations
