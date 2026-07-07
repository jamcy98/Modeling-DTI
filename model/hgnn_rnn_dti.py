"""
H-GNN-RNN-DTI: Hierarchical GAT + BiGRU + Gated Cross-Attention

Main model class combining all components.
Supports both DTI (binary classification) and DTA (regression) tasks.
"""

import torch
import torch.nn as nn

from .encoders import DrugEncoder, ProteinEncoder
from .fusion   import GatedCrossAttention


class HGNN_RNN_DTI(nn.Module):
    """
    H-GNN-RNN-DTI model.

    Args:
        task         : 'dti' (binary classification) or 'dta' (regression)
        node_feat_dim: atom feature dimension (default 65 for RDKit)
        esm_dim      : protein embedding dimension (320 for ESM-2 8M, 1280 for ESM-2 650M)
        hidden_dim   : internal representation dimension
        gat_layers   : number of GAT layers
        gat_heads    : attention heads per GAT layer
        gru_layers   : number of BiGRU layers
        chemberta_dim: ChemBERTa CLS embedding dim (768); 0 to disable
        fusion_heads : cross-attention heads
        dropout      : dropout rate
        n_classes    : output classes for DTI (2) or 1 for DTA
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
        fusion_heads:  int   = 8,
        dropout:       float = 0.1,
    ):
        super().__init__()
        assert task in ('dti', 'dta')
        self.task = task

        # Protein input projection (handles variable ESM-2 dim)
        self.prot_input_proj = nn.Linear(esm_dim, esm_dim) if esm_dim == 320 else \
                               nn.Linear(esm_dim, 320)
        self.prot_esm_dim = 320  # normalized to 320 after projection

        self.drug_encoder    = DrugEncoder(
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
        self.fusion = GatedCrossAttention(
            dim=hidden_dim,
            heads=fusion_heads,
            dropout=dropout,
        )

        # Task head
        out_dim = 2 if task == 'dti' else 1
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_dim),
        )

    def forward(self, drug_graph, protein_emb):
        """
        Args:
            drug_graph  : PyG Batch of molecular graphs
            protein_emb : Tensor (B, L, esm_dim), (B, esm_dim), or (B, hidden_dim)
                          The last case occurs when pre-cached protein representations
                          are passed directly (already encoded by ProteinEncoder).

        Returns:
            logits (B, 2) for DTI  |  preds (B, 1) for DTA
        """
        drug_repr = self.drug_encoder(drug_graph)  # (B, H)

        last_dim = protein_emb.shape[-1]

        if last_dim == self.protein_encoder.hidden_dim and protein_emb.dim() == 2:
            # Pre-cached: already encoded by ProteinEncoder — use directly
            protein_repr = protein_emb
        else:
            # Raw ESM-2 embeddings — project to 320 if needed, then encode
            if last_dim != 320:
                protein_emb = self.prot_input_proj(protein_emb)
            protein_repr = self.protein_encoder(protein_emb)   # (B, H)

        fused = self.fusion(drug_repr, protein_repr)  # (B, H)
        return self.head(fused)

    def get_attention_weights(self, drug_graph, protein_emb):
        """
        XAI hook for Phase 1 interpretability.

        Requires raw ESM-2 embeddings (B, L, esm_dim) — not pre-cached representations.
        Protein must be in sequence mode so per-residue attention weights are available.

        Returns a dict with:
            logits          : (B, 2) DTI logits or (B, 1) DTA predictions
            residue_weights : (B, L)      — per-residue importance from AttentionPooling
            gate            : (B, H)      — GCA gate (mean > 0.5 → drug context dominates)
            node_emb        : (N, H)      — per-atom embeddings after last GAT layer
            node_batch      : (N,)        — atom → molecule index mapping
            bigru_hidden    : (B, L, 2H)  — BiGRU hidden states per residue
        """
        if protein_emb.shape[-1] != 320:
            protein_emb = self.prot_input_proj(protein_emb)

        drug_repr, node_emb, node_batch = self.drug_encoder(
            drug_graph, return_node_emb=True
        )

        enc_out = self.protein_encoder(protein_emb, return_attn=True)
        if isinstance(enc_out, tuple):
            protein_repr, residue_weights, bigru_hidden = enc_out
        else:
            # Fallback: mean-pooled path (no per-residue weights)
            protein_repr = enc_out
            residue_weights = None
            bigru_hidden = None

        fused, gate = self.fusion(drug_repr, protein_repr, return_gate=True)
        logits = self.head(fused)

        return {
            'logits':           logits,
            'residue_weights':  residue_weights,
            'gate':             gate,
            'node_emb':         node_emb,
            'node_batch':       node_batch,
            'bigru_hidden':     bigru_hidden,
        }
