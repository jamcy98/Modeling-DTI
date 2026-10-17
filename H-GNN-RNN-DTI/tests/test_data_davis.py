"""Checks for the acquired DAVIS data (roadmap step 1).

Validates the cached raw CSV (fast, no network). Skips if it hasn't been
downloaded yet (run scripts/download_data.py --dataset davis).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hgnn_rnn_dti.data.datasets import DATASETS, summarize

RAW = ROOT / "data" / "raw" / "davis.csv"


@pytest.mark.skipif(not RAW.exists(), reason="run scripts/download_data.py --dataset davis first")
def test_davis_cached_schema_and_size():
    df = pd.read_csv(RAW)

    # schema
    for col in ["Drug_ID", "smiles", "Target_ID", "sequence", "Kd_nM"]:
        assert col in df.columns

    # completeness
    assert df["smiles"].isna().sum() == 0
    assert df["sequence"].isna().sum() == 0

    # counts match this project's ground truth (TDC DAVIS = 68 x 379)
    stats = summarize(df, "davis")
    ref = DATASETS["davis"]["reference"]
    assert stats["n_pairs"] == ref["n_pairs"] == 25772
    assert stats["n_drugs"] == ref["n_drugs"] == 68
    assert stats["n_targets"] == ref["n_targets"] == 379
    assert stats["Kd_nM_min"] > 0
