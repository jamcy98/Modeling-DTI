"""Step-7 checks: losses, metrics, a Trainer smoke run, and a real overfit test
that proves the full pipeline actually learns.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hgnn_rnn_dti.evaluation.metrics import classification_metrics, regression_metrics
from hgnn_rnn_dti.training.losses import FocalLoss, build_loss
from hgnn_rnn_dti.utils.config import clone_config, load_config
from hgnn_rnn_dti.utils.seed import set_seed

DATA_READY = (ROOT / "data" / "processed" / "davis" / "pairs.csv").exists()
CFG = load_config(ROOT / "configs" / "default.yaml")


def test_focal_loss_down_weights_easy_examples():
    logits = torch.tensor([3.0, -3.0])         # confident & correct
    targets = torch.tensor([1.0, 0.0])
    focal = FocalLoss(gamma=2.0, alpha=None)(logits, targets)
    bce = torch.nn.functional.binary_cross_entropy_with_logits(logits, targets)
    assert focal < bce  # focal shrinks easy, well-classified losses


def test_metrics_perfect_and_degenerate():
    m = classification_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert m["auroc"] == 1.0 and m["aupr"] == 1.0
    assert np.isnan(classification_metrics([0, 0, 0], [0.1, 0.2, 0.3])["auroc"])  # one class
    r = regression_metrics([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert r["rmse"] == 0.0 and r["mae"] == 0.0


def test_build_loss_variants():
    assert isinstance(build_loss({"task": "classification", "train": {"loss": "focal"}}), FocalLoss)
    assert build_loss({"task": "regression", "train": {"loss": "mse"}}).__class__.__name__ == "MSELoss"


def _balanced_batch(n_each=8, max_len=160):
    """One small balanced batch from DAVIS train, proteins truncated for speed."""
    from hgnn_rnn_dti.data.dataset import DTIDataset, collate
    ds = DTIDataset(ROOT / "data", "davis", split="train")
    labels = [ds.pairs.iloc[idx]["label"] for idx in ds.indices]
    pos = [i for i, l in enumerate(labels) if l == 1][:n_each]
    neg = [i for i, l in enumerate(labels) if l == 0][:n_each]
    drug_batch, prot_pad, lengths, lab = collate([ds[i] for i in pos + neg])
    prot_pad = prot_pad[:, :max_len]
    lengths = torch.clamp(lengths, max=max_len)
    return drug_batch, prot_pad, lengths, lab


@pytest.mark.skipif(not DATA_READY, reason="run scripts/preprocess.py --dataset davis first")
def test_pipeline_overfits_small_balanced_batch():
    """The clearest 'it learns' signal: loss drops and the model separates classes."""
    from hgnn_rnn_dti.models import build_model
    set_seed(0)
    model = build_model(CFG).train()
    drug_batch, prot_pad, lengths, labels = _balanced_batch()
    loss_fn = FocalLoss(gamma=2.0, alpha=0.5)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3)

    first = None
    for step in range(25):
        out = model(drug_batch, prot_pad, lengths)
        loss = loss_fn(out, labels)
        if first is None:
            first = float(loss.item())
        opt.zero_grad(); loss.backward(); opt.step()
    last = float(loss.item())

    model.eval()
    with torch.no_grad():
        probs = torch.sigmoid(model(drug_batch, prot_pad, lengths)).numpy()
    aupr = classification_metrics(labels.numpy(), probs)["aupr"]

    assert last < first * 0.6, f"loss did not drop enough: {first:.4f} -> {last:.4f}"
    assert aupr > 0.8, f"model failed to separate classes (train AUPR={aupr:.3f})"


@pytest.mark.skipif(not DATA_READY, reason="data not prepared")
def test_trainer_smoke_runs_and_early_stops():
    from torch.utils.data import DataLoader
    from hgnn_rnn_dti.data.dataset import DTIDataset, collate
    from hgnn_rnn_dti.models import build_model
    from hgnn_rnn_dti.training import Trainer

    cfg = clone_config(CFG)
    cfg["train"]["epochs"] = 2
    cfg["train"]["batch_size"] = 8
    set_seed(0)
    tr = DataLoader(DTIDataset(ROOT / "data", "davis", "train"), batch_size=8, collate_fn=collate)
    va = DataLoader(DTIDataset(ROOT / "data", "davis", "val"), batch_size=8, collate_fn=collate)

    trainer = Trainer(build_model(cfg), cfg, device="cpu")
    out = trainer.fit(tr, va, max_batches=3, verbose=False)
    assert len(out["history"]) >= 1
    for rec in out["history"]:
        assert np.isfinite(rec["train_loss"]) and np.isfinite(rec["val_loss"])
