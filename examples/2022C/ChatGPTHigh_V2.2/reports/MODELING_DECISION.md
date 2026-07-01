# Modeling Decision

## Final Accepted Route

采用 Route B：成分归一化 + 置换关联检验 + 类型内风化校正 + 可解释判别 + 稳定性聚类。

## Problem-Level Methods

| Problem | Objective | Method | Validation | Main Outputs |
| --- | --- | --- | --- | --- |
| Q1 | 分析风化与类型/纹饰/颜色关系，预测风化前成分 | 列联表、Cramer's V、置换检验、类型内均值差异校正 | 置换 p 值、分组均值差异、校正后总和检查 | 关联强度表、成分规律表、风化前预测表 |
| Q2 | 建立类型分类规律并划分亚类 | 标准化最近质心/对角协方差评分，类型内 k=2 聚类 | 留一交叉验证、轮廓系数、扰动一致率 | 分类规则、亚类标签、亚类中心 |
| Q3 | 鉴别未知样本类型 | 使用 Q2 判别器，结合风化状态做敏感性扰动 | ±5% 成分扰动稳定率、分类分数差距 | A1-A8 类别预测与置信说明 |
| Q4 | 比较类别内成分关联关系 | Pearson/Spearman 相关矩阵、相关差异排序 | 只解释稳定高差异元素对，提示闭合效应 | 类别相关矩阵、差异元素对 |

## Core Variables

- 基础成分：14 个氧化物百分比。
- 关键判别成分：SiO2、K2O、PbO、BaO、P2O5、Al2O3、CaO。
- 分类变量：类型、纹饰、颜色、表面风化。
- 派生变量：成分总和、有效性、归一化成分、采样点基础编号、采样点局部状态。

## Implementation Requirements

- 所有核心结果由 `code/analyze_glass.py` 生成。
- 输出 CSV 表格、PNG 图表、`results/RESULTS_MANIFEST.json`。
- 图表需使用中文字体，且在 `reports/FIGURE_AUDIT.md` 通过可读性检查。
- 论文中所有关键数字必须追踪到 manifest、结果表或图表。

