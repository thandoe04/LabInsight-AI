"""
Machine Learning Clustering module.
Algorithms:
- K-Means
- DBSCAN
- Agglomerative / Hierarchical clustering
PCA 2D projection for interactive scatter plot visualization.
Validation metrics:
- Silhouette Score
- Davies-Bouldin Index
- Calinski-Harabasz Index
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler


def run_clustering(
    features: np.ndarray,
    algorithm: str = "kmeans",
    hyperparameters: dict | None = None,
) -> dict:
    """Execute unsupervised clustering and return labels, 2D coordinates, and quality metrics."""
    hyperparameters = hyperparameters or {}
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    if algorithm == "kmeans":
        n_clusters = hyperparameters.get("n_clusters", 3)
        random_state = hyperparameters.get("random_state", 42)
        model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
        labels = model.fit_predict(scaled)

    elif algorithm == "dbscan":
        eps = hyperparameters.get("eps", 0.5)
        min_samples = hyperparameters.get("min_samples", 5)
        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(scaled)

    elif algorithm == "hierarchical":
        n_clusters = hyperparameters.get("n_clusters", 3)
        linkage = hyperparameters.get("linkage", "ward")
        model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
        labels = model.fit_predict(scaled)

    else:
        raise ValueError(f"Unsupported clustering algorithm '{algorithm}'.")

    # Compute 2D PCA projection for visualization
    pca = PCA(n_components=2, random_state=42)
    coords_2d = pca.fit_transform(scaled)

    # Compute evaluation metrics if at least 2 distinct clusters (excluding noise)
    unique_labels = set(labels)
    valid_clusters = [l for l in unique_labels if l != -1]
    
    sil_score = None
    db_index = None
    ch_score = None

    if len(valid_clusters) >= 2 and len(scaled) > len(valid_clusters):
        try:
            sil_score = round(float(silhouette_score(scaled, labels)), 4)
            db_index = round(float(davies_bouldin_score(scaled, labels)), 4)
            ch_score = round(float(calinski_harabasz_score(scaled, labels)), 4)
        except Exception:
            pass

    return {
        "labels": [int(l) for l in labels],
        "cluster_count": len(valid_clusters),
        "coordinates_2d": [
            {"x": round(float(pt[0]), 3), "y": round(float(pt[1]), 3), "cluster": int(labels[i])}
            for i, pt in enumerate(coords_2d)
        ],
        "explained_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        "metrics": {
            "silhouette_score": sil_score,
            "davies_bouldin_index": db_index,
            "calinski_harabasz_score": ch_score,
        },
    }
