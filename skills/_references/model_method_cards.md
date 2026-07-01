# Model Method Cards

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 被 [[skills/mm-model-strategy/SKILL|mm-model-strategy]] 引用

Use these cards to guide model selection. They are prompts for judgment, not mandatory templates.

## Prediction

Use when the task asks to forecast, estimate, or classify future/unknown values.

Typical methods:

- regression baseline
- tree models or gradient boosting
- time-series models
- classification models

Must include:

- train/validation split or justified validation scheme
- error metrics
- residual or prediction comparison figure
- leakage check for time-dependent data

## Evaluation And Ranking

Use when the task asks to score, rank, select, or compare.

Typical methods:

- entropy weight
- AHP with consistency check
- TOPSIS
- PCA or factor analysis
- clustering plus scoring

Must include:

- indicator direction
- normalization method
- weight source
- ranking stability or sensitivity

## Optimization

Use when the task asks for best allocation, scheduling, route, policy, or decision.

Typical methods:

- linear/integer programming
- nonlinear programming
- dynamic programming
- heuristic/metaheuristic
- simulation optimization

Must include:

- decision variables
- objective function
- hard constraints
- feasible baseline
- sensitivity on key parameters

## Statistical Inference

Use when the task asks to compare groups, test difference, estimate effects, or explain factors.

Typical methods:

- hypothesis tests
- regression and generalized linear models
- ANOVA or nonparametric tests
- Bayesian or bootstrap intervals

Must include:

- assumptions
- effect size or confidence interval
- diagnostic or robustness check

## Simulation

Use when direct analytical solution is difficult and system dynamics matter.

Typical methods:

- Monte Carlo simulation
- agent/state simulation
- queueing or epidemic-style dynamics
- scenario simulation

Must include:

- scenario definitions
- random seed policy
- repeated runs
- uncertainty visualization

## Do Not Template-Stuff

Do not use AHP, TOPSIS, neural networks, or genetic algorithms just because they look sophisticated. The model must answer the actual question with available data.
