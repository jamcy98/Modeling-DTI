"""
Download and pre-filter the BindingDB dataset.
Source: https://www.bindingdb.org

Run:
    python 03_download_bindingdb.py

Output:
    raw/bindingdb/BindingDB_All.tsv       -> full filtered TSV
    raw/bindingdb/BindingDB_DTI.csv       -> binary interaction labels (Kd <= 10000 nM)
    raw/bindingdb/BindingDB_DTA.csv       -> affinity regression labels (pKd values)

Notes:
    - The full TSV download is ~3 GB. This may take several minutes.
    - Filtering keeps only rows with valid SMILES, UniProt ID, and at least one affinity value.
"""

import os
import gzip
import shutil
import requests
import pandas as pd
import numpy as np
from tqdm import tqdm

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
OUT_DIR      = os.path.join(BASE_DIR, "raw", "bindingdb")
DOWNLOAD_PAGE = "https://www.bindingdb.org/rwd/bind/chemsearch/marvin/Download.jsp"
BASE_URL     = "https://www.bindingdb.org"

# Affinity threshold for binary labelling: Kd <= 10,000 nM = positive interaction
AFFINITY_THRESHOLD_NM = 10000.0


SESSION_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": DOWNLOAD_PAGE,
}


def get_download_url():
    """Scrape BindingDB download page to find the latest All TSV ZIP URL."""
    import re
    print("Checking BindingDB download page for current URL...")
    r = requests.get(DOWNLOAD_PAGE, timeout=20, headers=SESSION_HEADERS)
    if r.status_code != 200:
        raise RuntimeError(f"Cannot reach BindingDB download page: HTTP {r.status_code}")

    # BindingDB now serves files at /rwd/bind/downloads/BindingDB_All_YYYYMM_tsv.zip
    matches = re.findall(
        r'/rwd/bind/downloads/(BindingDB_All_\d+_tsv\.zip)',
        r.text
    )
    if not matches:
        raise RuntimeError(
            "Could not find TSV download link on BindingDB page.\n"
            f"Visit {DOWNLOAD_PAGE} manually and download 'BindingDB_All_*_tsv.zip'.\n"
            "Save it as Dataset/raw/bindingdb/BindingDB_All.tsv.zip"
        )
    filename = sorted(set(matches))[-1]   # latest dated version
    url = f"{BASE_URL}/rwd/bind/downloads/{filename}"
    print(f"  Found: {filename}  ({url})")
    return url, filename


def download_file(url, dest_path):
    print(f"Downloading from:\n  {url}")
    print(f"Saving to:\n  {dest_path}\n")
    response = requests.get(url, stream=True, timeout=300,
                            allow_redirects=True, headers=SESSION_HEADERS)
    if response.status_code != 200:
        raise RuntimeError(
            f"Download failed. HTTP {response.status_code}\n"
            f"Visit {DOWNLOAD_PAGE} and download manually."
        )
    total = int(response.headers.get("content-length", 0))
    with open(dest_path, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc="Downloading"
    ) as bar:
        for chunk in response.iter_content(chunk_size=65536):
            f.write(chunk)
            bar.update(len(chunk))
    print("Download complete.")


def extract_zip(zip_path, out_dir):
    import zipfile
    print("Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        tsv_files = [n for n in names if n.lower().endswith(".tsv")]
        if not tsv_files:
            raise FileNotFoundError(f"No TSV file found inside {zip_path}. Contents: {names}")
        target = tsv_files[0]
        z.extract(target, out_dir)
        extracted = os.path.join(out_dir, target)
        canonical = os.path.join(out_dir, "BindingDB_All.tsv")
        if extracted != canonical:
            os.rename(extracted, canonical)
        print(f"  Extracted -> {canonical}")
    return canonical


def detect_columns(tsv_path):
    """Read only the header row to detect column names."""
    with open(tsv_path, encoding="utf-8", errors="replace") as f:
        header = f.readline().strip().split("\t")
    header = [h.strip() for h in header]

    smiles_col   = next((c for c in header if "smiles" in c.lower()), None)
    uniprot_col  = next((c for c in header if "uniprot" in c.lower()
                         and "swiss" in c.lower()), None)
    kd_col       = next((c for c in header if c.strip() == "Kd (nM)"), None)
    ki_col       = next((c for c in header if c.strip() == "Ki (nM)"), None)
    ic50_col     = next((c for c in header if c.strip() == "IC50 (nM)"), None)
    seq_col      = next((c for c in header if "sequence" in c.lower()), None)

    if not smiles_col or not uniprot_col:
        raise KeyError(
            f"Could not find required SMILES or UniProt columns.\n"
            f"First 20 columns: {header[:20]}"
        )

    affinity_cols = [c for c in [kd_col, ki_col, ic50_col] if c]
    print(f"  SMILES col   : {smiles_col}")
    print(f"  UniProt col  : {uniprot_col}")
    print(f"  Affinity cols: {affinity_cols}")
    return smiles_col, uniprot_col, affinity_cols, seq_col


def filter_data(tsv_path, chunk_size=200_000):
    """
    Filter the 8 GB TSV in chunks to avoid loading it all into RAM.
    Keeps only rows that have valid SMILES, UniProt ID, and at least one
    affinity value. Returns a concatenated filtered DataFrame.
    """
    print("\nScanning TSV header...")
    smiles_col, uniprot_col, affinity_cols, seq_col = detect_columns(tsv_path)

    keep_cols = [smiles_col, uniprot_col] + affinity_cols
    if seq_col:
        keep_cols.append(seq_col)

    print(f"  Reading in chunks of {chunk_size:,} rows (file is ~8 GB — please wait)...")
    chunks      = []
    total_read  = 0
    total_kept  = 0

    reader = pd.read_csv(
        tsv_path, sep="\t", low_memory=False,
        encoding="utf-8", on_bad_lines="skip",
        usecols=keep_cols, chunksize=chunk_size,
    )

    for i, chunk in enumerate(reader):
        chunk.columns = chunk.columns.str.strip()
        total_read += len(chunk)

        # Drop rows missing SMILES or UniProt
        chunk = chunk.dropna(subset=[smiles_col, uniprot_col])

        # Keep rows with at least one affinity value
        aff_present = [c for c in affinity_cols if c in chunk.columns]
        if aff_present:
            chunk = chunk[chunk[aff_present].notna().any(axis=1)]

        if len(chunk):
            # Compute best (minimum) affinity across Kd/Ki/IC50
            def best_aff(row):
                vals = pd.to_numeric(row[aff_present], errors="coerce").dropna()
                return vals.min() if len(vals) else np.nan

            chunk["_best_affinity"] = chunk.apply(best_aff, axis=1)
            chunks.append(chunk)
            total_kept += len(chunk)

        if (i + 1) % 5 == 0:
            print(f"    Chunks processed: {i+1}  |  rows read: {total_read:,}  |  kept: {total_kept:,}")

    print(f"\n  Total rows read : {total_read:,}")
    print(f"  Rows after filter: {total_kept:,}")

    df = pd.concat(chunks, ignore_index=True)

    # Deduplicate: keep most potent (lowest affinity) per drug–protein pair
    before = len(df)
    df = df.sort_values("_best_affinity").drop_duplicates(
        subset=[smiles_col, uniprot_col], keep="first"
    )
    print(f"  After deduplication: {len(df):,} unique pairs (removed {before - len(df):,})")

    return df, smiles_col, uniprot_col, affinity_cols, seq_col


def save_dti(df, smiles_col, uniprot_col, affinity_cols, out_path):
    """Binary interaction labels: positive if Kd <= threshold."""
    print("\nCreating binary DTI labels...")
    dti = df[[smiles_col, uniprot_col, "_best_affinity"]].copy()
    dti.columns = ["smiles", "uniprot_id", "best_affinity_nM"]
    dti["label"] = (dti["best_affinity_nM"] <= AFFINITY_THRESHOLD_NM).astype(int)

    pos = dti["label"].sum()
    neg = len(dti) - pos
    print(f"  Positives (Kd <= {AFFINITY_THRESHOLD_NM} nM): {pos:,}")
    print(f"  Negatives:                                   {neg:,}")
    print(f"  Ratio positive:negative = 1:{neg/max(pos,1):.1f}")

    dti.to_csv(out_path, index=False)
    print(f"  Saved -> {out_path}")


def save_dta(df, smiles_col, uniprot_col, out_path):
    """Regression labels: pKd = -log10(Kd in Molar)."""
    print("\nCreating regression DTA labels (pKd)...")
    dta = df[[smiles_col, uniprot_col, "_best_affinity"]].copy()
    dta.columns = ["smiles", "uniprot_id", "kd_nM"]
    dta = dta.dropna(subset=["kd_nM"])
    dta["kd_nM"] = pd.to_numeric(dta["kd_nM"], errors="coerce")
    dta = dta.dropna(subset=["kd_nM"])
    dta = dta[dta["kd_nM"] > 0]

    # Convert nM to Molar, then apply -log10
    dta["pKd"] = -np.log10(dta["kd_nM"] * 1e-9)

    # Remove extreme outliers (keep pKd between 3 and 12)
    before = len(dta)
    dta = dta[(dta["pKd"] >= 3) & (dta["pKd"] <= 12)]
    print(f"  Removed {before - len(dta):,} rows with pKd outside [3, 12]")
    print(f"  Final DTA rows: {len(dta):,}")
    print(f"  pKd range: {dta['pKd'].min():.2f} – {dta['pKd'].max():.2f}")

    dta.to_csv(out_path, index=False)
    print(f"  Saved -> {out_path}")


def main():
    print("=" * 55)
    print(" BindingDB Download & Pre-Filter")
    print("=" * 55)

    TSV_PATH = os.path.join(OUT_DIR, "BindingDB_All.tsv")

    if not os.path.exists(TSV_PATH):
        url, filename = get_download_url()
        zip_path = os.path.join(OUT_DIR, filename)
        if not os.path.exists(zip_path):
            download_file(url, zip_path)
        extract_zip(zip_path, OUT_DIR)
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print("Removed ZIP to save disk space.")
    else:
        print(f"TSV already exists — skipping download: {TSV_PATH}")

    # Filter
    df, smiles_col, uniprot_col, affinity_cols, seq_col = filter_data(TSV_PATH)

    # Save DTI and DTA label files
    save_dti(df, smiles_col, uniprot_col, affinity_cols,
             os.path.join(OUT_DIR, "BindingDB_DTI.csv"))
    save_dta(df, smiles_col, uniprot_col,
             os.path.join(OUT_DIR, "BindingDB_DTA.csv"))

    print("\nDone. Run 04_download_chembl.py next.")


if __name__ == "__main__":
    main()
