"""Roadmap step 7: train one model configuration on a dataset.

Usage:
    python scripts/train.py --dataset davis --fusion gca --seed 42
    python scripts/train.py --dataset davis --fusion gca --epochs 3 --max-batches 20  # quick

Saves best-val metrics + test metrics + history to experiments/results/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch
from torch.utils.data import DataLoader

from hgnn_rnn_dti.data.dataset import DTIDataset, collate
from hgnn_rnn_dti.models import build_model
from hgnn_rnn_dti.training import Trainer
from hgnn_rnn_dti.utils.config import clone_config, load_config
from hgnn_rnn_dti.utils.seed import set_seed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="davis")
    ap.add_argument("--root", default=str(ROOT / "data"))
    ap.add_argument("--config", default=str(ROOT / "configs" / "default.yaml"))
    ap.add_argument("--fusion", default=None, help="override fusion type")
    ap.add_argument("--split", default="S1")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--max-batches", type=int, default=None, help="cap batches/epoch (quick runs)")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    cfg = clone_config(load_config(args.config))
    if args.fusion:
        cfg["model"]["fusion"]["type"] = args.fusion
    if args.epochs is not None:
        cfg["train"]["epochs"] = args.epochs
    if args.batch_size is not None:
        cfg["train"]["batch_size"] = args.batch_size
    seed = args.seed if args.seed is not None else cfg.get("seed", 42)
    set_seed(seed)

    bs = cfg["train"]["batch_size"]
    loaders = {}
    for split in ["train", "val", "test"]:
        ds = DTIDataset(args.root, args.dataset, split=split, split_name=args.split, seed=cfg["split"].get("seed", 42))
        loaders[split] = DataLoader(ds, batch_size=bs, shuffle=(split == "train"), collate_fn=collate)
        print(f"{split}: {len(ds)} pairs")

    model = build_model(cfg)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"model: fusion={cfg['model']['fusion']['type']} params={n_params:,} device={args.device}")

    trainer = Trainer(model, cfg, device=args.device)
    t0 = time.time()
    fit_out = trainer.fit(loaders["train"], loaders["val"], max_batches=args.max_batches)
    test_metrics = trainer.evaluate(loaders["test"], max_batches=args.max_batches)
    elapsed = time.time() - t0

    result = {
        "dataset": args.dataset, "split": args.split, "seed": seed,
        "fusion": cfg["model"]["fusion"]["type"], "task": cfg["task"],
        "best_val": {k: v for k, v in fit_out.items() if k != "history"},
        "test": test_metrics, "n_params": n_params,
        "epochs_run": len(fit_out["history"]), "elapsed_sec": round(elapsed, 1),
        "max_batches": args.max_batches,
    }
    out_dir = ROOT / "experiments" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.dataset}_{args.split}_{cfg['model']['fusion']['type']}_seed{seed}.json"
    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=2)

    print("\n=== TEST METRICS ===")
    print(json.dumps(test_metrics, indent=2))
    print(f"saved -> {out_path}  ({elapsed:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
