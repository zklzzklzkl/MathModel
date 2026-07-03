# Control Center 新手指南

这份文档面向第一次使用 MathModel Control Center 的用户。你不需要理解 LangGraph 内部原理，也可以完成第一次安全运行。

## 第一次使用 5 步

1. 打开 `app/start.bat`，进入本地前端页面。
2. 在“设置”页新建或选择一个工作区。
3. 在“设置”页上传题目 PDF、附件 Excel/CSV、图片或其它数据文件。
4. 回到“总览”，点击 `Run Recommended Graph`。
5. 到“运行结果”查看每次运行生成的报告，到“文件”查看当前工作区产物。

## provider=none 和真实 API 的区别

`provider=none` 是默认安全基线：

- 不需要 API key。
- 不调用真实大模型。
- 不会产生模型调用费用。
- 用来验证流程、安全边界和产物链路是否跑通。

真实 DeepSeek / OpenAI-compatible provider 才会调用外部模型。只有当你希望模型真正生成建模计划、代码、论文内容，或比较不同模型效果时，才需要配置 API key。

API key 应配置在后端运行环境中，不要粘贴到浏览器页面。配置后需要重启后端服务。

```env
DEEPSEEK_API_KEY=

OPENAI_API_KEY=
OPENAI_BASE_URL=
```

把真实 key 只填在你本机的私有 `.env` 或终端环境变量里，不要提交到 Git。

## 页面功能地图

- 总览：查看审计状态、推荐动作、阶段状态和下一步建议。
- 阶段运行：查看每个阶段的输入输出；P1/P4 可单阶段执行，其它阶段可 Dry Run。
- 运行图：查看 LangGraph Runtime 状态、运行推荐图、Human Gate 和最近运行结果。
- 运行结果：浏览每次 copied run workspace 产生的报告和文件。
- 文件：查看当前 workspace 的 artifacts、论文、结果清单和审计报告。
- 评测：查看 benchmark 报告，运行 provider=none 安全评测。
- 高级：手动生成 Prompt 或准备 harness 副本，主要用于调试。
- 设置：新建工作区、上传 source 文件、查看后端健康状态。
- 帮助：查看快速开始、按钮说明、术语解释、API 配置和常见问题。

## 常见术语

- Workspace / 工作区：一道题目的项目文件夹，包含 `source/`、`code/`、`paper/`、`results/`、`reports/` 等目录。
- Source Workspace：原始题目工作区。推荐在这里启动运行。
- Run Workspace：每次运行复制出来的安全副本，主要用于查看结果。
- LangGraph：把数学建模流程按阶段串起来的执行器。
- `contest_graph_v3`：当前推荐的完整安全流程。
- Skill：某个阶段的能力模块，例如建模策略、实验可视化、论文构建、评分审查。
- Human Gate：人工确认闸门。进入高风险阶段前必须人工确认模型选择和建模方案。
- Audit：审计检查，用于发现文件缺失、图表路径错误、证据链缺失等问题。
- Manifest：结果清单，记录生成了哪些指标、表格、图像和脚本。
- Dry Run：预演运行，只检查流程，不正式执行完整建模。
- Benchmark：评测，用已有工作区或报告检查系统稳定性和不同模型表现。

## 常见问题

**不配置 API 能用吗？**

能。默认 `provider=none` 可以验证流程和安全边界，但不代表真实 LLM 建模效果。

**Run Recommended 会花钱吗？**

默认 `provider=none` 不会调用真实 API，因此不会产生模型调用费用。

**为什么 Run This Skill 按钮不可用？**

当前单阶段执行只支持 P1/P4，其它阶段请用 Dry Run 或完整 `contest_graph_v3`。

**为什么有很多 Audit 问题？**

Audit 是检查器。它发现缺图表、缺结果、缺证据链是正常的，可以帮助你判断下一步该修哪里。

**Human Gate 是错误吗？**

不是。它是人工确认机制，用来防止系统自动选择错误建模路线。

**Run Workspace 是什么？**

Run Workspace 是每次运行的安全副本。查看结果可以用它，但不要在 run workspace 里继续嵌套运行。

## 安全边界

- 前端不会保存 API key。
- 默认 `provider=none` 不调用真实模型。
- Human Gate 不会被前端绕过。
- 系统不会自动写最终 `VERIFY_REPORT.md` 或声称最终 PASS。
- 推荐从 Source Workspace 启动运行，Run Workspace 只用于查看结果。
