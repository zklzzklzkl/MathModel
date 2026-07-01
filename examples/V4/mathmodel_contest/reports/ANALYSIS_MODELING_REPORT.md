# Analysis Modeling Report

**Date**: 2026-06-30
**Route**: C (B-lite hybrid) — CLR pipeline + thinned methods for small-sample validity

---

## 0. Data Preparation Pipeline

### 0.1 Artifact ID Parsing
- Extract base ID from Sheet 2 `文物采样点`: strip suffixes (部位1, 部位2, 未风化点, 未风化点1, 未风化点2, 严重风化点)
- Create `sampling_type` column: 'primary', '部位1', '部位2', '未风化点', '严重风化点'

### 0.2 Weathering Label Resolution
- Primary weathering label from Sheet 1 `表面风化`
- For multi-point artifacts with '未风化点' suffix: use '无风化' for those specific measurements
- For '严重风化点' suffix: use '严重风化' for those specific measurements

### 0.3 Chemical Component Selection
- **EXCLUDE**: SnO2 (89.9% missing), SO2 (88.4% missing)
- **KEEP**: SiO2, Na2O, K2O, CaO, MgO, Al2O3, Fe2O3, CuO, PbO, BaO, P2O5, SrO (12 components)

### 0.4 Zero and Missing Value Handling
- **Zeros**: Replace 0 with 0.01 (half the minimum non-zero value per element across all samples)
- **Na2O in High-K**: Treat None as `<detection_limit`, impute with half minimum non-zero Na2O in Pb-Ba
- **K2O in Pb-Ba**: Treat None as `<detection_limit`, impute with half minimum non-zero K2O in High-K
- **Other None values**: MICE with 5 imputations (pooled), or median per glass type if MICE fails

### 0.5 Artifact-Level Aggregation
- For multi-location (部位1/部位2): average composition
- For paired weathered/unweathered: keep both rows, mark as paired
- For severely weathered: keep separate, exclude from classification training
- For ID 42 with 2 unweathered points: average
- Result: ~58 artifact-level rows

### 0.6 Compositional Data Transform
- Multiplicative replacement for all zeros
- CLR (centered log-ratio) transformation on 12 components
- Formula: clr(x_i) = ln(x_i / g(x)) where g(x) = geometric mean of all components

---

## 1. Q1: Weathering Analysis and Prediction

### 1A: Association Analysis

**Mathematical Form:**
- H0: Weathering is independent of factor F
- Test statistic: χ² = Σ (O_ij - E_ij)² / E_ij
- Effect size: Cramer's V = √(χ² / (n × min(r-1, c-1)))
- For sparse tables: Fisher-Freeman-Halton exact test

**Algorithm:**
1. Build 2×2 (weathering × type) and 2×3 (weathering × 纹饰) contingency tables from artifact-level data (n=58)
2. For color: merge categories with <3 observations (黑+深蓝 → 深色)
3. Compute χ², p-value, Cramer's V for each association
4. Generate mosaic plot and grouped bar chart

### 1B: Compositional Weathering Statistics

**Mathematical Form:**
- CLR transform all compositions: `z_i = clr(x_i)`
- Per element j, stratified by glass type t:
  - Mean difference: δ_jt = mean(z_j | weathered) - mean(z_j | unweathered)
- Welch's t-test: t_jt = δ_jt / √(s²_w/n_w + s²_u/n_u)
- Effect size: Cohen's d_jt = δ_jt / s_pooled
- Multiple testing: 24 tests → Holm-Bonferroni adjusted α = 0.05 / (24 - rank + 1)

**Algorithm:**
1. CLR-transform all 69 rows
2. Split by glass type (High-K, Pb-Ba)
3. Within each type, test each element: weathered vs unweathered (including unweathered points)
4. Apply Holm correction across all 24 tests
5. Generate volcano plot: log2(mean weathered / mean unweathered + ε) vs -log10(adj_p)

### 1C: Pre-Weathering Prediction

**Mathematical Form (Method 1 — Immobile-Element Normalization):**
- Reference element R = Al2O3 (most complete, known immobile)
- Enrichment factor: EF = Al2O3_unweathered_ref / Al2O3_weathered
- Predicted original composition: X_i_original = X_i_weathered × EF

**Mathematical Form (Method 2 — Per-Element OLS):**
- For paired samples: X_i_original = β_i × X_i_weathered + α_i + ε
- Fitted via OLS on 4-8 calibration pairs

**Calibration pairs:**
| Weathered | Unweathered | Type |
|-----------|-------------|------|
| 49 | 49未风化点 | Pb-Ba |
| 50 | 50未风化点 | Pb-Ba |
| 08 | — (severe) | Pb-Ba |
| 26 | — (severe) | Pb-Ba |
| 23 | 23未风化点 | Pb-Ba |
| 25 | 25未风化点 | Pb-Ba |
| 28 | 28未风化点 | Pb-Ba |
| 29 | 29未风化点 | Pb-Ba |
| 42 | 42未风化点1+42未风化点2 | Pb-Ba |
| 44 | 44未风化点 | Pb-Ba |
| 53 | 53未风化点 | Pb-Ba |

**Algorithm:**
1. Compute mean Al2O3 in all unweathered High-K and Pb-Ba samples (separately)
2. For each weathered sample, compute EF relative to its type's reference
3. Apply EF to all 12 elements → predicted pre-weathering composition
4. Validate on paired samples: compute MAE per element
5. Apply Method 2 on paired samples as cross-check
6. Report Method 1 as primary, Method 2 as validation

---

## 2. Q2: Classification and Sub-Classification

### 2A: Discriminant Element Identification

**Mathematical Form:**
- Three-method consensus ranking:
  1. Random Forest importance: impurity decrease averaged over 500 trees
  2. Welch's t-test: |t| between High-K and Pb-Ba per element (CLR coordinates)
  3. Mutual Information: I(X_j; Y) = Σ p(x,y) log(p(x,y) / (p(x)p(y)))

**Algorithm:**
1. On CLR-transformed artifact-level data
2. Compute importance scores for each of 12 elements by each method
3. Rank elements within each method (1=best)
4. Average rank across methods → consensus rank
5. Report top-5 discriminant elements

### 2B: Sub-Classification

**Mathematical Form:**
- Distance: Euclidean on CLR + z-score standardized data
- Clustering: Ward's minimum variance method
  - Merges clusters A, B to minimize Δ(A,B) = ESS_AB - ESS_A - ESS_B
  - ESS = Σ ||x_i - centroid||²
- k selection: Silhouette score s(i) = (b(i) - a(i)) / max(a(i), b(i))

**Algorithm:**
1. For each glass type separately:
   a. CLR-transform artifact-level compositions
   b. Z-score standardize
   c. Compute Ward's hierarchical clustering
   d. Evaluate k=2..min(6, n/3) via silhouette score and gap statistic
   e. Select k where silhouette peaks and gap statistic is significant
2. Run k-means with selected k as cross-check
3. Compute ARI between Ward and k-means
4. Bootstrap (n=1000): resample, recluster, compute ARI → stability metric

### 2C: Decision Rule Extraction

**Mathematical Form:**
- Decision tree: recursive binary partitioning
- Split criterion: Gini impurity G = 1 - Σ p_k²
- Max depth = 3, min samples per leaf = 3
- Features: top-5 elements from 2A (original wt% scale)

**Algorithm:**
1. Train CART decision tree on original-scale data with cluster labels
2. Extract rules as paths from root to leaf
3. Simplify rules: round thresholds to reasonable precision

### 2D: Sensitivity

**Bootstrap stability:** Median ARI + 95% CI from 1000 resamples
**Perturbation:** ±5% random noise → recluster → ARI
**Method agreement:** Ward vs k-means ARI

---

## 3. Q3: Unknown Classification

### Mathematical Form

**k-Nearest Neighbors:**
- Distance: Euclidean on CLR coordinates
- k = 3, 5 (odd to avoid ties)
- Vote fraction: v = (number of k neighbors with class C) / k

**Random Forest:**
- 500 trees, Gini splitting
- Tree vote fraction: proportion of trees predicting class C
- Class assignment: majority vote among trees

**Mahalanobis Distance (sub-class):**
- D² = (x - μ_c)ᵀ Σ⁻¹ (x - μ_c)
- x = CLR coordinates of unknown
- μ_c = CLR centroid of sub-class c
- Σ = pooled within-group covariance (if n per sub-class < 5: use diagonal)

### Preprocessing
- For weathered unknowns (A2, A5, A6, A7): apply Q1C correction first
- CLR-transform all (training + corrected unknowns)
- Standardize to training data mean/SD

### Algorithm
1. Apply Q1C weathering correction to A2, A5, A6, A7
2. CLR-transform training data + unknowns
3. Run k-NN (k=3, k=5) and RF on transformed data
4. If k-NN and RF agree: confident assignment
5. If disagreement: report both with vote fractions
6. For sub-class: compute Mahalanobis distance to each sub-class centroid
7. Assign to nearest sub-class

### Sensitivity
- ±5% and ±10% perturbation on all elements → re-classify → report % stable
- Leave-one-out CV on training data
- Report classifier agreement matrix (Fleiss' κ if time permits)

---

## 4. Q4: Compositional Association Analysis

### 4.1 Variation Matrix

**Mathematical Form:**
- For elements i, j: τ_ij = var(ln(x_i / x_j)) across all samples
- Low τ_ij → i and j are proportional (co-vary together)
- High τ_ij → i and j vary independently (or inversely due to closure)

**Algorithm:**
1. CLR-transform artifact-level compositions
2. Compute all 66 pairwise log-ratio variances: τ_ij
3. Visualize as heatmap (ordered by hierarchical clustering)

### 4.2 PCA Biplot

- On CLR-transformed data, per glass type
- Display PC1 vs PC2 with element loading vectors
- Points colored by weathering status and sub-class

### 4.3 Group Difference Test

**Permutation Test:**
- H0: Σ_HighK = Σ_PbBa (correlation matrices equal)
- Test statistic: T = ||Σ_HighK - Σ_PbBa||_F (Frobenius norm of difference)
- Procedure:
  1. Compute observed T_obs
  2. Shuffle type labels 10000 times
  3. Compute T_perm for each shuffle
  4. p = (# T_perm ≥ T_obs) / 10000
- Reject H0 if p < 0.05

---

## 5. Implementation Notes

### Python Dependencies
```
numpy, scipy, pandas, matplotlib, seaborn, scikit-learn,
openpyxl, python-docx, statsmodels
```

### Figure Export
- Format: PDF (vector) for paper; PNG (300 DPI) as backup
- Color: 'viridis' for sequential, 'Set2' for categorical (colorblind-friendly)
- Font: SimHei or DejaVu Sans (Chinese-compatible)

### RESULTS_MANIFEST.json
Each key result gets a JSON entry:
```json
{
  "result_id": "Q1B_HighK_K2O_pvalue",
  "question": "Q1B",
  "value": 0.0034,
  "units": "p-value (Holm-adjusted)",
  "description": "K2O difference between weathered and unweathered High-K glass",
  "source": "code/q1_weathering.py"
}
```
