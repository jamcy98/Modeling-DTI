"""
Simple Concatenation GNN-RNN baseline for ablation (Objective 1).

Identical to H-GNN-RNN-DTI but replaces GatedCrossAttention with
a plain concatenation + MLP fusion. Isolates the contribution of
the cross-attention layer.
"""

import torch
import torch.nn as nn

from .encoders import DrugEncoder, ProteinEncoder


class ConcatGNN_RNN_DTI(nn.Module):
    """
    Ablation baseline: drug_repr || protein_repr → MLP → task head.

    Args match HGNN_RNN_DTI exactly so the same train.py config works.
    """

    def __init__(
        self,
        task:          str   = 'dti',
        node_feat_dim: int   = 65,
        esm_dim:       int   = 320,
        hidden_dim:    int   = 256,
        gat_layers:    int   = 3,
        gat_heads:     int   = 8,
        gru_layers:    int   = 2,
        chemberta_dim: int   = 768,
        fusion_heads:  int   = 8,   # unused — kept for API compatibility
        dropout:       float = 0.1,
    ):
        super().__init__()
        assert task in ('dti', 'dta')
        self.task = task

        self.prot_input_proj = nn.Linear(esm_dim, esm_dim) if esm_dim == 320 else \
                               nn.Linear(esm_dim, 320)
        self.prot_esm_dim = 320

        self.drug_encoder = DrugEncoder(
            node_feat_dim=node_feat_dim,
            hidden_dim=hidden_dim,
            n_layers=gat_layers,
            heads=gat_heads,
            chemberta_dim=chemberta_dim,
            dropout=dropout,
        )
        self.protein_encoder = ProteinEncoder(
            esm_dim=320,
            hidden_dim=hidden_dim,
            n_layers=gru_layers,
            dropout=dropout,
        )

        # Simple concat fusion: [drug || protein] → hidden_dim
        self.fusion_mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        out_dim = 2 if task == 'dti' else 1
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_dim),
        )

    def forward(self, drug_graph, protein_emb):
        drug_repr = self.drug_encoder(drug_graph)

        last_dim = protein_emb.shape[-1]
        if last_dim == self.protein_encoder.hidden_dim and protein_emb.dim() == 2:
            protein_repr = protein_emb
        else:
            if last_dim != 320:
                protein_emb = self.prot_input_proj(protein_emb)
            protein_repr = self.protein_encoder(protein_emb)

        fused = self.fusion_mlp(torch.cat([drug_repr, protein_repr], dim=-1))
        return self.head(fused)
