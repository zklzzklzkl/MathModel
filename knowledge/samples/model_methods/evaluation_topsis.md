---
library: model_methods
year: 2026
contest: generic
problem_id: evaluation-demo
tags: [evaluation, topsis, entropy-weight, sensitivity]
license: project-authored
---

# 综合评价类模型卡样例

适用题型：综合评价、排序、方案选择、风险评分、指标体系构建。

基准模型：等权加权评分、标准化后线性加权。

首选模型：熵权 TOPSIS、组合赋权 TOPSIS、PCA/factor analysis + ranking。

不推荐模型：没有指标方向说明时直接套 TOPSIS；样本极少但强行 PCA；没有一致性检验的 AHP。

验证方法：排名稳定性、权重敏感性、指标删除实验、与基准模型的 Spearman/Kendall 排名相关。

推荐图表：指标权重条形图、TOPSIS 贴近度排名图、敏感性热力图、方案雷达图。

论文表达重点：说明指标正负向、标准化方式、权重来源和排名稳定性，避免只给最终排名。
