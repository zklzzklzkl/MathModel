# Anti-Template Review

> 用于 `mm-model-strategy`、`mm-contest-review` 和必要时的 `mm-final-verify`。  
> 目标是识别“模型看起来高级，但没有回答题目、数据不支撑、验证不充分”的情况。

## Core Questions

每个候选核心模型都必须回答：

1. 为什么不用更简单的 baseline？
2. 当前数据是否支撑这个模型的参数量、假设和验证方式？
3. 模型输出是否直接回答原问题？
4. 如果模型失败，是否有可执行的备选路线？
5. 论文中是否会诚实呈现模型边界，而不是夸大？

## High-Risk Template Signals

### AHP

风险信号：

- 没有专家来源或判断矩阵来源。
- 没有一致性检验 `CR < 0.1`。
- 指标数量很多，但权重完全主观。

最低要求：

- 说明专家/题面/文献/人工判断来源。
- 报告一致性检验。
- 做权重敏感性。

### TOPSIS

风险信号：

- 指标正负向没有说明。
- 标准化方式没有说明。
- 只给最终排序，没有稳定性。

最低要求：

- 指标方向、标准化、权重来源完整。
- 与等权 baseline 对比。
- 排名稳定性或指标删除实验。

### Neural Network / Deep Learning

风险信号：

- 样本量小。
- 没有训练/验证划分。
- 任务需要解释，但模型完全黑箱。
- 没有调参、误差和泛化说明。

最低要求：

- 明确数据量足够。
- 有验证集或时间滚动验证。
- 有可解释性或特征贡献说明。
- 与简单模型比较。

### Genetic Algorithm / Metaheuristic

风险信号：

- 没有决策变量、编码、适应度函数。
- 可以精确求解，却直接用遗传算法。
- 没有收敛曲线或多次运行稳定性。

最低要求：

- 写清变量编码、目标函数、约束处理。
- 解释为什么精确求解不可行。
- 给出 baseline、收敛曲线、多次运行结果。

### PCA / Factor Analysis

风险信号：

- 样本量过小。
- 不报告方差解释率。
- 因子解释牵强。

最低要求：

- 样本量和变量数量合理。
- 报告方差解释率、载荷和可解释性。
- 与原始指标意义保持一致。

### Clustering

风险信号：

- 聚类数任意。
- 聚完类不解释类别含义。
- 没有稳定性或评价指标。

最低要求：

- 说明 K 的选择。
- 报告 silhouette、CH/DB 指标或稳定性。
- 给每类画像和题目决策含义。

## Review Output

在 `reports/MODEL_REVIEW_AI.md` 或 `reports/PAPER_SCORECARD.md` 写：

```markdown
## Anti-Template Review

| Model | Template Risk | Evidence | Required Justification | Verdict |
| --- | --- | --- | --- | --- |
```

Verdict:

- `clear`: 模型与题目、数据、验证匹配。
- `needs_justification`: 可以保留，但必须补充说明或验证。
- `downgrade_to_baseline`: 高级模型不成立，应改成更简单可靠路线。
- `reject`: 明显套模板或不可实现。

## Severity Mapping

- `reject` 且用于核心结论：`BLOCKER`。
- `downgrade_to_baseline` 但论文仍声称高级模型：`HIGH`。
- `needs_justification` 且验证不足：`MEDIUM` 或 `HIGH`，按核心程度决定。
- `clear` 不产生 revision action。

## Writing Rule

如果最终采用的是更简单的 baseline，不要把论文写成“用了高级模型”。  
诚实、可验证、能回答问题的简单模型，通常比不成立的复杂模型更接近获奖。
