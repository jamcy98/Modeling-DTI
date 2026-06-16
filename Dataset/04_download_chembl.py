"""
Download ChEMBL database (SQLite version) and extract DTI/DTA records.
Source: https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/

Run:
    python 04_download_chembl.py

Output:
    raw/chembl/chembl.db           -> SQLite database file
    raw/chembl/chembl_DTI.csv      -> binary interaction labels
    raw/chembl/chembl_DTA.csv      -> affinity regression labels (pChEMBL values)

Notes:
    - The SQLite file is ~1.5 GB compressed / ~5 GB uncompressed.
    - ChEMBL version is detected automatically from the FTP index.
"""

import os
import re
import tarfile
import sqlite3
import requests
import pandas as pd
import numpy as np
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(BASE_DIR, "raw", "chembl")
FTP_BASE = "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/"

AFFINITY_THRESHOLD_NM = 10000.0   # Kd/Ki/IC50 <= this value = positive interaction


def get_latest_sqlite_filename():
    """Parse the FTP directory listing to find the latest SQLite tar.gz filename."""
    print("Checking FTP for latest ChEMBL version...")
    response = requests.get(FTP_BASE, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Could not access FTP: HTTP {response.status_code}")

    matches = re.findall(r'chembl_\d+_sqlite\.tar\.gz', response.text)
    if not matches:
        raise RuntimeError(
            "Could not detect ChEMBL SQLite filename from FTP index.\n"
            f"Check manually: {FTP_BASE}"
        )
    filename = sorted(set(matches))[-1]   # take the latest version
    print(f"  Latest version found: {filename}")
    return filename


def download_file(url, dest_path):
    print(f"Downloading:\n  {url}")
    response = requests.get(url, stream=True, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(f"Download failed. HTTP {response.status_code}")

    total = int(response.headers.get("content-length", 0))
    with open(dest_path, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc="Downloading"
    ) as bar:
        for chunk in response.iter_content(chunk_size=16384):
            f.write(chunk)
            bar.update(len(chunk))
    print("Download complete.")


def extract_sqlite(tar_path, out_dir):
    print("Extracting SQLite database...")
    db_path = None
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith(".db"):
                member.name = "chembl.db"   # normalise filename
                tar.extract(member, path=out_dir)
                db_path = os.path.join(out_dir, "chembl.db")
                print(f"  Extracted -> {db_path}")
                break
    if db_path is None:
        raise FileNotFoundError("No .db file found inside the tar archive.")
    return db_path


def query_chembl(db_path):
    print("\nQuerying ChEMBL database...")
    conn = sqlite3.connect(db_path)

    # ChEMBL 26+: activities does not have tid directly.
    # Must join through assays: activities -> assays -> target_dictionary -> target_components -> component_sequences
    query = """
    SELECT
        cs.canonical_smiles   AS smiles,
        cp.accession          AS uniprot_id,
        cp.sequence           AS protein_sequence,
        act.standard_type     AS assay_type,
        act.standard_value    AS value_nM,
        act.pchembl_value     AS pchembl_value
    FROM activities act
    JOIN compound_structures cs
        ON act.molregno = cs.molregno
    JOIN assays ay
        ON act.assay_id = ay.assay_id
    JOIN target_dictionary td
        ON ay.tid = td.tid
    JOIN target_components tc
        ON td.tid = tc.tid
    JOIN component_sequences cp
        ON tc.component_id = cp.component_id
    WHERE
        act.standard_type     IN ('IC50', 'Ki', 'Kd')
        AND act.standard_relation = '='
        AND act.standard_units    = 'nM'
        AND act.pchembl_value     IS NOT NULL
        AND cs.canonical_smiles   IS NOT NULL
        AND cp.accession          IS NOT NULL
        AND td.target_type        = 'SINGLE PROTEIN'
    """

    print("  Running query (may take 1–2 minutes)...")
    df = pd.read_sql(query, conn)
    conn.close()

    print(f"  Retrieved {len(df):,} records.")
    return df


def save_labels(df, out_dir):
    # Remove duplicates
    df = df.sort_values("value_nM", na_position="last")
    df = df.drop_duplicates(subset=["smiles", "uniprot_id"], keep="first")
    print(f"  After deduplication: {len(df):,} unique drug–protein pairs.")

    # Binary DTI labels
    dti = df[["smiles", "uniprot_id", "value_nM"]].copy()
    dti["label"] = (dti["value_nM"] <= AFFINITY_THRESHOLD_NM).astype(int)
    dti_path = os.path.join(out_dir, "chembl_DTI.csv")
    dti.to_csv(dti_path, index=False)
    print(f"  DTI saved  -> {dti_path}")
    print(f"     Positives: {dti['label'].sum():,}  |  Negatives: {(dti['label']==0).sum():,}")

    # Regression DTA labels (use pChEMBL directly)
    dta = df[["smiles", "uniprot_id", "pchembl_value"]].dropna().copy()
    dta.columns = ["smiles", "uniprot_id", "pchembl"]
    dta = dta[(dta["pchembl"] >= 3) & (dta["pchembl"] <= 12)]
    dta_path = os.path.join(out_dir, "chembl_DTA.csv")
    dta.to_csv(dta_path, index=False)
    print(f"  DTA saved  -> {dta_path}")
    print(f"     Records: {len(dta):,}  |  pChEMBL range: {dta['pchembl'].min():.2f} – {dta['pchembl'].max():.2f}")


def main():
    print("=" * 55)
    print(" ChEMBL Download & Extraction")
    print("=" * 55)

    db_path = os.path.join(OUT_DIR, "chembl.db")

    if not os.path.exists(db_path):
        filename   = get_latest_sqlite_filename()
        tar_path   = os.path.join(OUT_DIR, filename)
        url        = FTP_BASE + filename

        if not os.path.exists(tar_path):
            download_file(url, tar_path)

        db_path = extract_sqlite(tar_path, OUT_DIR)

        # Remove tar to save disk space
        os.remove(tar_path)
        print("Removed .tar.gz file to save disk space.")
    else:
        print(f"SQLite database already exists: {db_path}")

    df = query_chembl(db_path)
    save_labels(df, OUT_DIR)

    print("\nDone.")
    print("NOTE: DrugBank requires manual registration at https://go.drugbank.com")
    print("      See the instructions at the top of the analysis plan.")


if __name__ == "__main__":
    main()
