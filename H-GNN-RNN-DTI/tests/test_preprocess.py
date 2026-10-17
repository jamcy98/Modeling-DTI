"""Unit checks for step-2 preprocessing: featurization, labels, split leakage.

These are dependency-light (RDKit + NumPy + pandas) and run without the full
DL stack.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hgnn_rnn_dti.data import featurize as F
from hgnn_rnn_dti.data.labels import binarize, class_balance
from hgnn_rnn_dti.data.splits import check_entity_leakage, check_pair_leakage, warm_start_split, cold_entity_split


def test_smiles_to_graph_ethanol():
    g = F.smiles_to_graph("CCO")  # ethanol: 3 atoms, 2 bonds -> 4 directed edges
    assert g is not None
    assert g["node_feats"].shape == (3, F.ATOM_FEATURE_DIM)
    assert g["edge_index"].shape == (2, 4)
    assert g["edge_feats"].shape == (4, F.BOND_FEATURE_DIM)


def test_smiles_to_graph_invalid():
    assert F.smiles_to_graph("not_a_smiles") is None


def test_encode_protein_truncates_and_maps():
    ids = F.encode_protein("ACDEFGHIKLMNPQRSTVWY", max_len=10)
    assert ids.shape == (10,)
    assert ids.min() >= F.PAD_ID and ids.max() < F.PROTEIN_VOCAB_SIZE
    # unknown residue -> UNK_ID
    assert F.encode_protein("ZZZ")[0] == F.UNK_ID


def test_binarize_directions():
    vals = np.array([10.0, 30.0, 100.0])
    assert binarize(vals, 30.0, "le").tolist() == [1, 1, 0]
    assert binarize(vals, 30.0, "ge").tolist() == [0, 1, 1]


def test_warm_start_no_pair_leakage():
    rng = np.random.default_rng(0)
    n = 500
    df = pd.DataFrame({
        "Drug_ID": rng.integers(0, 20, n),
        "Target_ID": rng.integers(0, 20, n),
        "label": rng.integers(0, 2, n),
    }).drop_duplicates(["Drug_ID", "Target_ID"]).reset_index(drop=True)
    df["split"] = warm_start_split(df["label"].to_numpy(), seed=42)
    check_pair_leakage(df)  # must not raise
    assert set(df["split"]) <= {"train", "val", "test"}


def test_cold_drug_entity_disjoint():
    rng = np.random.default_rng(1)
    n = 500
    df = pd.DataFrame({
        "Drug_ID": rng.integers(0, 30, n),
        "Target_ID": rng.integers(0, 30, n),
    })
    df["split"] = cold_entity_split(df["Drug_ID"].to_numpy(), seed=7)
    check_entity_leakage(df, "Drug_ID")  # must not raise


def test_class_balance():
    b = class_balance(np.array([1, 1, 0, 0, 0]))
    assert b == {"n": 5, "positives": 2, "negatives": 3, "positive_rate": 0.4}
