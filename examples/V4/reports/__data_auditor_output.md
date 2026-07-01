# Data Audit Report: CUMCM 2022 Problem C

**Ancient Glass Chemical Composition Analysis and Classification**
**Date**: 2026-06-30
**Source**: __data_raw.txt (XLSX extraction, UTF-8)
**Auditor**: Read-only data audit agent

---

## 1. Sheet 1 (表单1): Artifact Basic Information

### 1.1 Field Inventory

| # | Field Name | Data Type | Meaning | Missing |
|---|-----------|-----------|---------|---------|
| 1 | 文物编号 | string (2-digit) | Artifact ID, 01-58 | 0 |
| 2 | 纹饰 | categorical {A, B, C} | Decoration type | 0 |
| 3 | 类型 | categorical {高钾, 铅钡} | Glass type (High-K, Pb-Ba) | 0 |
| 4 | 颜色 | categorical (8 values) | Glass color | 4 |
| 5 | 表面风化 | categorical {风化, 无风化} | Surface weathering status | 0 |

### 1.2 Row and Column Counts

- **Data rows**: 58 (header excluded)
- **Columns**: 5
- **No duplicate IDs**: All IDs 01-58 are unique.

### 1.3 Missing Value Analysis

- **颜色 (Color)**: 4 missing (IDs: 19, 40, 48, 58)
  - All 4 are Pb-Ba + weathered. The weathering likely obliterates the color.
  - Risk: These 4 artifacts cannot contribute to color-based subtype analysis.

### 1.4 Variable Distributions

| Variable | Distribution |
|----------|-------------|
| Glass Type | 高钾 (High-K): 18, 铅钡 (Pb-Ba): 40 |
| Weathering | 风化 (Weathered): 34, 无风化 (Unweathered): 24 |
| Decoration | A: 22, B: 6, C: 30 |
| Color | 浅蓝 (Light Blue): 20, 蓝绿 (Blue-Green): 15, 深绿 (Dark Green): 7, 紫 (Purple): 4, 浅绿 (Light Green): 3, 黑 (Black): 2, 深蓝 (Dark Blue): 2, 绿 (Green): 1 |

---

## 2. Sheet 2 (表单2): Classified Glass Chemical Composition

### 2.1 Field Inventory

| # | Field Name | Data Type | Meaning | Missing |
|---|-----------|-----------|---------|---------|
| 1 | 文物采样点 | string | Sampling point ID (artifact ID + optional suffix) | 0 |
| 2 | 二氧化硅 (SiO2) | float (%) | Silicon dioxide | 0 |
| 3 | 氧化钠 (Na2O) | float (%) | Sodium oxide | 50 |
| 4 | 氧化钾 (K2O) | float (%) | Potassium oxide | 28 |
| 5 | 氧化钙 (CaO) | float (%) | Calcium oxide | 8 |
| 6 | 氧化镁 (MgO) | float (%) | Magnesium oxide | 25 |
| 7 | 氧化铝 (Al2O3) | float (%) | Aluminum oxide | 1 |
| 8 | 氧化铁 (Fe2O3) | float (%) | Iron oxide | 24 |
| 9 | 氧化铜 (CuO) | float (%) | Copper oxide | 5 |
| 10 | 氧化铅 (PbO) | float (%) | Lead oxide | 11 |
| 11 | 氧化钡 (BaO) | float (%) | Barium oxide | 16 |
| 12 | 五氧化二磷 (P2O5) | float (%) | Phosphorus pentoxide | 10 |
| 13 | 氧化锶 (SrO) | float (%) | Strontium oxide | 23 |
| 14 | 氧化锡 (SnO2) | float (%) | Tin oxide | 62 |
| 15 | 二氧化硫 (SO2) | float (%) | Sulfur dioxide | 61 |

### 2.2 Row and Column Counts

- **Data rows**: 69 (header excluded)
- **Columns**: 15 (1 ID + 14 chemical components)
- **Note**: 69 rows > 58 artifacts. Multiple sampling points for some artifacts.

### 2.3 Missing Value Analysis (Ranked by Missing Rate)

| Component | Missing Count | Missing Rate | Severity |
|-----------|--------------|--------------|----------|
| SnO2 | 62/69 | 89.9% | CRITICAL |
| SO2 | 61/69 | 88.4% | CRITICAL |
| Na2O | 50/69 | 72.5% | HIGH |
| K2O | 28/69 | 40.6% | HIGH |
| MgO | 25/69 | 36.2% | HIGH |
| Fe2O3 | 24/69 | 34.8% | HIGH |
| SrO | 23/69 | 33.3% | HIGH |
| BaO | 16/69 | 23.2% | MEDIUM |
| PbO | 11/69 | 15.9% | MEDIUM |
| P2O5 | 10/69 | 14.5% | MEDIUM |
| CaO | 8/69 | 11.6% | LOW |
| CuO | 5/69 | 7.2% | LOW |
| Al2O3 | 1/69 | 1.4% | LOW |
| SiO2 | 0/69 | 0.0% | NONE |

**Key finding**: SnO2 and SO2 are effectively unusable (>88% missing). Na2O is missing for most High-K samples (where it was below detection limit). K2O, MgO, Fe2O3, and SrO have high missing rates.

### 2.4 Composition Sum Check (Quality Gate: 85%-105%)

**Method**: Sum of all non-None component values for each row.

- **Min sum**: 71.89% (ID 17)
- **Max sum**: 100.00% (ID 08严重风化点 -- actually exceeds 100% slightly due to this being a sum of available values)
- **Mean sum**: 96.95%
- **In range [85%, 105%]**: 67/69 (97.1%)
- **Flagged (<85%)**: 2 rows

| Sample ID | Sum | Direction | None Count |
|-----------|-----|-----------|------------|
| 15 | 79.47% | LOW | 4 |
| 17 | 71.89% | LOW | 4 |

**Flagged (>105%)**: 0 rows

**Interpretation**: Both low-sum rows (IDs 15 and 17) are High-K type with CaO and other oxides missing. The low total may reflect undetected trace components or measurement uncertainty rather than data error. These are acceptable as-is but should be noted.

**Additional note**: Row '08严重风化点' sums to ~100.37% including all present values which is within rounding tolerance; the ">100%" is due to rounding in the original data.

### 2.5 Re-checking ALL rows' sums for any >105%

None found. All 69 rows have sums within 100% +/- rounding tolerance when all non-None values are summed.

---

## 3. Multi-Sample and Duplicate Records

### 3.1 Artifacts with Multiple Sampling Points

The following 11 base artifacts have 2+ sampling points in Sheet 2:

| Base ID | Sampling Points | Note |
|---------|----------------|------|
| 03 | 03部位1, 03部位2 | Two different locations |
| 06 | 06部位1, 06部位2 | Two different locations |
| 08 | 08, 08严重风化点 | Normal + severely weathered point |
| 26 | 26, 26严重风化点 | Normal + severely weathered point |
| 30 | 30部位1, 30部位2 | Two different locations |
| 42 | 42未风化点1, 42未风化点2 | Two unweathered points |
| 43 | 43部位1, 43部位2 | Two different locations |
| 49 | 49, 49未风化点 | Weathered + unweathered point |
| 50 | 50, 50未风化点 | Weathered + unweathered point |
| 51 | 51部位1, 51部位2 | Two different locations |
| 54 | 54, 54严重风化点 | Normal + severely weathered point |

### 3.2 Sampling Point Typology

Three types of multi-sampling exist:
1. **Multi-location** (部位1/部位2): IDs 03, 06, 30, 43, 51 -- different physical locations on the same artifact
2. **Weathered/Unweathered pair** (风化/未风化): IDs 49, 50 -- critical for Q1 weathering analysis
3. **Normal/Severely weathered pair** (严重风化点): IDs 08, 26, 54 -- different degrees of weathering
4. **Two unweathered points**: ID 42 -- duplicate unweathered measurements

### 3.3 Within-Pair Composition Variability (Notable Examples)

- **03部位1 vs 03部位2**: SiO2 87.05% vs 61.71% -- extreme difference, suggests different glass regions or contamination
- **08 vs 08严重风化点**: SiO2 20.14% vs 4.61% -- severe weathering massively depletes SiO2
- **26 vs 26严重风化点**: SiO2 19.79% vs 3.72% -- same pattern
- **49 vs 49未风化点**: SiO2 28.79% vs 54.61% -- weathering halves SiO2 in Pb-Ba glass

---

## 4. Sheet 1 + Sheet 2 Join Analysis

### 4.1 Join Coverage

- **Sheet 1 unique IDs**: 58 (01-58)
- **Sheet 2 unique base IDs**: 58 (01-58)
- **Full match**: All 58 artifacts have composition data in Sheet 2.
- **Orphans in Sheet 1**: 0
- **Orphans in Sheet 2**: 0

**Conclusion**: Every artifact in the basic info table has at least one chemical composition record. This is a complete join.

### 4.2 Implicit Weathering-Label Conflicts

Sheet 2 suffixes reveal information not in Sheet 1:

| Artifact | Sheet 1 表面风化 | Sheet 2 Implicit |
|----------|----------------|-------------------|
| 23 | 风化 | 23未风化点 (unweathered point exists) |
| 25 | 风化 | 25未风化点 (unweathered point exists) |
| 28 | 风化 | 28未风化点 (unweathered point exists) |
| 29 | 风化 | 29未风化点 (unweathered point exists) |
| 42 | 风化 | 42未风化点1, 42未风化点2 (unweathered points exist) |
| 44 | 风化 | 44未风化点 (unweathered point exists) |
| 53 | 风化 | 53未风化点 (unweathered point exists) |

**Risk HIGH**: Sheet 1 labels IDs 23, 25, 28, 29, 42, 44, 53 as "风化" (weathered), but Sheet 2 contains "未风化点" (unweathered point) measurements for these artifacts. This means the artifact has both weathered and unweathered regions, and the composition data may correspond to the unweathered portion. For Q1 weathering analysis, this ambiguity must be resolved.

---

## 5. Sheet 3 (表单3): Unclassified Glass Chemical Composition

### 5.1 Field Inventory

Same 14 chemical components as Sheet 2 (columns 3-16), plus:

| # | Field Name | Data Type | Meaning | Missing |
|---|-----------|-----------|---------|---------|
| 1 | 文物编号 | string (A1-A8) | Unclassified artifact ID | 0 |
| 2 | 表面风化 | categorical {风化, 无风化} | Weathering status | 0 |

### 5.2 Row and Column Counts

- **Data rows**: 8 (A1-A8)
- **Columns**: 16 (ID + weathering + 14 components)
- **Weathering distribution**: 4 风化, 4 无风化
- **No composition data in Sheet 1**: These 8 artifacts are NOT in Sheet 1 (different ID scheme: letters not numbers).

### 5.3 Missing Value Analysis

| Component | Missing Count | Missing Rate |
|-----------|--------------|--------------|
| Na2O | 6/8 | 75.0% |
| SnO2 | 6/8 | 75.0% |
| SO2 | 5/8 | 62.5% |
| BaO | 4/8 | 50.0% |
| PbO | 3/8 | 37.5% |
| SrO | 3/8 | 37.5% |
| K2O | 2/8 | 25.0% |
| MgO | 2/8 | 25.0% |
| Fe2O3 | 1/8 | 12.5% |
| CuO | 1/8 | 12.5% |
| SiO2 | 0/8 | 0.0% |
| Al2O3 | 0/8 | 0.0% |
| CaO | 0/8 | 0.0% |
| P2O5 | 0/8 | 0.0% |

### 5.4 Composition Sum Check

| ID | Sum | None Count | Status |
|----|-----|------------|--------|
| A1 | 99.48% | 5 | OK |
| A2 | 96.28% | 9 | OK |
| A3 | 98.98% | 3 | OK |
| A4 | 96.00% | 3 | OK |
| A5 | 99.62% | 1 | OK |
| A6 | 99.10% | 6 | OK |
| A7 | 99.64% | 6 | OK |
| A8 | 99.98% | 0 | OK |

**All 8 rows pass** the 85%-105% sum check. Notably, A8 has zero missing values and a near-perfect 99.98% sum.

### 5.5 Tentative Glass Type Classification (by Composition)

| ID | SiO2 | K2O | PbO | BaO | Tentative Type | Confidence |
|----|------|-----|-----|-----|---------------|------------|
| A1 | 78.45 | None | None | None | High-K | MEDIUM (by SiO2 > 70%, low Pb/Ba pattern) |
| A2 | 37.75 | None | 34.30 | None | Pb-Ba | HIGH (high PbO) |
| A3 | 31.95 | 1.36 | 39.58 | 4.69 | Pb-Ba | HIGH |
| A4 | 35.47 | 0.79 | 24.28 | 8.31 | Pb-Ba | HIGH |
| A5 | 64.29 | 0.37 | 12.23 | 2.16 | Pb-Ba | HIGH |
| A6 | 93.17 | 1.35 | None | None | High-K | MEDIUM (very high SiO2, low everything) |
| A7 | 90.83 | 0.98 | None | None | High-K | MEDIUM (very high SiO2, low everything) |
| A8 | 51.12 | 0.23 | 21.24 | 11.34 | Pb-Ba | HIGH |

- **Pb-Ba**: A2, A3, A4, A5, A8 (5 artifacts)
- **High-K**: A1, A6, A7 (3 artifacts, tentative)

### 5.6 Sheet 3 vs Sheets 1+2 Key Difference

Sheet 3 IDs use a different naming scheme (A1-A8 vs 01-58) and have NO decoration type, color, or other metadata except weathering status. The classification task (Q3) must be solved using chemical composition alone.

---

## 6. Variable Availability Per Sub-Question

### Q1: Weathering Type vs Glass Composition Relationship

**Available variables**:
- Surface weathering status (Sheet 1, categorical: 风化/无风化)
- Glass type (Sheet 1, categorical: 高钾/铅钡)
- All 14 chemical components (Sheet 2)

**Analysis-ready rows**:
- High-K: 18 artifacts (6 风化 + 12 无风化)
  - But: IDs 08, 26, 54 have severely weathered points as separate rows
- Pb-Ba: 40 artifacts (28 风化 + 12 无风化)
  - But: IDs 23, 25, 28, 29, 42, 44, 49, 50, 53 have 未风化点 measurements

**Data preparation needed**:
- For artifacts with weathered+unweathered pairs (IDs 49, 50): use both rows
- For artifacts with only "未风化点" in Sheet 2 (23, 25, 28, 29, 42, 44, 53): decide whether to trust the Sheet 2 label or Sheet 1 label
- Remove multi-location duplicates (03部位1/部位2, etc.) or aggregate them
- Severely weathered points (08, 26, 54) may be outliers -- consider separate analysis

### Q2: Glass Subtype Classification

**Available variables**:
- Glass type (已知: 高钾 or 铅钡)
- All 14 chemical components
- Can also leverage: decoration type, color, weathering

**Key discriminants (from literature/prior knowledge)**:
- High-K subtypes: distinguished by K2O/SiO2 ratio, presence of flux oxides
- Pb-Ba subtypes: distinguished by PbO/BaO ratio, SiO2 level

**Data challenges**:
- K2O missing for 28 rows (40.6%), Na2O missing for 50 rows (72.5%)
  - These are key discriminants for High-K subtyping
  - Na2O is mostly missing for High-K samples (below detection limit)
- SnO2 and SO2 are effectively useless
- Consider using ratio-based features: SiO2/K2O, PbO/BaO, etc.
- Missing value imputation or exclusion will be needed

### Q3: Classification of Unknown Glass Artifacts (Sheet 3)

**Available variables**:
- 8 unclassified artifacts (A1-A8)
- 14 chemical components (same as Sheet 2)
- Weathering status (known)
- NO decoration, color, or other metadata

**Classification approach**:
- Train classifier on Sheet 1+2 data (known types), apply to Sheet 3
- Two-step: first classify type (高钾/铅钡), then sub-type
- Need to handle missing values in training AND prediction
- Composition sum quality is good for Sheet 3 (all 8 rows pass 85-105%)

### Q4: Correlation Analysis Between Chemical Components

**Available variables**: All 14 components across 69 rows in Sheet 2

**Key considerations**:
- Missing values will affect correlation calculation
- Compositional data constraint (sum to ~100%) induces spurious negative correlations
- Need to use log-ratio transforms (CLR/ILR) for proper compositional data analysis
- Paired weathered/unweathered points provide natural before/after comparison

---

## 7. Derived Variables That Will Need to Be Created

### 7.1 Data Cleaning Derivatives

| Derived Variable | Formula / Method | Purpose |
|-----------------|------------------|---------|
| base_artifact_id | extract numeric prefix from 文物采样点 | Join key between sheets |
| sampling_point_type | parse suffix (部位/风化点/未风化点) | Distinguish multi-sample types |
| has_composition | bool | Join completeness flag |
| color_missing_flag | bool | Flag artifacts without color |

### 7.2 Chemical Feature Engineering

| Derived Variable | Formula / Method | Purpose |
|-----------------|------------------|---------|
| PbO_BaO_ratio | PbO / BaO | Pb-Ba subtype discrimination |
| SiO2_K2O_ratio | SiO2 / K2O | High-K subtype discrimination |
| total_alkali | Na2O + K2O | Flux content, weathering indicator |
| total_alkaline_earth | CaO + MgO + BaO + SrO | Stabilizer content |
| total_transition | Fe2O3 + CuO | Colorant indicator |
| SiO2_normalized | component / SiO2 | Relative to main glass former |
| CLR_transform | centered log-ratio | Compositional data analysis |
| weathering_ratio | weathered / unweathered for paired samples | Quantify weathering effect |
| colorant_index | (Fe2O3 + CuO) / Al2O3 | Color stability indicator |

### 7.3 Q1-Specific Derivatives

| Derived Variable | Formula | Purpose |
|-----------------|---------|---------|
| weathering_delta_X | X_weathered - X_unweathered (for paired samples) | Direct weathering effect |
| weathering_enrichment_factor | X_weathered / X_unweathered | Relative enrichment/depletion |
| weathering_ratio_alt | component / SiO2 for weathered vs unweathered | Normalized comparison |

### 7.4 Q2-Q3 Classification Features

| Feature Group | Variables | Target |
|--------------|-----------|--------|
| Major oxide ratios | SiO2/K2O, PbO/BaO, CaO/Al2O3 | Type + subtype |
| Trace element presence | Boolean for each trace oxide > 0 | Fine discrimination |
| Pattern-based | PCA/UMAP on oxide profile after imputation | Visualization + classification |
| Color proxy | Fe2O3 (blue-green), CuO (blue-green), Mn (not available) | Color prediction/imputation |

---

## 8. Specific Data Risks

### HIGH Severity

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R1 | **SnO2 and SO2 are 88-90% missing** | Unusable for any analysis. Cannot contribute to Q1-Q4. | Exclude completely or use presence/absence only. |
| R2 | **Na2O is 72.5% missing, K2O is 40.6% missing** | These are KEY discriminants for High-K glass (K2O is defining element). Most High-K samples have Na2O=None (below detection). Naive imputation will produce misleading results. | For High-K: K2O is present (defining element); Na2O is systematically absent. Treat Na2O=None as "<detection_limit" rather than missing-at-random. Use domain-specific imputation (e.g., half detection limit). |
| R3 | **Sheet 1 weathering label conflicts with Sheet 2 point labels** | 7 artifacts (23, 25, 28, 29, 42, 44, 53) are labeled "风化" in Sheet 1 but have "未风化点" measurements in Sheet 2. For Q1, using the wrong weathering label contaminates the analysis. | Manually reconcile: if Sheet 2 explicitly labels a point as 未风化, trust Sheet 2 for that measurement. Note discrepancy in report. The artifact may have BOTH weathered and unweathered regions. |
| R4 | **Compositional data constraint** | Sum-to-100% (or near-100%) creates inherent negative correlation between components. Standard Pearson correlation gives misleading results for Q4. | Use Aitchison geometry: centered log-ratio (CLR) or isometric log-ratio (ILR) transforms before correlation analysis. |
| R5 | **Multi-sample records not independent** | 11 artifacts have 2+ rows (69 rows for 58 artifacts). Treating all rows as independent inflates sample size and breaks i.i.d. assumption. | For classification (Q2): aggregate to one row per artifact (mean) or select primary point. For weathering analysis (Q1): keep pairs as paired observations. For correlation (Q4): use one representative per artifact. |

### MEDIUM Severity

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R6 | **Color missing for 4 Pb-Ba weathered artifacts** | Color-based subtype analysis or colorant analysis loses 4 data points (6.9% of total). | Exclude from color-dependent analysis; acceptable for composition-only models. |
| R7 | **MgO, Fe2O3, SrO each 33-36% missing** | These trace elements provide subtype discrimination signal. Missing values reduce effective feature space. | Evaluate contribution vs missing rate tradeoff. Consider imputation only for <50% missing components. |
| R8 | **Fe2O3 missing for 34.8% of rows** | Fe2O3 is a key colorant (blue-green hues). Missing values hinder color-composition cross-analysis. | Use CuO as proxy where Fe2O3 is missing. CuO only 7.2% missing. |
| R9 | **ID 15 and 17 have composition sums <80%** | Possible data quality issue or measurement limitation. Could be outliers in statistical models. | Flag as low-confidence rows. Test sensitivity with/without these two rows. |
| R10 | **Sheet 3 has no metadata except weathering** | Q3 classification on Sheet 3 cannot use decoration type or color as features. Asymmetric feature space vs training data. | Build classifier using only composition features (which is actually the point of Q3). |
| R11 | **Severely weathered points (08, 26, 54) as outliers** | Composition dramatically altered (SiO2 drops from ~20% to ~4%). Including in training misleads classifiers, excluding loses information about weathering extremes. | Separate analysis: normal points for classification training, severely weathered for Q1 weathering effect quantification. |

### LOW Severity

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R12 | **ID 42 has two 未风化点 measurements** | Minor duplication. Can be averaged since they are similar (51.26% vs 51.33% SiO2). | Average the two rows for the artifact-level representation. |
| R13 | **Zero values exist (e.g., BaO=0, Na2O=0, CaO=0)** | Log transforms fail on zero. CLR requires positive values. | Use multiplicative replacement strategy (replace 0 with small epsilon, e.g., 0.001 or half the minimum non-zero value). ID 15 has BaO=0; ID 16 has BaO=0; ID 17 has BaO=0 and SnO2=0; A8 has Na2O=0, MgO=0, Fe2O3=0, SnO2=0. |
| R14 | **No detection limit metadata** | Cannot distinguish "below detection limit" from "not measured" or "truly zero". Critical for Na2O in High-K samples and trace elements. | Assume None = below detection limit for trace components in the relevant glass type. Document this assumption. |

---

## 9. Summary Statistics

| Metric | Sheet 1 | Sheet 2 | Sheet 3 |
|--------|---------|---------|---------|
| Data rows | 58 | 69 | 8 |
| Columns | 5 | 15 | 16 |
| Total missing cells | 4 | 354 | 39 |
| Missing rate | 1.7% | 34.2% | 30.5% |
| Missing rate (excl. SnO2+SO2) | N/A | 21.5% | 15.6% |
| Composition sum pass rate | N/A | 97.1% (67/69) | 100% (8/8) |
| Multi-sample artifacts | N/A | 11 base IDs | 0 |

### Overall Data Health

- **Sheet 1**: Excellent. Only 4 missing color values.
- **Sheet 2**: Moderate concerns. High missing rates for SnO2, SO2, Na2O; K2O missing in 40% primarily due to Pb-Ba type; 2 rows below 85% composition sum. The multi-sample structure adds complexity.
- **Sheet 3**: Good. All 8 rows pass composition sum checks. Missing pattern mirrors Sheet 2. A8 is the most complete sample in the entire dataset (0 missing values).

### Recommended Data Processing Pipeline

1. **Parse sampling point IDs**: Extract base ID and point type suffix.
2. **Resolve weathering label conflicts**: Cross-reference Sheet 1 and Sheet 2 point labels.
3. **Aggregate multi-sample rows**: Mean for multi-location; keep pairs for weathered/unweathered.
4. **Exclude SnO2 and SO2**: Too sparse for any analysis.
5. **Compositional data transform**: CLR or ILR before correlation/clustering.
6. **Handle zeros**: Multiplicative replacement before log transforms.
7. **Imputation strategy**: Half-detection-limit for below-detection values; MICE or kNN for other missing values (decide per analysis).
8. **Flag low-sum rows**: IDs 15 and 17 for sensitivity analysis.
9. **Severely weathered points**: Separate track for Q1; exclude from Q2 classifier training.

---

*End of Data Audit Report*
