# Data Audit

> Synthesized from data-auditor subagent findings

## File Inventory

| File | Format | Sheets/Rows | Columns | Status |
|------|--------|-------------|---------|--------|
| 附件(1).xlsx | Excel | 3 sheets | — | OK, readable |
| — 表单1 | — | 58 rows | 5 | 4 missing color values |
| — 表单2 | — | 69 rows | 15 (1 ID + 14 compos.) | 34.2% missing (excl. SnO2+SO2: 21.5%) |
| — 表单3 | — | 8 rows | 16 (ID + 风化 + 14 compos.) | 30.5% missing (excl. SnO2+SO2: 15.6%) |

## Table And Field Summary

### 表单1: 基本信息 (58 artifacts)

| Field | Type | Values | Missing |
|-------|------|--------|---------|
| 文物编号 | string | 01-58 | 0 |
| 纹饰 | cat {A,B,C} | A:22, B:6, C:30 | 0 |
| 类型 | cat {高钾,铅钡} | 高钾:18, 铅钡:40 | 0 |
| 颜色 | cat (8 values) | 浅蓝:20, 蓝绿:15, 深绿:7, 紫:4, 浅绿:3, 黑:2, 深蓝:2, 绿:1 | 4 (19,40,48,58) |
| 表面风化 | cat {风化,无风化} | 风化:34, 无风化:24 | 0 |

### 表单2: 已分类文物化学成分 (69 sampling points)

14 chemical oxides (wt%): SiO2, Na2O, K2O, CaO, MgO, Al2O3, Fe2O3, CuO, PbO, BaO, P2O5, SrO, SnO2, SO2

Missing rates: SnO2 89.9% | SO2 88.4% | Na2O 72.5% | K2O 40.6% | MgO 36.2% | Fe2O3 34.8% | SrO 33.3%

### 表单3: 未分类文物化学成分 (8 artifacts: A1-A8)

4 风化 (A2,A5,A6,A7), 4 无风化 (A1,A3,A4,A8)。含风化状态列，无纹饰/颜色/类型信息。

## Missing / Abnormal / Duplicate Data

### CRITICAL: SnO2 & SO2 (88-90% missing)
→ 排除出所有分析，仅保留存在/缺失作为定性辅助

### HIGH: Na2O (72.5%) & K2O (40.6%) 缺失
- Na2O在高钾玻璃中系统性缺失（低于检出限），非随机缺失
- K2O在铅钡玻璃中常缺失（非定义元素）
→ 依赖领域知识的填补策略，不可简单零填充

### 成分和异常 (2 of 69)
- ID 15: sum=79.47% (CaO, MgO, Al2O3, K2O missing)
- ID 17: sum=71.89% (CaO, MgO, Al2O3, K2O missing)
→ 均在High-K中CaO缺失导致，标记为低置信度

### 风化标签冲突 (7 artifacts, HIGH risk)
23, 25, 28, 29, 42, 44, 53: 表单1标"风化"但表单2有"未风化点"数据
→ 优先信任表单2采样点标注

### 多采样点 (11 base IDs)
- 多部位: 03, 06, 30, 43, 51
- 风化/未风化配对: 49, 50
- 正常/严重风化: 08, 26, 54
- 两个未风化点: 42

### 零值 (A8: Na2O=0, MgO=0, Fe2O3=0, SnO2=0)
→ log变换前用乘性替换（半最小非零值）

## Usable Variables By Question

| Component | Q1 | Q2 | Q3 | Q4 | Notes |
|-----------|-----|-----|-----|-----|-------|
| SiO2 | ✓ | ✓ | ✓ | ✓ | Always available |
| Na2O | low | limited | limited | limited | Systematically missing in High-K |
| K2O | ✓ | key | ✓ | ✓ | Key High-K discriminant |
| CaO | ✓ | ✓ | ✓ | ✓ | Stabilizer, 11.6% missing |
| MgO | limited | limited | limited | limited | 36.2% missing |
| Al2O3 | ✓ | ✓ | ✓ | ✓ | Near-complete, immobile → reference |
| Fe2O3 | limited | limited | ✓ | limited | 34.8% missing |
| CuO | ✓ | ✓ | ✓ | ✓ | 7.2% missing |
| PbO | ✓ | key | ✓ | ✓ | Key Pb-Ba discriminant |
| BaO | ✓ | key | ✓ | ✓ | Key Pb-Ba discriminant |
| P2O5 | limited | ✓ | ✓ | ✓ | 14.5% missing |
| SrO | limited | limited | limited | limited | 33.3% missing |
| SnO2 | ✗ | ✗ | ✗ | ✗ | 89.9% missing → EXCLUDE |
| SO2 | ✗ | ✗ | ✗ | ✗ | 88.4% missing → EXCLUDE |

Available inputs per question:
- Q1: 纹饰, 颜色, 类型, 风化, 12 usable chemicals
- Q2: 类型 (已知), 12 usable chemicals, 可选纹饰/颜色/风化
- Q3: 风化, 12 usable chemicals → 预测类型+亚类
- Q4: Q1校正后12 chemicals, Q2/Q3标签

## Derived Variables Needed

| Variable | Formula | Use |
|----------|---------|-----|
| PbO/BaO ratio | PbO / BaO | Pb-Ba sub-type |
| K2O/SiO2 ratio | K2O / SiO2 | High-K sub-type |
| total_alkali | Na2O + K2O | Flux proxy |
| total_colorant | Fe2O3 + CuO | Color proxy |
| CLR transform | ln(x/g_mean) | All compositional analysis |
| weathering_ratio | weathered/unweathered (paired) | Q1 calibration |
| base_artifact_id | extract numeric prefix | Join key |

## Blocking Risks

| Risk | Severity | Mitigation | Block? |
|------|----------|------------|--------|
| Compositional data constraint | HIGH | CLR/ILR transform before correlation/clustering/PCA | Must handle |
| Weathering label conflicts | HIGH | Trust Sheet 2 point labels over Sheet 1 | Must resolve |
| Na2O/K2O missing-not-random | HIGH | Domain-specific imputation (half-DL) | Must justify |
| Multi-sample non-independence | MEDIUM | Aggregate to artifact level for Q2/Q4; keep pairs for Q1 | Handle |
| SnO2/SO2 unusable | MEDIUM | Exclude | Acceptable |
| Zero values for log transform | MEDIUM | Multiplicative replacement | Handle |
| Low-sum rows ID 15,17 | LOW | Sensitivity test with/without | Flag |
| Color missing for 4 artifacts | LOW | Exclude from color analysis | Acceptable |
