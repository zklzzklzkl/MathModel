# -*- coding: utf-8 -*-
"""
Q3: 未知类别玻璃文物的成分分析与鉴别
    + Multi-model classification
    + Sensitivity analysis
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score, StratifiedKFold, LeaveOneOut
from sklearn.metrics import classification_report, confusion_matrix
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

# Load unknown samples
df_unknown = pd.read_csv('form3_unknown.csv')
df_unknown.columns = ['文物编号', '表面风化', 'SiO2', 'Na2O', 'K2O', 'CaO', 'MgO',
                       'Al2O3', 'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']

# ============================================================
# 3.1 准备训练数据
# ============================================================
print("=" * 60)
print("3.1 训练数据准备")
print("=" * 60)

# Use all valid data from Form 2 (not just regular samples)
df_train_all = df[df['有效数据']].copy()
for col in component_cols:
    df_train_all[col] = df_train_all[col].fillna(0)

# Also include weathered and unweathered points for robustness
# Use all sampling points as training data
X_train = df_train_all[component_cols].values
y_train = df_train_all['类型'].values

print(f"Training samples: {len(X_train)}")
print(f"  高钾: {sum(y_train == '高钾')}")
print(f"  铅钡: {sum(y_train == '铅钡')}")

# Standardize
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# ============================================================
# 3.2 多模型分类与交叉验证
# ============================================================
print("\n" + "=" * 60)
print("3.2 多模型交叉验证")
print("=" * 60)

models = {
    'KNN (k=3)': KNeighborsClassifier(n_neighbors=3),
    'KNN (k=5)': KNeighborsClassifier(n_neighbors=5),
    'LDA': LDA(),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', probability=True, random_state=42),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("5-Fold Cross-Validation Results:")
print(f"{'Model':<25s} {'Accuracy':>10s} {'Std':>8s}")
print("-" * 45)

best_model = None
best_acc = 0
for name, model in models.items():
    scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    print(f"{name:<25s} {scores.mean():>10.4f} {scores.std():>8.4f}")
    if scores.mean() > best_acc:
        best_acc = scores.mean()
        best_model = name

print(f"\nBest model: {best_model} (accuracy = {best_acc:.4f})")

# ============================================================
# 3.3 LDA 判别分析
# ============================================================
print("\n" + "=" * 60)
print("3.3 LDA 判别分析")
print("=" * 60)

lda = LDA()
lda.fit(X_train_scaled, y_train)
print(f"LDA classes: {lda.classes_}")
print(f"LDA explained variance ratio: {lda.explained_variance_ratio_}")
print(f"LDA coefficients:")
lda_coef = pd.DataFrame({
    'Component': component_cols,
    'Coefficient': lda.coef_[0]
}).sort_values('Coefficient', key=abs, ascending=False)
print(lda_coef.to_string())

# ============================================================
# 3.4 预测未知样品
# ============================================================
print("\n" + "=" * 60)
print("3.4 预测未知样品")
print("=" * 60)

# Prepare unknown data
df_unknown_filled = df_unknown.copy()
for col in component_cols:
    df_unknown_filled[col] = df_unknown_filled[col].fillna(0)

X_unknown = df_unknown_filled[component_cols].values
X_unknown_scaled = scaler.transform(X_unknown)

# Predict with all models
results = []
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(X_unknown_scaled)
        preds = model.predict(X_unknown_scaled)
        for i in range(len(df_unknown)):
            class_idx = list(model.classes_).index(preds[i]) if preds[i] in model.classes_ else 0
            results.append({
                'Model': name,
                'Sample': df_unknown.iloc[i]['文物编号'],
                'Weathering': df_unknown.iloc[i]['表面风化'],
                'Predicted': preds[i],
                'Confidence': probs[i][class_idx],
                'Prob_高钾': probs[i][list(model.classes_).index('高钾')] if '高钾' in model.classes_ else 0,
                'Prob_铅钡': probs[i][list(model.classes_).index('铅钡')] if '铅钡' in model.classes_ else 0,
            })
    else:
        preds = model.predict(X_unknown_scaled)
        for i in range(len(df_unknown)):
            results.append({
                'Model': name,
                'Sample': df_unknown.iloc[i]['文物编号'],
                'Weathering': df_unknown.iloc[i]['表面风化'],
                'Predicted': preds[i],
                'Confidence': 1.0,
                'Prob_高钾': 1.0 if preds[i] == '高钾' else 0.0,
                'Prob_铅钡': 1.0 if preds[i] == '铅钡' else 0.0,
            })

df_results = pd.DataFrame(results)

# Consensus prediction
print("\n=== Consensus Predictions ===")
for sample in df_unknown['文物编号']:
    sample_results = df_results[df_results['Sample'] == sample]
    print(f"\n{sample} ({df_unknown[df_unknown['文物编号']==sample]['表面风化'].values[0]}):")
    for _, row in sample_results.iterrows():
        print(f"  {row['Model']:<25s}: {row['Predicted']:<6s} (confidence: {row['Confidence']:.3f})")

    # Voting
    votes = sample_results['Predicted'].value_counts()
    majority = votes.index[0]
    print(f"  → Majority vote: {majority} ({votes[majority]}/{len(sample_results)} models)")

# Final classification using best model (LDA or Random Forest)
final_model = RandomForestClassifier(n_estimators=100, random_state=42)
final_model.fit(X_train_scaled, y_train)
final_preds = final_model.predict(X_unknown_scaled)
final_probs = final_model.predict_proba(X_unknown_scaled)

print("\n" + "=" * 60)
print("FINAL CLASSIFICATION (Random Forest)")
print("=" * 60)
for i in range(len(df_unknown)):
    class_idx = list(final_model.classes_).index(final_preds[i])
    print(f"{df_unknown.iloc[i]['文物编号']}: {final_preds[i]} "
          f"(confidence: {final_probs[i][class_idx]:.4f}), "
          f"weathering: {df_unknown.iloc[i]['表面风化']}")

# Also provide detailed rationale for each classification
print("\n=== Detailed Classification Rationale ===")
for i, row in df_unknown.iterrows():
    print(f"\n{row['文物编号']} ({row['表面风化']}):")
    # Key indicators
    k2o = row['K2O'] if pd.notna(row['K2O']) else 0
    pbo = row['PbO'] if pd.notna(row['PbO']) else 0
    bao = row['BaO'] if pd.notna(row['BaO']) else 0

    if k2o > 1 or (pbo < 1 and bao < 1):
        type_signal = "高钾 indicator (K2O present, PbO/BaO negligible)"
    elif pbo > 5 or bao > 2:
        type_signal = "铅钡 indicator (PbO/BaO present)"
    else:
        type_signal = "ambiguous"

    print(f"  K2O={k2o:.2f}, PbO={pbo:.2f}, BaO={bao:.2f} → {type_signal}")

# ============================================================
# 3.5 敏感性分析
# ============================================================
print("\n" + "=" * 60)
print("3.5 敏感性分析")
print("=" * 60)

# 1. Leave-one-out cross-validation
print("\n=== Leave-One-Out CV ===")
loo = LeaveOneOut()
loo_scores = cross_val_score(
    RandomForestClassifier(n_estimators=100, random_state=42),
    X_train_scaled, y_train, cv=loo, scoring='accuracy'
)
print(f"LOO Accuracy: {loo_scores.mean():.4f} (±{loo_scores.std():.4f})")

# 2. Sensitivity to missing data
print("\n=== Sensitivity to Missing SiO2 ===")
component_cols_no_sio2 = [c for c in component_cols if c != 'SiO2']
X_train_no_sio2 = df_train_all[component_cols_no_sio2].values
X_unknown_no_sio2 = df_unknown_filled[component_cols_no_sio2].values

scaler2 = StandardScaler()
X_train_no_sio2_s = scaler2.fit_transform(X_train_no_sio2)
X_unknown_no_sio2_s = scaler2.transform(X_unknown_no_sio2)

rf_no_sio2 = RandomForestClassifier(n_estimators=100, random_state=42)
rf_no_sio2.fit(X_train_no_sio2_s, y_train)
preds_no_sio2 = rf_no_sio2.predict(X_unknown_no_sio2_s)

for i in range(len(df_unknown)):
    print(f"  {df_unknown.iloc[i]['文物编号']}: with SiO2={final_preds[i]}, "
          f"without SiO2={preds_no_sio2[i]}")

# 3. Only using K2O, PbO, BaO (simplest rule)
print("\n=== Sensitivity: K2O + PbO + BaO only ===")
key_cols = ['K2O', 'PbO', 'BaO']
X_train_key = df_train_all[key_cols].values
X_unknown_key = df_unknown_filled[key_cols].values

scaler3 = StandardScaler()
X_train_key_s = scaler3.fit_transform(X_train_key)
X_unknown_key_s = scaler3.transform(X_unknown_key)

rf_key = RandomForestClassifier(n_estimators=100, random_state=42)
rf_key.fit(X_train_key_s, y_train)
preds_key = rf_key.predict(X_unknown_key_s)

for i in range(len(df_unknown)):
    print(f"  {df_unknown.iloc[i]['文物编号']}: full={final_preds[i]}, "
          f"key3={preds_key[i]}")

# 4. LDA decision boundary visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# LDA scores
lda_scores = lda.transform(X_train_scaled)
ax = axes[0, 0]
for gtype, color in [('高钾', '#FF6B6B'), ('铅钡', '#4ECDC4')]:
    mask = y_train == gtype
    ax.hist(lda_scores[mask, 0], bins=15, alpha=0.6, color=color, label=gtype)
ax.set_xlabel('LDA Score', fontsize=11)
ax.set_ylabel('Count', fontsize=11)
ax.set_title('LDA Score Distribution', fontsize=13, fontweight='bold')
ax.legend()

# Project unknown onto LDA
ax = axes[0, 1]
lda_unknown = lda.transform(X_unknown_scaled)
for i, row in df_unknown.iterrows():
    ax.axvline(x=lda_unknown[i, 0], color='#45B7D1' if final_preds[i] == '高钾' else '#F7DC6F',
               linestyle='--', linewidth=2, alpha=0.7)
    ax.text(lda_unknown[i, 0], 1 + i * 0.3, row['文物编号'],
            fontsize=8, ha='center', rotation=45,
            color='#45B7D1' if final_preds[i] == '高钾' else '#F7DC6F',
            fontweight='bold')

for gtype, color in [('高钾', '#FF6B6B'), ('铅钡', '#4ECDC4')]:
    mask = y_train == gtype
    ax.hist(lda_scores[mask, 0], bins=15, alpha=0.4, color=color, label=f'Train-{gtype}')
ax.set_xlabel('LDA Score', fontsize=11)
ax.set_title('Unknown Samples on LDA Axis', fontsize=13, fontweight='bold')
ax.legend(fontsize=8)

# Cross-validation accuracy comparison
ax = axes[1, 0]
model_names = list(models.keys())
cv_means = []
cv_stds = []
for name in model_names:
    scores = cross_val_score(models[name], X_train_scaled, y_train, cv=cv, scoring='accuracy')
    cv_means.append(scores.mean())
    cv_stds.append(scores.std())

colors_bar = ['#FF6B6B' if m == best_model else '#4ECDC4' for m in model_names]
bars = ax.barh(model_names, cv_means, xerr=cv_stds, color=colors_bar, capsize=3)
ax.set_xlabel('Accuracy', fontsize=11)
ax.set_title('Model Comparison (5-Fold CV)', fontsize=13, fontweight='bold')
ax.set_xlim(0.7, 1.05)
for bar, v in zip(bars, cv_means):
    ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
            f'{v:.3f}', va='center', fontsize=9)

# Classification confidence
ax = axes[1, 1]
sample_names = df_unknown['文物编号'].values
confidences = []
pred_types = []
for i, sample in enumerate(sample_names):
    ci = list(final_model.classes_).index(final_preds[i])
    confidences.append(final_probs[i][ci])
    pred_types.append(final_preds[i])

colors_conf = ['#FF6B6B' if p == '高钾' else '#4ECDC4' for p in pred_types]
bars = ax.bar(sample_names, confidences, color=colors_conf, edgecolor='black')
ax.set_xlabel('Sample', fontsize=11)
ax.set_ylabel('Confidence', fontsize=11)
ax.set_title('Classification Confidence for Unknown Samples', fontsize=13, fontweight='bold')
ax.set_ylim(0, 1.1)
for bar, v in zip(bars, confidences):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{v:.2f}', ha='center', fontsize=9)
# Add prediction label
for bar, p in zip(bars, pred_types):
    ax.text(bar.get_x() + bar.get_width()/2, 0.05, p, ha='center', fontsize=9,
            color='white', fontweight='bold', rotation=90)

plt.suptitle('Unknown Sample Classification Analysis',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('output_figures/q3_classification.png')
plt.close()
print("→ Figure saved: q3_classification.png")

# Save results
df_results.to_csv('q3_classification_results.csv', index=False, encoding='utf-8-sig')
print("\n→ Results saved to q3_classification_results.csv")

print("\n" + "=" * 60)
print("Q3 ANALYSIS COMPLETE")
print("=" * 60)
