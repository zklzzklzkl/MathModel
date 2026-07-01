# V2 数学建模执行方案

用户偏好：
- 排版引擎：ReportLab PDF + Markdown 源稿（本机缺少 LaTeX/Typst 确认可用环境前，采用可直接生成 PDF 的方案）
- 竞赛类型：全国大学生数学建模竞赛
- 论文语言：中文
- 子问题数量：4

workflow:
0. 题面与数据建档 - `mm-problem-intake`
1. 候选模型与评审 - `mm-model-strategy`
2. 实验代码与图表 - `mm-data-experiment`
3. 论文整合与图文论证 - `mm-paper-build`
4. 高分论文对标评审 - `mm-contest-review`
5. 评审问题修订闭环 - `mm-revision-integrator`
6. 最终验收 - `mm-final-verify`

subagent_policy:
- review agents: simulated, read-only
- experiment agents: main Codex implementation, write only `code/`, `results/`, `figures/`, `reports/`
- final verifier: read all and write verification report

figure_policy:
- 科研绘图后端：Python + Pillow/ReportLab
- nature-figure：not requested

