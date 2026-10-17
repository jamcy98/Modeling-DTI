"""Roadmap step 1: download + sanity-check benchmark datasets.

Usage:
    python scripts/download_data.py --dataset davis
    python scripts/download_data.py --dataset all        # all TDC-available
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hgnn_rnn_dti.data.datasets import (  # noqa: E402
    DATASETS,
    UNAVAILABLE_ON_TDC,
    load_dti,
    summarize,
)


def _report(name: str, root: str) -> None:
    print(f"\n=== {name} ===")
    print(f"Downloading via PyTDC into {root}/raw/ ...")
    df = load_dti(name, root=root)
    stats = summarize(df, name)
    for k, v in stats.items():
        print(f"  {k:22s}: {v}")
    ref = DATASETS[name].get("reference")
    if ref:
        matches = all(stats[f"n_{k.split('_')[1]}"] == v for k, v in ref.items())
        print(f"  reference {ref} -> exact match: {matches}")
    assert stats["n_missing_smiles"] == 0, f"{name}: missing SMILES"
    assert stats["n_missing_sequence"] == 0, f"{name}: missing sequences"
    print(f"  raw CSV -> {root}/raw/{name}.csv  [OK]")


def main() -> int:
    ap = argparse.ArgumentParser(description="Download and sanity-check DTI datasets.")
    ap.add_argument("--dataset", default="davis",
                    help="dataset name, or 'all' for every TDC-available dataset")
    ap.add_argument("--root", default="data")
    args = ap.parse_args()

    targets = list(DATASETS) if args.dataset.lower() == "all" else [args.dataset.lower()]
    for name in targets:
        _report(name, args.root)

    if args.dataset.lower() == "all":
        print("\n--- NOT available via TDC (need separate sourcing) ---")
        for name, note in UNAVAILABLE_ON_TDC.items():
            print(f"  {name}: {note}")

    print("\nStep 1 'done': datasets acquired, schema complete, counts recorded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
