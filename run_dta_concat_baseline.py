"""
Train ConcatGNN_RNN_DTI on Davis and KIBA (DTA task), 5 seeds each.
Runs sequentially. Estimated time: ~2 hrs Davis + ~23 hrs KIBA (CPU).
Results saved to logs/concat_baseline_{dataset}_dta_random_fold0_seed{seed}.json
"""

import subprocess, sys, os, time

PYTHON = sys.executable
LOG    = os.path.join("logs", "dta_concat_baseline_run.log")

runs = [
    ("davis", 1), ("davis", 2), ("davis", 3), ("davis", 4), ("davis", 5),
    ("kiba",  1), ("kiba",  2), ("kiba",  3), ("kiba",  4), ("kiba",  5),
]

with open(LOG, "w", buffering=1) as log:
    for dataset, seed in runs:
        header = f"\n{'='*60}\n== concat_baseline {dataset} seed {seed} ==\n{'='*60}\n"
        print(header, flush=True)
        log.write(header); log.flush()

        t0  = time.time()
        cmd = [PYTHON, "train.py",
               "--dataset",    dataset,
               "--task",       "dta",
               "--split",      "random",
               "--model",      "concat_baseline",
               "--seed",       str(seed),
               "--fold",       "0"]

        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        elapsed = (time.time() - t0) / 60

        log.write(result.stdout); log.flush()

        status = "OK" if result.returncode == 0 else "FAILED"
        msg = f"  {status}: concat_baseline {dataset} seed {seed}  ({elapsed:.1f} min)\n"
        print(msg, flush=True)
        log.write(msg); log.flush()
