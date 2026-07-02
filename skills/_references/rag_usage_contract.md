# RAG Usage Contract

> 本契约规定 V2 skills 如何使用本地 8 库 RAG。  
> RAG 是证据和候选路线来源，不是最终裁判。最终选择仍由对应 skill、文件 gate 和人工确认决定。

## Local Commands

默认命令从仓库根目录运行：

```bash
python scripts/rag_ingest.py --source knowledge/samples
python scripts/rag_query.py "综合评价 TOPSIS 权重 稳定性" --library model_methods
```

真实资料建议放在 `knowledge/raw/<library_id>/` 下；该目录不提交 GitHub。  
索引和 SQLite ledger 默认位于 `knowledge/.local/`；该目录也不提交 GitHub。

## Eight Libraries

| Library ID | 用途 | 主要阶段 |
| --- | --- | --- |
| `cumcm_problems` | 历年国赛题面、附件说明、隐含评分点 | Phase 0/1 |
| `mcm_icm_problems` | 历年美赛题面、赛道、英文表达、模型路线 | Phase 0/1 |
| `excellent_papers` | 高分论文结构、模型路线、图表和结论表达 | Phase 1/3/4 |
| `model_methods` | 评价、预测、优化、机理、图论、统计、仿真、多目标模型卡 | Phase 1 |
| `code_templates` | Python/R/MATLAB 清洗、建模、验证、可视化模板 | Phase 2 |
| `figure_templates` | 推荐图、图表审计、caption、证据图谱 | Phase 1/2/3 |
| `paper_expression` | 摘要、假设、公式说明、结果分析、灵敏度、结论表达 | Phase 3 |
| `review_rubrics` | 评分标准、评委快审、扣分点、反模板审查 | Phase 4/6 |

## Required RAG Result Fields

任何被引用的 RAG 结果都必须保留：

- 命中文档标题。
- 来源路径。
- 可信度。
- 适用阶段。
- 推荐用法。
- 禁用/风险提示。

不得只复制检索片段而丢失来源。

## Citation Format In Artifacts

在报告中用轻量引用表，而不是长篇粘贴：

```markdown
## Local RAG Evidence Used

| Use | Library | Source | Confidence | Stage | Risk |
| --- | --- | --- | --- | --- | --- |
```

如果未使用 RAG，写：

```markdown
## Local RAG Evidence Used

Not used. Reason: <local index unavailable / query returned no reliable sourced hits / user requested no RAG>.
```

## Stage Query Guidance

### Phase 0: `mm-problem-intake`

查询：

- `cumcm_problems` 或 `mcm_icm_problems`：题面动词、附件字段、相似题型。

输出：

- 在 `PROBLEM_BRIEF.md` 记录可能题型和相似历史结构。
- 在 `WORKFLOW_STATE.md` 记录低置信或冲突的路由风险。

### Phase 1: `mm-model-strategy`

查询：

- `model_methods`：候选模型卡。
- `excellent_papers`：相似高分论文结构。
- `figure_templates`：推荐图表。
- 必要时查询题库：历史题型路线。

输出：

- 在 `MODEL_CANDIDATES.md` 写题型路由、首选/基准/备选/不推荐模型。
- 在 `MODEL_REVIEW_AI.md` 写反模板审查。

### Phase 2: `mm-data-experiment`

查询：

- `code_templates`：可复现代码骨架。
- `figure_templates`：图表类型和审计标准。

输出：

- 在 `EXPERIMENT_LOG.md` 记录使用的模板来源和改动。
- 不得直接复制模板变量名而不适配当前数据。

### Phase 3: `mm-paper-build`

查询：

- `paper_expression`：摘要、公式说明、结果解释、灵敏度、结论写法。
- `excellent_papers`：结构和图文证据组织。

输出：

- 在 `PAPER_BUILD_REPORT.md` 记录表达模板来源。
- 论文正文不得暴露 RAG、skill、reports 等内部流程名。

### Phase 4: `mm-contest-review`

查询：

- `review_rubrics`：评分标准、快审、扣分点。
- `model_methods` 或 `anti_template_review.md`：模型滥用检查。

输出：

- 在 `PAPER_SCORECARD.md` 写 RAG evidence 和 judge skim review。
- 将 actionable 问题同步到 `REVISION_ACTIONS.md`。

## Trust Rules

1. RAG 命中不是事实证明，只是本地资料证据。
2. 低可信命中只能用于提示，不可作为核心路线依据。
3. 第三方资料必须保留 license/source；大文件不进 GitHub。
4. 题库和优秀论文用于“相似结构”和“评审标准”，不得抄袭内容。
5. 如果 RAG 和当前题面/数据冲突，以当前题面和数据为准。
6. 没有来源的内容不得写入“RAG evidence used”。
7. RAG 推荐的高级模型必须通过反模板审查和人工模型 gate。

## Source Quality Addendum

Follow `source_quality_policy.md` for every RAG hit.

Required returned fields:

- `source_quality`: `S/A/B/C/D`.
- `allowed_use`: `core_evidence`, `auxiliary_only`, or `risk_signal_only`.
- `quality_reason`: why this level was assigned.
- `core_evidence_allowed`: true only for `S/A`.

For core modeling routes and paper claims, use `python scripts/rag_query.py "<query>" --core-only` or manually filter to `S/A`. `B` sources can guide templates and checks only. `C/D` sources can only trigger risks, cautions, or review actions.

Expanded evidence table:

```markdown
| Use | Library | Source | Confidence | Source Quality | Allowed Use | Core Evidence | Stage | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

## Failure Handling

- 本地索引不存在：继续执行 skill，但记录 RAG unavailable。
- 检索结果为空：不要编造；记录 no sourced hits。
- PDF 乱码或无法解析：记录 ingest error，优先改用 Markdown/TXT 摘要。
- Chroma/embedding 不可用：使用 SQLite lexical baseline，不阻塞比赛流程。
