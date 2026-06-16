"""
Master script: run all preprocessing steps in order.

This script runs steps 10 through 13 in sequence:
  10 -> Drug graphs (SMILES -> molecular graphs + ChemBERTa)
  11 -> Protein embeddings (sequences -> ESM-2)
  12 -> Label files (interaction labels + negative sampling)
  13 -> Data splits (random, cold-drug, cold-target, cold-pair)

Run:
    python run_all_preprocessing.py              # run all steps
    python run_all_preprocessing.py --step 10    # run only step 10
    python run_all_preprocessing.py --skip 11    # skip step 11

Notes:
    - Step 11 (ESM-2) requires significant memory (~3 GB GPU VRAM or ~8 GB RAM).
    - Steps are skipped automatically if output files already exist.
    - Each step can also be run independently.
"""

import os
import sys
import time
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STEPS = {
    10: "10_preprocess_drugs.py",
    11: "11_preprocess_proteins.py",
    12: "12_preprocess_labels.py",
    13: "13_preprocess_splits.py",
}

STEP_NAMES = {
    10: "Drug graphs        (SMILES -> RDKit graphs + ChemBERTa embeddings)",
    11: "Protein embeddings (sequences -> ESM-2 residue embeddings)",
    12: "Label files        (interaction labels + negative sampling)",
    13: "Data splits        (random / cold-drug / cold-target / cold-pair)",
}


def run_step(step_number):
    script = os.path.join(BASE_DIR, STEPS[step_number])
    print(f"\n{'='*55}")
    print(f" STEP {step_number}: {STEP_NAMES[step_number]}")
    print(f"{'='*55}")

    if not os.path.exists(script):
        print(f"  ERROR: Script not found: {script}")
        return False

    start   = time.time()
    result  = subprocess.run([sys.executable, script], cwd=BASE_DIR)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n  FAILED (exit code {result.returncode}) after {elapsed:.1f}s")
        return False

    print(f"\n  Completed in {elapsed:.1f}s")
    return True


def print_summary(results):
    print(f"\n{'='*55}")
    print(" Summary")
    print(f"{'='*55}")
    for step, (success, elapsed) in results.items():
        status = "OK" if success else "FAILED"
        print(f"  Step {step}: {status:<8}  {STEP_NAMES[step]}")


def check_requirements():
    """Check that required packages are installed before starting."""
    required = {
        "torch":           "torch",
        "torch_geometric": "torch-geometric",
        "rdkit":           "rdkit",
        "transformers":    "transformers",
        "pandas":          "pandas",
        "numpy":           "numpy",
        "sklearn":         "scikit-learn",
        "tqdm":            "tqdm",
    }
    missing = []
    for module, pkg in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(pkg)

    if missing:
        print("Missing required packages. Install with:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOr install everything at once:")
        print("  pip install -r requirements.txt")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run all preprocessing steps.")
    parser.add_argument("--step", type=int, help="Run only this step number (10-13).")
    parser.add_argument("--skip", type=int, nargs="+",
                        help="Skip these step numbers (e.g. --skip 11).")
    args = parser.parse_args()

    print("=" * 55)
    print(" H-GNN-RNN-DTI  Data Preprocessing Pipeline")
    print("=" * 55)
    print(f" Base directory: {BASE_DIR}")
    print()

    check_requirements()

    steps_to_run = list(STEPS.keys())
    if args.step:
        if args.step not in STEPS:
            print(f"Invalid step: {args.step}. Choose from {list(STEPS.keys())}")
            sys.exit(1)
        steps_to_run = [args.step]
    if args.skip:
        steps_to_run = [s for s in steps_to_run if s not in args.skip]

    print(f"Steps to run: {steps_to_run}")

    results = {}
    for step in steps_to_run:
        t0      = time.time()
        success = run_step(step)
        results[step] = (success, time.time() - t0)
        if not success:
            print("\nPipeline stopped due to error. Fix the issue and re-run.")
            break

    print_summary(results)

    all_ok = all(s for s, _ in results.values())
    if all_ok:
        print("\nAll preprocessing complete. Your data is ready in:")
        print(f"  {os.path.join(BASE_DIR, 'processed')}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
