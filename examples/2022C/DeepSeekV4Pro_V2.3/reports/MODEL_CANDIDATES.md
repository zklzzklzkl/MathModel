# Model Candidates

## Route A: Conservative Baseline (稳健基线)

**Philosophy**: Well-established, transparent, easily validated methods. Prioritizes interpretability and reliability over sophistication.

### Q1A: Weathering Association Analysis

| Component | Specification |
|-----------|---------------|
| Objective | Test association of weathering with glass type, decoration, and color |
| Variables | 风化 (binary) ~ 类型 (binary) + 纹饰 (3-level) + 颜色 (8-level) |
| Method | Chi-square test of independence (pairwise); Cramer's V for effect size |
| Assumptions | Expected frequencies ≥5 in contingency tables; observations independent |
| Output | p-values table, Cramer's V matrix, mosaic plots |
| Figure | Mosaic plot of weathering × type; grouped bar chart weathering × decoration |
| Risk | Small sample in some color × weathering cells → use exact tests or merge sparse categories |

### Q1B: Compositional Weathering Statistics

| Component | Specification |
|-----------|---------------|
| Objective | Quantify chemical differences between weathered and unweathered within each glass type |
| Variables | 12 usable chemicals (excl. SnO2, SO2) |
| Method | Mann-Whitney U test per element, stratified by glass type; report median difference + 95% CI |
| Assumptions | MW-U: independence, same shape under null |
| Handling | Missing treated as below detection limit (half minimum non-zero per element) |
| Output | Per-element weathered vs. unweathered comparison table; box plots by type |
| Table | Weathering effect table: Δmedian, p-value, effect size r |
| Figure | Paired box plot grid: 6×2 (6 key elements × 2 glass types) |

### Q1C: Pre-Weathering Prediction

| Component | Specification |
|-----------|---------------|
| Objective | Predict pre-weathering composition from weathered measurements |
| Method | **Immobile-element normalization**: Assume Al2O3 (most complete immobile) stable; compute enrichment factor; normalize weathered composition by factor |
| Variables | Al2O3 as reference; adjust all elements proportionally |
| Calibration | Use paired weathered/unweathered data (08, 26, 49, 50) for validation |
| Output | Predicted pre-weathering composition for all weathered points + Form 3 unknowns |
| Validation | Mean absolute error (MAE) on paired samples |
| Table | Prediction results: weathered → predicted original → MAE |

### Q2: Glass Classification and Sub-classification

| Component | Specification |
|-----------|---------------|
| Objective | Identify discriminant elements for 高钾/铅钡; discover sub-classes within each type |
| Part A — 判别元素 | LDA with stepwise forward selection on CLR-transformed data; report standardized loadings |
| Part B — 亚类划分 | Hierarchical clustering (Ward's method, Euclidean on CLR+z-score data); k via silhouette score |
| Part C — 规则定义 | Decision tree (CART) on original-scale key elements |
| Part D — 敏感性 | Compare k-means and hierarchical ARI; bootstrap cluster stability |
| Figure | Dendrogram per type; LDA score plot; silhouette plot; decision tree diagram |
| Table | Cluster characteristics: centroid composition, size, interpretability |

### Q3: Unknown Sample Classification

| Component | Specification |
|-----------|---------------|
| Objective | Classify A1-A8 into 高钾/铅钡 + sub-class |
| Method | LDA classifier (from Q2 Part A) + k-NN (k=3,5) + majority vote |
| Preprocessing | Apply Q1C correction for weathered samples (A2, A5, A6, A7) |
| Confidence | Posterior probability from LDA; vote fraction from k-NN |
| Sensitivity | ±5% perturbation on key elements → re-classify; report stability |
| Table | A1-A8 classification results with confidence scores |

### Q4: Chemical Association Analysis

| Component | Specification |
|-----------|---------------|
| Objective | Within-group correlation structure + between-group comparison |
| Method | Spearman's ρ on Q1-corrected data (per glass type); Mantel test for matrix difference |
| Variables | 12 usable chemicals |
| Figure | Heatmap: 12×12 Spearman correlation per type; pair plot of top 5 elements |
| Table | Significant correlations (|ρ|>0.5, p<0.05) per type |

### Route A: Summary

| Aspect | Assessment |
|--------|------------|
| Advantages | Transparent, fast, easily interpreted, minimal assumptions |
| Risks | Immobile-element normalization may oversimplify weathering physics; Spearman on raw compostional data still has closure bias; LDA assumes normality which raw compositions violate |
| Figure count | ~8 figures + ~6 tables |

---

## Route B: High-Score Route (高分冲刺)

**Philosophy**: Rigorous compositional data handling, modern machine learning, comprehensive validation. Targeted at top-tier score.

### Q1A: Weathering Association (Extended)

| Component | Specification |
|-----------|---------------|
| Method | Logistic regression: logit(P(风化)) = β0 + β1·类型 + β2·纹饰 + β3·颜色; odds ratios; model comparison via AIC |
| Enhancement | Correspondence analysis (CA) for multivariate visualization of associations among 风化, 类型, 纹饰, 颜色 |
| Output | Odds ratio table + 95% CI; CA biplot |
| Figure | CA biplot; forest plot of odds ratios |
| Handling | Missing color → treat as separate "unknown" category |

### Q1B: Compositional Weathering Statistics (Rigorous)

| Component | Specification |
|-----------|---------------|
| Method | CLR-transform data (with multiplicative replacement for zeros); two-way MANOVA (风化 × 类型); per-element Cohen's d on CLR coordinates |
| Enhancement | Bootstrapped 95% CI for median log-ratio differences |
| Output | MANOVA table; per-element effect size with CI |
| Figure | Volcano plot (log2 fold change vs. -log10 p-value) per glass type; PCA biplot colored by weathering status |

### Q1C: Pre-Weathering Prediction (Multi-Method)

| Component | Specification |
|-----------|---------------|
| Method 1 | Immobile-element normalization (Al2O3 reference) — physical basis |
| Method 2 | Per-element linear regression on paired data (08, 26, 49, 50, 23, 25, etc.) |
| Method 3 | Elastic Net regression (cross-validated) for multivariate prediction |
| Ensemble | Weighted average of methods 1-3; weights by validation MAE |
| Validation | Leave-one-pair-out cross-validation |
| Output | Prediction + 95% bootstrap CI for each element |
| Table | Method comparison table (MAE by element, overall MAE) |

### Q2: Classification and Sub-classification (Advanced)

| Component | Specification |
|-----------|---------------|
| Part A — 特征选择 | Random Forest importance (CLR data) + mutual information + t-test with Bonferroni correction; consensus ranking |
| Part B — 亚类发现 | **Three-method consensus**: (1) GMM with BIC for k; (2) HDBSCAN for density-based clusters; (3) Hierarchical clustering; cluster consensus via majority vote; ARI for method agreement |
| Part C — 规则定义 | Decision tree (CART) + rule simplification; SHAP values for feature contribution |
| Part D — 敏感性 | Bootstrap resampling (n=1000): cluster stability measured by adjusted Rand index; perturbation analysis: ±5%, ±10% on features; cross-validator comparison |
| Figure | UMAP/t-SNE visualization; dendrogram with bootstrap support; decision tree; SHAP summary plot; ARI heatmap (method comparison) |
| Table | Per-cluster chemical fingerprint table; classification rule table |

### Q3: Unknown Classification (Robust Ensemble)

| Component | Specification |
|-----------|---------------|
| Preprocessing | Q1C correction for A2, A5, A6, A7; CLR transform |
| Classifiers | Random Forest (n=500), SVM (RBF kernel, grid-search CV), k-NN (k=3,5,7), Gaussian NB, LDA |
| Ensemble | Soft voting with classifier weights from CV accuracy |
| Confidence | Posterior probability distributions; entropy of ensemble agreement |
| Sub-class | Mahalanobis distance to each sub-class centroid → nearest + probabilistic from GMM posterior |
| Sensitivity | Input perturbation ±5% and ±10% on key elements; LOOCV on training set; classifier ablation (remove one at a time) |
| Figure | Classification probability bar chart per artifact; PCA with Q3 samples projected |

### Q4: Compositional Association Network

| Component | Specification |
|-----------|---------------|
| Data | CLR-transformed, Q1-corrected compositions |
| Method 1 | Variation matrix (Aitchison): var(ln(x_i/x_j)) for all element pairs → log-ratio variance heatmap |
| Method 2 | Partial correlation network (Graphical Lasso, cross-validated λ) on CLR data → conditional dependency graph |
| Method 3 | PCA biplot per glass type → visualize element co-variation |
| Statistical test | Permutation test (n=10000): Frobenius norm of correlation matrix difference between types; p-value for H0: matrices equal |
| Figure | Variation matrix heatmap (per type); partial correlation network graph; PCA biplot; matrix difference heatmap |
| Table | Significant partial correlations (conditional dependencies) per type |

### Route B: Summary

| Aspect | Assessment |
|--------|------------|
| Advantages | Full compositional data pipeline; multi-method consensus; rigorous sensitivity/uncertainty quantification; ML interpretability (SHAP); network analysis |
| Risks | Higher complexity, more code, more computation; GMM convergence on small samples may be unstable; HDBSCAN may find no sub-clusters if data is continuous; some methods require more justification |
| Figure count | ~15 figures + ~8 tables |

---

## Route Comparison

| Dimension | Route A (Conservative) | Route B (High-Score) |
|-----------|----------------------|---------------------|
| Q1A Method | Chi-square + Cramer's V | Logistic regression + CA |
| Q1B Method | Mann-Whitney U per element | CLR-MANOVA + bootstrapped d |
| Q1C Method | Immobile-element normalization | 3-method ensemble + bootstrap CI |
| Q2 Discriminant | LDA stepwise | RF importance + mutual info |
| Q2 Clustering | Hierarchical (Ward) | GMM + HDBSCAN + Hierarchical consensus |
| Q3 Classifiers | LDA + k-NN | RF + SVM + k-NN + GNB + LDA ensemble |
| Q4 Correlation | Spearman + Mantel test | CLR variation matrix + graphical lasso + permutation test |
| Compositional data handling | CLR for clustering only | CLR/ILR throughout |
| Validation depth | Basic | Comprehensive |
| Sensitivity scope | Q2 only (method comparison) | Q2, Q3 both (bootstrap + perturbation + ablation) |
| Figure count | ~8 figures | ~15 figures |
| Implementation risk | Low | Medium (more dependencies) |
| Score potential | 3-4 | 4-5 |
