# V1 归档

> 归档日期：2026-07-01

## 内容说明

本目录保存了数学建模竞赛 **V1 工作流** 的全部技能和规范文件。V1 是线性管道流程（`0problem-triage → 1start-mathmodel → 2analysis-modeling → 3coding-visual → 4drawio → 5writing → 6verity`），已被 **V2 工作流**（`mm-start-contest-v2` 系列）完全替代。

## 当前工作流

请使用 **V2 工作流**，入口为 `skills/mm-start-contest-v2/SKILL.md`。V2 提供：

- 高分论文导向的 10 维度评分
- 子代理并行评审机制
- 强制人工确认门禁
- 结构化修订闭环
- 完整的声明追踪和图表审计

## 归档内容

```
archive/v1/
├── skills/
│   ├── 0problem-triage/SKILL.md        ← 赛题预审
│   ├── 1start-mathmodel/SKILL.md       ← V1 总控入口
│   ├── 2analysis-modeling/SKILL.md     ← 分析与建模
│   ├── 3coding-visual/SKILL.md         ← 代码与图表
│   ├── 4drawio/SKILL.md               ← 流程图
│   ├── 5writing/SKILL.md              ← 论文撰写
│   ├── 6verity/SKILL.md               ← 验证验收
│   └── 6verity/scripts/writing_check.sh ← 论文质量检查
├── _references/
│   ├── math_modeling_norms.md          ← 数学建模规范（V1 专用）
│   ├── claude_code_monitoring.md       ← 长流程监控规范（V1 专用）
│   └── check_context_contract.py        ← 上下文检查脚本（V1 专用）
└── README.md
```

## V2 保留的交叉文件

以下 V1 资源被 V2 复用，**未归档**，仍保留在原位：

| 文件 | 用途 |
|------|------|
| `skills/5writing/templates/` | 34 套 LaTeX/Typst 模板，V2 论文构建的唯一硬依赖 |
| `skills/doctor/SKILL.md` | 环境检查工具，V1/V2 共用 |

## 恢复

如需恢复 V1 工作流，将上述文件移回原路径即可。但建议使用 V2 工作流以获得更好的结果。
