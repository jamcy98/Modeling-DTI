"""
Download Yamanishi_08 dataset (Enzyme, Ion Channel, GPCR, Nuclear Receptor)
using verified KEGG REST API endpoints.

KEGG BRITE IDs confirmed working:
  Enzyme      br:hsa00199  (gene entries at level C: "C    1543 CYP1A1; ...")
  GPCR        br:hsa04030  (gene entries at level D: "D      1128 CHRM1; ...")
  Ion Channel br:hsa04040  (gene entries at level C: "C    2554 GABRA1; ...")
  NR          link via hsa04915/hsa04919 NR-signaling pathways

Gene IDs in BRITE files are plain NCBI integers, converted to hsa:NNNNN for KEGG queries.

Run:
    python 05_download_yamanishi08.py

Output:
    raw/yamanishi_08/{e,ic,gpcr,nr}/
        mat_drug_protein.txt   (n_drugs x n_proteins, 0/1)
        drug_dict_map.txt      (KEGG Drug IDs, one per line)
        protein_dict_map.txt   (UniProt accessions, one per line)
"""

import os, re, time, sys, io
import numpy as np
import requests
from tqdm import tqdm

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.path.join(BASE_DIR, "raw", "yamanishi_08")
SUBS     = ["e", "ic", "gpcr", "nr"]

SESSION  = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 DTI-Research/1.0"})


# ── KEGG source definitions ───────────────────────────────────────────────────

# Each entry maps a sub-class to the correct KEGG data source
KEGG_SOURCES = {
    "e": {
        "label": "Enzyme",
        # link/hsa/enzyme gives "ec:...\thsa:NNNNN" — extract hsa IDs directly
        "gene_url": "https://rest.kegg.jp/link/hsa/enzyme",
        "gene_mode": "link_hsa",       # parse hsa:NNNNN from column 2
        "max_genes": 700,
    },
    "ic": {
        "label": "Ion Channel",
        # br:hsa04040 is confirmed to contain ion channel genes
        "gene_url": "https://rest.kegg.jp/get/br:hsa04040",
        "gene_mode": "brite_integer",  # parse integer gene IDs from BRITE
        "max_genes": 300,
    },
    "gpcr": {
        "label": "GPCR",
        # br:hsa04030 is confirmed to contain GPCR genes
        "gene_url": "https://rest.kegg.jp/get/br:hsa04030",
        "gene_mode": "brite_integer",
        "max_genes": 200,
    },
    "nr": {
        "label": "Nuclear Receptor",
        # link/hsa/hsa04919 returns "path:hsa04919\thsa:NNNNN" — col 2 is hsa ID
        "gene_url": "https://rest.kegg.jp/link/hsa/hsa04919",  # thyroid hormone signaling
        "gene_url2": "https://rest.kegg.jp/link/hsa/hsa04915", # estrogen signaling
        "gene_mode": "link_hsa",
        "max_genes": 60,
    },
}


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def fetch(url, timeout=20):
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code == 200 and len(r.content) > 10:
            return r.text
    except Exception:
        pass
    return None


def parse_genes(text, mode):
    """Extract hsa:NNNNN gene IDs from KEGG API response."""
    if not text:
        return []
    genes = set()

    if mode == "link_hsa":
        # Format: "ec:2.3.1.5\thsa:10"  → extract column 2
        for line in text.strip().split("\n"):
            parts = line.strip().split("\t")
            if len(parts) == 2 and parts[1].startswith("hsa:"):
                genes.add(parts[1])

    elif mode == "brite_integer":
        # Format: "C    1543 CYP1A1; ..." or "D      1128 CHRM1; ..."
        # Gene ID is the integer immediately after the level letter and whitespace
        for m in re.finditer(r'^[BCD]\s+(\d{2,9})\s+\w', text, re.MULTILINE):
            genes.add(f"hsa:{m.group(1)}")

    elif mode == "pathway_hsa":
        # KEGG pathway text has lines like: "hsa:2099" or "hsa:2100"
        for m in re.finditer(r'hsa:(\d+)', text):
            genes.add(f"hsa:{m.group(1)}")

    return sorted(genes)


def get_genes(sub):
    """Fetch gene list for a sub-class using the confirmed KEGG source."""
    src  = KEGG_SOURCES[sub]
    text = fetch(src["gene_url"])
    genes = parse_genes(text, src["gene_mode"])

    # Fallback for NR: try second URL
    if not genes and sub == "nr":
        text2 = fetch(src.get("gene_url2", ""))
        genes  = parse_genes(text2, src["gene_mode"])

    # Deduplicate and limit
    genes = sorted(set(genes))[:src["max_genes"]]
    return genes


# ── Drug lookup ───────────────────────────────────────────────────────────────

def get_drugs_for_gene(gene_id, delay=0.12):
    """Return list of KEGG Drug IDs that target this gene."""
    time.sleep(delay)
    text = fetch(f"https://rest.kegg.jp/link/drug/{gene_id}")
    if not text:
        return []
    drugs = []
    for line in text.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) == 2:
            dr = parts[1].replace("dr:", "").strip()
            if dr:
                drugs.append(dr)
    return drugs


# ── UniProt lookup ────────────────────────────────────────────────────────────

def gene_to_uniprot(gene_id, delay=0.12):
    """Convert hsa:NNNNN to UniProt accession via KEGG."""
    time.sleep(delay)
    text = fetch(f"https://rest.kegg.jp/conv/uniprot/{gene_id}")
    if text:
        for line in text.strip().split("\n"):
            parts = line.strip().split("\t")
            if len(parts) == 2:
                return parts[1].replace("up:", "").strip()
    return None


# ── Build one sub-class ───────────────────────────────────────────────────────

def build_subclass(sub):
    dst = os.path.join(RAW_DIR, sub)
    os.makedirs(dst, exist_ok=True)
    src = KEGG_SOURCES[sub]
    print(f"\n  [{sub}] {src['label']}")

    # 1. Get protein-family gene list
    print(f"  Fetching {src['label']} gene list from KEGG...")
    genes = get_genes(sub)
    if not genes:
        print(f"  Could not retrieve genes. Skipping {sub}.")
        return False
    print(f"  Found {len(genes)} genes (capped at {src['max_genes']}).")

    # 2. Get drugs for each gene
    print(f"  Fetching drug-target links...")
    gene_drug = {}
    for gene in tqdm(genes, desc=f"  Gene->Drug ({sub})"):
        drugs = get_drugs_for_gene(gene)
        if drugs:
            gene_drug[gene] = drugs

    if not gene_drug:
        print(f"  No drug-gene links found for {sub}.")
        return False

    all_drugs  = sorted(set(d for ds in gene_drug.values() for d in ds))
    all_genes  = sorted(gene_drug.keys())
    print(f"  Unique drugs: {len(all_drugs)}  |  Genes with drugs: {len(all_genes)}")

    # 3. Convert gene IDs to UniProt
    print(f"  Converting {len(all_genes)} gene IDs to UniProt...")
    gene_uid = {}
    for gene in tqdm(all_genes, desc=f"  KEGG->UniProt ({sub})"):
        uid = gene_to_uniprot(gene)
        if uid:
            gene_uid[gene] = uid

    valid_genes = [g for g in all_genes if g in gene_uid]
    uniprot_ids = [gene_uid[g] for g in valid_genes]
    print(f"  UniProt IDs resolved: {len(uniprot_ids)}/{len(all_genes)}")

    # 4. Build interaction matrix
    drug_idx = {d: i for i, d in enumerate(all_drugs)}
    gene_idx = {g: i for i, g in enumerate(valid_genes)}
    matrix   = np.zeros((len(all_drugs), len(valid_genes)), dtype=int)

    for gene, drugs in gene_drug.items():
        if gene not in gene_idx:
            continue
        for drug in drugs:
            if drug in drug_idx:
                matrix[drug_idx[drug], gene_idx[gene]] = 1

    pos = int(matrix.sum())
    print(f"  Matrix: {matrix.shape}  Positive interactions: {pos}")

    # 5. Save files
    np.savetxt(os.path.join(dst, "mat_drug_protein.txt"), matrix, fmt="%d")
    with open(os.path.join(dst, "drug_dict_map.txt"), "w") as f:
        f.write("\n".join(all_drugs))
    with open(os.path.join(dst, "protein_dict_map.txt"), "w") as f:
        f.write("\n".join(uniprot_ids))

    print(f"  Saved -> {dst}/")
    return pos > 0


# ── Main ──────────────────────────────────────────────────────────────────────

def already_done(sub):
    return os.path.exists(os.path.join(RAW_DIR, sub, "mat_drug_protein.txt"))


def main():
    print("=" * 55)
    print(" Yamanishi_08 Download — KEGG BRITE method")
    print("=" * 55)

    missing = [s for s in SUBS if not already_done(s)]
    if not missing:
        print("All sub-classes already present.")
    else:
        print(f"Building: {missing}\n")
        for sub in missing:
            build_subclass(sub)

    # Final status
    print("\n" + "=" * 55)
    print(" Final Status")
    print("=" * 55)
    for sub in SUBS:
        mp = os.path.join(RAW_DIR, sub, "mat_drug_protein.txt")
        if os.path.exists(mp):
            m = np.loadtxt(mp)
            print(f"  {sub:<5} DONE   {m.shape}  positives={int(m.sum())}")
        else:
            print(f"  {sub:<5} MISSING")

    print("\nNext step: python fetch_yamanishi_smiles_sequences.py")
    print("(enriches each sub-class with SMILES + protein sequences)")


if __name__ == "__main__":
    main()
