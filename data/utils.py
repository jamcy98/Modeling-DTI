"""
DataLoader utilities for H-GNN-RNN-DTI.

Handles variable-length protein sequences via padding,
and batching of PyG graphs using torch_geometric.
"""

import torch
from torch.utils.data import DataLoader
from torch_geometric.data import Batch


MAX_SEQ_LEN = 256   # truncate residue sequences for BiGRU on CPU


def collate_fn(batch):
    """
    Custom collate: filters None items, batches PyG graphs, stacks protein tensors.
    Protein tensors are pre-encoded (cached) so they are always 1D: (hidden_dim,).
    For raw embeddings (not cached), truncates to MAX_SEQ_LEN and pads.
    """
    batch = [b for b in batch if b is not None]
    if not batch:
        return None

    graphs, prot_embs, labels = zip(*batch)
    drug_batch = Batch.from_data_list(list(graphs))

    if prot_embs[0].dim() == 1:
        # Pre-cached protein representations — just stack
        prot_batch = torch.stack(list(prot_embs))
    elif prot_embs[0].dim() == 2:
        # Raw residue embeddings — truncate then pad
        truncated  = [e[:MAX_SEQ_LEN] for e in prot_embs]
        max_len    = max(e.size(0) for e in truncated)
        padded     = torch.zeros(len(truncated), max_len, truncated[0].size(-1))
        for i, e in enumerate(truncated):
            padded[i, :e.size(0)] = e
        prot_batch = padded
    else:
        prot_batch = torch.stack(list(prot_embs))

    return drug_batch, prot_batch, torch.stack(list(labels))


def precompute_protein_cache(protein_encoder, emb_array, prot_ids, device,
                             batch_size=64, max_seq_len=MAX_SEQ_LEN):
    """
    Run all unique proteins through ProteinEncoder once and cache results.
    Returns: dict {prot_id: repr_tensor (hidden_dim,)}
    This makes per-batch protein lookup O(1) instead of re-running BiGRU.
    """
    import numpy as np
    protein_encoder.eval()
    cache = {}
    ids   = list(prot_ids)

    id_to_idx = {pid: i for i, pid in enumerate(ids)}

    with torch.no_grad():
        for i in range(0, len(ids), batch_size):
            batch_ids  = ids[i : i + batch_size]
            batch_embs = []
            for pid in batch_ids:
                idx = id_to_idx[pid]
                emb = torch.tensor(emb_array[idx], dtype=torch.float)
                if emb.dim() == 2:
                    emb = emb[:max_seq_len]          # truncate
                batch_embs.append(emb)

            if batch_embs[0].dim() == 2:
                # Pad sequence batch
                ml  = max(e.size(0) for e in batch_embs)
                pad = torch.zeros(len(batch_embs), ml, batch_embs[0].size(-1))
                for j, e in enumerate(batch_embs):
                    pad[j, :e.size(0)] = e
                inp = pad.to(device)
            else:
                inp = torch.stack(batch_embs).to(device)

            reprs = protein_encoder(inp)          # (B, hidden_dim)
            for pid, r in zip(batch_ids, reprs.cpu()):
                cache[pid] = r

    protein_encoder.train()
    return cache


def get_dataloader(
    dataset,
    batch_size:  int  = 32,
    shuffle:     bool = True,
    num_workers: int  = 0,
    pin_memory:  bool = False,
):
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=collate_fn,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=False,
    )
