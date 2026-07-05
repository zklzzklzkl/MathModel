# MathModel Studio V3 Implementation Notes

本文记录本次 V3 革命式更新已经落地的范围，以及后续仍需继续推进的边界。

## 已落地

### 1. 旧前端冻结

- `app/frontend/src/App.vue` 已标记为 legacy。
- 后续产品化工作迁移到 `app/frontend-studio/`，不继续往旧 Vue Control Center 堆功能。

### 2. Product API Layer

新增 `app/backend/app/studio_api.py`，并在 FastAPI 主应用中注册。当前提供：

- `POST /api/projects`
- `GET /api/projects`
- `POST /api/projects/{id}/files`
- `GET /api/projects/{id}/files`
- `GET /api/projects/{id}/artifacts/read`
- `POST /api/runs`
- `GET /api/runs/{id}`
- `POST /api/runs/{id}/resume`
- `POST /api/runs/{id}/cancel`
- `GET /api/runs/{id}/events`
- `GET /api/runs/{id}/events/stream`
- `GET /api/gates/{run_id}/current`
- `POST /api/gates/{run_id}/{gate_id}/submit`
- `GET /api/templates`
- `POST /api/templates/import-builtin`
- `POST /api/templates/upload`
- `GET /api/templates/{id}/preview`
- `GET /api/templates/{id}/download`
- `DELETE /api/templates/{id}`
- `GET /api/models/config`
- `PUT /api/models/config`
- `POST /api/models/test-connection`

### 3. 控制面实体

本地 SQLite 控制面包含：

- `Project`
- `Run`
- `RunEvent`
- `Gate`
- `Artifact`
- `TemplatePack`
- `ModelConfig`

workspace 仍然是真相源。DB 只做产品控制面、索引、事件和配置，不替代 `reports/`、`code/`、`figures/`、`results/`、`paper/`。

### 4. RuntimeDriver 抽象

已新增：

- `RuntimeDriver`
- `LocalWorkflowDriver`
- `LangGraphDriver`

`LangGraphDriver` 目前是对现有 LangGraph 路径的产品层包装：前端只看到 driver 和状态，不暴露 `contest_graph_v3`、`mode`、`phase_execute` 等内部概念。

### 5. Human Gate 产品化

`POST /api/runs` 会创建当前人工闸门。`POST /api/gates/{run_id}/{gate_id}/submit` 会写入 V2 文件：

- `reports/HUMAN_MODEL_REVIEW.md`
- `reports/MODELING_DECISION.md`

前端 `Human Gate` 面板可以批准、选择备选或提交自定义路线。

### 6. 模型配置体系

`/api/models/config` 支持 provider、阶段模型和阶段参数。默认阶段包括：

- 题面解析
- 建模策略
- 代码生成
- 调试
- 结果分析
- 论文写作
- 竞赛评审
- 最终验收

阶段参数包括 `temperature`、`max_tokens`、`timeout_sec`、`retry_count`、`context_budget`、`parallel_agents`。

### 7. Artifact 真实预览

`GET /api/projects/{id}/artifacts/read?path=...` 会从项目 workspace 读取真实制品内容，并同步回写 `Artifact` 索引。

当前策略：

- 只接受 workspace 内相对路径
- 禁止绝对路径、盘符路径和 `..` 目录逃逸
- 文本预览上限为 512 KiB，超出时返回 `truncated=true`
- 根据顶层目录分类为 `source/report/result/code/figure/paper/workspace`

前端 `制品索引` 与 `制品预览` 已接入该接口。

### 8. 模板包系统

模板 ZIP 上传已实现：

- 必须包含 `main.tex` 或 `main.typ`
- 支持 `template.json`
- 自动保存 `required_files`、`preview_file`、warning
- 支持预览、下载、删除、按 contest 管理
- 校验 ZIP 内路径和 `template.json` 元数据路径，禁止绝对路径和目录逃逸
- 支持从 `skills/5writing/templates` 一键导入内置模板库

`POST /api/templates/import-builtin` 会扫描现有中文/英文 Typst 和 LaTeX 模板目录，复制到 `template_packs/` 控制面目录，并写入 `TemplatePack` 索引。

### 9. 新 Studio 前端

新增 `app/frontend-studio/`：

- Next.js + TypeScript + Tailwind
- 本地 shadcn 风格 UI primitive
- React Flow 工作流图
- Monaco 制品预览
- 项目三步启动：选择任务、创建项目/上传资料、选择运行引擎并启动
- 阶段时间线
- RunEvent 面板
- Human Gate 面板
- 阶段模型配置
- 模板库
- 内置模板导入
- 真实制品索引与 Monaco 预览
- 质量检查入口
- 开发者模式入口

## 当前仍是骨架的部分

- `LocalWorkflowDriver` 和 `LangGraphDriver` 已形成产品抽象，但还没有把 Phase 0-6 的真实异步执行队列全部搬入 V3 Run 生命周期。
- `CodexDriver`、`ClaudeCodeDriver`、`CloudDriver` 仍是预留入口。
- `Artifact` 已支持文本预览，但还没有做版本差异、大文件分页、二进制图像/PDF 内嵌查看。
- 前端 Human Gate 目前提交默认文本，后续应读取 `MODEL_CANDIDATES.md`、`MODEL_REVIEW_AI.md` 并结构化展示候选路线、风险和图表计划。
- 统计建模、数据分析、论文写作、课程作业、科研/毕业设计目前是产品入口和架构预留，尚未有完整领域 workflow。
- 模板库已支持从 `skills/5writing/templates` 导入，但还没有批量生成 PDF/封面预览。

## 本地启动

后端：

```powershell
cd D:\WorkSpace_MathModel\app\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

V3 前端：

```powershell
cd D:\WorkSpace_MathModel\app\frontend-studio
npm install
$env:NEXT_PUBLIC_MATHMODEL_API_BASE="http://127.0.0.1:8000"
npm run dev
```

旧前端仍可构建和运行，但仅作为 legacy Control Center 保留。
