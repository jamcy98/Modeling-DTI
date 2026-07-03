import json, numpy as np
from scipy import stats

def load(prefix, dataset, seed):
    path = f"logs/{prefix}_{dataset}_dta_random_fold0_seed{seed}.json"
    try:
        with open(path) as f:
            return json.load(f)["test_metrics"]
    except:
        return None

METRICS = ["mse", "mae", "rmse", "r2", "pearson", "spearman"]
SEEDS = [1, 2, 3, 4, 5]

results = {}
for model in ["hgnn_rnn_dti", "concat_baseline"]:
    results[model] = {}
    for ds in ["davis", "kiba"]:
        data = [load(model, ds, s) for s in SEEDS]
        data = [d for d in data if d is not None]
        results[model][ds] = {k: np.array([d[k] for d in data]) for k in METRICS}

print("=== MEANS +- STD (ddof=1) ===")
for ds in ["davis", "kiba"]:
    print(f"\n  {ds.upper()}:")
    for k in METRICS:
        h = results["hgnn_rnn_dti"][ds][k]
        c = results["concat_baseline"][ds][k]
        t, p = stats.ttest_rel(h, c)
        sig = "p<0.01" if p < 0.01 else ("p<0.05" if p < 0.05 else "n.s.")
        delta = np.mean(h) - np.mean(c)
        print(f"    {k:<10} H={np.mean(h):.4f}+-{np.std(h,ddof=1):.4f}  "
              f"C={np.mean(c):.4f}+-{np.std(c,ddof=1):.4f}  "
              f"delta={delta:+.4f}  t={t:.3f}  p={p:.4f}  {sig}")

print("\n=== CONCAT SEED-BY-SEED ===")
for ds in ["davis", "kiba"]:
    print(f"\n  {ds.upper()} ConcatBaseline:")
    for s in SEEDS:
        d = load("concat_baseline", ds, s)
        if d:
            mse = d["mse"]
            mae = d["mae"]
            rmse = d["rmse"]
            r2 = d["r2"]
            pear = d["pearson"]
            spear = d["spearman"]
            print(f"    seed{s}: MSE={mse:.4f} MAE={mae:.4f} RMSE={rmse:.4f} "
                  f"R2={r2:.4f} Pear={pear:.4f} Spear={spear:.4f}")

print("\n=== CONCAT MEAN+STD SUMMARY ===")
for ds in ["davis", "kiba"]:
    print(f"\n  {ds.upper()} ConcatBaseline:")
    for k in METRICS:
        c = results["concat_baseline"][ds][k]
        print(f"    {k:<10} {np.mean(c):.4f} +- {np.std(c,ddof=1):.4f}")
