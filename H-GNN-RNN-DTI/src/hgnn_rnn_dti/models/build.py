"""Construct the model from a config dict (roadmap step 6).

Encoder input dims come from the featurizer constants (the single source of
truth set in step 2), so the model always matches the data.
"""
from __future__ import annotations

from ..data.featurize import ATOM_FEATURE_DIM, BOND_FEATURE_DIM, PROTEIN_VOCAB_SIZE
from ..encoders import BiLSTMEncoder, HGATEncoder
from ..fusion import build_fusion
from .model import HGNNRNNDTI


def build_model(cfg: dict) -> HGNNRNNDTI:
    m = cfg["model"]
    latent = m["latent_dim"]
    dropout = m["head"].get("dropout", 0.2)

    drug_encoder = HGATEncoder(
        atom_dim=ATOM_FEATURE_DIM,
        bond_dim=BOND_FEATURE_DIM,
        hidden=latent,
        latent_dim=latent,
        heads=m["drug_encoder"]["heads"],
        layers=m["drug_encoder"]["layers"],
        dropout=dropout,
    )
    protein_encoder = BiLSTMEncoder(
        vocab_size=PROTEIN_VOCAB_SIZE,
        embed_dim=latent,
        hidden=m["protein_encoder"]["hidden"],
        latent_dim=latent,
        layers=m["protein_encoder"]["layers"],
        dropout=dropout,
    )
    fusion = build_fusion(m["fusion"]["type"], latent, m["fusion"].get("attention_dim", latent))

    return HGNNRNNDTI(
        drug_encoder, protein_encoder, fusion,
        latent_dim=latent,
        head_hidden=m["head"]["hidden"],
        dropout=dropout,
        pooling=m.get("pooling", "masked_mean"),
        task=cfg.get("task", "classification"),
    )
