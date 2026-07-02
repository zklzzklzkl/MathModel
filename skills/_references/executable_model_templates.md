# Executable Model Templates

Model cards decide whether a method is appropriate. Executable templates decide whether the agent can actually implement it on the current data.

## General Requirements

Every accepted candidate route in `reports/MODEL_CANDIDATES.md` must either:

- cite one executable template from this file or the local `code_templates` RAG library; or
- explain why no executable template is applicable.

`mm-data-experiment` must convert the chosen executable template into concrete code tasks and result tables. Do not stop at a model name.

## Optimization Template: Linear Programming Standard Form

Use when decisions are continuous and objective/constraints are linear.

### Decision Variables

```text
x_i >= 0: quantity assigned to option/resource/activity i
```

### Standard Form

```text
minimize or maximize: c^T x
subject to:
  A_ub x <= b_ub
  A_eq x = b_eq
  l <= x <= u
```

### Required Implementation Tasks

- Build variable index table: `variable_id`, `meaning`, `unit`, `lower_bound`, `upper_bound`.
- Build coefficient matrices from current data, not hard-coded template data.
- Solve baseline first: greedy or equal allocation.
- Solve LP with a documented solver.
- Export scheme table and constraint check table.

### Required Result Tables

| Table | Columns |
| --- | --- |
| scheme table | variable, value, unit, interpretation |
| constraint check | constraint, lhs, rhs, slack, status |
| baseline comparison | method, objective_value, feasible, main tradeoff |
| sensitivity | parameter, low, base, high, objective_change, feasibility_change |

## Optimization Template: Integer / 0-1 Programming

Use when decisions are counts, selections, assignments, or yes/no choices.

### Variable Definition

```text
x_i in {0, 1}: 1 if option i is selected, 0 otherwise
y_ij in {0, 1}: 1 if item i is assigned to facility j
n_i in Z_+: integer count for activity i
```

### Required Checks

- Explain why integrality matters.
- Report solver status and optimality gap when available.
- If exact solve is too slow, compare heuristic output against a small exact subset.
- Always export selected items/assignments in a human-readable table.

## Optimization Template: Multi-Objective Weighted Sum

Use when objectives can be normalized and weights are defensible.

### Form

```text
maximize: sum_k w_k * normalized_objective_k(x)
subject to: original feasibility constraints
sum_k w_k = 1, w_k >= 0
```

### Required Checks

- State objective direction and normalization method.
- Justify weights from problem statement, sensitivity range, or human preference.
- Run at least three weight scenarios when the result drives a core claim.
- Pair with `figure_evidence_map.md` entry `pareto_frontier` or ranking sensitivity where feasible.

## Optimization Template: Epsilon-Constraint

Use when one objective is primary and other objectives become explicit thresholds.

### Form

```text
optimize: f_1(x)
subject to:
  f_2(x) <= epsilon_2
  f_3(x) >= epsilon_3
  original feasibility constraints
```

### Required Checks

- Sweep meaningful epsilon values.
- Report infeasible thresholds.
- Show trade-off table or Pareto-style plot.

## Optimization Template: Genetic Algorithm

Use only when exact/convex solvers are unsuitable or the search space is too complex.

### Encoding

```text
chromosome = [gene_1, gene_2, ..., gene_n]
gene_i maps to a current-problem decision variable, not a template placeholder
```

### Fitness

```text
fitness(x) = objective_score(x) - penalty_weight * constraint_violation(x)
constraint_violation(x) = sum(max(0, lhs_k(x)-rhs_k)^2)
```

### Required Algorithm Fields

- encoding and decoding rule;
- initialization rule;
- crossover and mutation operators;
- constraint repair or penalty rule;
- population size, generation count, random seed policy;
- convergence criterion;
- baseline and repeated-run comparison.

### Required Outputs

- best solution table;
- constraint violation table;
- convergence curve;
- repeated-run stability table;
- baseline comparison table.

If a linear/integer solver can solve the same problem cleanly, GA needs a written justification or should be downgraded.

## Sensitivity Analysis Code Skeleton

Use this shape, replacing names with current data variables.

```python
def run_base_model(params):
    """Return objective value, feasibility status, and key outputs."""
    raise NotImplementedError


def sensitivity_grid(base_params, perturbations):
    rows = []
    for name, values in perturbations.items():
        for value in values:
            params = dict(base_params)
            params[name] = value
            result = run_base_model(params)
            rows.append({
                "parameter": name,
                "value": value,
                "objective": result["objective"],
                "feasible": result["feasible"],
                "key_change": result.get("key_change", ""),
            })
    return rows
```

## Paper Formula Writing Template

Optimization sections must include:

1. Variable table: symbol, meaning, unit, domain.
2. Objective function: objective direction, formula, meaning.
3. Constraint groups: capacity, balance, demand, logical, policy, or fairness constraints.
4. Algorithm steps or solver setup.
5. Baseline comparison and feasibility check.
6. Sensitivity or robustness result.
7. Limitation: which assumptions or data estimates affect the solution.

## Template Adaptation Rule

When any `code_templates` RAG hit is used, `mm-data-experiment` must write `reports/TEMPLATE_ADAPTATION_LOG.md`:

```markdown
# Template Adaptation Log

| Template Source | Current Data Fields | Template Variables Replaced | Metrics Kept | Metrics Deleted | Why Applicable | Residual Template Names | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
```

`Residual Template Names` must be `none` unless the name truly appears in the current problem data. Missing adaptation log is a final-verify failure.
