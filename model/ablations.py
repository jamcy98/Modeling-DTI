"""
Ablation models for H-GNN-RNN-DTI (Objective 1).

GNN_Only  : Drug encoder (3-layer GAT + ChemBERTa) only — no protein, no fusion.
            Tests how much the drug molecular structure alone contributes.

RNN_Only  : Protein encoder (BiGRU) only — no drug graph, no fusion.
            Tests how much the protein sequence alone contributes.

Both share the same forward signature as HGNN_RNN_DTI so train.py works unchanged:
    forward(drug_graph, protein_emb) → logits
Each model simply ignores the argument it does not use.
"""

import torch
import torch.nn as nn

from .encoders import DrugEncoder, ProteinEncoder


class GNN_Only(nn.Module):
    """
    Drug-encoder-only ablation.
    Predicts DTI/DTA from drug molecular graph alone; protein_emb is ignored.
    """

    def __init__(
        self,
        task:          str   = 'dti',
        node_feat_dim: int   = 65,
        esm_dim:       int   = 320,   # kept for API compatibility — unused
        hidden_dim:    int   = 256,
        gat_layers:    int   = 3,
        gat_heads:     int   = 8,
        gru_layers:    int   = 2,     # kept for API compatibility — unused
        chemberta_dim: int   = 768,
        fusion_heads:  int   = 8,     # kept for API compatibility — unused
        dropout:       float = 0.1,
    ):
        super().__init__()
        assert task in ('dti', 'dta')
        self.task = task

        self.drug_encoder = DrugEncoder(
            node_feat_dim=node_feat_dim,
            hidden_dim=hidden_dim,
            n_layers=gat_layers,
            heads=gat_heads,
            chemberta_dim=chemberta_dim,
            dropout=dropout,
        )

        out_dim = 2 if task == 'dti' else 1
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_dim),
        )

        # Dummy attribute so train.py protein-cache logic can check
        self.protein_encoder = None

    def forward(self, drug_graph, protein_emb):
        drug_repr = self.drug_encoder(drug_graph)   # (B, H)
        return self.head(drug_repr)                 # protein_emb ignored


class RNN_Only(nn.Module):
    """
    Protein-encoder-only ablation.
    Predicts DTI/DTA from protein ESM-2 sequence alone; drug_graph is ignored.
    """

    def __init__(
        self,
        task:          str   = 'dti',
        node_feat_dim: int   = 65,    # kept for API compatibility — unused
        esm_dim:       int   = 320,
        hidden_dim:    int   = 256,
        gat_layers:    int   = 3,     # kept for API compatibility — unused
        gat_heads:     int   = 8,     # kept for API compatibility — unused
        gru_layers:    int   = 2,
        chemberta_dim: int   = 768,   # kept for API compatibility — unused
        fusion_heads:  int   = 8,     # kept for API compatibility — unused
        dropout:       float = 0.1,
    ):
        super().__init__()
        assert task in ('dti', 'dta')
        self.task = task

        self.prot_input_proj = nn.Linear(esm_dim, esm_dim) if esm_dim == 320 else \
                               nn.Linear(esm_dim, 320)

        self.protein_encoder = ProteinEncoder(
            esm_dim=320,
            hidden_dim=hidden_dim,
            n_layers=gru_layers,
            dropout=dropout,
        )

        out_dim = 2 if task == 'dti' else 1
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_dim),
        )

    def forward(self, drug_graph, protein_emb):
        # drug_graph is ignored

        last_dim = protein_emb.shape[-1]

        if last_dim == self.protein_encoder.hidden_dim and protein_emb.dim() == 2:
            # Pre-cached hidden representation
            protein_repr = protein_emb
        else:
            if last_dim != 320:
                protein_emb = self.prot_input_proj(protein_emb)
            protein_repr = self.protein_encoder(protein_emb)   # (B, H)

        return self.head(protein_repr)
