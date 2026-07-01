---
library: cumcm_problems
year: 2026
contest: CUMCM
problem_id: cumcm-routing-demo
tags: [cumcm, problem-routing, hidden-score]
license: project-authored
---

# 国赛题型识别样例

适用场景：读取国赛题面后，先判断它是否是评价、预测、优化、机理、空间、网络、仿真等混合题。

隐含评分点：

- 子问题之间是否有递进关系，而不是每问独立套模型。
- 附件字段是否足以支持模型，不能把题面背景当成可计算数据。
- 结论是否逐问回应题目要求，有没有提交可执行策略或可解释指标。

推荐用法：在 Phase 0 形成 `PROBLEM_BRIEF.md` 时记录候选题型和不确定性，交给 Phase 1 路由器进一步判断。

风险提示：不要只根据题目关键词决定模型；必须结合附件字段、问题动词和提交要求。
