"""
Fetch SMILES strings and protein sequences for Yamanishi_08 sub-classes.

After you have placed the interaction matrix files in:
    Dataset/raw/yamanishi_08/e/
    Dataset/raw/yamanishi_08/ic/
    Dataset/raw/yamanishi_08/gpcr/
    Dataset/raw/yamanishi_08/nr/

Run this script to enrich them with SMILES (from PubChem) and
protein sequences (from UniProt), producing a ready-to-use pairs.csv
in each sub-folder.

Run:
    python fetch_yamanishi_smiles_sequences.py

Output per sub-class:
    raw/yamanishi_08/{sub}/pairs.csv
        columns: drug_id, smiles, protein_id, sequence, label
"""

import os
import time
import requests
import numpy as np
import pandas as pd
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.path.join(BASE_DIR, "raw", "yamanishi_08")
SUBS     = ["e", "ic", "gpcr", "nr"]


# ── API helpers ───────────────────────────────────────────────────────────────

def _smiles_from_props(props):
    """Extract SMILES from a PubChem PropertyTable Properties dict, trying multiple key names."""
    for key in ("CanonicalSMILES", "IsomericSMILES", "SMILES", "ConnectivitySMILES"):
        if key in props:
            return props[key]
    return None


def fetch_smiles_pubchem(drug_id, retries=3):
    """
    Fetch canonical SMILES for a KEGG Drug ID (e.g. D00001).

    Strategy for KEGG Drug IDs (D#####):
      1. KEGG conv API → PubChem SID
      2. PubChem SID  → PubChem CID
      3. PubChem CID  → SMILES

    Fallback for any ID: PubChem name/synonym search.
    """
    if drug_id.upper().startswith("D") and drug_id[1:].isdigit():
        for _ in range(retries):
            try:
                # Step 1: KEGG Drug ID → PubChem SID
                # Response format: "dr:D00001\tpubchem:7847069"
                r = requests.get(
                    f"https://rest.kegg.jp/conv/pubchem/drug:{drug_id}",
                    timeout=10,
                )
                if r.status_code == 200 and r.text.strip():
                    parts = r.text.strip().split("\t")
                    if len(parts) == 2 and parts[1].startswith("pubchem:"):
                        sid = parts[1].replace("pubchem:", "").strip()

                        # Step 2: SID → CID
                        r2 = requests.get(
                            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug"
                            f"/substance/sid/{sid}/cids/JSON",
                            timeout=10,
                        )
                        if r2.status_code == 200:
                            cids = (
                                r2.json()
                                .get("InformationList", {})
                                .get("Information", [{}])[0]
                                .get("CID", [])
                            )
                            if cids:
                                # Step 3: CID → SMILES
                                r3 = requests.get(
                                    f"https://pubchem.ncbi.nlm.nih.gov/rest/pug"
                                    f"/compound/cid/{cids[0]}"
                                    f"/property/CanonicalSMILES,IsomericSMILES/JSON",
                                    timeout=10,
                                )
                                if r3.status_code == 200:
                                    props = r3.json()["PropertyTable"]["Properties"][0]
                                    smiles = _smiles_from_props(props)
                                    if smiles:
                                        return smiles
            except Exception:
                pass
            time.sleep(0.3)

    # Fallback: PubChem name/synonym search (handles non-KEGG IDs)
    for _ in range(retries):
        try:
            r = requests.get(
                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug"
                f"/compound/name/{drug_id}/property/CanonicalSMILES,IsomericSMILES/JSON",
                timeout=10,
            )
            if r.status_code == 200:
                props = r.json()["PropertyTable"]["Properties"][0]
                smiles = _smiles_from_props(props)
                if smiles:
                    return smiles
        except Exception:
            pass
        time.sleep(0.3)
    return None


def fetch_sequence_uniprot(uniprot_id, retries=3):
    """Fetch protein FASTA sequence from UniProt by accession ID."""
    for attempt in range(retries):
        try:
            url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                return "".join(lines[1:])   # skip FASTA header line
        except Exception:
            pass
        time.sleep(0.5)
    return None


# ── Per sub-class processing ──────────────────────────────────────────────────

def load_ids(map_path):
    """
    Load drug or protein IDs from a dict_map file.
    Supports two formats:
      - "DB00001:DrugName"  (one ID per line, colon-separated)
      - "0\\tDB00001"       (index tab ID)
    """
    if not os.path.exists(map_path):
        return []
    with open(map_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        return []
    if "\t" in lines[0]:
        return [l.split("\t")[1].split(":")[0] for l in lines]
    return [l.split(":")[0] for l in lines]


def process_subclass(sub):
    sub_dir  = os.path.join(RAW_DIR, sub)
    out_path = os.path.join(sub_dir, "pairs.csv")

    if os.path.exists(out_path):
        df = pd.read_csv(out_path)
        print(f"  {sub}/ already has pairs.csv ({len(df)} pairs) — skipping.")
        return

    matrix_path  = os.path.join(sub_dir, "mat_drug_protein.txt")
    drug_map     = os.path.join(sub_dir, "drug_dict_map.txt")
    protein_map  = os.path.join(sub_dir, "protein_dict_map.txt")

    if not os.path.exists(matrix_path):
        print(f"  {sub}/ — mat_drug_protein.txt not found. Skipping.")
        print(f"    Place interaction files in: {sub_dir}")
        return

    print(f"\nProcessing sub-class: {sub}")

    # Load interaction matrix
    matrix      = np.loadtxt(matrix_path)
    drug_ids    = load_ids(drug_map)    or [f"drug_{i}"    for i in range(matrix.shape[0])]
    protein_ids = load_ids(protein_map) or [f"protein_{j}" for j in range(matrix.shape[1])]

    n_drugs, n_proteins = matrix.shape
    print(f"  Matrix: {n_drugs} drugs × {n_proteins} proteins")
    print(f"  Positive interactions: {int(matrix.sum())}")

    # Build pair list
    rows, cols = np.where(matrix == 1)
    pos_pairs  = [(drug_ids[r], protein_ids[c], 1) for r, c in zip(rows, cols)]
    # Negative pairs (sample equal number)
    rng        = np.random.default_rng(42)
    neg_pairs  = []
    pos_set    = set((drug_ids[r], protein_ids[c]) for r, c in zip(rows, cols))
    while len(neg_pairs) < len(pos_pairs):
        d = drug_ids[rng.integers(n_drugs)]
        p = protein_ids[rng.integers(n_proteins)]
        if (d, p) not in pos_set:
            neg_pairs.append((d, p, 0))
    all_pairs = pos_pairs + neg_pairs

    # Fetch SMILES for unique drugs
    unique_drugs = list(set(d for d, _, _ in all_pairs))
    print(f"  Fetching SMILES for {len(unique_drugs)} unique drugs from PubChem...")
    smiles_map = {}
    for did in tqdm(unique_drugs, desc=f"  PubChem ({sub})"):
        smiles = fetch_smiles_pubchem(did)
        if smiles:
            smiles_map[did] = smiles
        time.sleep(0.1)    # respect rate limit
    print(f"  SMILES found: {len(smiles_map)}/{len(unique_drugs)}")

    # Fetch sequences for unique proteins
    unique_proteins = list(set(p for _, p, _ in all_pairs))
    print(f"  Fetching sequences for {len(unique_proteins)} proteins from UniProt...")
    seq_map = {}
    for pid in tqdm(unique_proteins, desc=f"  UniProt ({sub})"):
        seq = fetch_sequence_uniprot(pid)
        if seq:
            seq_map[pid] = seq
        time.sleep(0.1)
    print(f"  Sequences found: {len(seq_map)}/{len(unique_proteins)}")

    # Build final DataFrame
    records = []
    for drug_id, protein_id, label in all_pairs:
        smiles = smiles_map.get(drug_id)
        seq    = seq_map.get(protein_id)
        if smiles and seq:    # only keep rows with both
            records.append({
                "drug_id":    drug_id,
                "smiles":     smiles,
                "protein_id": protein_id,
                "sequence":   seq,
                "label":      label,
            })

    df = pd.DataFrame(records)
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df)} pairs (with SMILES + sequence) -> {out_path}")
    print(f"  Dropped {len(all_pairs) - len(df)} pairs with missing SMILES or sequence.")


def main():
    print("=" * 55)
    print(" Yamanishi_08 SMILES + Sequence Enrichment")
    print("=" * 55)
    print("This script fetches SMILES from PubChem and sequences")
    print("from UniProt for each drug-protein pair.")
    print("Ensure you have internet access before running.\n")

    any_found = False
    for sub in SUBS:
        matrix = os.path.join(RAW_DIR, sub, "mat_drug_protein.txt")
        if os.path.exists(matrix):
            any_found = True
            process_subclass(sub)
        else:
            print(f"  {sub}/ — no interaction matrix found. Skipping.")

    if not any_found:
        print("\nNo interaction matrix files found in any sub-class folder.")
        print("Please download them first from one of these sources:")
        print()
        print("  1. DTKGIN paper GitHub (Luo et al., 2024):")
        print("     Search: github.com search 'DTKGIN drug target'")
        print()
        print("  2. Original Yamanishi lab page:")
        print("     http://web.kuicr.kyoto-u.ac.jp/supp/yoshi/drugtarget/")
        print()
        print("  3. DTINet repo (already cloned) — combined data only:")
        print("     Dataset/raw/luo_17/mat_drug_protein.txt")
        print()
        print("Place the following files in each sub-folder and re-run:")
        print("  Dataset/raw/yamanishi_08/e/mat_drug_protein.txt")
        print("  Dataset/raw/yamanishi_08/e/drug_dict_map.txt")
        print("  Dataset/raw/yamanishi_08/e/protein_dict_map.txt")
        print("  (same for ic/, gpcr/, nr/)")
    else:
        print("\nDone. Run 12_preprocess_labels.py and 13_preprocess_splits.py")
        print("again to include Yamanishi_08 in the label and split files.")


if __name__ == "__main__":
    main()
