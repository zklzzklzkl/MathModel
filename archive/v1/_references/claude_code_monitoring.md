# Claude Code 外部监控规范

当使用 Claude Code、Codex 或其他长时间运行的 AI 工具完成数学建模全流程时，必须把“实时监控”作为外部质量层，而不是等到最后只看论文。

## 监控目标

1. 确认 AI 是否还在推进，而不是卡在交互确认、报错或空转。
2. 及时发现题面提取、中文编码、数据字段、代码语法、缺失阶段产物等问题。
3. 用文件状态评估流程位置，避免长上下文丢失后无法接手。
4. 把风险转化为 `WORKFLOW_STATE.md`、`reports/VERIFY_REPORT.md` 或对应阶段报告里的可处理事项。

## 建议监控文件

可在实际工作目录放置一个轻量监控脚本，例如：

- `monitor_claude_workflow.py`
- `run_monitor_once.bat`
- `run_monitor_live.bat`

监控输出建议放入 `_monitor/`，至少包含：

- `_monitor/status.md`：当前阶段、文件数、Claude 进程、最高风险。
- `_monitor/risk_register.md`：风险登记表。
- `_monitor/experience_summary.md`：阶段性不足与经验。
- `_monitor/events.jsonl`：文件变化事件流。
- `_monitor/snapshot.json`：最近一次文件快照。

## 必查风险

### 输入与编码

- 题目 PDF 和附件路径是否存在。
- 题面文本是否已提取，且中文没有明显乱码。
- 附件是否完成字段、单位、缺失和异常说明。

### 上下文契约

必须检查 `workflow_state_contract.md` 中列出的标准档案。若缺少以下文件，不允许直接进入写作阶段：

- `PROBLEM_BRIEF.md`
- `DATA_AUDIT.md`
- `WORKFLOW_STATE.md`
- `reports/ANALYSIS_MODELING_REPORT.md`
- `reports/RESULTS_REPORT.md`
- `results/RESULTS_MANIFEST.json`
- `reports/CLAIM_TRACE.md`

### 代码与结果

- 所有 Python 脚本通过语法编译检查。
- 每个子问题有对应脚本、输出和图表记录。
- 关键数值进入 `RESULTS_MANIFEST.json`，不能只存在于聊天记录或控制台输出。
- 图表要有源数据、生成脚本、论文放置章节和 caption 建议。

### 写作与验收

- 论文入口存在：`paper/main.typ`、`paper/main.tex`、`res.md`、`res.docx` 或 `report.pdf`。
- 正文无占位符、无内部路径泄露、无未追溯数值。
- PDF 编译和视觉检查结果写入 `reports/VERIFY_REPORT.md`。

## 监控结论处理

- `CRITICAL` 或 `HIGH` 风险未处理前，不进入下一阶段。
- `MEDIUM` 风险可以继续推进，但必须写入 `WORKFLOW_STATE.md` 的“阻塞与风险”。
- 若外部 AI 已生成代码但缺少契约文件，应先补齐 `PROBLEM_BRIEF.md`、`DATA_AUDIT.md`、`WORKFLOW_STATE.md`，再继续建模或写作。
- 若监控发现长时间没有文件变化，应检查 AI 是否等待确认、命令报错、权限受限或数据路径错误。

## 本次实测经验

在 `D:\WorkSpace_MathModel\workspace` 的监控中，Claude Code 已能生成预处理脚本、Q1-Q4 分析脚本和部分图表，但早期缺少 `PROBLEM_BRIEF.md`、`DATA_AUDIT.md`、`WORKFLOW_STATE.md`、`RESULTS_MANIFEST.json` 等上下文契约产物。该模式说明：纯 Agent 自动推进容易产出代码碎片，但不一定自然沉淀可审计的竞赛工作流状态。因此 MathModelAgent 应采用“skill 契约 + 外部监控 + 必要时 Agent 执行”的组合方式。
