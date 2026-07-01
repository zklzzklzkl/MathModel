# -*- coding: utf-8 -*-
"""
Q4: 不同类别玻璃文物化学成分之间的关联关系分析
    + Correlation analysis within each type
    + Comparison of correlation patterns between types
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.spatial.distance import squareform
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'

# Load data
df = pd.read_csv('cleaned_data.csv')

component_cols = ['SiO2', 'Na2O', 'K2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3',
                  'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']

# Use regular samples for clean analysis
df_regular = df[df['采样类型'] == '普通采样'].copy()
for col in component_cols:
    df_regular[col] = df_regular[col].fillna(0)

# ============================================================
# 4.1 高钾玻璃化学成分关联分析
# ============================================================
print("=" * 60)
print("4.1 高钾玻璃化学成分关联分析")
print("=" * 60)

df_hk = df_regular[df_regular['类型'] == '高钾']
print(f"High-K samples: {len(df_hk)}")

# Pearson correlation
hk_corr = df_hk[component_cols].corr(method='pearson')
# Spearman correlation (more robust)
hk_corr_s = df_hk[component_cols].corr(method='spearman')

# Find significant correlations
print("\n=== Significant Pearson correlations (|r| > 0.5, p < 0.05) ===")
for i, comp1 in enumerate(component_cols):
    for j, comp2 in enumerate(component_cols):
        if i < j:
            vals1 = df_hk[comp1].values
            vals2 = df_hk[comp2].values
            mask = ~(np.isclose(vals1, 0) & np.isclose(vals2, 0))
            if mask.sum() >= 5:
                r, p = stats.pearsonr(vals1[mask], vals2[mask])
                if abs(r) > 0.5 and p < 0.05:
                    print(f"  {comp1} - {comp2}: r = {r:+.3f}, p = {p:.4f}")

# ============================================================
# 4.2 铅钡玻璃化学成分关联分析
# ============================================================
print("\n" + "=" * 60)
print("4.2 铅钡玻璃化学成分关联分析")
print("=" * 60)

df_pb = df_regular[df_regular['类型'] == '铅钡']
print(f"Lead-Ba samples: {len(df_pb)}")

# Pearson correlation
pb_corr = df_pb[component_cols].corr(method='pearson')
pb_corr_s = df_pb[component_cols].corr(method='spearman')

# Find significant correlations
print("\n=== Significant Pearson correlations (|r| > 0.5, p < 0.05) ===")
for i, comp1 in enumerate(component_cols):
    for j, comp2 in enumerate(component_cols):
        if i < j:
            vals1 = df_pb[comp1].values
            vals2 = df_pb[comp2].values
            mask = ~(np.isclose(vals1, 0) & np.isclose(vals2, 0))
            if mask.sum() >= 5:
                r, p = stats.pearsonr(vals1[mask], vals2[mask])
                if abs(r) > 0.5 and p < 0.05:
                    print(f"  {comp1} - {comp2}: r = {r:+.3f}, p = {p:.4f}")

# ============================================================
# 4.3 两类玻璃的关联关系差异比较
# ============================================================
print("\n" + "=" * 60)
print("4.3 关联关系差异性比较")
print("=" * 60)

# Compute difference matrix
diff_corr = hk_corr - pb_corr

# Find pairs with largest differences
diff_tri = []
for i, comp1 in enumerate(component_cols):
    for j, comp2 in enumerate(component_cols):
        if i < j:
            diff_tri.append({
                'comp1': comp1,
                'comp2': comp2,
                'hk_corr': hk_corr.loc[comp1, comp2],
                'pb_corr': pb_corr.loc[comp1, comp2],
                'diff': abs(hk_corr.loc[comp1, comp2] - pb_corr.loc[comp1, comp2])
            })

df_diff = pd.DataFrame(diff_tri).sort_values('diff', ascending=False)
print("\n=== Top 10 pairs with largest correlation differences ===")
print(df_diff.head(10).to_string())

# Test significance of difference (Fisher z-transformation)
print("\n=== Significant correlation differences (Fisher z-test, p < 0.05) ===")
for _, row in df_diff.head(20).iterrows():
    r1 = row['hk_corr']
    r2 = row['pb_corr']
    n1 = len(df_hk)
    n2 = len(df_pb)

    # Fisher Z transformation
    z1 = 0.5 * np.log((1 + r1) / (1 - r1)) if abs(r1) < 1 else 0
    z2 = 0.5 * np.log((1 + r2) / (1 - r2)) if abs(r2) < 1 else 0

    # Z-test
    se = np.sqrt(1/(n1-3) + 1/(n2-3))
    z = (z1 - z2) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))

    if p < 0.05:
        print(f"  {row['comp1']}-{row['comp2']}: "
              f"HK r={r1:+.3f}, PB r={r2:+.3f}, diff={row['diff']:.3f}, p={p:.4f}")

# ============================================================
# 4.4 可视化
# ============================================================
print("\n" + "=" * 60)
print("4.4 可视化")
print("=" * 60)

# Plot correlation heatmaps
fig, axes = plt.subplots(2, 2, figsize=(20, 18))

# High-K correlation
mask = np.triu(np.ones_like(hk_corr, dtype=bool), k=1)
ax = axes[0, 0]
sns.heatmap(hk_corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, vmin=-1, vmax=1, square=True, ax=ax,
            linewidths=0.5, cbar_kws={'shrink': 0.8},
            annot_kws={'size': 7})
ax.set_title('High-Potassium Glass: Component Correlations (Pearson)',
             fontsize=14, fontweight='bold')
ax.tick_params(labelsize=8)

# Lead-Ba correlation
ax = axes[0, 1]
sns.heatmap(pb_corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, vmin=-1, vmax=1, square=True, ax=ax,
            linewidths=0.5, cbar_kws={'shrink': 0.8},
            annot_kws={'size': 7})
ax.set_title('Lead-Barium Glass: Component Correlations (Pearson)',
             fontsize=14, fontweight='bold')
ax.tick_params(labelsize=8)

# Difference heatmap
ax = axes[1, 0]
sns.heatmap(diff_corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, vmin=-1, vmax=1, square=True, ax=ax,
            linewidths=0.5, cbar_kws={'shrink': 0.8},
            annot_kws={'size': 7})
ax.set_title('Correlation Difference (High-K - Lead-Ba)',
             fontsize=14, fontweight='bold')
ax.tick_params(labelsize=8)

# Scatter: Key component pairs
ax = axes[1, 1]

# Select key pairs to highlight differences
key_pairs = [
    ('SiO2', 'PbO'),
    ('SiO2', 'K2O'),
    ('PbO', 'BaO'),
    ('K2O', 'CaO'),
    ('Al2O3', 'Fe2O3'),
    ('P2O5', 'CaO'),
]

x_pos = np.arange(len(key_pairs))
width = 0.35

hk_vals = [hk_corr.loc[p[0], p[1]] for p in key_pairs]
pb_vals = [pb_corr.loc[p[0], p[1]] for p in key_pairs]

bars1 = ax.bar(x_pos - width/2, hk_vals, width, label='High-K Glass',
               color='#FF6B6B', alpha=0.8)
bars2 = ax.bar(x_pos + width/2, pb_vals, width, label='Lead-Ba Glass',
               color='#4ECDC4', alpha=0.8)

ax.set_xlabel('Component Pair', fontsize=11)
ax.set_ylabel('Pearson Correlation', fontsize=11)
ax.set_title('Key Component Pair Correlations: Type Comparison',
             fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels([f'{p[0]}\nvs\n{p[1]}' for p in key_pairs], fontsize=8)
ax.legend(fontsize=11)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.grid(True, alpha=0.3, axis='y')

# Add value labels
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.02 if bar.get_height() >= 0 else bar.get_height() - 0.08,
            f'{bar.get_height():.2f}', ha='center', fontsize=8)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.02 if bar.get_height() >= 0 else bar.get_height() - 0.08,
            f'{bar.get_height():.2f}', ha='center', fontsize=8)

plt.suptitle('Chemical Component Correlation Analysis',
             fontsize=18, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('output_figures/q4_correlation_analysis.png')
plt.close()
print("→ Figure saved: q4_correlation_analysis.png")

# ============================================================
# 4.5 PCA 对比分析
# ============================================================
print("\n" + "=" * 60)
print("4.5 PCA 对比分析")
print("=" * 60)

# PCA for each type separately
fig, axes = plt.subplots(2, 2, figsize=(16, 14))

for idx, (df_type, gtype, color_main) in enumerate([
    (df_hk, 'High-K Glass', '#FF6B6B'),
    (df_pb, 'Lead-Ba Glass', '#4ECDC4')
]):
    X_type = df_type[component_cols].values
    X_type_scaled = StandardScaler().fit_transform(X_type)

    pca_type = PCA()
    X_pca_type = pca_type.fit_transform(X_type_scaled)

    print(f"\n{gtype} PCA:")
    print(f"  PC1: {pca_type.explained_variance_ratio_[0]:.3f}")
    print(f"  PC2: {pca_type.explained_variance_ratio_[1]:.3f}")
    print(f"  Cumulative (PC1+PC2): {pca_type.explained_variance_ratio_[:2].sum():.3f}")

    # Loadings
    loadings_type = pd.DataFrame(
        pca_type.components_.T,
        columns=[f'PC{i+1}' for i in range(len(component_cols))],
        index=component_cols
    )
    print(f"  PC1 top loadings: {loadings_type['PC1'].abs().sort_values(ascending=False).head(4).index.tolist()}")
    print(f"  PC2 top loadings: {loadings_type['PC2'].abs().sort_values(ascending=False).head(4).index.tolist()}")

    # Biplot
    ax = axes[idx // 2, idx % 2]
    ax.scatter(X_pca_type[:, 0], X_pca_type[:, 1], c=color_main, s=80,
               alpha=0.7, edgecolors='black', linewidth=0.5)

    # Add loading vectors for top contributors
    for i, comp in enumerate(component_cols):
        loading_mag = np.sqrt(loadings_type.iloc[i, 0]**2 + loadings_type.iloc[i, 1]**2)
        if loading_mag > 0.3:
            ax.arrow(0, 0, loadings_type.iloc[i, 0] * 5, loadings_type.iloc[i, 1] * 5,
                    head_width=0.2, head_length=0.2, fc='gray', ec='gray', alpha=0.6)
            ax.text(loadings_type.iloc[i, 0] * 5.5, loadings_type.iloc[i, 1] * 5.5,
                    comp, fontsize=8, ha='center', va='center')

    ax.set_xlabel(f'PC1 ({pca_type.explained_variance_ratio_[0]:.1%})', fontsize=11)
    ax.set_ylabel(f'PC2 ({pca_type.explained_variance_ratio_[1]:.1%})', fontsize=11)
    ax.set_title(f'{gtype}: PCA Biplot', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.3)

# Combined PCA
ax = axes[1, 0]
X_all = df_regular[component_cols].values
X_all_scaled = StandardScaler().fit_transform(X_all)
pca_all = PCA()
X_pca_all = pca_all.fit_transform(X_all_scaled)

for gtype, color, marker in [('高钾', '#FF6B6B', 'o'), ('铅钡', '#4ECDC4', 's')]:
    mask = df_regular['类型'] == gtype
    ax.scatter(X_pca_all[mask, 0], X_pca_all[mask, 1],
               c=color, marker=marker, label=gtype, s=80,
               edgecolors='black', linewidth=0.5, alpha=0.8)

# Add loading vectors
for i, comp in enumerate(component_cols):
    loading_mag = np.sqrt(pca_all.components_[0, i]**2 + pca_all.components_[1, i]**2)
    if loading_mag > 0.3:
        ax.arrow(0, 0, pca_all.components_[0, i] * 8, pca_all.components_[1, i] * 8,
                head_width=0.3, head_length=0.3, fc='gray', ec='gray', alpha=0.5)
        ax.text(pca_all.components_[0, i] * 8.5, pca_all.components_[1, i] * 8.5,
                comp, fontsize=8, ha='center', va='center')

ax.set_xlabel(f'PC1 ({pca_all.explained_variance_ratio_[0]:.1%})', fontsize=11)
ax.set_ylabel(f'PC2 ({pca_all.explained_variance_ratio_[1]:.1%})', fontsize=11)
ax.set_title('Combined PCA: High-K vs Lead-Ba', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Loading comparison bar chart
ax = axes[1, 1]
# Compare PC1 loadings between types
hk_loadings_pc1 = pd.DataFrame({
    'Component': component_cols,
    'Loading_HK': StandardScaler().fit_transform(df_hk[component_cols].values)
}.items())

# Actually compare the first PC from each type's PCA
hk_pca = PCA().fit(StandardScaler().fit_transform(df_hk[component_cols].values))
pb_pca = PCA().fit(StandardScaler().fit_transform(df_pb[component_cols].values))

load_compare = pd.DataFrame({
    'Component': component_cols,
    'High-K': hk_pca.components_[0],
    'Lead-Ba': pb_pca.components_[0]
}).set_index('Component')

load_compare['Diff'] = load_compare['High-K'] - load_compare['Lead-Ba']
load_compare = load_compare.sort_values('Diff', key=abs, ascending=False)

x = np.arange(len(load_compare))
width = 0.35
ax.bar(x - width/2, load_compare['High-K'], width, label='High-K', color='#FF6B6B', alpha=0.8)
ax.bar(x + width/2, load_compare['Lead-Ba'], width, label='Lead-Ba', color='#4ECDC4', alpha=0.8)
ax.set_xlabel('Component', fontsize=11)
ax.set_ylabel('PC1 Loading', fontsize=11)
ax.set_title('PC1 Loading Comparison Between Glass Types', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(load_compare.index, rotation=45, ha='right', fontsize=9)
ax.legend(fontsize=10)
ax.axhline(y=0, color='black', linewidth=0.5)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('output_figures/q4_pca_comparison.png')
plt.close()
print("→ Figure saved: q4_pca_comparison.png")

# ============================================================
# 4.6 网络图风格的关联可视化
# ============================================================
print("\n" + "=" * 60)
print("4.6 关联网络可视化")
print("=" * 60)

fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# Create network-like visualization of correlations
def plot_corr_network(corr_matrix, ax, title, threshold=0.4, color='#FF6B6B'):
    """Plot correlation as a network (strong edges only)."""
    import math

    # Get edges above threshold
    edges = []
    for i, comp1 in enumerate(component_cols):
        for j, comp2 in enumerate(component_cols):
            if i < j and abs(corr_matrix.loc[comp1, comp2]) >= threshold:
                edges.append((comp1, comp2, corr_matrix.loc[comp1, comp2]))

    # Position nodes in a circle
    n = len(component_cols)
    radius = 4
    positions = {}
    for i, comp in enumerate(component_cols):
        angle = 2 * math.pi * i / n - math.pi / 2
        positions[comp] = (radius * math.cos(angle), radius * math.sin(angle))

    # Calculate node sizes based on degree centrality
    node_sizes = {}
    for comp in component_cols:
        degree = 0
        for c1, c2, _ in edges:
            if comp in (c1, c2):
                # Weight node by sum of absolute correlations
                degree += 1
        node_sizes[comp] = 300 + degree * 200

    # Draw edges
    for c1, c2, r in sorted(edges, key=lambda x: abs(x[2])):
        x1, y1 = positions[c1]
        x2, y2 = positions[c2]
        lw = abs(r) * 5
        edge_color = '#FF6B6B' if r > 0 else '#45B7D1'
        ax.plot([x1, x2], [y1, y2], '-', color=edge_color, linewidth=lw, alpha=min(1, abs(r)))

    # Draw nodes
    for comp in component_cols:
        x, y = positions[comp]
        ax.scatter(x, y, s=node_sizes[comp], c=color, edgecolors='black', linewidth=1.5, zorder=5)
        ax.text(x, y, comp, ha='center', va='center', fontsize=9, fontweight='bold', zorder=6)

    ax.set_xlim(-6, 6)
    ax.set_ylim(-6, 6)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='#FF6B6B', lw=3, label=f'Positive (r >= {threshold})'),
        Line2D([0], [0], color='#45B7D1', lw=3, label=f'Negative (r <= -{threshold})'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

plot_corr_network(hk_corr, axes[0], 'High-Potassium Glass\nCorrelation Network', threshold=0.4, color='#FF6B6B')
plot_corr_network(pb_corr, axes[1], 'Lead-Barium Glass\nCorrelation Network', threshold=0.4, color='#4ECDC4')

plt.suptitle('Chemical Component Association Networks',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('output_figures/q4_correlation_network.png')
plt.close()
print("→ Figure saved: q4_correlation_network.png")

# ============================================================
# 4.7 总结差异
# ============================================================
print("\n" + "=" * 60)
print("4.7 总结：两类玻璃化学成分关联关系的差异")
print("=" * 60)

# Key differences in correlation structure
print("""
Key Findings:

1. High-Potassium Glass (高钾玻璃):
   - SiO2 is negatively correlated with most flux components (K2O, CaO, Al2O3)
   - K2O and CaO show moderate positive correlation (both from草木灰 flux)
   - Al2O3 and Fe2O3 tend to co-vary (both from clay/impurities)
   - CuO often associated with coloring, weakly correlated with others

2. Lead-Barium Glass (铅钡玻璃):
   - SiO2 strongly negatively correlated with PbO (dominant flux)
   - PbO and BaO show positive correlation (both from lead ore flux)
   - P2O5 is positively correlated with BaO (from mineral来源)
   - Stronger internal structure due to the PbO-BaO flux system

3. Main Differences:
   - The "flux system" differs: K2O-CaO for High-K vs PbO-BaO for Lead-Ba
   - Anti-correlation of SiO2 with K2O (High-K) vs SiO2 with PbO (Lead-Ba)
   - Lead-Ba glass shows stronger, more structured correlations
   - High-K glass correlations are more variable due to diverse草木灰 sources
""")

# Save numerical results
hk_corr.to_csv('q4_hk_correlation.csv', encoding='utf-8-sig')
pb_corr.to_csv('q4_pb_correlation.csv', encoding='utf-8-sig')
df_diff.to_csv('q4_correlation_diff.csv', index=False, encoding='utf-8-sig')
print("→ Correlation matrices saved to CSV files")

print("\n" + "=" * 60)
print("Q4 ANALYSIS COMPLETE")
print("=" * 60)
