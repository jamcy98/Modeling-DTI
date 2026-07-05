"""
Loss functions for H-GNN-RNN-DTI.

FocalLoss : for DTI binary classification (handles class imbalance)
DTALoss   : MSE for binding affinity regression
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Focal Loss for binary classification.
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25, reduction: str = 'mean'):
        super().__init__()
        self.gamma     = gamma
        self.alpha     = alpha
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # logits: (B, 2) or (B,)  |  targets: (B,) int64
        if logits.dim() == 2:
            probs = F.softmax(logits, dim=-1)
            p_t   = probs[torch.arange(len(targets)), targets.long()]
            alpha_t = torch.where(targets == 1,
                                  torch.tensor(self.alpha, device=logits.device),
                                  torch.tensor(1 - self.alpha, device=logits.device))
        else:
            probs = torch.sigmoid(logits)
            p_t   = torch.where(targets == 1, probs, 1 - probs)
            alpha_t = torch.where(targets == 1,
                                  torch.tensor(self.alpha, device=logits.device),
                                  torch.tensor(1 - self.alpha, device=logits.device))

        loss = -alpha_t * (1 - p_t) ** self.gamma * torch.log(p_t.clamp(min=1e-8))

        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        return loss


class WeightedBCELoss(nn.Module):
    """
    Weighted Binary Cross-Entropy for class-imbalanced DTI data.
    pos_weight: weight applied to positive class (e.g., 5.0 for 1:5 ratio).
    """

    def __init__(self, pos_weight: float = 1.0):
        super().__init__()
        self.pos_weight = pos_weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        if logits.dim() == 2:
            # Convert (B, 2) class logits to binary logit: log(p1) - log(p0)
            logits = logits[:, 1] - logits[:, 0]
        pw = torch.tensor(self.pos_weight, device=logits.device, dtype=torch.float)
        return F.binary_cross_entropy_with_logits(
            logits, targets.float(), pos_weight=pw)


class DTALoss(nn.Module):
    """MSE loss for binding affinity regression with optional clamp."""

    def __init__(self, reduction: str = 'mean'):
        super().__init__()
        self.mse = nn.MSELoss(reduction=reduction)

    def forward(self, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        return self.mse(preds.squeeze(-1), targets.float())
