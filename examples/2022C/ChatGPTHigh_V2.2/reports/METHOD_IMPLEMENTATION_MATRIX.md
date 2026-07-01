# Method Implementation Matrix

| Problem | Approved Method | Implemented In Code/Results | Paper Wording | Status | Action |
| --- | --- | --- | --- | --- | --- |
| Q1 | 关联统计、类型内风化校正 | `q1_association.csv`, `q1_group_component_means.csv`, `q1_weathering_prediction.csv`, F1, F2 | 表述为统计关联和平均校正 | implemented | none |
| Q2 | 最近质心判别、类型内 k=2 聚类 | `q2_loocv_validation.csv`, `q2_subclass_assignments.csv`, `q2_subclass_centers.csv`, F3, F4 | 表述为可解释判别和稳定性聚类 | implemented | none |
| Q3 | 未知样本判别、±5% 扰动敏感性 | `q3_unknown_predictions.csv`, `q3_sensitivity.csv`, F3, F5 | A5 降低置信表述 | implemented | none |
| Q4 | 类型内相关矩阵、类别间相关差异 | `q4_corr_高钾.csv`, `q4_corr_铅钡.csv`, `q4_top_correlation_differences.csv`, F6 | 表述为组成关联，不表述为因果 | implemented | none |
