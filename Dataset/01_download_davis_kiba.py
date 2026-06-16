"""
Download DAVIS and KIBA datasets.
Source: DeepDTA GitHub repository (Ozturk et al., 2018)

Run:
    python 01_download_davis_kiba.py

Output:
    raw/davis/   -> Y, ligands_can.txt, proteins.txt
    raw/kiba/    -> Y, ligands_can.txt, proteins.txt
"""

import os
import shutil
import subprocess
import sys

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
RAW_DIR    = os.path.join(BASE_DIR, "raw")
TEMP_DIR   = os.path.join(BASE_DIR, "_tmp_deepdta")
REPO_URL   = "https://github.com/hkmztrk/DeepDTA.git"


def run(cmd):
    print(f"  >> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def clone_repo():
    if os.path.exists(TEMP_DIR):
        print("Temp clone already exists — skipping clone.")
        return
    print("Cloning DeepDTA repository...")
    run(f'git clone --depth 1 "{REPO_URL}" "{TEMP_DIR}"')
    print("Clone complete.")


def copy_dataset(name):
    src = os.path.join(TEMP_DIR, "data", name)
    dst = os.path.join(RAW_DIR, name)

    if not os.path.exists(src):
        print(f"  WARNING: Source folder not found: {src}")
        return

    print(f"Copying {name} dataset...")
    for fname in os.listdir(src):
        src_path = os.path.join(src, fname)
        dst_path = os.path.join(dst, fname)
        if os.path.isdir(src_path):
            if os.path.exists(dst_path):
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)
        print(f"  Copied: {fname}")
    print(f"  Done -> {dst}")


def _remove_readonly(func, path, _):
    """Error handler for rmtree: clear read-only flag then retry (needed on Windows)."""
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)


def cleanup():
    if os.path.exists(TEMP_DIR):
        print("Removing temporary clone...")
        shutil.rmtree(TEMP_DIR, onexc=_remove_readonly)


def main():
    print("=" * 55)
    print(" DAVIS & KIBA Download")
    print("=" * 55)

    clone_repo()
    copy_dataset("davis")
    copy_dataset("kiba")
    cleanup()

    print("\nFile summary:")
    for dataset in ["davis", "kiba"]:
        folder = os.path.join(RAW_DIR, dataset)
        files  = os.listdir(folder)
        print(f"  {dataset}/  -> {files if files else 'EMPTY — check errors above'}")

    print("\nDone. Run 02_download_yamanishi_luo.py next.")


if __name__ == "__main__":
    main()
