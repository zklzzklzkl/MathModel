# -*- coding: utf-8 -*-
"""
Q1: 表面风化与玻璃类型、纹饰和颜色的关系分析
    + 化学成分统计规律
    + 预测风化前化学成分含量
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'

# Load cleaned data
df = pd.read_csv('cleaned_data.csv')
# Restore Chinese column names
cols_map = {
    '文物采样点': '文物采样点', 'SiO2': 'SiO2', 'Na2O': 'Na2O', 'K2O': 'K2O',
    'CaO': 'CaO', 'MgO': 'MgO', 'Al2O3': 'Al2O3', 'Fe2O3': 'Fe2O3',
    'CuO': 'CuO', 'PbO': 'PbO', 'BaO': 'BaO', 'P2O5': 'P2O5',
    'SrO': 'SrO', 'SnO2': 'SnO2', 'SO2': 'SO2',
    '文物编号': '文物编号', '采样类型': '采样类型',
    '类型': '类型', '纹饰': '纹饰', '颜色': '颜色', '表面风化': '表面风化',
    '成分总和': '成分总和', '有效数据': '有效数据'
}

component_cols = ['SiO2', 'Na2O', 'K2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3',
                  'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']

# ============================================================
# 1.1 表面风化与玻璃类型的关系
# ============================================================
print("=" * 60)
print("1.1 表面风化 vs 玻璃类型")
print("=" * 60)

# Use unique artifacts (not sampling points) for this analysis
df_artifacts = df[['文物编号', '类型', '纹饰', '颜色', '表面风化']].drop_duplicates()

# Contingency table: 风化 × 类型
ct_type = pd.crosstab(df_artifacts['表面风化'], df_artifacts['类型'])
print("\nContingency table (风化 × 类型):")
print(ct_type)

# Chi-square test
chi2, p_val, dof, expected = chi2_contingency(ct_type)
print(f"\nChi-square: {chi2:.4f}, p-value: {p_val:.6f}, dof: {dof}")
print("Significant!" if p_val < 0.05 else "Not significant at 0.05")

# Cramér's V
n = ct_type.sum().sum()
cramers_v = np.sqrt(chi2 / (n * min(ct_type.shape[0]-1, ct_type.shape[1]-1)))
print(f"Cramér's V: {cramers_v:.4f}")

# Bar chart: weathering proportion by type
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Count plot
ct_type_prop = ct_type.div(ct_type.sum(axis=1), axis=0)
ct_type_prop.plot(kind='bar', stacked=True, ax=axes[0], color=['#4ECDC4', '#FF6B6B'])
axes[0].set_title('Weathering Status by Glass Type', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Surface Weathering')
axes[0].set_ylabel('Proportion')
axes[0].legend(title='Glass Type')
axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=0)

# Type proportion by weathering
ct_type2 = ct_type.div(ct_type.sum(axis=0), axis=1)
ct_type2.plot(kind='bar', ax=axes[1], color=['#45B7D1', '#F7DC6F'])
axes[1].set_title('Glass Type by Weathering Status', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Glass Type')
axes[1].set_ylabel('Proportion')
axes[1].legend(title='Weathering')
axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=0)

plt.tight_layout()
plt.savefig('output_figures/q1_weathering_type.png')
plt.close()
print("→ Figure saved: q1_weathering_type.png")

# ============================================================
# 1.2 表面风化与纹饰的关系
# ============================================================
print("\n" + "=" * 60)
print("1.2 表面风化 vs 纹饰")
print("=" * 60)

ct_decoration = pd.crosstab(df_artifacts['表面风化'], df_artifacts['纹饰'])
print("\nContingency table (风化 × 纹饰):")
print(ct_decoration)

chi2_d, p_val_d, dof_d, _ = chi2_contingency(ct_decoration)
print(f"\nChi-square: {chi2_d:.4f}, p-value: {p_val_d:.6f}")
n_d = ct_decoration.sum().sum()
cramers_v_d = np.sqrt(chi2_d / (n_d * min(ct_decoration.shape[0]-1, ct_decoration.shape[1]-1)))
print(f"Cramér's V: {cramers_v_d:.4f}")

# ============================================================
# 1.3 表面风化与颜色的关系
# ============================================================
print("\n" + "=" * 60)
print("1.3 表面风化 vs 颜色")
print("=" * 60)

ct_color = pd.crosstab(df_artifacts['表面风化'], df_artifacts['颜色'])
print("\nContingency table (风化 × 颜色):")
print(ct_color)

# Filter colors with enough samples
color_counts = df_artifacts['颜色'].value_counts()
valid_colors = color_counts[color_counts >= 2].index
df_color_filtered = df_artifacts[df_artifacts['颜色'].isin(valid_colors)]
ct_color_f = pd.crosstab(df_color_filtered['表面风化'], df_color_filtered['颜色'])

if ct_color_f.shape[0] >= 2 and ct_color_f.shape[1] >= 2:
    chi2_c, p_val_c, dof_c, _ = chi2_contingency(ct_color_f)
    print(f"\nChi-square (filtered): {chi2_c:.4f}, p-value: {p_val_c:.6f}")
    n_c = ct_color_f.sum().sum()
    cramers_v_c = np.sqrt(chi2_c / (n_c * min(ct_color_f.shape[0]-1, ct_color_f.shape[1]-1)))
    print(f"Cramér's V: {cramers_v_c:.4f}")

# Visualizations
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Weathering × Decoration
ct_decoration.plot(kind='bar', stacked=True, ax=axes[0, 0], color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
axes[0, 0].set_title('Weathering by Decoration (纹饰)', fontsize=13, fontweight='bold')
axes[0, 0].set_xlabel('Weathering Status')
axes[0, 0].set_ylabel('Count')
axes[0, 0].legend(title='Decoration')
axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=0)

# Weathering × Color (filtered)
ct_color_f_prop = ct_color_f.div(ct_color_f.sum(axis=1), axis=0)
ct_color_f_prop.plot(kind='bar', ax=axes[0, 1], stacked=True)
axes[0, 1].set_title('Weathering by Color', fontsize=13, fontweight='bold')
axes[0, 1].set_xlabel('Weathering Status')
axes[0, 1].set_ylabel('Proportion')
axes[0, 1].legend(title='Color', bbox_to_anchor=(1.02, 1), loc='upper left')
axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=0)

# Summary of weathering proportions by type
type_weather = pd.crosstab(df_artifacts['类型'], df_artifacts['表面风化'], normalize='index')
type_weather.plot(kind='bar', ax=axes[1, 0], color=['#45B7D1', '#FF6B6B'])
axes[1, 0].set_title('Weathering Proportion by Glass Type', fontsize=13, fontweight='bold')
axes[1, 0].set_xlabel('Glass Type')
axes[1, 0].set_ylabel('Proportion')
axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=0)
for container in axes[1, 0].containers:
    axes[1, 0].bar_label(container, fmt='%.1f%%', fontsize=9)

# Weathering by decoration proportion
dec_weather = pd.crosstab(df_artifacts['纹饰'], df_artifacts['表面风化'], normalize='index')
dec_weather.plot(kind='bar', ax=axes[1, 1], color=['#45B7D1', '#FF6B6B'])
axes[1, 1].set_title('Weathering Proportion by Decoration', fontsize=13, fontweight='bold')
axes[1, 1].set_xlabel('Decoration')
axes[1, 1].set_ylabel('Proportion')
axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=0)
for container in axes[1, 1].containers:
    axes[1, 1].bar_label(container, fmt='%.1f%%', fontsize=9)

plt.tight_layout()
plt.savefig('output_figures/q1_weathering_relationships.png')
plt.close()
print("→ Figure saved: q1_weathering_relationships.png")

# ============================================================
# 1.4 化学成分含量统计规律 (按类型和风化状态分组)
# ============================================================
print("\n" + "=" * 60)
print("1.4 化学成分统计规律")
print("=" * 60)

# Use non-special sampling points (普通采样) for clean analysis
df_regular = df[df['采样类型'] == '普通采样'].copy()
print(f"Regular samples: {len(df_regular)}")

# Group by type and weathering
groups = df_regular.groupby(['类型', '表面风化'])

# Key components for analysis
key_components = ['SiO2', 'K2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SO2']

print("\n=== Mean composition by type and weathering ===")
mean_comp = groups[key_components].mean()
print(mean_comp.to_string())

print("\n=== Std composition by type and weathering ===")
std_comp = groups[key_components].std()
print(std_comp.to_string())

# Box plots for key components
fig, axes = plt.subplots(3, 4, figsize=(18, 14))
axes = axes.flatten()

plot_components = ['SiO2', 'K2O', 'CaO', 'Al2O3', 'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SO2', 'MgO', 'Na2O']

for i, comp in enumerate(plot_components):
    if i < len(axes):
        ax = axes[i]
        # Create a combined category
        df_regular_plot = df_regular.copy()
        df_regular_plot['Category'] = df_regular_plot['类型'] + '-' + df_regular_plot['表面风化']
        order = ['高钾-无风化', '高钾-风化', '铅钡-无风化', '铅钡-风化']
        available = [o for o in order if o in df_regular_plot['Category'].values]

        data_list = [df_regular_plot[df_regular_plot['Category'] == cat][comp].dropna().values
                     for cat in available]
        bp = ax.boxplot(data_list, patch_artist=True, widths=0.6)
        colors = ['#4ECDC4', '#FF6B6B', '#45B7D1', '#F7DC6F'][:len(available)]
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_xticklabels(available, rotation=30, fontsize=8)
        ax.set_title(comp, fontsize=11, fontweight='bold')
        ax.set_ylabel('%')

# Hide unused subplots
for j in range(len(plot_components), len(axes)):
    axes[j].set_visible(False)

plt.suptitle('Chemical Composition Distribution by Glass Type and Weathering',
             fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('output_figures/q1_composition_boxplots.png')
plt.close()
print("→ Figure saved: q1_composition_boxplots.png")

# Statistical test: Mann-Whitney U test for weathered vs unweathered within each type
print("\n=== Mann-Whitney U test: Weathered vs Unweathered ===")
for glass_type in ['高钾', '铅钡']:
    print(f"\n--- {glass_type} glass ---")
    df_type = df_regular[df_regular['类型'] == glass_type]
    weathered = df_type[df_type['表面风化'] == '风化']
    unweathered = df_type[df_type['表面风化'] == '无风化']

    if len(weathered) >= 3 and len(unweathered) >= 3:
        for comp in key_components:
            w_vals = weathered[comp].dropna().values
            u_vals = unweathered[comp].dropna().values
            if len(w_vals) >= 3 and len(u_vals) >= 3:
                stat, p = stats.mannwhitneyu(w_vals, u_vals, alternative='two-sided')
                sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
                if sig:
                    mean_w = np.mean(w_vals)
                    mean_u = np.mean(u_vals)
                    direction = "↑" if mean_w > mean_u else "↓"
                    print(f"  {comp}: weathered={mean_w:.1f}, unweathered={mean_u:.1f} {direction} p={p:.4f} {sig}")

# ============================================================
# 1.5 预测风化前化学成分含量
# ============================================================
print("\n" + "=" * 60)
print("1.5 预测风化前化学成分含量")
print("=" * 60)

# Use paired data: artifacts with both weathered and unweathered measurements
# Key pairs: 49/49未风化点, 50/50未风化点
# Also consider: artifacts where we have both weathered and 严重风化点 (08, 26, 54)
# These give us weathering effect information

# Find all paired samples
paired_data = []
for art_id in df['文物编号'].unique():
    art_samples = df[df['文物编号'] == art_id]
    types = art_samples['采样类型'].values

    # Check for weathered + unweathered pair
    has_weathered = any(t in ['普通采样'] for t in types) and \
                    df[df['文物编号'] == art_id]['表面风化'].values[0] == '风化'
    has_unweathered = any(t == '未风化' for t in types)

    if has_weathered and has_unweathered:
        weathered_sample = art_samples[art_samples['采样类型'] == '普通采样']
        unweathered_sample = art_samples[art_samples['采样类型'] == '未风化']
        if len(weathered_sample) > 0 and len(unweathered_sample) > 0:
            paired_data.append({
                'id': art_id,
                'weathered': weathered_sample.iloc[0],
                'unweathered': unweathered_sample.iloc[0]
            })
            print(f"Paired sample: {art_id}")
            print(f"  Weathered (sum={weathered_sample.iloc[0]['成分总和']:.1f}): "
                  f"SiO2={weathered_sample.iloc[0]['SiO2']:.1f}, PbO={weathered_sample.iloc[0]['PbO']:.1f}")
            print(f"  Unweathered (sum={unweathered_sample.iloc[0]['成分总和']:.1f}): "
                  f"SiO2={unweathered_sample.iloc[0]['SiO2']:.1f}, PbO={unweathered_sample.iloc[0]['PbO']:.1f}")

# Compute weathering effect ratios
# For each component, ratio = unweathered / (weathered + epsilon)
# We'll use this to predict pre-weathering composition
print("\n=== Weathering Effect Ratios (Unweathered / Weathered) ===")
weathering_ratios = {}
for comp in component_cols:
    ratios = []
    for pair in paired_data:
        w_val = pair['weathered'][comp]
        u_val = pair['unweathered'][comp]
        if pd.notna(w_val) and pd.notna(u_val) and w_val > 0.01 and u_val > 0.01:
            ratios.append(u_val / w_val)
    if len(ratios) >= 1:
        weathering_ratios[comp] = {
            'mean_ratio': np.mean(ratios),
            'std_ratio': np.std(ratios),
            'n_pairs': len(ratios),
            'ratios': ratios
        }
        print(f"  {comp}: mean ratio = {np.mean(ratios):.3f} ± {np.std(ratios):.3f} (n={len(ratios)})")

# Build prediction model
# For weathered samples, predict pre-weathering composition
# Strategy: use component-specific ratios where available, otherwise use type-specific averages

def predict_pre_weathering(weathered_sample, glass_type, ratios_dict):
    """Predict pre-weathering composition for a weathered sample."""
    predictions = {}
    for comp in component_cols:
        w_val = weathered_sample[comp]
        if pd.isna(w_val) or w_val <= 0:
            # If component not detected in weathered, likely also near 0 in unweathered
            predictions[comp] = 0.0
        elif comp in ratios_dict:
            predictions[comp] = w_val * ratios_dict[comp]['mean_ratio']
        else:
            predictions[comp] = w_val  # no correction available

    # Re-normalize to 100%
    total = sum(predictions.values())
    if total > 0:
        for comp in predictions:
            predictions[comp] = predictions[comp] / total * 100

    return predictions

# Test prediction on paired samples (validation)
print("\n=== Prediction Validation ===")
for pair in paired_data:
    w_sample = pair['weathered']
    u_sample = pair['unweathered']
    pred = predict_pre_weathering(w_sample, w_sample['类型'], weathering_ratios)

    # Compare predicted vs actual for key components
    print(f"\nArtifact {pair['id']}:")
    for comp in ['SiO2', 'K2O', 'CaO', 'Al2O3', 'PbO', 'BaO', 'P2O5']:
        actual = u_sample[comp] if pd.notna(u_sample[comp]) else 0
        predicted = pred.get(comp, 0)
        if actual > 0.5 or predicted > 0.5:
            print(f"  {comp}: predicted={predicted:.1f}, actual={actual:.1f}, "
                  f"error={abs(predicted-actual):.1f}")

# Predict for all weathered samples
print("\n=== Predicted Pre-Weathering Composition for Weathered Samples ===")
weathered_samples = df_regular[df_regular['表面风化'] == '风化'].copy()
predictions_list = []
for idx, row in weathered_samples.iterrows():
    pred = predict_pre_weathering(row, row['类型'], weathering_ratios)
    pred['文物编号'] = row['文物编号']
    pred['类型'] = row['类型']
    predictions_list.append(pred)

df_predictions = pd.DataFrame(predictions_list)
print(f"Predicted for {len(df_predictions)} weathered samples")

# Save predictions
df_predictions.to_csv('q1_predictions.csv', index=False, encoding='utf-8-sig')
print("→ Predictions saved to q1_predictions.csv")

# Visualization: actual weathered vs predicted unweathered for key components
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

for i, glass_type in enumerate(['高钾', '铅钡']):
    ax = axes[i // 2, i % 2]
    df_type_weathered = df_regular[(df_regular['类型'] == glass_type) & (df_regular['表面风化'] == '风化')]
    df_type_unweathered = df_regular[(df_regular['类型'] == glass_type) & (df_regular['表面风化'] == '无风化')]

    comps = ['SiO2', 'K2O', 'PbO', 'BaO']
    x = np.arange(len(comps))
    width = 0.25

    # Actual weathered mean
    w_means = [df_type_weathered[c].mean() for c in comps]
    # Actual unweathered mean
    u_means = [df_type_unweathered[c].mean() for c in comps]

    bars1 = ax.bar(x - width, w_means, width, label='Weathered (actual)', color='#FF6B6B', alpha=0.8)
    bars2 = ax.bar(x, u_means, width, label='Unweathered (actual)', color='#4ECDC4', alpha=0.8)

    ax.set_title(f'{glass_type} Glass', fontsize=13, fontweight='bold')
    ax.set_ylabel('Content (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(comps)
    ax.legend()

    # Add value labels
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=8)

# Summary: weathering effect visualization
ax = axes[1, 1]
# For lead-barium glass, show the exchange pattern
df_pb = df_regular[df_regular['类型'] == '铅钡']
pb_weather = df_pb.groupby('表面风化')[['SiO2', 'PbO', 'BaO', 'P2O5']].mean()
pb_weather.plot(kind='bar', ax=ax, color=['#45B7D1', '#FF6B6B', '#4ECDC4', '#F7DC6F'])
ax.set_title('Lead-Barium Glass: Key Components by Weathering', fontsize=13, fontweight='bold')
ax.set_ylabel('Mean Content (%)')
ax.set_xlabel('Weathering Status')
ax.legend(loc='upper right')
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)

plt.suptitle('Weathering Effect on Chemical Composition', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('output_figures/q1_weathering_prediction.png')
plt.close()
print("→ Figure saved: q1_weathering_prediction.png")

print("\n" + "=" * 60)
print("Q1 ANALYSIS COMPLETE")
print("=" * 60)
