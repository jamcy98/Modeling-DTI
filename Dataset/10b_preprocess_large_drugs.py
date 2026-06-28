"""
Build RDKit molecular graphs for large datasets (BindingDB, ChEMBL).
Does NOT load ChemBERTa — uses only RDKit atom/bond features.
Processes in chunks of 10,000 SMILES to stay within memory limits.

Run:
    python 10b_preprocess_large_drugs.py

Output:
    processed/drug_graphs/bindingdb_drug_graphs_chunks/chunk_NNNN.pt
    processed/drug_graphs/bindingdb_drug_graphs_manifest.json
    processed/drug_graphs/chembl_drug_graphs_chunks/chunk_NNNN.pt
    processed/drug_graphs/chembl_drug_graphs_manifest.json
"""

import os, json
import torch
import pandas as pd
from tqdm import tqdm
from rdkit import Chem
from torch_geometric.data import Data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.path.join(BASE_DIR, "raw")
OUT_DIR  = os.path.join(BASE_DIR, "processed", "drug_graphs")
CHUNK    = 10_000

DATASETS = {
    "bindingdb": (os.path.join(RAW_DIR, "bindingdb", "BindingDB_DTI.csv"), "smiles"),
    "chembl":    (os.path.join(RAW_DIR, "chembl",    "chembl_DTI.csv"),    "smiles"),
}

# ── RDKit atom/bond features (same as 10_preprocess_drugs.py) ────────────────

ATOM_LIST = [
    "C","N","O","S","F","Si","P","Cl","Br","Mg","Na","Ca","Fe","As","Al","I",
    "B","V","K","Tl","Yb","Sb","Sn","Ag","Pd","Co","Se","Ti","Zn","H","Li",
    "Ge","Cu","Au","Ni","Cd","In","Mn","Zr","Cr","Pt","Hg","Pb","other"
]
DEGREE_LIST = [0,1,2,3,4,5,6,7,8,9,10]
HYBRIDIZATION_MAP = {
    Chem.rdchem.HybridizationType.S:0, Chem.rdchem.HybridizationType.SP:1,
    Chem.rdchem.HybridizationType.SP2:2, Chem.rdchem.HybridizationType.SP3:3,
    Chem.rdchem.HybridizationType.SP3D:4, Chem.rdchem.HybridizationType.SP3D2:5,
}

def one_hot(v, choices):
    enc = [0]*len(choices)
    enc[choices.index(v) if v in choices else len(choices)-1] = 1
    return enc

def atom_features(atom):
    sym = atom.GetSymbol() if atom.GetSymbol() in ATOM_LIST else "other"
    hyb = [0]*6; hyb[HYBRIDIZATION_MAP.get(atom.GetHybridization(),5)] = 1
    return (one_hot(sym, ATOM_LIST) + one_hot(min(atom.GetDegree(),10), DEGREE_LIST)
            + hyb + [int(atom.GetIsAromatic()), int(atom.IsInRing()),
                     atom.GetFormalCharge(), atom.GetTotalNumHs()])

def bond_features(bond):
    bt = bond.GetBondTypeAsDouble()
    return [int(bt==1.0),int(bt==1.5),int(bt==2.0),int(bt==3.0),
            int(bond.GetIsConjugated()),int(bond.IsInRing())]

def smiles_to_graph(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    x = torch.tensor([atom_features(a) for a in mol.GetAtoms()], dtype=torch.float)
    ei, ea = [], []
    for b in mol.GetBonds():
        i,j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        bf = bond_features(b)
        ei += [[i,j],[j,i]]; ea += [bf,bf]
    if ei:
        ei_t = torch.tensor(ei,dtype=torch.long).t().contiguous()
        ea_t = torch.tensor(ea,dtype=torch.float)
    else:
        ei_t = torch.zeros((2,0),dtype=torch.long)
        ea_t = torch.zeros((0,6),dtype=torch.float)
    return Data(x=x, edge_index=ei_t, edge_attr=ea_t, smiles=smiles, num_nodes=x.size(0))


# ── Streaming processor ───────────────────────────────────────────────────────

def process(name, csv_path, smiles_col):
    chunk_dir     = os.path.join(OUT_DIR, f"{name}_drug_graphs_chunks")
    manifest_path = os.path.join(OUT_DIR, f"{name}_drug_graphs_manifest.json")
    os.makedirs(chunk_dir, exist_ok=True)

    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)

    seen        = set(manifest.get("seen_smiles", []))
    failed      = set(manifest.get("failed_smiles", []))
    chunk_n     = manifest.get("last_chunk", 0)
    total_graphs= manifest.get("total_graphs", 0)

    print(f"\n[{name}] Streaming {CHUNK:,} SMILES/chunk (RDKit only, no ChemBERTa)...")
    if seen:
        print(f"  Resuming: {len(seen):,} done, {chunk_n} chunks saved.")

    for chunk_df in pd.read_csv(csv_path, usecols=[smiles_col], chunksize=CHUNK):
        chunk_n += 1
        chunk_file = os.path.join(chunk_dir, f"chunk_{chunk_n:04d}.pt")
        if os.path.exists(chunk_file):
            continue

        new_smiles = [s for s in chunk_df[smiles_col].dropna().drop_duplicates().tolist()
                      if s not in seen and s not in failed]
        if not new_smiles:
            continue

        chunk_graphs = {}
        for smi in new_smiles:
            g = smiles_to_graph(smi)
            if g is None:
                failed.add(smi)
            else:
                chunk_graphs[smi] = g
                seen.add(smi)

        torch.save(chunk_graphs, chunk_file)
        total_graphs += len(chunk_graphs)
        del chunk_graphs

        manifest = {
            "chunk_files":   sorted(os.listdir(chunk_dir)),
            "last_chunk":    chunk_n,
            "total_graphs":  total_graphs,
            "total_failed":  len(failed),
            "seen_smiles":   list(seen),
            "failed_smiles": list(failed),
        }
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        print(f"  Chunk {chunk_n:04d}: +{len(chunk_graphs) if 'chunk_graphs' in dir() else 0}"
              f" | total: {total_graphs:,} | failed: {len(failed):,}")

    print(f"  Done: {total_graphs:,} graphs in {chunk_n} chunks -> {chunk_dir}")


def main():
    print("=" * 55)
    print(" Large Dataset Drug Graph Preprocessing (RDKit only)")
    print("=" * 55)
    os.makedirs(OUT_DIR, exist_ok=True)

    for name, (csv_path, smiles_col) in DATASETS.items():
        if not os.path.exists(csv_path):
            print(f"\nSkipping {name} -- CSV not found: {csv_path}")
            continue
        manifest = os.path.join(OUT_DIR, f"{name}_drug_graphs_manifest.json")
        chunk_dir = os.path.join(OUT_DIR, f"{name}_drug_graphs_chunks")
        # Check if already fully done (rough heuristic: manifest exists with chunks)
        if os.path.exists(manifest):
            with open(manifest) as f: m = json.load(f)
            if m.get("total_graphs", 0) > 0:
                print(f"\n{name}: {m['total_graphs']:,} graphs already in "
                      f"{m['last_chunk']} chunks -- resuming if incomplete.")
        process(name, csv_path, smiles_col)

    print("\nAll done.")


if __name__ == "__main__":
    main()
