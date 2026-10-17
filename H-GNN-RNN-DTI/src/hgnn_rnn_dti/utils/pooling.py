"""Masked pooling helpers (proposal §3.6.6).

Used to collapse retained atom-/residue-level states into fixed-dimensional
vectors AFTER fusion. Masked mean is the baseline; attention pooling is an
optional alternative evaluated only if validation justifies it.
"""
from __future__ import annotations

import torch
import torch.nn as nn


def masked_mean(x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Mean over valid positions. x [B, L, d], mask [B, L] bool -> [B, d]."""
    m = mask.unsqueeze(-1).to(x.dtype)
    summed = (x * m).sum(dim=1)
    count = m.sum(dim=1).clamp(min=1.0)
    return summed / count


class AttentionPool(nn.Module):
    """Optional learned attention pooling over valid positions."""

    def __init__(self, dim: int):
        super().__init__()
        self.score = nn.Linear(dim, 1)

    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        scores = self.score(x).squeeze(-1)  # [B, L]
        scores = scores.masked_fill(~mask, float("-inf"))
        weights = torch.softmax(scores, dim=1).unsqueeze(-1)  # [B, L, 1]
        weights = torch.nan_to_num(weights)
        return (x * weights).sum(dim=1)  # [B, d]
