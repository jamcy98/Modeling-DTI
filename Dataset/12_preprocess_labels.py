"""
Preprocess interaction labels for all datasets.

For DTI datasets (binary classification):
  - Keeps known positive interactions (label = 1)
  - Generates negative samples using unknown-negative sampling (label = 0)
  - Supports 1:1 and 1:10 positive:negative ratios

For DTA datasets (regression):
  - Converts raw Kd/Ki/IC50 (nM) to pKd = -log10(value in Molar)
  - Builds the drug x protein affinity matrix in the format used by DeepDTA

Run:
    python 12_preprocess_labels.py

Output:
    processed/labels/{dataset}_dti_labels_1to1.csv      -> balanced DTI labels
    processed/labels/{dataset}_dti_labels_1to10.csv     -> imbalanced DTI labels
    processed/labels/{dataset}_dta_labels.csv           -> regression labels

Requirements:
    pip install pandas numpy scikit-learn tqdm
"""

import os
import json
import numpy as np
import pandas as pd
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.path.join(BASE_DIR, "raw")
OUT_DIR  = os.path.join(BASE_DIR, "processed", "labels")


# ── DTI label builders ────────────────────────────────────────────────────────

def negative_sample(positives_df, drug_ids, protein_ids, ratio, seed=42):
    """
    Generate negative drug–protein pairs that are NOT in the positive set.

    positives_df : DataFrame with columns ['drug_id', 'protein_id']
    ratio        : number of negatives per positive (e.g., 1 or 10)
    """
    rng          = np.random.default_rng(seed)
    pos_set      = set(zip(positives_df["drug_id"], positives_df["protein_id"]))
    n_negatives  = len(positives_df) * ratio

    drug_arr    = np.array(drug_ids)
    protein_arr = np.array(protein_ids)
    negatives   = []
    attempts    = 0
    max_attempts = n_negatives * 20

    while len(negatives) < n_negatives and attempts < max_attempts:
        d = rng.choice(drug_arr)
        p = rng.choice(protein_arr)
        if (d, p) not in pos_set:
            negatives.append({"drug_id": d, "protein_id": p, "label": 0})
        attempts += 1

    if len(negatives) < n_negatives:
        print(f"    WARNING: Could only generate {len(negatives)} negatives "
              f"(requested {n_negatives}). Drug/protein space may be too small.")

    return pd.DataFrame(negatives)


def build_dti_labels(name, interaction_matrix_path, drug_map_path, protein_map_path,
                     ratios=(1, 10)):
    """
    Build DTI label CSV from an interaction matrix file.
    Matrix file format: space/tab-separated, rows=drugs, columns=proteins, value 0/1.
    """
    if not os.path.exists(interaction_matrix_path):
        print(f"  Skipping {name}: matrix file not found at {interaction_matrix_path}")
        return

    print(f"\nBuilding DTI labels for {name}...")

    # Load interaction matrix
    matrix = np.loadtxt(interaction_matrix_path)
    n_drugs, n_proteins = matrix.shape
    print(f"  Matrix shape: {n_drugs} drugs x {n_proteins} proteins")

    # Load index-to-name mappings if available
    drug_ids    = [f"drug_{i}"    for i in range(n_drugs)]
    protein_ids = [f"protein_{j}" for j in range(n_proteins)]

    if os.path.exists(drug_map_path):
        with open(drug_map_path) as f:
            lines = [l.strip() for l in f if l.strip()]
        # Support two formats:
        #   "0\tDB00001"  (index-tab-id)
        #   "DB00001:DrugName"  (id:name, one per line — Luo_17 format)
        if lines and "\t" in lines[0]:
            drug_map = {int(l.split("\t")[0]): l.split("\t")[1] for l in lines}
            drug_ids = [drug_map.get(i, f"drug_{i}") for i in range(n_drugs)]
        else:
            # Each line is an entry; row index = line index
            drug_ids = [l.split(":")[0] for l in lines]

    if os.path.exists(protein_map_path):
        with open(protein_map_path) as f:
            lines = [l.strip() for l in f if l.strip()]
        if lines and "\t" in lines[0]:
            prot_map = {int(l.split("\t")[0]): l.split("\t")[1] for l in lines}
            protein_ids = [prot_map.get(j, f"protein_{j}") for j in range(n_proteins)]
        else:
            protein_ids = [l.split(":")[0] for l in lines]

    # Extract positive pairs
    rows, cols  = np.where(matrix == 1)
    positives   = pd.DataFrame({
        "drug_id":    [drug_ids[r] for r in rows],
        "protein_id": [protein_ids[c] for c in cols],
        "label":      1,
    })
    print(f"  Positive pairs: {len(positives):,}")
    print(f"  Negative space: {n_drugs * n_proteins - len(positives):,}")

    for ratio in ratios:
        negatives = negative_sample(positives, drug_ids, protein_ids, ratio)
        labels_df = pd.concat([positives, negatives], ignore_index=True)
        labels_df = labels_df.sample(frac=1, random_state=42).reset_index(drop=True)

        out_path  = os.path.join(OUT_DIR, f"{name}_dti_labels_1to{ratio}.csv")
        labels_df.to_csv(out_path, index=False)
        print(f"  Saved 1:{ratio} labels ({len(labels_df):,} pairs) -> {out_path}")


def build_davis_kiba_dta(name):
    """
    Load DAVIS or KIBA affinity matrix and convert to long-form DTA CSV.
    Y is stored as a Python pickle (binary), not JSON.
    """
    import pickle
    print(f"\nBuilding DTA labels for {name}...")
    dataset_dir = os.path.join(RAW_DIR, name)

    y_path        = os.path.join(dataset_dir, "Y")
    ligands_path  = os.path.join(dataset_dir, "ligands_can.txt")
    proteins_path = os.path.join(dataset_dir, "proteins.txt")

    if not os.path.exists(y_path):
        print(f"  Skipping {name}: Y file not found.")
        return

    with open(ligands_path)  as f: drugs    = json.load(f)
    with open(proteins_path) as f: proteins = json.load(f)
    with open(y_path, "rb")  as f: Y        = pickle.load(f, encoding="latin-1")

    drug_ids    = list(drugs.keys())
    protein_ids = list(proteins.keys())
    Y_arr       = np.array(Y)

    rows = []
    for i, drug_id in enumerate(drug_ids):
        for j, protein_id in enumerate(protein_ids):
            val = Y_arr[i, j]
            if not np.isnan(val):
                # DAVIS values are Kd in nM; KIBA has its own KIBA score
                if name == "davis":
                    pkd = -np.log10(val * 1e-9) if val > 0 else np.nan
                    rows.append({"drug_id": drug_id, "protein_id": protein_id,
                                 "kd_nM": val, "pKd": pkd})
                else:
                    rows.append({"drug_id": drug_id, "protein_id": protein_id,
                                 "kiba_score": val})

    df = pd.DataFrame(rows)

    if name == "davis":
        df = df.dropna(subset=["pKd"])
        df = df[(df["pKd"] >= 3) & (df["pKd"] <= 12)]
        print(f"  DTA pairs: {len(df):,}  |  pKd range: {df['pKd'].min():.2f}–{df['pKd'].max():.2f}")
    else:
        print(f"  DTA pairs: {len(df):,}  |  KIBA range: {df['kiba_score'].min():.2f}–{df['kiba_score'].max():.2f}")

    out_path = os.path.join(OUT_DIR, f"{name}_dta_labels.csv")
    df.to_csv(out_path, index=False)
    print(f"  Saved -> {out_path}")


def build_bindingdb_labels():
    print("\nBuilding BindingDB labels...")
    dti_path = os.path.join(RAW_DIR, "bindingdb", "BindingDB_DTI.csv")
    dta_path = os.path.join(RAW_DIR, "bindingdb", "BindingDB_DTA.csv")

    for src, suffix in [(dti_path, "dti_labels_1to1.csv"),
                        (dta_path, "dta_labels.csv")]:
        if os.path.exists(src):
            out = os.path.join(OUT_DIR, f"bindingdb_{suffix}")
            df  = pd.read_csv(src)

            if "label" in df.columns and "1to1" in suffix:
                # Already has binary labels from download step
                positives = df[df["label"] == 1].copy()
                negatives_raw = df[df["label"] == 0].copy()
                if len(negatives_raw) > len(positives):
                    negatives_raw = negatives_raw.sample(n=len(positives), random_state=42)
                df_balanced = pd.concat([positives, negatives_raw]).sample(
                    frac=1, random_state=42
                ).reset_index(drop=True)
                df_balanced.to_csv(out, index=False)
                print(f"  Saved balanced DTI -> {out}  ({len(df_balanced):,} pairs)")
            else:
                import shutil
                shutil.copy(src, out)
                print(f"  Copied DTA labels -> {out}")


def main():
    print("=" * 55)
    print(" Label Preprocessing")
    print("=" * 55)

    # DAVIS and KIBA — DTA regression
    for name in ["davis", "kiba"]:
        out = os.path.join(OUT_DIR, f"{name}_dta_labels.csv")
        if not os.path.exists(out):
            build_davis_kiba_dta(name)
        else:
            print(f"\n{name} DTA labels already exist — skipping.")

    # Yamanishi_08 sub-classes — DTI binary classification
    for sub in ["e", "ic", "gpcr", "nr"]:
        name         = f"yamanishi_{sub}"
        sub_dir      = os.path.join(RAW_DIR, "yamanishi_08", sub)
        matrix_path  = os.path.join(sub_dir, "mat_drug_protein.txt")
        drug_map     = os.path.join(sub_dir, "drug_dict_map.txt")
        protein_map  = os.path.join(sub_dir, "protein_dict_map.txt")

        out1 = os.path.join(OUT_DIR, f"{name}_dti_labels_1to1.csv")
        if not os.path.exists(out1):
            build_dti_labels(name, matrix_path, drug_map, protein_map, ratios=(1, 10))
        else:
            print(f"\n{name} DTI labels already exist — skipping.")

    # Luo_17 — DTI binary classification
    luo_matrix  = os.path.join(RAW_DIR, "luo_17", "mat_drug_protein.txt")
    luo_drug    = os.path.join(RAW_DIR, "luo_17", "drug_dict_map.txt")
    luo_protein = os.path.join(RAW_DIR, "luo_17", "protein_dict_map.txt")
    out_luo     = os.path.join(OUT_DIR, "luo_17_dti_labels_1to1.csv")
    if not os.path.exists(out_luo):
        build_dti_labels("luo_17", luo_matrix, luo_drug, luo_protein, ratios=(1, 10))
    else:
        print("\nluo_17 DTI labels already exist — skipping.")

    # BindingDB — both tasks
    build_bindingdb_labels()

    print("\nDone. Run 13_preprocess_splits.py next.")


if __name__ == "__main__":
    main()
