#!/usr/bin/env python3
"""q1_analysis.py - Q1a(风化关系) + Q1b(成分统计) + Q1c(风化预测)"""
import os, json, warnings, sys
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact, mannwhitneyu, ttest_ind
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns

# Force UTF-8 output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore')
WORKSPACE = r'D:\WorkSpace_MathModel\space1'
os.makedirs(f'{WORKSPACE}/figures', exist_ok=True)
os.makedirs(f'{WORKSPACE}/results', exist_ok=True)

# Load processed data
df2 = pd.read_csv(f'{WORKSPACE}/code/outputs/form2_processed.csv')
df1 = pd.read_csv(f'{WORKSPACE}/code/outputs/form1_processed.csv')
with open(f'{WORKSPACE}/code/outputs/metadata.json') as f:
    meta = json.load(f)
comp_cols = meta['comp_cols_11']
norm_cols = [f'{c}_norm' for c in comp_cols]

# Filter valid samples
df2_valid = df2[df2['_valid'] == True].copy()
print(f"Q1 analysis on {len(df2_valid)} valid samples")

# Map for readable component names (short)
comp_short = {c: c.split('(')[0] for c in comp_cols}
norm_to_comp = {n: c for n, c in zip(norm_cols, comp_cols)}

# ============================================================
# Q1a: 风化与类型/纹饰/颜色关系
# ============================================================
print("\n" + "="*60)
print("Q1a: Weathering vs Type, Decoration, Color")
print("="*60)

# Cross-tabulations
df1['表面风化_bin'] = (df1['表面风化'] == '风化').astype(int)
df1['类型_bin'] = (df1['类型'] == '铅钡').astype(int)

# 1. Weathering vs Type
ct_weather_type = pd.crosstab(df1['表面风化'], df1['类型'])
chi2, p_wt, dof, expected = chi2_contingency(ct_weather_type)
n = ct_weather_type.sum().sum()
cramers_v = np.sqrt(chi2 / (n * min(ct_weather_type.shape[0]-1, ct_weather_type.shape[1]-1)))
print(f"\n风化×类型: χ²={chi2:.2f}, p={p_wt:.4f}, Cramér's V={cramers_v:.3f}")
print(ct_weather_type)

# 2. Weathering vs Decoration
ct_weather_deco = pd.crosstab(df1['表面风化'], df1['纹饰'])
if (ct_weather_deco.values >= 5).all():
    chi2_d, p_wd = chi2_contingency(ct_weather_deco)[:2]
else:
    # Use Fisher for sparse tables
    chi2_d, p_wd = 0, fisher_exact(ct_weather_deco)[1]
print(f"\n风化×纹饰: χ²={chi2_d:.2f}, p={p_wd:.4f}")
print(ct_weather_deco)

# 3. Logistic regression
df1_q1a = df1.dropna(subset=['颜色']).copy()
le_deco = LabelEncoder()
le_color = LabelEncoder()
df1_q1a['纹饰_enc'] = le_deco.fit_transform(df1_q1a['纹饰'])
df1_q1a['颜色_enc'] = le_color.fit_transform(df1_q1a['颜色'])

X = df1_q1a[['类型_bin', '纹饰_enc', '颜色_enc']]
y = df1_q1a['表面风化_bin']

lr = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', max_iter=1000)
lr.fit(X, y)
print(f"\nLogistic Regression: coef={lr.coef_[0]}, intercept={lr.intercept_[0]:.3f}")
print(f"  Predictors: 类型, 纹饰, 颜色")
print(f"  Accuracy: {lr.score(X, y):.3f}")

# OR calculation
for i, name in enumerate(['类型(铅钡)', '纹饰(编码)', '颜色(编码)']):
    or_val = np.exp(lr.coef_[0][i])
    print(f"  {name}: OR={or_val:.2f}")

# --- FIGURE F1.1: Stacked bar ---
fig, ax = plt.subplots(figsize=(8, 5))
ct = pd.crosstab(df1['类型'], df1['表面风化'])
ct.plot(kind='bar', stacked=True, ax=ax, color=['#4CAF50', '#FF9800'])
ax.set_xlabel('Glass Type', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('Weathering Distribution by Glass Type', fontsize=13)
ax.legend(title='Weathering')
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q1a_weather_type_bar.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F1.1] Saved q1a_weather_type_bar.pdf")

# --- FIGURE F1.2: OR forest plot ---
fig, ax = plt.subplots(figsize=(7, 3))
ors = [np.exp(lr.coef_[0][i]) for i in range(3)]
names = ['Type (Lead-Barium)', 'Decoration', 'Color']
y_pos = range(len(names))
colors = ['#2196F3', '#FF9800', '#4CAF50']
ax.barh(y_pos, ors, color=colors, height=0.5)
ax.axvline(1.0, color='black', linestyle='--', linewidth=1)
ax.set_yticks(y_pos)
ax.set_yticklabels(names)
ax.set_xlabel('Odds Ratio (Weathering)')
ax.set_title('Q1a: Odds Ratios from Logistic Regression')
for i, orv in enumerate(ors):
    ax.text(orv+0.05, i, f'{orv:.2f}', va='center')
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q1a_or_forest.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F1.2] Saved q1a_or_forest.pdf")

# ============================================================
# Q1b: 分类型风化前后成分统计规律
# ============================================================
print("\n" + "="*60)
print("Q1b: Composition Statistics by Type × Weathering")
print("="*60)

# Merge type/weathering info
df2_valid = df2_valid.dropna(subset=['类型', '表面风化'])
df2_valid['group'] = df2_valid['类型'] + '_' + df2_valid['表面风化']

groups = ['高钾_无风化', '高钾_风化', '铅钡_无风化', '铅钡_风化']
group_stats = {}
for g in groups:
    mask = df2_valid['group'] == g
    n_g = mask.sum()
    stats_g = {}
    for nc, cc in zip(norm_cols, comp_cols):
        vals = df2_valid.loc[mask, nc].dropna()
        if len(vals) > 1:
            stats_g[cc] = {
                'n': len(vals), 'mean': vals.mean(), 'std': vals.std(),
                'cv': vals.std()/vals.mean() if vals.mean() > 0 else np.nan
            }
    group_stats[g] = {'n': n_g, 'components': stats_g}
    print(f"  {g}: n={n_g}")

# Effect sizes (Hedges' g) for each type: weathered vs unweathered
print("\nEffect sizes (Hedges' g, weathered vs unweathered):")
for glass_type in ['高钾', '铅钡']:
    g_un = f'{glass_type}_无风化'
    g_w = f'{glass_type}_风化'
    print(f"\n  {glass_type}:")
    for nc, cc in zip(norm_cols, comp_cols):
        vals_un = df2_valid.loc[df2_valid['group'] == g_un, nc].dropna()
        vals_w = df2_valid.loc[df2_valid['group'] == g_w, nc].dropna()
        if len(vals_un) > 1 and len(vals_w) > 1:
            # Pooled SD
            n1, n2 = len(vals_un), len(vals_w)
            s1, s2 = vals_un.std(ddof=1), vals_w.std(ddof=1)
            sp = np.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / (n1+n2-2))
            if sp > 0:
                g = (vals_un.mean() - vals_w.mean()) / sp
                print(f"    {cc.split('(')[0]:8s}: g={g:+.3f} (mean diff={vals_un.mean()-vals_w.mean():+.2f}%)")

# --- FIGURE F2.1: Boxplot matrix ---
fig, axes = plt.subplots(3, 4, figsize=(18, 12))
axes = axes.flatten()
for idx, (nc, cc) in enumerate(zip(norm_cols, comp_cols)):
    if idx >= 11:
        break
    ax = axes[idx]
    data_plot = []
    labels_plot = []
    for g in groups:
        vals = df2_valid.loc[df2_valid['group'] == g, nc].dropna()
        if len(vals) > 0:
            data_plot.append(vals.values)
            labels_plot.append(g.replace('_', '\n'))
    bp = ax.boxplot(data_plot, patch_artist=True, widths=0.6)
    ax.set_xticklabels(labels_plot, fontsize=7)
    for patch, color in zip(bp['boxes'], ['#E3F2FD','#90CAF9','#FFE0B2','#FFB74D']):
        patch.set_facecolor(color)
    ax.set_title(cc.split('(')[0], fontsize=9)
    ax.tick_params(labelsize=7)
fig.suptitle('Q1b: Composition Distribution by Type × Weathering (11 components)', fontsize=14)
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q1b_boxplot_matrix.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F2.1] Saved q1b_boxplot_matrix.pdf")

# --- FIGURE F2.2: Effect size bar chart ---
fig, ax = plt.subplots(figsize=(10, 5))
effect_data = []
for glass_type in ['高钾', '铅钡']:
    for nc, cc in zip(norm_cols, comp_cols):
        vals_un = df2_valid.loc[df2_valid['group'] == f'{glass_type}_无风化', nc].dropna()
        vals_w = df2_valid.loc[df2_valid['group'] == f'{glass_type}_风化', nc].dropna()
        if len(vals_un) > 1 and len(vals_w) > 1:
            n1, n2 = len(vals_un), len(vals_w)
            sp = np.sqrt(((n1-1)*vals_un.std(ddof=1)**2 + (n2-1)*vals_w.std(ddof=1)**2)/(n1+n2-2))
            if sp > 0:
                g = (vals_un.mean() - vals_w.mean()) / sp
                effect_data.append({'Component': cc.split('(')[0], 'Type': glass_type, "Hedges' g": g})

df_eff = pd.DataFrame(effect_data)
df_eff = df_eff.sort_values("Hedges' g", key=abs, ascending=False)
colors_bar = ['#2196F3' if t == '高钾' else '#FF9800' for t in df_eff['Type']]
ax.barh(range(len(df_eff)), df_eff["Hedges' g"].values, color=colors_bar, height=0.6)
ax.set_yticks(range(len(df_eff)))
ax.set_yticklabels([f"{r['Component']} ({r['Type']})" for _, r in df_eff.iterrows()], fontsize=8)
ax.axvline(0, color='black', linewidth=0.8)
ax.set_xlabel("Hedges' g (Weathered → Unweathered)")
ax.set_title('Q1b: Weathering Effect Size by Component')
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q1b_effect_size.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F2.2] Saved q1b_effect_size.pdf")

# ============================================================
# Q1c: 风化前成分预测
# ============================================================
print("\n" + "="*60)
print("Q1c: Pre-weathering Composition Prediction")
print("="*60)

# Find paired weathered/unweathered samples
paired_ids = []
for art_id in df2_valid['文物编号_clean'].unique():
    sub = df2_valid[df2_valid['文物编号_clean'] == art_id]
    names = sub['文物采样点'].values
    has_normal = any('严重' not in str(n) and '未' not in str(n) and '部位' not in str(n) for n in names)
    has_severe = any('严重风化' in str(n) for n in names)
    if has_normal and has_severe:
        paired_ids.append(art_id)
print(f"Direct pairs (normal→severe weathered): {paired_ids}")

# Also find weathered artifacts with 未风化点
unweathered_pairs = []
for art_id in df2_valid['文物编号_clean'].unique():
    sub = df2_valid[df2_valid['文物编号_clean'] == art_id]
    names = [str(n) for n in sub['文物采样点'].values]
    has_unweathered = any('未风化' in n for n in names)
    has_regular = any('未风化' not in n and '严重' not in n for n in names)
    if has_unweathered and not has_regular:
        # This artifact has 风化 data and 未风化点
        unweathered_pairs.append(art_id)
print(f"Artifacts with 未风化点: {unweathered_pairs}")

# Compute weathering change rates from direct pairs
print("\nWeathering change rates from direct pairs:")
change_rates = {}
for art_id in paired_ids:
    sub = df2_valid[df2_valid['文物编号_clean'] == art_id]
    pre_row = sub[~sub['文物采样点'].str.contains('严重风化|未风化', na=False)].iloc[0]
    post_row = sub[sub['文物采样点'].str.contains('严重风化', na=False)].iloc[0]
    glass_type = pre_row['类型']
    rates = {}
    for nc, cc in zip(norm_cols, comp_cols):
        pre_v = pre_row[nc] if pd.notna(pre_row[nc]) else None
        post_v = post_row[nc] if pd.notna(post_row[nc]) else None
        if pre_v is not None and post_v is not None and pre_v > 0.1:
            r = (pre_v - post_v) / pre_v  # positive = loss
            rates[cc] = r
    change_rates[art_id] = {'type': glass_type, 'rates': rates}
    print(f"  {art_id} ({glass_type}): {len(rates)} components with rates")

# Average change rates by type
type_rates = {}
for glass_type in ['高钾', '铅钡']:
    all_rates = {}
    for art_id, data in change_rates.items():
        if data['type'] == glass_type:
            for cc, r in data['rates'].items():
                if cc not in all_rates:
                    all_rates[cc] = []
                all_rates[cc].append(r)
    type_rates[glass_type] = {cc: {'mean': np.mean(rr), 'std': np.std(rr, ddof=1) if len(rr)>1 else 0, 'n': len(rr)}
                               for cc, rr in all_rates.items()}
    print(f"\n  {glass_type} avg rates:")
    for cc, v in type_rates[glass_type].items():
        print(f"    {cc.split('(')[0]:8s}: r̄={v['mean']:+.3f} (n={v['n']})")

# Bootstrap prediction intervals
print("\nBootstrap prediction for weathered samples (example on PbO for 铅钡):")
np.random.seed(42)
for art_id in paired_ids:
    sub = df2_valid[df2_valid['文物编号_clean'] == art_id]
    post_row = sub[sub['文物采样点'].str.contains('严重风化', na=False)].iloc[0]
    glass_type = post_row['类型']

    if glass_type == '铅钡':
        for nc, cc in zip(norm_cols, comp_cols):
            if 'PbO' in cc or 'SiO2' in cc:
                post_v = post_row[nc] if pd.notna(post_row[nc]) else None
                if cc in type_rates.get(glass_type, {}) and post_v is not None:
                    r_mean = type_rates[glass_type][cc]['mean']
                    r_std = max(type_rates[glass_type][cc]['std'], 0.01)
                    # Bootstrap
                    r_boot = r_mean + r_std * np.random.randn(1000)
                    pred_boot = post_v / (1 - r_boot)
                    ci_low, ci_high = np.percentile(pred_boot, [2.5, 97.5])
                    print(f"  {art_id} {cc.split('(')[0]}: post={post_v:.2f}%, pred={post_v/(1-r_mean):.2f}%, 95%CI=[{ci_low:.2f},{ci_high:.2f}]%")

# --- FIGURE F3.1: Predicted vs Actual (for paired samples) ---
fig, ax = plt.subplots(figsize=(7, 6))
all_pred, all_actual = [], []
for art_id in paired_ids:
    sub = df2_valid[df2_valid['文物编号_clean'] == art_id]
    pre_row = sub[~sub['文物采样点'].str.contains('严重风化|未风化', na=False)].iloc[0]
    post_row = sub[sub['文物采样点'].str.contains('严重风化', na=False)].iloc[0]
    glass_type = pre_row['类型']
    for nc, cc in zip(norm_cols, comp_cols):
        pre_v = pre_row[nc] if pd.notna(pre_row[nc]) else None
        post_v = post_row[nc] if pd.notna(post_row[nc]) else None
        if pre_v is not None and post_v is not None and pre_v > 0.1 and cc in type_rates.get(glass_type, {}):
            r_mean = type_rates[glass_type][cc]['mean']
            pred = post_v / (1 - r_mean) if r_mean < 1 else post_v
            all_pred.append(pred)
            all_actual.append(pre_v)

ax.scatter(all_actual, all_pred, alpha=0.6, s=40, color='#2196F3')
max_val = max(max(all_actual), max(all_pred)) * 1.1
ax.plot([0, max_val], [0, max_val], 'r--', linewidth=1, label='y=x')
ax.set_xlabel('Actual Pre-weathering (%)')
ax.set_ylabel('Predicted Pre-weathering (%)')
ax.set_title('Q1c: Predicted vs Actual (Paired Samples)')
ax.legend()
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q1c_pred_vs_actual.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("\n  [F3.1] Saved q1c_pred_vs_actual.pdf")

# --- FIGURE F3.2: Change rates per component ---
fig, ax = plt.subplots(figsize=(10, 5))
rate_data = []
for glass_type in ['铅钡']:
    for cc, v in type_rates.get(glass_type, {}).items():
        rate_data.append({'Component': cc.split('(')[0], 'Rate': v['mean'], 'SD': v['std']})
df_rate = pd.DataFrame(rate_data).sort_values('Rate')
colors_r = ['#FF9800' if r > 0 else '#4CAF50' for r in df_rate['Rate']]
ax.barh(range(len(df_rate)), df_rate['Rate'].values, color=colors_r, height=0.6,
        xerr=df_rate['SD'].values, capsize=3)
ax.set_yticks(range(len(df_rate)))
ax.set_yticklabels(df_rate['Component'].values, fontsize=9)
ax.axvline(0, color='black', linewidth=0.8)
ax.set_xlabel('Mean Change Rate (positive = loss during weathering)')
ax.set_title('Q1c: Composition Change Rates During Weathering (Pb-Ba Glass)')
plt.tight_layout()
fig.savefig(f'{WORKSPACE}/figures/q1c_change_rates.pdf', dpi=150, bbox_inches='tight')
plt.close()
print("  [F3.2] Saved q1c_change_rates.pdf")

# ============================================================
# Save Q1 results
# ============================================================
q1_results = {
    'q1a': {
        'chi2_weather_type': float(chi2), 'p_weather_type': float(p_wt), 'cramers_v': float(cramers_v),
        'chi2_weather_deco': float(chi2_d), 'p_weather_deco': float(p_wd),
        'logistic_accuracy': float(lr.score(X, y)),
        'logistic_odds_ratios': {'类型(铅钡)': float(np.exp(lr.coef_[0][0])),
                                 '纹饰(编码)': float(np.exp(lr.coef_[0][1])),
                                 '颜色(编码)': float(np.exp(lr.coef_[0][2]))}
    },
    'q1b': {
        'group_sizes': {g: group_stats[g]['n'] for g in groups},
        'effect_sizes_recorded': len(effect_data)
    },
    'q1c': {
        'direct_pairs': paired_ids,
        'unweathered_references': unweathered_pairs,
        'type_rates': {gt: {cc.split('(')[0]: {'mean': v['mean'], 'std': v['std']}
                             for cc, v in rates.items()}
                       for gt, rates in type_rates.items()}
    }
}

with open(f'{WORKSPACE}/results/q1_results.json', 'w') as f:
    json.dump(q1_results, f, ensure_ascii=False, indent=2, default=float)

print("\nQ1 analysis complete. Results in results/q1_results.json")
