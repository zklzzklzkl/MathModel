# Claim Trace

Each paper claim maps to a specific result or code section.

| # | Claim | Section | Evidence |
|---|-------|---------|----------|
| C1 | Weathering associated with type (p=0.020) | Q1A | RESULTS_MANIFEST.json: Q1A_type_pvalue |
| C2 | Weathering associated with decoration (p=0.028) | Q1A | RESULTS_MANIFEST.json: Q1A_decoration_pvalue |
| C3 | K2O significantly leached in High-K weathering | Q1B | RESULTS_MANIFEST.json: Q1B_High-K_K2O_d |
| C4 | SiO2 decreases in Pb-Ba weathering | Q1B | Fig 2 volcano plot |
| C5 | Pre-weathering prediction MAE = 5.73% | Q1C | RESULTS_MANIFEST.json: Q1C_overall_MAE |
| C6 | PbO, BaO, K2O are top-3 discriminant elements | Q2A | Fig 6, ranking table |
| C7 | High-K = 2 sub-classes (k=2, sil=0.269) | Q2B | RESULTS_MANIFEST.json: Q2_High-K_best_k |
| C8 | Pb-Ba = 4 sub-classes (k=4, sil=0.214) | Q2B | RESULTS_MANIFEST.json: Q2_Pb-Ba_best_k |
| C9 | Bootstrap median ARI > 0.55 for both types | Q2D | RESULTS_MANIFEST.json: Q2_*_ari_bootstrap |
| C10 | A1, A6, A7 = High-K | Q3 | Fig 7, q3_classification_results.csv |
| C11 | A2-A5, A8 = Pb-Ba | Q3 | Fig 7, q3_classification_results.csv |
| C12 | 5% perturbation stability = 98% | Q3 | RESULTS_MANIFEST.json: Q3_stability_0.05 |
| C13 | Correlation structures significantly different (p=0.0032) | Q4 | RESULTS_MANIFEST.json: Q4_permutation_pvalue |
| C14 | PbO-BaO co-variation in Pb-Ba glass | Q4 | Fig 9 variation matrix |

## Figure-to-Claim Mapping

| Figure | Supports Claims |
|--------|----------------|
| Fig 1 | C1, C2 |
| Fig 2 | C3, C4 |
| Fig 3 | C5 |
| Fig 4-5 | C7, C8, C9 |
| Fig 6 | C6 |
| Fig 7-8 | C10, C11, C12 |
| Fig 9-10 | C13, C14 |

## Verdict

All quantitative claims are traceable to RESULTS_MANIFEST.json entries or generated figures. No invented numbers.
