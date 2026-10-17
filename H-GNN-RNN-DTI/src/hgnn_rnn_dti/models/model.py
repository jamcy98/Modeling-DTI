"""Full H-GNN-RNN-DTI/DTA model (roadmap step 6, proposal §3.6).

Wiring: H-GAT (drug) + Bi-LSTM (protein) -> bidirectional fusion -> masked
pooling of each modality -> concatenated joint vector z_joint ∈ ℝ^{2d} ->
task-specific prediction head.

Deliberately NO second post-pooling fusion gate (proposal §3.6.7): keeping the
only cross-modal interaction inside the swappable `fusion` module is what lets
the fusion ablation isolate the GCA contribution.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from ..utils.pooling import AttentionPool, masked_mean
from .heads import PredictionHead


class HGNNRNNDTI(nn.Module):
    def __init__(self, drug_encoder, protein_encoder, fusion, *,
                 latent_dim: int, head_hidden: list[int], dropout: float = 0.2,
                 pooling: str = "masked_mean", task: str = "classification"):
        super().__init__()
        self.drug_encoder = drug_encoder
        self.protein_encoder = protein_encoder
        self.fusion = fusion
        self.task = task
        self.pooling = pooling
        if pooling == "attention":
            self.drug_pool = AttentionPool(latent_dim)
            self.protein_pool = AttentionPool(latent_dim)
        elif pooling != "masked_mean":
            raise ValueError(f"Unknown pooling '{pooling}'")
        self.head = PredictionHead(2 * latent_dim, head_hidden, dropout, task)

    def _pool(self, x, mask, which):
        if self.pooling == "masked_mean":
            return masked_mean(x, mask)
        return (self.drug_pool if which == "drug" else self.protein_pool)(x, mask)

    def forward(self, drug_batch, prot_tokens, prot_lengths) -> torch.Tensor:
        D, drug_mask = self.drug_encoder(drug_batch)          # [B, n, d], [B, n]
        P, prot_mask = self.protein_encoder(prot_tokens, prot_lengths)  # [B, m, d], [B, m]
        D2, P2 = self.fusion(D, drug_mask, P, prot_mask)       # cross-modal-enriched
        z_drug = self._pool(D2, drug_mask, "drug")             # [B, d]
        z_prot = self._pool(P2, prot_mask, "protein")          # [B, d]
        z_joint = torch.cat([z_drug, z_prot], dim=-1)          # [B, 2d]
        return self.head(z_joint)                              # [B]

    @torch.no_grad()
    def predict_proba(self, drug_batch, prot_tokens, prot_lengths) -> torch.Tensor:
        assert self.task == "classification"
        return torch.sigmoid(self.forward(drug_batch, prot_tokens, prot_lengths))
