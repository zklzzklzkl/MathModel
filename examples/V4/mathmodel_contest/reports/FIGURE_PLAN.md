# Figure Plan

> Each core paper figure must have a contract: conclusion, archetype, source data, section placement.

## F1: Weathering × Glass Type Association (Q1A)

- **Core conclusion**: Whether weathering is significantly associated with glass type, decoration, and color
- **Archetype**: 2-panel: (left) mosaic plot of weathering × glass type, (right) grouped bar chart weathering × decoration type
- **Backend**: matplotlib (mosaic via statsmodels.graphics.mosaicplot)
- **Source data**: Form 1 (58 artifacts), artifact-level
- **Statistics**: Chi-square p-values, Cramer's V on figure annotation
- **Section**: Q1 results, first figure

## F2: Weathering Effect Volcano Plots (Q1B)

- **Core conclusion**: Which chemical elements significantly increase/decrease with weathering, by glass type
- **Archetype**: 2-panel (left: High-K, right: Pb-Ba), volcano style: x=CLR log2 fold change (weathered/unweathered), y=-log10(adjusted p)
- **Backend**: matplotlib
- **Source data**: Form 2, CLR-transformed, weathering × type groups
- **Statistics**: Holm-corrected p-values, Cohen's d
- **Section**: Q1 results, second figure

## F3: Weathering Correction Validation (Q1C)

- **Core conclusion**: Pre-weathering prediction accuracy on calibration pairs
- **Archetype**: Scatter plot: measured vs predicted for key elements (SiO2, K2O, PbO, BaO, Al2O3) across calibration pairs, with 1:1 reference line
- **Backend**: matplotlib
- **Source data**: Paired weathered/unweathered samples (49/50 + unweathered points)
- **Statistics**: MAE per element annotated
- **Section**: Q1 results, third figure

## F4: High-K Sub-classification Visualization (Q2)

- **Core conclusion**: High-K glass has N sub-classes with distinct chemical profiles
- **Archetype**: 3-panel: (top) dendrogram with cluster colors, (middle left) PCA biplot with cluster ellipses, (middle right) silhouette plot
- **Backend**: matplotlib + scipy dendrogram + sklearn PCA
- **Source data**: Q1-corrected, CLR-transformed High-K artifacts (n=18)
- **Statistics**: Silhouette scores, gap statistic
- **Section**: Q2 results, first figure

## F5: Pb-Ba Sub-classification Visualization (Q2)

- **Core conclusion**: Pb-Ba glass has M sub-classes with distinct chemical profiles
- **Archetype**: Same 3-panel layout as F4 but for Pb-Ba (n=40)
- **Backend**: matplotlib + scipy + sklearn
- **Source data**: Q1-corrected, CLR-transformed Pb-Ba artifacts (n=40)
- **Statistics**: Silhouette scores, gap statistic
- **Section**: Q2 results, second figure

## F6: Classification Decision Tree (Q2)

- **Core conclusion**: Sub-classification can be expressed as simple threshold rules
- **Archetype**: Decision tree diagram with split thresholds and class labels
- **Backend**: sklearn.tree.plot_tree
- **Source data**: Artifact-level, original-scale key elements (top 5 from RF importance)
- **Statistics**: Node impurity, samples per node
- **Section**: Q2 results, third figure

## F7: Q3 Unknown Projection (Q3)

- **Core conclusion**: Where the 8 unknown artifacts fall relative to known types and sub-classes
- **Archetype**: PCA biplot with training data (colored by type + sub-class) + 8 unknown samples as labeled points with uncertainty ellipses
- **Backend**: matplotlib
- **Source data**: Combined Form 2 + Form 3, CLR-transformed, Q1-corrected
- **Statistics**: Mahalanobis distance annotations
- **Section**: Q3 results, first figure

## F8: Classification Results (Q3)

- **Core conclusion**: Assigned type and sub-class for each of A1-A8, with confidence
- **Archetype**: Horizontal stacked bar: k-NN and RF vote fractions per artifact, grouped by assigned type
- **Backend**: matplotlib
- **Source data**: Classifier outputs
- **Statistics**: Vote fractions, agreement flag
- **Section**: Q3 results, second figure

## F9: Variation Matrix Heatmaps (Q4)

- **Core conclusion**: Pairwise log-ratio variance structure differs between High-K and Pb-Ba glass
- **Archetype**: 2-panel heatmap (left: High-K, right: Pb-Ba), color = var(ln(x_i/x_j)), ordered by hierarchical clustering
- **Backend**: seaborn.heatmap or matplotlib
- **Source data**: Q1-corrected, CLR-transformed compositions
- **Statistics**: Permutation test p-value (difference between matrices)
- **Section**: Q4 results, first figure

## F10: PCA Biplots per Glass Type (Q4)

- **Core conclusion**: Element co-variation patterns reveal different glass-making recipes
- **Archetype**: 2-panel PCA biplot (left: High-K, right: Pb-Ba), arrows for element loadings, points colored by weathering status
- **Backend**: matplotlib (custom biplot function)
- **Source data**: Q1-corrected, CLR-transformed compositions, by type
- **Statistics**: Variance explained per PC annotated
- **Section**: Q4 results, second figure

---

## Figure Quality Standards

- All figures: vector PDF @ 300 DPI fallback PNG
- Labels: ≥10pt font, Chinese or English (match paper language)
- Captions: Conclusion-forward (state the finding, not just describe the plot)
- Color: Colorblind-friendly palette (viridis or Okabe-Ito)
- All figures inserted in paper near their argument, not in an appendix dump
