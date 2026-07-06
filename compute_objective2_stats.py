"""
Objective 2 -- Statistical Analysis Script

Loads results for all Phase 1, Phase 2, Phase 3, and Phase 5 experiment
configurations, computes mean ± std across 5 seeds, and runs paired t-tests
against the Objective 1 baseline (C0 = hgnn_rnn_dti, focal γ=2, 1:1, ESM-2 8M).

Usage:
    python compute_objective2_stats.py              # Phase 2 (all loss/ratio configs)
    python compute_objective2_stats.py --phase 1    # Phase 1 (embedding configs)
    python compute_objective2_stats.py --phase 3    # Phase 3 (BindingDB pretraining)
    python compute_objective2_stats.py --phase 5    # Phase 5 (full ablation C0-C3)
    python compute_objective2_stats.py --phase all  # All phases
    python compute_objective2_stats.py --dataset yamanishi_e
    python compute_objective2_stats.py --metric auprc
"""

import json, argparse, sys, io
import numpy as np
from pathlib import Path
from scipy import stats

# Force UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

LOG  = Path("logs")
SEEDS  = [1, 2, 3, 4, 5]
SPLITS = ["random", "cold_drug", "cold_target", "cold_pair"]

# ── Configuration registry ─────────────────────────────────────────────────────

PHASE2_CONFIGS = [
    # (run_name,               label,                       datasets)
    ("hgnn_rnn_dti",           "C0 -- Focal 1:1  (baseline)",  ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_1to5",      "P2-F -- Focal 1:5",            ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_1to10",     "P2-G -- Focal 1:10",           ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_wbce",      "P2-B -- WeightedBCE 1:1",      ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_gamma1",    "P2-C -- Focal g=1  1:1",       ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_gamma3",    "P2-D -- Focal g=3  1:1",       ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_gamma5",    "P2-E -- Focal g=5  1:1",       ["yamanishi_e", "luo_17"]),
]

PHASE1_CONFIGS = [
    ("hgnn_rnn_dti",           "P1-A -- ESM-2 8M  (baseline)", ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_esm150m",   "P1-B -- ESM-2 150M",           ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_esm650m",   "P1-C -- ESM-2 650M",           ["yamanishi_e", "luo_17"]),
]

PHASE3_CONFIGS = [
    # Baseline is reused from PHASE2_CONFIGS (same C0 run)
    ("hgnn_rnn_dti",           "C0 -- Scratch (baseline)",      ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_phase3_ft", "P3-A -- BindingDB pretrained",  ["yamanishi_e", "luo_17"]),
]

# Phase 5 — Full Ablation Matrix (C0 → C1 → C2 → C3, additive)
PHASE5_CONFIGS = [
    ("hgnn_rnn_dti",                       "C0 -- 8M  1:1  none    (baseline)", ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_esm150m",               "C1 -- 150M 1:1  none",              ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_esm150m_1to5",          "C2 -- 150M 1:5  none",              ["yamanishi_e", "luo_17"]),
    ("hgnn_rnn_dti_phase3_ft_esm150m_1to5","C3 -- 150M 1:5  BindingDB",         ["yamanishi_e", "luo_17"]),
]


# ── Data loading ───────────────────────────────────────────────────────────────

def load_metric(run_name, dataset, split, seed, metric):
    p = LOG / f"{run_name}_{dataset}_dti_{split}_fold0_seed{seed}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        return d["test_metrics"].get(metric)
    except Exception:
        return None


def collect(run_name, dataset, split, metric):
    vals = [load_metric(run_name, dataset, split, s, metric) for s in SEEDS]
    return [v for v in vals if v is not None]


# ── Formatting ─────────────────────────────────────────────────────────────────

def fmt(vals):
    if not vals:
        return "N/A            "
    return f"{np.mean(vals):.3f}±{np.std(vals, ddof=1):.3f}  "


def sig_label(p):
    if p < 0.01:
        return "p<0.01 ✓✓"
    if p < 0.05:
        return "p<0.05 ✓"
    return "n.s.      "


# ── Reporting ──────────────────────────────────────────────────────────────────

def report(configs, datasets, metric):
    baseline_run = configs[0][0]

    for ds in datasets:
        print(f"\n{'='*80}")
        print(f"  Dataset: {ds.upper()}    Metric: {metric.upper()}")
        print(f"{'='*80}")

        # Header
        label_w = 30
        header  = f"  {'Config':<{label_w}}  " + "  ".join(f"{sp:<14}" for sp in SPLITS)
        print(header)
        print("  " + "-" * (len(header) - 2))

        # Collect baseline values for t-test
        baseline = {sp: collect(baseline_run, ds, sp, metric) for sp in SPLITS}

        for run_name, label, cfg_datasets in configs:
            if ds not in cfg_datasets:
                continue
            row = f"  {label:<{label_w}}  "
            for sp in SPLITS:
                vals = collect(run_name, ds, sp, metric)
                row += fmt(vals)
            print(row)

        # Significance table vs. C0
        print(f"\n  Statistical comparison vs. {configs[0][1].split('--')[1].strip()} (paired t-test, n=5):")
        print(f"  {'Config':<{label_w}}  " + "  ".join(f"{sp:<20}" for sp in SPLITS))
        print("  " + "-" * (len(header) + 40))

        for run_name, label, cfg_datasets in configs[1:]:
            if ds not in cfg_datasets:
                continue
            row = f"  {label:<{label_w}}  "
            for sp in SPLITS:
                exp_vals  = collect(run_name, ds, sp, metric)
                base_vals = baseline[sp]
                if len(exp_vals) < 2 or len(base_vals) < 2:
                    row += f"{'N/A':<20}  "
                    continue
                n = min(len(exp_vals), len(base_vals))
                t, p = stats.ttest_rel(exp_vals[:n], base_vals[:n])
                delta = np.mean(exp_vals[:n]) - np.mean(base_vals[:n])
                sign  = "+" if delta >= 0 else ""
                row += f"{sign}{delta:.3f} {sig_label(p):<12}"
            print(row)


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase",   default="2", choices=["1", "2", "3", "5", "all"])
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--metric",  default="auroc",
                        choices=["auroc", "auprc", "f1", "acc"])
    args = parser.parse_args()

    all_configs = []
    if args.phase in ("2", "all"):
        all_configs.extend(PHASE2_CONFIGS)
    if args.phase in ("1", "all"):
        seen = {c[0] for c in all_configs}
        all_configs.extend(c for c in PHASE1_CONFIGS if c[0] not in seen)
    if args.phase in ("3", "all"):
        seen = {c[0] for c in all_configs}
        all_configs.extend(c for c in PHASE3_CONFIGS if c[0] not in seen)
    if args.phase in ("5", "all"):
        seen = {c[0] for c in all_configs}
        all_configs.extend(c for c in PHASE5_CONFIGS if c[0] not in seen)

    datasets = [args.dataset] if args.dataset else ["yamanishi_e", "luo_17"]

    print(f"\nObjective 2 -- Statistical Analysis")
    print(f"Metric: {args.metric.upper()}   Phase: {args.phase}")

    report(all_configs, datasets, args.metric)

    print(f"\n{'='*80}")
    print("  Note: N/A = log file not yet present; run the relevant experiments first.")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
