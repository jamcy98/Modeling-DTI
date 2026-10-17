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
       "**Before running:** `Runtime -> Change runtime type -> Hardware accelerator = GPU (T4)`, "
       "then `Runtime -> Run all`.",
       "",
       "If the `git clone` cell fails, the code hasn't been pushed to the branch yet - push "
       f"`{BRANCH}` to `{REPO_URL}`, or upload a zip of the `H-GNN-RNN-DTI/` folder and `%cd` into it."),
    md("## 1. Check the GPU"),
    code("!nvidia-smi -L",
         "import torch; print('torch', torch.__version__, '| CUDA available:', torch.cuda.is_available())"),
    md("## 2. Get the code"),
    code(f"REPO_URL = '{REPO_URL}'",
         f"BRANCH = '{BRANCH}'",
         "!git clone --depth 1 --branch $BRANCH $REPO_URL",
         "%cd Modeling-DTI/H-GNN-RNN-DTI"),
    md("## 3. Install dependencies",
       "(Colab already ships a CUDA build of PyTorch; we add the rest. `PyTDC==0.4.1` and "
       "`setuptools<81` are pinned for the same reasons as locally.)"),
    code("!pip -q install torch-geometric 'PyTDC==0.4.1' 'setuptools<81' rdkit scipy scikit-learn pyyaml",
         "print('deps installed')"),
    md("## 4. Download + preprocess DAVIS",
       "Binarizes at Kd <= 30 nM and builds the stratified S1 split (same as locally)."),
    code("!python scripts/download_data.py --dataset davis",
         "!python scripts/preprocess.py --dataset davis"),
    md("## 5. Run the fusion ablation on GPU",
       "Full DAVIS, all four fusions, seeds 42/43/44. On a T4 this is the main compute; "
       "expect roughly tens of minutes. To do a fast dry run first, add "
       "`--epochs 2 --max-batches 30`."),
    code("!python scripts/run_ablation.py --dataset davis --split S1 --device cuda --seeds 42 43 44"),
    md("## 6. Show + download results"),
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
       "see docs/objective1_analysis.md Risk R1."),
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
