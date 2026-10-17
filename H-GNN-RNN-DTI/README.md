# H-GNN-RNN-DTI

Implementation of **H-GNN-RNN-DTI/DTA** — a hybrid deep-learning model for
drug–target interaction (DTI) classification and drug–target affinity (DTA)
regression, integrating a Hierarchical Graph Attention Network (H-GAT) drug
encoder and a Bidirectional LSTM (Bi-LSTM) protein encoder through a
**bidirectional Gated Cross-Attention (GCA)** fusion mechanism.

This repository currently targets **Objective 1 — Dynamic Cross-Modal Fusion**
(Research Question 1). See [`docs/objective1_analysis.md`](docs/objective1_analysis.md)
for the full analysis, roadmap, and feasibility assessment.

## Objective 1 in one line
> Given identical drug/protein inputs, does bidirectional GCA fusion outperform
> static concatenation, flat gating, and ungated cross-attention for DTI/DTA?

## Project structure

```
H-GNN-RNN-DTI/
├── configs/              # YAML configs (default.yaml is the Obj1 reference config)
│   ├── data/             # per-dataset configs
│   ├── model/            # encoder / fusion / head variants
│   └── experiment/       # named experiment presets (e.g., fusion ablation)
├── data/
│   ├── raw/              # downloaded benchmarks (DAVIS, KIBA, BindingDB, ...)
│   ├── processed/        # cleaned, split-ready tables
│   ├── embeddings/       # cached ChemBERTa / ESM-2 embeddings (precomputed)
│   └── splits/           # frozen S1/S2/S3/cold-pair/cross-dataset index files
├── src/hgnn_rnn_dti/
│   ├── data/             # loaders, graph construction, negative sampling, split logic
│   ├── features/         # RDKit, ChemBERTa, ESM-2, SS, physicochemical, caching
│   ├── encoders/         # H-GAT (drug), Bi-LSTM (protein)
│   ├── fusion/           # GCA + gating, and baselines: concat, flat_gate, ungated_xattn
│   ├── models/           # assembled model + prediction heads (classification/regression)
│   ├── training/         # trainer, focal loss, early stopping, seeding
│   ├── evaluation/       # metrics, split protocols, repeated-run statistics
│   ├── ablation/         # fusion / encoder / training-strategy ablations
│   └── utils/            # config, logging, reproducibility helpers
├── scripts/              # precompute_embeddings.py, run_train.py, run_ablation.py
├── experiments/          # logs / checkpoints / results (gitignored)
├── notebooks/            # exploratory analysis
├── tests/                # unit tests (shapes, split leakage, metric correctness)
└── docs/
    └── objective1_analysis.md   # ← the Objective 1 analysis (read this first)
```

## Setup (provisional — compute not yet secured)
```bash
python -m venv .venv && source .venv/bin/activate   # or conda
pip install -r requirements.txt
```
PyTorch / PyTorch Geometric wheels are hardware-specific — install the build
matching your eventual CUDA/CPU target. Until compute is chosen, develop against
CPU and a small data subset.

## Status
Scaffold + analysis only. No model code committed yet. See the analysis doc's
roadmap (§5) for the build order.
