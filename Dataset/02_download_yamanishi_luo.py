"""
Download Yamanishi_08 (4 sub-classes) and Luo_17 datasets.

Sources:
  Yamanishi_08 -> DeepPurpose repo (kexinhuang12345) — includes SMILES + sequences
  Luo_17       -> DTINet repo (luoyunan) — heterogeneous network data

Run:
    python 02_download_yamanishi_luo.py

Output:
    raw/yamanishi_08/e/     -> pairs.csv (drug_smiles, protein_seq, label)
    raw/yamanishi_08/ic/
    raw/yamanishi_08/gpcr/
    raw/yamanishi_08/nr/
    raw/luo_17/             -> interaction matrix + similarity files
"""

import os
import stat
import shutil
import subprocess
import sys
import json
import requests
import pandas as pd

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
RAW_DIR        = os.path.join(BASE_DIR, "raw")
TEMP_DTINET    = os.path.join(BASE_DIR, "_tmp_dtinet")
TEMP_DEEPPURP  = os.path.join(BASE_DIR, "_tmp_deeppurpose")

DTINET_REPO    = "https://github.com/luoyunan/DTINet.git"
DEEPPURP_REPO  = "https://github.com/kexinhuang12345/DeepPurpose.git"

YAMANISHI_SUBS = ["enzyme", "ion_channel", "GPCR", "nuclear_receptor"]
SUB_SHORT      = {"enzyme": "e", "ion_channel": "ic", "GPCR": "gpcr", "nuclear_receptor": "nr"}

LUO17_FILES = [
    "mat_drug_protein.txt",
    "drug_dict_map.txt",
    "protein_dict_map.txt",
    "mat_drug_drug.txt",
    "mat_protein_protein.txt",
]


# ── helpers ───────────────────────────────────────────────────────────────────

def run(cmd):
    print(f"  >> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        sys.exit(1)


def _remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clone(url, dest, label):
    if os.path.exists(dest):
        print(f"{label} clone already exists — skipping.")
        return
    print(f"Cloning {label} repository...")
    run(f'git clone --depth 1 "{url}" "{dest}"')
    print("Clone complete.")


def copy_files(src_folder, dst_folder, filenames):
    os.makedirs(dst_folder, exist_ok=True)
    copied = []
    for fname in filenames:
        src = os.path.join(src_folder, fname)
        dst = os.path.join(dst_folder, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied.append(fname)
        else:
            print(f"    WARNING: {fname} not found — skipping.")
    return copied


# ── Luo_17 ────────────────────────────────────────────────────────────────────

def download_luo17():
    print("\nCopying Luo_17 from DTINet...")
    repo_data = os.path.join(TEMP_DTINET, "data")
    dst       = os.path.join(RAW_DIR, "luo_17")
    copied    = copy_files(repo_data, dst, LUO17_FILES)
    print(f"  luo_17/ -> {len(copied)} files: {copied}")


# ── Yamanishi_08 ──────────────────────────────────────────────────────────────

def find_yamanishi_data(repo_root):
    """Walk repo to find where Yamanishi sub-class folders live."""
    for root, dirs, _ in os.walk(repo_root):
        # DeepPurpose stores data inside DeepPurpose/data/
        for sub in YAMANISHI_SUBS:
            if sub in dirs:
                return root
    return None


def download_yamanishi_deeppurpose():
    """Extract Yamanishi_08 sub-class data from DeepPurpose repo."""
    print("\nCopying Yamanishi_08 from DeepPurpose...")

    # DeepPurpose data is inside DeepPurpose/data/
    data_root = None
    for candidate in [
        os.path.join(TEMP_DEEPPURP, "DeepPurpose", "data"),
        os.path.join(TEMP_DEEPPURP, "data"),
    ]:
        if os.path.isdir(candidate):
            data_root = candidate
            break

    # Also try walking
    if data_root is None:
        for root, dirs, _ in os.walk(TEMP_DEEPPURP):
            if any(s in dirs for s in YAMANISHI_SUBS):
                data_root = root
                break

    if data_root is None:
        print("  WARNING: Could not locate Yamanishi sub-class folders.")
        print(f"  Repo structure: {os.listdir(TEMP_DEEPPURP)}")
        download_yamanishi_fallback()
        return

    found = 0
    for full_name in YAMANISHI_SUBS:
        src     = os.path.join(data_root, full_name)
        short   = SUB_SHORT[full_name]
        dst_dir = os.path.join(RAW_DIR, "yamanishi_08", short)
        os.makedirs(dst_dir, exist_ok=True)

        if not os.path.isdir(src):
            print(f"  WARNING: {full_name}/ not found at {src}")
            continue

        files_copied = []
        for f in os.listdir(src):
            fp = os.path.join(src, f)
            if os.path.isfile(fp):
                shutil.copy2(fp, os.path.join(dst_dir, f))
                files_copied.append(f)
        print(f"  {short}/ ({full_name}) -> {len(files_copied)} files: {files_copied}")
        found += 1

    if found == 0:
        download_yamanishi_fallback()


def download_yamanishi_fallback():
    """
    Fallback: download Yamanishi_08 directly from raw GitHub content.
    Uses the ESPF (kexinhuang12345) benchmark data.
    """
    print("\n  Using fallback: downloading Yamanishi_08 from raw GitHub URLs...")

    BASE = "https://raw.githubusercontent.com/kexinhuang12345/ESPF/master/dataset/dti/"
    sub_map = {
        "e":    "biosnap",  # enzyme
        "nr":   "biosnap",
        "ic":   "biosnap",
        "gpcr": "biosnap",
    }

    # Alternative: try downloading from ESPF repo
    try:
        url_check = requests.get(
            "https://raw.githubusercontent.com/kexinhuang12345/ESPF/master/README.md",
            timeout=10
        )
        espf_ok = url_check.status_code == 200
    except Exception:
        espf_ok = False

    if not espf_ok:
        print("  WARNING: ESPF repo not reachable.")
        print("  Please download Yamanishi_08 manually:")
        print("    1. Go to https://github.com/kexinhuang12345/DeepPurpose")
        print("    2. Navigate to DeepPurpose/data/")
        print("    3. Copy enzyme/, ion_channel/, GPCR/, nuclear_receptor/ folders")
        print("    4. Paste into Dataset/raw/yamanishi_08/e|ic|gpcr|nr/")
        return

    # If ESPF is accessible, its datasets have train.csv / val.csv / test.csv
    # with columns: SMILES, Target Sequence, Label
    for sub in ["e", "ic", "gpcr", "nr"]:
        dst = os.path.join(RAW_DIR, "yamanishi_08", sub)
        os.makedirs(dst, exist_ok=True)
        print(f"    Placeholder created for {sub}/ — manual download needed.")


# ── main ─────────────────────────────────────────────────────────────────────

def cleanup():
    for tmp, label in [(TEMP_DTINET, "DTINet"), (TEMP_DEEPPURP, "DeepPurpose")]:
        if os.path.exists(tmp):
            print(f"Removing temporary clone: {label}...")
            shutil.rmtree(tmp, onexc=_remove_readonly)


def main():
    print("=" * 55)
    print(" Yamanishi_08 & Luo_17 Download")
    print("=" * 55)

    # Clone repos
    clone(DTINET_REPO,   TEMP_DTINET,   "DTINet")
    clone(DEEPPURP_REPO, TEMP_DEEPPURP, "DeepPurpose")

    # Download datasets
    download_luo17()
    download_yamanishi_deeppurpose()
    cleanup()

    # Summary
    print("\n" + "=" * 55)
    print(" File Summary")
    print("=" * 55)
    for sub in ["e", "ic", "gpcr", "nr"]:
        folder = os.path.join(RAW_DIR, "yamanishi_08", sub)
        files  = os.listdir(folder) if os.path.exists(folder) else []
        status = f"{len(files)} files: {files}" if files else "EMPTY — manual download needed"
        print(f"  yamanishi_08/{sub}/  -> {status}")

    luo_files = os.listdir(os.path.join(RAW_DIR, "luo_17"))
    print(f"  luo_17/  -> {len(luo_files)} files: {luo_files}")

    print("\nNote: SMILES for Luo_17/Yamanishi drugs will be fetched")
    print("      from PubChem during preprocessing (step 10).")
    print("\nDone. Run 03_download_bindingdb.py next.")


if __name__ == "__main__":
    main()
