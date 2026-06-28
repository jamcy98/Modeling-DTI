"""
PyTorch Dataset classes for H-GNN-RNN-DTI.

Supports:
  - DTI (binary) and DTA (regression) tasks
  - Both single .pt drug graph files and chunked files (BindingDB/ChEMBL)
  - Full residue protein embeddings and mean-pooled embeddings
"""

import os, json
import numpy as np
import torch
from torch.utils.data import Dataset


BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR   = os.path.join(BASE_DIR, "Dataset", "processed")
GRAPH_DIR  = os.path.join(PROC_DIR, "drug_graphs")
EMB_DIR    = os.path.join(PROC_DIR, "protein_embeddings")
LABEL_DIR  = os.path.join(PROC_DIR, "labels")


def _load_drug_graphs(dataset_name: str) -> dict:
    """Load drug graphs from a .pt file or chunked directory."""
    pt_path = os.path.join(GRAPH_DIR, f"{dataset_name}_drug_graphs.pt")
    if os.path.exists(pt_path):
        return torch.load(pt_path, map_location="cpu", weights_only=False)

    # Chunked datasets (BindingDB, ChEMBL)
    chunk_dir = os.path.join(GRAPH_DIR, f"{dataset_name}_drug_graphs_chunks")
    if os.path.isdir(chunk_dir):
        graphs = {}
        for fname in sorted(os.listdir(chunk_dir)):
            if fname.endswith(".pt"):
                chunk = torch.load(os.path.join(chunk_dir, fname),
                                   map_location="cpu", weights_only=False)
                graphs.update(chunk)
        return graphs

    raise FileNotFoundError(f"No drug graphs found for '{dataset_name}'")


def _load_protein_embeddings(dataset_name: str):
    """Load protein embeddings. Returns numpy array and ID list."""
    emb_path = os.path.join(EMB_DIR, f"{dataset_name}_protein_embeddings.npy")
    id_path  = os.path.join(EMB_DIR, f"{dataset_name}_protein_ids.json")

    if not os.path.exists(emb_path):
        raise FileNotFoundError(f"No protein embeddings found for '{dataset_name}'")

    embeddings = np.load(emb_path)   # (n_proteins, ...) — lazy load
    with open(id_path) as f:
        protein_ids = json.load(f)

    return embeddings, protein_ids


class DTIDataset(Dataset):
    """
    Binary DTI dataset.
    Each item: (drug_graph, protein_emb, label)
    """

    def __init__(
        self,
        dataset_name:  str,
        split_indices: list,
        ratio:         str = '1to1',   # '1to1' or '1to10'
    ):
        self.drug_graphs = _load_drug_graphs(dataset_name)
        emb, prot_ids    = _load_protein_embeddings(dataset_name)
        self.emb         = emb
        self.prot_id_map = {pid: i for i, pid in enumerate(prot_ids)}

        # Load label CSV
        csv_name = f"{dataset_name}_dti_labels_{ratio}.csv"
        import pandas as pd
        df = pd.read_csv(os.path.join(LABEL_DIR, csv_name))
        df = df.iloc[split_indices].reset_index(drop=True)
        self.pairs = df[['drug_id', 'protein_id', 'label']].values

    def __len__(self):
        return len(self.pairs)

    def set_protein_cache(self, cache: dict):
        self.prot_cache = cache

    def __getitem__(self, idx):
        drug_id, prot_id, label = self.pairs[idx]
        graph    = self.drug_graphs.get(str(drug_id))
        prot_idx = self.prot_id_map.get(str(prot_id))

        if graph is None or prot_idx is None:
            return None

        if hasattr(self, 'prot_cache') and str(prot_id) in self.prot_cache:
            prot_emb = self.prot_cache[str(prot_id)]
        else:
            prot_emb = torch.tensor(self.emb[prot_idx], dtype=torch.float)

        return graph, prot_emb, torch.tensor(int(label), dtype=torch.long)


class DTADataset(Dataset):
    """
    Binding affinity regression dataset.
    Each item: (drug_graph, protein_emb, affinity_value)
    Affinity column: pKd (Davis/KIBA) — auto-detected.
    """

    def __init__(self, dataset_name: str, split_indices: list):
        self.drug_graphs = _load_drug_graphs(dataset_name)
        emb, prot_ids    = _load_protein_embeddings(dataset_name)
        self.emb         = emb
        self.prot_id_map = {pid: i for i, pid in enumerate(prot_ids)}

        import pandas as pd
        csv_name = f"{dataset_name}_dta_labels.csv"
        df = pd.read_csv(os.path.join(LABEL_DIR, csv_name))
        df = df.iloc[split_indices].reset_index(drop=True)
        # Auto-detect affinity column
        aff_col = 'label' if 'label' in df.columns else \
                  'pKd'   if 'pKd'   in df.columns else \
                  'kiba'  if 'kiba'  in df.columns else df.columns[-1]
        self.pairs = df[['drug_id', 'protein_id', aff_col]].values

    def __len__(self):
        return len(self.pairs)

    def set_protein_cache(self, cache: dict):
        self.prot_cache = cache

    def __getitem__(self, idx):
        drug_id, prot_id, label = self.pairs[idx]
        graph    = self.drug_graphs.get(str(drug_id))
        prot_idx = self.prot_id_map.get(str(prot_id))

        if graph is None or prot_idx is None:
            return None

        if hasattr(self, 'prot_cache') and str(prot_id) in self.prot_cache:
            prot_emb = self.prot_cache[str(prot_id)]
        else:
            prot_emb = torch.tensor(self.emb[prot_idx], dtype=torch.float)

        return graph, prot_emb, torch.tensor(float(label), dtype=torch.float)


def build_dataset(dataset_name: str, task: str, split_indices: list, ratio: str = '1to1'):
    """Factory function: returns the right Dataset class."""
    if task == 'dta':
        return DTADataset(dataset_name, split_indices)
    return DTIDataset(dataset_name, split_indices, ratio=ratio)
