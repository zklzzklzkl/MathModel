# Figure Plan

## fig_model_score_comparison

- core_conclusion: The proposed route improves validation score over the baseline while keeping sensitivity loss small.
- figure_archetype: quantitative grid
- backend: Python
- final_size: double-column friendly SVG/PDF
- panel_map:
  - a: validation score by model route
  - b: sensitivity drop under perturbation
- evidence_hierarchy:
  - hero_evidence: validation score comparison
  - validation_evidence: sensitivity drop comparison
  - controls_or_robustness: baseline route
- statistics_needed: mean score and sensitivity drop from `code/outputs/model_scores.csv`
- source_data_needed: `code/outputs/model_scores.csv`
- export_formats: SVG, PDF, PNG preview
- reviewer_risks: small sample and synthetic demonstration data
- intended_section: Results
- supports_claim: proposed route has stronger contest-facing performance than the baseline in this demonstration
