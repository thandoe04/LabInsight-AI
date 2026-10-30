# LabInsight AI — Machine Learning & Analytics Documentation

## 1. Principles & Clinical Boundaries

Machine learning in LabInsight AI is engineered strictly for **operational intelligence, statistical anomaly detection, and data pattern analysis**.

> ⚠️ **CRITICAL DISCLAIMER**  
> An anomaly score is an index of mathematical statistical rarity relative to historical training data. It is **NOT** a clinical diagnosis, an indicator of disease probability, or an alert of medical urgency. All outputs must be subjected to professional human evaluation.

---

## 2. Implemented Algorithms

### A. Anomaly Detection
1. **Isolation Forest (`IsolationForest`)**:
   - Isolates observations by randomly selecting a feature and randomly splitting between maximum and minimum values.
   - Computes normalized anomaly scores in `[0, 1]`.
   - Generates contributing feature vectors using standardized Z-scores ($z = \frac{x - \mu}{\sigma}$).
2. **Local Outlier Factor (`LocalOutlierFactor`)**:
   - Measures the local deviation of density with respect to its $k$-nearest neighbors.
3. **One-Class SVM (`OneClassSVM`)**:
   - Computes a non-linear hyper-boundary enclosing high-density clinical reference values using radial basis function (RBF) kernels.

### B. Unsupervised Clustering
1. **K-Means Clustering**:
   - Discovers empirical centroids across laboratory test panels using Euclidean distance metrics.
2. **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)**:
   - Groups continuous high-density specimen patterns while isolating noise points (`label = -1`).
3. **Principal Component Analysis (PCA)**:
   - Reduces multi-analyte feature spaces to 2 orthogonal components for interactive scatter visual analysis.
4. **Validation Metrics**:
   - **Silhouette Score**: Evaluates cluster cohesion vs. separation ($[-1, 1]$).
   - **Davies-Bouldin Index**: Evaluates average similarity measure between each cluster and its most similar counterpart.
   - **Calinski-Harabasz Index**: Ratio of between-cluster variance to within-cluster dispersion.

---

## 3. Data Quality Intelligence Rules

| Defect Identifier | Classification | Trigger Criteria |
|-------------------|----------------|------------------|
| `missing_value` | Warning | Null numeric value for a quantitative assay |
| `impossible_value` | Critical | Negative value for positive physical analyte (e.g. Hemoglobin < 0) |
| `inconsistent_timestamps` | Error | Specimen collection timestamp later than receipt timestamp |
| `extreme_outlier` | Warning | Observed measurement exceeds 5x upper reference limit |
