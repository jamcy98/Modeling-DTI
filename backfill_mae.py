"""
Back-fill MAE into existing H-GNN-RNN-DTI DTA seed JSON files.
Loads each saved checkpoint, re-runs test-set inference, adds mae to test_metrics.
"""

import os, json
import numpy as np
import torch
from sklearn.metrics import mean_absolute_error

from config     import MODEL, TRAIN, CKPT_DIR, LOG_DIR, DATA_DIR
from model      import HGNN_RNN_DTI, DTALoss
from data       import build_dataset, get_dataloader
from data.utils import precompute_protein_cache
from train      import load_split, eval_epoch

SEEDS   = [1, 2, 3, 4, 5]
DEVICE  = torch.device('cpu')


def backfill(dataset, seed):
    log_path  = os.path.join(LOG_DIR,  f"hgnn_rnn_dti_{dataset}_dta_random_fold0_seed{seed}.json")
    ckpt_path = os.path.join(CKPT_DIR, f"hgnn_rnn_dti_{dataset}_dta_random_fold0_seed{seed}_best.pt")

    if not os.path.exists(log_path):
        print(f"  SKIP {dataset} seed {seed}: no log file")
        return
    if not os.path.exists(ckpt_path):
        print(f"  SKIP {dataset} seed {seed}: no checkpoint")
        return

    with open(log_path) as f:
        result = json.load(f)

    if 'mae' in result.get('test_metrics', {}):
        print(f"  SKIP {dataset} seed {seed}: MAE already present ({result['test_metrics']['mae']:.4f})")
        return

    print(f"  Processing {dataset} seed {seed}...")

    _, _, test_idx = load_split(dataset, 'dta', 'random', '1to1', fold=0)
    test_ds = build_dataset(dataset, 'dta', test_idx)

    emb_path = os.path.join(DATA_DIR, "protein_embeddings", f"{dataset}_protein_embeddings.npy")
    emb = np.load(emb_path, mmap_mode='r')
    esm_dim = emb.shape[-1]

    ckpt = torch.load(ckpt_path, map_location=DEVICE, weights_only=False)
    model = HGNN_RNN_DTI(
        task='dta', esm_dim=esm_dim, hidden_dim=MODEL['hidden_dim'],
        **{k: v for k, v in MODEL.items() if k not in ('esm_dim', 'hidden_dim')},
    ).to(DEVICE)
    model.load_state_dict(ckpt['state_dict'])

    if emb.ndim == 3:
        ids_path = os.path.join(DATA_DIR, "protein_embeddings", f"{dataset}_protein_ids.json")
        with open(ids_path) as f:
            all_prot_ids = json.load(f)
        prot_cache = precompute_protein_cache(model.protein_encoder, emb, all_prot_ids, DEVICE, batch_size=64)
        test_ds.set_protein_cache(prot_cache)

    test_loader = get_dataloader(test_ds, batch_size=256, shuffle=False)
    criterion   = DTALoss()
    _, metrics, _ = eval_epoch(model, test_loader, criterion, DEVICE, 'dta')

    # metrics already contains mae now (train.py was updated)
    mae_val = metrics['mae']
    result['test_metrics']['mae'] = float(mae_val)

    # reorder keys: mse, mae, rmse, r2, pearson, spearman
    ordered = {}
    for k in ['mse', 'mae', 'rmse', 'r2', 'pearson', 'spearman']:
        if k in result['test_metrics']:
            ordered[k] = result['test_metrics'][k]
    result['test_metrics'] = ordered

    with open(log_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"    MAE={mae_val:.4f}  ->  {log_path}")


if __name__ == '__main__':
    for dataset in ['davis', 'kiba']:
        print(f"\n=== {dataset.upper()} ===")
        for seed in SEEDS:
            backfill(dataset, seed)
    print("\nDone.")
