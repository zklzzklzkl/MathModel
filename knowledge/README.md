# MathModel Local RAG Knowledge Base

这里保存 MathModel 能力层本地 RAG 的配置、样例和使用说明。  
大型题面、附件、优秀论文 PDF、向量索引和本地数据库不要提交到 GitHub。

## Directory Policy

可提交：

- `knowledge/libraries.json`
- `knowledge/samples/`
- 本 README

不可提交：

- `knowledge/raw/`: 你的真实题库、论文、附件、模板资料。
- `knowledge/.local/`: SQLite ledger、Chroma 索引和缓存。

这些路径已经写入 `.gitignore`。

## Eight Libraries

1. `cumcm_problems`: 历年国赛题库，包含赛题、附件说明、题型标签、隐含评分点。
2. `mcm_icm_problems`: 历年美赛题库，包含 MCM/ICM 题面、赛道、英文表达、常见模型路线。
3. `excellent_papers`: 优秀论文库，包含高分论文结构、摘要、图表、模型路线、结论表达。
4. `model_methods`: 常规模型库，包含评价、预测、优化、机理、图论、统计、仿真、多目标决策等模型卡。
5. `code_templates`: 代码模板库，包含 Python/R/MATLAB 清洗、建模、验证、可视化脚本。
6. `figure_templates`: 图表模板库，包含推荐图、图表审计标准、caption 写法、证据图谱。
7. `paper_expression`: 论文表达模板库，包含摘要、问题重述、模型假设、公式说明、结果分析、灵敏度分析、结论。
8. `review_rubrics`: 评分评审库，包含评分标准、评委快审、扣分点、反模板审查、高分/低分差距。

## Quick Start

索引仓库内置样例：

```powershell
python scripts\rag_ingest.py --source knowledge\samples --vector-store none
```

查询全部库：

```powershell
python scripts\rag_query.py "综合评价类题目 TOPSIS 权重 稳定性"
```

查询指定库：

```powershell
python scripts\rag_query.py "预测 优化 混合题 约束 验证" --library model_methods
```

输出 JSON：

```powershell
python scripts\rag_query.py "评委 快审 摘要 关键图 结论" --library review_rubrics --json
```

## Local Database Location

当前默认是本地文件数据库，不需要 Docker、Redis 或远程服务：

- SQLite ledger: `knowledge/.local/rag.sqlite3`
- Optional Chroma store: `knowledge/.local/chroma/`
- Raw imported materials: `knowledge/raw/`

这些路径都被 `.gitignore` 忽略。也就是说，GitHub 可以提交脚本、配置、样例和来源说明，但不会上传你的本地资料库和第三方大文件。

## Adding Local Documents

建议把真实资料放入对应目录：

```text
knowledge/raw/cumcm_problems/
knowledge/raw/mcm_icm_problems/
knowledge/raw/excellent_papers/
knowledge/raw/model_methods/
knowledge/raw/code_templates/
knowledge/raw/figure_templates/
knowledge/raw/paper_expression/
knowledge/raw/review_rubrics/
```

然后索引：

```powershell
python scripts\rag_ingest.py --source knowledge\raw --vector-store none
```

## Importing zhanwen/MathModel

如果你已经下载了 `zhanwen/MathModel`，可以用导入器把高价值资料复制到本地 RAG 原料区：

```powershell
python scripts\import_zhanwen_mathmodel.py --source "C:\Users\zklzk\Downloads\Compressed\MathModel-master\MathModel-master"
python scripts\rag_ingest.py --source knowledge\raw\zhanwen_mathmodel --vector-store none
```

默认导入策略：

- 国赛试题、模型资料、代码/Matlab、论文模板、竞赛经验文档尽量纳入。
- 优秀论文 PDF 默认只导入 120 份高价值样本，避免首次复制几 GB。
- 生成本地 manifest: `knowledge/raw/zhanwen_mathmodel/zhanwen_mathmodel_manifest.jsonl`
- 生成可提交来源说明: `knowledge/source_notes/zhanwen_mathmodel_import.md`

如果要全量复制优秀论文：

```powershell
python scripts\import_zhanwen_mathmodel.py --source "C:\Users\zklzk\Downloads\Compressed\MathModel-master\MathModel-master" --full-papers
python scripts\rag_ingest.py --source knowledge\raw\zhanwen_mathmodel --vector-store none
```

注意：当前本地下载包未发现明确 `LICENSE/COPYING` 文件。原始 PDF、论文、模板和附件默认只做本地索引，不随仓库上传；仓库可以提交导入脚本、配置、样例和来源说明。

如果已安装 ChromaDB，可以同时写入本地 Chroma store：

```powershell
python scripts\rag_ingest.py --source knowledge\raw --vector-store chroma
```

默认 embedding 模式是 `auto-local`：优先尝试本机已有的 BGE 模型，不会强制下载；如果不可用，会使用本地 hashing embedding 占位。之后可以显式切到：

```powershell
python scripts\rag_ingest.py --source knowledge\raw --vector-store chroma --embedding-mode sentence-transformer --embedding-model BAAI/bge-m3
```

## Source Metadata

推荐给 Markdown/TXT 文件加 front matter：

```markdown
---
library: model_methods
year: 2026
contest: generic
problem_id: evaluation-demo
tags: [evaluation, topsis, sensitivity]
license: project-authored
source_quality: A
source_type: model_card
verified_by: maintainer
last_verified_at: 2026-07-02
quality_reason: Curated local model card aligned with V2 workflow.
---
```

最低元数据应包含：

- `library`
- `source_path` 或实际文件路径
- `license`
- `year`
- `contest`
- `problem_id`
- `tags`

脚本会把这些字段写入 SQLite ledger，并在检索结果中返回来源路径、可信度、适用阶段、推荐用法和风险提示。

## Source Quality Fields

Additional recommended metadata:

- `source_quality`: `S/A/B/C/D`; see `skills/_references/source_quality_policy.md`.
- `source_type`: e.g. `official_problem`, `excellent_paper`, `model_card`, `code_template`.
- `verified_by`: human or policy that assigned the quality level.
- `last_verified_at`: date or timestamp.
- `quality_reason`: short reason for the quality level.

Core modeling and paper evidence should be queried with:

```powershell
python scripts\rag_query.py "your query" --core-only --json
```

## Important Rule

RAG 只提供证据、候选路线和写作/审查提醒。  
最终模型选择仍由 `mm-model-strategy`、人工模型 gate 和后续评审共同决定。
