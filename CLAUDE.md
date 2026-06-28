# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**H-GNN-RNN-DTI**: A deep learning model for Drug-Target Interaction (DTI) and Drug-Target Affinity (DTA) prediction. Developed as a research project under Assoc. Prof. Dr. Nurul Hashimah at USM.

The model encodes drugs as molecular graphs (Hierarchical GAT) and proteins as ESM-2 embeddings processed by a BiGRU, then fuses them via Gated Cross-Attention.

## Running the Model

**Training:**
```bash
python train.py --dataset davis --task dta --split random
python train.py --dataset luo_17 --task dti --split cold_drug
python train.py --dataset yamanishi_e --task dti --split random --fold 0
```

Key arguments: `--dataset`, `--task {dti,dta}`, `--split {random,cold_drug,cold_target,cold_pair}`, `--ratio` (for DTI: `1to1`), `--fold`, `--device`, `--epochs`, `--batch_size`, `--lr`, `--hidden_dim`.

Checkpoints are saved to `checkpoints/` and training logs to `logs/`.

## Data Preprocessing Pipeline

All preprocessing scripts live in `Dataset/`. Run them in order (or use the master script):

```bash
cd Dataset
python run_all_preprocessing.py              # run all steps 10-13
python run_all_preprocessing.py --step 10    # run one step
python run_all_preprocessing.py --skip 11    # skip ESM-2 (slow, needs GPU)
```

Steps:
- **Step 10** (`10_preprocess_drugs.py`): SMILES → PyG molecular graphs + ChemBERTa embeddings → `processed/drug_graphs/{dataset}_drug_graphs.pt`
- **Step 10b** (`10b_preprocess_large_drugs.py`): streaming version for BindingDB/ChEMBL (saves chunked `.pt` files instead of one file)
- **Step 11** (`11_preprocess_proteins.py`): sequences → ESM-2 embeddings → `processed/protein_embeddings/{dataset}_protein_embeddings.npy` + `_protein_ids.json`
- **Step 12** (`12_preprocess_labels.py`): interaction labels + negative sampling → `processed/labels/`
- **Step 13** (`13_preprocess_splits.py`): train/val/test splits → `processed/splits/`

Raw dataset files go in `Dataset/raw/{dataset_name}/`.

## Architecture

```
Drug (SMILES)          Protein (sequence)
     │                       │
  RDKit + ChemBERTa       ESM-2 embeddings
     │                       │
  DrugEncoder             ProteinEncoder
  (3-layer GAT,           (2-layer BiGRU +
   8 heads + mean/         attention pooling,
   max pooling +           or linear proj for
   ChemBERTa fusion)       mean-pooled input)
     │                       │
     └──────────┬────────────┘
           GatedCrossAttention
           (bidirectional: drug↔protein)
                 │
            Task head
           DTI: (B,2) logits → FocalLoss
           DTA: (B,1) scalar → MSE
```

Key files:
- `config.py` — all hyperparameters (`MODEL`, `TRAIN`, `FOCAL`, `DATASETS`)
- `model/hgnn_rnn_dti.py` — top-level `HGNN_RNN_DTI` module
- `model/encoders.py` — `DrugEncoder` (GAT) and `ProteinEncoder` (BiGRU)
- `model/fusion.py` — `GatedCrossAttention`
- `model/losses.py` — `FocalLoss` (DTI) and `DTALoss` (DTA)
- `data/dataset.py` — `DTIDataset`, `DTADataset`, `build_dataset()`
- `data/utils.py` — `collate_fn`, `get_dataloader`, `precompute_protein_cache()`
- `train.py` — training loop with early stopping, cosine LR scheduler, test evaluation

## Supported Datasets

| Dataset | Task | Notes |
|---------|------|-------|
| `davis` | DTA | pKd regression |
| `kiba` | DTA | KIBA score regression |
| `luo_17` | DTI | DrugBank IDs, SMILES fetched from PubChem |
| `yamanishi_e/ic/gpcr/nr` | DTI | 4 subsets of Yamanishi 2008 |
| `bindingdb` | DTI | Large — uses streaming/chunked processing |

## Protein Embedding Modes

`ProteinEncoder` auto-selects based on input tensor shape:
- `(B, L, 320)` — full residue embeddings → BiGRU path
- `(B, 320)` — mean-pooled → linear projection path

ESM-2 model used: `facebook/esm2_t6_8M_UR50D` (8M params, 320-dim). Luo_17 uses ESM-2 650M (1280-dim) — projected down to 320 inside `HGNN_RNN_DTI`.

## Performance Note

For 3D protein embeddings, `train.py` pre-runs all proteins through `ProteinEncoder` once before training (`precompute_protein_cache`) and stores results in a dict. Datasets call `set_protein_cache()` to use it, making per-batch protein lookup O(1).

## Dependencies

Core: `torch`, `torch-geometric`, `rdkit`, `transformers`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `tqdm`

ChemBERTa model: `seyonec/ChemBERTa-zinc-base-v1` (downloaded automatically by HuggingFace on first run)
