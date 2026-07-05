"""
Objective 2 — Phase 1: Foundation Model Embedding Comparison

Experiments:
  P1-A (baseline):  hgnn_rnn_dti + ESM-2 8M  (already done in Obj 1 — loads existing logs)
  P1-B:             hgnn_rnn_dti + ESM-2 150M (runs here)
  P1-C:             hgnn_rnn_dti + ESM-2 650M (runs here, if embeddings exist)

Datasets: yamanishi_e, luo_17
Splits:   random, cold_drug, cold_target, cold_pair
Seeds:    1, 2, 3, 4, 5

Usage:
    python run_objective2_phase1.py                  # preprocess ESM-2 150M then train
    python run_objective2_phase1.py --skip_preproc   # skip preprocessing, train only
    python run_objective2_phase1.py --emb esm650m    # use 650M instead of 150M
    python run_objective2_phase1.py --dataset yamanishi_e  # one dataset only
"""

import os, sys, subprocess, argparse, json
from pathlib import Path

PYTHON = sys.executable
ROOT   = Path(__file__).parent
LOG_DIR  = ROOT / "logs"
DATA_DIR = ROOT / "Dataset" / "processed" / "protein_embeddings"

SEEDS   = [1, 2, 3, 4, 5]
SPLITS  = ["random", "cold_drug", "cold_target", "cold_pair"]
DATASETS = {
    "yamanishi_e": "dti",
    "luo_17":      "dti",
}


def run(cmd, desc=""):
    print(f"\n{'-'*60}")
    print(f"  {desc}")
    print(f"  CMD: {' '.join(str(c) for c in cmd)}")
    print(f"{'-'*60}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"  WARNING: command exited with code {result.returncode}")
    return result.returncode


def log_exists(run_name, dataset, task, split, seed):
    p = LOG_DIR / f"{run_name}_{dataset}_{task}_{split}_fold0_seed{seed}.json"
    return p.exists()


def emb_exists(dataset, tag):
    if not tag or tag == "esm8m":
        p = DATA_DIR / f"{dataset}_protein_embeddings.npy"
    else:
        p = DATA_DIR / f"{dataset}_{tag}_protein_embeddings.npy"
    return p.exists()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--emb',         default='esm150m',
                        choices=['esm150m', 'esm650m'],
                        help='ESM-2 variant to run (default: esm150m).')
    parser.add_argument('--dataset',     default=None,
                        help='Run only this dataset (default: all).')
    parser.add_argument('--skip_preproc', action='store_true',
                        help='Skip protein preprocessing (assume embeddings already exist).')
    parser.add_argument('--dry_run',     action='store_true',
                        help='Print commands without running them.')
    args = parser.parse_args()

    datasets = (
        {args.dataset: DATASETS[args.dataset]}
        if args.dataset else DATASETS
    )
    emb_tag  = args.emb
    run_name = f"hgnn_rnn_dti_{emb_tag}"

    print(f"\n{'='*60}")
    print(f"  Objective 2 — Phase 1: Embedding Comparison")
    print(f"  Embedding tag: {emb_tag}")
    print(f"  Run name:      {run_name}")
    print(f"  Datasets:      {list(datasets.keys())}")
    print(f"{'='*60}\n")

    # ── Step 1: Preprocess protein embeddings ────────────────────────────────
    if not args.skip_preproc:
        for ds in datasets:
            if emb_exists(ds, emb_tag):
                print(f"  {ds} [{emb_tag}]: embeddings exist — skipping preprocessing.")
                continue
            print(f"\n  Preprocessing {ds} with {emb_tag}...")
            cmd = [PYTHON, "Dataset/11_preprocess_proteins.py",
                   "--dataset", ds, "--esm_model", emb_tag]
            if not args.dry_run:
                rc = run(cmd, f"ESM-2 {emb_tag} embeddings for {ds}")
                if rc != 0:
                    print(f"  ERROR: preprocessing failed for {ds}. Aborting.")
                    sys.exit(1)
            else:
                print(f"  [DRY RUN] {' '.join(str(c) for c in cmd)}")

    # ── Step 2: Train P1-B (or P1-C) configs ────────────────────────────────
    total = len(datasets) * len(SPLITS) * len(SEEDS)
    done  = 0
    skipped = 0

    for ds, task in datasets.items():
        if not emb_exists(ds, emb_tag):
            print(f"\n  {ds} [{emb_tag}]: embeddings not found — skipping training.")
            continue

        for split in SPLITS:
            for seed in SEEDS:
                done += 1
                if log_exists(run_name, ds, task, split, seed):
                    print(f"  [{done}/{total}] {run_name} {ds} {split} seed{seed} — DONE (skip)")
                    skipped += 1
                    continue

                cmd = [
                    PYTHON, "train.py",
                    "--dataset",         ds,
                    "--task",            task,
                    "--split",           split,
                    "--seed",            str(seed),
                    "--ratio",           "1to1",
                    "--fold",            "0",
                    "--protein_emb_tag", emb_tag,
                    "--run_name",        run_name,
                ]
                desc = f"[{done}/{total}] {run_name} | {ds} | {split} | seed {seed}"
                if args.dry_run:
                    print(f"  [DRY RUN] {' '.join(str(c) for c in cmd)}")
                else:
                    run(cmd, desc)

    print(f"\n{'='*60}")
    print(f"  Phase 1 complete.")
    print(f"  Total runs: {total}  |  Skipped (already done): {skipped}")
    print(f"  New runs:   {total - skipped}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
