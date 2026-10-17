"""Reusable single-experiment runner (used by train.py and run_ablation.py)."""
from __future__ import annotations

import time

from torch.utils.data import DataLoader

from ..data.dataset import DTIDataset, make_collate
from ..models import build_model
from ..utils.seed import set_seed
from .trainer import Trainer


def run_experiment(
    cfg: dict,
    data_root,
    dataset: str,
    split: str = "S1",
    seed: int = 42,
    device: str = "cpu",
    max_batches: int | None = None,
    max_protein_length: int | None = None,
    verbose: bool = True,
) -> dict:
    """Train + select on val + evaluate on test for one config/seed."""
    set_seed(seed)
    collate_fn = make_collate(max_protein_length)
    bs = cfg["train"]["batch_size"]
    split_seed = cfg["split"].get("seed", 42)

    loaders = {
        s: DataLoader(
            DTIDataset(data_root, dataset, split=s, split_name=split, seed=split_seed),
            batch_size=bs, shuffle=(s == "train"), collate_fn=collate_fn,
        )
        for s in ["train", "val", "test"]
    }

    model = build_model(cfg)
    trainer = Trainer(model, cfg, device=device)
    t0 = time.time()
    fit_out = trainer.fit(loaders["train"], loaders["val"], max_batches=max_batches, verbose=verbose)
    test = trainer.evaluate(loaders["test"], max_batches=max_batches)
    return {
        "best_val": {k: v for k, v in fit_out.items() if k != "history"},
        "test": test,
        "epochs_run": len(fit_out["history"]),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_params": sum(p.numel() for p in model.parameters()),
        "history": fit_out["history"],
    }
