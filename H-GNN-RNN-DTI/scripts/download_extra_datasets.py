"""Download the non-TDC benchmark datasets: Yamanishi (2008) and Luo (2017/DTINet).

Both are network/similarity datasets distributed as interaction matrices keyed by
database IDs (KEGG for Yamanishi; DrugBank/UniProt for Luo) — NOT SMILES/FASTA.
This script downloads the raw files, parses them into tidy interaction lists
(Drug_ID, Target_ID, label), reports stats, and writes a provenance note that
spells out the ID -> SMILES / FASTA mapping still required before these datasets
can feed the H-GAT (needs SMILES) + Bi-LSTM (needs sequences) model.

Usage:
    python scripts/download_extra_datasets.py --root data
"""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

import pandas as pd

UA = {"User-Agent": "Mozilla/5.0"}

YAMANISHI_BASE = "http://web.kuicr.kyoto-u.ac.jp/supp/yoshi/drugtarget/"
YAMANISHI_CLASSES = ["e", "ic", "gpcr", "nr"]
YAMANISHI_SUFFIXES = ["admat_dgc", "simmat_dc", "simmat_dg"]

LUO_BASE = "https://raw.githubusercontent.com/luoyunan/DTINet/master/data/"
LUO_FILES = [
    "drug.txt", "protein.txt", "drug_dict_map.txt", "protein_dict_map.txt",
    "mat_drug_protein.txt", "mat_drug_protein_remove_homo.txt",
]  # core DTI files; repo also has disease/side-effect/similarity matrices (not needed here)


def _download(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    dest.write_bytes(data)
    return len(data)


def fetch_yamanishi(root: Path) -> None:
    out = root / "raw" / "yamanishi_08"
    print("=== Yamanishi (2008) — Kyoto ===")
    all_inter = []
    for cls in YAMANISHI_CLASSES:
        for suf in YAMANISHI_SUFFIXES:
            fname = f"{cls}_{suf}.txt"
            n = _download(YAMANISHI_BASE + fname, out / fname)
            print(f"  downloaded {fname} ({n:,} bytes)")
        # parse interaction adjacency matrix
        adm = pd.read_csv(out / f"{cls}_admat_dgc.txt", sep="\t", index_col=0)
        # columns are drugs (D#####) in this distribution; rows are genes (hsa####)
        cols_are_drugs = str(adm.columns[0]).startswith("D")
        drug_axis, target_axis = ("col", "row") if cols_are_drugs else ("row", "col")
        stacked = adm.stack()
        pos = stacked[stacked == 1]
        inter = pd.DataFrame({
            "Drug_ID": (pos.index.get_level_values(1) if drug_axis == "col"
                        else pos.index.get_level_values(0)),
            "Target_ID": (pos.index.get_level_values(0) if target_axis == "row"
                          else pos.index.get_level_values(1)),
        })
        inter["label"] = 1
        inter["class"] = cls
        all_inter.append(inter)
        print(f"  [{cls}] matrix {adm.shape} -> {len(inter)} positive interactions "
              f"({adm.shape[1] if cols_are_drugs else adm.shape[0]} drugs, "
              f"{adm.shape[0] if cols_are_drugs else adm.shape[1]} targets)")
    combined = pd.concat(all_inter, ignore_index=True)
    combined.to_csv(out / "interactions.csv", index=False)
    print(f"  -> {out/'interactions.csv'} ({len(combined)} positive interactions, 4 classes)")
    _write_readme_yamanishi(out)


def fetch_luo(root: Path) -> None:
    out = root / "raw" / "luo_17"
    print("\n=== Luo (2017) — DTINet GitHub ===")
    for fname in LUO_FILES:
        n = _download(LUO_BASE + fname, out / fname)
        print(f"  downloaded {fname} ({n:,} bytes)")

    drugs = (out / "drug.txt").read_text(encoding="utf-8").split("\n")
    drugs = [d.strip() for d in drugs if d.strip()]
    proteins = (out / "protein.txt").read_text(encoding="utf-8").split("\n")
    proteins = [p.strip() for p in proteins if p.strip()]

    mat = pd.read_csv(out / "mat_drug_protein.txt", sep=r"\s+", header=None).to_numpy()
    print(f"  mat_drug_protein shape {mat.shape} "
          f"(drug.txt={len(drugs)} ids, protein.txt={len(proteins)} ids)")
    rows, cols = mat.nonzero()
    inter = pd.DataFrame({
        "Drug_ID": [drugs[r] if r < len(drugs) else f"row{r}" for r in rows],
        "Target_ID": [proteins[c] if c < len(proteins) else f"col{c}" for c in cols],
        "label": 1,
    })
    inter.to_csv(out / "interactions.csv", index=False)
    print(f"  -> {out/'interactions.csv'} ({len(inter)} positive interactions)")
    _write_readme_luo(out)


def _write_readme_yamanishi(out: Path) -> None:
    (out / "README_PROVENANCE.md").write_text(
        "# Yamanishi (2008) — provenance & what remains\n\n"
        f"Source: {YAMANISHI_BASE}\n\n"
        "Four target classes: e (enzyme), ic (ion channel), gpcr, nr (nuclear receptor).\n"
        "Files per class: `{cls}_admat_dgc.txt` (drug x target interaction matrix), "
        "`{cls}_simmat_dc.txt` (drug-drug chemical similarity), "
        "`{cls}_simmat_dg.txt` (target-target sequence similarity).\n\n"
        "IDs: drugs are **KEGG DRUG** ids (D#####); targets are **KEGG gene** ids (hsa####).\n"
        "`interactions.csv` is the tidy positive-interaction list (Drug_ID, Target_ID, label, class).\n\n"
        "## Still required before this feeds the H-GAT + Bi-LSTM model\n"
        "- Drug SMILES: map KEGG DRUG D##### -> SMILES (KEGG REST / PubChem).\n"
        "- Protein sequence: map KEGG gene hsa#### -> UniProt -> FASTA.\n"
        "- Negatives: the matrices give positives; sample negatives AFTER splitting "
        "(see src/hgnn_rnn_dti/data/splits.py `sample_negatives`).\n"
        "- This is a cold-start / network dataset — primarily Objective 2, not Objective 1.\n",
        encoding="utf-8",
    )


def _write_readme_luo(out: Path) -> None:
    (out / "README_PROVENANCE.md").write_text(
        "# Luo (2017) / DTINet — provenance & what remains\n\n"
        "Source: https://github.com/luoyunan/DTINet (data/ folder)\n\n"
        "Core DTI files downloaded: drug.txt (DrugBank ids), protein.txt (UniProt ids), "
        "drug_dict_map.txt / protein_dict_map.txt (id -> name maps), "
        "mat_drug_protein.txt (708 x 1512 binary interaction matrix), "
        "mat_drug_protein_remove_homo.txt (same, with homologous proteins removed — the "
        "standard setting for unbiased evaluation).\n"
        "Row order = drug.txt; column order = protein.txt. `interactions.csv` is the tidy "
        "positive-interaction list (Drug_ID, Target_ID, label).\n\n"
        "The repo also contains disease / side-effect / similarity matrices used by the "
        "DTINet network method; they are NOT downloaded here because our sequence/graph model "
        "does not use them.\n\n"
        "## Still required before this feeds the H-GAT + Bi-LSTM model\n"
        "- Drug SMILES: map DrugBank id -> SMILES (DrugBank export / PubChem).\n"
        "- Protein sequence: map UniProt id -> FASTA (UniProt REST).\n"
        "- Negatives: sample from the 0-cells AFTER splitting.\n"
        "- Prefer `mat_drug_protein_remove_homo.txt` for cold-start evaluation.\n"
        "- This is a cold-start / network dataset — primarily Objective 2, not Objective 1.\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--skip-yamanishi", action="store_true")
    ap.add_argument("--skip-luo", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    if not args.skip_yamanishi:
        fetch_yamanishi(root)
    if not args.skip_luo:
        fetch_luo(root)
    print("\nDownloaded. NOTE: both are ID/matrix datasets; SMILES + FASTA mapping is still "
          "required before model use (see each README_PROVENANCE.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
