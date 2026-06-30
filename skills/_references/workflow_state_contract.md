# MathModelAgent 持久化上下文契约

本契约用于解决数学建模竞赛长上下文任务中的信息丢失问题。后续 skill 不应依赖聊天历史记忆，而应依赖本文件规定的项目档案。每个阶段开始时读取上游档案，结束时更新自己的档案。

## 核心原则

1. 题面、数据、模型、实验、图表、论文结论必须文件化。
2. 后续阶段不得从“记忆”中取关键数值，必须从结果文件、图表源数据或 manifest 中取数。
3. 每个关键结论必须能追溯到题目要求、模型假设、代码结果或图表证据。
4. 阶段门禁不通过时，不进入下一阶段；若必须继续，必须在对应报告中记录风险和用户确认。
5. 新会话、上下文压缩或不同 AI 工具接手后，读取这些文件应能恢复完整项目状态。

## 标准档案

| 文件 | 负责阶段 | 用途 |
| --- | --- | --- |
| `PROBLEM_BRIEF.md` | `0problem-triage` / `2analysis-modeling` | 题面重述、子问题拆解、输入输出、目标、约束、评价指标 |
| `DATA_AUDIT.md` | `0problem-triage` / `2analysis-modeling` / `3coding-visual` | 附件字段、单位、缺失、异常、主键、数据风险 |
| `WORKFLOW_STATE.md` | 全阶段 | 当前阶段、已完成产物、阻塞点、人工确认记录、下一步 |
| `reports/TRIAGE_REPORT.md` | `0problem-triage` | 赛题可行性、路线预审、换题或继续条件 |
| `reports/ANALYSIS_MODELING_REPORT.md` | `2analysis-modeling` | 最终建模方案、公式、约束、算法、代码任务清单 |
| `reports/MODELING_DECISIONS.md` | `2analysis-modeling` | 候选模型比较、采用/放弃理由、关键假设和风险 |
| `reports/ANALYSIS_GATE.md` | `2analysis-modeling` | 建模阶段门禁结论 |
| `reports/EXPERIMENT_LOG.md` | `3coding-visual` | 每次实验的脚本、参数、随机种子、输出和状态 |
| `results/RESULTS_MANIFEST.json` | `3coding-visual` | 所有论文可引用关键数值、图表、表格的唯一来源 |
| `reports/RESULTS_REPORT.md` | `3coding-visual` | 代码结果说明、约束检查、敏感性分析和复现方式 |
| `reports/FIGURE_PLAN.md` | `3coding-visual` / `4drawio` / `5writing` | 每张图的用途、来源、放置章节和 caption 建议 |
| `reports/DRAWIO_REPORT.md` | `4drawio` | 非数据图生成记录和嵌入建议 |
| `reports/CLAIM_TRACE.md` | `5writing` | 论文核心结论到证据来源的映射 |
| `reports/VERIFY_REPORT.md` | `6verity` | 最终验收结论和问题清单 |

## 阶段门禁

### Gate 0: 赛题预审

通过条件：

- 子问题数量明确或风险已记录。
- 附件清点完成。
- 数据风险和时间预算已写入。
- 结论为 `GO` 或 `CONDITIONAL_GO`。

### Gate 1: 建模门禁

通过条件：

- 每个子问题都有目标函数或评价指标。
- 关键变量、约束、假设、求解方法明确。
- 至少有基准路线和主路线，必要时有备用路线。
- 数据字段含义和单位风险已经在 `DATA_AUDIT.md` 中记录。

### Gate 2: 代码结果门禁

通过条件：

- 每个子问题都有可复现脚本或 notebook 入口。
- Python 脚本至少通过语法编译检查；关键脚本能在当前数据上运行。
- 关键随机过程有随机种子或稳定性说明。
- 关键结果进入 `RESULTS_MANIFEST.json`。
- 每张论文候选图都有来源和用途记录。

### Gate 3: 写作门禁

通过条件：

- 论文中的关键数值全部来自 `RESULTS_MANIFEST.json` 或明确结果文件。
- 每个核心结论写入 `CLAIM_TRACE.md`。
- 图表被放在与论证匹配的章节，且正文有解释。

### Gate 4: 最终验收

通过条件：

- 章节结构、图表、引用、数值一致性、模板、编译和 PDF 检查通过。
- 没有占位符、内部工作流泄漏、无法追溯的关键结论。
- 若某项无法执行，必须记录原因和残余风险。

## `WORKFLOW_STATE.md` 建议结构

```markdown
# 工作流状态

## 当前阶段
<triage / analysis / coding / drawing / writing / verification>

## 已完成产物
- ...

## 阻塞与风险
- ...

## 关键决策
- ...

## 下一步
- ...
```

## `RESULTS_MANIFEST.json` 建议结构

```json
{
  "problem_count": 3,
  "metrics": [
    {
      "id": "q1_objective_value",
      "problem": "ques1",
      "value": 123.45,
      "unit": "万元",
      "source_file": "results/q1_summary.csv",
      "script": "code/problem1.py",
      "description": "问题一最优目标函数值"
    }
  ],
  "figures": [
    {
      "id": "fig_q1_convergence",
      "path": "figures/fig_q1_convergence.pdf",
      "problem": "ques1",
      "source_data": "results/q1_iterations.csv",
      "script": "code/problem1.py",
      "intended_section": "问题一模型求解",
      "caption": "问题一优化算法收敛过程"
    }
  ]
}
```

## `CLAIM_TRACE.md` 建议结构

```markdown
# 结论证据追踪

| 结论编号 | 论文位置 | 结论 | 证据来源 | 是否通过 |
| --- | --- | --- | --- | --- |
| C1 | 摘要 | 问题一最优目标值为... | results/RESULTS_MANIFEST.json#q1_objective_value | PASS |
```
