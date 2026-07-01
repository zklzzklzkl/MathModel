# Devil's Advocate Report

**Date**: 2026-06-30
**Context**: CUMCM 2022 Problem C -- Ancient glass composition analysis
**Role**: Competition judge with 200+ papers reviewed
**Scope**: Route A (Conservative Baseline) and Route B (High-Score) from MODEL_CANDIDATES.md

---

## 结论: CONDITIONAL_PASS

Both routes are salvageable but each carries a distinct failure mode. Route A would be scored 3-4 for its honesty but methodological gaps will cap it. Route B is scored 4-5 aspirationally, but it is one judge who knows compositional data analysis away from a 2 -- the "method shopping" pattern is glaring. The conditional is: **Route B must be thinned substantially and all compositional data handling must be proven, not claimed.**

---

## Critical Issues (BLOCKER severity)

### C1. Route A Q4: Spearman on raw compositions is a known statistical fallacy

**Location**: Route A Q4, line 73. "Spearman's rho on Q1-corrected data (per glass type)"

**Why this is a blocker**: Spearman's rho is rank correlation, which still operates on the compositional simplex. Despite being non-parametric, it does NOT escape the closure constraint. Consider: if the true composition is (A, B, C) summing to 100% and A increases, something must decrease. Spearman will dutifully report a significant negative correlation between A and every other element -- which is a mathematical artifact, not a chemical truth.

The `PROBLEM_BRIEF.md` line 65 explicitly warns: "所有分析（相关性、聚类、PCA）必须在Aitchison几何框架下进行，使用CLR或ILR变换，否则会产生虚假负相关."

Route A's Q4 as written will produce a heatmap full of spurious negative correlations. A judge who has read Pawlowsky-Glahn & Egozcue (or even just the contest's own problem statement hint) will flag this immediately. This alone could cost 1-1.5 points on Q4.

**Severity**: BLOCKER for Route A on Q4.

**Route A's own risk note** (line 82) already acknowledges "Spearman on raw compositional data still has closure bias" -- this is self-contradictory. If you know it's wrong, why keep it?

### C2. Route A Q3: LDA assumes multivariate normality on compositions

**Location**: Route A Q3, line 61. "LDA classifier (from Q2 Part A)" and Route A Q2 Part A, line 49. "LDA with stepwise forward selection on CLR-transformed data"

**Why this is a blocker**: CLR-transformed compositional data is singular (sum of CLR coordinates = 0), and with 12 usable elements this yields 12 CLR coordinates that are rank-deficient (true dimension = 11). LDA inverts the within-class covariance matrix, which will be singular or nearly singular on:
- 18 High-K samples in 11 or 12 dimensions
- High missing rates for several elements (72.5% Na2O, 36.2% MgO, 34.8% Fe2O3)

The residual covariance matrix after imputation of these missing values will have extremely unstable eigenvalues. LDA discriminant loadings will be unreliable.

**Severity**: BLOCKER for Route A Q3 (and Q2). Use regularized LDA (rLDA) or switch to a method that doesn't require covariance inversion.

### C3. Route B: GMM clustering on 18 points in 11+ dimensions is indefensible

**Location**: Route B Q2 Part B, line 127. "(1) GMM with BIC for k"

**Why this is a blocker**: Gaussian Mixture Models estimate a full or tied covariance matrix per cluster. For 18 High-K samples with ~12 features:
- Each component has O(d^2) = 144 covariance parameters in the full case
- Even with tied covariances, you have O(d^2) + k*d = ~ 144 + 18k parameters
- That is 8+ parameters per data point at minimum

BIC penalizes parameters but the penalty is asymptotic -- BIC's derivation assumes n >> d, which is violently violated here. BIC will likely select k=1 regardless of real structure, or worse, select spurious structure from noise.

A judge with statistical training will ask: "You ran GMM on 18 points in 12 dimensions. How many parameters per component? How many data points per parameter? What is the effective degrees of freedom of your BIC?"

**Severity**: BLOCKER for Route B Q2. GMM should be removed from the consensus or restricted to 2-3 PC dimensions (not 12).

### C4. Route B Q3: 5-classifier soft voting on 66 training samples will produce overconfident predictions

**Location**: Route B Q3, line 138. "Classifiers: Random Forest (n=500), SVM (RBF kernel, grid-search CV), k-NN (k=3,5,7), Gaussian NB, LDA"

**Why this is a blocker**:
5 classifiers each with their own tuning. Grid-search CV for SVM on 66 samples means nested CV is required for honest evaluation. Without it, the "CV accuracy" used for ensemble weights is optimistically biased. The ensemble's "confidence" (vote fraction) is not a calibrated probability -- it is a measure of classifier agreement, not of correctness likelihood.

For 8 unknown samples (A1-A8), reporting "posterior probability distributions" as confidence is misleading. On a dataset this small, an RF of 500 trees with 12 features has each tree seeing ~42 bootstrap samples; the out-of-bag estimate uses ~24 samples per tree. The variance of the OOB error is enormous.

A judge would ask: "Show me your calibration curve on held-out data." With n=69 training and unknown n for test, LOOCV is the only honest option, but ensemble weights learned via CV on 69 points have very low precision.

**Severity**: BLOCKER for Route B Q3 confidence reporting.

---

## High-Severity Concerns

### H1. Route A Q1C: Immobile-element normalization assumes all elements mobilize proportionally

**Location**: Route A Q1C, line 37. "Immobile-element normalization: Assume Al2O3 stable; compute enrichment factor; normalize weathered composition by factor"

**Why it's high**: Al2O3 may be relatively immobile, but the assumption that *all other elements* enrich/deplete proportionally to Al2O3 enrichment is physically dubious. Calcium leaches faster than silicon. Sodium and potassium are orders of magnitude more mobile than aluminum. A proportional correction misattributes differential mobility.

The validation plan (line 39) uses only 4 paired samples (08, 26, 49, 50). With 4 data points, MAE (line 41) has no meaningful confidence interval. The model will look better than it is because 4 points cannot expose generalization failure.

**Recommendation**: Expand paired data to include all points with both weathered and unweathered measurements from the same artifact (DATA_AUDIT.md lists several: 08, 26, 49, 50, plus potentially 23/25/28/29/42/44/53 with resolved label conflicts). Use element-specific enrichment factors rather than one global factor.

### H2. Route B Q1C: Multi-method ensemble with 4 validation points

**Location**: Route B Q1C, line 116-118. "Method 1: Immobile-element... Method 2: Per-element linear regression on paired data (08, 26, 49, 50, 23, 25, etc.)... Method 3: Elastic Net regression"

**Why it's high**: The "(23, 25, etc.)" is hand-waving. Which pairs? How many? The `etc.` signals uncertainty about the actual paired sample count. Elastic Net regression on 4-7 paired data points to predict 12 outputs is severely underpowered. Cross-validated lambda selection with 7 observations is meaningless -- each fold has 1-2 points.

The ensemble weights are "by validation MAE" (line 117), but MAE on 4-7 points has a standard error approximately equal to the MAE itself. The weighted ensemble could be substantially worse than the single best method, and you would not know.

**Recommendation**: Quantify the uncertainty of ensemble weights. If paired data < 8 points, drop the ensemble and report all three methods separately with honest uncertainty bounds. Or use all points that have any weathered + unweathered measurements after label conflict resolution.

### H3. Route B Q1B: CLR-MANOVA is sensitive to missing-value imputation

**Location**: Route B Q1B, line 105. "CLR-transform data (with multiplicative replacement for zeros); two-way MANOVA"

**Why it's high**: MANOVA requires complete cases. CLR requires no zeros. The data has 21.5% missing (excl. SnO2/SO2). The pipeline is: missing imputation -> multiplicative replacement -> CLR -> MANOVA. Four sequential data modifications, each adding noise. The imputation for Na2O (72.5% missing, not random) is particularly dangerous -- MANOVA is sensitive to imputation artifacts because the between/within covariance decomposition depends on group means, which are biased by non-random missingness.

The bootstrapped CI (line 106) helps with variance but not with bias. If the imputed Na2O values are systematically too high in High-K (where they are below detection limit --> actually near-zero), the MANOVA will exaggerate the Na2O weathering effect.

**Recommendation**: For elements with >40% missing within a glass type, report "insufficient data" rather than running MANOVA on imputed values. Run MANOVA only on elements with <20% missing. Alternatively, use multiple imputation and report the between-imputation variance as additional uncertainty.

### H4. Neither route addresses the non-independence of multi-sampling in Q1 statistical tests

**Location**: Both routes Q1A and Q1B.

The DATA_AUDIT.md identifies 11 base IDs with multiple sampling points. For Q1A chi-square (Route A) or logistic regression (Route B), these 11 artifacts contribute up to 2x as many rows. The rows are not independent -- two measurements from artifact 03 are correlated observations, not independent data points.

Standard errors will be artificially small, p-values artificially significant, and CIs artificially narrow because the effective sample size is smaller than the row count.

**Recommendation**: For Q1, either (a) report effective sample size with a clustering correction (cluster-robust standard errors in the logistic regression), or (b) aggregate multi-sampled artifacts to a single representative row before independence tests. The latter is simpler and defensible.

### H5. Route B Q2: HDBSCAN may find 0 or 1 cluster

**Location**: Route B Q2 Part B, line 127. "(2) HDBSCAN for density-based clusters"

**Why it's high**: HDBSCAN has no prior on the number of clusters -- it finds clusters based on density persistence. With 18 High-K points and 40 Pb-Ba points in 11+ CLR dimensions, HDBSCAN may:
- Find 1 cluster (everything is connected at a low density threshold)
- Find noise points only (points separated by large gaps in the sparse high-dimensional space)
- Find spurious micro-clusters from outlier points

If HDBSCAN returns "1 cluster" or "all noise," what is the consensus with GMM and hierarchical clustering? The "majority vote" logic (line 127) breaks down. This needs an explicit fallback protocol.

**Recommendation**: Define the consensus protocol for disagreement edge cases (k=1, k=0, mismatch by >2 clusters). Report method agreement (ARI) between methods honestly -- if ARI < 0.3, do not report a "consensus."

---

## Medium Concerns

### M1. Route A Q1B: Mann-Whitney U with 6 elements at >33% missing

**Location**: Route A Q1B, line 25. "Mann-Whitney U test per element, stratified by glass type"

MW-U tests require observations to be independent and have the same distribution shape under the null. With Na2O (72.5%), K2O (40.6%), MgO (36.2%), Fe2O3 (34.8%), SrO (33.3%) missing, the effective sample size for stratified High-K tests on these elements may be single-digit. A MW-U test on n=3 vs n=5 has essentially zero power and will produce misleading "non-significant" results.

**Recommendation**: State minimum sample size per group (e.g., n >= 5 in each stratum) and suppress tests that fall below it. Report "insufficient data" instead of a p-value.

### M2. Route A Q2: Stepwise selection bias

**Location**: Route A Q2 Part A, line 49. "LDA with stepwise forward selection on CLR-transformed data"

Stepwise selection is known to produce optimistic bias in model fit statistics (R^2, Wilks' lambda, classification accuracy). The selected features will have inflated importance estimates. Combined with the small sample size (C1 above), this is doubly dangerous.

**Recommendation**: Use RF importance or mutual information (as Route B does) for feature ranking instead. If stepwise must be used, report bootstrap-adjusted selection probabilities for each feature rather than a single final model.

### M3. Route B Q1A: Logistic regression with sparse categorical levels

**Location**: Route B Q1A, line 93. "logit(P(风化)) = beta0 + beta1*类型 + beta2*纹饰 + beta3*颜色"

颜色 has 8 levels including rare categories (黑:n=2, 深蓝:n=2, 绿:n=1, 浅绿:n=3). The logistic regression with all 8 color levels will have near-zero observations in several categories, leading to quasi-complete separation and inflated standard errors for those coefficients.

The "unknown" category for 4 missing colors (artifacts 19, 40, 48, 58, all weathered Pb-Ba) creates an additional problem: if all 4 are weathered, the "unknown" category perfectly predicts weathering and causes complete separation.

**Recommendation**: Merge sparse color categories into broader groups (e.g., "green tones" combining 浅绿/深绿/蓝绿/绿) before regression. Handle "unknown" as a separate missing-data indicator or exclude from the color coefficient.

### M4. Route B Q4: Graphical Lasso on 18 samples

**Location**: Route B Q4, line 151. "Partial correlation network (Graphical Lasso, cross-validated lambda) on CLR data"

Graphical Lasso estimates a sparse inverse covariance matrix. With 18 High-K samples in 12 CLR dimensions (true rank 11), the sample covariance is rank-deficient and the GLasso optimization is at the boundary of identifiability. Cross-validated lambda selection with 18 samples per glass type means each CV fold has ~3-4 samples -- the standard error of the selected lambda dominates the estimate.

The resulting partial correlation network will be unstable. Re-run the GLasso with a bootstrap and report edge selection frequencies -- edges appearing in <50% of bootstrap samples are unreliable. I expect most or all edges will fall below this threshold.

**Recommendation**: Use the variation matrix (Aitchison distance) as the primary Q4 result. Present the GLasso network as exploratory with explicit caveats about sample size. Do not draw strong conclusions from GLasso edges for the High-K subgroup.

### M5. Route B Q2: UMAP/t-SNE with 18-40 samples

**Location**: Route B Q2, line 130. "Figure: UMAP/t-SNE visualization"

t-SNE and UMAP are designed for datasets with hundreds to millions of points. With 18 High-K points, t-SNE's perplexity parameter (default 30 > n) is undefined. UMAP with 15 neighbors works formally but the resulting embedding has large random variability between runs. Showing a single t-SNE/UMAP plot as evidence of cluster structure on 18 points is misleading -- the plot is mostly capturing initialization noise, not data structure.

**Recommendation**: Skip t-SNE/UMAP for publication figures. Use PCA biplot (interpretable loadings) as the primary visualization. If t-SNE/UMAP must be included, run with 5+ random seeds and show the most representative embedding, or overlay bootstrap confidence ellipses.

### M6. Route A Q1A: Chi-square test with sparse contingency cells

**Location**: Route A Q1A, line 13. "Chi-square test of independence (pairwise)"

Route A correctly notes the risk (line 17): "Small sample in some color x weathering cells." But "use exact tests or merge sparse categories" is stated as an option, not a protocol. For color (8 levels) x weathering (2 levels), the expected frequencies for rare colors will be << 5. The chi-square approximation is invalid for these tests.

**Recommendation**: Make Fisher's exact test the default for any contingency table with expected cell count < 5. Report which tests use chi-square vs. exact and why.

### M7. Na2O fill strategy not specified in either route

The DATA_AUDIT.md flags Na2O as "systematically missing in High-K" (below detection limit). Neither MODEL_CANDIDATES.md route specifies the actual imputation strategy for this element. Route B mentions "multiplicative replacement for zeros" (line 105) which addresses true zeros, not missing values. The half-DL (half detection limit) approach mentioned in DATA_AUDIT.md is conventional but needs to be justified for Na2O specifically -- Na2O in High-K is a flux component that is definitionally near-zero, so half-DL may systematically overestimate the true concentration.

**Recommendation**: Define the Na2O imputation strategy explicitly: half the minimum detected Na2O value in High-K samples? Half-DL from instrument specification? Zero (treat as below detection = effectively zero)? Each choice has different implications for CLR transforms and subsequent analyses.

---

## Route-Specific Critiques

### Route A: The "Too Honest to Place" Problem

**Structural weakness**: Route A is transparent but incomplete. The problematic pieces:

1. **Q4 is wrong** (C1 above). Spearman on raw compositions produces spurious correlations. This isn't "conservative," it's incorrect. A conservative approach would use CLR + variation matrix as the baseline and note that Spearman in the simplex is not valid.

2. **Validation gaps**: Route A validates only Q1C (4 paired samples for MAE), Q2 Part D (method comparison, which is not validation), and Q3 (sensitivity perturbation). Q1A, Q1B, Q4 have essentially no validation -- the "output" is presented as the result without verification.

3. **Missing uncertainty quantification**: Mann-Whitney p-values are reported without correction for multiple comparisons (12 elements x 2 glass types = 24 tests). Cramer's V has no confidence interval. The Q3 "confidence" from k-NN vote fraction is not a real probability.

4. **The compositional data double standard**: Route A applies CLR for clustering (Q2) but not for correlation (Q4) or effect sizes (Q1B uses raw MW-U). This is inconsistent and suggests the team understands CLR is needed but selectively applies it. A judge will notice.

**Route A grade prediction**: 3-4 if Q4 is fixed. 2-3 if Q4 ships as written. The paper will feel "safe but shallow."

### Route B: The "Method Shopping" Problem

**Structural weakness**: Route B deploys ~15 distinct methods across 4 questions. This is a classic contest anti-pattern: throw many methods at each question and cherry-pick the best-looking results. Specific problems:

1. **Method count by question**:
   - Q1A: Logistic regression + CA = 2 methods
   - Q1B: CLR-MANOVA + Cohen's d + bootstrap CI = 3 techniques
   - Q1C: 3 regression methods + ensemble = 4 models
   - Q2: 3 feature selectors + 3 clusterers + CART + SHAP = 8 methods
   - Q3: 5 classifiers + Mahalanobis + GMM posterior + 3 perturbation levels = many
   - Q4: Variation matrix + GLasso + PCA + permutation test = 4 techniques

   Total: approximately 15-20 distinct statistical/ML methods. No judge believes a team in 3 days properly validated, debugged, and cross-checked 15+ methods. This looks like a GitHub repository, not a contest solution.

2. **The consensus trap**: When multiple methods agree, the paper can claim "consensus." When they disagree, which is expected with n=18-40, the team will be forced to pick -- which is exactly the bias consensus methods claim to avoid. The "majority vote" approach (Q2) assumes methods are independent, but k-means, GMM, and hierarchical clustering on the same data are not independent -- they share the same input and will find similar artifacts.

3. **ML overkill for problem scale**: Random Forest (n=500), SVM with RBF grid search, and 5-classifier ensemble for a 66-sample, 2-class problem is extreme. A careful LDA on properly transformed data would likely match or beat the ensemble on this sample size. The complexity is not justified by the data scale.

4. **The SHAP question**: SHAP values (line 128) are computed from a model's predictions. If the underlying RF or XGBoost model is unreliable due to sample size, the SHAP values inherit that unreliability. SHAP does not make a weak model interpretable -- it just explains a weak model's behavior.

**Route B grade prediction**: 4-5 if the judge is impressed by methodology breadth. 1-2 if the judge is a compositional data specialist who can see through the complexity. The bimodal outcome risk is high.

---

## What A Judge Would Ask

### During Defense / Q&A

1. **"You used CLR transformation. How did you handle the zeros? What is the detection limit? Show me the sensitivity of your results to the replacement value."**

2. **"Your GMM clusters 18 High-K samples in 12 dimensions. How many covariance parameters does each component have? Show me the BIC curve -- was there a clear minimum?"**

3. **"You have an ensemble of 5 classifiers. Show me the calibration curve. What is the Brier score? How does the ensemble compare to the single best classifier?"**

4. **"You claim immobile-element normalization with Al2O3. How do you know Al2O3 is immobile under these burial conditions? What geochemical literature supports this assumption?"**

5. **"Your Q4 partial correlation network for High-K has 18 observations. How many edges are stable under bootstrap? Show the edge selection frequencies."**

6. **"The problem states that Na2O and K2O are systematically depleted during weathering. How does your Q1C model account for element-specific, non-proportional depletion?"**

7. **"Why is Route B using RF importance AND mutual information AND t-test with Bonferroni for feature selection? If they disagree on feature ranking, how do you resolve it? What is the consensus rule?"**

8. **"How do you aggregate multi-sampled artifacts for Q1? The 11 artifacts with multiple measurements violate the independence assumption of your chi-square and logistic regression tests."**

### Methodological Inconsistencies a Detail-Oriented Judge Will Catch

1. Route A applies CLR for Q2 clustering but uses raw compositions for Q4 correlation. Why?
2. Route B Q1B uses CLR for MANOVA. Route B Q1C uses raw-scale regression (Elastic Net on wt%). Why the switch?
3. Route A Q1C normalizes by Al2O3 (one element). Route B Q3 uses "Q1C correction" from an ensemble. If the ensemble disagrees with the physical model, which takes priority and why?

---

## Recommended Hardening Actions

### Must-Fix (before any code is written)

| # | Action | Routes Affected | Priority |
|---|--------|----------------|----------|
| 1 | **Replace Spearman on raw data with Aitchison variation matrix** for Q4 (Route A). Or adopt Route B's Q4 approach entirely. | A | BLOCKER |
| 2 | **Drop GMM from Q2 clustering or restrict to 2-3 PC dimensions**. Use only hierarchical + k-means + bootstrap stability for Route B. | B | BLOCKER |
| 3 | **Define the multi-sample aggregation protocol** before Q1. Cluster-robust SE for logistic regression OR artifact-level aggregation. | A, B | BLOCKER |
| 4 | **Reduce Route B classifiers from 5 to 3** (drop GNB and LDA; keep RF, SVM, k-NN). Report LOOCV accuracy (not CV accuracy from a grid search). | B | BLOCKER |
| 5 | **Specify Na2O/K2O imputation explicitly**. Name the strategy (half-min-DL, zero-fill, or multiple imputation) and justify it per glass type. | A, B | HIGH |

### Should-Fix (before paper writing)

| # | Action | Routes Affected | Priority |
|---|--------|----------------|----------|
| 6 | **Add multiple comparison correction** to all pairwise tests (Bonferroni or Benjamini-Hochberg). 24 element-type tests in Q1 require correction. | A, B | HIGH |
| 7 | **Expand Q1C paired data** by resolving all weathering label conflicts and extracting all artifact-level pairs. | A, B | HIGH |
| 8 | **Merge sparse color categories** (n < 5) before any model that uses color as a predictor. | A, B | HIGH |
| 9 | **Skip t-SNE/UMAP for n<50**. Use PCA biplot as primary visualization. | B | HIGH |
| 10 | **Report bootstrap edge selection frequencies** for GLasso partial correlation network. Suppress edges with <50% bootstrap support. | B | HIGH |
| 11 | **Define HDBSCAN fallback protocol** for k=0 or k=1 cases. | B | MEDIUM |
| 12 | **Use Fisher's exact test** (not chi-square approximation) for any Q1A table with expected counts < 5. | A | MEDIUM |
| 13 | **Report calibration metrics** (Brier score, calibration curve) if reporting classifier "confidence" or "probability." | B | MEDIUM |
| 14 | **Thin Route B** by merging Q1B and Q4 methods where they overlap. MANOVA + variation matrix + GLasso + PCA all address related questions -- pick the 2-3 most informative. | B | MEDIUM |

### Route Recommendation

If the team has strong coding skills and a statistician: **Route B-lite** -- take Route B's compositional data pipeline (CLR throughout) but thin the method count by 40%. Keep: logistic regression for Q1A, CLR-MANOVA for Q1B, 2-method max for Q1C, hierarchical + k-means consensus for Q2, RF + SVM ensemble for Q3, variation matrix + PCA for Q4. Drop: GMM, HDBSCAN, Elastic Net, GNB, LDA, GLasso, t-SNE/UMAP, SHAP. Report ARI between methods transparently.

If the team has limited time or ML experience: **Route A+** -- fix only the blocking compositional data errors (CLR for Q4, regularized LDA for Q3), add multiple comparison correction, and improve the Q1C paired data. Route A with these fixes is a solid 4.

---

## Appendix: Compositional Data Checklist

Every analysis method must be traceable to one of:

| Analysis Type | Valid Approach | Invalid Approach |
|--------------|----------------|-----------------|
| Correlation | Variation matrix var(ln(x_i/x_j)), or correlation on CLR coordinates | Pearson/Spearman on raw wt% |
| Clustering | Euclidean distance on CLR/ILR coordinates | Euclidean on raw wt% |
| PCA | PCA on CLR coordinates (= Aitchison PCA) | PCA on raw wt% |
| Effect size | Cohen's d on CLR coordinates, or log-ratio fold change | t-test on raw wt% |
| Regression (composition predictors) | CLR/ILR coordinates as predictors | Raw wt% as predictors |
| Regression (composition response) | ILR coordinates as multivariate response | Raw wt% as response |

A judge who knows compositional data analysis will apply this checklist mentally. Every deviation needs an explicit justification in the paper.
