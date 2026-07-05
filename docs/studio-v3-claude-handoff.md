# MathModel Studio V3 工作交接给 Claude Code

生成时间：2026-07-05  
工作目录：`D:\WorkSpace_MathModel`  
当前分支：`codex/v3-studio`

## 目标背景

用户要求把 MathModelAgent 从“技能集合 + 文件协议 + 初级 Control Center”升级为：

```text
本地私人化 AI 建模与科研 Studio
+ MathModelAgent 高分竞赛质量内核
+ 未来可商业化扩展的平台底座
```

核心方向：

- 学习 MathArk 的项目管理、运行流、模型配置、模板体系和前端体验。
- 保留 V2 高分论文质量内核：Human Gate、Claim Trace、Figure Audit、Scorecard、Revision、Final Verify。
- LangGraph 降级为可插拔 `RuntimeDriver`，不再作为用户侧产品概念。
- 当前以本地私人化为主，预留未来商业化。

## 当前已完成

### 1. 后端 V3 Product API

新增文件：

- `app/backend/app/studio_api.py`

已在主应用注册：

- `app/backend/app/main.py`

关键接口已实现：

```text
POST /api/projects
GET  /api/projects
POST /api/projects/{id}/files
GET  /api/projects/{id}/files
GET  /api/projects/{id}/artifacts/read

POST /api/runs
GET  /api/runs/{id}
POST /api/runs/{id}/resume
POST /api/runs/{id}/cancel
GET  /api/runs/{id}/events
GET  /api/runs/{id}/events/stream

GET  /api/gates/{run_id}/current
POST /api/gates/{run_id}/{gate_id}/submit

GET  /api/models/config
PUT  /api/models/config
POST /api/models/test-connection

GET    /api/templates
POST   /api/templates/import-builtin
POST   /api/templates/upload
GET    /api/templates/{id}/preview
GET    /api/templates/{id}/download
DELETE /api/templates/{id}
```

### 2. 控制面实体

`studio_api.py` 使用本地 SQLite 作为产品控制面，已包含：

- `Project`
- `Run`
- `RunEvent`
- `Gate`
- `Artifact`
- `TemplatePack`
- `ModelConfig`

注意：workspace 文件仍是真相源，DB 只做控制面和索引。

### 3. RuntimeDriver 初版

已实现：

- `RuntimeDriver`
- `LocalWorkflowDriver`
- `LangGraphDriver`

`LangGraphDriver` 当前只是产品层包装，还没有真正把 Phase 0-6 全部异步接管到 V3 Run 生命周期。

### 4. Human Gate 初版

已实现：

- 创建 Run 时生成 `human_model_review` Gate。
- 提交 Gate 时写入：
  - `reports/HUMAN_MODEL_REVIEW.md`
  - `reports/MODELING_DECISION.md`
- 提交后更新 Run 状态和 RunEvent。

### 5. Artifact 真实读取

已实现：

- `GET /api/projects/{id}/artifacts/read?path=...`

安全策略：

- 只接受 workspace 内相对路径。
- 禁止绝对路径、盘符和 `..`。
- 预览上限 512 KiB。
- 读取时同步回写 Artifact 索引。

### 6. 模板系统

已实现：

- ZIP 上传。
- `template.json` 解析。
- `main.tex/main.typ` 校验。
- 路径逃逸校验。
- 预览、下载、删除。
- 从 `skills/5writing/templates` 导入内置模板：
  - `POST /api/templates/import-builtin`

运行验证时导入会生成本地 `template_packs/`，已加入 `.gitignore`。

### 7. 新前端 Studio

新增目录：

- `app/frontend-studio/`

技术栈：

- Next.js
- TypeScript
- Tailwind
- lucide-react
- React Flow
- Monaco Editor
- 本地 shadcn 风格 `Button`

已实现 UI：

- 任务入口：数学建模竞赛、统计建模、数据分析、论文写作、课程作业、科研/毕设。
- 项目创建。
- 文件上传。
- RuntimeDriver 选择。
- 阶段时间线。
- React Flow 工作流图。
- RunEvent 面板。
- Human Gate 面板。
- 阶段模型配置。
- 模板库。
- 内置模板导入。
- 制品索引。
- Monaco 制品预览。
- 开发者模式入口。

旧前端已标记 legacy：

- `app/frontend/src/App.vue`

### 8. 文档

已新增：

- `docs/studio-v3-implementation.md`
- `docs/testing/studio-v3-tdd.md`
- `docs/studio-v3-claude-handoff.md`（本文件）

## 当前未完成且正在进行中的工作

### 重点：Human Gate 内容还没有完全产品化

我刚开始把 Human Gate 从静态卡片升级为真实读取：

- `reports/MODEL_CANDIDATES.md`
- `reports/MODEL_REVIEW_AI.md`
- `reports/FIGURE_PLAN.md`

当前测试已先写好，但后端实现还没补完。

当前失败测试：

```powershell
python -m pytest tests/test_studio_v3_api.py::test_studio_project_run_events_and_gate_write_v2_artifacts -q --tb=short
```

失败点：

```text
KeyError: 'artifact_previews'
```

原因：

`GET /api/gates/{run_id}/current` 当前只返回：

```json
{
  "id": "...",
  "run_id": "...",
  "type": "human_model_review",
  "status": "required",
  "title": "...",
  "artifacts": [...]
}
```

但测试现在要求返回：

```json
{
  "...": "...",
  "artifact_previews": [
    {
      "path": "reports/MODEL_CANDIDATES.md",
      "type": "report",
      "content": "..."
    },
    {
      "path": "reports/MODEL_REVIEW_AI.md",
      "type": "report",
      "content": "..."
    },
    {
      "path": "reports/FIGURE_PLAN.md",
      "type": "report",
      "content": "..."
    }
  ]
}
```

测试位置：

- `tests/test_studio_v3_api.py`
- 函数：`test_studio_project_run_events_and_gate_write_v2_artifacts`

新增断言内容大致是：

```python
previews = {item["path"]: item for item in gate["artifact_previews"]}
assert set(previews) == {
    "reports/MODEL_CANDIDATES.md",
    "reports/MODEL_REVIEW_AI.md",
    "reports/FIGURE_PLAN.md",
}
assert "Route A" in previews["reports/MODEL_CANDIDATES.md"]["content"]
assert "risk" in previews["reports/MODEL_REVIEW_AI.md"]["content"].lower()
assert "figure" in previews["reports/FIGURE_PLAN.md"]["content"].lower()
for relative in previews:
    assert (workspace / relative).is_file()
```

## Claude Code 下一步应做

### Step 1：补后端 Gate artifact bootstrap

文件：

- `app/backend/app/studio_api.py`

建议新增 helper：

```python
def ensure_human_gate_artifacts(workspace: Path) -> list[str]:
    ...
```

需要保证创建 Run 时，workspace 下存在：

```text
reports/MODEL_CANDIDATES.md
reports/MODEL_REVIEW_AI.md
reports/FIGURE_PLAN.md
```

内容要求用于测试和产品预览：

- `MODEL_CANDIDATES.md` 包含 `Route A`
- `MODEL_REVIEW_AI.md` 包含 `risk`
- `FIGURE_PLAN.md` 包含 `figure`

这只是 V3 产品占位内容，不要替代 V2 真正的模型策略阶段。后续真实 LangGraph/Skill 运行会覆盖这些文件。

建议在 `create_run()` 中插入：

```python
artifact_paths = ensure_human_gate_artifacts(Path(project_row["workspace_path"]))
```

然后 Gate 的 `artifacts` 使用 `artifact_paths`。

同时 `LocalWorkflowDriver.start()` 里的 RunEvent artifacts 也应包含三项：

```text
reports/MODEL_CANDIDATES.md
reports/MODEL_REVIEW_AI.md
reports/FIGURE_PLAN.md
```

### Step 2：补 Gate preview serialization

建议修改：

```python
def row_to_gate(...)
```

不要直接让 `row_to_gate` 读文件，因为它目前没有 workspace 上下文。

更稳妥：

新增 helper：

```python
def row_to_gate_with_previews(row: sqlite3.Row, workspace: Path) -> dict[str, Any]:
    gate = row_to_gate(row)
    gate["artifact_previews"] = [...]
    return gate
```

然后在：

```python
@router.get("/api/gates/{run_id}/current")
def current_gate(...)
```

同时查 `runs.workspace_path`，返回 `row_to_gate_with_previews(...)`。

预览逻辑可复用 artifact 安全读取思想：

- 只读取 Gate artifacts 中列出的相对路径。
- 限制在 run workspace 内。
- 文本大小限制 512 KiB。
- 返回 `path/type/size/truncated/content`。

### Step 3：跑 RED -> GREEN

先确认当前 RED：

```powershell
python -m pytest tests/test_studio_v3_api.py::test_studio_project_run_events_and_gate_write_v2_artifacts -q --tb=short
```

实现后跑：

```powershell
python -m pytest tests/test_studio_v3_api.py -q --tb=short
```

期望从当前 `6 passed` 增长为仍然全绿。

再跑相邻回归：

```powershell
python -m pytest tests/test_studio_v3_api.py tests/test_human_gate_api.py tests/test_workspace_management_api.py tests/test_run_workspace_artifacts_api.py -q --tb=short
```

上一次结果是：

```text
25 passed, 1 warning
```

实现后应保持通过。

### Step 4：前端 Human Gate 接真实 preview

文件：

- `app/frontend-studio/src/lib/api.ts`
- `app/frontend-studio/src/app/page.tsx`

类型扩展：

```ts
export type GateArtifactPreview = {
  path: string;
  type: string;
  size: number;
  truncated: boolean;
  content: string;
};

export type Gate = {
  ...
  artifact_previews?: GateArtifactPreview[];
};
```

页面中把当前静态内容：

```tsx
推荐路线：方案 A
优先完成可解释模型...
```

替换为从：

```ts
gate?.artifact_previews
```

渲染。

建议 UI：

- 左侧/上方显示候选路线 `MODEL_CANDIDATES.md`
- 下方显示 AI 风险评审 `MODEL_REVIEW_AI.md`
- 下方显示图表计划 `FIGURE_PLAN.md`
- 保留三个按钮：批准、备选、自定义
- 增加可编辑 textarea：
  - `selected_route`
  - `human_notes`

当前 `submitGate()` 仍写死：

```ts
selected_route: decision === "approved" ? "方案 A" : "自定义路线"
human_notes: ...
```

需要改成使用用户输入状态。

### Step 5：前端构建

```powershell
cd app\frontend-studio
npm run build
```

上一次通过。

### Step 6：更新文档

更新：

- `docs/studio-v3-implementation.md`
- `docs/testing/studio-v3-tdd.md`

记录：

- Human Gate artifact previews 已实现。
- 当前 Gate 已从静态卡片升级为真实 artifact 展示。
- 对应测试命令和结果。

## 当前验证状态

在我中断前，最新已验证：

```powershell
python -m pytest tests/test_studio_v3_api.py -q --tb=short
```

结果曾为：

```text
6 passed, 1 warning
```

但注意：我随后新增了 Human Gate preview 的 RED 断言，所以当前这个命令会失败，直到你完成上面 Step 1/2。

前端构建上一次通过：

```powershell
cd app\frontend-studio
npm run build
```

## 本地服务状态

之前为了验证启动过多个本地服务：

```text
127.0.0.1:8000  旧 uvicorn，可能没有 V3 路由
127.0.0.1:8001  早期 V3 后端
127.0.0.1:8002  较新 V3 后端
127.0.0.1:5174  早期 Studio 前端
127.0.0.1:5175  早期 Studio 前端
127.0.0.1:5176  较新 Studio 前端
```

Claude Code 接手时建议不要直接复用这些进程。可以新开端口，例如：

```powershell
cd D:\WorkSpace_MathModel\app\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

```powershell
cd D:\WorkSpace_MathModel\app\frontend-studio
$env:NEXT_PUBLIC_MATHMODEL_API_BASE="http://127.0.0.1:8010"
npm run dev -- --hostname 127.0.0.1 --port 5180
```

## 工作树注意事项

仓库在接手前已经有不少脏改动，不要随意 revert。

本轮相关新增/修改主要包括：

```text
.gitignore
app/backend/app/main.py
app/backend/app/studio_api.py
app/frontend/src/App.vue
app/frontend-studio/
docs/studio-v3-implementation.md
docs/testing/studio-v3-tdd.md
tests/test_studio_v3_api.py
```

还有一些文件在我接手前/过程中已经是脏的，可能属于前序工作：

```text
app/backend/app/langgraph_runner.py
app/backend/app/langgraph_state.py
app/backend/app/models.py
app/backend/app/phase_plan.py
app/backend/app/workspace.py
app/frontend/src/api.ts
app/frontend/src/store.ts
app/frontend/src/styles.css
docs/frontend-control-center-v2.md
app/backend/app/json_preprocessor.py
tests/test_human_gate_api.py
tests/test_json_preprocessor.py
tests/test_workspace_management_api.py
```

不要回滚这些，除非用户明确要求。

## 忽略规则

已加入 `.gitignore`：

```text
app/backend/.local/
app/frontend-studio/node_modules/
app/frontend-studio/.next/
template_packs/
```

原因：

- `app/backend/.local/` 是本地 SQLite 控制面。
- `template_packs/` 是导入内置模板后的本地运行数据。
- `.next/` 和 `node_modules/` 是前端构建/依赖产物。

## 后续大方向

Human Gate 真实预览完成后，下一批高价值任务是：

1. 把 `LocalWorkflowDriver / LangGraphDriver` 接入真实 Phase 0-6 生命周期，而不是只创建 Run/Gate。
2. 用 RunEvent 驱动前端时间线真实更新。
3. 质量面板读取真实：
   - `CLAIM_TRACE`
   - `METHOD_IMPLEMENTATION_MATRIX`
   - `FIGURE_AUDIT`
   - `PAPER_SCORECARD`
   - `REVISION_ACTIONS`
   - `VERIFY_REPORT`
4. 为统计建模、数据分析、论文写作、课程作业、科研/毕设建立领域 workflow skeleton。
5. 加 Playwright E2E：创建项目 -> 导入模板 -> 启动 run -> 查看 gate preview -> 提交 gate -> 查看 artifact preview。

