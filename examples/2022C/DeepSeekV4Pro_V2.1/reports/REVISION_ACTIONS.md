# Revision Actions

Generated from PAPER_SCORECARD.md (score 42/50)

## Priority: HIGH (建议修改，影响得分)

| # | Action | Source | Severity | Effort |
|---|--------|--------|----------|--------|
| H1 | **Q1c预测措辞谨慎化**: 将"预测"改为"基于有限配对样本的统计分析"，增加"本节为探索性分析的说明" | devil's-advocate 质疑1 | HIGH | 小 |
| H2 | **Q1b补充p值表**: 在论文4.2节增加风化vs未风化各组分显著性检验的p值表（Mann-Whitney U） | visualization-reviewer | HIGH | 小 |
| H3 | **添加技术路线图**: 用4drawio或文字描述整体建模框架，放在问题分析之后 | contest-reviewer | HIGH | 中 |

## Priority: MEDIUM (改善论文质量)

| # | Action | Source | Severity | Effort |
|---|--------|--------|----------|--------|
| M1 | **Q2b k=2 vs k=3对比**: 在5.2节增加k=3的聚类结果简述及为何选择k=2的论证 | devil's-advocate 质疑2 | MEDIUM | 小 |
| M2 | **Q4高钾n<p说明**: 在7.2节增加一段关于Graphical Lasso在n<p条件下适用性的讨论 | devil's-advocate 质疑4 | MEDIUM | 小 |
| M3 | **未插入图表作为附录**: 在论文附录中补充主要图表（ROC曲线、聚类谱系图、分类对比图等） | visualization-reviewer | MEDIUM | 中 |
| M4 | **A1成分分析补充**: 在6.2节补充A1为何归为高钾的成分依据（低PbO、高CaO） | devil's-advocate 质疑5 | MEDIUM | 小 |
| M5 | **增加Q1c验证**: 在4.3节增加留一交叉验证结果（对3对配对数据逐一留出） | contest-reviewer | MEDIUM | 小 |

## Priority: LOW (锦上添花)

| # | Action | Source | Severity | Effort |
|---|--------|--------|----------|--------|
| L1 | 图表中文标签修复：matplotlib设置中文字体重新生成关键图表 | visualization-reviewer | LOW | 中 |
| L2 | 添加requirements.txt和随机种子说明 | contest-reviewer | LOW | 小 |
| L3 | Q1a交互效应讨论：补充风化×类型在纹饰分层下的探索性结果 | devil's-advocate 质疑3 | LOW | 小 |

## 修改统计
- HIGH: 3项
- MEDIUM: 5项
- LOW: 3项

## 建议修改顺序
1. H1（措辞）+ H2（p值表）+ M4（A1分析）— 纯文本修改，15分钟
2. M1（k对比）+ M2（n<p说明）+ L3（交互效应）— 补充分析+文本
3. H3（技术路线图）— 需要绘图
4. M3（附录图表）+ L1（中文标签）— 图表工作
5. M5（Q1c验证）+ L2（requirements.txt）
