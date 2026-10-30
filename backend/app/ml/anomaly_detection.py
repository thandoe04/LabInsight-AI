"""
Machine Learning Anomaly Detection module.
Algorithms supported:
- Isolation Forest
- Local Outlier Factor (LOF)
- One-Class SVM

SAFETY NOTICE:
Statistical anomaly scores are mathematical deviation signals, NOT clinical diagnoses.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


def run_anomaly_detection(
    features: np.ndarray,
    feature_names: list[str],
    algorithm: str = "isolation_forest",
    contamination: float = 0.05,
    hyperparameters: dict | None = None,
) -> dict:
    """
    Fit an unsupervised anomaly detection model and compute per-sample anomaly scores.

    Returns:
    {
        "is_anomaly": list[bool],
        "anomaly_scores": list[float],
        "contributing_features": list[dict],
        "summary": {
            "total_records": int,
            "anomalies_detected": int,
            "anomaly_rate": float,
            "algorithm": str,
        }
    }
    """
    hyperparameters = hyperparameters or {}
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    if algorithm == "isolation_forest":
        n_estimators = hyperparameters.get("n_estimators", 100)
        random_state = hyperparameters.get("random_state", 42)
        model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
        )
        preds = model.fit_predict(scaled_features)  # 1 normal, -1 anomaly
        # decision_function gives negative scores for anomalies; invert and scale
        raw_scores = -model.decision_function(scaled_features)
        # Normalize to [0, 1] range
        min_s, max_s = raw_scores.min(), raw_scores.max()
        scores = (raw_scores - min_s) / (max_s - min_s + 1e-8) if max_s > min_s else np.zeros_like(raw_scores)

    elif algorithm == "local_outlier_factor":
        n_neighbors = hyperparameters.get("n_neighbors", 20)
        model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=False,
        )
        preds = model.fit_predict(scaled_features)
        raw_scores = -model.negative_outlier_factor_
        min_s, max_s = raw_scores.min(), raw_scores.max()
        scores = (raw_scores - min_s) / (max_s - min_s + 1e-8) if max_s > min_s else np.zeros_like(raw_scores)

    elif algorithm == "one_class_svm":
        kernel = hyperparameters.get("kernel", "rbf")
        nu = hyperparameters.get("nu", contamination)
        model = OneClassSVM(kernel=kernel, nu=nu)
        preds = model.fit_predict(scaled_features)
        raw_scores = -model.decision_function(scaled_features)
        min_s, max_s = raw_scores.min(), raw_scores.max()
        scores = (raw_scores - min_s) / (max_s - min_s + 1e-8) if max_s > min_s else np.zeros_like(raw_scores)

    else:
        raise ValueError(f"Unsupported algorithm '{algorithm}'.")

    is_anomaly = [bool(p == -1) for p in preds]

    # Calculate feature deviations (z-scores as contributing factors)
    z_scores = np.abs(scaled_features)
    contributing: list[dict] = []
    for i in range(len(features)):
        top_feat_idx = np.argsort(z_scores[i])[::-1][:3]
        contrib = {
            feature_names[idx]: round(float(z_scores[i][idx]), 2)
            for idx in top_feat_idx
        }
        contributing.append(contrib)

    anom_count = int(sum(is_anomaly))
    return {
        "is_anomaly": is_anomaly,
        "anomaly_scores": [round(float(s), 4) for s in scores],
        "contributing_features": contributing,
        "summary": {
            "total_records": len(features),
            "anomalies_detected": anom_count,
            "anomaly_rate": round(anom_count / len(features), 4) if len(features) > 0 else 0.0,
            "algorithm": algorithm,
        },
    }
