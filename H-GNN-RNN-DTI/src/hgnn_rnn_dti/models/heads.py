"""Prediction head (roadmap step 6, proposal §3.6.7).

A task-specific MLP on the joint representation z_joint ∈ ℝ^{2d}:
  - classification: emits a single raw LOGIT (pair with BCEWithLogitsLoss /
    focal loss; apply sigmoid only at inference for a probability);
  - regression: emits a single continuous value (binding affinity).
"""
from __future__ import annotations

import torch
import torch.nn as nn


class PredictionHead(nn.Module):
    def __init__(self, in_dim: int, hidden: list[int], dropout: float = 0.2,
                 task: str = "classification"):
        super().__init__()
        self.task = task
        layers: list[nn.Module] = []
        d = in_dim
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU(), nn.Dropout(dropout)]
            d = h
        layers += [nn.Linear(d, 1)]
        self.net = nn.Sequential(*layers)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z).squeeze(-1)  # [B] logit (classification) or value (regression)
