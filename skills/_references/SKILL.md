---
name: _references
description: "共享规范知识库。包含 V2 流程契约、Codex 子代理协议、评分标准、图表标准、本地 RAG 使用契约、题型路由、模型卡和评审协议等参考内容。其他 skills 在执行过程中按需读取；不要单独触发本 skill。"
---

# _references

> 文件关系全貌请见 [[FILE_RELATIONSHIP_MAP]]。
> 上游：无。下游：V2 总控与所有 V2 阶段 skills。
> V1 已归档，当前以 V2/V2.3 为主。

本目录是共享规范知识库，不是可独立执行的 skill。其他 skills 在需要流程契约、上下文交接、门禁、评分、模型选择、图表标准、RAG 证据或评审协议时读取这里的文件。

## Core Contracts

- `workflow_state_contract.md`: 持久化上下文、阶段门禁、结果 manifest 和结论追踪约定。
- `v2_pipeline_contract.md`: V2 Skill + Codex 子代理混合工作流的总契约。
- `codex_subagent_protocol.md`: Codex 子代理角色、并行执行、线程记录、权限继承和模型/推理强度配置协议。
- `agent_review_protocol.md`: 模型、论文、图表和最终验收的统一评审格式。
- `agent_profiles/`: 可复制给 Codex 子代理或自定义 agent 的数学建模角色画像。

## Contest Quality References

- `contest_score_rubric.md`: 高分论文导向的评分维度和硬失败条件。
- `paper_benchmark_profile.md`: 弱论文与高分论文的差距画像和最低质量线。
- `figure_quality_standard.md`: 论文图表质量、元数据和硬失败标准。
- `nature_figure_integration_guide.md`: 可选接入 `Yuan1z0825/nature-skills` 的 scientific plotting 契约、Python/R 后端纪律、导出质量和图表审查。

## Capability Layer

- `model_method_cards.md`: 评价、预测、优化、机理、图论网络、统计检验、仿真、多目标决策等模型卡。
- `problem_type_router.md`: 题型-模型路由器；输出主/子题型、首选模型、基准模型、备选模型、不推荐模型、验证方法和推荐图表。
- `anti_template_review.md`: 反模板审查；检查 AHP/TOPSIS/神经网络/遗传算法/PCA/聚类等是否被滥用。
- `judge_skim_review_protocol.md`: 评委 5 分钟快审；检查摘要、目录、关键图、创新点、结论和第一眼扣分点。
- `rag_usage_contract.md`: 本地 8 库 RAG 使用契约；规定 source citation、可信度、阶段用法、风险提示和失败处理。

## Helper Scripts

V2.3 read-only audit scripts live under this skill:

- `scripts/resolve_nature_figure.py`: locate and validate supported `nature-figure` layouts.
- `scripts/audit_v2_run.py`: read-only final audit for PNG-only figures, Pillow data figures, missing vector bundles, incomplete figure audit columns, short-paper false PASS, and unresolved HIGH/BLOCKER actions.

Local RAG helper scripts live in the repository root:

- `scripts/rag_ingest.py`: ingest Markdown/TXT/CSV/code/PDF sources into the local SQLite ledger, with optional Chroma indexing.
- `scripts/rag_query.py`: retrieve source-grounded hits from the 8 local knowledge libraries.

Do not manually trigger `_references` as a standalone skill.
