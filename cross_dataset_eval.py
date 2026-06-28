"""
Cross-dataset DTI evaluation: train on luo_17, test on yamanishi_e.

Tests whether H-GNN-RNN-DTI generalises across DTI benchmarks without any
fine-tuning. Both datasets use the same drug-graph format (65-dim RDKit atoms)
but different ESM-2 models for protein embeddings:
  luo_17      : ESM-2 650M -> 1280-dim (projected to 320 inside model)
  yamanishi_e : ESM-2   8M ->  320-dim (no projection needed)

The model is inductive, so it can process unseen drugs and proteins
from the test dataset without retraining.

Usage:
    python cross_dataset_eval.py --seed 1
    python cross_dataset_eval.py --seed 1 --epochs 100
"""

import os, json, argparse, time, random
import numpy as np
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, accuracy_score

from config     import MODEL, TRAIN, FOCAL, CKPT_DIR, LOG_DIR, DATA_DIR
from model      import HGNN_RNN_DTI, FocalLoss
from data       import build_dataset, get_dataloader
from data.utils import get_dataloader, precompute_protein_cache


TRAIN_DATASET = 'luo_17'
TEST_DATASET  = 'yamanishi_e'
RATIO         = '1to1'


# ── Protein caching that handles dim projection ───────────────────────────────

@torch.no_grad()
def cache_proteins_with_proj(model, emb_array, prot_ids, device,
                              batch_size=64, max_seq_len=256):
    """
    Like precompute_protein_cache but applies prot_input_proj before
    protein_encoder. Needed for luo_17 (1280-dim -> 320 projection).
    """
    model.eval()
    cache = {}
    ids   = list(prot_ids)
    id_to_idx = {pid: i for i, pid in enumerate(ids)}

    for i in range(0, len(ids), batch_size):
        batch_ids  = ids[i : i + batch_size]
        batch_embs = []
        for pid in batch_ids:
            idx = id_to_idx[pid]
            emb = torch.tensor(emb_array[idx], dtype=torch.float)
            if emb.dim() == 2:
                emb = emb[:max_seq_len]
            batch_embs.append(emb)

        if batch_embs[0].dim() == 2:
            ml  = max(e.size(0) for e in batch_embs)
            pad = torch.zeros(len(batch_embs), ml, batch_embs[0].size(-1))
            for j, e in enumerate(batch_embs):
                pad[j, :e.size(0)] = e
            inp = pad.to(device)
        else:
            inp = torch.stack(batch_embs).to(device)

        last_dim = inp.shape[-1]
        if last_dim != 320:
            inp = model.prot_input_proj(inp)

        reprs = model.protein_encoder(inp)
        for pid, r in zip(batch_ids, reprs.cpu()):
            cache[pid] = r

    model.train()
    return cache


# ── Metrics ───────────────────────────────────────────────────────────────────

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_probs, all_preds, all_targets = [], [], []

    with torch.no_grad():
        for batch in loader:
            if batch is None:
                continue
            drug, prot, labels = batch
            drug   = drug.to(device)
            prot   = prot.to(device)
            labels = labels.to(device)

            logits = model(drug, prot)
            loss   = criterion(logits, labels)
            total_loss += loss.item()

            probs = torch.softmax(logits, dim=-1)[:, 1].cpu().numpy()
            preds = (probs > 0.5).astype(int)
            all_probs.extend(probs)
            all_preds.extend(preds)
            all_targets.extend(labels.cpu().numpy())

    avg_loss = total_loss / max(len(loader), 1)
    targets  = np.array(all_targets)
    metrics  = dict(
        auroc  = roc_auc_score(targets, np.array(all_probs)),
        auprc  = average_precision_score(targets, np.array(all_probs)),
        acc    = accuracy_score(targets, np.array(all_preds)),
        f1     = f1_score(targets, np.array(all_preds)),
    )
    primary = metrics['auroc']
    return avg_loss, metrics, primary


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed',       type=int,   default=42)
    parser.add_argument('--epochs',     type=int,   default=TRAIN['epochs'])
    parser.add_argument('--batch_size', type=int,   default=TRAIN['batch_size'])
    parser.add_argument('--lr',         type=float, default=TRAIN['lr'])
    parser.add_argument('--device',     default='cuda' if torch.cuda.is_available() else 'cpu')
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    device = torch.device(args.device)

    print(f"\n{'='*60}")
    print(f"  Cross-dataset: {TRAIN_DATASET} -> {TEST_DATASET}")
    print(f"  Seed: {args.seed}  Device: {device}  Epochs: {args.epochs}")
    print(f"{'='*60}\n")

    # ── Load train/val indices from luo_17 random fold 0 ─────────────────────
    split_path = os.path.join(DATA_DIR, "splits",
                              f"{TRAIN_DATASET}_dti_labels_{RATIO}_random_split.json")
    with open(split_path) as f:
        splits = json.load(f)
    train_idx = splits['fold_0']['train']
    val_idx   = splits['fold_0']['val']

    # ── Load ALL yamanishi_e pairs as test set ────────────────────────────────
    test_label_path = os.path.join(DATA_DIR, "labels",
                                   f"{TEST_DATASET}_dti_labels_{RATIO}.csv")
    test_df  = pd.read_csv(test_label_path)
    test_idx = list(range(len(test_df)))

    # ── Build datasets ────────────────────────────────────────────────────────
    train_ds = build_dataset(TRAIN_DATASET, 'dti', train_idx, ratio=RATIO)
    val_ds   = build_dataset(TRAIN_DATASET, 'dti', val_idx,   ratio=RATIO)
    test_ds  = build_dataset(TEST_DATASET,  'dti', test_idx,  ratio=RATIO)

    train_loader = get_dataloader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader   = get_dataloader(val_ds,   batch_size=args.batch_size, shuffle=False)
    test_loader  = get_dataloader(test_ds,  batch_size=args.batch_size, shuffle=False)

    print(f"  Train ({TRAIN_DATASET}): {len(train_ds):,}  "
          f"Val: {len(val_ds):,}  Test ({TEST_DATASET}): {len(test_ds):,}")

    # ── Determine ESM dims ────────────────────────────────────────────────────
    import numpy as _np
    train_emb = _np.load(os.path.join(DATA_DIR, "protein_embeddings",
                                       f"{TRAIN_DATASET}_protein_embeddings.npy"),
                          mmap_mode='r')
    test_emb  = _np.load(os.path.join(DATA_DIR, "protein_embeddings",
                                       f"{TEST_DATASET}_protein_embeddings.npy"),
                          mmap_mode='r')
    train_esm_dim = train_emb.shape[-1]
    test_esm_dim  = test_emb.shape[-1]
    print(f"  Train ESM dim: {train_esm_dim}  Test ESM dim: {test_esm_dim}")

    # ── Model ─────────────────────────────────────────────────────────────────
    model = HGNN_RNN_DTI(
        task='dti',
        esm_dim=train_esm_dim,
        **{k: v for k, v in MODEL.items() if k not in ('esm_dim',)},
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Parameters: {n_params:,}\n")

    # ── Pre-cache train proteins (luo_17, may need projection) ───────────────
    with open(os.path.join(DATA_DIR, "protein_embeddings",
                            f"{TRAIN_DATASET}_protein_ids.json")) as f:
        train_prot_ids = json.load(f)

    print(f"  Caching {TRAIN_DATASET} proteins ({len(train_prot_ids)})...")
    train_prot_cache = cache_proteins_with_proj(
        model, train_emb, train_prot_ids, device, batch_size=32)
    train_ds.set_protein_cache(train_prot_cache)
    val_ds.set_protein_cache(train_prot_cache)
    print(f"  Done. {len(train_prot_cache)} proteins cached.\n")

    # ── Pre-cache test proteins (yamanishi_e, 320-dim, no projection) ─────────
    with open(os.path.join(DATA_DIR, "protein_embeddings",
                            f"{TEST_DATASET}_protein_ids.json")) as f:
        test_prot_ids = json.load(f)

    print(f"  Caching {TEST_DATASET} proteins ({len(test_prot_ids)})...")
    test_prot_cache = precompute_protein_cache(
        model.protein_encoder, test_emb, test_prot_ids, device, batch_size=64)
    test_ds.set_protein_cache(test_prot_cache)
    print(f"  Done. {len(test_prot_cache)} proteins cached.\n")

    # ── Loss / optimiser / scheduler ─────────────────────────────────────────
    criterion = FocalLoss(**FOCAL)
    optimizer = optim.Adam(model.parameters(), lr=args.lr,
                           weight_decay=TRAIN['weight_decay'])
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)

    ckpt_path = os.path.join(CKPT_DIR,
        f"cross_{TRAIN_DATASET}_to_{TEST_DATASET}_seed{args.seed}_best.pt")

    best_metric  = -float('inf')
    best_epoch   = 0
    patience_cnt = 0
    history      = []

    # ── Training loop ─────────────────────────────────────────────────────────
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            if batch is None:
                continue
            drug, prot, labels = batch
            drug   = drug.to(device)
            prot   = prot.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(drug, prot)
            loss   = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), TRAIN['grad_clip'])
            optimizer.step()
            total_loss += loss.item()
        train_loss = total_loss / max(len(train_loader), 1)

        val_loss, val_metrics, val_primary = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - t0
        met_str = '  '.join(f"{k}={v:.4f}" for k, v in val_metrics.items())
        print(f"Epoch {epoch:3d}/{args.epochs} | "
              f"train={train_loss:.4f} | val={val_loss:.4f} | {met_str} | {elapsed:.1f}s")

        history.append(dict(epoch=epoch, train_loss=train_loss,
                            val_loss=val_loss, **val_metrics))

        if val_primary > best_metric:
            best_metric  = val_primary
            best_epoch   = epoch
            patience_cnt = 0
            torch.save({'epoch': epoch, 'state_dict': model.state_dict(),
                        'val_metrics': val_metrics}, ckpt_path)
        else:
            patience_cnt += 1
            if patience_cnt >= TRAIN['patience']:
                print(f"\n  Early stopping at epoch {epoch} (best: {best_epoch})")
                break

    # ── Test evaluation ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Loading best checkpoint from epoch {best_epoch}...")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt['state_dict'])

    # Re-cache test proteins with best model weights
    test_prot_cache = precompute_protein_cache(
        model.protein_encoder, test_emb, test_prot_ids, device, batch_size=64)
    test_ds.set_protein_cache(test_prot_cache)

    _, test_metrics, _ = evaluate(model, test_loader, criterion, device)
    print(f"  TEST ({TEST_DATASET}):")
    for k, v in test_metrics.items():
        print(f"    {k}: {v:.4f}")

    def to_py(obj):
        if isinstance(obj, dict): return {k: to_py(v) for k, v in obj.items()}
        if isinstance(obj, list): return [to_py(v) for v in obj]
        if hasattr(obj, 'item'): return obj.item()
        return obj

    results = to_py(dict(
        train_dataset=TRAIN_DATASET, test_dataset=TEST_DATASET,
        seed=args.seed, best_epoch=best_epoch,
        test_metrics=test_metrics, history=history,
    ))

    log_path = os.path.join(LOG_DIR,
        f"cross_{TRAIN_DATASET}_to_{TEST_DATASET}_seed{args.seed}.json")
    import json as _json
    with open(log_path, 'w') as f:
        _json.dump(results, f, indent=2)

    print(f"\n  Results saved -> {log_path}")
    print(f"  Checkpoint   -> {ckpt_path}")


if __name__ == '__main__':
    main()
