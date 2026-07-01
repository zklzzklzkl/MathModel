# Modeling Decision

**Date**: 2026-06-29
**Decision**: **采纳 Route B（高分增强路线）**
**确认方式**: 人工确认

## Final Route

| 子问题 | 主要方法 | 对比基线 |
|--------|----------|----------|
| Q1a | 多重对应分析(MCA) + Logistic回归 | 卡方检验 |
| Q1b | MANOVA + Bootstrap CI + Hedges' g | 分组统计描述 |
| Q1c | Bayesian层次模型（先预测区间） | 配对差值比例模型 |
| Q2a | 组分比值特征 + 正则化Logistic回归 | LDA |
| Q2b | 层次聚类(Ward) + Gap统计量 + 轮廓系数 | K-means |
| Q3 | 4分类器集成 + 风化矫正 ±5%敏感性 | 单一马氏距离 |
| Q4 | Graphical Lasso + 偏相关网络 + Fisher Z差异检验 | Pearson矩阵 |

## Revised Per AI Review

执行以下修正（来自 MODEL_REVIEW_AI.md 和 devil's-advocate）：

1. **Q1c**: 先验Beta(2,2), MCMC收敛诊断R̂<1.1, 报告预测区间而非点估计
2. **Q2b**: 多重聚类指标(DBI, CHI, Silhouette), 亚类与考古学含义讨论
3. **Q3**: 风化样品(Q2,A5,A6,A7)先用Q1c模型矫正再分类，对比矫正前后
4. **Q4**: 选择6-8个主要组分(排除缺失>50%的Na2O/SnO2/SO2)，Pearson矩阵作稳健基准
5. **全部**: Route A简化版本保留为论文中对比引用

## Excluded Components
- SnO2 (89.9% missing)
- SO2 (88.4% missing)
- Na2O (72.5% missing) — 建模时排除，但Q1b分组统计中作为辅助讨论
- **最终建模组分**: SiO2, K2O, CaO, MgO, Al2O3, Fe2O3, CuO, PbO, BaO, P2O5, SrO (11种)

## Normalization Protocol
所有有效数据（Σ∈[85%,105%]）在进行任何分析前，先归一化到总和=100%：
X'_j = X_j / (Σ_i X_i) × 100%

## Approval
- model-reviewer: CONDITIONAL_PASS ✓
- devil's-advocate: CONDITIONAL_PASS ✓
- human: Route B confirmed ✓
