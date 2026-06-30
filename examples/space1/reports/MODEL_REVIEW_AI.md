# Model Review AI

Generated: 2026-06-29

---

## A. model-reviewer (模型正确性评审)

结论：**CONDITIONAL_PASS**

### Strengths
1. 两条路线互补。Route A提供可靠基线，Route B追求深度和创新
2. Q1a的卡方+对应分析直接回答"关系分析"，方法匹配问题类型
3. Q1c明确识别了配对数据不足的瓶颈，Route B的Bayesian层次模型合理借力
4. Q2a使用比值特征(PbO/SiO2, K2O/SiO2)有物理化学意义
5. Q3的多分类器集成+敏感性分析覆盖了分类鲁棒性的关键维度
6. Q4的Graphical Lasso+差异网络比简单相关矩阵更有论文深度
7. 每问都规划了具体的图表产出

### Blocking Issues
无BLOCKER级别问题。

### HIGH级别问题
| # | 问题 | 影响 | 建议 |
|---|------|------|------|
| H1 | SnO2/SO2建议排除但未明确最终的成分列表 | 编码时可能出现分歧 | 最终决策中锁定：排除SnO2, SO2, Na2O(72.5%缺失)；保留11种成分或对Na2O做分组处理 |
| H2 | Q1c贝叶斯模型先验选择未具体化 | MCMC可能不收敛 | 推荐使用弱信息先验(Beta(2,2))，并在代码中设置收敛诊断(R̂<1.1) |
| H3 | Q4 Graphical Lasso在高钾组(n=18)估计14×14精度矩阵 | 样本远小于参数数量 | 建议对高钾组降维至5-6个主要组分后再做偏相关网络 |
| H4 | 归一化方法未明确 | 不同归一化策略结果不同 | 建议用总和归一化：X'_j = X_j / ΣX_i × 100% |

### Score (per Contest Score Rubric 0-5)
| Dimension | Route A | Route B |
|-----------|---------|---------|
| Problem understanding | 4 | 5 |
| Data understanding | 4 | 4 |
| Modeling fit | 4 | 5 |
| Mathematical rigor | 3 | 5 |
| Implementation clarity | 5 | 4 |
| Result validity | 3 | 5 |
| Visualization | 4 | 5 |
| Writing structure | 4 | 5 |
| Claim traceability | 4 | 4 |
| Submission readiness | N/A | N/A |

### Required Fixes
1. 最终决策中明确11种保留组分列表
2. Q1c贝叶斯模型指定先验参数和收敛诊断标准
3. 高钾组Q4使用降维组分集

### Evidence Reviewed
- MODEL_CANDIDATES.md
- PROBLEM_BRIEF.md
- DATA_AUDIT.md

---

## B. devil's-advocate (评委异议模拟)

结论：**CONDITIONAL_PASS**

### Strengths
- 两条路线均避免了模型堆砌(AHP/TOPSIS/神经网络等模板方法)
- 问题和方法之间存在实质性的匹配论证
- 每条路线都承认局限性和回退方案

### 模拟评委质疑

#### 质疑1: "风化预测的根本性困难被低估了"
仅有3对严重风化配对数据。无论用简单比例模型还是贝叶斯层次模型，3对数据的统计推断基础都非常薄弱。评委可能质疑："你们如何证明风化矫正的可靠性？"
- **严重性**: HIGH
- **对策**: 
  - 明确声明3对数据的局限性（放在论文模型假设中）
  - 将预测结果标记为"估计值"而非"精确值"
  - 增加一个validation check：用未风化点配对(约10对)额外验证风化趋势的一致性
  - 报告预测区间而非点估计

#### 质疑2: "Q2亚类划分的主观性"
K-means的k选择依赖轮廓系数，但即使轮廓系数"最优"，划分也可能缺乏考古学意义。评委可能问："你们的亚类在考古学上是否有意义？"
- **严重性**: MEDIUM
- **对策**: 
  - 在论文中明确说明亚类是"基于统计特征的聚类"，不代表考古学定论
  - 将亚类的化学成分特征与已知文献/常识对照（如高钾玻璃中是否有CaO高/低亚群）
  - 用多个聚类评价指标(DBI, CHI, Silhouette)交叉验证
  - 对比不同k下的划分稳定性

#### 质疑3: "Q3风化样品未做成分矫正"
A2, A5, A6, A7都是风化样品，其化学成分已偏离原始值。直接用风化后的数据做分类可能产生系统偏差。
- **严重性**: HIGH
- **对策**:
  - 使用Q1c的模型先对风化样品做成分矫正
  - 对比矫正前/后的分类结果
  - 如果矫正前后分类一致，说明分类结果稳健

#### 质疑4: "Q4的Graphical Lasso在n<p时理论保证不足"
高钾18个样本估计14个变量的精度矩阵，n<p问题严重。虽然L1正则化提供稀疏解，但稀疏假设本身可能不成立。
- **严重性**: MEDIUM
- **对策**:
  - 使用两组都有的6-8个主要组分(排除缺失>50%的)做分析
  - 同时提供Pearson/Spearman相关矩阵作为稳健基准
  - 在论文中讨论n<p的局限性

#### 质疑5: "Route B是否过度设计?"
评委关注模型是否"必要且充分"。Bayesian MCMC + Graphical Lasso + 多分类器集成，是否每个都有必要？
- **严重性**: LOW
- **对策**: 
  - 每个方法都回答特定的子问题需求，不存在冗余
  - 每个复杂方法都有简单方法作对比基准
  - 在论文中为每个方法选择提供一句话理由

### Required Fixes
1. Q1c: 补充配对验证和区间估计
2. Q2: 添加多重聚类指标和考古学含义讨论
3. Q3: **必须**加入风化矫正前后对比
4. Q4: 高钾组降维 + 简单相关矩阵作基准

### Evidence Reviewed
- MODEL_CANDIDATES.md
- DATA_AUDIT.md
- contest_score_rubric.md
