"""Generate the Colab notebook that runs the Objective 1 fusion ablation on a GPU.

Output: notebooks/Objective1_Ablation_Colab.ipynb
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_URL = "https://github.com/jamcy98/Modeling-DTI.git"
BRANCH = "objective1-impl"


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines]}


def code(*lines):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": [l + "\n" for l in lines]}


cells = [
    md("# H-GNN-RNN-DTI - Objective 1 Fusion Ablation (GPU)",
       "",
       "Runs the core RQ1 experiment: **GCA vs concat vs flat_gate vs ungated_xattn** on "
       "DAVIS (S1 warm-start), 3 seeds each, reporting AUROC/AUPR mean±std + a paired "
       "significance test.",
       "",
       "The **preprocessed DAVIS dataset is bundled in the repo**, so there is nothing to "
       "download and no RDKit / PyTDC to install - only `torch-geometric` on top of Colab's "
       "stock PyTorch. That keeps 'Run all' reliable.",
       "",
       "**Before running:** `Runtime -> Change runtime type -> Hardware accelerator = GPU (T4)`, "
       "then `Runtime -> Run all`.",
       "",
       "If the `git clone` cell fails, the code hasn't been pushed to the branch yet - push "
       f"`{BRANCH}` to `{REPO_URL}`, or upload the `H-GNN-RNN-DTI/` folder and `%cd` into it."),
    md("## 1. Check the GPU"),
    code("!nvidia-smi -L",
         "import torch; print('torch', torch.__version__, '| CUDA available:', torch.cuda.is_available())"),
    md("## 2. Get the code (+ bundled preprocessed data)",
       "Re-run safe (wipes any earlier clone) and works for a **private** repo. It tries an "
       "anonymous clone first; if that fails it reads a GitHub token from **Colab Secrets** "
       "(preferred) and otherwise prompts via `getpass`.",
       "",
       "**NEVER paste the token into this notebook** - it would get committed to the repo. "
       "Instead store it in Colab Secrets so it stays in your account, not in the file:",
       "",
       "1. Create a fine-grained token: GitHub -> Settings -> Developer settings -> Fine-grained "
       "tokens. Repository access: only `Modeling-DTI`. Permissions: **Contents = Read-only**.",
       "2. In Colab, click the **key icon** (Secrets) in the left sidebar -> **+ Add new secret** "
       "-> Name = `GH_TOKEN`, Value = the token -> toggle **Notebook access** on.",
       "3. Run this cell. (If you skip the secret, it will prompt you once via `getpass`.)",
       "",
       "Treat the token as disposable: revoke it on GitHub when you're done."),
    code(f"REPO = 'jamcy98/Modeling-DTI'",
         f"BRANCH = '{BRANCH}'",
         "import os, shutil, subprocess",
         "DEST = '/content/Modeling-DTI'",
         "if os.path.isdir(DEST):",
         "    shutil.rmtree(DEST)  # remove stale clone from an earlier run",
         "",
         "def _clone(url):",
         "    return subprocess.run(['git', 'clone', '--depth', '1', '--branch', BRANCH, url, DEST],",
         "                          capture_output=True, text=True)",
         "",
         "res = _clone(f'https://github.com/{REPO}.git')  # anonymous (works if public)",
         "if res.returncode != 0:",
         "    token = None",
         "    try:  # preferred: token stored in Colab Secrets (key icon), name GH_TOKEN",
         "        from google.colab import userdata",
         "        token = userdata.get('GH_TOKEN')",
         "    except Exception:",
         "        token = None",
         "    if not token:  # fallback: one-time prompt, not saved anywhere",
         "        from getpass import getpass",
         "        token = getpass('GitHub token (Contents:Read on Modeling-DTI): ').strip()",
         "    res = _clone(f'https://{token}@github.com/{REPO}.git')",
         "    del token",
         "    if res.returncode != 0:",
         "        raise RuntimeError('Clone failed:\\n' + res.stderr[-800:])",
         "%cd /content/Modeling-DTI/H-GNN-RNN-DTI",
         "# sanity: the bundled processed DAVIS data should be present",
         "assert os.path.exists('data/processed/davis/pairs.csv'), 'processed DAVIS missing'",
         "print('bundled DAVIS data found')"),
    md("## 3. Install dependencies",
       "Colab already ships a CUDA build of PyTorch, plus numpy / pandas / scipy / scikit-learn / "
       "pyyaml. We only need PyTorch Geometric. (No RDKit or PyTDC: the preprocessed graphs are "
       "already in the repo, and the training/ablation code imports RDKit lazily.)"),
    code("!pip -q install torch-geometric",
         "print('deps installed')"),
    md("## 4. Run the fusion ablation on GPU",
       "Full DAVIS, all four fusions, seeds 42/43/44. On a T4 this is the main compute; "
       "expect roughly tens of minutes. For a fast dry run first, add `--epochs 2 --max-batches 30`."),
    code("!python scripts/run_ablation.py --dataset davis --split S1 --device cuda --seeds 42 43 44"),
    md("## 5. Show + download results"),
    code("import json",
         "res = json.load(open('experiments/results/ablation_davis_S1.json'))",
         "print(json.dumps(res['summary'], indent=2))",
         "print(json.dumps(res['significance_gca_vs_baselines'], indent=2))"),
    code("from google.colab import files",
         "files.download('experiments/results/ablation_davis_S1.json')"),
    md("## What the result means",
       "- **AUPR** is the honest metric here (DAVIS is ~4% positive).",
       "- RQ1 is supported if **gca** beats concat / flat_gate / ungated_xattn on AUPR, and the "
       "paired test `dAUPR` is positive with a small p-value.",
       "- If GCA does *not* beat the simpler fusions, that is a real (publishable) finding too - "
       "see docs/objective1_analysis.md Risk R1.",
       "",
       "To regenerate the preprocessed data from scratch instead of using the bundled copy "
       "(needs RDKit + PyTDC): `pip install rdkit 'PyTDC==0.4.1' 'setuptools<81'` then "
       "`python scripts/download_data.py --dataset davis && python scripts/preprocess.py --dataset davis`."),
]

nb = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

out = Path(__file__).resolve().parents[1] / "notebooks" / "Objective1_Ablation_Colab.ipynb"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print(f"wrote {out}")
