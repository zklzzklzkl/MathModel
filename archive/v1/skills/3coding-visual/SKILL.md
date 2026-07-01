---
name: 3coding-visual
description: "数学建模编程实现与数据图表生成阶段。根据 ANALYSIS_MODELING_REPORT.md 编写可复现代码、运行求解、验证约束、输出 RESULTS_REPORT.md 并生成论文可用的数据驱动图表 PDF。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# 编程实现与数据图表生成

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]] · 上游: [[skills/2analysis-modeling/SKILL|Phase 1 建模]] · 下游: [[skills/4drawio/SKILL|Phase 3 流程图]] · 共享规范: [[skills/_references/SKILL|_references]]

本 skill 承接 `2analysis-modeling`。目标是把 `reports/ANALYSIS_MODELING_REPORT.md` 里的模型和算法落实为可复现程序，跑出可信结果，并生成论文中需要的数据型图表。

本阶段必须额外产出：

- `reports/EXPERIMENT_LOG.md`：每次运行的脚本、参数、输入、输出、状态。
- `results/RESULTS_MANIFEST.json`：论文可引用关键数值、表格、图表的唯一索引。
- `reports/FIGURE_PLAN.md`：每张图的来源、用途、建议放置章节和 caption。
- 更新 `WORKFLOW_STATE.md`。

## 数学建模规范参考

如需领域判断，读取 `../_references/math_modeling_norms.md` 中的“题型防错速查”“代码实现与结果”“编码阶段常见错误”和“图表与可视化”小节。该文件只作为规范知识库，不新增本阶段的固定产物。

开始编码前读取 `../_references/workflow_state_contract.md`，确认 `PROBLEM_BRIEF.md`、`DATA_AUDIT.md`、`WORKFLOW_STATE.md`、`reports/ANALYSIS_MODELING_REPORT.md`、`reports/ANALYSIS_GATE.md` 已存在。若缺失，不要直接写代码，应先补齐或在 `WORKFLOW_STATE.md` 标记阻塞。

## 阶段边界

- 本阶段负责：代码、实验运行、结果、结果表、数据驱动图表。
- 本阶段不负责：技术路线图、算法流程图、系统架构图、概念示意图。这些交给 `4drawio`。
- 本阶段不写论文正文，只为 `5writing` 提供可信数值和图表资产。


### Step 1: 代码结构

按 `plan.md` 中"项目目录结构"创建 `code/` 和 `figures/` 骨架，再开始写代码。子问题数不一定是 3，按赛题实际数量调整。

若接手的是外部 AI 已经生成的散落脚本，先整理入口、输入输出和运行方式，再决定是否迁移到 `code/`。不要在不知道脚本用途的情况下继续堆新文件。


### Step 2: 逐子问题实现

按子问题顺序实现，不要一次性写完不跑。

每个子问题必须完成：

1. 读取所需数据。
2. 实现模型或算法。
3. 验证约束。
4. 输出核心结果。
5. 绘制丰富的图表。
6. 在 `reports/RESULTS_REPORT.md` 中写清楚方法、关键数值和校验结果。
7. 将可被论文引用的关键数值写入 `results/RESULTS_MANIFEST.json`。
8. 将运行记录写入 `reports/EXPERIMENT_LOG.md`。

优化类问题必须先保证可行解，再优化目标值。预测类问题必须做训练/验证划分或合理误差评估。评价类问题必须说明指标方向、归一化方法和权重来源。

### Step 3: 结果文件格式


AI 在实现、求解和作图过程中，必须把关键中间过程保存成数据并做好记录，例如清洗后的数据摘要、模型参数、迭代历史、约束检查、灵敏度分析过程、图表所用数据和运行日志。中间数据优先保存到 `figures/` 或 `code/outputs/`，并在 `reports/RESULTS_REPORT.md` 中说明文件用途。

`reports/RESULTS_REPORT.md` 推荐结构：

```markdown
# 计算结果

## 运行环境
## 数据读取与预处理
## 问题一结果
## 问题二结果
## 问题三结果
## 灵敏度分析
## 约束与一致性校验
## 与建模报告的一致性说明
## 可复现运行方式
```

所有数据和图表结果都必须出现在 `reports/RESULTS_REPORT.md` 中引用

`results/RESULTS_MANIFEST.json` 必须至少包含 `metrics` 和 `figures` 两类记录。每个 metric 要包含 `id`、`problem`、`value`、`unit`、`source_file`、`script`、`description`；每个 figure 要包含 `id`、`path`、`problem`、`source_data`、`script`、`intended_section`、`caption`。

所有 Python 脚本生成后必须立即做语法编译检查；核心脚本还要在当前数据上运行一次，并把成功或失败写入 `reports/EXPERIMENT_LOG.md`。

### Step 4: 生成数据驱动图表

根据 `reports/ANALYSIS_MODELING_REPORT.md` 和 `reports/RESULTS_REPORT.md` 规划图表，生成 PDF 到 `figures/`。

典型图表：

- 预测类：真实值-预测值对比、误差分布、指标对比。
- 优化类：收敛曲线、成本对比、资源利用率、方案前后对比。
- 评价类：综合得分排序、雷达图、热力图、敏感性曲线。
- 数据理解：分布图、趋势图、相关性图、箱线图。

图表要求：

- PDF 矢量输出，适合论文。
- 不在图内写大标题，标题交给论文 caption（Typst 的 `caption:` 或 LaTeX 的 `\caption{}`）。
- 中文论文图表使用中文坐标轴和图例；英文论文使用英文。
- 不生成流程图/架构图/路线图。

图表可以由主程序或独立脚本生成，不强制固定脚本名。无论采用哪种方式，都必须保存图表对应的数据来源和生成记录。

阶段结束前创建或更新 `reports/FIGURE_PLAN.md`，列出每张图是否用于论文、证据来源、推荐章节和 caption。若图表只适合调试，不要让 `5writing` 自动引用。
