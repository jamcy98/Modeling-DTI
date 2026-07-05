"""
Objective 2 — Phase 2: Imbalance-Aware Learning

Experiments:
  P2-A (baseline):  Focal γ=2  / ratio 1:1   (Obj 1 results — referenced only)
  P2-F:             Focal γ=2  / ratio 1:5   (generate labels + train)
  P2-G:             Focal γ=2  / ratio 1:10  (labels exist — train only)
  P2-B:             Weighted BCE / ratio 1:1  (train only)
  P2-C:             Focal γ=1  / ratio 1:1   (train only)
  P2-D:             Focal γ=3  / ratio 1:1   (train only)
  P2-E:             Focal γ=5  / ratio 1:1   (train only)

Datasets: yamanishi_e, luo_17
Splits:   random, cold_drug, cold_target, cold_pair
Seeds:    1, 2, 3, 4, 5

Usage:
    python run_objective2_phase2.py                         # run all experiments
    python run_objective2_phase2.py --exp ratio             # only ratio experiments (P2-F, P2-G)
    python run_objective2_phase2.py --exp loss              # only loss experiments (P2-B/C/D/E)
    python run_objective2_phase2.py --dataset yamanishi_e   # one dataset only
    python run_objective2_phase2.py --dry_run               # print commands only
"""

import os, sys, subprocess, argparse, json
from pathlib import Path

PYTHON   = sys.executable
ROOT     = Path(__file__).parent
LOG_DIR  = ROOT / "logs"
LABEL_DIR = ROOT / "Dataset" / "processed" / "labels"
SPLIT_DIR = ROOT / "Dataset" / "processed" / "splits"

SEEDS    = [1, 2, 3, 4, 5]
SPLITS   = ["random", "cold_drug", "cold_target", "cold_pair"]
DATASETS = {
    "yamanishi_e": "dti",
    "luo_17":      "dti",
}

# Experiment configs: (run_name, loss, focal_gamma, ratio)
RATIO_EXPERIMENTS = [
    ("hgnn_rnn_dti_1to5",  "focal", None,  "1to5"),
    ("hgnn_rnn_dti_1to10", "focal", None,  "1to10"),
]

LOSS_EXPERIMENTS = [
    ("hgnn_rnn_dti_wbce",     "weighted_bce", None, "1to1"),
    ("hgnn_rnn_dti_gamma1",   "focal",        1.0,  "1to1"),
    ("hgnn_rnn_dti_gamma3",   "focal",        3.0,  "1to1"),
    ("hgnn_rnn_dti_gamma5",   "focal",        5.0,  "1to1"),
]


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


def label_exists(dataset, ratio):
    p = LABEL_DIR / f"{dataset}_dti_labels_{ratio}.csv"
    return p.exists()


def split_exists(dataset, ratio, split_type):
    p = SPLIT_DIR / f"{dataset}_dti_labels_{ratio}_{split_type}_split.json"
    return p.exists()


def ensure_labels_and_splits(dataset, ratio, dry_run=False):
    """Generate label CSV and splits for a ratio if they don't exist."""
    if not label_exists(dataset, ratio):
        print(f"\n  Generating {dataset} labels ratio {ratio}...")
        cmd = [PYTHON, "Dataset/12_preprocess_labels.py",
               "--dataset", dataset, "--ratio", ratio]
        if dry_run:
            print(f"  [DRY RUN] {' '.join(str(c) for c in cmd)}")
        else:
            result = subprocess.run(cmd, cwd=ROOT)
            if result.returncode != 0:
                print(f"  ERROR: label generation failed.")
                return False
    else:
        print(f"  {dataset} {ratio} labels exist.")

    # Generate splits for this label file
    missing_splits = [s for s in SPLITS
                      if not split_exists(dataset, ratio, s)]
    if missing_splits:
        print(f"  Generating splits for {dataset} {ratio}...")
        cmd = [PYTHON, "Dataset/13_preprocess_splits.py"]
        if dry_run:
            print(f"  [DRY RUN] {' '.join(str(c) for c in cmd)}")
        else:
            result = subprocess.run(cmd, cwd=ROOT)
            if result.returncode != 0:
                print(f"  ERROR: split generation failed.")
                return False
    else:
        print(f"  {dataset} {ratio} splits exist.")
    return True


def train_experiment(experiments, datasets, dry_run=False):
    total   = len(experiments) * len(datasets) * len(SPLITS) * len(SEEDS)
    done    = 0
    skipped = 0

    for run_name, loss, gamma, ratio in experiments:
        for ds, task in datasets.items():
            for split in SPLITS:
                for seed in SEEDS:
                    done += 1
                    if log_exists(run_name, ds, task, split, seed):
                        print(f"  [{done}/{total}] {run_name} {ds} {split} seed{seed} — SKIP")
                        skipped += 1
                        continue

                    cmd = [
                        PYTHON, "train.py",
                        "--dataset",  ds,
                        "--task",     task,
                        "--split",    split,
                        "--seed",     str(seed),
                        "--ratio",    ratio,
                        "--fold",     "0",
                        "--loss",     loss,
                        "--run_name", run_name,
                    ]
                    if gamma is not None:
                        cmd += ["--focal_gamma", str(gamma)]

                    desc = f"[{done}/{total}] {run_name} | {ds} | {split} | seed {seed}"
                    if dry_run:
                        print(f"  [DRY RUN] {' '.join(str(c) for c in cmd)}")
                    else:
                        run(cmd, desc)

    return total, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', default='all',
                        choices=['all', 'ratio', 'loss'],
                        help='Which experiment group to run.')
    parser.add_argument('--dataset', default=None,
                        help='Run only this dataset.')
    parser.add_argument('--dry_run', action='store_true',
                        help='Print commands without running them.')
    args = parser.parse_args()

    datasets = (
        {args.dataset: DATASETS[args.dataset]}
        if args.dataset else DATASETS
    )

    print(f"\n{'='*60}")
    print(f"  Objective 2 — Phase 2: Imbalance-Aware Learning")
    print(f"  Experiment group: {args.exp}")
    print(f"  Datasets: {list(datasets.keys())}")
    print(f"{'='*60}\n")

    # ── Step 1: Ensure 1:5 labels and splits exist ──────────────────────────
    if args.exp in ('all', 'ratio'):
        for ds in datasets:
            ok = ensure_labels_and_splits(ds, "1to5", dry_run=args.dry_run)
            if not ok and not args.dry_run:
                print(f"  ERROR: Could not generate 1:5 data for {ds}. Aborting.")
                sys.exit(1)

        print("\n  Note: 1:10 labels and splits already exist from Objective 1 preprocessing.")

    # ── Step 2: Run experiments ──────────────────────────────────────────────
    experiments = []
    if args.exp in ('all', 'ratio'):
        experiments.extend(RATIO_EXPERIMENTS)
    if args.exp in ('all', 'loss'):
        experiments.extend(LOSS_EXPERIMENTS)

    total, skipped = train_experiment(experiments, datasets, dry_run=args.dry_run)

    print(f"\n{'='*60}")
    print(f"  Phase 2 complete.")
    print(f"  Total runs: {total}  |  Skipped: {skipped}  |  New: {total - skipped}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
