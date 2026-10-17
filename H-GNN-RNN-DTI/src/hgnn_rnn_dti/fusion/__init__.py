"""Fusion mechanisms + factory. Swap `name` to run the RQ1 fusion ablation."""
from __future__ import annotations

import torch.nn as nn

from .modules import (
    CrossAttention,
    FlatGateFusion,
    GatedCrossAttentionFusion,
    IdentityConcatFusion,
)

FUSION_NAMES = ["gca", "ungated_xattn", "flat_gate", "concat"]


def build_fusion(name: str, dim: int, attn_dim: int = 128) -> nn.Module:
    """Factory: the single knob the Objective 1 fusion ablation varies."""
    name = name.lower()
    if name == "gca":
        return GatedCrossAttentionFusion(dim, attn_dim, gated=True)
    if name == "ungated_xattn":
        return GatedCrossAttentionFusion(dim, attn_dim, gated=False)
    if name == "flat_gate":
        return FlatGateFusion(dim)
    if name == "concat":
        return IdentityConcatFusion()
    raise ValueError(f"Unknown fusion '{name}'. Options: {FUSION_NAMES}")


__all__ = [
    "build_fusion", "FUSION_NAMES", "CrossAttention",
    "GatedCrossAttentionFusion", "FlatGateFusion", "IdentityConcatFusion",
]
