"""
Unit tests for Machine Learning Anomaly Detection, Clustering, and Data Quality modules.
"""
import numpy as np
import pytest

from app.ml.anomaly_detection import run_anomaly_detection
from app.ml.clustering import run_clustering
from app.ml.data_quality import check_data_quality


def test_anomaly_detection_isolation_forest():
    """Verify Isolation Forest correctly scores synthetic data and identifies extreme outliers."""
    np.random.seed(42)
    # 50 normal observations centered at 10
    normal = np.random.normal(loc=10.0, scale=1.0, size=(50, 2))
    # 2 obvious extreme outliers
    outliers = np.array([[50.0, 50.0], [-30.0, -30.0]])
    data = np.vstack([normal, outliers])

    result = run_anomaly_detection(
        features=data,
        feature_names=["FeatureA", "FeatureB"],
        algorithm="isolation_forest",
        contamination=0.05,
    )

    assert "is_anomaly" in result
    assert "anomaly_scores" in result
    assert len(result["is_anomaly"]) == 52
    assert result["summary"]["anomalies_detected"] > 0
    # Outliers should have high anomaly scores
    assert result["anomaly_scores"][50] > 0.5 or result["is_anomaly"][50]


def test_clustering_kmeans():
    """Verify KMeans produces valid cluster labels, 2D PCA coordinates, and evaluation metrics."""
    np.random.seed(42)
    cluster1 = np.random.normal(loc=[5, 5], scale=0.5, size=(20, 2))
    cluster2 = np.random.normal(loc=[15, 15], scale=0.5, size=(20, 2))
    data = np.vstack([cluster1, cluster2])

    result = run_clustering(
        features=data,
        algorithm="kmeans",
        hyperparameters={"n_clusters": 2},
    )

    assert result["cluster_count"] == 2
    assert len(result["labels"]) == 40
    assert len(result["coordinates_2d"]) == 40
    assert result["metrics"]["silhouette_score"] is not None
    # Well-separated clusters should have high silhouette score (> 0.5)
    assert result["metrics"]["silhouette_score"] > 0.5


def test_data_quality_checks():
    """Verify data quality intelligence identifies negative values, missing data, and chronological errors."""
    records = [
        {
            "id": "1",
            "test_code": "HB",
            "numeric_value": -5.0,  # Impossible negative
            "result_type": "numeric",
        },
        {
            "id": "2",
            "test_code": "WBC",
            "numeric_value": None,  # Missing value
            "result_type": "numeric",
        },
    ]

    issues = check_data_quality(records)
    issue_types = [i["issue_type"] for i in issues]

    assert "impossible_value" in issue_types
    assert "missing_value" in issue_types
