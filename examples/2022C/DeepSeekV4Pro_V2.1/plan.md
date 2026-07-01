# V2 数学建模执行方案

用户偏好：
- 排版引擎：LaTeX
- 竞赛类型：国赛 (CUMCM 2022)
- 论文语言：中文
- 子问题数量：4

workflow:
0. 题面与数据建档 - `mm-problem-intake`
1. 候选模型与评审 - `mm-model-strategy`
2. 实验代码与图表 - `mm-data-experiment`
3. 论文整合与图文论证 - `mm-paper-build`
4. 高分论文对标评审 - `mm-contest-review`
5. 最终验收 - `mm-final-verify`

subagent_policy:
- review agents: read-only
- experiment agents: write only task outputs
- final verifier: read all and write verification report

参考文献：
- 题目: C:\Users\zklzk\xwechat_files\wxid_nn0sj7wymrcv22_9942\msg\file\2026-05\C题(1).docx
- 附件: C:\Users\zklzk\xwechat_files\wxid_nn0sj7wymrcv22_9942\msg\file\2026-05\附件(1).xlsx
