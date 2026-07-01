# Method Implementation Matrix

| Model Route Promise | Implemented? | Code Location | Notes |
|---------------------|-------------|---------------|-------|
| CLR transform throughout | YES | run_all.py:clr_transform() | Applied before all analyses |
| SnO2/SO2 exclusion | YES | run_all.py:COMPONENTS list | Only 12 chemicals used |
| Multiplicative zero replacement | YES | run_all.py:L124-127 | half-min-nonzero per element |
| Na2O/K2O domain-specific imputation | YES | run_all.py:L133-144 | Half-min in defining type |
| Weathering label resolution | YES | run_all.py:resolve_weathering() | Trust Sheet 2 point labels |
| Artifact-level aggregation | YES | run_all.py:aggregate_to_artifact() | Mean for multi-location |
| Q1A: Chi-square + Cramer's V | YES | run_all.py:L237-262 | 3 association tests |
| Q1B: CLR + Welch t + Holm | YES | run_all.py:L313-360 | 24 tests corrected |
| Q1C: Al2O3 immobile-element norm | YES | run_all.py:L414-448 | EF = ref_Al2O3 / weathered_Al2O3 |
| Q2A: RF + t-test + MI consensus | YES | run_all.py:L492-515 | 3-method average rank |
| Q2B: Ward hierarchical clustering | YES | run_all.py:L526-553 | NOT GMM (dropped per review) |
| Q2B: k-means cross-check | YES | run_all.py:L548-550 | ARI comparison |
| Q2C: Decision tree (max_depth=3) | YES | run_all.py:L643-655 | CART on top-5 elements |
| Q2D: Bootstrap stability (500 samples) | YES | run_all.py:L553-565 | Median ARI reported |
| Q3: k-NN (k=3,5) + RF (2 classifiers) | YES | run_all.py:L740-755 | NOT 5-classifier ensemble |
| Q3: Perturbation sensitivity | YES | run_all.py:L833-847 | 5% and 10% tested |
| Q4: Aitchison variation matrix | YES | run_all.py:L864-880 | var(ln(x_i/x_j)) |
| Q4: Permutation test (5000 permutations) | YES | run_all.py:L896-914 | Frobenius norm |

## Downgrade Justifications

| Method in Route B | Downgrade | Reason |
|-------------------|-----------|--------|
| GMM | Ward hierarchical | 18 High-K samples too few for covariance estimation |
| HDBSCAN | Omitted | Density-based clustering unreliable on 18 points |
| Elastic Net (Q1C) | Omitted | Only 4-8 calibration pairs |
| 5-classifier ensemble | 2 classifiers (k-NN + RF) | Method shopping concern |
| Graphical Lasso | Omitted | Sample size insufficient for partial correlation estimation |
| SHAP | Omitted | Adds complexity without core value |
| GNB | Omitted | Violates CLR normality assumption |

## Verdict: ALL PROMISES MET OR HONESTLY DOWNGRADED
