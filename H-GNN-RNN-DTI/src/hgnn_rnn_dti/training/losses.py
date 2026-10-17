"""Losses (roadmap step 7). Focal loss is the primary imbalance-aware objective
for Objective 1 (DAVIS is ~4% positive); BCE and MSE are alternatives.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """Binary focal loss on logits (Lin et al., 2017).

    gamma down-weights easy examples; alpha balances the positive class.
    """

    def __init__(self, gamma: float = 2.0, alpha: float | None = 0.25):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        p = torch.sigmoid(logits)
        p_t = p * targets + (1 - p) * (1 - targets)
        loss = (1 - p_t) ** self.gamma * bce
        if self.alpha is not None:
            a_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
            loss = a_t * loss
        return loss.mean()


def build_loss(cfg: dict) -> nn.Module:
    task = cfg.get("task", "classification")
    name = cfg["train"].get("loss", "focal")
    if task == "regression" or name == "mse":
        return nn.MSELoss()
    if name == "bce":
        return nn.BCEWithLogitsLoss()
    if name == "focal":
        return FocalLoss(
            gamma=cfg["train"].get("focal_gamma", 2.0),
            alpha=cfg["train"].get("focal_alpha", 0.25),
        )
    raise ValueError(f"Unknown loss '{name}'")
