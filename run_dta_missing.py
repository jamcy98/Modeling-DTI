"""
Run the three missing DTA seeds:
  - davis  seed 5
  - kiba   seed 4
  - kiba   seed 5
Outputs are captured in logs/dta_missing_run.log.
"""

import subprocess, sys, time, os

PYTHON = sys.executable
LOG    = os.path.join("logs", "dta_missing_run.log")

runs = [
    ("davis", 5),
    ("kiba",  4),
    ("kiba",  5),
]

with open(LOG, "w", buffering=1) as log:
    def w(s):
        print(s)
        log.write(s + "\n")

    for dataset, seed in runs:
        tag = f"{dataset} seed {seed}"
        w(f"\n{'='*60}")
        w(f"== {tag} ==")
        w(f"{'='*60}\n")
        t0 = time.time()
        cmd = [
            PYTHON, "train.py",
            "--dataset", dataset,
            "--task",    "dta",
            "--split",   "random",
            "--seed",    str(seed),
            "--fold",    "0",
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output = result.stdout
        log.write(output)
        print(output, end="")
        elapsed = (time.time() - t0) / 60
        if result.returncode == 0:
            w(f"\n  OK: {tag}  ({elapsed:.1f} min)")
        else:
            w(f"\n  FAILED (exit {result.returncode}): {tag}  ({elapsed:.1f} min)")

    w("\n== All missing DTA seeds complete. ==")
