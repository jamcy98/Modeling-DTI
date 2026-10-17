"""Step-4 shape checks: run a real DAVIS batch through both encoders.

Skips if the processed DAVIS artifacts aren't present (run scripts/preprocess.py
first). Verifies the encoders retain atom-/residue-level states at the common
latent dimension, ready for Gated Cross-Attention (step 5).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hgnn_rnn_dti.data.featurize import ATOM_FEATURE_DIM, BOND_FEATURE_DIM, PROTEIN_VOCAB_SIZE

DATA_READY = (ROOT / "data" / "processed" / "davis" / "pairs.csv").exists()
LATENT = 128


@pytest.mark.skipif(not DATA_READY, reason="run scripts/preprocess.py --dataset davis first")
def test_encoders_forward_shapes():
    from torch.utils.data import DataLoader
    from hgnn_rnn_dti.data.dataset import DTIDataset, collate
    from hgnn_rnn_dti.encoders import BiLSTMEncoder, HGATEncoder

    ds = DTIDataset(ROOT / "data", "davis", split="train")
    loader = DataLoader(ds, batch_size=4, shuffle=False, collate_fn=collate)
    drug_batch, prot_pad, lengths, labels = next(iter(loader))
    B = labels.shape[0]

    drug_enc = HGATEncoder(ATOM_FEATURE_DIM, BOND_FEATURE_DIM, latent_dim=LATENT)
    prot_enc = BiLSTMEncoder(PROTEIN_VOCAB_SIZE, latent_dim=LATENT)
    drug_enc.eval(); prot_enc.eval()

    with torch.no_grad():
        D, drug_mask = drug_enc(drug_batch)
        P, prot_mask = prot_enc(prot_pad, lengths)

    # drug: [B, n_max, latent]; mask [B, n_max]
    assert D.shape[0] == B and D.shape[2] == LATENT
    assert drug_mask.shape == (B, D.shape[1])
    # protein: [B, m, latent]; mask [B, m]
    assert P.shape[0] == B and P.shape[2] == LATENT
    assert prot_mask.shape == (B, P.shape[1])
    # masks count real atoms/residues (at least one each)
    assert int(drug_mask.sum()) > 0 and int(prot_mask.sum()) > 0
    # no NaNs
    assert torch.isfinite(D).all() and torch.isfinite(P).all()
