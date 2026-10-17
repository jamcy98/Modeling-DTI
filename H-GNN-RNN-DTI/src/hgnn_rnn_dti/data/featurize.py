"""Featurization for H-GNN-RNN-DTI (roadmap step 2).

Drug side: SMILES -> molecular graph (atom-node features, bond-edge features,
bidirectional edge index) as plain NumPy arrays. We deliberately do NOT build
PyTorch Geometric `Data` objects here — step 2 stays dependency-light (RDKit +
NumPy only); PyG assembly happens in the dataloader at encoder time (step 4).

Protein side (Objective 1 reference config C1 = basic sequence): amino-acid
sequence -> integer token ids. Pretrained ESM-2 / secondary-structure /
physicochemical enrichment is Objective 2 and is not applied here.
"""
from __future__ import annotations

import numpy as np
from rdkit import Chem

# --- atom vocabulary --------------------------------------------------------
ATOM_SYMBOLS = [
    "C", "N", "O", "S", "F", "Si", "P", "Cl", "Br", "Mg", "Na", "Ca", "Fe",
    "As", "Al", "I", "B", "V", "K", "Tl", "Yb", "Sb", "Sn", "Ag", "Pd", "Co",
    "Se", "Ti", "Zn", "H", "Li", "Ge", "Cu", "Au", "Ni", "Cd", "In", "Mn",
    "Zr", "Cr", "Pt", "Hg", "Pb", "other",
]
DEGREES = list(range(11))
NUM_HS = list(range(9))
IMPLICIT_VALENCE = list(range(7))
HYBRIDIZATIONS = [
    Chem.rdchem.HybridizationType.SP,
    Chem.rdchem.HybridizationType.SP2,
    Chem.rdchem.HybridizationType.SP3,
    Chem.rdchem.HybridizationType.SP3D,
    Chem.rdchem.HybridizationType.SP3D2,
    "other",
]
BOND_TYPES = [
    Chem.rdchem.BondType.SINGLE,
    Chem.rdchem.BondType.DOUBLE,
    Chem.rdchem.BondType.TRIPLE,
    Chem.rdchem.BondType.AROMATIC,
]
BOND_STEREO = [
    Chem.rdchem.BondStereo.STEREONONE,
    Chem.rdchem.BondStereo.STEREOANY,
    Chem.rdchem.BondStereo.STEREOZ,
    Chem.rdchem.BondStereo.STEREOE,
]

# Feature dimensions (consumed by the drug encoder, step 4)
ATOM_FEATURE_DIM = (
    len(ATOM_SYMBOLS) + len(DEGREES) + len(NUM_HS) + len(IMPLICIT_VALENCE)
    + len(HYBRIDIZATIONS) + 3  # formal charge, radical electrons, is_aromatic
)
BOND_FEATURE_DIM = len(BOND_TYPES) + len(BOND_STEREO) + 2  # conjugated, in_ring


def _one_hot(value, choices):
    """One-hot encode `value` over `choices`; last slot catches unknowns."""
    vec = [0.0] * len(choices)
    if value in choices:
        vec[choices.index(value)] = 1.0
    else:
        vec[-1] = 1.0  # 'other' / unknown bucket
    return vec


def _implicit_valence(atom) -> int:
    """Implicit valence, using the non-deprecated API when available."""
    try:  # RDKit >= 2024.x
        return int(atom.GetValence(Chem.ValenceType.IMPLICIT))
    except (AttributeError, TypeError):  # older RDKit
        return int(atom.GetImplicitValence())


def atom_features(atom) -> list[float]:
    feats: list[float] = []
    feats += _one_hot(atom.GetSymbol(), ATOM_SYMBOLS)
    feats += _one_hot(atom.GetDegree(), DEGREES)
    feats += _one_hot(atom.GetTotalNumHs(), NUM_HS)
    feats += _one_hot(_implicit_valence(atom), IMPLICIT_VALENCE)
    feats += _one_hot(atom.GetHybridization(), HYBRIDIZATIONS)
    feats += [float(atom.GetFormalCharge())]
    feats += [float(atom.GetNumRadicalElectrons())]
    feats += [1.0 if atom.GetIsAromatic() else 0.0]
    return feats


def bond_features(bond) -> list[float]:
    feats: list[float] = []
    feats += _one_hot(bond.GetBondType(), BOND_TYPES)
    feats += _one_hot(bond.GetStereo(), BOND_STEREO)
    feats += [1.0 if bond.GetIsConjugated() else 0.0]
    feats += [1.0 if bond.IsInRing() else 0.0]
    return feats


def smiles_to_graph(smiles: str) -> dict | None:
    """SMILES -> {node_feats [n,F], edge_index [2,E], edge_feats [E,Eb]}.

    Edges are stored bidirectionally (both (i,j) and (j,i)). Returns None if
    RDKit cannot parse the SMILES, so the caller can drop the pair.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or mol.GetNumAtoms() == 0:
        return None

    node_feats = np.array([atom_features(a) for a in mol.GetAtoms()], dtype=np.float32)

    src, dst, e_feats = [], [], []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        bf = bond_features(bond)
        src += [i, j]
        dst += [j, i]
        e_feats += [bf, bf]

    if len(src) == 0:  # single-atom molecule: no bonds
        edge_index = np.zeros((2, 0), dtype=np.int64)
        edge_feats = np.zeros((0, BOND_FEATURE_DIM), dtype=np.float32)
    else:
        edge_index = np.array([src, dst], dtype=np.int64)
        edge_feats = np.array(e_feats, dtype=np.float32)

    return {"node_feats": node_feats, "edge_index": edge_index, "edge_feats": edge_feats}


# --- protein (C1 basic sequence) -------------------------------------------
AA_VOCAB = "ACDEFGHIKLMNPQRSTVWY"  # 20 standard amino acids
# token 0 = padding, 1 = unknown/non-standard, 2..21 = amino acids
AA_TO_ID = {aa: i + 2 for i, aa in enumerate(AA_VOCAB)}
PAD_ID = 0
UNK_ID = 1
PROTEIN_VOCAB_SIZE = len(AA_VOCAB) + 2


def encode_protein(sequence: str, max_len: int = 1000) -> np.ndarray:
    """Amino-acid sequence -> int token ids (truncated to `max_len`)."""
    seq = (sequence or "").upper()[:max_len]
    ids = [AA_TO_ID.get(ch, UNK_ID) for ch in seq]
    return np.array(ids, dtype=np.int64)
