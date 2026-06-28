"""
Drug and Protein encoders for H-GNN-RNN-DTI.

Drug Encoder  : Hierarchical GAT (3 layers, 8 heads) with optional ChemBERTa fusion
Protein Encoder: BiGRU with attention pooling (for full residue embeddings)
                 or linear projection (for mean-pooled embeddings)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, global_mean_pool, global_max_pool


# ── Drug Encoder ──────────────────────────────────────────────────────────────

class ResidualGATBlock(nn.Module):
    """Single GAT layer with residual connection and layer norm."""

    def __init__(self, in_dim: int, out_dim: int, heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.gat   = GATConv(in_dim, out_dim // heads, heads=heads, dropout=dropout,
                             edge_dim=6, add_self_loops=True)
        self.proj  = nn.Linear(in_dim, out_dim) if in_dim != out_dim else nn.Identity()
        self.norm  = nn.LayerNorm(out_dim)
        self.drop  = nn.Dropout(dropout)

    def forward(self, x, edge_index, edge_attr=None):
        h = self.gat(x, edge_index, edge_attr)
        h = self.drop(F.elu(h))
        return self.norm(h + self.proj(x))


class DrugEncoder(nn.Module):
    """
    Hierarchical GAT: 3 layers × 8 heads.
    Optionally fuses ChemBERTa CLS embedding (768-dim) after graph pooling.

    Output: drug_repr of shape (batch, hidden_dim)
    """

    def __init__(
        self,
        node_feat_dim: int = 65,
        hidden_dim:    int = 256,
        n_layers:      int = 3,
        heads:         int = 8,
        chemberta_dim: int = 768,
        dropout:       float = 0.1,
    ):
        super().__init__()
        self.input_proj = nn.Sequential(
            nn.Linear(node_feat_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        self.gat_layers = nn.ModuleList([
            ResidualGATBlock(hidden_dim, hidden_dim, heads=heads, dropout=dropout)
            for _ in range(n_layers)
        ])

        # Mean + Max pooling → 2 × hidden_dim
        graph_out_dim = 2 * hidden_dim

        # Optional ChemBERTa fusion
        self.chemberta_proj = nn.Sequential(
            nn.Linear(chemberta_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        fused_dim = graph_out_dim + hidden_dim  # with ChemBERTa

        self.output_proj = nn.Sequential(
            nn.Linear(fused_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
        )
        # Fallback when no ChemBERTa available
        self.output_proj_no_cb = nn.Sequential(
            nn.Linear(graph_out_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
        )

        self.hidden_dim = hidden_dim

    def forward(self, data):
        x         = self.input_proj(data.x)
        edge_index = data.edge_index
        edge_attr  = data.edge_attr if hasattr(data, 'edge_attr') else None
        batch      = data.batch

        for layer in self.gat_layers:
            x = layer(x, edge_index, edge_attr)

        # Global pooling
        mean_pool = global_mean_pool(x, batch)   # (B, H)
        max_pool  = global_max_pool(x, batch)    # (B, H)
        graph_rep = torch.cat([mean_pool, max_pool], dim=-1)  # (B, 2H)

        # ChemBERTa fusion
        if hasattr(data, 'chemberta') and data.chemberta is not None:
            cb = data.chemberta
            if cb.dim() == 3:
                cb = cb.squeeze(1)            # (B, 768)
            cb_proj   = self.chemberta_proj(cb)
            fused     = torch.cat([graph_rep, cb_proj], dim=-1)
            return self.output_proj(fused)

        return self.output_proj_no_cb(graph_rep)


# ── Protein Encoder ───────────────────────────────────────────────────────────

class AttentionPooling(nn.Module):
    """Learnable attention pooling over sequence dimension."""

    def __init__(self, dim: int):
        super().__init__()
        self.attn = nn.Linear(dim, 1)

    def forward(self, x, mask=None):
        # x: (B, L, D)
        scores = self.attn(x).squeeze(-1)          # (B, L)
        if mask is not None:
            scores = scores.masked_fill(mask, -1e9)
        weights = torch.softmax(scores, dim=-1)    # (B, L)
        return (weights.unsqueeze(-1) * x).sum(dim=1)  # (B, D)


class ProteinEncoder(nn.Module):
    """
    Two modes:
      - 'sequence': BiGRU over residue embeddings (B, L, esm_dim) → (B, hidden_dim)
      - 'pooled':   Linear projection of mean-pooled embedding (B, esm_dim) → (B, hidden_dim)

    Automatically selects mode based on input tensor shape.
    """

    def __init__(
        self,
        esm_dim:    int   = 320,
        hidden_dim: int   = 256,
        n_layers:   int   = 2,
        dropout:    float = 0.1,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim

        # Projection for any input dim → esm_dim (handles 1280-dim Luo_17)
        self.input_norm = nn.LayerNorm(esm_dim)

        # BiGRU path (for full residue embeddings)
        self.bigru = nn.GRU(
            input_size=esm_dim,
            hidden_size=hidden_dim,
            num_layers=n_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if n_layers > 1 else 0.0,
        )
        self.attn_pool = AttentionPooling(hidden_dim * 2)
        self.gru_proj  = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # Linear path (for mean-pooled embeddings)
        self.linear_path = nn.Sequential(
            nn.Linear(esm_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
        )

    def forward(self, x):
        # x: (B, L, D) for sequence mode or (B, D) for pooled mode
        if x.dim() == 3:
            # Full residue sequence — BiGRU path
            x = self.input_norm(x)
            out, _ = self.bigru(x)             # (B, L, 2H)
            pooled = self.attn_pool(out)       # (B, 2H)
            return self.gru_proj(pooled)       # (B, H)
        else:
            # Mean-pooled — linear projection
            return self.linear_path(x)        # (B, H)
