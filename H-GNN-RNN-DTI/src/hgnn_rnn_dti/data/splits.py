"""Data-splitting protocols and leakage control (roadmap step 2).

Objective 1 uses S1 warm-start as the primary protocol (RQ1 is about fusion,
not generalization). Cold-drug (S2), cold-target (S3), and cold-pair splits are
provided for Objective 2 and for optional robustness checks.

Leakage control:
  - S1 warm-start : the same drug/target MAY appear across splits (that is the
    definition of warm-start); the invariant is that no identical (drug, target)
    PAIR appears in two splits.
  - S2/S3/cold-pair: the relevant ENTITY must be disjoint across splits.

Negative sampling (`sample_negatives`) is for positive-only / sparse binary
datasets (e.g., Yamanishi, Luo). DAVIS/KIBA are affinity matrices whose
negatives come directly from binarization, so no sampling is needed there.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _assign(n: int, idx_train, idx_val, idx_test) -> np.ndarray:
    split = np.empty(n, dtype=object)
    split[idx_train] = "train"
    split[idx_val] = "val"
    split[idx_test] = "test"
    return split


def warm_start_split(
    labels: np.ndarray | None,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    seed: int = 42,
    stratify: bool = True,
) -> np.ndarray:
    """Random pair-level split (S1). Stratified by label when provided."""
    n = len(labels) if labels is not None else 0
    rng = np.random.default_rng(seed)

    def _split_indices(indices: np.ndarray):
        indices = indices.copy()
        rng.shuffle(indices)
        n_test = int(round(len(indices) * test_frac))
        n_val = int(round(len(indices) * val_frac))
        test = indices[:n_test]
        val = indices[n_test:n_test + n_val]
        train = indices[n_test + n_val:]
        return train, val, test

    if stratify and labels is not None:
        labels = np.asarray(labels)
        tr, va, te = [], [], []
        for cls in np.unique(labels):
            cls_idx = np.where(labels == cls)[0]
            a, b, c = _split_indices(cls_idx)
            tr.append(a); va.append(b); te.append(c)
        idx_train = np.concatenate(tr); idx_val = np.concatenate(va); idx_test = np.concatenate(te)
    else:
        a, b, c = _split_indices(np.arange(n))
        idx_train, idx_val, idx_test = a, b, c

    return _assign(n, idx_train, idx_val, idx_test)


def cold_entity_split(
    entities: np.ndarray,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    seed: int = 42,
) -> np.ndarray:
    """Entity-disjoint split (S2 cold-drug on Drug_ID, S3 cold-target on Target_ID)."""
    entities = np.asarray(entities)
    uniq = np.unique(entities)
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    n_test = int(round(len(uniq) * test_frac))
    n_val = int(round(len(uniq) * val_frac))
    test_e = set(uniq[:n_test])
    val_e = set(uniq[n_test:n_test + n_val])
    split = np.array(
        ["test" if e in test_e else "val" if e in val_e else "train" for e in entities],
        dtype=object,
    )
    return split


def cold_pair_split(
    drugs: np.ndarray,
    targets: np.ndarray,
    test_frac: float = 0.1,
    seed: int = 42,
) -> np.ndarray:
    """Both drug and target unseen in test (orthogonal entity hold-out)."""
    rng = np.random.default_rng(seed)
    ud, ut = np.unique(drugs), np.unique(targets)
    rng.shuffle(ud); rng.shuffle(ut)
    test_d = set(ud[: int(round(len(ud) * test_frac))])
    test_t = set(ut[: int(round(len(ut) * test_frac))])
    split = np.array(
        ["test" if (d in test_d and t in test_t) else "train"
         for d, t in zip(drugs, targets)],
        dtype=object,
    )
    return split


def sample_negatives(
    positives: pd.DataFrame,
    all_drugs: np.ndarray,
    all_targets: np.ndarray,
    ratio: float = 1.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Sample unobserved (drug, target) pairs as assumed negatives.

    For positive-only / sparse binary datasets ONLY. Generate AFTER splitting to
    avoid leakage. Returns a dataframe of sampled negative pairs (label 0).
    """
    rng = np.random.default_rng(seed)
    observed = set(zip(positives["Drug_ID"], positives["Target_ID"]))
    n_target = int(len(positives) * ratio)
    negs, attempts, max_attempts = [], 0, n_target * 50
    while len(negs) < n_target and attempts < max_attempts:
        d = all_drugs[rng.integers(len(all_drugs))]
        t = all_targets[rng.integers(len(all_targets))]
        attempts += 1
        if (d, t) not in observed:
            observed.add((d, t))
            negs.append({"Drug_ID": d, "Target_ID": t, "label": 0})
    return pd.DataFrame(negs)


# --- leakage assertions -----------------------------------------------------
def check_pair_leakage(df: pd.DataFrame, split_col: str = "split") -> None:
    """Assert no identical (Drug_ID, Target_ID) pair appears in >1 split."""
    pair = df["Drug_ID"].astype(str) + "||" + df["Target_ID"].astype(str)
    counts = df.assign(_pair=pair).groupby("_pair")[split_col].nunique()
    bad = counts[counts > 1]
    assert bad.empty, f"Pair leakage: {len(bad)} pairs span multiple splits."


def check_entity_leakage(df: pd.DataFrame, entity_col: str, split_col: str = "split") -> None:
    """Assert `entity_col` values are disjoint across train/val/test."""
    groups = df.groupby(entity_col)[split_col].nunique()
    bad = groups[groups > 1]
    assert bad.empty, f"Entity leakage on {entity_col}: {len(bad)} entities span splits."
