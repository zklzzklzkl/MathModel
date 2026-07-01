# Modeling Decision

**Date**: 2026-06-30
**Decision**: **Route C (Hybrid B-lite)** — adopted from model-reviewer and devils-advocate consensus

## Route Selection Logic

- Route A had fatal compositional data errors (Q4 Spearman on raw wt%, Q3 singular LDA)
- Route B had method overkill (GMM, Elastic Net, 5-classifier ensemble on small data)
- **Route C** keeps Route B's CLR/ILR pipeline + permutation-based validation, thins methods 40%

---

## Route C: Final Modeling Plan

### Data Preparation (All Questions)

1. **Parse** artifact IDs from Sheet 2 sampling points. Extract base ID + suffix type.
2. **Resolve** weathering label conflicts: trust Sheet 2 point labels over Sheet 1 for 23, 25, 28, 29, 42, 44, 49, 50, 53.
3. **Exclude** SnO2 and SO2 (>88% missing). Work with 12 chemical components.
4. **Zero handling**: multiplicative replacement (half minimum non-zero per element) before log transforms.
5. **Missing handling**: For Na2O, K2O in their non-defining glass types → half-detection-limit imputation. For other missing → MICE (5 imputations, pooled).
6. **Aggregation rule**: For Q1 association tests (artifact-level), use primary sampling point. For paired weathered/unweathered samples, keep both as pairs. For multi-location (部位1/部位2), average composition. Severely weathered points excluded from classification training.
7. **Compositional transform**: CLR (centered log-ratio) before all distance-based, correlation, or PCA analyses.

### Q1A: Weathering Association Analysis

| Field | Specification |
|-------|---------------|
| Data unit | Artifact-level (n=58, one row per artifact) |
| Method | Chi-square test (weathering × type, weathering × 纹饰, weathering × 颜色) |
| Effect size | Cramer's V for each pair |
| Sparse cells | Fisher's exact test where expected < 5; merge 黑+深蓝 (n=2 each) for color test |
| Missing color | Exclude 4 artifacts from color tests (document separately) |
| Figure | Mosaic plot: weathering × type; grouped bar: weathering × 纹饰 |
| Table | Association summary: χ², df, p, Cramer's V |

### Q1B: Weathering Composition Statistics

| Field | Specification |
|-------|---------------|
| Data unit | Sampling-point-level (69 rows), but paired points handled as pairs |
| Transform | CLR on 12 chemicals (with multiplicative replacement for zeros) |
| Method | Per-element Welch's t-test on CLR coordinates, stratified by glass type |
| Multiple testing | **Holm-Bonferroni correction** across 24 tests (12 elements × 2 types) |
| Effect size | Cohen's d on CLR coordinates |
| Output | Which elements significantly differ (weathered vs unweathered) per type |
| Figure | Volcano plot per glass type (log2 fold change in CLR space vs -log10 adjusted p) |
| Table | Δmedian (original scale), adjusted p, Cohen's d, direction |

### Q1C: Pre-Weathering Prediction

| Field | Specification |
|-------|---------------|
| **Calibration pairs** (exhaustive list) | 49/49未风化点, 50/50未风化点, 08/08严重风化点 (severe, note caveat), 26/26严重风化点 (severe, note caveat) |
| **Additional unweathered points on weathered artifacts** | 23未风化点, 25未风化点, 28未风化点, 29未风化点, 42未风化点, 44未风化点, 53未风化点 — use as reference targets |
| Method 1 (primary) | **Immobile-element normalization**: Scale all elements by Al2O3_unweathered / Al2O3_weathered. Al2O3 is chosen as reference (only 1.4% missing, known to be immobile in glass weathering) |
| Method 2 (supplementary) | Per-element simple OLS: C_original = β · C_weathered + α (fit on paired data, max 8 pairs) |
| Ensemble | Use Method 1 (physical) as primary prediction. Use Method 2 as validation check. Report both. |
| Validation | MAE on paired samples (leave-one-out). If OLS disagrees > 20% with physical model, investigate. |
| Output | Predicted pre-weathering composition for all weathered points + Form 3 unknowns (A2, A5, A6, A7) |
| Figure | Scatter: predicted vs measured on calibration pairs (key elements); before-after composition comparison |
| Table | Prediction results with MAE per element |

### Q2: Classification and Sub-classification

| Field | Specification |
|-------|---------------|
| Data | Q1-corrected compositions (artifact-level, n=58) |
| Transform | CLR + z-score standardization |
| **Part A — 判别元素** | |
| Method | Random Forest feature importance (n_estimators=500, on CLR data) + per-element Welch's t-test with Holm correction + Mutual Information (MI) score |
| Consensus ranking | Average rank across 3 methods. Report top-5 elements. |
| **Part B — 亚类划分** | |
| Method | **Ward's hierarchical clustering** (Euclidean distance on CLR+z-score data). k selection via: (1) silhouette score, (2) gap statistic, (3) dendrogram inspection. Compare with BIC-optimal k-means as robustness check only. |
| Consensus | If 2+ methods agree on k, accept. If all 3 disagree, report all and let manual interpretation decide. |
| Clustering run separately for 高钾 (n=18) and 铅钡 (n=40). | |
| **Part C — 规则** | Decision tree (max_depth=3, min_samples_leaf=3) on original-scale top-5 key elements |
| **Part D — 敏感性** | |
| Bootstrap stability | Resample with replacement (n=1000), recluster, compute ARI against original → median ARI + 95% CI |
| Perturbation | ±5% random perturbation on all elements, recluster → ARI |
| Method comparison | ARI between Ward hierarchical and k-means |
| Figure | Dendrogram with colored clusters; PCA biplot with cluster colors; silhouette plot; decision tree |
| Table | Cluster chemical fingerprint (mean ± SD of key elements per cluster); classification rules |

### Q3: Unknown Classification

| Field | Specification |
|-------|---------------|
| Data | Form 3 (8 unknowns), Q1-corrected for A2, A5, A6, A7 |
| Classifiers | **k-NN (k=3, 5) + Random Forest (n_estimators=500)** (2 classifiers, not 5) |
| Training | Q1-corrected artifact-level Form 2 data (n=58), CLR-transformed |
| Type assignment | Agreement of both classifiers → confident. Disagreement → report both, indicate uncertainty. |
| Confidence | k-NN: fraction of k neighbors voting for assigned class. RF: proportion of trees. Report as "vote fraction" NOT "probability." |
| Sub-class | Mahalanobis distance to each sub-class centroid (from Q2); assign to nearest |
| Sensitivity | |
| Perturbation | ±5% and ±10% on all elements → re-classify → report stability (% unchanged) |
| LOOCV | Leave-one-out on training set → accuracy on known data |
| Classifier ablation | Report if k-NN and RF agree/disagree per artifact |
| Figure | PCA biplot with training data colored by type + Q3 samples marked; classification bar chart |
| Table | A1-A8: type, sub-class, k-NN vote, RF vote, agreement status |

### Q4: Chemical Association Analysis

| Field | Specification |
|-------|---------------|
| Data | Q1-corrected, artifact-level (n=58), CLR-transformed 12 chemicals |
| Groups | 高钾 (n≈18) vs 铅钡 (n≈40); also sub-class groups from Q2 |
| Method 1 | **Aitchison variation matrix**: var(ln(x_i / x_j)) for all i,j pairs → pairwise log-ratio variance |
| Method 2 | PCA biplot per glass type on CLR data → visualize element co-variation structure |
| Method 3 | Spearman on CLR coordinates (valid post-transform) as supplementary |
| Group difference test | **Permutation test** (n=10000): Frobenius norm of correlation matrix difference; p = proportion of permuted norms ≥ observed |
| Figure | Variation matrix heatmap (per type); PCA biplot (per type); CLR correlation heatmap (per type) |
| Table | Significantly different element pairs between types (permutation p < 0.05) |

---

## Figure Plan (Core Paper Figures)

| Fig# | Content | Q | Type | Backend |
|------|---------|----|------|---------|
| F1 | Mosaic plot: weathering × glass type + decoration bar chart | Q1A | Categorical | matplotlib |
| F2 | Volcano plots: weathering effect per element (one per glass type) | Q1B | Statistical | matplotlib |
| F3 | Before-after composition comparison (paired samples) | Q1C | Comparison | matplotlib |
| F4 | PCA biplot + dendrogram: High-K sub-classes | Q2 | Multivariate | matplotlib |
| F5 | PCA biplot + dendrogram: Pb-Ba sub-classes | Q2 | Multivariate | matplotlib |
| F6 | Decision tree: classification rules | Q2 | Tree | matplotlib/sklearn |
| F7 | PCA biplot with Q3 unknowns projected | Q3 | Projection | matplotlib |
| F8 | Classification results bar chart: A1-A8 | Q3 | Bar | matplotlib |
| F9 | Variation matrix heatmaps (High-K + Pb-Ba) | Q4 | Heatmap | matplotlib/seaborn |
| F10 | PCA biplots per glass type (correlation structure) | Q4 | Multivariate | matplotlib |

---

## Implementation Quality Rules

1. Every figure must have legible labels (font ≥ 10pt), explicit axis titles, and a caption stating the conclusion.
2. All numerical claims in the paper must map to a row in RESULTS_MANIFEST.json.
3. Sensitivity analysis results must have their own table or figure, not just a text mention.
4. Missing data handling decisions must be documented in code comments and paper methods section.
