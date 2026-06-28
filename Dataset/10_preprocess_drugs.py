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


# ── PubChem helper ───────────────────────────────────────────────────────────

def _smiles_from_props(props):
    """Extract SMILES from PubChem PropertyTable Properties dict.
    PubChem returns varying key names depending on the compound type."""
    for key in ("CanonicalSMILES", "IsomericSMILES", "SMILES", "ConnectivitySMILES"):
        if key in props:
            return props[key]
    return None


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


def load_yamanishi_smiles(subclass):
    """Load unique drug SMILES from Yamanishi pairs.csv."""
    path = os.path.join(RAW_DIR, "yamanishi_08", subclass, "pairs.csv")
    df   = pd.read_csv(path, usecols=["drug_id", "smiles"]).dropna().drop_duplicates("drug_id")
    return dict(zip(df["drug_id"], df["smiles"]))


def load_luo17_smiles():
    """
    DrugBank IDs (e.g. DB00001:Lepirudin) -> SMILES via PubChem name search.
    Results are cached in raw/luo_17/drug_smiles_cache.json to avoid re-fetching.
    Biologics without SMILES (antibodies, proteins) are skipped automatically.
    """
    import requests, time
    map_path   = os.path.join(RAW_DIR, "luo_17", "drug_dict_map.txt")
    cache_path = os.path.join(RAW_DIR, "luo_17", "drug_smiles_cache.json")

    # Load cache
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            cache = json.load(f)

    # Parse drug IDs and names
    drugs = {}
    with open(map_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            drug_id, *name_parts = line.split(":")
            drugs[drug_id.strip()] = ":".join(name_parts).strip()

    smiles_map = {}
    to_fetch   = [did for did in drugs if did not in cache]
    print(f"  Luo_17: {len(drugs)} drugs, {len(to_fetch)} need PubChem lookup, "
          f"{len(drugs) - len(to_fetch)} cached.")

    for i, drug_id in enumerate(tqdm(to_fetch, desc="  PubChem (luo_17)")):
        name = drugs[drug_id]
        smi  = None
        # Search PubChem by drug name; use _smiles_from_props to handle all key variants
        for query in [name, drug_id]:
            try:
                r = requests.get(
                    f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                    f"{requests.utils.quote(query)}"
                    f"/property/CanonicalSMILES,IsomericSMILES/JSON",
                    timeout=10)
                if r.status_code == 200:
                    props = r.json()["PropertyTable"]["Properties"][0]
                    smi   = _smiles_from_props(props)
                    if smi:
                        break
            except Exception:
                pass
            time.sleep(0.1)

        cache[drug_id] = smi
        if (i + 1) % 200 == 0:
            with open(cache_path, "w") as f:
                json.dump(cache, f)

    with open(cache_path, "w") as f:
        json.dump(cache, f)

    smiles_map = {did: smi for did, smi in cache.items() if smi}
    print(f"  Luo_17: {len(smiles_map)}/{len(drugs)} drugs resolved to SMILES "
          f"({len(drugs)-len(smiles_map)} biologics/unfound skipped).")
    return smiles_map


DATASET_LOADERS = {
    "davis":          load_davis_smiles,
    "kiba":           load_kiba_smiles,
    "luo_17":         load_luo17_smiles,
    "yamanishi_e":    lambda: load_yamanishi_smiles("e"),
    "yamanishi_ic":   lambda: load_yamanishi_smiles("ic"),
    "yamanishi_gpcr": lambda: load_yamanishi_smiles("gpcr"),
    "yamanishi_nr":   lambda: load_yamanishi_smiles("nr"),
}

# Large datasets processed via streaming (CSV path only — not loaded into memory)
LARGE_DATASET_PATHS = {
    "bindingdb": (os.path.join("raw", "bindingdb", "BindingDB_DTI.csv"), "smiles"),
    "chembl":    (os.path.join("raw", "chembl",    "chembl_DTI.csv"),    "smiles"),
}


# ── Main processing ───────────────────────────────────────────────────────────

CHECKPOINT_INTERVAL = 5000   # save partial graphs every N drugs for large datasets
STREAM_CHUNK_SIZE   = 10000  # rows per chunk for BindingDB / ChEMBL streaming


def process_dataset(name, smiles_dict, encoder, out_path):
    print(f"\nProcessing {name} ({len(smiles_dict):,} drugs)...")

    # Load existing checkpoint if present (allows resume after interruption)
    ckpt_path = out_path.replace(".pt", "_ckpt.pt")
    graphs    = torch.load(ckpt_path) if os.path.exists(ckpt_path) else {}
    already   = set(graphs.keys())
    remaining = {did: smi for did, smi in smiles_dict.items() if did not in already}
    if already:
        print(f"  Resuming from checkpoint: {len(already):,} done, "
              f"{len(remaining):,} remaining.")

    failed = []

    # ChemBERTa embeddings in batches
    unique_smiles = list({smi for smi in remaining.values()
                          if smi not in {g.smiles for g in graphs.values()
                                         if hasattr(g, 'smiles')}})
    if unique_smiles:
        print(f"  Getting ChemBERTa embeddings for {len(unique_smiles):,} unique SMILES...")
        emb_map = encoder.encode_batch(unique_smiles)
    else:
        emb_map = {}

    for i, (drug_id, smiles) in enumerate(
            tqdm(remaining.items(), desc=f"  Building graphs ({name})")):
        graph = smiles_to_graph(smiles)
        if graph is None:
            failed.append(drug_id)
            continue

        global_emb = emb_map.get(smiles)
        if global_emb is not None:
            graph.chemberta = torch.tensor(global_emb, dtype=torch.float).unsqueeze(0)

        graphs[drug_id] = graph

        # Periodic checkpoint for large datasets
        if (i + 1) % CHECKPOINT_INTERVAL == 0:
            torch.save(graphs, ckpt_path)
            print(f"    Checkpoint saved ({len(graphs):,} graphs).")

    print(f"  Successful: {len(graphs):,}  |  Failed (invalid SMILES): {len(failed)}")
    if failed:
        print(f"  Failed: {failed[:10]}{'...' if len(failed) > 10 else ''}")

    # Remove checkpoint on clean completion
    if os.path.exists(ckpt_path):
        os.remove(ckpt_path)

    return graphs


# Map dataset names to their raw data subdirectories for existence checks
RAW_CHECK_MAP = {
    "davis":          "davis",
    "kiba":           "kiba",
    "luo_17":         "luo_17",
    "yamanishi_e":    os.path.join("yamanishi_08", "e"),
    "yamanishi_ic":   os.path.join("yamanishi_08", "ic"),
    "yamanishi_gpcr": os.path.join("yamanishi_08", "gpcr"),
    "yamanishi_nr":   os.path.join("yamanishi_08", "nr"),
    "bindingdb":      "bindingdb",
    "chembl":         "chembl",
}


def process_dataset_streaming(name, csv_path, smiles_col, encoder, out_path):
    """
    Memory-safe processor for large datasets (BindingDB, ChEMBL).
    Saves one .pt file per chunk to avoid accumulating millions of objects in RAM.
    Final output is a manifest JSON listing the chunk files.
    """
    chunk_dir = out_path.replace(".pt", "_chunks")
    os.makedirs(chunk_dir, exist_ok=True)
    manifest_path = out_path.replace(".pt", "_manifest.json")

    # Load manifest to resume
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)

    seen   = set(manifest.get("seen_smiles", []))
    failed = set(manifest.get("failed_smiles", []))
    chunk_n = manifest.get("last_chunk", 0)

    print(f"\nProcessing {name} (streaming {STREAM_CHUNK_SIZE:,}/chunk -> separate files)...")
    if seen:
        print(f"  Resuming: {len(seen):,} SMILES already processed, "
              f"{chunk_n} chunks saved.")

    total_graphs = manifest.get("total_graphs", 0)

    for chunk in pd.read_csv(csv_path, usecols=[smiles_col],
                              chunksize=STREAM_CHUNK_SIZE):
        chunk_n += 1
        chunk_file = os.path.join(chunk_dir, f"chunk_{chunk_n:04d}.pt")
        if os.path.exists(chunk_file):
            continue   # already processed this chunk

        new_smiles = (chunk[smiles_col].dropna()
                                       .drop_duplicates()
                                       .tolist())
        new_smiles = [s for s in new_smiles if s not in seen and s not in failed]
        if not new_smiles:
            continue

        emb_map     = encoder.encode_batch(new_smiles)
        chunk_graphs = {}

        for smiles in new_smiles:
            graph = smiles_to_graph(smiles)
            if graph is None:
                failed.add(smiles)
                continue
            emb = emb_map.get(smiles)
            if emb is not None:
                graph.chemberta = torch.tensor(emb, dtype=torch.float).unsqueeze(0)
            chunk_graphs[smiles] = graph
            seen.add(smiles)

        # Save this chunk and free memory immediately
        torch.save(chunk_graphs, chunk_file)
        total_graphs += len(chunk_graphs)
        del chunk_graphs, emb_map

        # Update manifest
        manifest = {
            "chunk_files":    sorted(os.listdir(chunk_dir)),
            "last_chunk":     chunk_n,
            "total_graphs":   total_graphs,
            "total_failed":   len(failed),
            "seen_smiles":    list(seen),
            "failed_smiles":  list(failed),
        }
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        print(f"  Chunk {chunk_n:04d}: +{len(chunk_graphs) if 'chunk_graphs' in dir() else 0:,} "
              f"| total: {total_graphs:,} | failed: {len(failed):,}")

    print(f"  {name} complete: {total_graphs:,} graphs in {chunk_n} chunk files.")
    print(f"  Chunks saved in: {chunk_dir}")
    print(f"  Manifest: {manifest_path}")
    # Return manifest path as signal of completion (caller saves manifest, not .pt)
    return None


def main():
    print("=" * 55)
    print(" Drug Preprocessing (SMILES -> Graphs + ChemBERTa)")
    print("=" * 55)

    os.makedirs(OUT_DIR, exist_ok=True)
    encoder = ChemBERTaEncoder()

    # ── Standard datasets (fit in memory) ────────────────────────────────────
    for name, loader_fn in DATASET_LOADERS.items():
        raw_sub   = RAW_CHECK_MAP.get(name, name)
        raw_check = os.path.join(RAW_DIR, raw_sub)
        if not os.path.isdir(raw_check) or not os.listdir(raw_check):
            print(f"\nSkipping {name} — raw data not found.")
            continue

        out_path = os.path.join(OUT_DIR, f"{name}_drug_graphs.pt")
        if os.path.exists(out_path):
            print(f"\n{name}: graphs already exist — skipping.")
            continue

        try:
            smiles_dict = loader_fn()
            if not smiles_dict:
                print(f"\n{name}: no SMILES loaded — skipping.")
                continue
            graphs = process_dataset(name, smiles_dict, encoder, out_path)
            torch.save(graphs, out_path)
            print(f"  Saved -> {out_path}")
        except FileNotFoundError as e:
            print(f"\n  WARNING: Could not load {name}: {e}")

    # ── Large datasets (streamed chunk-by-chunk) ──────────────────────────────
    for name, (rel_csv, smiles_col) in LARGE_DATASET_PATHS.items():
        csv_path  = os.path.join(BASE_DIR, rel_csv)
        out_path  = os.path.join(OUT_DIR, f"{name}_drug_graphs.pt")

        if not os.path.exists(csv_path):
            print(f"\nSkipping {name} — CSV not found: {csv_path}")
            continue
        if os.path.exists(out_path):
            print(f"\n{name}: graphs already exist — skipping.")
            continue

        process_dataset_streaming(name, csv_path, smiles_col, encoder, out_path)
        print(f"  Done -> chunks in {out_path.replace('.pt','_chunks/')}")

    print("\nDone. Run 11_preprocess_proteins.py next.")


if __name__ == "__main__":
    main()
