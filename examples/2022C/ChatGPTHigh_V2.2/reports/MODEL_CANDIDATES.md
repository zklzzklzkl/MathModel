# Model Candidates

## Route A: 保守统计规则路线

- route name: 关联统计 + 阈值分类 + 描述性亚类
- applicable problem types: 风化关联分析、类型判别、未知样本分类、成分相关性解释。
- assumptions: 空白成分为 0；成分总和有效样本进入建模；高钾样品 K2O 偏高，铅钡样品 PbO/BaO 偏高。
- required fields: 类型、纹饰、颜色、表面风化、14 个化学成分比例。
- mathematical form:
  - 列联表关联强度用 Cramer's V。
  - 类型分类使用阈值规则：PbO+BaO 与 K2O/SiO2 等关键特征。
  - 亚类依据类型内关键元素高低分组。
- algorithm steps:
  1. 剔除成分总和不在 85%~105% 的训练样本。
  2. 空白成分置 0 后归一化到总和 100。
  3. 建立列联表和均值差异表。
  4. 用经验阈值进行类型和亚类判别。
- validation and sensitivity plan: 留一法检验阈值分类；阈值上下浮动 5% 检查未知样本类别是否变化。
- figure/table plan: 风化列联热图、成分均值差异条形图、未知样本分类表、相关矩阵图。
- figure contract draft:
  - F1: 风化与类型/纹饰/颜色关联热图；支持 Q1 关系判断。
  - F2: 类型-风化分组关键成分均值条形图；支持 Q1 成分规律。
  - F3: PbO+BaO 与 K2O 判别散点图；支持 Q2/Q3 分类规律。
  - F4: 不同类型相关矩阵对比图；支持 Q4。
- advantages: 实现简单、解释直接、不易过拟合。
- risks: 阈值主观，亚类划分说服力不足，风化前预测精度有限。
- reason to adopt or reject: 作为基线采用，不作为最终主路线。

## Route B: 高分稳健可解释路线

- route name: 成分归一化 + 置换关联检验 + 类型内风化校正 + 可解释判别 + 稳定性聚类
- applicable problem types: 全部四个问题。
- assumptions:
  - 空白成分为未检测到，建模置 0。
  - 有效样本成分归一化后保留相对组成信息。
  - 风化效应在同一玻璃类型内具有可估计的平均迁移方向。
  - 小样本下优先采用可解释低方差方法。
- required fields: 表单 1-3 全部字段，尤其类型、表面风化、采样点状态、14 个化学成分比例。
- mathematical form:
  - 有效性：`85 <= sum(x_j) <= 105`。
  - 归一化：`z_j = 100 x_j / sum_k x_k`。
  - 关联强度：`V = sqrt(chi2 / (n * min(r-1,c-1)))`，p 值用置换检验。
  - 风化校正：在类型 t 内估计 `delta_t = mean(z | t, unweathered) - mean(z | t, weathered)`，风化点预测为 `clip(z + delta_t)` 后再归一化；若样本标记为“未风化点”则直接作为风化前近似。
  - 类型判别：对关键特征向量 `[SiO2, K2O, PbO, BaO, P2O5, Al2O3, CaO]` 使用标准化最近质心/对角协方差评分，并报告留一法准确率。
  - 亚类划分：在每个类型内选择贡献最大的关键成分，使用 k=2 的确定性 k-means，并用轮廓系数和扰动一致率评估。
  - 相关关系：分别对高钾、铅钡的归一化成分计算 Pearson/Spearman 相关矩阵，比较相关差绝对值。
- algorithm steps:
  1. 解析采样点基础编号并合并表单 1。
  2. 生成有效样本、归一化成分、采样状态标签。
  3. 完成 Q1 分类变量关联、分组均值、风化校正。
  4. 完成 Q2 类型分类、留一验证、亚类聚类、聚类稳定性。
  5. 完成 Q3 未知样本判别、概率/距离分数、扰动敏感性。
  6. 完成 Q4 类别内相关矩阵、相关差异和代表性元素对解释。
- validation and sensitivity plan:
  - 类型判别：留一交叉验证。
  - 未知分类：成分 ±5% 相对扰动、缺失低含量成分置 0/小值两种情形。
  - 亚类：初始化和扰动一致率。
  - 风化校正：报告类型内风化/未风化均值差异，不做超出样本范围的强预测。
- figure/table plan:
  - 列联关系热图。
  - 关键成分分组均值图。
  - 类型判别散点和未知样本位置图。
  - 亚类雷达/条形图。
  - 敏感性稳定率图。
  - 类别相关矩阵差异图。
- figure contract draft:
  - F1: Q1 风化关联强度热图；source: 表单 1；stats: Cramer's V + permutation p。
  - F2: Q1 类型-风化关键成分均值条形图；source: 表单 1+2；stats: group mean and delta。
  - F3: Q2/Q3 K2O vs PbO+BaO 判别散点；source: valid normalized samples + 表单 3；stats: centroid distance and predicted label。
  - F4: Q2 亚类中心组成对比图；source: clustering output；stats: cluster centers and silhouette。
  - F5: Q3 敏感性稳定率图；source: perturbation runs；stats: stable classification ratio。
  - F6: Q4 高钾/铅钡相关矩阵差异图；source: valid normalized samples；stats: Pearson correlation and delta.
- advantages: 兼顾可解释性、有效性筛选、验证与敏感性，适合小样本竞赛论文。
- risks: 风化校正为平均效应模型，不能代表精细化学动力学；聚类结果受样本量限制。
- reason to adopt or reject: 采纳为最终路线，并保留 Route A 的阈值规则作为解释性基线。

