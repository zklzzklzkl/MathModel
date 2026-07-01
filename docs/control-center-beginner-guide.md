# MathModel Control Center 小白使用指南

适用对象：第一次使用本项目、不会命令行、只想把数学建模工作流跑起来的同学。

## 1. 这个工具是做什么的？

MathModel Control Center 是一个本地网页控制台，用来管理数学建模 V2.3 工作区。

它不是自动替你完成比赛的黑盒，而是帮你把流程管清楚：

- 当前赛题进行到哪个阶段
- 哪些文件已经生成，哪些文件缺失
- 审计发现了哪些 `BLOCKER/HIGH` 问题
- 下一步应该修什么
- 该复制什么 Prompt 给 Codex、Claude Code 或 OpenCode
- 修改后如何再审计

简单说：它是“数学建模项目驾驶舱”。

## 2. 一键启动

打开 PowerShell，执行：

```powershell
cd D:\WorkSpace_MathModel\app
.\start.bat
```

启动成功后，浏览器打开：

```text
http://127.0.0.1:5173
```

后端地址是：

```text
http://127.0.0.1:8000
```

## 3. 如果 start.bat 卡在安装依赖怎么办？

如果你看到类似：

```text
ReadTimeoutError ... pypi.org ... python-multipart
```

这不是代码坏了，而是网络访问 PyPI 超时。

现在 `start.bat` 已经改成：

- 先检查依赖是否已安装
- 已安装就跳过联网安装
- 未安装才安装
- PyPI 失败后自动用清华镜像重试

如果仍失败，可以手动执行：

```powershell
cd D:\WorkSpace_MathModel\app\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

前端依赖如果失败，执行：

```powershell
cd D:\WorkSpace_MathModel\app\frontend
pnpm install
```

## 4. 推荐使用流程

### 第一步：选择或新建工作区

进入网页后，在左下角选择一个工作区。

如果要开始新赛题：

1. 进入“设置”
2. 在“新建工作区”里填写名称、竞赛、语言、绘图后端
3. 点击“创建”

新工作区会生成标准 V2.3 目录结构：

```text
plan.md
todo.md
WORKFLOW_STATE.md
reports/
results/
code/
figures/
paper/
source/
```

### 第二步：上传题面和附件

进入“设置”里的“上传 source”，选择题面 PDF、附件 Excel、数据文件等。

文件会保存到：

```text
source/
```

这些文件不会被上传到 GitHub，避免泄露赛题、附件或个人资料。

### 第三步：看总览

进入“总览”页面，重点看：

- `Audit`：整体审计状态
- `Manifest`：结果清单是否符合 V2.3
- `Missing`：缺失的关键文件数量
- “下一步建议”：当前最该修的问题
- “审计问题”：脚本发现的具体风险

如果看到 `FAIL/HIGH`，不要急着润色论文，先修高风险问题。

### 第四步：按阶段推进

进入“阶段”页面，可以看到 Phase 0-6：

| 阶段 | 作用 |
| --- | --- |
| Phase 0 | 题面与数据建档 |
| Phase 1 | 建模策略与人工确认 |
| Phase 2 | 实验、代码、图表、结果清单 |
| Phase 3 | 论文构建、图表审计、结论追踪 |
| Phase 4 | 高分论文审查 |
| Phase 5 | 修订集成 |
| Phase 6 | 最终验收 |

每个阶段都会显示：

- 输入文件是否齐全
- 输出文件是否生成
- Gate 状态
- 下一步动作
- 可复制 Prompt

### 第五步：生成 Prompt

在“阶段”或“执行”页面选择：

- Phase
- Harness：Manual、Codex、Claude Code、OpenCode

点击“生成 Prompt”。

然后把 Prompt 复制到你正在使用的 agent 工具里。

当前版本不会自动调用任何 agent，这是为了避免误改文件。

### 第六步：准备安全副本

如果你想让 agent 在副本里试跑，点击：

```text
准备安全副本
```

系统会复制当前工作区到：

```text
runs/<timestamp>-<name>/
```

并写入：

```text
CONTROL_PROMPT_PHASE_<n>.md
```

这样即使 agent 改坏了文件，也不会直接污染原工作区。

### 第七步：运行审计和生成修订任务

agent 修改完后，回到网页：

1. 点击“刷新”
2. 点击“运行审计”
3. 点击“生成修订任务”

修订任务会写入：

```text
reports/REVISION_ACTIONS_CONTROL.md
```

## 5. 当前已经实现的功能

### 已完成：MVP 打磨

- 新建 V2.3 工作区
- 读取 Markdown、JSON、文本、图片、PDF
- 生成 Phase 0-6 专用 Prompt
- 记录运行历史
- 修复 `start.bat` 反复联网安装依赖的问题

### 已完成：工作流控制

- Dashboard 下一步建议
- 阶段输入/输出检查
- Gate 状态检查
- 审计 issue 转修订任务
- 上传题面和附件到 `source/`

### 已完成：Harness Adapter 基础层

- Manual、Codex、Claude Code、OpenCode 统一入口
- 安全副本运行机制
- Prompt 文件自动写入副本
- 命令预览
- 当前不自动执行 CLI

## 6. 现在不会做什么？

当前版本不会：

- 自动调用 Codex、Claude Code 或 OpenCode
- 自动联网搜索资料
- 自动把结果合并回原工作区
- 自动判断论文一定能获奖
- 上传你的题面、附件、source 文件到 GitHub

这些限制是有意保留的安全边界。

## 7. 未来开发方向

### 方向 A：更完整的 Artifact Viewer

- 更漂亮的 Markdown 渲染
- Excel/CSV 预览
- PDF 页码定位
- 图表画廊
- 代码文件树

### 方向 B：真正的 Harness 执行器

在安全副本基础上逐步支持：

- Codex 自动执行
- Claude Code 自动执行
- OpenCode 自动执行
- 执行后自动审计
- 人工确认后合并回主工作区

### 方向 C：图表质量系统

- 图表模板库
- Nature-style 图表检查
- `RESULTS_MANIFEST.json` 自动修复建议
- 图文一致性检查

### 方向 D：RAG 知识库

未来可以加入：

- 优秀论文案例库
- 常用模型卡片
- 代码模板库
- 论文写作模板库
- 本地 ChromaDB 检索

### 方向 E：联网资料搜索

可以接入 Tavily 或其他搜索 API，用于：

- 找真实背景资料
- 找政策/行业数据
- 找论文参考

但必须配套来源记录和引用审计，避免污染论文可信度。

## 8. GitHub 上传安全规则

默认不上传：

- `workspaces/`
- `examples/**/source/`
- `examples/**/runs/`
- `control-center-history.jsonl`
- `.env`
- `.venv`
- `node_modules`
- `dist`

这些文件可能包含题面、附件、个人路径、运行记录或本地依赖。

上传 GitHub 前建议执行：

```powershell
git status --short --untracked-files=all
```

确认没有题面 PDF、Excel 附件、`.env` 或本地工作区被加入提交。
