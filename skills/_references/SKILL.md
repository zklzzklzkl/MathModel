---
name: _references
description: "共享规范知识库。包含数学建模竞赛规范、V2 流程契约、Codex 子代理协议、评分标准、图表标准、持久化上下文契约和外部监控规范等参考内容。其他 skills 在执行过程中按需读取，无需单独触发。"
---

# _references

本文件夹是共享规范知识库，不是可独立执行的 skill。

其他 skills 在需要领域判断时读取 `math_modeling_norms.md` 中的相关小节；在需要长上下文交接、阶段门禁、V2 子代理协作或外部 AI 监控时读取：

- `workflow_state_contract.md`：持久化上下文档案、阶段门禁、结果 manifest 和结论追踪约定。
- `claude_code_monitoring.md`：Claude Code / Codex 等外部 AI 长流程监控、风险登记和经验反馈规范。
- `v2_pipeline_contract.md`：V2 Skill + Codex 子代理混合工作流的总契约。
- `codex_subagent_protocol.md`：Codex 子代理角色、并行执行、线程记录、权限继承和模型/推理强度配置协议。
- `contest_score_rubric.md`：高分论文导向的评分维度和硬失败条件。
- `paper_benchmark_profile.md`：弱论文与高分论文的差距画像和最低质量线。
- `figure_quality_standard.md`：论文图表质量、元数据和硬失败标准。
- `nature_figure_integration_guide.md`：可选接入 `Yuan1z0825/nature-skills` 的 `nature-figure`，增强科研绘图契约、Python/R 后端纪律、导出质量和图表审查。
- `model_method_cards.md`：预测、评价、优化、统计推断、仿真等常见建模路线卡片。
- `agent_review_protocol.md`：模型、论文、图表和最终验收的统一评审格式。
- `agent_profiles/`：可复制给 Codex 子代理或自定义 agent 的数学建模角色画像。

请勿手动触发此 skill。
