# MathModel Control Center

本目录是 MathModelAgent V2.3 的本地全栈控制中心。

- 后端：FastAPI，默认端口 `8000`
- 前端：Vue 3 + Vite，默认端口 `5173`
- 首版模式：Manual harness，不自动调用 Codex、Claude Code 或 OpenCode
- 数据来源：本地 V2.3 workspace files

## 一键启动

```powershell
cd D:\WorkSpace_MathModel\app
.\start.bat
```

启动后打开：

```text
http://127.0.0.1:5173
```

## 配置

后端默认读取父级仓库 `D:\WorkSpace_MathModel`。如需覆盖，创建 `backend\.env`：

```text
MATHMODEL_ROOT=D:\WorkSpace_MathModel
WORKSPACE_ROOT=D:\WorkSpace_MathModel\workspaces
EXAMPLES_ROOT=D:\WorkSpace_MathModel\examples
```

## Manual Harness 流程

1. 在 UI 选择工作区。
2. 查看阶段、文件和审计问题。
3. 选择阶段与 harness 类型，生成 Prompt。
4. 将 Prompt 复制到 Codex、Claude Code、OpenCode 或其他 agent。
5. agent 修改 workspace 后，回到 UI 刷新并运行审计。

首版不会自动驾驶任何 harness；这是刻意的保护边界。
