# Paper Scorecard

Review date: 2026-06-29
Rubric: contest_score_rubric.md (0-5 scale)

## Contest Review Panel

### Panel 1: contest-reviewer (simulated)

**结论: PASS (score 42/50)**

#### Strengths
1. 问题拆解清晰，四个子问题有独立的分析框架
2. L1正则化Logistic回归选对了PbO/SiO₂等有物理意义的特征
3. 多分类器集成策略增加了Q3分类的可靠性
4. Q4的Graphical Lasso + Fisher Z差异检验方法有深度
5. 敏感性分析的覆盖面较广（组分扰动、训练集扰动、交叉验证）
6. 两类玻璃风化模式相反的发现具有实质学术价值

#### Concerns
1. Q1c仅3对配对数据，Bootstrap不足以为预测提供充分支撑（MEDIUM）
2. 论文中部分图表未插入（FIGURE_PLAN有20张，论文中插入约7张）
3. Q2b亚类的考古学解释还不够深入
4. 缺少非数据型图示（技术路线图、整体建模框架图）

#### Score per dimension

| # | Dimension | Score | Rationale |
|---|-----------|-------|-----------|
| 1 | Problem understanding | 5 | 四个子问题准确拆解，关系分析到位，约束条件（85-105%）正确纳入 |
| 2 | Modeling fit | 4 | 方法选择与问题类型高度匹配，但Q1c的Bayesian设计降为Bootstrap，理论深度略降 |
| 3 | Mathematical rigor | 4 | 公式完整，变量定义清晰，但Q1c预测模型缺少严格的误差传播推导 |
| 4 | Data processing | 4 | 归一化、缺失处理、成分选择有依据，但Na₂O的辅助讨论未在论文中充分展开 |
| 5 | Code/result reproducibility | 4 | 5个script均可独立运行，结果写入JSON；缺少requirements.txt和种子统一声明 |
| 6 | Visualization quality | 3 | 图表数据驱动、含统计量，但存在两个问题：(a)图中中文标签因DejaVu Sans缺失显示为方框；(b)论文只插入了约1/3的图表 |
| 7 | Paper structure | 4 | 结构符合国赛标准（摘要→重述→分析→假设→求解→评价→参考文献→附录），但缺少总技术路线图 |
| 8 | Claim evidence | 4 | CLAIM_TRACE.md中19条声明全部traced，但部分声明（如Q1c预测）支持证据偏弱 |
| 9 | Validation and sensitivity | 4 | Q3有组分扰动+训练集扰动，Q2有交叉验证+ARI，Q4有Fisher Z。Q1c缺少验证，Q2b扰动分析可加强 |
| 10 | Submission readiness | 4 | 论文可编译（需xelatex），无占位符，格式规范。图表路径引用正确。缺少编译后的PDF验证 |

**Total: 42/50**

### Panel 2: devil's-advocate (simulated)

**结论: CONDITIONAL_PASS**

#### 评委可能提出的质疑

**质疑1: "你们的Q1c预测真的可信吗？" (HIGH)**
仅依赖3对铅钡玻璃的配对数据，就声称可以预测风化前成分。评委可能直接否定Q1c的可靠性。
→ **应对**: 在论文中强化"估计"措辞，明确标注为基于有限样本的近似推断，并将该部分定性为"探索性分析"而非确定性预测。

**质疑2: "亚类划分只有2类，是不是太简单了？" (MEDIUM)**
k=2是否可能是过简化的结果？轮廓系数虽然最优，但k=3和k=2的Silhouette差异需要讨论。
→ **应对**: 补充k=2 vs k=3的对比，说明为何2类在考古学上更有意义。

**质疑3: "为什么问题一中只分析了风化×类型的Logistic回归，而没有做多因素交互？" (LOW)**
风化×类型×纹饰的交互效应是否考虑？
→ **应对**: 样本量限制（高钾风化仅6例）使得交互项估计不稳定，在论文中说明即可。

**质疑4: "Graphical Lasso在高钾组n=18时估计8变量精度矩阵，稀疏性假设合理吗？" (MEDIUM)**
→ **应对**: 已使用8个核心组分（而非全部11个），且同时提供了Pearson相关矩阵作为稳健基准。

**质疑5: "论文中的图表标签是英文的，但这是中文论文" (LOW)**
matplotlib生成的PDF中轴标签为英文（因中文缺失字体），与论文中文主体不一致。
→ **应对**: 若时间允许，用matplotlib中文配置重新生成；否则在图题中添加中文说明。

#### 额外注意
- A1在论文中分类为高钾，但A1的CaO=6.08%偏高而PbO未检出——这确实是典型的高钾玻璃特征（低PbO），结论无误但论文中可补充一行成分分析
- Q1b中高钾和铅钡的风化效应方向"相反"是一个很强的结论，需要确保对比统计的p值有充足效力——建议补充Mann-Whitney U检验的p值表

### Panel 3: visualization-reviewer (simulated)

**结论: CONDITIONAL_PASS**

#### 图表质量逐张审查

| Figure | 轴标签 | 图例 | 清晰度 | 论文插入 | 意见 |
|--------|--------|------|--------|----------|------|
| q1a_weather_type_bar.pdf | ✓ EN | ✓ | ✓ | ✓ | OK |
| q1a_or_forest.pdf | ✓ EN | ✓ | ✓ | — | 未插入论文 |
| q1b_boxplot_matrix.pdf | ✗ 缺中文 | ✓ | ✓ | — | 轴标签需修复 |
| q1b_effect_size.pdf | ✓ EN | ✓ | ✓ | ✓ | OK |
| q1c_pred_vs_actual.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q1c_change_rates.pdf | ✓ EN | ✓ | ✓ | ✓ | OK |
| q2a_ratio_scatter.pdf | ✓ EN | ✓ | ✓ | ✓ | OK |
| q2a_decision_boundary.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q2a_roc.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q2b_dendro_gaok.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q2b_dendro_qianbei.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q2b_pca_gaok.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q2b_pca_qianbei.pdf | ✓ EN | ✓ | ✓ | ✓ | OK |
| q2b_silhouette.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q3_classifier_compare.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q3_mahalanobis.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q3_sensitivity_heat.pdf | ✓ EN | ✓ | ✓ | ✓ | OK |
| q4_heatmaps.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |
| q4_partial_networks.pdf | ✓ EN | ✓ | ✓ | ✓ | OK |
| q4_diff_network.pdf | ✓ EN | ✓ | ✓ | — | 未插入 |

**图表面板结论**: 20张图生成了，论文中插入了7张（35%）。核心图（风化效应、分类决策边界、偏相关网络）都已插入，其余图可作为附录。但缺少一张总览性质的"技术路线/研究框架图"。

#### 表格审查
- 论文中T1-T5均有完整定义，格式规范（三线表）
- 缺失：Q1b显著性检验表（Mann-Whitney U p值）仅有效应量，未附p值
