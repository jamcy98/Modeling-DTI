"""
Gated Cross-Attention fusion module for H-GNN-RNN-DTI.

drug_repr   (B, H) → query
protein_repr(B, H) → key / value

Output: fused representation (B, H)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class GatedCrossAttention(nn.Module):
    """
    Bidirectional gated cross-attention:
      1. Drug attends over protein  → drug_ctx
      2. Protein attends over drug  → prot_ctx
      3. Gating: g = sigmoid(W [drug; prot]) controls blend
      4. Fused = g * drug_ctx + (1-g) * prot_ctx + residual
    """

    def __init__(self, dim: int, heads: int = 8, dropout: float = 0.1):
        super().__init__()
        assert dim % heads == 0
        self.dim     = dim
        self.heads   = heads
        self.head_d  = dim // heads
        self.scale   = self.head_d ** -0.5

        # Projections for drug attending to protein
        self.Wq_d  = nn.Linear(dim, dim)
        self.Wk_d  = nn.Linear(dim, dim)
        self.Wv_d  = nn.Linear(dim, dim)

        # Projections for protein attending to drug
        self.Wq_p  = nn.Linear(dim, dim)
        self.Wk_p  = nn.Linear(dim, dim)
        self.Wv_p  = nn.Linear(dim, dim)

        # Gate
        self.gate  = nn.Linear(dim * 2, dim)

        # Output
        self.out_proj = nn.Linear(dim * 2, dim)
        self.norm     = nn.LayerNorm(dim)
        self.drop     = nn.Dropout(dropout)

    def _attn(self, q, k, v):
        # q, k, v: (B, H, 1, d) — single-vector cross attention
        score = torch.matmul(q, k.transpose(-2, -1)) * self.scale  # (B, H, 1, 1)
        w     = torch.softmax(score, dim=-1)
        return torch.matmul(w, v)  # (B, H, 1, d)

    def _split_heads(self, x):
        B = x.size(0)
        return x.view(B, self.heads, 1, self.head_d)

    def _merge_heads(self, x):
        B = x.size(0)
        return x.view(B, self.dim)

    def forward(self, drug, protein, return_gate=False):
        # drug, protein: (B, dim)
        # Drug → Protein cross-attention
        q_d = self._split_heads(self.Wq_d(drug))
        k_d = self._split_heads(self.Wk_d(protein))
        v_d = self._split_heads(self.Wv_d(protein))
        drug_ctx = self._merge_heads(self._attn(q_d, k_d, v_d))  # (B, dim)

        # Protein → Drug cross-attention
        q_p = self._split_heads(self.Wq_p(protein))
        k_p = self._split_heads(self.Wk_p(drug))
        v_p = self._split_heads(self.Wv_p(drug))
        prot_ctx = self._merge_heads(self._attn(q_p, k_p, v_p))  # (B, dim)

        # Gating: g→1 means drug context dominates; g→0 means protein context dominates
        g       = torch.sigmoid(self.gate(torch.cat([drug, protein], dim=-1)))  # (B, dim)
        blended = g * drug_ctx + (1 - g) * prot_ctx                             # (B, dim)

        # Output projection with residual
        fused  = self.out_proj(torch.cat([blended, drug + protein], dim=-1))  # (B, dim)
        result = self.norm(self.drop(fused) + drug + protein)
        if return_gate:
            return result, g.detach()
        return result
