"""
Create a tractable BindingDB subset for Phase 3 CPU pretraining.

Samples N_PAIRS pairs from the full BindingDB DTI label file, extracts
the corresponding drug graphs from chunks (scanning one chunk at a time
to stay within RAM), and writes:

  processed/labels/bindingdb_pretrain_dti_labels_1to1.csv
  processed/drug_graphs/bindingdb_pretrain_drug_graphs.pt
  processed/protein_embeddings/bindingdb_pretrain_protein_embeddings.npy
  processed/protein_embeddings/bindingdb_pretrain_protein_ids.json
  processed/splits/bindingdb_pretrain_dti_labels_1to1_random_split.json

Usage:
    python 14_preprocess_bindingdb_subset.py
    python 14_preprocess_bindingdb_subset.py --n_pairs 50000
"""

import os, sys, json, random, shutil, argparse
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from tqdm import tqdm

BASE_DIR  = Path(__file__).parent
PROC_DIR  = BASE_DIR / "processed"
CHUNK_DIR = PROC_DIR / "drug_graphs" / "bindingdb_drug_graphs_chunks"
LABEL_DIR = PROC_DIR / "labels"
GRAPH_DIR = PROC_DIR / "drug_graphs"
SPLIT_DIR = PROC_DIR / "splits"
EMB_DIR   = PROC_DIR / "protein_embeddings"

VAL_FRAC  = 0.15
TEST_FRAC = 0.15


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_pairs', type=int, default=50_000,
                        help='Total pairs to include (balanced pos:neg, default 50000)')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    random.seed(args.seed)
    N_PAIRS = args.n_pairs

    print(f"\n{'='*60}")
    print(f"  BindingDB subset preprocessing")
    print(f"  Target pairs: {N_PAIRS:,}  Seed: {args.seed}")
    print(f"{'='*60}\n")

    # ── Step 1: Load protein embedding IDs ──────────────────────────────────
    print("Step 1: Loading protein embedding IDs...")
    with open(EMB_DIR / "bindingdb_protein_ids.json") as f:
        prot_ids_list = json.load(f)
    prot_id_set = set(prot_ids_list)
    print(f"  Proteins with embeddings: {len(prot_id_set):,}")

    # ── Step 2: Load full label CSV, filter to valid proteins ────────────────
    print("Step 2: Loading BindingDB label CSV (this takes ~30s)...")
    df = pd.read_csv(LABEL_DIR / "bindingdb_dti_labels_1to1.csv")
    df_valid = df[df['uniprot_id'].isin(prot_id_set)].reset_index(drop=True)
    n_pos = (df_valid['label'] == 1).sum()
    n_neg = (df_valid['label'] == 0).sum()
    print(f"  Total rows: {len(df):,}  ->  valid: {len(df_valid):,}")
    print(f"  Positives: {n_pos:,}  Negatives: {n_neg:,}")

    # ── Step 3: Sample balanced pairs ───────────────────────────────────────
    print(f"Step 3: Sampling {N_PAIRS:,} pairs (balanced)...")
    n_each = N_PAIRS // 2
    pos = df_valid[df_valid['label'] == 1].sample(n=min(n_each, n_pos), random_state=args.seed)
    neg = df_valid[df_valid['label'] == 0].sample(n=min(n_each, n_neg), random_state=args.seed)
    sample_df = pd.concat([pos, neg]).sample(frac=1, random_state=args.seed).reset_index(drop=True)
    needed_smiles = set(sample_df['smiles'].unique())
    print(f"  Sampled: {len(sample_df):,} pairs  ({len(pos):,} pos, {len(neg):,} neg)")
    print(f"  Unique SMILES needed: {len(needed_smiles):,}")

    # ── Step 4: Extract drug graphs from chunks (one at a time) ─────────────
    out_graph = GRAPH_DIR / "bindingdb_pretrain_drug_graphs.pt"
    if out_graph.exists():
        print(f"Step 4: Drug graphs already extracted -> {out_graph}")
        extracted_smiles = set(torch.load(out_graph, map_location='cpu', weights_only=False).keys())
    else:
        print(f"Step 4: Scanning {len(list(CHUNK_DIR.glob('chunk_*.pt')))} chunks...")
        chunk_files = sorted(CHUNK_DIR.glob("chunk_*.pt"))
        extracted = {}
        for cf in tqdm(chunk_files, desc="  Scanning chunks"):
            chunk = torch.load(cf, map_location="cpu", weights_only=False)
            for smi, graph in chunk.items():
                if smi in needed_smiles:
                    extracted[smi] = graph
            del chunk
            if len(extracted) >= len(needed_smiles):
                print(f"  All SMILES found at {cf.name}, stopping early.")
                break
        print(f"  Extracted: {len(extracted):,} / {len(needed_smiles):,} drug graphs")
        torch.save(extracted, out_graph)
        print(f"  Saved -> {out_graph}")
        extracted_smiles = set(extracted.keys())

    # ── Step 5: Filter sample to rows with found drug graphs ─────────────────
    sample_df = sample_df[sample_df['smiles'].isin(extracted_smiles)].reset_index(drop=True)
    print(f"Step 5: Pairs after drug graph filter: {len(sample_df):,}")

    # ── Step 6: Save label CSV with drug_id / protein_id columns ────────────
    out_df = sample_df[['smiles', 'uniprot_id', 'label']].copy()
    out_df.columns = ['drug_id', 'protein_id', 'label']
    out_label = LABEL_DIR / "bindingdb_pretrain_dti_labels_1to1.csv"
    out_df.to_csv(out_label, index=False)
    print(f"  Saved labels -> {out_label} ({len(out_df):,} rows)")
    print(f"  Final pos/neg: {(out_df['label']==1).sum()} / {(out_df['label']==0).sum()}")

    # ── Step 7: Copy protein embeddings (same file, new dataset name) ────────
    out_emb  = EMB_DIR / "bindingdb_pretrain_protein_embeddings.npy"
    out_pids = EMB_DIR / "bindingdb_pretrain_protein_ids.json"
    src_emb  = EMB_DIR / "bindingdb_protein_embeddings.npy"
    src_pids = EMB_DIR / "bindingdb_protein_ids.json"
    if not out_emb.exists():
        shutil.copy(src_emb, out_emb)
        print(f"  Copied protein embeddings -> {out_emb}")
    if not out_pids.exists():
        shutil.copy(src_pids, out_pids)
        print(f"  Copied protein IDs -> {out_pids}")

    # ── Step 8: Generate random train/val/test split (fold 0 only) ──────────
    n = len(out_df)
    idx = list(range(n))
    random.shuffle(idx)
    n_test  = int(n * TEST_FRAC)
    n_val   = int(n * VAL_FRAC)
    n_train = n - n_val - n_test
    split = {
        "fold_0": {
            "train": idx[:n_train],
            "val":   idx[n_train:n_train + n_val],
            "test":  idx[n_train + n_val:]
        }
    }
    out_split = SPLIT_DIR / "bindingdb_pretrain_dti_labels_1to1_random_split.json"
    with open(out_split, 'w') as f:
        json.dump(split, f)
    print(f"  Saved split -> {out_split}")
    print(f"  Train: {n_train:,}  Val: {n_val:,}  Test: {n_test:,}")

    print(f"\n{'='*60}")
    print("  Preprocessing complete!")
    print(f"  Dataset name for training: bindingdb_pretrain")
    print(f"  Run: python train.py --dataset bindingdb_pretrain --task dti "
          f"--split random --ratio 1to1")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
