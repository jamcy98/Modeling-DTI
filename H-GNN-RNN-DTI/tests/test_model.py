"""Step-6 checks: assemble the full model from config and run it on DAVIS.

Covers: construction from default.yaml; forward produces [B] outputs; every
fusion variant plugs in; both classification (logits -> probs in [0,1]) and
regression tasks work; a loss backpropagates (the model is trainable).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hgnn_rnn_dti.fusion import FUSION_NAMES
from hgnn_rnn_dti.models import build_model
from hgnn_rnn_dti.utils.config import clone_config, load_config

DATA_READY = (ROOT / "data" / "processed" / "davis" / "pairs.csv").exists()
CFG = load_config(ROOT / "configs" / "default.yaml")


def _batch(bs=4):
    from torch.utils.data import DataLoader
    from hgnn_rnn_dti.data.dataset import DTIDataset, collate
    ds = DTIDataset(ROOT / "data", "davis", split="train")
    return next(iter(DataLoader(ds, batch_size=bs, collate_fn=collate)))


@pytest.mark.skipif(not DATA_READY, reason="run scripts/preprocess.py --dataset davis first")
def test_build_and_forward_classification():
    drug_batch, prot_pad, lengths, labels = _batch()
    model = build_model(CFG).eval()
    with torch.no_grad():
        logits = model(drug_batch, prot_pad, lengths)
        probs = model.predict_proba(drug_batch, prot_pad, lengths)
    assert logits.shape == (labels.shape[0],)
    assert torch.isfinite(logits).all()
    assert (probs >= 0).all() and (probs <= 1).all()


@pytest.mark.skipif(not DATA_READY, reason="data not prepared")
@pytest.mark.parametrize("fusion_name", FUSION_NAMES)
def test_all_fusion_variants_assemble(fusion_name):
    cfg = clone_config(CFG)
    cfg["model"]["fusion"]["type"] = fusion_name
    drug_batch, prot_pad, lengths, labels = _batch()
    model = build_model(cfg).eval()
    with torch.no_grad():
        out = model(drug_batch, prot_pad, lengths)
    assert out.shape == (labels.shape[0],) and torch.isfinite(out).all()


@pytest.mark.skipif(not DATA_READY, reason="data not prepared")
def test_regression_task():
    cfg = clone_config(CFG)
    cfg["task"] = "regression"
    drug_batch, prot_pad, lengths, labels = _batch()
    model = build_model(cfg).eval()
    with torch.no_grad():
        out = model(drug_batch, prot_pad, lengths)
    assert out.shape == (labels.shape[0],) and torch.isfinite(out).all()


@pytest.mark.skipif(not DATA_READY, reason="data not prepared")
def test_backward_step_updates_params():
    drug_batch, prot_pad, lengths, labels = _batch()
    model = build_model(CFG).train()
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    logits = model(drug_batch, prot_pad, lengths)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, labels)
    opt.zero_grad(); loss.backward(); opt.step()
    assert torch.isfinite(loss)
    grads = [p.grad for p in model.parameters() if p.grad is not None]
    assert len(grads) > 0 and all(torch.isfinite(g).all() for g in grads)
