# MathModel Control Center 小白使用指南

适用对象：第一次使用本项目、不会命令行、只想把数学建模工作流跑起来的同学。

## 1. 这个工具是做什么的？

MathModel Control Center 是一个本地网页控制台，用来管理数学建模 V2.6 工作区。

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
cd app
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
cd app\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

前端依赖如果失败，执行：

```powershell
cd app\frontend
pnpm install
```

## 4. 推荐使用流程

### 第一步：选择或新建工作区

进入网页后，在左下角选择一个工作区。

如果要开始新赛题：

1. 进入“设置”
2. 在“新建工作区”里填写名称、竞赛、语言、绘图后端
3. 点击“创建”

新工作区会生成标准 V2.6 目录结构：

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
- `Manifest`：结果清单是否符合 V2.6
- `Missing`：缺失的关键文件数量
- “下一步建议”：当前最该修的问题
- “审计问题”：脚本发现的具体风险

如果看到 `FAIL/HIGH`，不要急着润色论文，先修高风险问题。
