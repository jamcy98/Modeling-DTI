"""
Objective 2 — Phase 5: Full Ablation (C2 and C3)

Ablation matrix:
  C0 — Objective 1 baseline: ChemBERTa + ESM-2 8M, Focal γ=2, 1:1          (done)
  C1 — Better embedding:     ChemBERTa + ESM-2 150M, Focal γ=2, 1:1         (done in Phase 1)
  C2 — Embedding + Ratio:    ChemBERTa + ESM-2 150M, Focal γ=2, 1:5         (this script)
  C3 — C2 + Pretraining:     C2 settings + BindingDB pretrained init         (this script)

Each configuration is run for 5 seeds × 2 datasets × 4 splits = 40 runs.

Usage:
    python run_phase5_ablation.py                      # run C2 then C3
    python run_phase5_ablation.py --only c2            # run C2 only
    python run_phase5_ablation.py --only c3            # run C3 only (requires C2 checkpoint)
    python run_phase5_ablation.py --device cpu --epochs 100
"""

import os, sys, subprocess, time, argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent
PYTHON   = sys.executable

# ── Config ────────────────────────────────────────────────────────────────────

DATASETS = {
    "yamanishi_e": ["random", "cold_drug", "cold_target", "cold_pair"],
    "luo_17":      ["random", "cold_drug", "cold_target", "cold_pair"],
}
SEEDS = [1, 2, 3, 4, 5]

# C2: ESM-2 150M + 1:5 ratio, from scratch
C2_RUN_NAME      = "hgnn_rnn_dti_esm150m_1to5"
C2_RATIO         = "1to5"
C2_EMB_TAG       = "esm150m"

# C3: same as C2 but with BindingDB pretrained encoder init
C3_RUN_NAME      = "hgnn_rnn_dti_phase3_ft_esm150m_1to5"
C3_PRETRAIN_CKPT = (BASE_DIR / "checkpoints" /
                    "hgnn_rnn_dti_phase3_bindingdb_pretrain_dti_random_fold0_seed1_best.pt")


def run(cmd, label="", check=True):
    print(f"\n{'-'*60}")
    if label:
        print(f"  {label}")
    print(f"  CMD: {' '.join(str(x) for x in cmd)}")
    print(f"{'-'*60}")
    t0 = time.time()
    result = subprocess.run(cmd, check=check)
    elapsed = time.time() - t0
    print(f"  Finished in {elapsed/60:.1f} min (exit={result.returncode})")
    return result


def log_exists(run_name, dataset, split, seed):
    p = BASE_DIR / "logs" / f"{run_name}_{dataset}_dti_{split}_fold0_seed{seed}.json"
    return p.exists()


def count_remaining(run_name):
    total = sum(len(splits) for splits in DATASETS.values()) * len(SEEDS)
    done  = sum(
        1 for ds, splits in DATASETS.items()
          for sp in splits
          for sd in SEEDS
          if log_exists(run_name, ds, sp, sd)
    )
    return total, total - done


def run_config(run_name, ratio, emb_tag, epochs, batch_size, lr, device,
               pretrain_ckpt=None):
    total, remaining = count_remaining(run_name)
    print(f"\n[{run_name}] {total} total runs, {remaining} remaining.")
    done = 0
    skipped = 0

    for dataset, splits in DATASETS.items():
        for split in splits:
            for seed in SEEDS:
                run_num = done + skipped + 1
                if log_exists(run_name, dataset, split, seed):
                    print(f"  [SKIP] {run_name} {dataset} {split} seed{seed}")
                    skipped += 1
                    continue

                cmd = [
                    PYTHON, "train.py",
                    "--dataset",         dataset,
                    "--task",            "dti",
                    "--split",           split,
                    "--ratio",           ratio,
                    "--protein_emb_tag", emb_tag,
                    "--model",           "hgnn_rnn_dti",
                    "--run_name",        run_name,
                    "--seed",            str(seed),
                    "--epochs",          str(epochs),
                    "--batch_size",      str(batch_size),
                    "--lr",              str(lr),
                    "--device",          device,
                ]
                if pretrain_ckpt:
                    cmd += ["--pretrain_checkpoint", str(pretrain_ckpt)]

                run(cmd, label=(f"{run_name}  {dataset} {split} seed={seed} "
                                f"({run_num}/{total})"))
                done += 1

    print(f"\n[{run_name}] Done.  New runs: {done}  Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only',       default=None, choices=["c2", "c3"],
                        help='Run only C2 or C3 (default: both in sequence)')
    parser.add_argument('--device',     default='cpu')
    parser.add_argument('--epochs',     type=int, default=100)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--lr_c2',      type=float, default=1e-3,
                        help='Learning rate for C2 from-scratch runs')
    parser.add_argument('--lr_c3',      type=float, default=1e-4,
                        help='Learning rate for C3 fine-tuning runs')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("  Objective 2 — Phase 5: Full Ablation (C2 and C3)")
    print(f"  Device: {args.device}   Epochs: {args.epochs}")
    print(f"  C2 LR: {args.lr_c2}   C3 LR: {args.lr_c3}")
    print(f"{'='*60}\n")

    run_c2 = args.only in (None, "c2")
    run_c3 = args.only in (None, "c3")

    # ── C2: ESM-2 150M + 1:5 ratio, from scratch ─────────────────────────────
    if run_c2:
        print(f"\n{'='*60}")
        print(f"  C2: ESM-2 150M + 1:5 ratio (from scratch)")
        print(f"  run_name: {C2_RUN_NAME}")
        print(f"{'='*60}")
        run_config(
            run_name    = C2_RUN_NAME,
            ratio       = C2_RATIO,
            emb_tag     = C2_EMB_TAG,
            epochs      = args.epochs,
            batch_size  = args.batch_size,
            lr          = args.lr_c2,
            device      = args.device,
            pretrain_ckpt = None,
        )

    # ── C3: C2 settings + BindingDB pretrained init ───────────────────────────
    if run_c3:
        if not C3_PRETRAIN_CKPT.exists():
            print(f"\nERROR: BindingDB pretrain checkpoint not found:")
            print(f"  {C3_PRETRAIN_CKPT}")
            print("  Run run_objective2_phase3.py first.")
            sys.exit(1)

        print(f"\n{'='*60}")
        print(f"  C3: ESM-2 150M + 1:5 ratio + BindingDB pretrained init")
        print(f"  run_name:    {C3_RUN_NAME}")
        print(f"  pretrain_ckpt: {C3_PRETRAIN_CKPT.name}")
        print(f"  NOTE: prot_input_proj is re-initialised (8M→150M shape mismatch).")
        print(f"        Drug encoder + cross-attention weights carry over from BindingDB.")
        print(f"{'='*60}")
        run_config(
            run_name    = C3_RUN_NAME,
            ratio       = C2_RATIO,
            emb_tag     = C2_EMB_TAG,
            epochs      = args.epochs,
            batch_size  = args.batch_size,
            lr          = args.lr_c3,
            device      = args.device,
            pretrain_ckpt = C3_PRETRAIN_CKPT,
        )

    print(f"\n{'='*60}")
    print("  Phase 5 ablation complete.")
    print("  Next: compute statistics with:")
    print("    python compute_objective2_stats.py --phase 5")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
