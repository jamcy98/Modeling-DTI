"""Dataset acquisition for H-GNN-RNN-DTI (roadmap step 1).

Canonical, reproducible source = Therapeutics Data Commons (PyTDC) for the
affinity datasets. Binarization into interacting / non-interacting pairs is a
preprocessing concern (roadmap step 2, see labels.py) — this module only
acquires raw data and records a tidy schema.

Tidy schema (all datasets): Drug_ID, smiles, Target_ID, sequence, <value_col>.

Binarization conventions (applied later, in preprocessing):
  - DAVIS, BindingDB_Kd : value = Kd in nM; interacting iff Kd <= 30 nM  (direction "le")
  - KIBA                : value = KIBA score; interacting iff score >= 12.1 (direction "ge")
Yamanishi_08 and Luo_17 are already-binary interaction datasets and are NOT on
TDC — see UNAVAILABLE_ON_TDC.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

# --- dataset registry -------------------------------------------------------
# `reference` holds a known published size for a sanity check (informational).
DATASETS: dict[str, dict] = {
    "davis": dict(
        tdc_name="DAVIS", value_col="Kd_nM", threshold=30.0, direction="le",
        complete_matrix=True,
        reference=dict(n_pairs=25772, n_drugs=68, n_targets=379),  # TDC's packaged DAVIS
    ),
    "kiba": dict(
        tdc_name="KIBA", value_col="KIBA_score", threshold=12.1, direction="ge",
        complete_matrix=False, reference=None,
    ),
    "bindingdb_kd": dict(
        tdc_name="BindingDB_Kd", value_col="Kd_nM", threshold=30.0, direction="le",
        complete_matrix=False, reference=None,
    ),
}

# Not on TDC — downloaded separately via scripts/download_extra_datasets.py.
# These arrive as interaction matrices keyed by database IDs (KEGG / DrugBank /
# UniProt), NOT SMILES/sequences. `load_local_interactions` reads the parsed
# interaction list; an ID -> SMILES/FASTA mapping is still required before they
# can feed the H-GAT + Bi-LSTM model (see each data/raw/<name>/README_PROVENANCE.md).
LOCAL_ONLY: dict[str, str] = {
    "yamanishi_08": (
        "Yamanishi (2008) binary DTI dataset (Enzyme/IonChannel/GPCR/NuclearReceptor). "
        "KEGG IDs. Downloaded to data/raw/yamanishi_08/. Needs KEGG->SMILES and "
        "KEGG gene->UniProt->FASTA mapping. Primarily an Objective 2 (cold-start) dataset."
    ),
    "luo_17": (
        "Luo (2017)/DTINet dataset (708 drugs x 1512 proteins). DrugBank/UniProt IDs. "
        "Downloaded to data/raw/luo_17/. Needs DrugBank->SMILES and UniProt->FASTA mapping. "
        "Primarily an Objective 2 (cold-start) dataset."
    ),
}
# Backward-compat alias.
UNAVAILABLE_ON_TDC = LOCAL_ONLY

RAW_COLUMNS_BASE = ["Drug_ID", "smiles", "Target_ID", "sequence"]


def load_dti(name: str, root: str | Path = "data", save_raw: bool = True) -> pd.DataFrame:
    """Download a TDC DTI dataset and return a tidy dataframe.

    Columns: Drug_ID, smiles, Target_ID, sequence, <value_col>.
    Raw CSV cached to ``<root>/raw/<name>.csv``.
    """
    name = name.lower()
    if name in LOCAL_ONLY:
        raise NotImplementedError(
            f"'{name}' is not on TDC — download with "
            f"`python scripts/download_extra_datasets.py`, then read its interaction "
            f"list via load_local_interactions('{name}'). {LOCAL_ONLY[name]}"
        )
    if name not in DATASETS:
        raise KeyError(f"Unknown dataset '{name}'. Known: {list(DATASETS)}")

    meta = DATASETS[name]
    try:
        from tdc.multi_pred import DTI
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "PyTDC is required for dataset acquisition. Install with "
            "`uv pip install 'PyTDC==0.4.1'` (newer 1.x needs tiledbsoma, "
            "which won't build on Windows)."
        ) from e

    root = Path(root)
    tdc_dir = root / "raw" / "tdc"
    tdc_dir.mkdir(parents=True, exist_ok=True)

    data = DTI(name=meta["tdc_name"], path=str(tdc_dir))
    df = data.get_data()  # Drug_ID, Drug, Target_ID, Target, Y
    df = df.rename(columns={"Drug": "smiles", "Target": "sequence", "Y": meta["value_col"]})
    df = df[RAW_COLUMNS_BASE + [meta["value_col"]]]

    if save_raw:
        out = root / "raw" / f"{name}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)

    return df


def load_davis(root: str | Path = "data", save_raw: bool = True) -> pd.DataFrame:
    """Backward-compatible convenience wrapper."""
    return load_dti("davis", root=root, save_raw=save_raw)


def summarize(df: pd.DataFrame, name: str = "davis") -> dict:
    """Compute the quantities used for the step-1 'done' test."""
    value_col = DATASETS[name.lower()]["value_col"]
    return {
        "n_pairs": int(len(df)),
        "n_drugs": int(df["Drug_ID"].nunique()),
        "n_targets": int(df["Target_ID"].nunique()),
        f"{value_col}_min": float(df[value_col].min()),
        f"{value_col}_max": float(df[value_col].max()),
        "n_missing_smiles": int(df["smiles"].isna().sum()),
        "n_missing_sequence": int(df["sequence"].isna().sum()),
    }


def load_local_interactions(name: str, root: str | Path = "data") -> pd.DataFrame:
    """Read the parsed positive-interaction list for a locally-downloaded dataset.

    Returns columns: Drug_ID, Target_ID, label (+ class for yamanishi_08).
    NOTE: these are IDs only — smiles/sequence are NOT present and must be
    mapped from KEGG/DrugBank/UniProt before model use. See the dataset's
    README_PROVENANCE.md.
    """
    name = name.lower()
    if name not in LOCAL_ONLY:
        raise KeyError(f"'{name}' is not a local-only dataset. Known: {list(LOCAL_ONLY)}")
    path = Path(root) / "raw" / name / "interactions.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run `python scripts/download_extra_datasets.py` first."
        )
    return pd.read_csv(path)


# Backward-compat alias (old code referenced this name).
DAVIS_REFERENCE = DATASETS["davis"]["reference"]
