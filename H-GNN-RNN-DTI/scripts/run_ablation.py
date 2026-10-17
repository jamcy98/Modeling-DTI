"""Roadmap step 8/9: the fusion ablation — the core Objective 1 / RQ1 result.

Trains each fusion mechanism (gca vs concat vs flat_gate vs ungated_xattn) under
identical encoders/features/splits, over multiple seeds, then reports
AUROC/AUPR mean±std and a paired significance test of GCA vs each baseline.

Usage (GPU, full):
    python scripts/run_ablation.py --dataset davis --device cuda --seeds 42 43 44
Quick CPU smoke:
    python scripts/run_ablation.py --device cpu --seeds 42 --epochs 1 --max-batches 3 \
        --fusions gca concat
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import ttest_rel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hgnn_rnn_dti.fusion import FUSION_NAMES
from hgnn_rnn_dti.training.run import run_experiment
from hgnn_rnn_dti.utils.config import clone_config, load_config


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="davis")
    ap.add_argument("--root", default=str(ROOT / "data"))
    ap.add_argument("--config", default=str(ROOT / "configs" / "default.yaml"))
    ap.add_argument("--split", default="S1")
    ap.add_argument("--fusions", nargs="+", default=FUSION_NAMES)
    ap.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--max-batches", type=int, default=None)
    ap.add_argument("--max-protein-length", type=int, default=None)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    base = load_config(args.config)
    records = []
    for fusion in args.fusions:
        for seed in args.seeds:
            cfg = clone_config(base)
            cfg["task"] = "classification"
            cfg["model"]["fusion"]["type"] = fusion
            if args.epochs is not None:
                cfg["train"]["epochs"] = args.epochs
            if args.batch_size is not None:
                cfg["train"]["batch_size"] = args.batch_size
            print(f"\n### fusion={fusion} seed={seed} device={args.device} ###")
            res = run_experiment(
                cfg, args.root, args.dataset, split=args.split, seed=seed,
                device=args.device, max_batches=args.max_batches,
                max_protein_length=args.max_protein_length, verbose=True,
            )
            rec = {"fusion": fusion, "seed": seed, **res["test"],
                   "epochs_run": res["epochs_run"], "elapsed_sec": res["elapsed_sec"]}
            records.append(rec)
            print(f"  -> test AUROC {rec.get('auroc'):.4f} AUPR {rec.get('aupr'):.4f} "
                  f"({res['elapsed_sec']}s)")

    # aggregate mean±std per fusion
    summary = {}
    for fusion in args.fusions:
        aurocs = [r["auroc"] for r in records if r["fusion"] == fusion]
        auprs = [r["aupr"] for r in records if r["fusion"] == fusion]
        summary[fusion] = {
            "auroc_mean": float(np.mean(aurocs)), "auroc_std": float(np.std(aurocs)),
            "aupr_mean": float(np.mean(auprs)), "aupr_std": float(np.std(auprs)),
            "seeds": len(auprs),
        }

    # paired significance test: GCA vs each baseline on AUPR (aligned by seed)
    sig = {}
    if "gca" in args.fusions and len(args.seeds) >= 2:
        gca_by_seed = {r["seed"]: r["aupr"] for r in records if r["fusion"] == "gca"}
        for fusion in args.fusions:
            if fusion == "gca":
                continue
            other = {r["seed"]: r["aupr"] for r in records if r["fusion"] == fusion}
            seeds = sorted(set(gca_by_seed) & set(other))
            if len(seeds) >= 2:
                a = [gca_by_seed[s] for s in seeds]
                b = [other[s] for s in seeds]
                t, p = ttest_rel(a, b)
                sig[f"gca_vs_{fusion}"] = {
                    "aupr_delta": float(np.mean(a) - np.mean(b)),
                    "t_stat": float(t), "p_value": float(p), "n_seeds": len(seeds),
                }

    out = {"dataset": args.dataset, "split": args.split, "seeds": args.seeds,
           "fusions": args.fusions, "runs": records, "summary": summary,
           "significance_gca_vs_baselines": sig}

    out_dir = ROOT / "experiments" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"ablation_{args.dataset}_{args.split}.json"
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=2)

    # readable table (ASCII-only for cross-platform console safety)
    print("\n================ FUSION ABLATION (mean +/- std) ================")
    print(f"{'fusion':16s} {'AUROC':>18s} {'AUPR':>18s}")
    for fusion in args.fusions:
        s = summary[fusion]
        print(f"{fusion:16s} {s['auroc_mean']:.4f}+/-{s['auroc_std']:.4f}   "
              f"{s['aupr_mean']:.4f}+/-{s['aupr_std']:.4f}")
    if sig:
        print("\nGCA vs baselines (paired t-test on AUPR):")
        for k, v in sig.items():
            star = "*" if v["p_value"] < 0.05 else " "
            print(f"  {k:24s} dAUPR {v['aupr_delta']:+.4f}  p={v['p_value']:.4f} {star}")
    print(f"\nsaved -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
