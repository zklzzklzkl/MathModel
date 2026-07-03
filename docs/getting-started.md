# MathModelAgent V2.7-alpha 小白使用教程

> 写给第一次接触这个项目的同学。不需要懂代码，跟着步骤点就行。

---

## 这是什么？

一个**数学建模竞赛辅助工具**。它帮你做三件事：

1. **管理赛题文件** — 把题目 PDF、数据 Excel 放到 workspace 里统一查看
2. **跑 LangGraph 自动化流程** — 点击按钮，让它自动走一遍"审题→建模→实验→写论文→评审→修订→验收"的流程
3. **浏览结果** — 跑完后在浏览器里直接看生成的报告、图表、论文

它跑在你的电脑上，不需要联网（除非你想接 DeepSeek 等外部 AI）。

---

## 第一步：安装环境

### 你需要的软件

| 软件 | 干什么用 | 怎么装 |
|---|---|---|
| Python 3.10+ | 后端运行环境 | [python.org](https://python.org) 下载安装，勾选"Add to PATH" |
| Node.js 18+ | 前端运行环境 | [nodejs.org](https://nodejs.org) 下载 LTS 版 |
| pnpm | 前端包管理器 | 装好 Node.js 后，打开终端运行 `npm install -g pnpm` |
| Git | 下载仓库 | [git-scm.com](https://git-scm.com) 下载安装 |

### 下载项目

打开终端（PowerShell 或 CMD），输入：

```bash
git clone https://github.com/zklzzklzkl/MathModel.git
cd MathModel
```

### 安装依赖

```bash
# 安装 Python 包
pip install fastapi uvicorn numpy pandas matplotlib scipy scikit-learn openpyxl

# 安装前端包
cd app/frontend
pnpm install
cd ../..
```

### 验收安装

```bash
# 检查后端
python -c "import fastapi; print('FastAPI OK')"

# 检查前端
cd app/frontend && pnpm run build
```

看到 `✓ built in x.xxs` 就说明安装成功。

---

## 第二步：启动

打开**两个**终端窗口：

**终端 1 — 启动后端**：

```bash
cd D:\WorkSpace_MathModel\app\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

看到 `Uvicorn running on http://127.0.0.1:8000` 就说明后端启动了。

**终端 2 — 启动前端**：

```bash
cd D:\WorkSpace_MathModel\app\frontend
pnpm run dev
```

看到 `Local: http://127.0.0.1:5173` 就说明前端启动了。

**打开浏览器**，访问 `http://127.0.0.1:5173`，你会看到 Control Center 的主界面。

---

## 第三步：认识界面

左侧是**导航栏**，有 8 个页面：

| 图标 | 页面 | 干什么用 |
|---|---|---|
| 📊 | 总览 | 看当前 workspace 的健康状态 |
| ⚡ | 阶段 | 按 Phase 0-6 查看每个阶段的输入输出 |
| 📁 | 文件 | 浏览 workspace 里的所有文件 |
| 💻 | 执行 | 生成 Prompt，复制到 Claude Code 里用 |
| 🔀 | LangGraph | **核心功能**：配置并运行自动化流程 |
| 📂 | Runs | 浏览运行后产生的产物 |
| 📈 | 对标 | 查看 Benchmark 报告 |
| ⚙ | 设置 | 新建 workspace、上传文件 |

左侧底部是 **workspace 选择器**，默认会选中一个已有 workspace。如果没有，先去"设置"页新建一个。

---

## 第四步：新建一个 Workspace

Workspace 就是你的"工作目录"，所有赛题文件、代码、图表、论文都放在里面。

1. 点击左侧 **设置**
2. 在"新建工作区"卡片中填写：
   - **名称**：给你的 workspace 起个名字，比如 `2024-CUMCM-C`
   - **竞赛**：选 `CUMCM`（国赛）或 `MCM`（美赛）
   - **排版引擎**：选 `LaTeX`（推荐）或 `Typst`
   - **语言**：填写 `中文`
3. 点击 **创建**

创建后，左侧 workspace 选择器会自动切换到新 workspace。

### 上传赛题文件

1. 在设置页的"上传 source"卡片中
2. 点击 **选择文件**，把题目 PDF、数据 Excel、附件都上传
3. 上传后文件会出现在 workspace 的 `source/` 目录下

---

## 第五步：运行 LangGraph（核心操作）

这是 Control Center 最重要的功能。一次运行 = 自动串起全部 7 个阶段。

### 5.1 进入 LangGraph 页面

点击左侧 **LangGraph**，你会看到 7 个信息卡片。

### 5.2 确认 Runtime 状态

最上面"Runtime 状态"卡片应该显示：

```
Available: ready
Version: v1.0-alpha
```

如果显示 `unavailable`，说明 LangGraph 没装好，运行：

```bash
pip install langgraph langchain-core openai
```

### 5.3 配置运行参数

在"Run Config"卡片中，保持默认值即可：

| 参数 | 默认值 | 说明 |
|---|---|---|
| Mode | `contest_graph_v3` | 完整 7 阶段流程 |
| Phase | P1 | 从 Phase 1 开始 |
| Provider | `none` | 不调用外部 AI（安全基线） |
| Copy workspace | ✅ 勾选 | 在副本中运行，保护原文件 |
| Temperature | 0.2 | 不用改 |
| Max Tokens | 4096 | 不用改 |

### 5.4 点击运行

点击绿色的 **Run LangGraph** 按钮。按钮会变成"运行中..."，等待几秒到十几秒（取决于 workspace 大小）。

### 5.5 查看结果

运行完成后，"Run Summary"卡片会显示：

- **Status**：当前流程状态（如 `PHASE2_PLAN_ONLY` 表示 Phase 2 只做了规划，没有跑代码实验）
- **Contest Status**：整体竞赛状态
- **Completed Phases**：已完成的阶段（如 `[0, 1, 2]` 表示 Phase 0-2 已完成）
- **Paused At**：暂停在哪个阶段

**关于 `provider=none` 的结果**：因为你选的是 `provider=none`，LangGraph 不会调用外部 AI，所以 Phase 2（代码实验）、Phase 3（论文写作）只会生成骨架/计划，不会生成实际内容。这是正常的——这个模式主要用于**验证流程是否通畅**。

如果你想生成真正的建模内容，需要配 DeepSeek API key（见高级用法）。

---

## 第六步：浏览运行产物（Runs 页面）

跑完 LangGraph 后，产物都在 workspace 的 `runs/` 子目录下。

1. 点击左侧 **Runs**
2. 你会看到"Run Workspaces"列表，每个 run 显示：
   - **LG** 绿色标签 = 有 LangGraph 报告
   - **AR** 蓝色标签 = 有 Agent 运行记录
   - **PP** 黄色标签 = 有 Phase Plan
3. 点击一个 run，右侧"Run Artifacts"会列出这个 run 里所有文件
4. 使用顶部的快速过滤按钮（LangGraph / Evidence / Review / Paper）缩小范围
5. 点击文件，右侧会显示预览（Markdown 会渲染，JSON 会格式化，图片会显示）

**常用的产物文件**：

| 文件 | 是什么 |
|---|---|
| `reports/LANGGRAPH_CONTEST_GRAPH_REPORT.md` | 完整运行报告 |
| `reports/LANGGRAPH_PHASE_PLAN.json` | 各阶段的规划 JSON |
| `reports/AGENT_RUNS.md` | 每次运行的记录 |
| `results/RESULTS_MANIFEST.json` | 实验数据清单 |
| `paper/main.tex` | 论文 LaTeX 源文件 |

---

## 第七步：查看 Benchmark 报告

点击左侧 **对标**，你会看到 Benchmark Lab。

**主要功能**：

1. **Safe LangGraph Benchmark** — 绿色卡片，一键跑 `provider=none` 安全基线（和 LangGraph 页功能一样）
2. **报告列表** — 已生成的 benchmark 报告，按类别过滤
3. **多模型对比** — 对比不同 provider/mode 的报告
4. **Legacy 2022C Audit** — 2022C 赛题各 workspace 的审计结果

---

## 常见问题

### Q: 运行后状态停在 `PHASE2_PLAN_ONLY`，没有跑代码？

这是正常的。`provider=none` 模式下，Phase 2 不会生成真正的实验命令。要跑真实代码实验需要接 DeepSeek API。

### Q: 怎么接 DeepSeek？

在终端设置环境变量：

```bash
set MATHMODEL_LLM_PROVIDER=deepseek
set MATHMODEL_LLM_API_KEY=
set MATHMODEL_LLM_MODEL=deepseek-chat
```

把真实 API key 只填在本机终端或私有 `.env` 中，不要写进文档或提交到 Git。

然后在 LangGraph 页面的 Provider 下拉选 `deepseek`，Model 填 `deepseek-chat`。

### Q: 前端刷新后 API Key 要重新填吗？

Key 是通过环境变量设置的，不是在前端填的，所以重启后端才需要重新设。

### Q: 页面报错 "Failed to fetch"？

后端没启动或端口不对。确认终端 1 里的后端在运行。

### Q: workspace 选择器里没有我的 workspace？

workspace 需要放在 `workspaces/` 或 `examples/` 目录下。用"设置"页创建会自动放对位置。

### Q: 原 workspace 文件会被覆盖吗？

不会。`copy_workspace=true` 时，运行在 `runs/` 下的副本中进行，原文件不动。

### Q: 能从前端启动真实 DeepSeek benchmark 吗？

Safe Launcher 只允许 `provider=none`。真实 API benchmark 需要用命令行脚本：

```bash
python scripts/real_provider_benchmark.py --workspace <路径> --mode llm_plan --phase 1 --provider deepseek --model deepseek-chat
```

---

## 进阶技巧

### 用 Claude Code 跑完整建模流程

Control Center 是辅助工具。真正的完整建模流程建议在 Claude Code 中用 Skill 工作流：

```
/mm-start-contest-v2
```

这会启动 V2.6 Skill 工作流，逐步完成审题→建模→实验→论文→评审→修订→验收。

### 只用 Control Center 的 Prompt 生成功能

如果你习惯在 Claude Code / Codex 里手动操作：

1. 点击左侧 **执行**
2. 选 Phase 和 Harness
3. 点击 **生成 Prompt**
4. 复制生成的 Prompt 到 Claude Code 里使用

---

## 需要帮助？

- 完整功能文档：`docs/frontend-control-center-v2.md`
- API 参考：`docs/frontend-api-contract.md`
- LangGraph 架构：`docs/langgraph-runner.md`
- 版本说明：`docs/RELEASE_v2.7-alpha.md`
