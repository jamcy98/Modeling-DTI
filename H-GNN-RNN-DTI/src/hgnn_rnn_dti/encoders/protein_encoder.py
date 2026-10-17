"""Bi-LSTM protein encoder (roadmap step 4, proposal §3.6.3).

Embeds amino-acid tokens and runs a multi-layer bidirectional LSTM, producing
contextual residue-level states p_t = [forward_t || backward_t] projected to the
common latent dimension. Residue-level states are RETAINED (not pooled) for the
bidirectional Gated Cross-Attention with drug atoms. Padding is handled via
pack_padded_sequence so padded positions never contribute.

Objective 1 reference config (C1): a learned embedding over the 22-token
amino-acid vocabulary. Pretrained ESM-2 / secondary-structure / physicochemical
enrichment is Objective 2 and is not applied here.
"""
from __future__ import annotations

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from ..data.featurize import PAD_ID, PROTEIN_VOCAB_SIZE


class BiLSTMEncoder(nn.Module):
    def __init__(
        self,
        vocab_size: int = PROTEIN_VOCAB_SIZE,
        embed_dim: int = 128,
        hidden: int = 128,
        latent_dim: int = 128,
        layers: int = 2,
        dropout: float = 0.2,
        pad_idx: int = PAD_ID,
    ):
        super().__init__()
        self.pad_idx = pad_idx
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(
            embed_dim, hidden, num_layers=layers, batch_first=True,
            bidirectional=True, dropout=dropout if layers > 1 else 0.0,
        )
        self.out_proj = nn.Linear(2 * hidden, latent_dim)

    def forward(self, tokens: torch.Tensor, lengths: torch.Tensor):
        """tokens [B, L], lengths [B] -> (P [B, L, latent], mask [B, L])."""
        mask = tokens != self.pad_idx
        emb = self.embedding(tokens)
        packed = pack_padded_sequence(
            emb, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        out, _ = self.lstm(packed)
        out, _ = pad_packed_sequence(
            out, batch_first=True, total_length=tokens.size(1)
        )
        P = self.out_proj(out)  # [B, L, latent]
        return P, mask
