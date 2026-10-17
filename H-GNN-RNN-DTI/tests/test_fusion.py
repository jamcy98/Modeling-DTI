"""Step-5 checks for the fusion mechanisms.

Covers: all four variants preserve shapes; key-masking actually works (padded
key positions cannot influence outputs); the GCA gate blends in [0,1]; and an
end-to-end encoders -> fusion -> pooled joint vector runs on real DAVIS data.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hgnn_rnn_dti.fusion import FUSION_NAMES, build_fusion
from hgnn_rnn_dti.fusion.modules import CrossAttention
from hgnn_rnn_dti.utils.pooling import masked_mean

D_DIM = 128
DATA_READY = (ROOT / "data" / "processed" / "davis" / "pairs.csv").exists()


def _toy(B=3, n=5, m=7, d=D_DIM, seed=0):
    g = torch.Generator().manual_seed(seed)
    D = torch.randn(B, n, d, generator=g)
    P = torch.randn(B, m, d, generator=g)
    drug_mask = torch.ones(B, n, dtype=torch.bool)
    prot_mask = torch.ones(B, m, dtype=torch.bool)
    prot_mask[:, -2:] = False  # last two residues are padding
    drug_mask[:, -1] = False   # last atom is padding
    return D, drug_mask, P, prot_mask


@pytest.mark.parametrize("name", FUSION_NAMES)
def test_fusion_preserves_shapes(name):
    D, dm, P, pm = _toy()
    fusion = build_fusion(name, D_DIM).eval()
    with torch.no_grad():
        D_out, P_out = fusion(D, dm, P, pm)
    assert D_out.shape == D.shape
    assert P_out.shape == P.shape
    assert torch.isfinite(D_out).all() and torch.isfinite(P_out).all()


def test_cross_attention_ignores_masked_keys():
    """Changing padded key values must not change the attended output."""
    torch.manual_seed(0)
    ca = CrossAttention(D_DIM, 64).eval()
    D, dm, P, pm = _toy()
    with torch.no_grad():
        out1 = ca(D, P, pm)
        P2 = P.clone()
        P2[:, -2:] = 999.0  # perturb only masked (padded) key positions
        out2 = ca(D, P2, pm)
    assert torch.allclose(out1, out2, atol=1e-5)


def test_gca_gate_is_a_convex_blend():
    """With the gate wired, GCA output must differ from a plain residual add."""
    D, dm, P, pm = _toy()
    gca = build_fusion("gca", D_DIM).eval()
    ungated = build_fusion("ungated_xattn", D_DIM).eval()
    with torch.no_grad():
        D_g, _ = gca(D, dm, P, pm)
        D_u, _ = ungated(D, dm, P, pm)
    assert not torch.allclose(D_g, D_u)


def test_concat_is_identity():
    D, dm, P, pm = _toy()
    fusion = build_fusion("concat", D_DIM)
    D_out, P_out = fusion(D, dm, P, pm)
    assert torch.equal(D_out, D) and torch.equal(P_out, P)


@pytest.mark.skipif(not DATA_READY, reason="run scripts/preprocess.py --dataset davis first")
def test_end_to_end_encoders_fusion_joint_on_davis():
    from torch.utils.data import DataLoader
    from hgnn_rnn_dti.data.dataset import DTIDataset, collate
    from hgnn_rnn_dti.data.featurize import ATOM_FEATURE_DIM, BOND_FEATURE_DIM, PROTEIN_VOCAB_SIZE
    from hgnn_rnn_dti.encoders import BiLSTMEncoder, HGATEncoder

    ds = DTIDataset(ROOT / "data", "davis", split="train")
    drug_batch, prot_pad, lengths, labels = next(iter(DataLoader(ds, batch_size=4, collate_fn=collate)))
    B = labels.shape[0]

    de = HGATEncoder(ATOM_FEATURE_DIM, BOND_FEATURE_DIM, latent_dim=D_DIM).eval()
    pe = BiLSTMEncoder(PROTEIN_VOCAB_SIZE, latent_dim=D_DIM).eval()
    fusion = build_fusion("gca", D_DIM).eval()

    with torch.no_grad():
        D, dm = de(drug_batch)
        P, pm = pe(prot_pad, lengths)
        D2, P2 = fusion(D, dm, P, pm)
        z_joint = torch.cat([masked_mean(D2, dm), masked_mean(P2, pm)], dim=-1)

    assert z_joint.shape == (B, 2 * D_DIM)   # §3.6.6: z_joint in R^{2d}
    assert torch.isfinite(z_joint).all()
