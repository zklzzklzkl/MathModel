"""
CUMCM 2022 Problem C: Ancient Glass Composition Analysis
Route C (B-lite): Full CLR pipeline with sample-size-appropriate methods
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.model_selection import cross_val_score, LeaveOneOut
from sklearn.feature_selection import mutual_info_classif
import json, os, warnings, re
warnings.filterwarnings('ignore')

# Paths
SRC = r"C:\Users\zklzk\xwechat_files\wxid_nn0sj7wymrcv22_9942\msg\file\2026-05\附件(1).xlsx"
WS = r"C:\Users\zklzk\Desktop\mathmodel_contest"
FIG = os.path.join(WS, "figures")
RES = os.path.join(WS, "results")
COD = os.path.join(WS, "code")
os.makedirs(FIG, exist_ok=True); os.makedirs(RES, exist_ok=True); os.makedirs(COD, exist_ok=True)

plt.rcParams.update({
    'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 11,
    'figure.dpi': 150, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
    'font.sans-serif': ['SimHei', 'DejaVu Sans', 'Arial'],
    'axes.unicode_minus': False
})

MANIFEST = []

def record(result_id, question, value, units, description, source):
    MANIFEST.append({
        "result_id": result_id, "question": question,
        "value": value if not isinstance(value, np.floating) else float(value),
        "units": units, "description": description, "source": source
    })

# ============================================================
# 0. DATA LOADING & PREPARATION
# ============================================================
print("=" * 60)
print("LOADING DATA")
print("=" * 60)

s1 = pd.read_excel(SRC, sheet_name='表单1')
s2 = pd.read_excel(SRC, sheet_name='表单2')
s3 = pd.read_excel(SRC, sheet_name='表单3')

s1.columns = ['id', 'decoration', 'type', 'color', 'weathering']
s2.columns = ['sample_id', 'SiO2', 'Na2O', 'K2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']
s3.columns = ['id', 'weathering', 'SiO2', 'Na2O', 'K2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']

COMPONENTS = ['SiO2', 'Na2O', 'K2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SrO']
EXCLUDE = ['SnO2', 'SO2']

print(f"Sheet 1: {s1.shape[0]} artifacts")
print(f"Sheet 2: {s2.shape[0]} composition rows")
print(f"Sheet 3: {s3.shape[0]} unknown artifacts")

# Parse artifact IDs from Sheet 2
def parse_sample_id(sid):
    sid_str = str(sid)
    # Extract base numeric ID
    m = re.match(r'(\d+)', sid_str)
    base = m.group(1) if m else sid_str
    # Determine sample type
    if '严重风化点' in sid_str: stype = 'severe_weathered'
    elif '未风化点' in sid_str: stype = 'unweathered_point'
    elif '部位1' in sid_str: stype = 'location1'
    elif '部位2' in sid_str: stype = 'location2'
    else: stype = 'primary'
    return base, stype

parsed = s2['sample_id'].apply(parse_sample_id)
s2['base_id'] = parsed.apply(lambda x: x[0])
s2['sample_type'] = parsed.apply(lambda x: x[1])

# Merge with Sheet 1
s2['base_id_int'] = s2['base_id'].astype(int)
s1['id_int'] = s1['id'].astype(int)
merged = s2.merge(s1[['id_int', 'decoration', 'type', 'color', 'weathering']],
                   left_on='base_id_int', right_on='id_int', how='left')

# Resolve weathering labels
def resolve_weathering(row):
    if row['sample_type'] == 'unweathered_point':
        return '无风化'
    if row['sample_type'] == 'severe_weathered':
        return '严重风化'
    return row['weathering']

merged['weathering_resolved'] = merged.apply(resolve_weathering, axis=1)

# Select usable components
X_raw = merged[COMPONENTS].copy().values  # numpy array
X_has = ~pd.isna(merged[COMPONENTS].values)  # bool mask of present values

# Exclude SnO2 and SO2 (already done by selecting COMPONENTS)

# Compute composition sums
merged['comp_sum'] = np.nansum(X_raw, axis=1)
valid_mask = (merged['comp_sum'] >= 85) & (merged['comp_sum'] <= 105)
print(f"Valid composition sum (85-105%): {valid_mask.sum()}/{len(merged)}")

# Zero and missing handling
# 1. Replace zeros with half-minimum non-zero per element
X_filled = X_raw.copy()
for j, comp in enumerate(COMPONENTS):
    vals = X_raw[:, j]
    non_zero = vals[(~np.isnan(vals)) & (vals > 0)]
    if len(non_zero) > 0:
        half_min = np.min(non_zero) / 2
        X_filled[(~np.isnan(vals)) & (vals == 0), j] = half_min

# 2. Impute NaN for components systematically missing by glass type
high_k_mask = merged['type'].values == '高钾'
pb_ba_mask = merged['type'].values == '铅钡'

# Na2O: systematically missing in High-K -> half-min in Pb-Ba
na2o_pb = X_filled[pb_ba_mask & ~pd.isna(merged['Na2O'].values), 1]
if len(na2o_pb) > 0:
    half_min_na2o = np.min(na2o_pb[na2o_pb > 0]) / 2 if np.any(na2o_pb > 0) else 0.01
    na2o_high_k_missing = high_k_mask & pd.isna(merged['Na2O'].values)
    X_filled[na2o_high_k_missing, 1] = half_min_na2o

# K2O: systematically missing in Pb-Ba -> half-min in High-K
k2o_hk = X_filled[high_k_mask & ~pd.isna(merged['K2O'].values), 2]
if len(k2o_hk) > 0:
    half_min_k2o = np.min(k2o_hk[k2o_hk > 0]) / 2 if np.any(k2o_hk > 0) else 0.01
    k2o_pb_missing = pb_ba_mask & pd.isna(merged['K2O'].values)
    X_filled[k2o_pb_missing, 2] = half_min_k2o

# 3. For remaining NaN: use half-min-nonzero per element
for j in range(len(COMPONENTS)):
    missing = np.isnan(X_filled[:, j])
    if missing.any():
        vals = X_filled[~missing, j]
        vals_pos = vals[vals > 0]
        fill_val = np.min(vals_pos) / 2 if len(vals_pos) > 0 else 0.001
        X_filled[missing, j] = fill_val

merged_filled = merged.copy()
for j, comp in enumerate(COMPONENTS):
    merged_filled[comp] = X_filled[:, j]

# Renormalize: scale so sum = 100
row_sums = X_filled.sum(axis=1)
X_norm = X_filled / row_sums[:, None] * 100
for j, comp in enumerate(COMPONENTS):
    merged_filled[comp] = X_norm[:, j]

print("Data preparation complete. All rows filled and normalized.")

# CLR transform
def clr_transform(X):
    """Centered log-ratio transform. X must be all-positive."""
    X_pos = np.maximum(X, 1e-10)
    gmean = np.exp(np.mean(np.log(X_pos), axis=1))
    return np.log(X_pos / gmean[:, None])

X_clr = clr_transform(X_norm)

# Add CLR columns
for j, comp in enumerate(COMPONENTS):
    merged_filled[f'{comp}_clr'] = X_clr[:, j]

# ============================================================
# ARTIFACT-LEVEL AGGREGATION
# ============================================================
print("\n" + "=" * 60)
print("ARTIFACT-LEVEL AGGREGATION")
print("=" * 60)

def aggregate_to_artifact(df_merged, X_clr, X_norm):
    """Aggregate multi-sample artifacts to artifact level."""
    artifacts = []

    for base_id, group in df_merged.groupby('base_id_int'):
        row = {'base_id': str(base_id).zfill(2)}
        # Basic info from Sheet 1 (first row in group)
        row['type'] = group['type'].iloc[0]
        row['weathering'] = group['weathering'].iloc[0]
        row['decoration'] = group['decoration'].iloc[0]
        row['color'] = group['color'].iloc[0]
        row['n_samples'] = len(group)

        # Composition: use primary point, or mean of multi-location
        primary = group[group['sample_type'].isin(['primary', 'unweathered_point'])]
        if len(primary) == 0:
            primary = group  # fallback

        # Average composition for artifact-level
        idxs = primary.index.tolist()
        row.update({comp: X_norm[idxs, j].mean() for j, comp in enumerate(COMPONENTS)})
        row.update({f'{comp}_clr': X_clr[idxs, j].mean() for j, comp in enumerate(COMPONENTS)})

        # Weathering resolved
        if 'unweathered_point' in group['sample_type'].values:
            row['has_unweathered_point'] = True
        else:
            row['has_unweathered_point'] = False

        # Preserve group indices for paired analysis
        row['_indices'] = list(group.index)

        artifacts.append(row)

    return pd.DataFrame(artifacts)

artifacts = aggregate_to_artifact(merged_filled, X_clr, X_norm)
print(f"Artifact-level data: {len(artifacts)} artifacts")
print(f"  High-K: {(artifacts['type']=='高钾').sum()}")
print(f"  Pb-Ba: {(artifacts['type']=='铅钡').sum()}")
print(f"  Weathered: {(artifacts['weathering']=='风化').sum()}")
print(f"  Unweathered: {(artifacts['weathering']=='无风化').sum()}")

# ============================================================
# Q1A: WEATHERING ASSOCIATION ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("Q1A: WEATHERING ASSOCIATION ANALYSIS")
print("=" * 60)

results_q1a = {}

# Weathering x Type
ct_type = pd.crosstab(artifacts['weathering'], artifacts['type'])
chi2_type, p_type, dof_type, exp_type = stats.chi2_contingency(ct_type)
n = len(artifacts)
cramer_v_type = np.sqrt(chi2_type / (n * min(ct_type.shape[0]-1, ct_type.shape[1]-1)))
results_q1a['type'] = {'chi2': chi2_type, 'p': p_type, 'dof': dof_type, 'cramer_v': cramer_v_type}
print(f"Weathering x Type: chi2({dof_type})={chi2_type:.2f}, p={p_type:.4f}, V={cramer_v_type:.3f}")

# Weathering x Decoration
ct_dec = pd.crosstab(artifacts['weathering'], artifacts['decoration'])
chi2_dec, p_dec, dof_dec, exp_dec = stats.chi2_contingency(ct_dec)
cramer_v_dec = np.sqrt(chi2_dec / (n * min(ct_dec.shape[0]-1, ct_dec.shape[1]-1)))
results_q1a['decoration'] = {'chi2': chi2_dec, 'p': p_dec, 'dof': dof_dec, 'cramer_v': cramer_v_dec}
print(f"Weathering x Decoration: chi2({dof_dec})={chi2_dec:.2f}, p={p_dec:.4f}, V={cramer_v_dec:.3f}")

# Weathering x Color (merge sparse categories)
color_merged = artifacts['color'].copy()
color_merged[color_merged.isin(['黑', '深蓝'])] = '深色'
ct_color = pd.crosstab(artifacts['weathering'], color_merged)
chi2_color, p_color, dof_color, exp_color = stats.chi2_contingency(ct_color)
cramer_v_color = np.sqrt(chi2_color / (n * min(ct_color.shape[0]-1, ct_color.shape[1]-1)))
results_q1a['color'] = {'chi2': chi2_color, 'p': p_color, 'dof': dof_color, 'cramer_v': cramer_v_color}
print(f"Weathering x Color: chi2({dof_color})={chi2_color:.2f}, p={p_color:.4f}, V={cramer_v_color:.3f}")

# Record
for k, v in results_q1a.items():
    record(f"Q1A_{k}_chi2", "Q1A", v['chi2'], "chi2", f"Weathering x {k} chi-square", "q1_weathering.py")
    record(f"Q1A_{k}_pvalue", "Q1A", v['p'], "p-value", f"Weathering x {k} p-value", "q1_weathering.py")
    record(f"Q1A_{k}_cramer_v", "Q1A", v['cramer_v'], "Cramer's V", f"Weathering x {k} effect size", "q1_weathering.py")

# FIGURE 1: Mosaic-like grouped bar charts
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Weathering x Type
ct = pd.crosstab(artifacts['type'], artifacts['weathering'])
ct_pct = ct.div(ct.sum(axis=1), axis=0)
ct_pct.plot(kind='barh', stacked=True, ax=axes[0], color=['#4CAF50', '#FF9800'])
axes[0].set_title('Weathering Status by Glass Type')
axes[0].set_xlabel('Proportion'); axes[0].set_ylabel('Glass Type')
axes[0].legend(title='Weathering', loc='lower right')
axes[0].text(0.5, -0.25, f'chi2={chi2_type:.1f}, p={p_type:.3f}, V={cramer_v_type:.3f}',
             transform=axes[0].transAxes, ha='center', fontsize=9)

# Weathering x Decoration
ct2 = pd.crosstab(artifacts['decoration'], artifacts['weathering'])
ct2_pct = ct2.div(ct2.sum(axis=1), axis=0)
ct2_pct.plot(kind='barh', stacked=True, ax=axes[1], color=['#4CAF50', '#FF9800'])
axes[1].set_title('Weathering Status by Decoration Type')
axes[1].set_xlabel('Proportion'); axes[1].set_ylabel('Decoration')
axes[1].legend(title='Weathering', loc='lower right')
axes[1].text(0.5, -0.25, f'chi2={chi2_dec:.1f}, p={p_dec:.3f}, V={cramer_v_dec:.3f}',
             transform=axes[1].transAxes, ha='center', fontsize=9)

plt.tight_layout()
fig.savefig(os.path.join(FIG, 'fig1_weathering_association.pdf'), format='pdf')
fig.savefig(os.path.join(FIG, 'fig1_weathering_association.png'), format='png')
plt.close()
print("Figure 1 saved.")

# ============================================================
# Q1B: COMPOSITIONAL WEATHERING STATISTICS
# ============================================================
print("\n" + "=" * 60)
print("Q1B: COMPOSITIONAL WEATHERING STATISTICS")
print("=" * 60)

# Use artifact-level data for CLR-based comparison
hk = artifacts[artifacts['type'] == '高钾']
pb = artifacts[artifacts['type'] == '铅钡']

clr_cols = [f'{c}_clr' for c in COMPONENTS]
hk_clr = hk[clr_cols].values
pb_clr = pb[clr_cols].values
hk_weat = (hk['weathering'].values == '风化') | (hk['weathering'].values == '严重风化')
pb_weat = (pb['weathering'].values == '风化') | (pb['weathering'].values == '严重风化')

# Welch's t-test per element per type
q1b_results = []
for glass_type, clr_data, weat_mask, df_art in [('High-K', hk_clr, hk_weat, hk), ('Pb-Ba', pb_clr, pb_weat, pb)]:
    for j, comp in enumerate(COMPONENTS):
        w_vals = clr_data[weat_mask, j]
        u_vals = clr_data[~weat_mask, j]
        if len(w_vals) < 2 or len(u_vals) < 2:
            continue
        t_stat, p_val = stats.ttest_ind(w_vals, u_vals, equal_var=False)
        # Cohen's d
        d = (np.mean(w_vals) - np.mean(u_vals)) / np.sqrt((np.var(w_vals) + np.var(u_vals)) / 2)
        # Raw-scale fold change
        raw_w = df_art[df_art['weathering'].isin(['风化', '严重风化'])][comp].mean()
        raw_u = df_art[~df_art['weathering'].isin(['风化', '严重风化'])][comp].mean()
        fc = raw_w / raw_u if raw_u > 0 else 1.0
        q1b_results.append({
            'glass_type': glass_type, 'component': comp,
            't_stat': t_stat, 'p_raw': p_val,
            'cohens_d': d, 'fc_raw': fc
        })

df_q1b = pd.DataFrame(q1b_results)
# Holm-Bonferroni correction
n_tests = len(df_q1b)
df_q1b['p_holm'] = np.minimum(df_q1b['p_raw'].values * n_tests, 1.0)
# Sort for Holm: multiply by rank
sorted_p = np.sort(df_q1b['p_raw'].values)
for i, (idx, row) in enumerate(df_q1b.iterrows()):
    rank = np.sum(sorted_p <= row['p_raw'])
    df_q1b.loc[idx, 'p_holm'] = min(row['p_raw'] * (n_tests - rank + 1), 1.0)

# Significant results
sig = df_q1b[df_q1b['p_holm'] < 0.05]
print(f"Significant elements (Holm-adjusted p < 0.05): {len(sig)}/{len(df_q1b)}")
for _, row in sig.iterrows():
    print(f"  {row['glass_type']} {row['component']}: d={row['cohens_d']:.3f}, p_holm={row['p_holm']:.4f}")
    record(f"Q1B_{row['glass_type']}_{row['component']}_d", "Q1B", row['cohens_d'], "Cohen's d",
           f"{row['glass_type']} {row['component']} weathering effect", "q1_weathering.py")

# FIGURE 2: Volcano plots
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for ax, (gt_name, gt_df) in zip(axes, df_q1b.groupby('glass_type')):
    gt_df = gt_df.copy()
    gt_df['neg_log10_p'] = -np.log10(np.maximum(gt_df['p_holm'].values, 1e-10))
    gt_df['log2_fc'] = np.log2(gt_df['fc_raw'].values)

    colors = ['#2196F3' if p >= 0.05 else '#F44336' if fc <= 1 else '#FF9800'
              for p, fc in zip(gt_df['p_holm'], gt_df['fc_raw'])]
    ax.scatter(gt_df['log2_fc'], gt_df['neg_log10_p'], c=colors, s=80, edgecolors='black', linewidth=0.5, zorder=5)
    ax.axhline(-np.log10(0.05), color='gray', linestyle='--', alpha=0.5, label='p=0.05')
    ax.axvline(0, color='gray', linestyle='--', alpha=0.3)

    # Label significant points
    for _, row in gt_df[gt_df['p_holm'] < 0.05].iterrows():
        ax.annotate(row['component'], (row['log2_fc'], row['neg_log10_p']),
                   fontsize=8, xytext=(5, 5), textcoords='offset points')

    ax.set_title(f'{gt_name} Glass: Weathering Effect')
    ax.set_xlabel('log2(Weathered / Unweathered)')
    ax.set_ylabel('-log10(Holm-adjusted p)')

plt.tight_layout()
fig.savefig(os.path.join(FIG, 'fig2_weathering_volcano.pdf'), format='pdf')
fig.savefig(os.path.join(FIG, 'fig2_weathering_volcano.png'), format='png')
plt.close()
print("Figure 2 saved.")

# ============================================================
# Q1C: PRE-WEATHERING PREDICTION
# ============================================================
print("\n" + "=" * 60)
print("Q1C: PRE-WEATHERING PREDICTION")
print("=" * 60)

# Calibration pairs from merged data (point-level)
# Artifacts with both weathered and unweathered data
paired_artifacts = ['08', '26', '49', '50', '23', '25', '28', '29', '42', '44', '53']
calibration_pairs = []

for aid in paired_artifacts:
    aid_rows = merged_filled[merged_filled['base_id'] == aid]
    weathered_rows = aid_rows[aid_rows['weathering_resolved'].isin(['风化', '严重风化'])]
    unweathered_rows = aid_rows[aid_rows['weathering_resolved'] == '无风化']
    if len(weathered_rows) > 0 and len(unweathered_rows) > 0:
        # Average if multiple
        w_comp = weathered_rows[COMPONENTS].mean().values
        u_comp = unweathered_rows[COMPONENTS].mean().values
        calibration_pairs.append({
            'artifact_id': aid,
            'type': aid_rows['type'].iloc[0],
            'weathered': w_comp,
            'unweathered': u_comp
        })

print(f"Calibration pairs: {len(calibration_pairs)}")
for cp in calibration_pairs:
    print(f"  {cp['artifact_id']} ({cp['type']}): Al2O3 w={cp['weathered'][5]:.2f}, u={cp['unweathered'][5]:.2f}")

# Method 1: Immobile-element normalization (Al2O3 as reference)
al2o3_idx = COMPONENTS.index('Al2O3')

# Reference Al2O3 per glass type (from unweathered artifacts)
hk_unweathered = artifacts[(artifacts['type'] == '高钾') & (~artifacts['weathering'].isin(['风化', '严重风化']))]
pb_unweathered = artifacts[(artifacts['type'] == '铅钡') & (~artifacts['weathering'].isin(['风化', '严重风化']))]
ref_al2o3_hk = hk_unweathered['Al2O3'].mean()
ref_al2o3_pb = pb_unweathered['Al2O3'].mean()
print(f"Reference Al2O3 -- High-K: {ref_al2o3_hk:.2f}, Pb-Ba: {ref_al2o3_pb:.2f}")

# Validate Method 1 on calibration pairs
mae_q1c = {comp: [] for comp in COMPONENTS}
predictions_q1c = []

for cp in calibration_pairs:
    ref_al2o3 = ref_al2o3_hk if cp['type'] == '高钾' else ref_al2o3_pb
    ef = ref_al2o3 / cp['weathered'][al2o3_idx]  # enrichment factor
    predicted = cp['weathered'] * ef
    actual = cp['unweathered']

    for j, comp in enumerate(COMPONENTS):
        mae_q1c[comp].append(abs(predicted[j] - actual[j]))

    predictions_q1c.append({
        'artifact_id': cp['artifact_id'],
        'type': cp['type'],
        'enrichment_factor': ef,
        'predicted': predicted.tolist(),
        'actual': actual.tolist()
    })

mae_summary = {comp: np.mean(vals) for comp, vals in mae_q1c.items()}
print("\nMethod 1 MAE per element:")
for comp, mae in sorted(mae_summary.items(), key=lambda x: x[1]):
    print(f"  {comp}: {mae:.3f}%")
    record(f"Q1C_MAE_{comp}", "Q1C", mae, "%", f"MAE for {comp} prediction", "q1_weathering.py")

overall_mae = np.mean(list(mae_summary.values()))
record("Q1C_overall_MAE", "Q1C", overall_mae, "%", "Overall MAE for pre-weathering prediction", "q1_weathering.py")
print(f"Overall MAE: {overall_mae:.3f}%")

# Predict for all weathered artifacts + Sheet 3 unknowns
def predict_preweathering(weathered_comp, glass_type):
    ref_al2o3 = ref_al2o3_hk if glass_type == '高钾' else ref_al2o3_pb
    ef = ref_al2o3 / np.maximum(weathered_comp[al2o3_idx], 0.01)
    return weathered_comp * ef

# FIGURE 3: Validation scatter
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
key_elements = ['SiO2', 'K2O', 'CaO', 'Al2O3', 'PbO', 'BaO', 'CuO', 'P2O5']
axes = axes.flatten()
all_actual = []; all_pred = []

for j, comp in enumerate(key_elements):
    ax = axes[j]
    comp_idx = COMPONENTS.index(comp)
    actuals = [cp['actual'][comp_idx] for cp in predictions_q1c]
    preds = [cp['predicted'][comp_idx] for cp in predictions_q1c]
    all_actual.extend(actuals); all_pred.extend(preds)

    ax.scatter(actuals, preds, alpha=0.7, s=50)
    max_val = max(max(actuals), max(preds))
    ax.plot([0, max_val], [0, max_val], 'r--', alpha=0.5)
    ax.set_xlabel('Actual'); ax.set_ylabel('Predicted')
    ax.set_title(comp, fontsize=10)
    ax.set_xlim(0, max_val); ax.set_ylim(0, max_val)

plt.suptitle('Q1C: Pre-Weathering Prediction Validation', fontweight='bold')
plt.tight_layout()
fig.savefig(os.path.join(FIG, 'fig3_weathering_pred_validation.pdf'), format='pdf')
fig.savefig(os.path.join(FIG, 'fig3_weathering_pred_validation.png'), format='png')
plt.close()
print("Figure 3 saved.")

# ============================================================
# Q2: CLASSIFICATION & SUB-CLASSIFICATION
# ============================================================
print("\n" + "=" * 60)
print("Q2: CLASSIFICATION & SUB-CLASSIFICATION")
print("=" * 60)

# Feature importance: 3 methods
X_clr_art = artifacts[clr_cols].values
y_type = artifacts['type'].values
y_type_bin = (y_type == '铅钡').astype(int)

# 1. Random Forest
rf = RandomForestClassifier(n_estimators=500, random_state=42)
rf.fit(X_clr_art, y_type_bin)
rf_imp = rf.feature_importances_

# 2. Welch t-test
ttest_stats = []
for j in range(len(COMPONENTS)):
    hk_vals = X_clr_art[y_type == '高钾', j]
    pb_vals = X_clr_art[y_type == '铅钡', j]
    t_stat, _ = stats.ttest_ind(hk_vals, pb_vals, equal_var=False)
    ttest_stats.append(abs(t_stat))

# 3. Mutual information
mi_scores = mutual_info_classif(X_clr_art, y_type_bin, random_state=42)

# Consensus ranking
ranks = pd.DataFrame({
    'component': COMPONENTS,
    'rf_rank': pd.Series(rf_imp).rank(ascending=False),
    'ttest_rank': pd.Series(ttest_stats).rank(ascending=False),
    'mi_rank': pd.Series(mi_scores).rank(ascending=False)
})
ranks['avg_rank'] = ranks[['rf_rank', 'ttest_rank', 'mi_rank']].mean(axis=1)
ranks = ranks.sort_values('avg_rank')

print("Top discriminant elements:")
for _, row in ranks.head(8).iterrows():
    print(f"  {row['component']}: avg_rank={row['avg_rank']:.1f} (RF={row['rf_rank']:.0f}, t={row['ttest_rank']:.0f}, MI={row['mi_rank']:.0f})")
    record(f"Q2_discriminant_{row['component']}", "Q2", row['avg_rank'], "rank",
           f"Discriminant rank for {row['component']}", "q2_classification.py")

# Sub-classification per glass type
top5_elements = ranks.head(5)['component'].tolist()
print(f"\nTop 5 for sub-classification: {top5_elements}")

scaler = StandardScaler()
X_clr_scaled = scaler.fit_transform(X_clr_art)

subclass_results = {}
for gt_name, gt_mask in [('High-K', y_type == '高钾'), ('Pb-Ba', y_type == '铅钡')]:
    X_gt = X_clr_scaled[gt_mask]
    n_gt = X_gt.shape[0]
    print(f"\n--- {gt_name} Glass (n={n_gt}) ---")

    # Ward hierarchical clustering
    Z = linkage(X_gt, method='ward', metric='euclidean')

    # Silhouette for k=2..min(5, n/3)
    max_k = min(5, n_gt // 3)
    silhouettes = {}
    for k in range(2, max_k + 1):
        labels = fcluster(Z, k, criterion='maxclust')
        sil = silhouette_score(X_gt, labels)
        silhouettes[k] = sil

    if silhouettes:
        best_k = max(silhouettes, key=silhouettes.get)
        best_sil = silhouettes[best_k]
        print(f"  Best k={best_k} (silhouette={best_sil:.3f})")
    else:
        best_k = 2
        best_sil = 0.0
        print(f"  Default k=2 (not enough samples)")

    labels = fcluster(Z, best_k, criterion='maxclust')

    # k-means cross-check
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    km_labels = km.fit_predict(X_gt)
    ari = adjusted_rand_score(labels, km_labels)
    print(f"  ARI (Ward vs k-means): {ari:.3f}")

    # Bootstrap stability
    aris = []
    for _ in range(500):
        idx = np.random.choice(n_gt, n_gt, replace=True)
        X_boot = X_gt[idx]
        try:
            Z_boot = linkage(X_boot, method='ward')
            labels_boot = fcluster(Z_boot, best_k, criterion='maxclust')
            # Map labels back to common space
            aris.append(adjusted_rand_score(labels[idx], labels_boot))
        except:
            pass

    median_ari = np.median(aris) if aris else 0
    print(f"  Bootstrap median ARI: {median_ari:.3f}")

    # Cluster profiles
    cluster_profiles = {}
    for c in range(1, best_k + 1):
        c_mask = labels == c
        cluster_data = artifacts[gt_mask].iloc[c_mask]
        cluster_profiles[c] = {
            'size': c_mask.sum(),
            'mean_composition': {comp: cluster_data[comp].mean() for comp in COMPONENTS}
        }
        print(f"  Cluster {c}: n={c_mask.sum()}")

    subclass_results[gt_name] = {
        'best_k': best_k, 'silhouette': best_sil,
        'ari_km': ari, 'median_ari_bootstrap': median_ari,
        'labels': labels, 'cluster_profiles': cluster_profiles,
        'indices': artifacts[gt_mask].index.values
    }

    record(f"Q2_{gt_name}_best_k", "Q2", best_k, "clusters", f"Optimal k for {gt_name}", "q2_classification.py")
    record(f"Q2_{gt_name}_silhouette", "Q2", best_sil, "silhouette", f"Silhouette score for {gt_name}", "q2_classification.py")
    record(f"Q2_{gt_name}_ari_bootstrap", "Q2", median_ari, "ARI", f"Bootstrap stability ARI for {gt_name}", "q2_classification.py")

# Assign sub-class labels to all artifacts
artifacts['subclass'] = ''
for gt_name, result in subclass_results.items():
    mask = artifacts['type'].values == gt_name
    for i, idx in enumerate(result['indices']):
        artifacts.loc[idx, 'subclass'] = f"{gt_name}-{result['labels'][i]}"

# FIGURE 4 & 5: Dendrograms + PCA + Silhouette
for gt_name, gt_full in [('High-K', '高钾'), ('Pb-Ba', '铅钡')]:
    result = subclass_results[gt_name]
    gt_mask = y_type == gt_full
    X_gt = X_clr_scaled[gt_mask]
    Z = linkage(X_gt, method='ward')

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.2])

    # Dendrogram
    ax_dend = fig.add_subplot(gs[0, :])
    dendrogram(Z, ax=ax_dend, labels=None, leaf_font_size=8,
               color_threshold=Z[-(result['best_k']-1), 2] if result['best_k'] > 1 else 1e10)
    ax_dend.set_title(f'{gt_name} Glass: Hierarchical Clustering (Ward)')
    ax_dend.set_ylabel('Distance')

    # PCA biplot
    ax_pca = fig.add_subplot(gs[1, 0])
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_gt)
    colors = plt.cm.Set2(np.linspace(0, 0.8, result['best_k']))
    for c in range(1, result['best_k'] + 1):
        ax_pca.scatter(X_pca[result['labels'] == c, 0], X_pca[result['labels'] == c, 1],
                      c=[colors[c-1]], label=f'Cluster {c}', s=60, edgecolors='black', linewidth=0.5)
    # Add element loading vectors
    loadings = pca.components_.T
    for j, comp in enumerate(COMPONENTS):
        ax_pca.arrow(0, 0, loadings[j, 0]*5, loadings[j, 1]*5, head_width=0.15, alpha=0.5)
        ax_pca.text(loadings[j, 0]*5.3, loadings[j, 1]*5.3, comp, fontsize=7)
    ax_pca.set_title(f'PCA Biplot (PC1={pca.explained_variance_ratio_[0]:.1%}, PC2={pca.explained_variance_ratio_[1]:.1%})')
    ax_pca.set_xlabel('PC1'); ax_pca.set_ylabel('PC2')
    ax_pca.legend(fontsize=8)

    # Silhouette
    ax_sil = fig.add_subplot(gs[1, 1])
    if result['best_k'] > 1:
        from sklearn.metrics import silhouette_samples
        sil_vals = silhouette_samples(X_gt, result['labels'])
        y_lower = 0
        for c in range(1, result['best_k'] + 1):
            c_sil = np.sort(sil_vals[result['labels'] == c])
            ax_sil.fill_betweenx(np.arange(y_lower, y_lower + len(c_sil)), 0, c_sil,
                                facecolor=colors[c-1], alpha=0.7)
            y_lower += len(c_sil)
        ax_sil.axvline(result['silhouette'], color='red', linestyle='--')
    ax_sil.set_title(f'Silhouette Plot (avg={result["silhouette"]:.3f})')
    ax_sil.set_xlabel('Silhouette Coefficient'); ax_sil.set_ylabel('Sample')

    fig_num = '4' if gt_name == 'High-K' else '5'
    plt.suptitle(f'{gt_name} Glass Sub-Classification', fontweight='bold', fontsize=14)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG, f'fig{fig_num}_{gt_name.lower()}_subclass.pdf'), format='pdf')
    fig.savefig(os.path.join(FIG, f'fig{fig_num}_{gt_name.lower()}_subclass.png'), format='png')
    plt.close()
    print(f"Figure {fig_num} ({gt_name}) saved.")

# ============================================================
# FIGURE 6: Decision Tree
# ============================================================
print("\n" + "=" * 60)
print("FIGURE 6: DECISION TREE")
print("=" * 60)

# Train decision tree on original-scale top-5 elements
X_tree = artifacts[top5_elements].values
y_subclass = artifacts['subclass'].values

# Encode subclass labels
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
y_subclass_enc = le.fit_transform(y_subclass)

dt = DecisionTreeClassifier(max_depth=3, min_samples_leaf=3, random_state=42)
dt.fit(X_tree, y_subclass_enc)

fig, ax = plt.subplots(figsize=(18, 8))
plot_tree(dt, feature_names=top5_elements, class_names=le.classes_,
          filled=True, rounded=True, fontsize=9, ax=ax, impurity=False)
ax.set_title('Glass Sub-Classification Decision Rules', fontweight='bold')
plt.tight_layout()
fig.savefig(os.path.join(FIG, 'fig6_decision_tree.pdf'), format='pdf')
fig.savefig(os.path.join(FIG, 'fig6_decision_tree.png'), format='png')
plt.close()
print("Figure 6 saved.")

dt_accuracy = dt.score(X_tree, y_subclass_enc)
record("Q2_decision_tree_accuracy", "Q2", dt_accuracy, "accuracy", "Decision tree training accuracy", "q2_classification.py")

# ============================================================
# Q3: UNKNOWN CLASSIFICATION
# ============================================================
print("\n" + "=" * 60)
print("Q3: UNKNOWN CLASSIFICATION")
print("=" * 60)

# Prepare Sheet 3 data
s3_filled = np.array(s3[COMPONENTS].values, dtype=float, copy=True)
# Fill zeros and NaN
for j, comp in enumerate(COMPONENTS):
    vals = s3[comp].values
    # Zeros
    zero_mask = (~pd.isna(vals)) & (vals == 0)
    non_zero = vals[(~pd.isna(vals)) & (vals > 0)]
    half_min = np.min(non_zero) / 2 if len(non_zero) > 0 else 0.01
    s3_filled[zero_mask, j] = half_min
    # NaN
    nan_mask = pd.isna(vals)
    if nan_mask.any():
        s3_filled[nan_mask, j] = half_min

# Normalize
s3_sums = s3_filled.sum(axis=1)
s3_norm = s3_filled / s3_sums[:, None] * 100

# Apply Q1C correction for weathered unknowns
s3_corrected = s3_norm.copy()
for i in range(len(s3)):
    if s3['weathering'].iloc[i] == '风化':
        # Guess type for EF: use Al2O3-based method without type knowledge
        # Use average of both ref values as first pass
        ef = ((ref_al2o3_hk + ref_al2o3_pb) / 2) / np.maximum(s3_norm[i, al2o3_idx], 0.01)
        s3_corrected[i] = s3_norm[i] * ef

# CLR transform
s3_clr = clr_transform(s3_corrected)
s3_clr_scaled = scaler.transform(s3_clr)

# Train classifiers on artifact-level CLR training data
# k-NN
knn3 = KNeighborsClassifier(n_neighbors=3)
knn3.fit(X_clr_scaled, y_type_bin)
knn5 = KNeighborsClassifier(n_neighbors=5)
knn5.fit(X_clr_scaled, y_type_bin)

# Random Forest
rf_clf = RandomForestClassifier(n_estimators=500, random_state=42)
rf_clf.fit(X_clr_scaled, y_type_bin)

# LOOCV accuracy
loo = LeaveOneOut()
rf_cv_scores = cross_val_score(rf_clf, X_clr_scaled, y_type_bin, cv=loo)
knn3_cv = cross_val_score(knn3, X_clr_scaled, y_type_bin, cv=loo)
print(f"LOOCV accuracy -- RF: {rf_cv_scores.mean():.3f}, k-NN(k=3): {knn3_cv.mean():.3f}")

record("Q3_RF_LOOCV", "Q3", rf_cv_scores.mean(), "accuracy", "RF LOOCV accuracy", "q3_identification.py")
record("Q3_kNN3_LOOCV", "Q3", knn3_cv.mean(), "accuracy", "k-NN k=3 LOOCV accuracy", "q3_identification.py")

# Classify S3
knn3_pred = knn3.predict(s3_clr_scaled)
knn3_prob = knn3.predict_proba(s3_clr_scaled)
knn5_pred = knn5.predict(s3_clr_scaled)
rf_pred = rf_clf.predict(s3_clr_scaled)
rf_prob = rf_clf.predict_proba(s3_clr_scaled)

# Classification results
q3_results = []
for i in range(len(s3)):
    sid = s3['id'].iloc[i]
    weathered = s3['weathering'].iloc[i]

    knn3_label_en = 'Pb-Ba' if knn3_pred[i] == 1 else 'High-K'
    knn5_label_en = 'Pb-Ba' if knn5_pred[i] == 1 else 'High-K'
    rf_label_en = 'Pb-Ba' if rf_pred[i] == 1 else 'High-K'

    # Map to Chinese type names
    type_map = {'High-K': '高钾', 'Pb-Ba': '铅钡'}
    knn3_label = type_map[knn3_label_en]
    knn5_label = type_map[knn5_label_en]
    rf_label = type_map[rf_label_en]

    knn3_vote = knn3_prob[i][knn3_pred[i]]
    rf_vote = rf_prob[i][rf_pred[i]]

    # Agreement
    predictions = [knn3_label, knn5_label, rf_label]
    from collections import Counter
    consensus = Counter(predictions).most_common(1)[0]
    agreed = len(set(predictions)) == 1

    # Final type (Chinese for artifact matching)
    final_type = consensus[0]
    final_confidence = consensus[1] / 3

    # Sub-class assignment via Mahalanobis
    final_mask = artifacts['type'] == final_type
    subclass_centroids = {}
    for sc in artifacts.loc[final_mask, 'subclass'].unique():
        sc_data = artifacts.loc[artifacts['subclass'] == sc, clr_cols].values
        subclass_centroids[sc] = sc_data.mean(axis=0)

    # Simple Euclidean distance to centroids (Mahalanobis with diagonal cov for small n)
    sample_clr = s3_clr[i]
    distances = {}
    for sc, centroid in subclass_centroids.items():
        # Use diagonal of covariance
        sc_cov_diag = np.var(artifacts.loc[artifacts['subclass'] == sc, clr_cols].values, axis=0)
        sc_cov_diag = np.maximum(sc_cov_diag, 1e-6)
        d = np.sqrt(np.sum((sample_clr - centroid) ** 2 / sc_cov_diag))
        distances[sc] = d

    assigned_subclass = min(distances, key=distances.get)

    q3_results.append({
        'id': sid, 'weathering': weathered,
        'final_type': final_type, 'confidence': final_confidence,
        'knn3_label': knn3_label, 'knn5_label': knn5_label, 'rf_label': rf_label,
        'knn3_vote': knn3_vote, 'rf_vote': rf_vote,
        'agreed': agreed,
        'subclass': assigned_subclass,
        'subclass_distance': distances[assigned_subclass]
    })

print("\nQ3 Classification Results:")
for r in q3_results:
    status = "AGREED" if r['agreed'] else "SPLIT"
    print(f"  {r['id']} ({r['weathering']}): {r['final_type']} [{status}, conf={r['confidence']:.2f}] -> {r['subclass']}")
    record(f"Q3_{r['id']}_type", "Q3", r['final_type'], "type", f"Classification for {r['id']}", "q3_identification.py")
    record(f"Q3_{r['id']}_confidence", "Q3", r['confidence'], "fraction", f"Confidence for {r['id']}", "q3_identification.py")
    record(f"Q3_{r['id']}_subclass", "Q3", r['subclass'], "subclass", f"Sub-class for {r['id']}", "q3_identification.py")

# Sensitivity: perturbation analysis
perturbation_results = []
for pert in [0.05, 0.10]:
    stable = 0
    for _ in range(100):
        noise = np.random.normal(0, pert, s3_clr_scaled.shape)
        s3_pert = s3_clr_scaled + noise
        knn_preds = knn3.predict(s3_pert)
        rf_preds = rf_clf.predict(s3_pert)
        stable += np.sum((knn_preds == knn3_pred) & (rf_preds == rf_pred))
    stability = stable / (100 * len(s3))
    perturbation_results.append({'perturbation': pert, 'stability': stability})
    print(f"  +/-{pert*100:.0f}% perturbation stability: {stability:.2%}")
    record(f"Q3_stability_{pert}", "Q3", stability, "fraction", f"Classification stability at {pert*100}% perturbation", "q3_identification.py")

# FIGURE 7: PCA projection
fig, ax = plt.subplots(figsize=(10, 8))
pca_all = PCA(n_components=2)
all_data = np.vstack([X_clr_scaled, s3_clr_scaled])
pca_all.fit(all_data)
X_pca_art = pca_all.transform(X_clr_scaled)
s3_pca = pca_all.transform(s3_clr_scaled)

for gt_name, gt_full, marker in [('High-K', '高钾', 'o'), ('Pb-Ba', '铅钡', 's')]:
    mask = y_type == gt_full
    ax.scatter(X_pca_art[mask, 0], X_pca_art[mask, 1],
              c=plt.cm.Set2(0) if gt_name == 'High-K' else plt.cm.Set2(1),
              marker=marker, alpha=0.6, label=gt_name, s=60, edgecolors='black', linewidth=0.3)

# Plot unknowns
for i, r in enumerate(q3_results):
    color = '#F44336' if r['final_type'] == 'High-K' else '#FF9800'
    ax.scatter(s3_pca[i, 0], s3_pca[i, 1], c=color, s=200, marker='*',
              edgecolors='black', linewidth=1.5, zorder=10)
    ax.annotate(r['id'], (s3_pca[i, 0], s3_pca[i, 1]), fontsize=10, fontweight='bold',
               xytext=(10, 5), textcoords='offset points')

ax.set_title(f'PCA Projection: Training Data + Unknowns ({pca_all.explained_variance_ratio_[0]:.1%} + {pca_all.explained_variance_ratio_[1]:.1%} variance)')
ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
ax.legend()
plt.tight_layout()
fig.savefig(os.path.join(FIG, 'fig7_classification_pca.pdf'), format='pdf')
fig.savefig(os.path.join(FIG, 'fig7_classification_pca.png'), format='png')
plt.close()
print("Figure 7 saved.")

# FIGURE 8: Classification results bar chart
fig, ax = plt.subplots(figsize=(10, 5))
x_pos = np.arange(len(q3_results))
width = 0.35
rf_votes = [r['rf_vote'] for r in q3_results]
knn_votes = [r['knn3_vote'] for r in q3_results]
ids = [r['id'] for r in q3_results]
types = [r['final_type'] for r in q3_results]

bars1 = ax.bar(x_pos - width/2, knn_votes, width, label='k-NN (k=3) vote', color='#2196F3')
bars2 = ax.bar(x_pos + width/2, rf_votes, width, label='RF vote', color='#4CAF50')
ax.set_xticks(x_pos)
ax.set_xticklabels([f'{i}\n({t})' for i, t in zip(ids, types)], fontsize=9)
ax.set_ylabel('Vote Fraction'); ax.set_title('Q3: Unknown Artifact Classification Confidence')
ax.legend()
ax.set_ylim(0, 1.1)
ax.axhline(0.5, color='red', linestyle='--', alpha=0.5, label='50% threshold')

plt.tight_layout()
fig.savefig(os.path.join(FIG, 'fig8_classification_results.pdf'), format='pdf')
fig.savefig(os.path.join(FIG, 'fig8_classification_results.png'), format='png')
plt.close()
print("Figure 8 saved.")

# ============================================================
# Q4: COMPOSITIONAL ASSOCIATION ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("Q4: COMPOSITIONAL ASSOCIATION ANALYSIS")
print("=" * 60)

# Variation matrix per type
for gt_name, gt_full in [('High-K', '高钾'), ('Pb-Ba', '铅钡')]:
    mask = y_type == gt_full
    X_gt_norm = artifacts.loc[mask, COMPONENTS].values

    n_comp = len(COMPONENTS)
    var_matrix = np.zeros((n_comp, n_comp))
    for i in range(n_comp):
        for j in range(n_comp):
            log_ratios = np.log(np.maximum(X_gt_norm[:, i], 1e-10) / np.maximum(X_gt_norm[:, j], 1e-10))
            var_matrix[i, j] = np.var(log_ratios)

    # FIGURE 9: Variation matrix heatmaps
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(np.log1p(var_matrix), cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(n_comp)); ax.set_yticks(range(n_comp))
    ax.set_xticklabels(COMPONENTS, rotation=45, ha='right', fontsize=8)
    ax.set_yticklabels(COMPONENTS, fontsize=8)
    ax.set_title(f'Variation Matrix: var(ln(x_i/x_j)) -- {gt_name} Glass\n(Lower values = proportional co-variation)')
    plt.colorbar(im, ax=ax, label='log(1 + variance)')

    fig_num = '9a' if gt_name == 'High-K' else '9b'
    fig.savefig(os.path.join(FIG, f'fig9_{gt_name.lower()}_var_matrix.pdf'), format='pdf')
    fig.savefig(os.path.join(FIG, f'fig9_{gt_name.lower()}_var_matrix.png'), format='png')
    plt.close()
    print(f"Figure 9{gt_name[0].lower()} ({gt_name}) saved.")

# FIGURE 10: PCA biplots per type
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
for ax, (gt_name, gt_full) in zip(axes, [('High-K', '高钾'), ('Pb-Ba', '铅钡')]):
    mask = y_type == gt_full
    X_gt_clr = X_clr_art[mask]
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_gt_clr)

    weat_status = artifacts.loc[mask, 'weathering'].values
    weat_mask = np.isin(weat_status, ['风化', '严重风化'])

    ax.scatter(X_pca[~weat_mask, 0], X_pca[~weat_mask, 1],
              c='#4CAF50', label='Unweathered', alpha=0.7, s=60, edgecolors='black', linewidth=0.3)
    ax.scatter(X_pca[weat_mask, 0], X_pca[weat_mask, 1],
              c='#FF9800', label='Weathered', alpha=0.7, s=60, edgecolors='black', linewidth=0.3, marker='^')

    # Element loadings
    loadings = pca.components_.T
    for j, comp in enumerate(COMPONENTS):
        ax.arrow(0, 0, loadings[j, 0]*4, loadings[j, 1]*4, head_width=0.1, alpha=0.5, color='gray')
        ax.text(loadings[j, 0]*4.3, loadings[j, 1]*4.3, comp, fontsize=7)

    ax.set_title(f'{gt_name} Glass\n(PC1={pca.explained_variance_ratio_[0]:.1%}, PC2={pca.explained_variance_ratio_[1]:.1%})')
    ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
    ax.legend(fontsize=8)

plt.suptitle('PCA Biplots: Element Co-Variation Structure by Glass Type', fontweight='bold')
plt.tight_layout()
fig.savefig(os.path.join(FIG, 'fig10_pca_biplots.pdf'), format='pdf')
fig.savefig(os.path.join(FIG, 'fig10_pca_biplots.png'), format='png')
plt.close()
print("Figure 10 saved.")

# Permutation test for group difference
corr_hk_clr = np.corrcoef(X_clr_art[y_type == '高钾'].T)
corr_pb_clr = np.corrcoef(X_clr_art[y_type == '铅钡'].T)
T_obs = np.linalg.norm(corr_hk_clr - corr_pb_clr, 'fro')

n_perms = 5000
T_perm = []
all_indices = np.arange(len(artifacts))
hk_n = (y_type == '高钾').sum()
rng = np.random.RandomState(42)
for _ in range(n_perms):
    perm_idx = rng.permutation(all_indices)
    perm_hk = perm_idx[:hk_n]
    perm_pb = perm_idx[hk_n:]
    corr_phk = np.corrcoef(X_clr_art[perm_hk].T)
    corr_ppb = np.corrcoef(X_clr_art[perm_pb].T)
    T_perm.append(np.linalg.norm(corr_phk - corr_ppb, 'fro'))

T_perm = np.array(T_perm)
p_perm = np.mean(T_perm >= T_obs)
print(f"\nPermutation test: T_obs={T_obs:.3f}, p={p_perm:.4f} (n={n_perms})")
record("Q4_permutation_F_norm", "Q4", T_obs, "Frobenius norm", "Observed correlation matrix difference", "q4_correlation.py")
record("Q4_permutation_pvalue", "Q4", p_perm, "p-value", "Permutation test for group difference", "q4_correlation.py")

# Top CLR correlations per type
for gt_name, gt_full in [('High-K', '高钾'), ('Pb-Ba', '铅钡')]:
    mask = y_type == gt_full
    corr = np.corrcoef(X_clr_art[mask].T)
    # Find top 5 non-diagonal pairs
    pairs = []
    for i in range(len(COMPONENTS)):
        for j in range(i+1, len(COMPONENTS)):
            pairs.append((COMPONENTS[i], COMPONENTS[j], corr[i, j]))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    print(f"\nTop CLR correlations for {gt_name}:")
    for p in pairs[:5]:
        print(f"  {p[0]} ↔ {p[1]}: r={p[2]:.3f}")

# ============================================================
# SAVE RESULTS MANIFEST
# ============================================================
manifest_path = os.path.join(RES, 'RESULTS_MANIFEST.json')
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(MANIFEST, f, indent=2, ensure_ascii=False, default=str)
print(f"\nRESULTS_MANIFEST.json saved with {len(MANIFEST)} entries.")

# Save Q3 results table
q3_df = pd.DataFrame(q3_results)
q3_df.to_csv(os.path.join(RES, 'q3_classification_results.csv'), index=False, encoding='utf-8-sig')

# Save Q1B results
df_q1b.to_csv(os.path.join(RES, 'q1b_weathering_stats.csv'), index=False, encoding='utf-8-sig')

# Save perturbation results
pd.DataFrame(perturbation_results).to_csv(os.path.join(RES, 'q3_sensitivity.csv'), index=False, encoding='utf-8-sig')

print("\n" + "=" * 60)
print("EXPERIMENT COMPLETE")
print("=" * 60)
print(f"Figures: {len(os.listdir(FIG))} files in {FIG}")
print(f"Results: {len(os.listdir(RES))} files in {RES}")
