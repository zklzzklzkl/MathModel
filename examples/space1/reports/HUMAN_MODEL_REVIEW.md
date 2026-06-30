# Human Model Review Gate

**状态**: 等待人工确认

---

## 评审摘要

两条建模路线已生成并经过AI评审（model-reviewer + devil's-advocate）。

### 路线对比

| | Route A (保守) | Route B (高分, 推荐) |
|---|---|---|
| Q1a | 卡方+对应分析 | MCA + logistic回归 |
| Q1b | 分组统计+t检验 | MANOVA + Bootstrap CI |
| Q1c | 配对差值比例 | Bayesian层次模型 (含A作为对比) |
| Q2a | 阈值规则+LDA | 比值特征+正则化Logistic |
| Q2b | K-means+轮廓系数 | 层次聚类+Gap+多重指标 |
| Q3 | 马氏距离 | 多分类器集成+风化矫正 |
| Q4 | Pearson+Fisher Z | Graphical Lasso+差异网络 |

### AI评审结论: CONDITIONAL_PASS (两条路线均通过, 带修正项)

**关键修正项**:
1. Q1c: 明确预测不确定性，使用预测区间
2. Q3: **必须**加入风化样品的成分矫正
3. Q4: 高钾组(n=18)降维处理
4. 所有方法保留Route A简单版本作为对比基准

---

## 需要您确认的事项

请选择以下一项：

- [ ] **采纳Route B（推荐）** — 高分增强路线，Route A作为对比基线
- [ ] **采纳Route A** — 保守路线，降低实现风险
- [ ] **混合路线** — 指定每问使用哪条路线（请说明）

确认后，请回复选择，我将更新 MODELING_DECISION.md 并进入实验阶段。
