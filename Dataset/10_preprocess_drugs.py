"""
Preprocess drug molecules: SMILES -> molecular graphs with ChemBERTa node features.

For each dataset, reads SMILES strings, builds a PyTorch Geometric graph for each
drug molecule, and initialises node features using:
  - RDKit atom descriptors (structural features)
  - ChemBERTa embeddings (pre-trained chemical language model features)

Run:
    python 10_preprocess_drugs.py

Output:
    processed/drug_graphs/{dataset}_drug_graphs.pt
        -> dict { drug_id : torch_geometric.data.Data }

Requirements:
    pip install torch torch-geometric rdkit transformers tqdm
"""

import os
import json
import pickle
import torch
import numpy as np
import pandas as pd
from tqdm import tqdm

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from torch_geometric.data import Data
from transformers import AutoTokenizer, AutoModel

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
RAW_DIR        = os.path.join(BASE_DIR, "raw")
OUT_DIR        = os.path.join(BASE_DIR, "processed", "drug_graphs")
CHEMBERTA_MODEL = "seyonec/ChemBERTa-zinc-base-v1"

# ── Atom feature helpers ──────────────────────────────────────────────────────

ATOM_LIST = [
    "C", "N", "O", "S", "F", "Si", "P", "Cl", "Br", "Mg",
    "Na", "Ca", "Fe", "As", "Al", "I", "B", "V", "K", "Tl",
    "Yb", "Sb", "Sn", "Ag", "Pd", "Co", "Se", "Ti", "Zn",
    "H", "Li", "Ge", "Cu", "Au", "Ni", "Cd", "In", "Mn",
    "Zr", "Cr", "Pt", "Hg", "Pb", "other"
]

DEGREE_LIST       = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
HYBRIDIZATION_MAP = {
    Chem.rdchem.HybridizationType.S:    0,
    Chem.rdchem.HybridizationType.SP:   1,
    Chem.rdchem.HybridizationType.SP2:  2,
    Chem.rdchem.HybridizationType.SP3:  3,
    Chem.rdchem.HybridizationType.SP3D: 4,
    Chem.rdchem.HybridizationType.SP3D2:5,
}


def one_hot(value, choices):
    """One-hot encode `value` against `choices`. Puts 1 in last slot if unknown."""
    enc = [0] * len(choices)
    idx = choices.index(value) if value in choices else len(choices) - 1
    enc[idx] = 1
    return enc


def atom_features(atom):
    symbol      = atom.GetSymbol() if atom.GetSymbol() in ATOM_LIST else "other"
    degree      = min(atom.GetDegree(), 10)
    hyb         = HYBRIDIZATION_MAP.get(atom.GetHybridization(), 5)
    hyb_enc     = [0] * 6
    hyb_enc[hyb]= 1

    feat = (
        one_hot(symbol, ATOM_LIST)          # 45 dims
        + one_hot(degree, DEGREE_LIST)       # 11 dims
        + hyb_enc                            # 6 dims
        + [int(atom.GetIsAromatic())]        # 1 dim
        + [int(atom.IsInRing())]             # 1 dim
        + [atom.GetFormalCharge()]           # 1 dim
        + [atom.GetTotalNumHs()]             # 1 dim
    )
    return feat  # total: 66 dims


def bond_features(bond):
    bt = bond.GetBondTypeAsDouble()
    return [
        int(bt == 1.0),    # single
        int(bt == 1.5),    # aromatic
        int(bt == 2.0),    # double
        int(bt == 3.0),    # triple
        int(bond.GetIsConjugated()),
        int(bond.IsInRing()),
    ]  # total: 6 dims


def smiles_to_graph(smiles):
    """Convert a SMILES string to a PyTorch Geometric Data object."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    # Node features
    node_feats = [atom_features(a) for a in mol.GetAtoms()]
    x = torch.tensor(node_feats, dtype=torch.float)

    # Edge index and edge features
    edge_index = []
    edge_attr  = []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        bf   = bond_features(bond)
        edge_index += [[i, j], [j, i]]   # undirected -> add both directions
        edge_attr  += [bf, bf]

    if len(edge_index) == 0:
        # Single-atom molecule
        edge_index_t = torch.zeros((2, 0), dtype=torch.long)
        edge_attr_t  = torch.zeros((0, 6), dtype=torch.float)
    else:
        edge_index_t = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_attr_t  = torch.tensor(edge_attr,  dtype=torch.float)

    return Data(x=x, edge_index=edge_index_t, edge_attr=edge_attr_t,
                smiles=smiles, num_nodes=x.size(0))


# ── ChemBERTa embedding ───────────────────────────────────────────────────────

class ChemBERTaEncoder:
    def __init__(self, model_name=CHEMBERTA_MODEL, device=None, batch_size=32):
        self.device     = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        print(f"  Loading ChemBERTa model: {model_name} (device: {self.device})")
        self.tokenizer  = AutoTokenizer.from_pretrained(model_name)
        self.model      = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self.embed_dim  = self.model.config.hidden_size

    @torch.no_grad()
    def encode_batch(self, smiles_list):
        """Returns a dict {smiles: embedding_vector (numpy 1D)}."""
        results = {}
        for i in range(0, len(smiles_list), self.batch_size):
            batch = smiles_list[i : i + self.batch_size]
            tokens = self.tokenizer(batch, return_tensors="pt", padding=True,
                                    truncation=True, max_length=512).to(self.device)
            out  = self.model(**tokens)
            # Use CLS token as global drug-level embedding
            embs = out.last_hidden_state[:, 0, :].cpu().numpy()
            for smi, emb in zip(batch, embs):
                results[smi] = emb
        return results


# ── Dataset-specific SMILES loaders ──────────────────────────────────────────

def load_davis_smiles():
    path = os.path.join(RAW_DIR, "davis", "ligands_can.txt")
    with open(path) as f:
        data = json.load(f)
    return data   # {drug_name: smiles}


def load_kiba_smiles():
    path = os.path.join(RAW_DIR, "kiba", "ligands_can.txt")
    with open(path) as f:
        data = json.load(f)
    return data


def load_bindingdb_smiles():
    dti_path = os.path.join(RAW_DIR, "bindingdb", "BindingDB_DTI.csv")
    df = pd.read_csv(dti_path)
    return {row["smiles"]: row["smiles"] for _, row in df.iterrows()}


def load_chembl_smiles():
    path = os.path.join(RAW_DIR, "chembl", "chembl_DTI.csv")
    df   = pd.read_csv(path)
    return {row["smiles"]: row["smiles"] for _, row in df.iterrows()}


DATASET_LOADERS = {
    # DAVIS and KIBA: small, fast on CPU — run now
    "davis":     load_davis_smiles,
    "kiba":      load_kiba_smiles,
    # BindingDB (~1.3M drugs) and ChEMBL (~935K drugs): need GPU or overnight run
    # Uncomment when GPU is available or running batch overnight
    # "bindingdb": load_bindingdb_smiles,
    # "chembl":    load_chembl_smiles,
}


# ── Main processing ───────────────────────────────────────────────────────────

def process_dataset(name, smiles_dict, encoder):
    print(f"\nProcessing {name} ({len(smiles_dict):,} drugs)...")
    graphs = {}
    failed = []

    # Get ChemBERTa embeddings for all SMILES in one batched pass
    unique_smiles = list(set(smiles_dict.values()))
    print(f"  Getting ChemBERTa embeddings for {len(unique_smiles)} unique SMILES...")
    emb_map = encoder.encode_batch(unique_smiles)

    for drug_id, smiles in tqdm(smiles_dict.items(), desc=f"  Building graphs"):
        graph = smiles_to_graph(smiles)
        if graph is None:
            failed.append(drug_id)
            continue

        # Append ChemBERTa CLS embedding as graph-level feature
        global_emb    = emb_map.get(smiles)
        if global_emb is not None:
            graph.chemberta = torch.tensor(global_emb, dtype=torch.float).unsqueeze(0)

        graphs[drug_id] = graph

    print(f"  Successful: {len(graphs):,}  |  Failed (invalid SMILES): {len(failed)}")
    if failed:
        print(f"  Failed drug IDs: {failed[:10]}{'...' if len(failed)>10 else ''}")

    return graphs


def main():
    print("=" * 55)
    print(" Drug Preprocessing (SMILES -> Graphs + ChemBERTa)")
    print("=" * 55)

    encoder = ChemBERTaEncoder()

    for name, loader_fn in DATASET_LOADERS.items():
        raw_check = os.path.join(RAW_DIR, name if name not in ("bindingdb","chembl")
                                 else name)
        if not os.path.isdir(raw_check) or not os.listdir(raw_check):
            print(f"\nSkipping {name} — raw data not found. Run download script first.")
            continue

        out_path = os.path.join(OUT_DIR, f"{name}_drug_graphs.pt")
        if os.path.exists(out_path):
            print(f"\n{name} graphs already exist at {out_path} — skipping.")
            continue

        try:
            smiles_dict = loader_fn()
            graphs      = process_dataset(name, smiles_dict, encoder)
            torch.save(graphs, out_path)
            print(f"  Saved -> {out_path}")
        except FileNotFoundError as e:
            print(f"\n  WARNING: Could not load {name}: {e}")

    print("\nDone. Run 11_preprocess_proteins.py next.")


if __name__ == "__main__":
    main()
