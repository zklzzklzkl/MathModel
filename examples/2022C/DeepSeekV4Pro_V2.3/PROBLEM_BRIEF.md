# Problem Brief

## Contest And Task

| Field | Value |
|-------|-------|
| Name | 高教社杯全国大学生数学建模竞赛 (CUMCM) |
| Year | 2022 |
| Problem | C |
| Title | 古代玻璃制品的成分分析与鉴别 |
| Domain | Archaeometry / Chemometrics / Statistical Classification |

## Background

古代玻璃沿丝绸之路传播，我国古代玻璃吸收外来技术后本土取材制作，外观相似但化学成分不同：
- **高钾玻璃 (High-K)**: 以草木灰为助熔剂，K2O含量高，流行于岭南及东南亚
- **铅钡玻璃 (Pb-Ba)**: 以铅矿石为助熔剂，PbO和BaO含量高，被认为是中国独创（楚文化）

风化作用导致内部元素与环境元素交换，成分比例变化，影响类型判断。风化过程中某些元素淋失（Na2O, K2O），某些富集（来自埋藏环境）。

## Source Files

- `C:\Users\zklzk\xwechat_files\wxid_nn0sj7wymrcv22_9942\msg\file\2026-05\C题(1).docx` — 赛题文档
- `C:\Users\zklzk\xwechat_files\wxid_nn0sj7wymrcv22_9942\msg\file\2026-05\附件(1).xlsx` — 数据附件（3个工作表）

## Top-Level Questions

| Q# | Task | Mathematical Type |
|----|------|-------------------|
| Q1 | 风化与类型/纹饰/颜色关系；风化前后化学成分统计规律；预测风化前含量 | 分类关联分析 + 统计检验 + 逆回归/风化校正 |
| Q2 | 高钾/铅钡分类规律；亚类划分（特征选择+聚类+敏感性分析） | 有监督/无监督分类 + 特征选择 + 敏感性检验 |
| Q3 | 对表单3未知文物进行类型鉴别 + 敏感性分析 | 监督分类（Q1风化校正 + Q2分类规则） |
| Q4 | 不同类别玻璃化学成分关联关系 + 不同类别间关联差异比较 | 组成数据相关性 + 组间差异检验 |

## Dependencies Between Questions

```
Q1 (风化分析与校正) ──→ Q3 (需要风化校正 A2,A5,A6,A7)
    │                    │
    └──→ Q4 (需要风化校正后数据) ←── Q2 (需要类型与亚类标签)
                                    │
Q2 (分类规则与亚类) ──→ Q3 (分类规则应用于未知样品)
```

Q1 和 Q2 可并行求解，两者均为 Q3 和 Q4 的基础。

## Constraints

1. **成分累加和 85%-105% 视为有效**，空白=未检测到（低于检出限）
2. **成分性数据约束**: 14种化学成分比例为整体，总和约100%，形成闭合效应 — 相关性/聚类/PCA前必须进行CLR/ILR变换
3. **多采样点**: 部分文物有部位1/部位2、风化/未风化点、严重风化点等
4. **配对数据**: 风化/未风化配对样本是Q1风化校正的关键校准数据

## Inputs And Outputs

| Question | Inputs | Expected Outputs |
|----------|--------|------------------|
| Q1 | 表单1 (58条) + 表单2 (69条) | 风化关联检验、风化元素变化规律表、风化前成分预测值 |
| Q2 | 表单2 (69条) + 表单1 类型标签 | 判别元素排序、亚类数量与成员、亚类划分规则 |
| Q3 | 表单3 (8条) + Q1模型 + Q2规则 | A1-A8类型归属 + 置信度 + 亚类归属 |
| Q4 | Q1校正后数据 + Q2/Q3标签 | 组内相关矩阵、组间差异检验、PCA biplot |

## Key Technical Challenge

**组成数据 (Compositional Data) 的闭和约束**: 所有分析（相关性、聚类、PCA）必须在Aitchison几何框架下进行，使用CLR或ILR变换，否则会产生虚假负相关。

## Ambiguities And Risks

1. **HIGH**: 风化标签冲突 — 7件文物在表单1标"风化"但表单2有"未风化点"数据
2. **HIGH**: Na2O/K2O缺失模式不是随机缺失 — 高钾玻璃Na2O系统性地低于检出限
3. **MEDIUM**: 低于检出限的处理（零 vs. 半检出限 vs. 结构零）
4. **MEDIUM**: 亚类数量无先验信息，需纯数据驱动
5. **MEDIUM**: Q1风化前预测的建模路径选择（固定元素归一化 vs 配对回归 vs 质量平衡）
6. **LOW**: 4件文物颜色缺失（均为风化铅钡）

## Next Modeling Needs

- Q1A: 卡方检验 / Logistic回归 / Cramer's V
- Q1B: 按玻璃类型分组的风化vs未风化成分比较 (Mann-Whitney U)
- Q1C: 基于不移动元素(Al2O3, Fe2O3)的归一化校正 + 配对回归模型
- Q2: CLR变换 → 层次聚类/K-means/GMM → 决策树规则
- Q3: 多分类器集成 (LDA, k-NN, Random Forest, SVM)
- Q4: CLR变差矩阵 → 偏相关网络 → 组间排列检验
