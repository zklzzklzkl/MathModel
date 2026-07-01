# Human Model Review — Confirmation Gate

**Date**: 2026-06-30
**Status**: ⚠️ **AWAITING HUMAN CONFIRMATION**

---

## What Was Analyzed

Two candidate routes (A=conservative, B=high-score) were independently reviewed by:
- **model-reviewer**: verified correctness, feasibility, data fit, implementation clarity
- **devils-advocate**: found weak assumptions, method overreach, judge objections

Both reviewers independently identified the same 3 BLOCKER issues and recommended a hybrid approach.

---

## Final Recommendation: Route C (B-lite)

**Route C = Route B's compositional data pipeline + Route A's simplicity on small samples**

### Key Design Decisions:

| Decision | Rationale |
|----------|-----------|
| CLR transform throughout (not raw wt%) | Compositional data closure constraint requires it |
| Ward's hierarchical clustering, not GMM | 18 High-K samples too few for Gaussian mixture |
| 2 classifiers (k-NN + RF), not 5 | Ensemble of 5 is "method shopping" on 58 samples |
| Immobile-element norm for Q1C, not Elastic Net | Only 4-8 calibration pairs, not enough for regularized regression |
| Permutation test for Q4 group difference | Only statistically valid approach for comparing correlation matrices |
| Artifact-level aggregation for Q1 tests | 69 rows ≠ 69 independent observations |

### Methods Dropped from Route B:
- GMM (sample size), HDBSCAN (density unreliable on 18 points), Elastic Net (overfitting on 4-8 pairs)
- Gaussian NB (violates CLR normality assumption), t-SNE (redundant with PCA), Graphical Lasso (sample size)
- SHAP (adds complexity without core value), 5-classifier ensemble (reduced to 2)

---

## Questions for Human Confirmation

Please confirm or adjust:

1. **Route C is acceptable?** The hybrid approach keeps compositional data rigor while eliminating methods inappropriate for the sample sizes.

2. **Immobile-element normalization for Q1C** — using Al2O3 as the reference immobile element. Is this physically justifiable for your domain?

3. **Artifact-level aggregation for Q1** — this reduces effective sample size to n=58 but is statistically honest. Acceptable?

4. **10 core figures** is the target. Is this sufficient? The benchmark profile expects 1+ figures per subproblem plus EDA.

5. **Python (matplotlib/seaborn)** as the plotting backend. OK?

6. Any domain knowledge about ancient Chinese glass that should inform the modeling?

---

## Next Step After Confirmation

Once confirmed, I will:
1. Write `reports/ANALYSIS_MODELING_REPORT.md` with full model specifications
2. Write `reports/ANALYSIS_GATE.md`
3. Proceed to `mm-data-experiment` phase (code + experiments + figures)
