---
library: model_methods
year: 2026
contest: generic
problem_id: prediction-optimization-demo
tags: [prediction, optimization, hybrid, baseline, validation]
license: project-authored
---

# 预测 + 优化混合题模型卡样例

适用题型：先预测需求、风险、流量、价格或性能，再根据预测结果制定资源配置、调度、路线或策略。

基准模型：历史均值、线性回归、朴素时间序列、贪心分配。

首选模型：可解释预测模型 + 线性/整数规划；树模型或时间序列模型 + 鲁棒优化；情景预测 + 多目标优化。

备选模型：仿真优化、动态规划、启发式算法。

不推荐模型：没有验证误差就把预测值直接用于优化；只报告最优解不报告约束满足；用黑箱预测但无法解释策略来源。

验证方法：预测误差、残差诊断、优化可行性、情景敏感性、与贪心/规则基准方案比较。

推荐图表：真实值-预测值、误差分布、方案对比、约束利用率、关键参数敏感性曲线。
