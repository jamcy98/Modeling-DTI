"""Evaluation metrics (roadmap step 8).

Classification: AUROC + AUPR (AUPR is the honest metric under imbalance).
Regression: RMSE, MAE, PCC.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import (
    average_precision_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)


def classification_metrics(y_true, y_prob) -> dict:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    if len(np.unique(y_true)) < 2:  # AUROC/AUPR undefined with one class
        return {"auroc": float("nan"), "aupr": float("nan")}
    return {
        "auroc": float(roc_auc_score(y_true, y_prob)),
        "aupr": float(average_precision_score(y_true, y_prob)),
    }


def regression_metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    pcc = float(pearsonr(y_true, y_pred)[0]) if len(y_true) > 1 else float("nan")
    return {"rmse": rmse, "mae": mae, "pcc": pcc}


def compute_metrics(y_true, y_score, task: str = "classification") -> dict:
    if task == "classification":
        return classification_metrics(y_true, y_score)
    return regression_metrics(y_true, y_score)
