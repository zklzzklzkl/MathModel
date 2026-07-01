# Experiment Log

## Session: 2026-06-29

### preprocessing.py — PASS
- 67/69 samples valid (Σ∈[85%,105%])
- 11 components retained (SnO2/SO2/Na2O excluded)
- All samples normalized to 100%

### q1_analysis.py — PASS
- Q1a: Chi-square test shows significant association between weathering and glass type (χ²=5.45, p=0.02)
- Q1a: Logistic regression: OR(铅钡)=3.88, accuracy=0.648
- Q1b: 4-group statistics computed. High-K: SiO2 loss g=-3.38, K2O enrichment g=+2.67
- Q1b: Pb-Ba: SiO2 enrichment g=+1.26, PbO loss g=-1.08 — weathering effects opposite to high-K glass!
- Q1c: 3 direct pairs (08, 26, 54). SiO2 prediction CIs are wide due to high variability.
- Figures: F1.1, F1.2, F2.1, F2.2, F3.1, F3.2 — all saved

### q2_classification.py — PASS
- Q2a: L1-Logistic Regression 5-fold CV accuracy=0.892±0.062, AUC=1.0
- Q2a: Most discriminative features: PbO/SiO2, K2O/SiO2, BaO/K2O
- Q2b: High-K sub-classes: k_opt=2 (Silhouette=0.686)
- Q2b: Pb-Ba sub-classes: k_opt=2 (Silhouette=0.683)
- ARI between K-means and Hierarchical: 1.0 for both types
- Figures: F4.1, F4.2, F4.3, F5.1, F5.2, F5.3, F5.4, F5.5 — all saved

### q3_prediction.py — PASS
- 4-classifier ensemble + Mahalanobis distance
- Classification results:
  - A1: 高钾 (5/5 agreement), A2: 铅钡 (5/5), A3: 铅钡 (5/5), A4: 铅钡 (5/5)
  - A5: 铅钡 (5/5), A6: 高钾 (5/5), A7: 高钾 (5/5), A8: 铅钡 (5/5)
- Sensitivity: 8/8 stable under ±10% perturbation, 6/8 under LOO training perturbation
- Figures: F6.1, F6.2, F6.3 — all saved

### q4_correlation.py — PASS
- 11 significant differences in correlations (Fisher Z, p<0.05)
- High-K: SiO2 negatively correlated with K2O(r=-0.85), Al2O3(r=-0.85)
- Pb-Ba: SiO2 negatively correlated with PbO(r=-0.78)
- Graphical Lasso: High-K has more edges (15) than Pb-Ba (6) — denser interaction network
- Community structures differ between types
- Figures: F7.1/F7.2, F7.3, F7.4 — all saved

## Issues Encountered
| Issue | Impact | Resolution |
|-------|--------|------------|
| CJK fonts missing in matplotlib | Chinese labels in figures show as boxes | Low priority; figures reference components by chemical symbols in paper |
| Q1c SiO2 CIs very wide | High uncertainty in silica prediction | Document limitation; use PbO prediction (more stable) for type classification |
| Graphical Lasso convergence warnings | Some lambdas failed for high-K | Acceptable; BIC-selected optimal lambda converged |
| FutureWarning: penalty deprecated | sklearn 1.8+ deprecation | Cosmetic; functionality unaffected |
