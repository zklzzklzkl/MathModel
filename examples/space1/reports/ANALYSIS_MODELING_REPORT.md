# Analysis & Modeling Report

Route B — High-Score Enhanced | 2026-06-29

---

## 预处理规范

### 数据清洗
1. 排除组分总和不在85%-105%的记录（2条）
2. 排除组分: SnO2, SO2 (缺失>88%), Na2O (缺失72.5%, Q1b辅助讨论)
3. 建模组分: SiO2, K2O, CaO, MgO, Al2O3, Fe2O3, CuO, PbO, BaO, P2O5, SrO (11种)

### 归一化
对所有有效数据行:
$$X'_j = \frac{X_j}{\sum_{i=1}^{11} X_i} \times 100\%$$

### 缺失值处理策略
- Q1b统计: 成对删除(pairwise)，仅当组分存在时纳入计算
- Q2/Q3/Q4建模: 使用各组分在所有样本中的均值填充缺失值（仅在样本缺失率<50%时）
- 对于特定缺失: 若某组分在高钾玻璃中全部缺失则在该类中标记为"未检出"

---

## Q1a: 风化与类型/纹饰/颜色关系

### 方法1: 卡方独立性检验 (基线)
- H₀: 风化与变量X独立
- H₁: 风化与变量X相关
- 检验统计量: $\chi^2 = \sum \frac{(O_{ij} - E_{ij})^2}{E_{ij}}$
- Cramér's V效应量: $V = \sqrt{\frac{\chi^2}{n \cdot \min(r-1, c-1)}}$
- 当期望频数<5的单元格>20%时, 使用Fisher精确检验替代

### 方法2: Logistic回归 (主方法)
$$\text{logit}(P_{\text{风化}}) = \beta_0 + \beta_1 \cdot \text{类型}_{\text{铅钡}} + \beta_2 \cdot \text{纹饰}_B + \beta_3 \cdot \text{纹饰}_C + \beta_4 \cdot \text{颜色}_{...}$$

- 优势比: $OR = e^{\beta}$, 95% CI: $e^{\beta \pm 1.96 \cdot SE}$
- 模型评估: AIC, pseudo-R², Hosmer-Lemeshow检验

### 方法3: 多重对应分析 (MCA)
- 输入: 风化, 类型, 纹饰, 颜色 → 指示矩阵
- 奇异值分解 → 2维投影
- 双标图可视化类别关联结构

### 期望图表
1. 风化×类型堆叠柱状图
2. Logistic回归优势比森林图
3. MCA双标图 (Dim1 vs Dim2)

---

## Q1b: 分类型风化前后成分统计规律

### 分组设计
4组: 高钾无风化(12), 高钾风化(6), 铅钡无风化(12), 铅钡风化(28)

### 统计量
每组11种组分:
- 均值: $\bar{X}_j^{(g)} = \frac{1}{n_g} \sum_{i \in g} X'_{ij}$
- 标准差: $s_j^{(g)}$
- 变异系数: $CV_j^{(g)} = s_j^{(g)} / \bar{X}_j^{(g)}$
- 风化效应量: $g_j = \frac{\bar{X}_j^{\text{无}} - \bar{X}_j^{\text{风}}}{s_{\text{pooled}}}$ (Hedges' g)
- 95% Bootstrap CI: 1000次重采样

### 组间比较
- 风化vs非风化(同类型内): 独立样本t检验 + Mann-Whitney U(非参数)
- 高钾vs铅钡(同风化状态下): 同上

### 期望图表
1. 11组分 × 4组箱线图矩阵
2. 风化效应量(g)排序条形图(含Bootstrap CI)
3. 均值对比雷达图(4组叠加)

---

## Q1c: 风化前成分预测

### 数据基础
- 配对数据: 08(原始→严重风化), 26(原始→严重风化), 54(原始→严重风化)
- 补充: 约10对未风化点配对

### 方法A: 比例模型 (基线)
风化变化率: $r_j = \frac{X_j^{\text{pre}} - X_j^{\text{post}}}{X_j^{\text{pre}}}$

平均变化率(按类型): $\bar{r}_j^{(t)} = \frac{1}{N_{\text{pairs},t}} \sum r_{j,k}$

反演预测: $\hat{X}_j^{\text{pre}} = \frac{X_j^{\text{post}}}{1 - \bar{r}_j^{(t)}}$

预测区间: $\hat{X}_j^{\text{pre}} \pm t_{0.025, df} \cdot SE_{\bar{r}} \cdot \frac{\partial \hat{X}_j^{\text{pre}}}{\partial r}$

### 方法B: Bayesian层次模型 (主方法)
层次结构:
$$y_j^{\text{post}} = y_j^{\text{pre}} \cdot (1 - \delta_{j,k}) + \varepsilon$$
$$\delta_{j,k} \sim \text{Beta}(a_j, b_j) \quad \text{(组分j, 样品k的变化率)}$$
$$\varepsilon \sim N(0, \sigma_j^2)$$

先验: $a_j = b_j = 2$ (弱信息先验)

MCMC: 2000 burn-in + 4000 samples, 2 chains

预测: 从后验预测分布采样 → 后验均值 + 95% HDI

收敛诊断: $\hat{R} < 1.1$, effective sample size > 400

### 验证
- 留一交叉验证(对3对配对)
- 与未风化点配对(补充验证,非严格配对)
- MAE, RMSE, 覆盖率(95% HDI是否包含真实值)

### 期望图表
1. 预测值vs实测值散点图(3对+验证)
2. 各组分变化率后验分布图
3. 预测区间可视化(误差棒)

---

## Q2a: 分类规律分析

### 特征工程
构造5个有物理意义的比值特征:
1. $R_1 = \text{PbO} / \text{SiO}_2$ — 铅硅比
2. $R_2 = \text{BaO} / \text{K}_2\text{O}$ — 钡钾比
3. $R_3 = (\text{PbO} + \text{BaO}) / \text{SiO}_2$ — 助熔剂总量比
4. $R_4 = \text{K}_2\text{O} / \text{SiO}_2$ — 钾硅比
5. $R_5 = \text{Al}_2\text{O}_3 / \text{CaO}$ — 稳定剂比

### 方法: 正则化Logistic回归
$$\text{logit}(P(\text{铅钡})) = \beta_0 + \sum_{j=1}^{p} \beta_j X'_j$$

L1正则化: $\min_{\beta} -\ell(\beta) + \lambda \sum |\beta_j|$

λ由10折交叉验证选择 (1-SE规则)

### 评估
- 10折交叉验证准确率, AUC, F1
- 混淆矩阵
- 特征重要性排序(L1选中的非零系数)
- 与LDA、SVM对比

### 期望图表
1. 关键比值散点矩阵(高钾vs铅钡着色)
2. L1正则化路径图
3. 分类决策边界图(PCA前2维)
4. ROC曲线 + AUC

---

## Q2b: 亚类划分

### 输入
- 高钾组: 18个样品 × 11组分
- 铅钡组: 40个样品 × 11组分
- PCA降维至3维主成分(解释方差>85%)

### 方法1: 层次聚类 (主方法)
- 距离: Euclidean (标准化后)
- 链接: Ward's method
- 聚类数选择: Gap统计量
  $$\text{Gap}(k) = \frac{1}{B}\sum_{b=1}^{B} \log(W_{kb}^*) - \log(W_k)$$
  $k_{\text{opt}} = \min\{k: \text{Gap}(k) \ge \text{Gap}(k+1) - s_{k+1}\}$

### 方法2: K-means (对比)
- 同样用轮廓系数选择k
- ARI比较层次聚类与K-means结果的一致性

### 聚类评价指标
- Silhouette Index: $s(i) = \frac{b(i)-a(i)}{\max(a(i), b(i))}$
- Davies-Bouldin Index (DBI)
- Calinski-Harabasz Index (CHI)

### 稳定性分析
- 逐个剔除样本, 重聚类, 计算与原始聚类标签的ARI
- 亚类特征雷达图(均值)

### 期望图表
1. 谱系图(树状图) for each type
2. Gap统计量曲线
3. PCA散点图(按亚类着色)
4. 亚类均值雷达图
5. 轮廓系数图

---

## Q3: 未知样品分类

### 输入
- 8个未知样品(A1-A8) × 11组分
- 已知标签训练集: 67个样品 × 11组分

### 四分类器集成

**分类器1 — 马氏距离判别**
$$D_M(\mathbf{x}, \mu_k) = \sqrt{(\mathbf{x} - \mu_k)^T \Sigma^{-1} (\mathbf{x} - \mu_k)}$$

**分类器2 — LDA**
$$P(k|\mathbf{x}) \propto \mathbf{x}^T\Sigma^{-1}\mu_k - \frac{1}{2}\mu_k^T\Sigma^{-1}\mu_k + \log \pi_k$$

**分类器3 — QDA**
$$P(k|\mathbf{x}) \propto -\frac{1}{2}\log|\Sigma_k| - \frac{1}{2}(\mathbf{x}-\mu_k)^T\Sigma_k^{-1}(\mathbf{x}-\mu_k) + \log \pi_k$$

**分类器4 — KNN (k=5)**
多数投票

### 集成决策
- 各分类器权重 = 其10折CV准确率
- 加权投票: $P(k|\mathbf{x}) = \sum_{c} w_c \cdot \mathbb{1}[c(\mathbf{x}) = k]$
- 一致性: Fleiss' κ

### 风化矫正
对A2, A5, A6, A7 (风化样品):
1. 使用Q1c比例模型矫正至估计风化前成分
2. 分类后再与矫正前结果对比
3. 如果铅钡类(含PbO可区分), 风化通常不改变定性判断

### 敏感性分析
1. 组分扰动: 每个组分±5%, ±10%, 重新分类
2. 训练集扰动: 留一重训练, 检查分类一致性
3. 分类器扰动: 对比单一vs集成结果

### 期望图表
1. 分类结果表(8个样品 × 4分类器 + 集成)
2. 马氏距离条形图
3. 敏感性扰动热图
4. 风化矫正前后对比表

---

## Q4: 成分关联关系

### 输入
- 高钾组: 18个样品 × 8组分 (排除高缺失组分后选主要组分)
- 铅钡组: 40个样品 × 8组分
- 主要组分: SiO2, K2O, CaO, Al2O3, Fe2O3, CuO, PbO, BaO

### 方法1: 相关系数矩阵 (基线)
- Pearson: $r_{ij} = \frac{\sum(x_i - \bar{x}_i)(x_j - \bar{x}_j)}{\sqrt{\sum(x_i-\bar{x}_i)^2}\sqrt{\sum(x_j-\bar{x}_j)^2}}$
- Spearman: 秩相关, 对非正态稳健

### 方法2: 偏相关矩阵
$$r_{ij|rest} = -\frac{\omega_{ij}}{\sqrt{\omega_{ii} \cdot \omega_{jj}}}$$
其中 $\Omega = [\omega_{ij}] = \Sigma^{-1}$ 为精度矩阵

### 方法3: Graphical Lasso (主方法)
$$\min_{\Theta} -\log\det(\Theta) + \text{tr}(S\Theta) + \lambda \sum_{i<j} |\theta_{ij}|$$

- λ由BIC选择: $BIC = -\ell(\Theta_\lambda) + \frac{\log n}{2} \cdot \text{df}$
- 结果: 高斯图模型, 边表示条件依赖

### 组间差异检验
- Fisher Z变换: $z = \frac{1}{2}\ln\frac{1+r}{1-r}$
- 差异检验: $z_{\text{diff}} = \frac{z_1 - z_2}{\sqrt{\frac{1}{n_1-3} + \frac{1}{n_2-3}}}$
- Benjamini-Hochberg FDR校正

### 网络分析
- 社区检测: Modularity最大化
- 节点中心性: Strength (加权度)
- 差异网络: 移除不显著边, 标记仅在一组存在的边

### 期望图表
1. 高钾热力图(8×8) + 铅钡热力图(8×8)
2. Graphical Lasso网络图(组对比)
3. 差异网络图(显著不同的边)
4. Fisher Z显著性矩阵

---

## 全局验证计划

| 子问题 | 验证方法 | 成功标准 |
|--------|----------|----------|
| Q1a | OR置信区间, MCA惯量解释 | logistic模型AIC显著优于零模型 |
| Q1b | Bootstrap CI覆盖, 效应量一致性 | 效应量|g|>0.5的组分>3个 |
| Q1c | 留一交叉验证 | 预测区间覆盖实际值≥66% |
| Q2a | 10折CV | AUC > 0.90 |
| Q2b | 多重指标一致性, 删除稳定性 | ARI > 0.7 (层次聚类vs K-means) |
| Q3 | 敏感性分析 | 分类结果在±10%扰动下不变 |
| Q4 | Fisher Z检验 + FDR | 发现≥3个显著差异的组分对 |

---

## 代码执行顺序

```
preprocessing.py     → 清洗, 归一化, 缺失处理
q1_analysis.py       → Q1a MCA+logistic, Q1b 统计+MANOVA, Q1c Bayesian
q2_classification.py → Q2a 比值特征+正则化LR, Q2b 层次聚类+K-means
q3_prediction.py     → Q3 多分类器集成+敏感性
q4_correlation.py    → Q4 Pearson+Graphical Lasso+差异网络
```

每个脚本写入 `code/` 目录, 结果写入 `results/RESULTS_MANIFEST.json`, 图表写入 `figures/`.
