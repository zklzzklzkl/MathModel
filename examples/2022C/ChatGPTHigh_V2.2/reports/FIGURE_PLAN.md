# Figure Plan

| Figure ID | Core Conclusion | Archetype | Backend | Source Data | Statistics Needed | Intended Section | Supported Claim |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | 表面风化与玻璃类型关系最强，纹饰次之，颜色受缺失影响较大 | heatmap | Python Pillow | 表单1 | Cramer's V, permutation p | 问题1 | 风化与类型/纹饰/颜色存在不同强度关联 |
| F2 | 高钾和铅钡玻璃在风化后关键成分变化方向不同 | grouped bar | Python Pillow | 表单1+表单2 | group means, deltas | 问题1 | 类型内风化校正具有统计依据 |
| F3 | K2O 与 PbO+BaO 构成清晰主类别判别平面 | scatter | Python Pillow | 表单2+表单3 | centroid distance, LOOCV | 问题2/3 | 未知样本可由关键成分判别所属类型 |
| F4 | 每个主类别可分为两个成分结构不同的亚类 | grouped bar | Python Pillow | 聚类结果 | cluster centers, silhouette | 问题2 | 亚类划分具有成分解释 |
| F5 | 多数未知样本在扰动下分类稳定 | bar | Python Pillow | 敏感性结果 | stability ratio | 问题3 | 未知分类结论具有稳健性差异 |
| F6 | 高钾和铅钡类别的成分关联结构存在显著差异 | matrix heatmap | Python Pillow | 表单2 | Pearson r and absolute difference | 问题4 | 类别间关联关系不同 |
| F7 | 建模流程由数据清洗、风化校正、判别、聚类、敏感性、关联分析组成 | flow diagram | Python Pillow | 方法报告 | process nodes | 模型建立 | 论文具备完整技术路线 |

