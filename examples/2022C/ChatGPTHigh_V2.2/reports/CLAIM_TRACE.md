# Claim Trace

| Claim | Paper Section | Evidence Type | Evidence ID/File | Strength | Paper Wording Check |
| --- | --- | --- | --- | --- | --- |
| 表面风化与玻璃类型存在稳定关联 | 问题一 | table/figure | `t_q1_association`, F1 | strong | 使用 Cramer's V 和置换 p 支撑 |
| 高钾与铅钡可由关键成分判别 | 问题二 | metric/figure | `m_q2_loocv_accuracy`, F3 | strong | 报告留一准确率 |
| 高钾和铅钡各可划分为两个亚类 | 问题二 | table/figure | `t_q2_subclass_centers`, F4 | acceptable | 同时报告轮廓系数，未夸大 |
| A1/A5/A6/A7 为高钾，A2/A3/A4/A8 为铅钡 | 问题三 | table/figure | `t_q3_unknown_predictions`, F5 | acceptable | A5 标注相对边界样本 |
| 两类玻璃相关结构存在差异 | 问题四 | table/figure | `t_q4_corr_diff`, F6 | acceptable | 明确为组成关联，非因果 |
