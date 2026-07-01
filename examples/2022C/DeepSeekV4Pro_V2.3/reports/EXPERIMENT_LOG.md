# Experiment Log

**Date**: 2026-06-30
**Script**: `code/run_all.py`
**Status**: SUCCESS

## Run Summary

| Phase | Description | Status |
|-------|-------------|--------|
| Data Prep | Load, clean, impute, CLR transform | OK |
| Q1A | Chi-square association tests | OK |
| Q1B | CLR-based Welch t-tests + Holm correction | OK |
| Q1C | Al2O3 immobile-element normalization + OLS validation | OK |
| Q2 | RF importance + Ward clustering + Decision tree + Bootstrap | OK |
| Q3 | k-NN + RF classification + perturbation sensitivity | OK |
| Q4 | Variation matrix + PCA + Permutation test | OK |

## Key Numerical Results

| Metric | Value |
|--------|-------|
| Q1A: Weathering x Type p-value | 0.020 |
| Q1A: Weathering x Type Cramer's V | 0.307 |
| Q1A: Weathering x Decoration p-value | 0.028 |
| Q1C: Overall MAE | 5.73% |
| Q2: High-K optimal k | 2 (silhouette=0.269) |
| Q2: Pb-Ba optimal k | 4 (silhouette=0.214) |
| Q2: Bootstrap median ARI (High-K) | 0.581 |
| Q2: Bootstrap median ARI (Pb-Ba) | 0.559 |
| Q3: LOOCV accuracy (RF) | 100% |
| Q3: LOOCV accuracy (k-NN) | 100% |
| Q3: 5% perturbation stability | 98.00% |
| Q3: 10% perturbation stability | 92.12% |
| Q4: Permutation test p-value | 0.0032 |

## Generated Files

| Type | Count | Location |
|------|-------|----------|
| Figures (PDF) | 11 | figures/ |
| Figures (PNG) | 11 | figures/ |
| Results JSON | 1 (69 entries) | results/RESULTS_MANIFEST.json |
| CSV exports | 3 | results/ |
