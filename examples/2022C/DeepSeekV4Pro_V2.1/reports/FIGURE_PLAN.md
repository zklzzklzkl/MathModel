# Figure Plan

## Q1a: 风化关系
| # | 图名 | 类型 | 输出文件 | 论文引用 |
|---|------|------|----------|----------|
| F1.1 | 风化×类型堆叠柱状图 | 柱状图 | figures/q1a_weather_type_bar.pdf | 图1 |
| F1.2 | Logistic回归OR森林图 | 森林图 | figures/q1a_or_forest.pdf | 图2 |
| F1.3 | MCA双标图 | 散点图 | figures/q1a_mca_biplot.pdf | 图3 |

## Q1b: 成分统计规律
| # | 图名 | 类型 | 输出文件 | 论文引用 |
|---|------|------|----------|----------|
| F2.1 | 11组分×4组箱线图 | 箱线图 | figures/q1b_boxplot_matrix.pdf | 图4 |
| F2.2 | 风化效应量排序(Hedges' g) | 条形图+Bootstrap CI | figures/q1b_effect_size.pdf | 图5 |
| F2.3 | 四组均值雷达图 | 雷达图 | figures/q1b_radar.pdf | 图6 |

## Q1c: 风化预测
| # | 图名 | 类型 | 输出文件 | 论文引用 |
|---|------|------|----------|----------|
| F3.1 | 预测vs实测散点图 | 散点+对角线 | figures/q1c_pred_vs_actual.pdf | 图7 |
| F3.2 | 各组分变化率后验分布 | 小提琴图 | figures/q1c_posterior.pdf | 图8 |
| F3.3 | 预测区间误差棒 | 误差棒图 | figures/q1c_pred_intervals.pdf | 图9 |

## Q2a: 分类规律
| # | 图名 | 类型 | 输出文件 | 论文引用 |
|---|------|------|----------|----------|
| F4.1 | 关键比值散点矩阵 | 散点矩阵 | figures/q2a_ratio_scatter.pdf | 图10 |
| F4.2 | PCA投影+决策边界 | 散点+轮廓 | figures/q2a_decision_boundary.pdf | 图11 |
| F4.3 | ROC曲线 | ROC | figures/q2a_roc.pdf | 图12 |

## Q2b: 亚类划分
| # | 图名 | 类型 | 输出文件 | 论文引用 |
|---|------|------|----------|----------|
| F5.1 | 高钾谱系图+Gap曲线 | 树状图 | figures/q2b_dendro_gaok.pdf | 图13 |
| F5.2 | 铅钡谱系图+Gap曲线 | 树状图 | figures/q2b_dendro_qianbei.pdf | 图14 |
| F5.3 | 高钾PCA+亚类着色 | 散点图 | figures/q2b_pca_gaok.pdf | 图15 |
| F5.4 | 铅钡PCA+亚类着色 | 散点图 | figures/q2b_pca_qianbei.pdf | 图16 |
| F5.5 | 亚类均值雷达图 | 雷达图 | figures/q2b_radar.pdf | 图17 |

## Q3: 未知分类
| # | 图名 | 类型 | 输出文件 | 论文引用 |
|---|------|------|----------|----------|
| F6.1 | 多分类器结果对比 | 分组条形 | figures/q3_classifier_compare.pdf | 图18 |
| F6.2 | 马氏距离条形图 | 条形图 | figures/q3_mahalanobis.pdf | 图19 |
| F6.3 | 敏感性扰动热图 | 热图 | figures/q3_sensitivity_heat.pdf | 图20 |

## Q4: 关联分析
| # | 图名 | 类型 | 输出文件 | 论文引用 |
|---|------|------|----------|----------|
| F7.1 | 高钾相关热图 | 热图 | figures/q4_heat_gaok.pdf | 图21 |
| F7.2 | 铅钡相关热图 | 热图 | figures/q4_heat_qianbei.pdf | 图22 |
| F7.3 | Graphical Lasso网络对比 | 网络图 | figures/q4_network_compare.pdf | 图23 |
| F7.4 | 差异网络图 | 网络图 | figures/q4_diff_network.pdf | 图24 |

## 表格计划

| # | 表名 | 内容 | 论文引用 |
|---|------|------|----------|
| T1 | 表单1基本统计 | 类型/风化/纹饰/颜色频率 | 表1 |
| T2 | Q1a logistic回归表 | β, SE, OR, 95%CI, p | 表2 |
| T3 | Q1b 四组均值±SD表 | 11组分×4组 | 表3 |
| T4 | Q1b 显著性检验表 | 组间比较p值 | 表4 |
| T5 | Q1c 风化变化率 | 11组分平均r±SE | 表5 |
| T6 | Q1c 预测结果 | 预测值+95%HDI | 表6 |
| T7 | Q2a 分类性能对比 | 各分类器CV准确率/AUC | 表7 |
| T8 | Q2b 亚类统计 | 各亚类均值±SD | 表8 |
| T9 | Q3 未知样品分类结果 | 8样品×完整结果 | 表9 |
| T10 | Q3 敏感性分析 | 扰动比例vs分类一致性 | 表10 |
| T11 | Q4 显著差异组分对 | Fisher Z + FDR | 表11 |

**共计: 24张图 + 11张表**
