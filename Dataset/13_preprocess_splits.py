"""
Create train/validation/test splits for all datasets.

Implements four splitting strategies as described in the analysis plan:
  S0 - Random split with 10-fold cross-validation (warm-start)
  S1 - Cold-drug split  (test drugs not seen during training)
  S2 - Cold-target split (test proteins not seen during training)
  S3 - Cross-dataset split (train on one dataset, test on another)

Run:
    python 13_preprocess_splits.py

Output:
    processed/splits/{dataset}_{strategy}_split.json
        -> { "fold_0": {"train": [...], "val": [...], "test": [...]}, ... }
        -> Each list contains row indices into the labels CSV

Requirements:
    pip install pandas numpy scikit-learn
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
LABELS_DIR  = os.path.join(BASE_DIR, "processed", "labels")
OUT_DIR     = os.path.join(BASE_DIR, "processed", "splits")

N_FOLDS     = 10     # number of folds for cross-validation
VAL_RATIO   = 0.1    # fraction of training set used as validation
RANDOM_SEED = 42


# ── Split builders ────────────────────────────────────────────────────────────

def random_split(df, n_folds=N_FOLDS, label_col=None):
    """
    S0: Random split with k-fold cross-validation.
    Stratified by label if label_col is provided.
    """
    indices = np.arange(len(df))
    splits  = {}

    kf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED) \
        if label_col and label_col in df.columns \
        else KFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)

    labels = df[label_col].values if label_col and label_col in df.columns else None

    for fold, (train_val_idx, test_idx) in enumerate(
        kf.split(indices, labels) if labels is not None else kf.split(indices)
    ):
        # Further split train_val into train and val
        n_val      = max(1, int(len(train_val_idx) * VAL_RATIO))
        rng        = np.random.default_rng(RANDOM_SEED + fold)
        rng.shuffle(train_val_idx)
        val_idx    = train_val_idx[:n_val]
        train_idx  = train_val_idx[n_val:]

        splits[f"fold_{fold}"] = {
            "train": train_idx.tolist(),
            "val":   val_idx.tolist(),
            "test":  test_idx.tolist(),
        }

    return splits


def cold_drug_split(df, n_folds=N_FOLDS):
    """
    S1: Cold-drug split.
    All interactions of certain drugs go into the test set.
    The model never sees these drugs during training.
    """
    all_drugs = df["drug_id"].unique()
    rng       = np.random.default_rng(RANDOM_SEED)
    drug_folds= np.array_split(rng.permutation(all_drugs), n_folds)
    splits    = {}

    for fold, test_drugs in enumerate(drug_folds):
        test_mask  = df["drug_id"].isin(test_drugs)
        test_idx   = df.index[test_mask].tolist()
        train_val  = df.index[~test_mask].values

        n_val      = max(1, int(len(train_val) * VAL_RATIO))
        rng2       = np.random.default_rng(RANDOM_SEED + fold)
        rng2.shuffle(train_val)
        val_idx    = train_val[:n_val].tolist()
        train_idx  = train_val[n_val:].tolist()

        splits[f"fold_{fold}"] = {
            "train":      train_idx,
            "val":        val_idx,
            "test":       test_idx,
            "test_drugs": test_drugs.tolist(),
        }

    return splits


def cold_target_split(df, n_folds=N_FOLDS):
    """
    S2: Cold-target split.
    All interactions of certain proteins go into the test set.
    The model never sees these proteins during training.
    """
    all_proteins = df["protein_id"].unique()
    rng          = np.random.default_rng(RANDOM_SEED)
    prot_folds   = np.array_split(rng.permutation(all_proteins), n_folds)
    splits       = {}

    for fold, test_proteins in enumerate(prot_folds):
        test_mask     = df["protein_id"].isin(test_proteins)
        test_idx      = df.index[test_mask].tolist()
        train_val     = df.index[~test_mask].values

        n_val         = max(1, int(len(train_val) * VAL_RATIO))
        rng2          = np.random.default_rng(RANDOM_SEED + fold)
        rng2.shuffle(train_val)
        val_idx       = train_val[:n_val].tolist()
        train_idx     = train_val[n_val:].tolist()

        splits[f"fold_{fold}"] = {
            "train":         train_idx,
            "val":           val_idx,
            "test":          test_idx,
            "test_proteins": test_proteins.tolist(),
        }

    return splits


def cold_pair_split(df, test_ratio=0.2):
    """
    S3 (variant): Cold-pair split.
    Drug–protein pairs not seen during training are used for testing.
    Individual drugs and proteins may still appear in the training set.
    """
    rng       = np.random.default_rng(RANDOM_SEED)
    indices   = rng.permutation(len(df))
    n_test    = int(len(df) * test_ratio)
    n_val     = int((len(df) - n_test) * VAL_RATIO)

    test_idx  = indices[:n_test].tolist()
    val_idx   = indices[n_test : n_test + n_val].tolist()
    train_idx = indices[n_test + n_val:].tolist()

    return {
        "fold_0": {"train": train_idx, "val": val_idx, "test": test_idx}
    }


def cross_dataset_split(source_df, target_df):
    """
    S4: Cross-dataset split.
    Train on all of source_df, test on all of target_df.
    No overlapping pairs required.
    """
    n_val     = max(1, int(len(source_df) * VAL_RATIO))
    rng       = np.random.default_rng(RANDOM_SEED)
    train_val = rng.permutation(len(source_df))
    val_idx   = train_val[:n_val].tolist()
    train_idx = train_val[n_val:].tolist()

    return {
        "fold_0": {
            "train": train_idx,
            "val":   val_idx,
            "test":  list(range(len(target_df))),
        }
    }


# ── Save and report ───────────────────────────────────────────────────────────

def save_split(splits, dataset, strategy):
    path = os.path.join(OUT_DIR, f"{dataset}_{strategy}_split.json")
    with open(path, "w") as f:
        json.dump(splits, f)

    # Print summary for the first fold
    fold0     = splits.get("fold_0", list(splits.values())[0])
    n_train   = len(fold0["train"])
    n_val     = len(fold0["val"])
    n_test    = len(fold0["test"])
    n_folds   = len(splits)
    print(f"  [{strategy:20s}] {n_folds} folds | "
          f"fold_0: train={n_train}, val={n_val}, test={n_test}")
    print(f"    Saved -> {path}")


def process_label_file(label_path, dataset):
    df = pd.read_csv(label_path)

    if "drug_id" not in df.columns:
        # Rename columns if they come from BindingDB format
        rename = {"smiles": "drug_id", "uniprot_id": "protein_id"}
        df = df.rename(columns=rename)

    df = df.reset_index(drop=True)

    label_col = "label" if "label" in df.columns else None
    print(f"\n{dataset}: {len(df):,} pairs | columns: {list(df.columns)}")

    # S0 — random
    save_split(random_split(df, label_col=label_col),
               dataset, "random")

    # S1 — cold-drug
    if "drug_id" in df.columns and df["drug_id"].nunique() >= N_FOLDS:
        save_split(cold_drug_split(df), dataset, "cold_drug")

    # S2 — cold-target
    if "protein_id" in df.columns and df["protein_id"].nunique() >= N_FOLDS:
        save_split(cold_target_split(df), dataset, "cold_target")

    # S3 — cold-pair
    save_split(cold_pair_split(df), dataset, "cold_pair")

    return df


def main():
    print("=" * 55)
    print(" Split Generation")
    print("=" * 55)

    # Datasets to split — process all CSV files in the labels directory
    label_files = sorted(f for f in os.listdir(LABELS_DIR) if f.endswith(".csv"))

    if not label_files:
        print("No label files found. Run 12_preprocess_labels.py first.")
        return

    loaded_dfs = {}
    for fname in label_files:
        dataset   = fname.replace(".csv", "")
        out_check = os.path.join(OUT_DIR, f"{dataset}_random_split.json")
        if os.path.exists(out_check):
            print(f"\n{dataset}: splits already exist — skipping.")
            continue

        label_path = os.path.join(LABELS_DIR, fname)
        df = process_label_file(label_path, dataset)
        loaded_dfs[dataset] = df

    # Cross-dataset split: train on BindingDB, test on DAVIS (if both available)
    source_key = "bindingdb_dti_labels_1to1"
    target_key = "davis_dta_labels"
    if source_key in loaded_dfs and target_key in loaded_dfs:
        print(f"\nCross-dataset split: {source_key} -> {target_key}")
        cross = cross_dataset_split(loaded_dfs[source_key], loaded_dfs[target_key])
        save_split(cross, "bindingdb_to_davis", "cross_dataset")

    print("\nDone. All splits saved to processed/splits/")
    print("\nNext steps:")
    print("  1. Install requirements:  pip install -r requirements.txt")
    print("  2. Run preprocessing:     python run_all_preprocessing.py")
    print("  3. Start model training.")


if __name__ == "__main__":
    main()
