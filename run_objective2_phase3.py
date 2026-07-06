"""
Objective 2 — Phase 3: BindingDB Pretraining + Fine-tuning

Pipeline:
  1. Preprocess BindingDB subset (50K pairs) via Dataset/14_preprocess_bindingdb_subset.py
  2. Pretrain H-GNN-RNN-DTI on the BindingDB subset (1 seed)
  3. Fine-tune (with pretrained weights) on yamanishi_e × 4 splits × 5 seeds
  4. Fine-tune on luo_17 × 4 splits × 5 seeds

Logs are written to logs/ with run_name prefix hgnn_rnn_dti_phase3_ft.
Use compute_objective2_stats.py --phase phase3 to compute paired t-tests.

Usage:
    python run_objective2_phase3.py [--skip_preprocess] [--skip_pretrain]
                                    [--device cpu] [--epochs 100]
"""

import os, sys, subprocess, json, time, argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent
PYTHON   = sys.executable

# ── Config ────────────────────────────────────────────────────────────────────

PRETRAIN_DATASET  = "bindingdb_pretrain"
PRETRAIN_RUN_NAME = "hgnn_rnn_dti_phase3"
PRETRAIN_SEED     = 1

FINETUNE_RUN_NAME = "hgnn_rnn_dti_phase3_ft"
BASELINE_RUN_NAME = "hgnn_rnn_dti"   # Objective 1 baseline (for comparison)

DATASETS = {
    "yamanishi_e": ["random", "cold_drug", "cold_target", "cold_pair"],
    "luo_17":      ["random", "cold_drug", "cold_target", "cold_pair"],
}
SEEDS = [1, 2, 3, 4, 5]


def run(cmd, label="", check=True):
    print(f"\n{'-'*60}")
    if label:
        print(f"  {label}")
    print(f"  CMD: {' '.join(cmd)}")
    print(f"{'-'*60}")
    t0 = time.time()
    result = subprocess.run(cmd, check=check)
    elapsed = time.time() - t0
    print(f"  Finished in {elapsed/60:.1f} min (exit={result.returncode})")
    return result


def pretrain_ckpt_path(dataset, split, seed, run_name=None):
    rn = run_name or PRETRAIN_RUN_NAME
    return BASE_DIR / "checkpoints" / (
        f"{rn}_{dataset}_dti_{split}_fold0_seed{seed}_best.pt"
    )


def log_exists(run_name, dataset, split, seed):
    p = BASE_DIR / "logs" / f"{run_name}_{dataset}_dti_{split}_fold0_seed{seed}.json"
    return p.exists()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip_preprocess', action='store_true',
                        help='Skip Dataset/14_preprocess_bindingdb_subset.py')
    parser.add_argument('--skip_pretrain', action='store_true',
                        help='Skip BindingDB pretraining (use existing checkpoint)')
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--pretrain_epochs', type=int, default=50,
                        help='Epochs for BindingDB pretraining (default 50)')
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--lr', type=float, default=1e-4)
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("  Objective 2 — Phase 3: BindingDB Pretraining + Fine-tuning")
    print(f"  Device: {args.device}  Pretrain epochs: {args.pretrain_epochs}")
    print(f"  Finetune epochs: {args.epochs}  LR: {args.lr}")
    print(f"{'='*60}\n")

    # ── Step 1: Preprocess BindingDB subset ───────────────────────────────────
    if not args.skip_preprocess:
        label_path = BASE_DIR / "Dataset" / "processed" / "labels" / \
                     "bindingdb_pretrain_dti_labels_1to1.csv"
        if label_path.exists():
            print(f"[Step 1] Subset label CSV already exists ({label_path.name}). Skipping.")
        else:
            run([PYTHON, str(BASE_DIR / "Dataset" / "14_preprocess_bindingdb_subset.py")],
                label="Step 1: BindingDB subset preprocessing")
    else:
        print("[Step 1] Skipped (--skip_preprocess).")

    # ── Step 2: Pretrain on BindingDB subset ──────────────────────────────────
    pretrain_ckpt = pretrain_ckpt_path(PRETRAIN_DATASET, "random", PRETRAIN_SEED)
    if not args.skip_pretrain:
        if pretrain_ckpt.exists():
            print(f"\n[Step 2] Pretrain checkpoint exists: {pretrain_ckpt.name}. Skipping.")
        else:
            run([
                PYTHON, "train.py",
                "--dataset",    PRETRAIN_DATASET,
                "--task",       "dti",
                "--split",      "random",
                "--ratio",      "1to1",
                "--model",      "hgnn_rnn_dti",
                "--run_name",   PRETRAIN_RUN_NAME,
                "--seed",       str(PRETRAIN_SEED),
                "--epochs",     str(args.pretrain_epochs),
                "--batch_size", str(args.batch_size),
                "--lr",         str(args.lr),
                "--device",     args.device,
            ], label="Step 2: Pretrain on BindingDB subset")
    else:
        print(f"\n[Step 2] Skipped (--skip_pretrain). "
              f"Using checkpoint: {pretrain_ckpt}")

    if not pretrain_ckpt.exists():
        print(f"\nERROR: Pretrain checkpoint not found at {pretrain_ckpt}")
        print("  Run Step 2 first, or pass --skip_pretrain with an existing checkpoint.")
        sys.exit(1)

    print(f"\n[Phase 3] Using pretrained checkpoint: {pretrain_ckpt.name}")

    # ── Step 3 & 4: Fine-tune on yamanishi_e and luo_17 ───────────────────────
    total_runs  = sum(len(splits) for splits in DATASETS.values()) * len(SEEDS)
    done_runs   = 0
    skipped     = 0

    print(f"\n[Fine-tuning] Total runs planned: {total_runs}")
    print(f"  Datasets: {list(DATASETS.keys())}")
    print(f"  Splits: {list(DATASETS.values())}")
    print(f"  Seeds: {SEEDS}\n")

    for dataset, splits in DATASETS.items():
        for split in splits:
            for seed in SEEDS:
                if log_exists(FINETUNE_RUN_NAME, dataset, split, seed):
                    print(f"  [SKIP] {FINETUNE_RUN_NAME} {dataset} {split} seed{seed}")
                    skipped += 1
                    done_runs += 1
                    continue

                run([
                    PYTHON, "train.py",
                    "--dataset",             dataset,
                    "--task",                "dti",
                    "--split",               split,
                    "--ratio",               "1to1",
                    "--model",               "hgnn_rnn_dti",
                    "--run_name",            FINETUNE_RUN_NAME,
                    "--seed",                str(seed),
                    "--epochs",              str(args.epochs),
                    "--batch_size",          str(args.batch_size),
                    "--lr",                  str(args.lr),
                    "--device",              args.device,
                    "--pretrain_checkpoint", str(pretrain_ckpt),
                ], label=f"Fine-tune: {dataset} {split} seed={seed} "
                         f"({done_runs+1}/{total_runs})")

                done_runs += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Phase 3 complete!")
    print(f"  Total runs: {total_runs}  Skipped: {skipped}  New: {total_runs - skipped}")
    print(f"\n  Next: compute statistics with:")
    print(f"    python compute_objective2_stats.py --phase phase3")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
