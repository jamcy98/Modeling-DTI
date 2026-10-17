"""Cross-modal fusion mechanisms (roadmap step 5, proposal §3.6.4-3.6.5, §3.9.1).

All fusion modules share ONE interface so they are swappable in the ablation
that provides the Objective 1 / RQ1 evidence:

    forward(D, drug_mask, P, prot_mask) -> (D_out, P_out)

where D [B, n, d] are atom-level drug states, P [B, m, d] are residue-level
protein states, masks are [B, *] booleans (True = real), and the outputs keep
the same shapes (cross-modal-enriched states), ready for pooling (step 6).

The four variants isolate the contribution of each design element:
  - concat         : no cross-modal interaction (static-concatenation baseline)
  - flat_gate      : global cross-modal gating only, no token-level attention
                     (MGNDTI-style flat gating)
  - ungated_xattn  : bidirectional cross-attention WITHOUT the gate
  - gca            : bidirectional GATED cross-attention (the proposed mechanism)
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..utils.pooling import masked_mean


class CrossAttention(nn.Module):
    """Single-head scaled dot-product cross-attention with key masking.

    Queries from one modality attend over the (valid) keys/values of the other.
    Q, K project to `attn_dim` (d_k); V projects back to `dim` so the attended
    output lives in the same space as the original states (needed for gating).
    """

    def __init__(self, dim: int, attn_dim: int):
        super().__init__()
        self.q = nn.Linear(dim, attn_dim, bias=False)
        self.k = nn.Linear(dim, attn_dim, bias=False)
        self.v = nn.Linear(dim, dim, bias=False)
        self.scale = attn_dim ** -0.5

    def forward(self, query_states, key_states, key_mask, return_attn=False):
        Q = self.q(query_states)                 # [B, nq, dk]
        K = self.k(key_states)                   # [B, nk, dk]
        V = self.v(key_states)                   # [B, nk, d]
        scores = torch.matmul(Q, K.transpose(1, 2)) * self.scale  # [B, nq, nk]
        scores = scores.masked_fill(~key_mask.unsqueeze(1), float("-inf"))
        attn = torch.softmax(scores, dim=-1)
        attn = torch.nan_to_num(attn)            # guard: query over all-masked keys
        out = torch.matmul(attn, V)              # [B, nq, d]
        return (out, attn) if return_attn else out


class GatedCrossAttentionFusion(nn.Module):
    """Bidirectional cross-attention with an optional learned sigmoid gate.

    gated=True  -> GCA (proposed): D' = G_D ⊙ D̃ + (1-G_D) ⊙ D
    gated=False -> ungated ablation: D' = D + D̃ (residual add)
    """

    def __init__(self, dim: int, attn_dim: int = 128, gated: bool = True):
        super().__init__()
        self.gated = gated
        self.drug_to_protein = CrossAttention(dim, attn_dim)  # drug Q, protein K/V
        self.protein_to_drug = CrossAttention(dim, attn_dim)  # protein Q, drug K/V
        if gated:
            self.gate_d = nn.Linear(2 * dim, dim)
            self.gate_p = nn.Linear(2 * dim, dim)

    def forward(self, D, drug_mask, P, prot_mask):
        D_tilde = self.drug_to_protein(D, P, prot_mask)   # [B, n, d]
        P_tilde = self.protein_to_drug(P, D, drug_mask)   # [B, m, d]
        if self.gated:
            g_d = torch.sigmoid(self.gate_d(torch.cat([D, D_tilde], dim=-1)))
            g_p = torch.sigmoid(self.gate_p(torch.cat([P, P_tilde], dim=-1)))
            D_out = g_d * D_tilde + (1 - g_d) * D
            P_out = g_p * P_tilde + (1 - g_p) * P
        else:
            D_out = D + D_tilde
            P_out = P + P_tilde
        return D_out, P_out


class IdentityConcatFusion(nn.Module):
    """No cross-modal interaction. The two modalities are only combined later,
    at the pooling/concatenation step (static-concatenation baseline)."""

    def forward(self, D, drug_mask, P, prot_mask):
        return D, P


class FlatGateFusion(nn.Module):
    """Global (flat) cross-modal gating, no token-level attention.

    A gate derived from the two pooled modality vectors rescales each modality's
    states — cross-modal signal enters only at the global level, contrasting
    with GCA's token-level interaction (MGNDTI-style flat gating)."""

    def __init__(self, dim: int):
        super().__init__()
        self.gate_d = nn.Linear(2 * dim, dim)
        self.gate_p = nn.Linear(2 * dim, dim)

    def forward(self, D, drug_mask, P, prot_mask):
        g_drug = masked_mean(D, drug_mask)                # [B, d]
        g_prot = masked_mean(P, prot_mask)                # [B, d]
        z = torch.cat([g_drug, g_prot], dim=-1)           # [B, 2d]
        gate_d = torch.sigmoid(self.gate_d(z)).unsqueeze(1)  # [B, 1, d]
        gate_p = torch.sigmoid(self.gate_p(z)).unsqueeze(1)
        return D * gate_d, P * gate_p
