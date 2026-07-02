# Figure Evidence Map

A figure is accepted as a core paper figure only when it supports a claim with traceable data and metrics.

## Required Evidence Map Fields

Every core entry in `reports/FIGURE_PLAN.md` must contain:

| Field | Requirement |
| --- | --- |
| `claim_id` | Claim that the figure supports. |
| `figure_archetype` | Evidence-map entry, e.g. `predicted_vs_actual`. |
| `supported_claim` | One sentence conclusion the figure can support. |
| `required_data` | Data columns/files needed. |
| `required_metrics` | Metrics that must appear in figure/caption/table. |
| `axes_and_units` | Required axes labels and units. |
| `intended_section` | Paper section where it belongs. |
| `core_figure` | `yes/no`; whether it is needed for the main argument. |
| `failure_signals` | Conditions that make the figure invalid. |
| `caption_points` | What the caption must say. |

## Template: predicted_vs_actual

- `supported_claim`: The prediction model has acceptable out-of-sample accuracy.
- `required_data`: `y_true`, `y_pred`, `time/index`, train/test split marker.
- `required_metrics`: MAE, RMSE, MAPE or task-specific error metric; test-set metric required.
- `axes_and_units`: x-axis is time/index/sample id; y-axis is target variable with unit.
- `intended_section`: prediction result and validation section.
- `core_figure`: yes for prediction tasks.
- `failure_signals`: training-set-only plot; no test set; no error metric; target units missing; leakage-prone split.
- `caption_points`: state test-set scope, main error metric, and whether errors are acceptable for the problem objective.

## Template: constraint_utilization

- `supported_claim`: The optimization solution is feasible and uses resources reasonably.
- `required_data`: constraint name, capacity/limit, actual usage, slack or violation.
- `required_metrics`: utilization rate, violation count, worst slack/violation.
- `axes_and_units`: x-axis constraint/resource; y-axis utilization percentage or quantity with unit.
- `intended_section`: optimization result and feasibility check section.
- `core_figure`: yes for resource allocation, scheduling, and capacity planning.
- `failure_signals`: only reporting objective value; no constraint satisfaction evidence; capacity units mixed; infeasible solution hidden.
- `caption_points`: state feasibility status, tight constraints, and what the utilization pattern means for the decision.

## Template: pareto_frontier

- `supported_claim`: There is a meaningful trade-off among objectives, and the recommended solution is a justified compromise.
- `required_data`: objective vectors for feasible schemes, chosen solution id, baseline solution id.
- `required_metrics`: objective values for each shown scheme; dominance or trade-off explanation.
- `axes_and_units`: each axis is an objective with direction and unit.
- `intended_section`: multi-objective decision or sensitivity section.
- `core_figure`: yes for explicit multi-objective tasks.
- `failure_signals`: only one solution shown; weights not disclosed; dominated solution called optimal; axes omit units or direction.
- `caption_points`: state trade-off shape, chosen point, and why the selected point is defensible.

## Template: ranking_sensitivity

- `supported_claim`: Evaluation/ranking conclusions are stable under reasonable weight or indicator perturbations.
- `required_data`: alternatives, baseline ranking, perturbed weights/indicators, resulting ranks.
- `required_metrics`: rank correlation, rank change count, top-k stability.
- `axes_and_units`: x-axis perturbation scenario; y-axis rank or score; lower rank direction must be clear.
- `intended_section`: evaluation validation or robustness section.
- `core_figure`: yes when rankings drive final recommendations.
- `failure_signals`: no baseline comparison; arbitrary weights; no explanation of perturbation range.
- `caption_points`: state which alternatives remain stable and where ranking uncertainty matters.

## Template: residual_distribution

- `supported_claim`: Model errors are centered and do not show obvious systematic bias.
- `required_data`: residuals, fitted values or time/index, train/test marker.
- `required_metrics`: mean residual, standard deviation, error quantiles; optional normality or autocorrelation check.
- `axes_and_units`: residual axis uses target unit; fitted/time axis is labeled.
- `intended_section`: model diagnostics.
- `core_figure`: optional but recommended for serious prediction or regression routes.
- `failure_signals`: residuals only from training data; no unit; strong pattern ignored.
- `caption_points`: state whether residual pattern supports or weakens the model claim.

## Review Rules

- `mm-data-experiment` must update `FIGURE_PLAN.md` before accepting a core figure.
- `mm-paper-build` may insert a core figure only if it has a claim binding and source-data trace.
- `mm-contest-review` should judge whether the figure supports the paper claim, not only visual polish.
- `mm-final-verify` must fail or create a `HIGH` action when a core figure lacks claim binding, required metrics, source data, or axes/units.
