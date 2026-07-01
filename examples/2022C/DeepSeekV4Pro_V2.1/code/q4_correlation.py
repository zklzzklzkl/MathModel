#!/usr/bin/env python3
"""q4_correlation.py - Q4 成分关联关系 + 差异网络"""
import os, json, sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from scipy.cluster import hierarchy
from scipy.spatial.distance import pdist
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.covariance import GraphicalLasso
from sklearn.preprocessing import StandardScaler

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

# Select 8 core components (exclude high-missing)
# Use: SiO2, K2O, CaO, Al2O3, Fe2O3, CuO, PbO, BaO
core_indices = [0, 1, 2, 4, 5, 6, 7, 8]  # indices in comp_cols
core_cols = [comp_cols[i] for i in core_indices]
core_norms = [norm_cols[i] for i in core_indices]
core_short = [comp_short[i] for i in core_indices]
print(f"Core 8 components: {core_short}")

# Filter valid, split by type
df2_valid = df2[df2['_valid'] == True].dropna(subset=['类型']).copy()

# Prepare data matrices
def prepare_matrix(df, cols):
    X = np.zeros((len(df), len(cols)))
    for i, nc in enumerate(cols):
        for j in range(len(df)):
            val = df.iloc[j][nc] if pd.notna(df.iloc[j][nc]) else np.nan
            X[j, i] = val
    # Fill NaN with column mean
    for i in range(len(cols)):
        mask = np.isnan(X[:, i])
        if mask.any():
            X[mask, i] = np.nanmean(X[:, i])
    return X

X_gaok = prepare_matrix(df2_valid[df2_valid['类型'] == '高钾'], core_norms)
X_qb = prepare_matrix(df2_valid[df2_valid['类型'] == '铅钡'], core_norms)
print(f"高钾: {X_gaok.shape}, 铅钡: {X_qb.shape}")

# ============================================================
# Q4: Correlation Analysis
# ============================================================
print("\n" + "="*60)
print("Q4: Component Correlation Analysis")
print("="*60)

# --- Pearson correlation ---
corr_gaok = np.corrcoef(X_gaok.T)
corr_qb = np.corrcoef(X_qb.T)

# --- Spearman ---
corr_s_gaok, _ = spearmanr(X_gaok)
corr_s_qb, _ = spearmanr(X_qb)

# --- Graphical Lasso ---
print("\nGraphical Lasso:")
for name, X, corr in [('高钾', X_gaok, corr_gaok), ('铅钡', X_qb, corr_qb)]:
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    n, p = X_std.shape
    # Try multiple lambda values, select by BIC
    lambdas = np.logspace(-1, 1, 20)
    best_bic = np.inf
    best_gl = None
    best_prec = None
    for lam in lambdas:
        try:
            gl = GraphicalLasso(alpha=lam, max_iter=200, tol=1e-4)
            gl.fit(X_std)
            prec = gl.precision_
            # BIC: -2*log_likelihood + log(n)*df
            # log_likelihood ≈ -n/2 * (trace(S*Theta) - log_det(Theta))
            S = np.cov(X_std.T, bias=True)
            log_lik = -n/2 * (np.trace(S @ prec) - np.linalg.slogdet(prec)[1])
            df = np.sum(prec != 0) - p  # non-zero off-diagonal
            bic = -2 * log_lik + np.log(n) * df
            if bic < best_bic:
                best_bic = bic
                best_gl = gl
                best_prec = prec
        except:
            pass
    if best_prec is not None:
        # Partial correlation from precision matrix
        d = np.sqrt(np.diag(best_prec))
        partial_corr = -best_prec / np.outer(d, d)
        np.fill_diagonal(partial_corr, 0)
        n_edges = np.sum(np.abs(partial_corr) > 0.01) // 2
        print(f"  {name}: optimal λ={best_gl.alpha:.3f}, edges={n_edges}, BIC={best_bic:.1f}")
    else:
        partial_corr = np.zeros((p, p))
        print(f"  {name}: GL failed, using zero partial correlation")

    # Store partial correlation
    if name == '高钾':
        partial_gaok = partial_corr
    else:
        partial_qb = partial_corr

# --- Fisher Z test for group differences ---
print("\nSignificant difference in correlations (Fisher Z, |Z|>1.96):")
sig_pairs = []
for i in range(len(core_short)):
    for j in range(i+1, len(core_short)):
        r1 = corr_gaok[i, j]
        r2 = corr_qb[i, j]
        # Fisher Z transformation
        z1 = np.arctanh(max(min(r1, 0.999), -0.999))
        z2 = np.arctanh(max(min(r2, 0.999), -0.999))
        se = np.sqrt(1/(X_gaok.shape[0]-3) + 1/(X_qb.shape[0]-3))
        zdiff = abs(z1 - z2) / se
        if zdiff > 1.96:  # p < 0.05
            sig_pairs.append({'pair': f'{core_short[i]}-{core_short[j]}',
                            'r_gaok': r1, 'r_qb': r2, 'Z_diff': zdiff})
            print(f"  {core_short[i]:8s}-{core_short[j]:8s}: r_gaok={r1:+.3f}, r_qb={r2:+.3f}, Z={zdiff:.2f}")

# ============================================================
# Figures
# ============================================================
# --- FIGURE F7.1 & F7.2: Correlation heatmaps ---
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

for ax, corr_mat, title in zip(axes, [corr_gaok, corr_qb], ['高钾玻璃', '铅钡玻璃']):
    # Create mask for upper triangle
    mask = np.triu(np.ones_like(corr_mat, dtype=bool), k=1)
    im = ax.imshow(corr_mat, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    ax.set_xticks(range(len(core_short)))
    ax.set_xticklabels(core_short, rotation=45, ha='right', fontsize=7)
    ax.set_yticks(range(len(core_short)))
    ax.set_yticklabels(core_short, fontsize=7)
    ax.set_title(f'{title} (n={X_gaok.shape[0] if "高钾" in title else X_qb.shape[0]})')
    # Annotate
    for i in range(len(core_short)):
        for j in range(len(core_short)):
            if i != j:
                ax.text(j, i, f'{corr_mat[i,j]:.2f}', ha='center', va='center', fontsize=5,
                        color='white' if abs(corr_mat[i,j]) > 0.7 else 'black')

plt.colorbar(im, ax=axes, fraction=0.02)
fig.suptitle('Q4: Pearson Correlation Matrices', fontsize=14)
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q4_heatmaps.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F7.1/F7.2] Saved q4_heatmaps.pdf")

# --- FIGURE F7.3: Partial correlation network comparison ---
# Simplified: show significant edges
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for ax, pcorr, title, color in zip(axes, [partial_gaok, partial_qb],
                                     ['高钾 (Partial Corr.)', '铅钡 (Partial Corr.)'],
                                     ['#2196F3', '#FF9800']):
    im = ax.imshow(pcorr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    ax.set_xticks(range(len(core_short)))
    ax.set_xticklabels(core_short, rotation=45, ha='right', fontsize=7)
    ax.set_yticks(range(len(core_short)))
    ax.set_yticklabels(core_short, fontsize=7)
    ax.set_title(title)
    for i in range(len(core_short)):
        for j in range(len(core_short)):
            if abs(pcorr[i, j]) > 0.05:
                ax.text(j, i, f'{pcorr[i,j]:.2f}', ha='center', va='center', fontsize=6,
                        color='white' if abs(pcorr[i,j]) > 0.5 else 'black')

plt.colorbar(im, ax=axes, fraction=0.02)
fig.suptitle('Q4: Graphical Lasso Partial Correlation Networks', fontsize=14)
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q4_partial_networks.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F7.3] Saved q4_partial_networks.pdf")

# --- FIGURE F7.4: Difference network ---
fig, ax = plt.subplots(figsize=(8, 7))
diff_corr = corr_qb - corr_gaok
im = ax.imshow(diff_corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
ax.set_xticks(range(len(core_short)))
ax.set_xticklabels(core_short, rotation=45, ha='right', fontsize=8)
ax.set_yticks(range(len(core_short)))
ax.set_yticklabels(core_short, fontsize=8)
ax.set_title('Q4: Correlation Difference (Lead-Barium - High-Potassium)')
for i in range(len(core_short)):
    for j in range(len(core_short)):
        if i != j:
            ax.text(j, i, f'{diff_corr[i,j]:+.2f}', ha='center', va='center', fontsize=7,
                    color='white' if abs(diff_corr[i,j]) > 0.6 else 'black')
plt.colorbar(im, ax=ax)
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q4_diff_network.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F7.4] Saved q4_diff_network.pdf")

# ============================================================
# Community detection (simplified)
# ============================================================
for name, corr in [('高钾', corr_gaok), ('铅钡', corr_qb)]:
    dist = 1 - np.abs(corr)
    Z = hierarchy.linkage(pdist(dist), method='ward')
    clusters = hierarchy.fcluster(Z, t=0.5, criterion='distance')
    print(f"\n  {name} component communities:")
    for cluster_id in range(1, max(clusters)+1):
        members = [core_short[i] for i in range(len(core_short)) if clusters[i] == cluster_id]
        print(f"    Community {cluster_id}: {members}")

# Save Q4 results
q4_results = {
    'q4': {
        'sig_correlation_differences': sig_pairs,
        'n_significant_pairs': len(sig_pairs)
    }
}

with open(f'{WORKSPACE}/results/q4_results.json', 'w') as f:
    json.dump(q4_results, f, ensure_ascii=False, indent=2, default=float)

print("\nQ4 analysis complete.")
