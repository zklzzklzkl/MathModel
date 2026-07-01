#!/usr/bin/env python3
"""preprocessing.py - 数据清洗、归一化、缺失处理"""
import json, os, sys
import numpy as np
import pandas as pd

WORKSPACE = r'D:\WorkSpace_MathModel\space1'
DATA_FILE = r'D:\WorkSpace_MathModel\workspace\_data_full.json'

os.makedirs(f'{WORKSPACE}/code/outputs', exist_ok=True)
os.makedirs(f'{WORKSPACE}/results', exist_ok=True)

# Load data
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    raw = json.load(f)

# Parse Form 1
h1 = raw['表单1'][0]
df1 = pd.DataFrame(raw['表单1'][1:], columns=h1)

# Parse Form 2
h2 = raw['表单2'][0]
df2 = pd.DataFrame(raw['表单2'][1:], columns=h2)

# Parse Form 3
h3 = raw['表单3'][0]
df3 = pd.DataFrame(raw['表单3'][1:], columns=h3)

# Component columns
comp_cols_all = [c for c in df2.columns[1:]]
exclude = ['二氧化硫(SO2)', '氧化锡(SnO2)', '氧化钠(Na2O)']
comp_cols_11 = [c for c in comp_cols_all if c not in exclude]

print(f"Form1: {df1.shape}, Form2: {df2.shape}, Form3: {df3.shape}")
print(f"11 modeling components: {comp_cols_11}")

# === Validity check ===
def check_valid(row):
    vals = [v for v in row[1:] if pd.notna(v)]
    if not vals:
        return False
    s = sum(vals)
    return 85.0 <= s <= 105.0

df2['_valid'] = df2.apply(check_valid, axis=1)
print(f"Valid samples: {df2['_valid'].sum()}/{len(df2)}")

# === Normalization ===
def normalize_row(row, cols):
    vals = [row[c] if pd.notna(row[c]) else 0.0 for c in cols]
    total = sum(vals)
    if total == 0:
        return [None]*len(cols)
    return [v/total*100 if total > 0 else None for v in vals]

norm_vals = df2.apply(lambda r: normalize_row(r, comp_cols_11), axis=1, result_type='expand')
norm_vals.columns = [f'{c}_norm' for c in comp_cols_11]
df2_norm = pd.concat([df2[['文物采样点']], norm_vals, df2['_valid']], axis=1)

# Normalize Form3
norm_vals3 = df3.apply(lambda r: normalize_row(r, comp_cols_11), axis=1, result_type='expand')
norm_vals3.columns = [f'{c}_norm' for c in comp_cols_11]
df3_norm = pd.concat([df3[['文物编号', '表面风化']], norm_vals3], axis=1)

# Extract base artifact ID (e.g., '03部位1' -> '03')
def extract_aid(name):
    s = str(name)
    for suffix in ['部位1','部位2','严重风化点','未风化点','未风化点1','未风化点2']:
        s = s.replace(suffix, '')
    return s

df2_norm['文物编号_clean'] = df2_norm['文物采样点'].apply(extract_aid)

# Merge with Form1 metadata
df2_norm = df2_norm.merge(df1, left_on='文物编号_clean', right_on='文物编号', how='left', suffixes=('', '_f1'))

# === Missing value summary ===
print("\nMissing rates (Form2, 11 components):")
for c in comp_cols_11:
    missing = df2[c].isna().sum()
    print(f"  {c}: {missing}/{len(df2)} ({100*missing/len(df2):.1f}%)")

# Save processed data
df2_norm.to_csv(f'{WORKSPACE}/code/outputs/form2_processed.csv', index=False)
df3_norm.to_csv(f'{WORKSPACE}/code/outputs/form3_processed.csv', index=False)
df1.to_csv(f'{WORKSPACE}/code/outputs/form1_processed.csv', index=False)

# Save component metadata
with open(f'{WORKSPACE}/code/outputs/metadata.json', 'w') as f:
    json.dump({
        'comp_cols_11': comp_cols_11,
        'excluded': exclude,
        'n_form1': len(df1),
        'n_form2_valid': int(df2['_valid'].sum()),
        'n_form3': len(df3_norm)
    }, f, ensure_ascii=False, indent=2)

print("\nPreprocessing complete. Outputs in code/outputs/")
