# Studio V3 TDD And Verification

## RED

新增 `tests/test_studio_v3_api.py` 后，最初运行：

```powershell
python -m pytest tests/test_studio_v3_api.py -q
```

结果为 404 失败，证明 V3 Product API 尚未实现。

随后增加模板元数据目录逃逸测试：

```powershell
python -m pytest tests/test_studio_v3_api.py::test_template_metadata_cannot_write_outside_template_root -q --tb=short
```

结果为失败：恶意 `template.json` 被接受。随后在模板元数据解析和 ZIP 解压中加入路径校验。

## GREEN

当前通过：

```powershell
python -m pytest tests/test_studio_v3_api.py -q --tb=short
```

结果：

```text
6 passed, 1 warning
```

相邻 API 回归：

```powershell
python -m pytest tests/test_studio_v3_api.py tests/test_human_gate_api.py tests/test_workspace_management_api.py tests/test_run_workspace_artifacts_api.py -q --tb=short
```

结果：

```text
25 passed, 1 warning
```

后端语法检查：

```powershell
python -m py_compile app\backend\app\studio_api.py app\backend\app\main.py
```

结果：通过。

前端构建：

```powershell
cd app\frontend-studio
npm run build
```

结果：通过。

旧 Vue Control Center 构建：

```powershell
cd app\frontend
npm run build
```

结果：通过。

LangGraph provider-free benchmark：

```powershell
python scripts\langgraph_benchmark.py --root examples\2022C --mode contest_graph_v3 --provider none
```

结果：命令成功，3 个示例 workspace 均进入 `PHASE2_PLAN_ONLY`，无脚本错误。

说明：AGENTS.md 中的 `tests/langgraph_benchmark_fixtures` 当前不存在，因此使用仓库实际存在的 `examples/2022C` 验证 Benchmark Arena。

## Coverage

`tests/test_studio_v3_api.py` 覆盖：

- Project 创建和列表
- Workspace skeleton 创建
- 文件上传和 Artifact 索引
- Artifact 安全读取和真实内容预览
- Run 创建、查询、取消、恢复
- RunEvent 列表和 SSE 快照流
- Human Gate 当前闸门查询
- Human Gate 提交后写入 V2 报告文件
- ModelConfig 默认值和更新
- Provider 连接检测
- Template ZIP 上传、预览、下载、删除
- 从 `skills/5writing/templates` 导入内置模板库
- Template ZIP 缺少主文件拒绝
- Template 元数据目录逃逸拒绝
