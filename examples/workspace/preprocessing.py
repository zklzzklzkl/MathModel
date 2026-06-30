# -*- coding: utf-8 -*-
"""
2022 CUMCM Problem C: 古代玻璃制品的成分分析与鉴别
Data Preprocessing Module
"""
import pandas as pd
import numpy as np

# ============================================================
# 0. DATA LOADING
# ============================================================
print("=" * 60)
print("DATA LOADING AND PREPROCESSING")
print("=" * 60)

# Load Form 1: Basic info
df_info = pd.read_csv('form1_basic_info.csv')
# Rename columns (the CSV has proper Chinese headers)
expected_cols = ['文物编号', '纹饰', '类型', '颜色', '表面风化']
df_info.columns = expected_cols
# Ensure 文物编号 is string with zero-padding
df_info['文物编号'] = df_info['文物编号'].astype(str).str.zfill(2)

print(f"\nForm 1 loaded: {df_info.shape[0]} artifacts")
print(df_info.to_string(max_rows=10))
print(f"\nTypes: {df_info['类型'].value_counts().to_dict()}")
print(f"纹饰: {df_info['纹饰'].value_counts().to_dict()}")
print(f"Weathering: {df_info['表面风化'].value_counts().to_dict()}")
print(f"Colors: {df_info['颜色'].value_counts().to_dict()}")

# Load Form 2: Chemical composition
df_comp = pd.read_csv('form2_composition.csv')
comp_cols_orig = ['文物采样点', 'SiO2', 'Na2O', 'K2O', 'CaO', 'MgO', 'Al2O3',
                   'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']
df_comp.columns = comp_cols_orig
print(f"\nForm 2 loaded: {df_comp.shape[0]} sampling points")

# Load Form 3: Unknown samples
df_unknown = pd.read_csv('form3_unknown.csv')
unknown_cols = ['文物编号', '表面风化', 'SiO2', 'Na2O', 'K2O', 'CaO', 'MgO',
                'Al2O3', 'Fe2O3', 'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']
df_unknown.columns = unknown_cols
print(f"\nForm 3 loaded: {df_unknown.shape[0]} unknown samples")
print(df_unknown.to_string())

# ============================================================
# 1. EXTRACT ARTIFACT ID FROM SAMPLING POINT NAME
# ============================================================
def extract_id(name):
    """Extract artifact ID from sampling point name."""
    name = str(name).strip()
    import re
    # Handle special suffixes
    for suffix in ['严重风化点', '未风化点', '部位']:
        idx = name.find(suffix)
        if idx > 0:
            return name[:idx]
    # Try to extract leading digits
    match = re.match(r'(\d+)', name)
    if match:
        return match.group(1).zfill(2)
    return name

df_comp['文物编号'] = df_comp['文物采样点'].apply(extract_id)
print(f"\nExtracted IDs: {sorted(df_comp['文物编号'].unique())}")

# Classify sampling point type
def classify_sample(name):
    name = str(name)
    if '严重风化点' in name:
        return '严重风化'
    elif '未风化点' in name:
        return '未风化'
    elif '部位' in name:
        return '部位采样'
    else:
        return '普通采样'

df_comp['采样类型'] = df_comp['文物采样点'].apply(classify_sample)
print(f"\nSampling types:\n{df_comp['采样类型'].value_counts()}")

# ============================================================
# 2. MERGE COMPOSITION WITH BASIC INFO
# ============================================================
df_merged = df_comp.merge(df_info, on='文物编号', how='left')
print(f"\nMerged data: {df_merged.shape[0]} rows")
print(f"Missing type: {df_merged['类型'].isna().sum()}")
print(f"Missing weathering: {df_merged['表面风化'].isna().sum()}")

# ============================================================
# 3. COMPUTE COMPONENT SUMS AND VALIDATE
# ============================================================
component_cols = ['SiO2', 'Na2O', 'K2O', 'CaO', 'MgO', 'Al2O3', 'Fe2O3',
                  'CuO', 'PbO', 'BaO', 'P2O5', 'SrO', 'SnO2', 'SO2']

df_merged['成分总和'] = df_merged[component_cols].sum(axis=1, skipna=True)
df_merged['有效数据'] = (df_merged['成分总和'] >= 85) & (df_merged['成分总和'] <= 105)

print(f"\nValid data (85%-105%): {df_merged['有效数据'].sum()}/{len(df_merged)}")
print(f"Component sum - min: {df_merged['成分总和'].min():.1f}, max: {df_merged['成分总和'].max():.1f}")
print(f"Component sum - mean: {df_merged['成分总和'].mean():.1f}, median: {df_merged['成分总和'].median():.1f}")

# Check invalid
invalid = df_merged[~df_merged['有效数据']]
if len(invalid) > 0:
    print(f"\nInvalid data points ({len(invalid)}):")
    print(invalid[['文物采样点', '成分总和']].to_string())

# ============================================================
# 4. PREPARE CLEAN DATASET
# ============================================================
# Fill NaN with 0 for numerical analysis
df_clean = df_merged.copy()
for col in component_cols:
    df_clean[col] = df_clean[col].fillna(0)

# Normalize to 100% for valid data
mask_valid = df_clean['有效数据']
for col in component_cols:
    df_clean.loc[mask_valid, f'{col}_norm'] = (
        df_clean.loc[mask_valid, col] / df_clean.loc[mask_valid, '成分总和'] * 100
    )

# Save
df_clean.to_csv('cleaned_data.csv', index=False, encoding='utf-8-sig')
print("\nCleaned data saved to 'cleaned_data.csv'")
print(f"Columns: {list(df_clean.columns)}")
print("\nPreprocessing complete!")
