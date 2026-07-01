# Model Review

结论: **CONDITIONAL_PASS**

## Strengths

1. **Both routes are structurally complete.** Every subproblem (Q1A-Q4) has an objective, defined variables, a named method, an output, and planned figures/tables. This is a solid starting point for implementation.

2. **Route B shows genuine compositional-data awareness.** The CLR transform is placed correctly throughout (before MANOVA, before RF importance, before PCA, before Graphical Lasso). The variation matrix (Aitchison) for Q4 is the correct tool for pairwise log-ratio dispersion, not a naive Spearman-on-raw approach. The inclusion of permutation tests for matrix difference comparison is appropriate.

3. **Multi-method consensus discipline in Route B.** Three-method clustering (GMM + HDBSCAN + hierarchical), five-classifier ensemble for Q3, three-method Q1C prediction — this is the right structure for robustness claims. The use of ARI for method agreement and bootstrap for stability are appropriate quantitative sensitivity metrics.

4. **Validation plans exist for all subproblems.** Both routes specify validation per subproblem (MAE for Q1C, silhouette for clustering, LOOCV/perturbation for Q3, permutation test for Q4). Route B extends this with classifier ablation and bootstrap CIs.

5. **The data risks from the audit are mostly addressed.** Weathering label conflicts are acknowledged (Sheet 2 priority), SnO2/SO2 excluded, zero-handling mentioned (multiplicative replacement), and low-sum rows flagged for sensitivity testing.

## Weaknesses by Subproblem

### Q1A: Weathering Association Analysis

| Issue | Severity | Route A | Route B |
|-------|----------|---------|---------|
| **Multi-sample non-independence ignored** | HIGH | Yes | Yes |
| Logistic regression variable separation risk | HIGH | N/A | Yes |
| Small expected-freq cells in chi-square | MEDIUM | Yes | N/A |
| Missing color treated as "unknown" in Route B | LOW | N/A | Addressed |

**Multi-sample non-independence (HIGH, both routes):** Both routes treat each sampling point (69 in Sheet 2) as an independent observation for Q1A. However, Sheet 1 has 58 artifacts, not 69. Eleven artifacts have multiple sampling points (multi-部位, paired 风化/无风化, normal/severe). The chi-square test in Route A and logistic regression in Route B will inflate effective sample size and produce artificially narrow p-values. Neither route specifies whether Q1A operates on artifact-level (n=58) or point-level (n=69) data, and neither mentions adjusting for the clustering.

**Logistic regression separation risk (HIGH, Route B):** With only 18 High-K artifacts across 8 color levels plus some colors being rare (N=1 or N=2 per cell), the logistic model `logit(P(风化)) ~ 类型 + 纹饰 + 颜色` with 8-level color as a factor runs a real risk of complete or quasi-complete separation (some predictor combinations perfectly predict the outcome). Neither Firth's penalized likelihood nor Bayesian logistic regression with weakly informative priors is mentioned as a fallback.

**Small expected frequencies (MEDIUM, Route A):** The chi-square test for weathering x color has 8 x 2 = 16 cells with only 34 weathered + 24 unweathered = 58 observations. Several color categories have fewer than 5 artifacts. The route mentions "use exact tests or merge sparse categories" but does not specify which colors get merged or what the exact-test alternative is (Fisher-Freeman-Halton).

### Q1B: Compositional Weathering Statistics

| Issue | Severity | Route A | Route B |
|-------|----------|---------|---------|
| **Mann-Whitney U on raw compositions** | HIGH | Yes | No |
| Multiple testing correction missing in Route A | MEDIUM | Yes | N/A |
| MANOVA sample size too thin for Route B | MEDIUM | N/A | Yes |
| Zero-handling incompletely specified | MEDIUM | Both | Both |

**Mann-Whitney U on raw compositional data (HIGH, Route A):** Route A applies Mann-Whitney U to raw wt% data element-by-element. This is problematic because compositional data has a sum constraint: an increase in one element mechanically forces decreases in others. The MW-U test per element ignores this dependency and can yield spurious significance when the real driver is the compositional closure, not weathering. For Q1B specifically, comparing weathered-vs-unweathered differences in Aitchison space (via CLR coordinates or pairwise log-ratios) is the correct approach. Route B does this correctly with CLR-MANOVA and Cohen's d on CLR coordinates.

**Multiple testing correction (MEDIUM, Route A):** 12 elements x 2 glass types = 24 MW-U tests. Neither Bonferroni, Holm, nor FDR correction is mentioned. This guarantees inflated Type I error.

**MANOVA sample size (MEDIUM, Route B):** CLR-transformed data has D-1 = 11 effective dimensions (12 chemicals minus 1 from closure). With High-K having 18 points (split by weathering status), a two-way MANOVA (风化 x 类型) with 11 response variables and interaction term pushes the limits: the weathered High-K group may have as few as 6-8 samples. Pillai's trace is robust to unequal n, but near-zero eigenvalues from small groups can inflate Type II error. The route should specify which MANOVA test statistic and acknowledge the power limitation.

### Q1C: Pre-Weathering Prediction

| Issue | Severity | Route A | Route B |
|-------|----------|---------|---------|
| **Single-element reference physically implausible** | HIGH | Yes | Yes (Method 1) |
| Calibration pair sample size | MEDIUM | Both | Both |
| Elastic Net on 4 pairs → overfitting | HIGH | N/A | Yes |
| Ensemble weighting on 4 held-out pairs | HIGH | N/A | Yes |

**Single immobile-element assumption (HIGH, Route A + Route B Method 1):** Both routes use Al2O3 as the sole immobile reference for normalization. In archaeometric glass weathering, the standard approach uses multiple immobile elements (typically Al2O3, Fe2O3, TiO2 when available) because no single element is perfectly conserved across all burial environments. Al is mobile under alkaline conditions (pH > 8), which occur in some Chinese burial contexts. The model should at minimum:
- State the assumption and its limitations
- Test sensitivity using Fe2O3 as an alternative reference (or an average of Al2O3 + Fe2O3)
- Note that TiO2, the element most commonly considered immobile in geochemistry, is not measured in this dataset (a data limitation that should be disclosed)

**Route A calibration plan (MEDIUM, Route A):** Route A lists 4 paired samples (08, 26, 49, 50) for validation. But IDs 08 and 26 are normal/severe weathering pairs (not weathered/unweathered — these are different degrees on already-weathered artifacts), and 23 and 25 also have both weathered and unweathered measurements. The calibration data should be exhaustively enumerated.

**Elastic Net on 4-6 pairs (HIGH, Route B):** Route B Method 3 applies cross-validated Elastic Net regression to predict pre-weathering composition from weathered measurements. With at most 6-8 paired samples (even after exhaustively enumerating all pairs), fitting an Elastic Net with cross-validation for hyperparameter selection is severely underpowered. The paper will need to explicitly justify how many features (elements) are in the model, what the CV fold size is, and acknowledge the fundamental n << p problem.

**Ensemble weighting (HIGH, Route B):** Route B weights the three prediction methods by validation MAE. If this MAE is computed on the same 4-6 held-out pairs (leave-one-pair-out), the weighting is itself a parameter estimated on 4-6 data points. The ensemble weights will have exceptionally high variance. A simple equal-weight ensemble or a pre-specified weighting scheme (e.g., 60% physical model, 40% regression) is more defensible with this sample size.

### Q2: Glass Classification and Sub-classification

| Issue | Severity | Route A | Route B |
|-------|----------|---------|---------|
| **LDA on raw compositions (Route A Part A)** | CRITICAL | Yes | No |
| Stepwise selection with compositional data | HIGH | Yes | N/A |
| GMM convergence on n=18 | HIGH | N/A | Yes |
| HDBSCAN rejecting all sub-clusters | MEDIUM | N/A | Yes |
| Multi-sample aggregation unclear | MEDIUM | Both | Both |

**LDA on raw compositions (CRITICAL, Route A):** Route A specifies "LDA with stepwise forward selection on CLR-transformed data." This is correct — LDA is applied to CLR coordinates, not raw wt%. However, the MODEL_CANDIDATES.md Route A summary table contradicts this by listing "LDA assumes normality which raw compositions violate" as a risk, implying raw-data application. This must be resolved: the implementation spec must be unambiguously "CLR-transform then LDA."

**Stepwise selection with compositional data (HIGH, Route A):** Forward stepwise selection on CLR coordinates is problematic: CLR coordinates are not independent (they are a D-dimensional representation of a D-1 dimensional simplex). Removing one CLR coordinate changes the geometric meaning of the remaining ones because the geometric mean changes. ILR (isometric log-ratio) coordinates preserve exact subcompositional coherence and are the correct basis for variable selection. Route A should either switch to ILR-based selection or acknowledge this limitation.

**GMM convergence (HIGH, Route B):** With 18 High-K samples, fitting a Gaussian Mixture Model (even with BIC for k selection) is unreliable. The covariance matrix of each component has O(D^2) parameters where D is the number of features; a 1-component model on 11 CLR dimensions already consumes nearly all degrees of freedom. GMM on 18 points should be explicitly scoped to use diagonal covariance (or tied covariance) and limited to k <= 2, with a strong caveat about instability.

**HDBSCAN no-cluster outcome (MEDIUM, Route B):** HDBSCAN can legitimately classify all points as noise if the data is continuous with no density-based separation. Route B should specify what happens if HDBSCAN finds zero sub-clusters (does the ensemble go with the remaining methods, or does this provide evidence against sub-clustering?).

**Multi-sample aggregation (MEDIUM, both routes):** Neither route explicitly states the aggregation strategy for artifacts with multiple sampling points. When clustering at the artifact level, multiple measurements from the same artifact should not enter the cluster analysis as independent data points. Options: (a) use only the "部位1" or unweathered point, (b) average all points from the same artifact, (c) treat each point independently and report the difference. This choice must be documented.

### Q3: Unknown Sample Classification

| Issue | Severity | Route A | Route B |
|-------|----------|---------|---------|
| **Q1C correction before classification not validated** | HIGH | Yes | Yes |
| k-NN with k={3,5} on 18 High-K samples | MEDIUM | Yes | N/A |
| SVM grid-search CV on small training set | MEDIUM | N/A | Yes |
| Sub-class assignment method inconsistency | MEDIUM | N/A | Yes |

**Q1C correction validation (HIGH, both routes):** Both routes apply Q1C weathering correction to A2, A5, A6, A7 before classification. However, Q3 classification accuracy depends critically on Q1C accuracy. If the weathering correction introduces systematic bias, the downstream classification will be wrong. Neither route proposes a validation loop: (a) apply Q1C to known weathered samples, (b) classify them, (c) compare to known labels. This should be added as a sanity check.

**k-NN with k={3,5} on 18 High-K (MEDIUM, Route A):** With only 18 High-K samples, k=5 means ~28% of the training set votes on each query. The effective resolution is low. Route A should justify the choice of k relative to class size or at minimum note the limitation.

**SVM grid-search CV (MEDIUM, Route B):** Grid-search CV for SVM (RBF kernel, optimizing C and gamma) on 18 + 40 = 58 training samples, some of which will be held out in each fold, is underpowered. The synthetic test (perturbation +/- 5%) partially addresses this, but the grid-search itself may overfit. A nested CV design or explicit regularization choice justification is needed.

**Sub-class assignment drift (MEDIUM, Route B):** Route B uses Mahalanobis distance to centroids + GMM posterior for sub-class assignment, but the sub-classes themselves are discovered in Q2 via three-method consensus. If the consensus does not produce a GMM-compatible partition (e.g., HDBSCAN produces non-elliptical clusters), the GMM posterior for assignment is inconsistent with the discovery method. Route B should declare a single sub-class assignment protocol that matches the discovery output format.

### Q4: Chemical Association Analysis

| Issue | Severity | Route A | Route B |
|-------|----------|---------|---------|
| **Spearman on raw compositions** | CRITICAL | Yes | No |
| Mantel test without compositional adjustment | HIGH | Yes | N/A |
| Graphical Lasso regularization choice | MEDIUM | N/A | Yes |
| Partial correlation interpretation in CLR space | MEDIUM | N/A | Yes |

**Spearman on raw compositions (CRITICAL, Route A):** Route A applies Spearman's rho directly to raw wt% data. Spearman is rank-based and does not assume linearity, but it does not escape the closure constraint: if the sum of all 12 elements is ~100%, there exists a negative bias in all pairwise correlations. This is the fundamental reason Aitchison (1986) developed the log-ratio approach. Route A's own risk summary acknowledges "Spearman on raw compositional data still has closure bias" but does not propose a fix. The correct approach is either (a) apply Spearman to pairwise log-ratios (not raw elements), (b) use the variation matrix, or (c) use proportionality coefficients (rho_p from Lovell et al. 2015).

**Mantel test (HIGH, Route A):** The Mantel test compares two distance/dissimilarity matrices. If both matrices are computed from the same raw compositional data (just for different glass types), the internal dependencies from closure propagate into the distance calculations. The Mantel permutation test then permutes already-dependent observations. Route B's alternative (permutation test on Frobenius norm of correlation matrix difference) on CLR data is the correct approach.

**Graphical Lasso regularization (MEDIUM, Route B):** Route B specifies cross-validated lambda for Graphical Lasso. On 18 High-K samples with 11 CLR dimensions, the graph has 55 possible edges. Cross-validation on 18 samples to select a regularization path is unstable. The route should at minimum specify (a) Extended BIC (EBIC) instead of CV for lambda selection, or (b) StARS (Stability Approach to Regularization Selection), which is better suited to small-n graphical model selection.

**Partial correlation interpretation (MEDIUM, Route B):** In CLR space, partial correlations have a specific interpretation: they represent conditional dependencies between the CLR coordinates, which does not directly correspond to conditional independence of the original compositional parts in the simplex. The report should explain that CLR partial correlations indicate linear association between the relative abundances, not between absolute concentrations, and avoid statements like "PbO is correlated with BaO controlling for K2O" which are ambiguous in the simplex.

## Route Comparison Verdict

### Verdict: Adopt Route B as primary, with specific Route A fallbacks

**Subproblem-by-subproblem recommendations:**

| Subproblem | Recommended Route | Rationale |
|------------|-------------------|-----------|
| Q1A | **Route A** (chi-square + exact tests) | Route B's logistic regression is overparameterized given the data structure. Chi-square with Fisher-Freeman-Halton exact test for sparse cells is more defensible. Add Cramer's V for effect size. |
| Q1B | **Route B** (CLR-MANOVA + bootstrapped d) | Route A's Mann-Whitney U on raw compositions is fatally flawed. Route B's CLR-aware approach is correct. Drop the two-way MANOVA; use one-way per glass type + multiple testing correction. |
| Q1C | **Route A** (immobile-element) as primary; **Route B Method 2** (per-element regression) as sensitivity | Route B's Elastic Net is overfitting on 4-6 pairs. Immobile-element normalization is simpler and more physically grounded. Add Fe2O3-based normalization as a sensitivity check. Per-element linear regression on paired data is a low-risk second method. Drop the ensemble weighting. |
| Q2 (Discriminant) | **Route B** (RF importance + mutual info) on ILR coordinates | Route A's stepwise LDA is fragile. Random Forest importance on ILR-transformed data (not CLR) preserves subcompositional coherence in feature selection. Mutual information adds robustness to non-monotonic relationships. |
| Q2 (Clustering) | **Route B reduced**: hierarchical + HDBSCAN only | GMM on n=18 is unreliable. Use Ward's hierarchical (from Route A) + HDBSCAN (from Route B) dual consensus. Drop GMM. Report ARI between the two methods. If HDBSCAN returns all noise, report this as evidence of continuous data rather than sub-clusters. |
| Q3 (Classification) | **Route B reduced**: RF + LDA + SVM | The five-classifier ensemble in Route B is fine, but drop Gaussian NB (assumes CLR coordinates are independent, which they are not by construction) and reduce k-NN to k=3 only (k=5,7 are too large relative to class size). Add the Q1C validation loop. |
| Q4 (Association) | **Route B** (variation matrix + Graphical Lasso + permutation test) | Route A's Spearman-on-raw is the single most critical flaw in the entire document. Route B's Aitchison-geometric approach is correct. Use EBIC instead of CV for Graphical Lasso. |

### Elements to definitely keep from Route B:
- CLR/ILR transforms throughout the pipeline (the core architectural decision)
- Multi-method consensus with quantitative agreement metrics (ARI)
- Bootstrap/p perturbation sensitivity analysis
- Variation matrix for compositional association
- Permutation tests for group comparisons

### Elements from Route A worth keeping:
- Simpler Q1A (chi-square with exact tests, not logistic regression)
- Ward's hierarchical clustering (well-established, complements HDBSCAN)
- Immobile-element normalization simplicity for Q1C

## Required Fixes

### CRITICAL (BLOCK — must fix before implementation)

1. **[C1] Route A Q4: Replace Spearman-on-raw with Aitchison variation matrix.** The current plan is fundamentally incompatible with compositional data analysis. Adopt Route B's Q4 approach.

2. **[C2] Q1A multi-sample non-independence.** Specify whether Q1A operates on artifact-level (n=58) or point-level (n=69) data. If point-level, use clustered standard errors or mixed-effects logistic regression. If artifact-level, define the aggregation rule for artifacts with multiple points.

3. **[C3] Q1C calibration data enumeration.** Exhaustively list all artifact IDs with both weathered and unweathered measurements. Distinguish weathered/unweathered from normal/severe weathering pairs (08, 26). The current "paired data (08, 26, 49, 50)" is ambiguous — 08 and 26 are normal/severe, not weathered/unweathered.

4. **[C4] Route A Q2: Clarify LDA pipeline on CLR vs. raw data.** The specification says CLR then LDA, but the risk summary implies raw data. Resolve to "CLR-transform, then LDA" unambiguously. Replace stepwise selection with ILR-based variable selection or RF importance.

### HIGH (WARN — should fix before implementation)

5. **[H1] Q1B multiple testing correction.** Route A: apply Holm-Bonferroni or Benjamini-Hochberg FDR to the 12 x 2 = 24 tests. Route B: specify MANOVA test statistic (Pillai's trace) and acknowledge the small sample limitation.

6. **[H2] Route B Q1C: Drop Elastic Net and ensemble weighting.** Replace with: Method 1 (Al2O3 immobile-element) + Method 2 (Fe2O3 immobile-element as sensitivity) + Method 3 (per-element OLS on paired data). Report all three separately; do not ensemble-weight.

7. **[H3] Route B Q2: Drop GMM from clustering.** Replace three-method consensus with two-method (Ward's hierarchical + HDBSCAN). Add a protocol for the HDBSCAN-noise outcome.

8. **[H4] Q2 multi-sample aggregation.** Define whether clustering operates at artifact level or point level. If artifact level, specify aggregation (mean of all points, or select primary point).

9. **[H5] Route B Q3: Add Q1C-to-Q3 validation loop.** Apply Q1C correction to known weathered samples, classify them, and compare to known labels before classifying A1-A8.

10. **[H6] Route B Q4: Use EBIC or StARS for Graphical Lasso regularization.** Cross-validation on 18 samples is unstable for graph selection.

### MEDIUM (INFO — consider fixing)

11. **[M1] Q1A Route B: Add Firth's penalized likelihood fallback.** If logistic regression with 8-level color shows separation, automatically fall back to Firth's method.

12. **[M2] Route B Q2: Use ILR, not CLR, for feature selection.** ILR coordinates (specifically, pivot coordinates) preserve subcompositional coherence. CLR coordinates change meaning when one coordinate is removed.

13. **[M3] Route B Q3: Remove Gaussian NB from ensemble.** CLR coordinates are not independent by construction (sum to zero), violating the NB independence assumption.

14. **[M4] Route B Q3: Reduce k-NN to k=3 only.** k=5 and k=7 exceed ~28% and ~39% of the High-K training set respectively.

15. **[M5] Route A Q1B: Document the half-minimum-DL imputation per-element.** The current spec says "half minimum non-zero per element" which is correct but needs the actual threshold values documented (what is the minimum non-zero Na2O? K2O? etc.).

16. **[M6] Q4: Add interpretation caveat for CLR partial correlations.** State explicitly that partial correlations in CLR space indicate conditional dependency of relative abundances, not absolute concentrations.

## Implementation Readiness

**Overall: Ready to proceed with corrections applied.**

| Aspect | Assessment |
|--------|------------|
| Python feasibility | All methods (chi-square, Mann-Whitney, CLR/ILR transforms, MANOVA, OLS, hierarchical clustering, HDBSCAN, RF, SVM, LDA, k-NN, Graphical Lasso, permutation tests) have well-maintained implementations in scipy, scikit-learn, scikit-bio, and scikit-learn. No custom algorithm implementation needed. |
| Clear data flow | Yes — Q1C correction flows to Q3 and Q4; Q2 labels flow to Q3 and Q4. The pipeline topology is well-defined. |
| Figures are purposeful | Yes — every figure has a specific analytical question it answers. The figure count inflation from Route A (8) to Route B (15) is mostly justified by additional sensitivity visualizations. |
| Ambiguity remaining | Q2 aggregation strategy (artifact vs. point), Q1C calibration pair list, and exact zero-handling thresholds are not resolved in the spec. These must be finalized before coding. |
| Critical blockers | 4 CRITICAL issues (C1-C4). All are fixable with specification changes, not fundamental redesign. |
| High-priority issues | 6 HIGH issues (H1-H6). All are scope reductions or methodological refinements, not new analyses. |
| Estimated implementation effort | Route B with corrections: approximately 800-1200 lines of Python (including visualization code). Core analysis: 400-600 lines. Figures: 300-400 lines. Utility/wrangling: 200-300 lines. |
