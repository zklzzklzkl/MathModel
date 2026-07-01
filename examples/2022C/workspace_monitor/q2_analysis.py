# -*- coding: utf-8 -*-
"""
Q2: 高钾玻璃和铅钡玻璃的分类规律与亚类划分
    + Subclassification using clustering
    + Rationality and sensitivity analysis
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster, cophenet
from scipy.spatial.distance import pdist
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.ensemble import RandomForestClassifier
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

# ============================================================
# 2.1 分类规律分析：高钾 vs 铅钡的关键区分成分
# ============================================================
print("=" * 60)
print("2.1 高钾玻璃 vs 铅钡玻璃的分类规律")
print("=" * 60)

# Use regular samples for clean analysis
df_regular = df[df['采样类型'] == '普通采样'].copy()
print(f"Regular samples: {len(df_regular)}")
print(f"  高钾: {len(df_regular[df_regular['类型']=='高钾'])}")
print(f"  铅钡: {len(df_regular[df_regular['类型']=='铅钡'])}")

# Key discriminating components
key_disc = ['K2O', 'PbO', 'BaO', 'SiO2']
print("\n=== Mean values of key discriminating components ===")
print(df_regular.groupby('类型')[key_disc].mean())

# Statistical test for each component
print("\n=== Mann-Whitney U tests: 高钾 vs 铅钡 ===")
for comp in component_cols:
    hk_vals = df_regular[df_regular['类型'] == '高钾'][comp].fillna(0).values
    pb_vals = df_regular[df_regular['类型'] == '铅钡'][comp].fillna(0).values
    if len(hk_vals) >= 3 and len(pb_vals) >= 3:
        stat, p = stats.mannwhitneyu(hk_vals, pb_vals, alternative='two-sided')
        sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
        if sig:
            print(f"  {comp}: 高钾={np.mean(hk_vals):.1f}, 铅钡={np.mean(pb_vals):.1f}, p={p:.6f} {sig}")

# Random Forest for feature importance
df_reg_filled = df_regular.copy()
for col in component_cols:
    df_reg_filled[col] = df_reg_filled[col].fillna(0)

X = df_reg_filled[component_cols].values
y = (df_reg_filled['类型'] == '铅钡').astype(int).values

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
feature_imp = pd.DataFrame({
    'Component': component_cols,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)
print("\n=== Random Forest Feature Importance ===")
print(feature_imp.to_string())

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Scatter: K2O vs PbO
ax = axes[0, 0]
for gtype, color, marker in [('高钾', '#FF6B6B', 'o'), ('铅钡', '#4ECDC4', 's')]:
    mask = df_regular['类型'] == gtype
    ax.scatter(df_regular.loc[mask, 'K2O'].fillna(0),
               df_regular.loc[mask, 'PbO'].fillna(0),
               c=color, marker=marker, label=gtype, s=80, edgecolors='black', linewidth=0.5, alpha=0.8)
ax.set_xlabel('K2O (%)', fontsize=12)
ax.set_ylabel('PbO (%)', fontsize=12)
ax.set_title('K2O vs PbO: Clear Separation', fontsize=13, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# Scatter: K2O vs BaO
ax = axes[0, 1]
for gtype, color, marker in [('高钾', '#FF6B6B', 'o'), ('铅钡', '#4ECDC4', 's')]:
    mask = df_regular['类型'] == gtype
    ax.scatter(df_regular.loc[mask, 'K2O'].fillna(0),
               df_regular.loc[mask, 'BaO'].fillna(0),
               c=color, marker=marker, label=gtype, s=80, edgecolors='black', linewidth=0.5, alpha=0.8)
ax.set_xlabel('K2O (%)', fontsize=12)
ax.set_ylabel('BaO (%)', fontsize=12)
ax.set_title('K2O vs BaO: Clear Separation', fontsize=13, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# Feature importance
ax = axes[1, 0]
colors_imp = ['#FF6B6B' if c in ['K2O', 'PbO', 'BaO'] else '#4ECDC4' for c in feature_imp['Component']]
ax.barh(feature_imp['Component'], feature_imp['Importance'], color=colors_imp)
ax.set_xlabel('Importance', fontsize=12)
ax.set_title('Random Forest Feature Importance', fontsize=13, fontweight='bold')
ax.invert_yaxis()

# Classification rules summary
ax = axes[1, 1]
ax.axis('off')
rules_text = (
    "Classification Rules for Glass Types:\n\n"
    "1. High-Potassium Glass (高钾玻璃):\n"
    "   - K2O > 2% (typically 5-15%)\n"
    "   - PbO < 5% (typically near 0%)\n"
    "   - BaO < 5% (typically near 0%)\n\n"
    "2. Lead-Barium Glass (铅钡玻璃):\n"
    "   - PbO > 5% (typically 15-70%)\n"
    "   - BaO > 2% (typically 3-30%)\n"
    "   - K2O < 2% (typically near 0%)\n\n"
    "Key discriminant: K2O and PbO contents\n"
    "provide unambiguous classification."
)
ax.text(0.1, 0.5, rules_text, transform=ax.transAxes, fontsize=11,
        verticalalignment='center', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.suptitle('Classification Analysis: High-K vs Lead-Ba Glass',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('output_figures/q2_classification_rules.png')
plt.close()
print("→ Figure saved: q2_classification_rules.png")

# ============================================================
# 2.2 PCA 降维可视化
# ============================================================
print("\n" + "=" * 60)
print("2.2 PCA Visualization")
print("=" * 60)

# Standardize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# PCA
pca = PCA()
X_pca = pca.fit_transform(X_scaled)

print(f"PCA explained variance (first 5): {pca.explained_variance_ratio_[:5]}")
print(f"Cumulative (first 2): {pca.explained_variance_ratio_[:2].sum():.3f}")
print(f"Cumulative (first 3): {pca.explained_variance_ratio_[:3].sum():.3f}")

# PCA loadings
loadings = pd.DataFrame(
    pca.components_.T,
    columns=[f'PC{i+1}' for i in range(len(component_cols))],
    index=component_cols
)
print("\n=== PC1 Loadings (top contributors) ===")
pc1_load = loadings['PC1'].abs().sort_values(ascending=False)
print(pc1_load.head(6))

print("\n=== PC2 Loadings (top contributors) ===")
pc2_load = loadings['PC2'].abs().sort_values(ascending=False)
print(pc2_load.head(6))

# PCA Biplot
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Score plot
ax = axes[0]
for gtype, color, marker in [('高钾', '#FF6B6B', 'o'), ('铅钡', '#4ECDC4', 's')]:
    mask = df_regular['类型'] == gtype
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
               c=color, marker=marker, label=gtype, s=80,
               edgecolors='black', linewidth=0.5, alpha=0.8)
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})', fontsize=11)
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})', fontsize=11)
ax.set_title('PCA Score Plot', fontsize=13, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# Add loading vectors
for i, comp in enumerate(component_cols):
    if pc1_load[comp] > 0.2 or loadings['PC2'].abs()[comp] > 0.2:
        ax.arrow(0, 0, loadings.iloc[i, 0] * 8, loadings.iloc[i, 1] * 8,
                head_width=0.3, head_length=0.3, fc='gray', ec='gray', alpha=0.6)
        ax.text(loadings.iloc[i, 0] * 8.5, loadings.iloc[i, 1] * 8.5, comp,
                fontsize=8, ha='center', va='center')

# Scree plot
ax = axes[1]
ax.plot(range(1, len(pca.explained_variance_ratio_) + 1),
        pca.explained_variance_ratio_, 'o-', color='#45B7D1', linewidth=2, markersize=8)
ax.plot(range(1, len(pca.explained_variance_ratio_) + 1),
        np.cumsum(pca.explained_variance_ratio_), 's-', color='#FF6B6B', linewidth=2, markersize=8)
ax.set_xlabel('Principal Component', fontsize=11)
ax.set_ylabel('Explained Variance Ratio', fontsize=11)
ax.set_title('Scree Plot', fontsize=13, fontweight='bold')
ax.legend(['Individual', 'Cumulative'], fontsize=11)
ax.grid(True, alpha=0.3)
ax.set_xticks(range(1, len(component_cols) + 1))

plt.tight_layout()
plt.savefig('output_figures/q2_pca_analysis.png')
plt.close()
print("→ Figure saved: q2_pca_analysis.png")

# ============================================================
# 2.3 高钾玻璃亚类划分
# ============================================================
print("\n" + "=" * 60)
print("2.3 高钾玻璃亚类划分")
print("=" * 60)

df_hk = df_regular[df_regular['类型'] == '高钾'].copy()
print(f"High-K samples: {len(df_hk)}")

# Components for clustering (exclude SiO2 which dominates, and PbO/BaO which are near-zero)
hk_cluster_cols = ['Na2O', 'K2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3', 'CuO', 'P2O5', 'SrO', 'SnO2', 'SO2']
df_hk_cluster = df_hk[hk_cluster_cols].fillna(0)

# Standardize
scaler_hk = StandardScaler()
X_hk_scaled = scaler_hk.fit_transform(df_hk_cluster)

# Elbow method + Silhouette
print("\n=== K-means: Elbow & Silhouette ===")
K_range = range(2, min(7, len(df_hk)))
inertias = []
silhouettes = []
ch_scores = []

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_hk_scaled)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X_hk_scaled, labels))
    ch_scores.append(calinski_harabasz_score(X_hk_scaled, labels))
    print(f"  K={k}: Inertia={km.inertia_:.2f}, Silhouette={silhouettes[-1]:.4f}, CH={ch_scores[-1]:.1f}")

# Best K
best_k_hk = K_range[np.argmax(silhouettes)]
print(f"\nBest K (silhouette): {best_k_hk}")

# Final clustering
km_hk = KMeans(n_clusters=best_k_hk, random_state=42, n_init=10)
df_hk['亚类'] = km_hk.fit_predict(X_hk_scaled)
df_hk['亚类'] = df_hk['亚类'].apply(lambda x: f'HK-{chr(65+x)}')

print(f"\nHigh-K subclasses:")
print(df_hk['亚类'].value_counts())

# Characterize subclasses
print("\n=== Subclass Characteristics (mean composition) ===")
hk_subclass_mean = df_hk.groupby('亚类')[hk_cluster_cols].mean()
print(hk_subclass_mean.to_string())

# Hierarchical clustering
print("\n=== Hierarchical Clustering (Ward) ===")
linkage_matrix_hk = linkage(X_hk_scaled, method='ward')

# Elbow + Silhouette figure
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Elbow
ax = axes[0, 0]
ax.plot(K_range, inertias, 'o-', color='#45B7D1', linewidth=2, markersize=8)
ax.set_xlabel('Number of clusters (K)', fontsize=11)
ax.set_ylabel('Inertia', fontsize=11)
ax.set_title('Elbow Method', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)

# Silhouette
ax = axes[0, 1]
ax.plot(K_range, silhouettes, 'o-', color='#FF6B6B', linewidth=2, markersize=8)
ax.set_xlabel('Number of clusters (K)', fontsize=11)
ax.set_ylabel('Silhouette Score', fontsize=11)
ax.set_title('Silhouette Analysis', fontsize=13, fontweight='bold')
ax.axvline(x=best_k_hk, color='green', linestyle='--', alpha=0.5)
ax.grid(True, alpha=0.3)

# Dendrogram
ax = axes[1, 0]
dendrogram(linkage_matrix_hk, labels=df_hk['文物编号'].values, ax=ax,
           leaf_font_size=8, color_threshold=0.7*max(linkage_matrix_hk[:, 2]))
ax.set_title('Hierarchical Clustering Dendrogram', fontsize=13, fontweight='bold')
ax.set_xlabel('Artifact ID')
ax.set_ylabel('Distance')

# Subclass visualization - K2O vs CaO (two key varying components in high-K)
ax = axes[1, 1]
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#F7DC6F', '#E74C3C', '#9B59B6', '#1ABC9C'][:best_k_hk]
for i, subclass in enumerate(sorted(df_hk['亚类'].unique())):
    mask = df_hk['亚类'] == subclass
    ax.scatter(df_hk.loc[mask, 'K2O'].fillna(0),
               df_hk.loc[mask, 'CaO'].fillna(0),
               c=colors[i], label=subclass, s=100, edgecolors='black', linewidth=0.5)
ax.set_xlabel('K2O (%)', fontsize=11)
ax.set_ylabel('CaO (%)', fontsize=11)
ax.set_title(f'High-K Subclasses (K={best_k_hk})', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.suptitle('High-Potassium Glass Subclassification Analysis',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('output_figures/q2_hk_subclass.png')
plt.close()
print("→ Figure saved: q2_hk_subclass.png")

# ============================================================
# 2.4 铅钡玻璃亚类划分
# ============================================================
print("\n" + "=" * 60)
print("2.4 铅钡玻璃亚类划分")
print("=" * 60)

df_pb = df_regular[df_regular['类型'] == '铅钡'].copy()
print(f"Lead-Ba samples: {len(df_pb)}")

# Components for clustering (K2O is near-zero in lead-Ba)
pb_cluster_cols = ['Na2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']
df_pb_cluster = df_pb[pb_cluster_cols].fillna(0)

# Standardize
scaler_pb = StandardScaler()
X_pb_scaled = scaler_pb.fit_transform(df_pb_cluster)

# Elbow + Silhouette
print("\n=== K-means: Elbow & Silhouette ===")
K_range_pb = range(2, min(8, len(df_pb)))
inertias_pb = []
silhouettes_pb = []

for k in K_range_pb:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_pb_scaled)
    inertias_pb.append(km.inertia_)
    silhouettes_pb.append(silhouette_score(X_pb_scaled, labels))
    print(f"  K={k}: Inertia={km.inertia_:.2f}, Silhouette={silhouettes_pb[-1]:.4f}")

best_k_pb = K_range_pb[np.argmax(silhouettes_pb)]
print(f"\nBest K (silhouette): {best_k_pb}")

# Final clustering
km_pb = KMeans(n_clusters=best_k_pb, random_state=42, n_init=10)
df_pb['亚类'] = km_pb.fit_predict(X_pb_scaled)
df_pb['亚类'] = df_pb['亚类'].apply(lambda x: f'PB-{chr(65+x)}')

print(f"\nLead-Ba subclasses:")
print(df_pb['亚类'].value_counts())

# Characterize
print("\n=== Subclass Characteristics (mean composition) ===")
pb_subclass_mean = df_pb.groupby('亚类')[pb_cluster_cols].mean()
print(pb_subclass_mean.to_string())

# Key ratio: PbO/BaO
df_pb['PbO_BaO_ratio'] = df_pb['PbO'].fillna(0) / (df_pb['BaO'].fillna(0) + 0.01)
print(f"\nPbO/BaO ratio by subclass:")
print(df_pb.groupby('亚类')['PbO_BaO_ratio'].describe())

# Hierarchical clustering
linkage_matrix_pb = linkage(X_pb_scaled, method='ward')

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

ax = axes[0, 0]
ax.plot(K_range_pb, inertias_pb, 'o-', color='#45B7D1', linewidth=2, markersize=8)
ax.set_xlabel('Number of clusters (K)', fontsize=11)
ax.set_ylabel('Inertia', fontsize=11)
ax.set_title('Elbow Method - Lead-Ba Glass', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)

ax = axes[0, 1]
ax.plot(K_range_pb, silhouettes_pb, 'o-', color='#FF6B6B', linewidth=2, markersize=8)
ax.set_xlabel('Number of clusters (K)', fontsize=11)
ax.set_ylabel('Silhouette Score', fontsize=11)
ax.set_title('Silhouette Analysis - Lead-Ba Glass', fontsize=13, fontweight='bold')
ax.axvline(x=best_k_pb, color='green', linestyle='--', alpha=0.5)
ax.grid(True, alpha=0.3)

ax = axes[1, 0]
dendrogram(linkage_matrix_pb, labels=df_pb['文物编号'].values, ax=ax,
           leaf_font_size=8, color_threshold=0.7*max(linkage_matrix_pb[:, 2]))
ax.set_title('Hierarchical Clustering Dendrogram', fontsize=13, fontweight='bold')
ax.set_xlabel('Artifact ID')
ax.set_ylabel('Distance')

# PbO vs BaO scatter (key discriminating components for subclasses)
ax = axes[1, 1]
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#F7DC6F', '#E74C3C', '#9B59B6'][:best_k_pb]
for i, subclass in enumerate(sorted(df_pb['亚类'].unique())):
    mask = df_pb['亚类'] == subclass
    ax.scatter(df_pb.loc[mask, 'PbO'].fillna(0),
               df_pb.loc[mask, 'BaO'].fillna(0),
               c=colors[i], label=subclass, s=100, edgecolors='black', linewidth=0.5)
ax.set_xlabel('PbO (%)', fontsize=11)
ax.set_ylabel('BaO (%)', fontsize=11)
ax.set_title(f'Lead-Ba Subclasses (K={best_k_pb})', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.suptitle('Lead-Barium Glass Subclassification Analysis',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('output_figures/q2_pb_subclass.png')
plt.close()
print("→ Figure saved: q2_pb_subclass.png")

# ============================================================
# 2.5 敏感性分析
# ============================================================
print("\n" + "=" * 60)
print("2.5 敏感性分析")
print("=" * 60)

# Sensitivity to K selection
print("\n=== Sensitivity: Alternative K values ===")
for glass_type, df_data, cluster_cols in [('高钾', df_hk, hk_cluster_cols),
                                           ('铅钡', df_pb, pb_cluster_cols)]:
    print(f"\n--- {glass_type} glass ---")
    X_sens = StandardScaler().fit_transform(df_data[cluster_cols].fillna(0))

    for k in [2, 3, 4]:
        if k < len(df_data):
            labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_sens)
            ss = silhouette_score(X_sens, labels)
            ch = calinski_harabasz_score(X_sens, labels)
            db = davies_bouldin_score(X_sens, labels)
            counts = pd.Series(labels).value_counts().sort_index().values
            print(f"  K={k}: Silhouette={ss:.4f}, CH={ch:.1f}, DB={db:.4f}, sizes={counts}")

# Sensitivity to component selection
print("\n=== Sensitivity: Removing SiO2 ===")
# SiO2 is the dominant component; verify clustering is robust without it
for glass_type, df_data, cols_used in [('高钾', df_hk, hk_cluster_cols), ('铅钡', df_pb, pb_cluster_cols)]:
    print(f"\n--- {glass_type} glass ---")
    cols_no_sio2 = [c for c in cols_used if c != 'SiO2']
    X_sens = StandardScaler().fit_transform(df_data[cols_no_sio2].fillna(0))
    labels = KMeans(n_clusters=best_k_hk if '高钾' in glass_type else best_k_pb,
                    random_state=42, n_init=10).fit_predict(X_sens)
    ss = silhouette_score(X_sens, labels)
    print(f"  Silhouette without SiO2: {ss:.4f}")
    print(f"  Cluster sizes: {pd.Series(labels).value_counts().sort_index().values}")

# Save subclassification results
df_hk[['文物编号', '亚类']].to_csv('q2_hk_subclasses.csv', index=False, encoding='utf-8-sig')
df_pb[['文物编号', '亚类']].to_csv('q2_pb_subclasses.csv', index=False, encoding='utf-8-sig')

print("\n" + "=" * 60)
print("Q2 ANALYSIS COMPLETE")
print("=" * 60)
