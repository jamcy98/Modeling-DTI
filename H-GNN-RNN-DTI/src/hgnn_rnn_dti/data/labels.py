"""Binary label construction for DTI classification (roadmap step 2).

Default convention (Objective 1):
  - Kd-based datasets (DAVIS, BindingDB_Kd): interacting iff Kd <= 30 nM  ("le")
  - KIBA score:                              interacting iff score >= 12.1 ("ge")

The threshold and direction are configurable; `scripts/preprocess.py` reads the
default from the dataset registry and lets the CLI override it.
"""
from __future__ import annotations

import numpy as np


def binarize(values: np.ndarray, threshold: float, direction: str = "le") -> np.ndarray:
    """Return int labels (1 = interacting) from continuous affinities/scores.

    direction "le": label = 1 where value <= threshold  (Kd in nM; lower = stronger)
    direction "ge": label = 1 where value >= threshold  (KIBA score; higher = stronger)
    """
    values = np.asarray(values, dtype=np.float64)
    if direction == "le":
        labels = (values <= threshold)
    elif direction == "ge":
        labels = (values >= threshold)
    else:
        raise ValueError(f"direction must be 'le' or 'ge', got {direction!r}")
    return labels.astype(np.int64)


def class_balance(labels: np.ndarray) -> dict:
    labels = np.asarray(labels)
    n = int(labels.size)
    pos = int(labels.sum())
    return {
        "n": n,
        "positives": pos,
        "negatives": n - pos,
        "positive_rate": (pos / n) if n else 0.0,
    }
