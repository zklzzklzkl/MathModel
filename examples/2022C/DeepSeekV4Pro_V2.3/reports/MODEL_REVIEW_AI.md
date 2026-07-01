# Model Review AI

> Synthesized from model-reviewer and devils-advocate independent reviews

## Overall Verdict: CONDITIONAL_PASS

Both routes have structural completeness but each carries distinct failure modes. The recommendation is a **Route C** hybrid that uses Route B's compositional data pipeline with Route A's simplicity where sample sizes demand it.

## Review Consensus

Both reviewers independently converged on these critical findings:

| # | Issue | Routes Affected | Severity |
|---|-------|-----------------|----------|
| C1 | Q4 Spearman on raw wt% → spurious correlations from closure | A | **BLOCKER** |
| C2 | LDA on CLR-transformed 18×12 data → near-singular covariance | A (Q2/Q3) | **BLOCKER** |
| C3 | GMM on 18 High-K samples → ~144 cov parameters per component | B (Q2) | **BLOCKER** |
| C4 | 5-classifier ensemble without calibration → pseudo-probabilities | B (Q3) | **HIGH** |
| C5 | All tests treat 69 rows as independent → inflated significance | Both (Q1) | **HIGH** |
| C6 | Q1C calibration pairs: 08/26 are normal-severe, not weathered-unweathered | Both (Q1) | **HIGH** |
| C7 | Route A Q1B: 24 MW-U tests without multiple testing correction | A | **HIGH** |
| C8 | Elastic Net on 4-6 calibration pairs → severe overfitting | B (Q1C) | **HIGH** |

## Route Comparison Verdict

| Dimension | Route A | Route B | Winner |
|-----------|---------|---------|--------|
| Q1A (association) | Chi-square + Cramer's V | Logistic regression + CA | B (adds quantitative interpretation) |
| Q1B (weathering stats) | MW-U (raw) | CLR-MANOVA + Cohen's d | **B** (compositional data aware) |
| Q1C (prediction) | Immobile-element norm | 3-method (overkill) | **A** (simpler is better here) |
| Q2 (classification) | LDA + hierarchical | RF + GMM+HDBSCAN+HC | **Hybrid**: RF importance + hierarchical + Decision Tree |
| Q3 (unknown class.) | LDA + k-NN | RF+SVM+kNN+GNB+LDA | **Hybrid**: k-NN + RF (2 classifiers, calibrated) |
| Q4 (correlation) | Spearman (wrong) | CLR variation matrix + GLasso | **B** (only correct option) |

## Final Recommendation: Route C (B-lite)

**Core principle**: Full compositional data pipeline (CLR/ILR throughout) from Route B, but methods thinned 40% to match sample size reality:

- Drop: GMM, HDBSCAN, Elastic Net, GNB, t-SNE, GLasso, SHAP
- Keep: CLR transforms everywhere, variation matrix, hierarchical clustering, RF, permutation tests
- Simplify: Q1C → immobile-element + simple linear regression (no ensemble)
- Simplify: Q3 → k-NN + RF (2 classifiers)
- Fix: Multi-sample aggregation rules for all Q1 analyses

Expected score: 4-5, implementation risk: low-medium.

## Required Fixes

The following fixes must be incorporated into MODELING_DECISION.md:

1. **[BLOCKER]** Q4: Replace Route A Spearman with Route B CLR variation matrix + permutation test
2. **[BLOCKER]** Q2/Q3: Replace LDA with regularized LDA (shrinkage) or drop LDA, keep RF+k-NN
3. **[BLOCKER]** Q2: Replace GMM with Ward's hierarchical clustering (n=18 too small for GMM)
4. **[HIGH]** Q1: All statistical tests must use artifact-level aggregation (n=58), not point-level (n=69). Specify aggregation rules.
5. **[HIGH]** Q1C: Drop Elastic Net, keep immobile-element + simple OLS per element. Enumerate exact calibration pairs.
6. **[HIGH]** Q1B: MW-U needs CLR transformation OR use Route B's CLR-based approach. Add Bonferroni correction.
7. **[HIGH]** Q3: Reduce to 2 classifiers (k-NN + RF). Report raw vote agreement, not "probabilities."
8. **[MEDIUM]** Q1A: Logistic regression needs Firth correction or fallback to chi-square for sparse categories.

## Evidence Reviewed

- MODEL_CANDIDATES.md (Routes A and B)
- PROBLEM_BRIEF.md
- DATA_AUDIT.md
- Model review output (__model_review_output.md)
- Devil's advocate output (__devils_advocate_output.md)
