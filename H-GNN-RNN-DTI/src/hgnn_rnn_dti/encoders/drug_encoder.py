"""H-GAT drug encoder (roadmap step 4, proposal §3.6.2).

A Hierarchical Graph Attention Network over the molecular graph:
  - multi-head attention message passing (GATv2, with bond/edge features);
  - a stack of layers whose receptive field grows from local atom neighbourhoods
    toward larger substructures ("hierarchical");
  - jumping-knowledge concatenation of per-layer states to retain multi-scale
    (local + substructure) information;
  - atom-level states are RETAINED (converted to a dense [B, n_max, d] tensor +
    mask) rather than pooled, because each atom must later participate in the
    bidirectional Gated Cross-Attention with protein residues.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as Fnn
from torch_geometric.nn import GATv2Conv
from torch_geometric.utils import to_dense_batch


class HGATEncoder(nn.Module):
    def __init__(
        self,
        atom_dim: int,
        bond_dim: int,
        hidden: int = 128,
        latent_dim: int = 128,
        heads: int = 4,
        layers: int = 3,
        dropout: float = 0.2,
        jumping_knowledge: str = "cat",  # "cat" | "last"
    ):
        super().__init__()
        assert hidden % heads == 0, "hidden must be divisible by heads"
        self.jk = jumping_knowledge
        self.input_proj = nn.Linear(atom_dim, hidden)
        self.convs = nn.ModuleList([
            GATv2Conv(hidden, hidden // heads, heads=heads, concat=True,
                      edge_dim=bond_dim, dropout=dropout, add_self_loops=True)
            for _ in range(layers)
        ])
        self.norms = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(layers)])
        self.dropout = nn.Dropout(dropout)
        in_dim = hidden * layers if jumping_knowledge == "cat" else hidden
        self.out_proj = nn.Linear(in_dim, latent_dim)

    def forward(self, data):
        """data: PyG Batch -> (D [B, n_max, latent], mask [B, n_max])."""
        x = Fnn.relu(self.input_proj(data.x))
        layer_states = []
        for conv, norm in zip(self.convs, self.norms):
            h = conv(x, data.edge_index, data.edge_attr)
            h = self.dropout(Fnn.relu(norm(h)))
            x = x + h  # residual: progressively larger receptive field
            layer_states.append(x)
        x = torch.cat(layer_states, dim=-1) if self.jk == "cat" else x
        x = self.out_proj(x)  # [N_total, latent]
        D, mask = to_dense_batch(x, data.batch)  # [B, n_max, latent], [B, n_max]
        return D, mask
