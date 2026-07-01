# V2 数学建模执行方案

用户偏好：
- 排版引擎：LaTeX
- 竞赛类型：国赛（2022 高教社杯 CUMCM）
- 论文语言：中文
- 子问题数量：4

赛题概要：
- C题：古代玻璃制品的成分分析与鉴别
- 数据类型：58 件文物基本信息（类型/纹饰/颜色/风化）+ 69 条化学成分数据 + 8 件待分类文物
- 核心任务：统计分析、风化预测、亚类划分、未知分类、关联分析

workflow:
0. 题面与数据建档 - `mm-problem-intake`
1. 候选模型与评审 - `mm-model-strategy`
2. 人工确认最终建模路线 - `reports/HUMAN_MODEL_REVIEW.md`
3. 实验代码与图表 - `mm-data-experiment`
4. 论文整合与图文论证 - `mm-paper-build`
5. 高分论文对标评审 - `mm-contest-review`
6. 评审问题修订闭环 - `mm-revision-integrator`
7. 最终验收 - `mm-final-verify`

subagent_policy:
- review agents: read-only
- experiment agents: write only task outputs
- final verifier: read all and write verification report

figure_policy:
- 科研绘图后端：Python (matplotlib/seaborn)
- nature-figure：unavailable
- formal_paper_mode：true
- short_report_mode：false
