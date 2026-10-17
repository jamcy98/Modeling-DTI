"""Torch dataset + collate that assembles model inputs from step-2 artifacts.

Reads the saved numpy drug graphs, protein token arrays, pair labels, and the
frozen split indices, and produces, per batch:
  - a PyTorch Geometric `Batch` of drug molecular graphs
  - a padded protein token tensor [B, L_max] + true lengths [B]
  - labels [B]

PyG `Data` assembly happens here (at load time), keeping step-2 preprocessing
dependency-light as intended.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset
from torch_geometric.data import Batch, Data

from .featurize import PAD_ID


class DTIDataset(Dataset):
    def __init__(self, root: str | Path, dataset: str, split: str,
                 split_name: str = "S1", seed: int = 42):
        root = Path(root)
        pdir = root / "processed" / dataset
        self.pairs = pd.read_csv(pdir / "pairs.csv")
        with open(pdir / "drug_graphs.pkl", "rb") as fh:
            self.drug_graphs = pickle.load(fh)
        with open(pdir / "protein_tokens.pkl", "rb") as fh:
            self.protein_tokens = pickle.load(fh)
        with open(root / "splits" / dataset / f"{split_name}_seed{seed}.json") as fh:
            self.indices = json.load(fh)[split]

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, i: int):
        row = self.pairs.iloc[self.indices[i]]
        g = self.drug_graphs[row["Drug_ID"]]
        data = Data(
            x=torch.from_numpy(g["node_feats"]),
            edge_index=torch.from_numpy(g["edge_index"]),
            edge_attr=torch.from_numpy(g["edge_feats"]),
        )
        prot = torch.from_numpy(self.protein_tokens[row["Target_ID"]]).long()
        label = torch.tensor(float(row["label"]))
        return data, prot, label


def collate(batch):
    drugs, prots, labels = zip(*batch)
    drug_batch = Batch.from_data_list(list(drugs))
    lengths = torch.tensor([len(p) for p in prots], dtype=torch.long)
    prot_pad = pad_sequence(list(prots), batch_first=True, padding_value=PAD_ID)
    labels = torch.stack(labels)
    return drug_batch, prot_pad, lengths, labels


def make_collate(max_protein_length: int | None = None):
    """Collate factory. Pass a cap to truncate proteins (a CPU cost lever);
    None keeps full length (use on GPU)."""
    if max_protein_length is None:
        return collate

    def _truncating_collate(batch):
        drug_batch, prot_pad, lengths, labels = collate(batch)
        prot_pad = prot_pad[:, :max_protein_length]
        lengths = torch.clamp(lengths, max=max_protein_length)
        return drug_batch, prot_pad, lengths, labels

    return _truncating_collate
