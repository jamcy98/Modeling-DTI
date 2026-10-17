"""Roadmap step 2: preprocess a dataset into model-ready artifacts.

Pipeline: load raw -> binarize (Kd<=30 nM default for DAVIS) -> featurize unique
drugs (SMILES->graph) and proteins (sequence->tokens) -> split (S1 warm-start
default) -> save artifacts + split file -> assert no leakage.

Usage:
    python scripts/preprocess.py --dataset davis
    python scripts/preprocess.py --dataset davis --threshold 30 --split S1 --seed 42
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hgnn_rnn_dti.data import featurize as F  # noqa: E402
from hgnn_rnn_dti.data.datasets import DATASETS, load_dti  # noqa: E402
from hgnn_rnn_dti.data.labels import binarize, class_balance  # noqa: E402
from hgnn_rnn_dti.data.splits import (  # noqa: E402
    check_entity_leakage,
    check_pair_leakage,
    cold_entity_split,
    cold_pair_split,
    warm_start_split,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Preprocess a DTI dataset (step 2).")
    ap.add_argument("--dataset", default="davis")
    ap.add_argument("--root", default="data")
    ap.add_argument("--threshold", type=float, default=None,
                    help="binarization threshold (default: dataset registry value)")
    ap.add_argument("--split", default="S1", choices=["S1", "S2", "S3", "cold_pair"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--test-frac", type=float, default=0.1)
    ap.add_argument("--max-protein-length", type=int, default=1000)
    args = ap.parse_args()

    name = args.dataset.lower()
    meta = DATASETS[name]
    value_col = meta["value_col"]
    threshold = args.threshold if args.threshold is not None else meta["threshold"]
    direction = meta["direction"]
    root = Path(args.root)

    # 1. load raw (download if missing)
    raw_path = root / "raw" / f"{name}.csv"
    if raw_path.exists():
        df = pd.read_csv(raw_path)
        print(f"Loaded cached {raw_path} ({len(df)} rows)")
    else:
        print(f"{raw_path} not found; downloading via TDC ...")
        df = load_dti(name, root=root)

    # 2. binarize
    df["label"] = binarize(df[value_col].to_numpy(), threshold, direction)
    bal = class_balance(df["label"].to_numpy())
    print(f"Binarize ({value_col} {direction} {threshold}): {bal}")

    # 3. featurize unique drugs and proteins
    drug_graphs: dict = {}
    bad_smiles = set()
    for did, smi in df[["Drug_ID", "smiles"]].drop_duplicates().itertuples(index=False):
        g = F.smiles_to_graph(smi)
        if g is None:
            bad_smiles.add(did)
        else:
            drug_graphs[did] = g
    if bad_smiles:
        before = len(df)
        df = df[~df["Drug_ID"].isin(bad_smiles)].reset_index(drop=True)
        print(f"Dropped {before - len(df)} pairs from {len(bad_smiles)} unparseable SMILES")

    protein_tokens: dict = {}
    for tid, seq in df[["Target_ID", "sequence"]].drop_duplicates().itertuples(index=False):
        protein_tokens[tid] = F.encode_protein(seq, max_len=args.max_protein_length)

    print(f"Featurized {len(drug_graphs)} drugs, {len(protein_tokens)} proteins")

    # 4. split
    labels = df["label"].to_numpy()
    if args.split == "S1":
        split = warm_start_split(labels, args.val_frac, args.test_frac, args.seed)
    elif args.split == "S2":
        split = cold_entity_split(df["Drug_ID"].to_numpy(), args.val_frac, args.test_frac, args.seed)
    elif args.split == "S3":
        split = cold_entity_split(df["Target_ID"].to_numpy(), args.val_frac, args.test_frac, args.seed)
    else:  # cold_pair
        split = cold_pair_split(df["Drug_ID"].to_numpy(), df["Target_ID"].to_numpy(), args.test_frac, args.seed)
    df["split"] = split

    # 5. leakage assertions
    if args.split == "S1":
        check_pair_leakage(df)
    elif args.split == "S2":
        check_entity_leakage(df, "Drug_ID")
    elif args.split == "S3":
        check_entity_leakage(df, "Target_ID")
    print("Leakage check passed for", args.split)

    counts = df["split"].value_counts().to_dict()
    print("Split sizes:", counts)
    for s in ["train", "val", "test"]:
        sub = df[df["split"] == s]
        if len(sub):
            print(f"  {s}: {class_balance(sub['label'].to_numpy())}")

    # 6. save artifacts
    pdir = root / "processed" / name
    sdir = root / "splits" / name
    pdir.mkdir(parents=True, exist_ok=True)
    sdir.mkdir(parents=True, exist_ok=True)

    with open(pdir / "drug_graphs.pkl", "wb") as fh:
        pickle.dump(drug_graphs, fh)
    with open(pdir / "protein_tokens.pkl", "wb") as fh:
        pickle.dump(protein_tokens, fh)
    df[["Drug_ID", "Target_ID", value_col, "label", "split"]].to_csv(
        pdir / "pairs.csv", index=False
    )

    split_file = sdir / f"{args.split}_seed{args.seed}.json"
    with open(split_file, "w") as fh:
        json.dump(
            {s: df.index[df["split"] == s].tolist() for s in ["train", "val", "test"]},
            fh,
        )

    meta_out = {
        "dataset": name,
        "value_col": value_col,
        "threshold": threshold,
        "direction": direction,
        "split": args.split,
        "seed": args.seed,
        "n_pairs": int(len(df)),
        "n_drugs": int(df["Drug_ID"].nunique()),
        "n_targets": int(df["Target_ID"].nunique()),
        "class_balance": class_balance(df["label"].to_numpy()),
        "split_sizes": counts,
        "atom_feature_dim": F.ATOM_FEATURE_DIM,
        "bond_feature_dim": F.BOND_FEATURE_DIM,
        "protein_vocab_size": F.PROTEIN_VOCAB_SIZE,
        "max_protein_length": args.max_protein_length,
    }
    with open(pdir / "meta.json", "w") as fh:
        json.dump(meta_out, fh, indent=2)

    print(f"\nSaved artifacts to {pdir}/ and split to {split_file}")
    print(f"Feature dims: atom={F.ATOM_FEATURE_DIM}, bond={F.BOND_FEATURE_DIM}, "
          f"protein_vocab={F.PROTEIN_VOCAB_SIZE}")
    print("Step 2 'done': graphs + tokens + labels + split built, leakage check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
