"""
Compile DTA results from all 5 seeds for davis and kiba.
Run after all seeds are complete to get final mean ± std and
print a ready-to-paste Section 3.5 table.
"""

import json, glob, numpy as np

def load_seed(dataset, seed):
    path = f"logs/hgnn_rnn_dti_{dataset}_dta_random_fold0_seed{seed}.json"
    try:
        with open(path) as f:
            d = json.load(f)
        return d["test_metrics"], d["best_epoch"]
    except FileNotFoundError:
        return None, None

METRICS = ["mse", "mae", "rmse", "r2", "pearson", "spearman"]
SEEDS   = [1, 2, 3, 4, 5]

print("\n=== DTA Results (H-GNN-RNN-DTI, random split, fold 0) ===\n")

for dataset in ["davis", "kiba"]:
    results, epochs = [], []
    missing = []
    for seed in SEEDS:
        m, ep = load_seed(dataset, seed)
        if m:
            results.append(m)
            epochs.append(ep)
        else:
            missing.append(seed)

    n = len(results)
    status = f"{n}/5 seeds" + (f"  [MISSING seeds: {missing}]" if missing else " (complete)")
    print(f"--- {dataset.upper()} ({status}) ---")

    if not results:
        print("  No results yet.\n")
        continue

    for k in METRICS:
        vals = np.array([r[k] for r in results])
        print(f"  {k:10s}: {np.mean(vals):.4f} ± {np.std(vals):.4f}"
              f"  [{', '.join(f'{v:.4f}' for v in vals)}]")

    print(f"  best_epochs: {epochs}\n")

# Markdown table for Section 3.5
print("\n=== Markdown table ===\n")
print("| Metric | Davis | KIBA |")
print("|---|---|---|")

rows = {}
for dataset in ["davis", "kiba"]:
    results = []
    for seed in SEEDS:
        m, _ = load_seed(dataset, seed)
        if m:
            results.append(m)
    rows[dataset] = results

for k, label in [("mse","MSE"), ("mae","MAE"), ("rmse","RMSE"), ("r2","R²"),
                 ("pearson","Pearson r"), ("spearman","Spearman ρ")]:
    davis_vals = np.array([r[k] for r in rows.get("davis", [])])
    kiba_vals  = np.array([r[k] for r in rows.get("kiba",  [])])

    davis_str = (f"{np.mean(davis_vals):.3f} ± {np.std(davis_vals):.3f}"
                 if len(davis_vals) == 5 else f"({len(davis_vals)}/5 seeds)")
    kiba_str  = (f"{np.mean(kiba_vals):.3f} ± {np.std(kiba_vals):.3f}"
                 if len(kiba_vals) == 5 else f"({len(kiba_vals)}/5 seeds)")

    print(f"| {label} | {davis_str} | {kiba_str} |")
