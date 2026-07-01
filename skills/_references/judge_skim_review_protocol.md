# Judge Skim Review Protocol

> 用于 `mm-contest-review`，位置在论文初稿之后、最终验收之前。  
> 它模拟评委 5 分钟快速浏览，不替代完整评分，只负责发现“第一眼就丢分”的问题。

## When To Run

只在以下文件基本存在后运行：

- `paper/` 中已有可读论文草稿。
- `reports/CLAIM_TRACE.md` 已建立。
- `reports/FIGURE_AUDIT.md` 已有图表审查。
- `results/RESULTS_MANIFEST.json` 至少包含主要指标或图表。

不要在建模前运行快审。建模前需要的是题型路由和反模板审查。

## Five-Minute Reading Order

1. 摘要：是否直接回答题目，是否有模型名、量化结果、验证和结论边界。
2. 目录/结构：子问题是否清楚，逻辑是否从问题到模型到结果闭环。
3. 关键图表：是否一眼能看懂结论，caption 是否写出发现。
4. 模型路线：是否像“为题目而建模”，还是像模型堆料。
5. 结论与建议：是否有可执行建议、数字支撑和局限说明。
6. 创新点：是否和题目难点相关，是否可被证据支撑。

## Output Format

写入 `reports/PAPER_SCORECARD.md` 的 `Judge Skim Review` 小节：

```markdown
## Judge Skim Review

结论：值得继续细看 / 勉强继续 / 不值得继续

### First Impression

### Evidence Seen In 5 Minutes

| Area | Evidence | Status | Comment |
| --- | --- | --- | --- |

### First-Eye Deductions

| Issue | Severity | Evidence | Required Fix |
| --- | --- | --- | --- |

### Top 3 Fixes

1.
2.
3.
```

任何 `HIGH` 或 `BLOCKER` 的 first-eye deduction 必须同步写入 `reports/REVISION_ACTIONS.md`。

## Skim Rubric

### 值得继续细看

- 摘要有明确模型路线和量化结果。
- 至少 2-3 张关键图表能支撑核心结论。
- 子问题结构清楚，结果逐问回应。
- 模型和数据匹配，没有明显模板堆料。
- 结论有边界，不夸大。

### 勉强继续

- 题目回应基本存在，但摘要空泛或图表弱。
- 模型路线能看懂，但验证不足。
- 结论有数字，但与图表/manifest 追溯不够清楚。
- 有可修复的结构或表达问题。

### 不值得继续

- 摘要看不出解决了什么。
- 没有关键图表，或图表不支撑结论。
- 模型名称堆砌，变量/公式/验证缺失。
- 结论没有数字或没有对应证据。
- 暴露内部工作流文件名、agent 过程或未完成占位符。

## Common First-Eye Deductions

- 摘要只写背景，不写结果。
- 关键图 caption 只写“某某图”，不写“说明了什么”。
- 论文说用了复杂模型，但方法和代码没有对应。
- 图中文字乱码、坐标轴没有单位、图例不可读。
- 结论写“显著提升”“最优方案”，但没有 baseline 或统计/敏感性支撑。
- 模型创新点只是算法名，没有对应题目痛点。

## Relation To Full Review

快审只判断第一印象，不得替代十维 scorecard。  
如果快审认为“不值得继续”，但完整评分没有发现硬失败，最终仍不得直接 PASS；至少要留下 `HIGH` revision action，修摘要、关键图或结论表达。
