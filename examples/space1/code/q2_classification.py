#!/usr/bin/env python3
"""q2_classification.py - Q2a(分类规律) + Q2b(亚类划分)"""
import os, json, sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, silhouette_score, davies_bouldin_score, adjusted_rand_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

WORKSPACE = r'D:\WorkSpace_MathModel\space1'
os.makedirs(f'{WORKSPACE}/figures', exist_ok=True)
os.makedirs(f'{WORKSPACE}/results', exist_ok=True)

# Load data
df2 = pd.read_csv(f'{WORKSPACE}/code/outputs/form2_processed.csv')
with open(f'{WORKSPACE}/code/outputs/metadata.json') as f:
    meta = json.load(f)
comp_cols = meta['comp_cols_11']
norm_cols = [f'{c}_norm' for c in comp_cols]
comp_short = [c.split('(')[0] for c in comp_cols]

# Filter valid, merge with type
df2_valid = df2[df2['_valid'] == True].dropna(subset=['类型']).copy()
print(f"Q2 analysis: {len(df2_valid)} samples, {df2_valid['类型'].value_counts().to_dict()}")

# Prepare feature matrix
# Fill missing values with column median (by type group)
X_norm_full = np.zeros((len(df2_valid), len(norm_cols)))
idx_counter = 0
for _, row in df2_valid.iterrows():
    for i, nc in enumerate(norm_cols):
        val = row[nc] if pd.notna(row[nc]) else None
        if val is None:
            t = row['类型']
            med = df2_valid.loc[df2_valid['类型'] == t, nc].median()
            if pd.isna(med):
                med = df2_valid[nc].median()
            val = med
        X_norm_full[idx_counter, i] = val
    idx_counter += 1

y = (df2_valid['类型'] == '铅钡').astype(int).values

# ============================================================
# Q2a: Classification
# ============================================================
print("\n" + "="*60)
print("Q2a: Classification Rules for 高钾 vs 铅钡")
print("="*60)

# 1. Ratio features
ratios = []
labels_r = []
rho_pb_si = []
rho_ba_k = []
for idx_counter in range(len(df2_valid)):
    idx = idx_counter
    sio2 = X_norm_full[idx, 0]
    k2o = X_norm_full[idx, 1]
    cao = X_norm_full[idx, 2]
    al2o3 = X_norm_full[idx, 4]
    pbo = X_norm_full[idx, 7]
    bao = X_norm_full[idx, 8]
    r = [
        pbo / max(sio2, 0.01),
        bao / max(k2o, 0.01) if k2o > 0.01 else 0,
        (pbo + bao) / max(sio2, 0.01),
        k2o / max(sio2, 0.01),
        al2o3 / max(cao, 0.01) if cao > 0.01 else 0
    ]
    ratios.append(r)
    rho_pb_si.append(r[0])
    rho_ba_k.append(r[1])

X_ratios = np.array(ratios)
ratio_names = ['PbO/SiO2', 'BaO/K2O', '(PbO+BaO)/SiO2', 'K2O/SiO2', 'Al2O3/CaO']

# -- Simple threshold rule --
print("\nSimple threshold classification:")
for rn, ri in zip(ratio_names, range(5)):
    vals_gaok = [X_ratios[i, ri] for i in range(len(y)) if y[i] == 0]
    vals_qb = [X_ratios[i, ri] for i in range(len(y)) if y[i] == 1]
    print(f"  {rn:20s}: 高钾={np.mean(vals_gaok):.4f}±{np.std(vals_gaok):.4f}, 铅钡={np.mean(vals_qb):.4f}±{np.std(vals_qb):.4f}")

# -- L1-regularized Logistic Regression (main method) --
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_ratios)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

lr_l1 = LogisticRegression(penalty='l1', solver='saga', C=0.5, max_iter=2000, random_state=42)
cv_scores = cross_val_score(lr_l1, X_scaled, y, cv=skf, scoring='accuracy')
lr_l1.fit(X_scaled, y)

print(f"\nL1-Logistic Regression 5-fold CV accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
print(f"Non-zero coefficients (selected features):")
for i, (rn, coef) in enumerate(zip(ratio_names, lr_l1.coef_[0])):
    if abs(coef) > 1e-5:
        print(f"  {rn}: β={coef:.4f}")

# -- LDA comparison --
lda = LinearDiscriminantAnalysis()
cv_lda = cross_val_score(lda, X_scaled, y, cv=skf, scoring='accuracy')
lda.fit(X_scaled, y)
print(f"\nLDA 5-fold CV accuracy: {cv_lda.mean():.3f} ± {cv_lda.std():.3f}")

# -- PCA visualization --
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
print(f"PCA explained variance: {pca.explained_variance_ratio_}")

# --- FIGURE F4.1: Ratio scatter matrix ---
fig, axes = plt.subplots(2, 3, figsize=(14, 9))
axes = axes.flatten()
key_pairs = [(0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 4)]
for ax, (i, j) in zip(axes, key_pairs):
    ax.scatter(X_ratios[y==0, i], X_ratios[y==0, j], c='#2196F3', alpha=0.6, s=30, label='高钾')
    ax.scatter(X_ratios[y==1, i], X_ratios[y==1, j], c='#FF9800', alpha=0.6, s=30, label='铅钡')
    ax.set_xlabel(ratio_names[i], fontsize=8)
    ax.set_ylabel(ratio_names[j], fontsize=8)
    ax.legend(fontsize=7)
axes[-1].set_visible(False)
fig.suptitle('Q2a: Key Ratio Scatter Matrix', fontsize=14)
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q2a_ratio_scatter.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F4.1] Saved q2a_ratio_scatter.pdf")

# --- FIGURE F4.2: PCA decision boundary ---
fig, ax = plt.subplots(figsize=(8, 6))
# Create mesh
h = 0.1
x_min, x_max = X_pca[:, 0].min() - 1, X_pca[:, 0].max() + 1
y_min, y_max = X_pca[:, 1].min() - 1, X_pca[:, 1].max() + 1
xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
# Fit LDA on PCA space
lda_pca = LinearDiscriminantAnalysis()
lda_pca.fit(X_pca, y)
Z = lda_pca.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)
ax.contourf(xx, yy, Z, alpha=0.2, cmap='RdYlBu')
ax.scatter(X_pca[y==0, 0], X_pca[y==0, 1], c='#2196F3', edgecolors='k', s=50, label='高钾')
ax.scatter(X_pca[y==1, 0], X_pca[y==1, 1], c='#FF9800', edgecolors='k', s=50, label='铅钡')
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
ax.set_title('Q2a: PCA Projection with LDA Decision Boundary')
ax.legend()
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q2a_decision_boundary.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F4.2] Saved q2a_decision_boundary.pdf")

# --- FIGURE F4.3: ROC ---
from sklearn.metrics import RocCurveDisplay
fig, ax = plt.subplots(figsize=(6, 5))
for name, model in [('L1-LR', lr_l1), ('LDA', lda)]:
    skf2 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    tprs, aucs = [], []
    for train, test in skf2.split(X_scaled, y):
        model.fit(X_scaled[train], y[train])
        y_prob = model.predict_proba(X_scaled[test])[:, 1] if hasattr(model, 'predict_proba') else model.decision_function(X_scaled[test])
        auc = roc_auc_score(y[test], y_prob)
        aucs.append(auc)
    print(f"  {name} mean AUC: {np.mean(aucs):.3f} ± {np.std(aucs):.3f}")

RocCurveDisplay.from_estimator(lr_l1, X_scaled, y, ax=ax, name=f'L1-LR (AUC={roc_auc_score(y, lr_l1.predict_proba(X_scaled)[:,1]):.3f})')
RocCurveDisplay.from_estimator(lda, X_scaled, y, ax=ax, name=f'LDA (AUC={roc_auc_score(y, lda.predict_proba(X_scaled)[:,1]):.3f})')
ax.plot([0, 1], [0, 1], 'k--', linewidth=0.8)
ax.set_title('Q2a: ROC Curves')
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q2a_roc.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F4.3] Saved q2a_roc.pdf")

# ============================================================
# Q2b: Sub-classification
# ============================================================
print("\n" + "="*60)
print("Q2b: Sub-classification")
print("="*60)

for glass_type, type_label in [('高钾', 0), ('铅钡', 1)]:
    mask = y == type_label
    X_type = X_scaled[mask]
    n_type = X_type.shape[0]
    print(f"\n{glass_type} glass: n={n_type}")

    # PCA for visualization
    pca_sub = PCA(n_components=min(3, n_type-1))
    X_pca_sub = pca_sub.fit_transform(X_type)
    print(f"  PCA explained variance: {pca_sub.explained_variance_ratio_}")

    # --- Hierarchical clustering (Ward) ---
    Z = linkage(X_type, method='ward')

    # Gap statistic simulation (simplified)
    ks = range(1, min(6, n_type))
    inertias = []
    for k in ks:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_type)
        inertias.append(km.inertia_)

    # Silhouette for k=2,3,4
    sil_scores = {}
    for k in [2, 3, 4]:
        if k <= n_type - 1:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X_type)
            sil_scores[k] = silhouette_score(X_type, labels)
            print(f"  k={k}: Silhouette={sil_scores[k]:.3f}")

    # Select best k
    if sil_scores:
        best_k = max(sil_scores, key=sil_scores.get)
        print(f"  Best k = {best_k} (Silhouette={sil_scores[best_k]:.3f})")

        # Final clustering with best k
        km_best = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels_best = km_best.fit_predict(X_type)

        # Hierarchical clustering labels for comparison
        hc_labels = fcluster(Z, best_k, criterion='maxclust')
        ari = adjusted_rand_score(labels_best, hc_labels)
        print(f"  ARI (K-means vs Hierarchical): {ari:.3f}")

        # Sub-class statistics
        for kk in range(best_k):
            sub_mask = labels_best == kk
            n_sub = sub_mask.sum()
            print(f"  Sub-class {kk+1}: n={n_sub}")
            for ci, cn in enumerate(ratio_names[:4]):
                print(f"    {cn}: {X_type[sub_mask, ci].mean():.4f} ± {X_type[sub_mask, ci].std():.4f}")

    # --- FIGURE: Dendrogram ---
    fig, ax = plt.subplots(figsize=(10, 5))
    dendrogram(Z, ax=ax, leaf_font_size=8, color_threshold=0.7*max(Z[:,2]))
    ax.set_title(f'Q2b: Hierarchical Clustering Dendrogram ({glass_type})')
    ax.set_xlabel('Sample Index')
    ax.set_ylabel('Ward Distance')
    plt.tight_layout()
    fname = f'q2b_dendro_{"gaok" if type_label==0 else "qianbei"}.pdf'
    fig.savefig(f'{WORKSPACE}/figures/{fname}', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [F5.{1 if type_label==0 else 2}] Saved {fname}")

    # --- FIGURE: PCA with clusters ---
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#2196F3', '#FF9800', '#4CAF50', '#E91E63']
    if sil_scores:
        for kk in range(best_k):
            mask_kk = labels_best == kk
            ax.scatter(X_pca_sub[mask_kk, 0], X_pca_sub[mask_kk, 1],
                      c=[colors[kk % 4]], s=60, edgecolors='k', label=f'Sub-class {kk+1}')
    else:
        ax.scatter(X_pca_sub[:, 0], X_pca_sub[:, 1], c='#2196F3', s=60, edgecolors='k')

    ax.set_xlabel(f'PC1 ({pca_sub.explained_variance_ratio_[0]:.1%})')
    ax.set_ylabel(f'PC2 ({pca_sub.explained_variance_ratio_[1]:.1%})' if pca_sub.explained_variance_ratio_.shape[0] > 1 else '')
    ax.set_title(f'Q2b: PCA Projection with Sub-classes ({glass_type})')
    ax.legend(fontsize=8)
    plt.tight_layout()
    fname2 = f'q2b_pca_{"gaok" if type_label==0 else "qianbei"}.pdf'
    fig.savefig(f'{WORKSPACE}/figures/{fname2}', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [F5.{3 if type_label==0 else 4}] Saved {fname2}")

# --- FIGURE: Silhouette comparison ---
fig, ax = plt.subplots(figsize=(7, 4))
k_vals = [2, 3, 4]
x_labels = []
sil_vals = []
colors_sil = []
for gt, tl in [('高钾', 0), ('铅钡', 1)]:
    X_t = X_scaled[y == tl]
    n_t = X_t.shape[0]
    for k in k_vals:
        if k < n_t:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labs = km.fit_predict(X_t)
            sil_vals.append(silhouette_score(X_t, labs))
            x_labels.append(f'{gt} k={k}')
            colors_sil.append('#2196F3' if tl == 0 else '#FF9800')

ax.bar(range(len(sil_vals)), sil_vals, color=colors_sil)
ax.set_xticks(range(len(sil_vals)))
ax.set_xticklabels(x_labels)
ax.set_ylabel('Silhouette Score')
ax.set_title('Q2b: Silhouette Scores for Sub-classification')
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q2b_silhouette.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F5.5] Saved q2b_silhouette.pdf")

# Save Q2 results
q2_results = {
    'q2a': {
        'l1_lr_cv_accuracy': float(cv_scores.mean()),
        'l1_lr_cv_std': float(cv_scores.std()),
        'lda_cv_accuracy': float(cv_lda.mean()),
        'lda_cv_std': float(cv_lda.std()),
        'selected_features': [ratio_names[i] for i, c in enumerate(lr_l1.coef_[0]) if abs(c) > 1e-5],
        'pca_variance': pca.explained_variance_ratio_.tolist()
    },
    'q2b': {
        'silhouette_scores': sil_scores if sil_scores else {},
        'best_k': best_k if sil_scores else None
    }
}

with open(f'{WORKSPACE}/results/q2_results.json', 'w') as f:
    json.dump(q2_results, f, ensure_ascii=False, indent=2, default=float)

print("\nQ2 analysis complete. Results in results/q2_results.json")
