"""
Training script for H-GNN-RNN-DTI.

Usage:
    python train.py --dataset davis --task dta --split random
    python train.py --dataset luo_17 --task dti --split cold_drug
    python train.py --dataset yamanishi_e --task dti --split random
"""

import os, json, argparse, time, random
import numpy as np
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

from config       import MODEL, TRAIN, FOCAL, CKPT_DIR, LOG_DIR, DATA_DIR
from model        import HGNN_RNN_DTI, ConcatGNN_RNN_DTI, FocalLoss, DTALoss
from data         import build_dataset, get_dataloader
from data.utils   import precompute_protein_cache

from sklearn.metrics import (roc_auc_score, average_precision_score,
                             accuracy_score, f1_score,
                             mean_squared_error, r2_score)
from scipy.stats import pearsonr, spearmanr


# ── Metrics ───────────────────────────────────────────────────────────────────

def evaluate_dti(preds, probs, targets):
    return dict(
        auroc  = roc_auc_score(targets, probs),
        auprc  = average_precision_score(targets, probs),
        acc    = accuracy_score(targets, preds),
        f1     = f1_score(targets, preds),
    )


def evaluate_dta(preds, targets):
    mse = mean_squared_error(targets, preds)
    r, _ = pearsonr(targets, preds)
    rho, _ = spearmanr(targets, preds)
    return dict(
        mse  = mse,
        rmse = mse ** 0.5,
        r2   = r2_score(targets, preds),
        pearson  = r,
        spearman = rho,
    )


# ── Training loop ─────────────────────────────────────────────────────────────

def train_epoch(model, loader, optimizer, criterion, device, grad_clip):
    model.train()
    total_loss = 0.0
    for batch in loader:
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
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        total_loss += loss.item()

    return total_loss / max(len(loader), 1)


@torch.no_grad()
def eval_epoch(model, loader, criterion, device, task):
    model.eval()
    total_loss = 0.0
    all_preds, all_probs, all_targets = [], [], []

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

        if task == 'dti':
            probs = torch.softmax(logits, dim=-1)[:, 1].cpu().numpy()
            preds = (probs > 0.5).astype(int)
            all_probs.extend(probs)
            all_preds.extend(preds)
        else:
            preds = logits.squeeze(-1).cpu().numpy()
            all_preds.extend(preds)

        all_targets.extend(labels.cpu().numpy())

    avg_loss = total_loss / max(len(loader), 1)
    targets  = np.array(all_targets)
    preds    = np.array(all_preds)

    if task == 'dti':
        metrics = evaluate_dti(preds, np.array(all_probs), targets)
        primary = metrics['auroc']
    else:
        metrics = evaluate_dta(preds, targets)
        primary = -metrics['mse']   # higher is better (negated MSE)

    return avg_loss, metrics, primary


# ── Split loading ─────────────────────────────────────────────────────────────

def load_split(dataset_name, task, split_type, ratio, fold=0):
    label_suffix = f"dta_labels" if task == 'dta' else f"dti_labels_{ratio}"
    split_file   = os.path.join(
        DATA_DIR, "splits",
        f"{dataset_name}_{label_suffix}_{split_type}_split.json"
    )
    with open(split_file) as f:
        splits = json.load(f)

    fold_key = f"fold_{fold}"
    s = splits[fold_key]
    return s['train'], s['val'], s['test']


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset',    default='davis')
    parser.add_argument('--task',       default='dta', choices=['dti','dta'])
    parser.add_argument('--split',      default='random',
                        choices=['random','cold_drug','cold_target','cold_pair'])
    parser.add_argument('--model',      default='hgnn_rnn_dti',
                        choices=['hgnn_rnn_dti', 'concat_baseline'])
    parser.add_argument('--seed',       type=int, default=42)
    parser.add_argument('--ratio',      default='1to1')
    parser.add_argument('--fold',       type=int, default=0)
    parser.add_argument('--hidden_dim', type=int, default=MODEL['hidden_dim'])
    parser.add_argument('--epochs',     type=int, default=TRAIN['epochs'])
    parser.add_argument('--batch_size', type=int, default=TRAIN['batch_size'])
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
    print(f"  Model: {args.model}")
    print(f"  Dataset: {args.dataset}  Task: {args.task}  Split: {args.split}")
    print(f"  Device: {device}  Epochs: {args.epochs}")
    print(f"{'='*60}\n")

    # Load splits
    train_idx, val_idx, test_idx = load_split(
        args.dataset, args.task, args.split, args.ratio, fold=args.fold)

    # Datasets
    train_ds = build_dataset(args.dataset, args.task, train_idx, ratio=args.ratio)
    val_ds   = build_dataset(args.dataset, args.task, val_idx,   ratio=args.ratio)
    test_ds  = build_dataset(args.dataset, args.task, test_idx,  ratio=args.ratio)

    train_loader = get_dataloader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader   = get_dataloader(val_ds,   batch_size=args.batch_size, shuffle=False)
    test_loader  = get_dataloader(test_ds,  batch_size=args.batch_size, shuffle=False)

    print(f"  Train: {len(train_ds):,}  Val: {len(val_ds):,}  Test: {len(test_ds):,}")

    # Determine protein ESM dim from dataset
    import numpy as _np, json as _json
    emb = _np.load(os.path.join(DATA_DIR, "protein_embeddings",
                               f"{args.dataset}_protein_embeddings.npy"), mmap_mode='r')
    esm_dim = emb.shape[-1]
    print(f"  Protein ESM dim: {esm_dim}")

    # Model
    model_cls = ConcatGNN_RNN_DTI if args.model == 'concat_baseline' else HGNN_RNN_DTI
    model = model_cls(
        task=args.task,
        esm_dim=esm_dim,
        hidden_dim=args.hidden_dim,
        **{k: v for k, v in MODEL.items()
           if k not in ('esm_dim', 'hidden_dim')},
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Parameters: {n_params:,}\n")

    # Pre-cache all unique protein representations (runs BiGRU once per protein)
    if emb.ndim == 3:   # full residue embeddings — precompute to avoid per-batch BiGRU
        import json as _json
        with open(os.path.join(DATA_DIR, "protein_embeddings",
                               f"{args.dataset}_protein_ids.json")) as f:
            all_prot_ids = _json.load(f)
        prot_id_to_idx = {pid: i for i, pid in enumerate(all_prot_ids)}
        print(f"  Pre-computing protein representations for {len(all_prot_ids)} proteins...")
        prot_cache = precompute_protein_cache(
            model.protein_encoder, emb, all_prot_ids, device,
            batch_size=64)
        print(f"  Done. Cache: {len(prot_cache)} proteins -> (hidden_dim={args.hidden_dim},)\n")
        for ds in [train_ds, val_ds, test_ds]:
            ds.set_protein_cache(prot_cache)
    else:
        prot_cache = None

    # Loss, optimizer, scheduler
    criterion = FocalLoss(**FOCAL) if args.task == 'dti' else DTALoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr,
                           weight_decay=TRAIN['weight_decay'])
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)

    # Training loop
    best_metric  = -float('inf')
    best_epoch   = 0
    patience_cnt = 0
    history      = []

    ckpt_path = os.path.join(CKPT_DIR,
        f"{args.model}_{args.dataset}_{args.task}_{args.split}_fold{args.fold}_seed{args.seed}_best.pt")

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss = train_epoch(model, train_loader, optimizer, criterion,
                                 device, TRAIN['grad_clip'])
        val_loss, val_metrics, val_primary = eval_epoch(
            model, val_loader, criterion, device, args.task)
        scheduler.step()

        elapsed = time.time() - t0
        met_str = '  '.join(f"{k}={v:.4f}" for k, v in val_metrics.items())
        print(f"Epoch {epoch:3d}/{args.epochs} | "
              f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | "
              f"{met_str} | {elapsed:.1f}s")

        history.append(dict(epoch=epoch, train_loss=train_loss,
                            val_loss=val_loss, **val_metrics))

        # Early stopping
        if val_primary > best_metric:
            best_metric  = val_primary
            best_epoch   = epoch
            patience_cnt = 0
            torch.save({'epoch': epoch, 'state_dict': model.state_dict(),
                        'val_metrics': val_metrics, 'args': vars(args)}, ckpt_path)
        else:
            patience_cnt += 1
            if patience_cnt >= TRAIN['patience']:
                print(f"\n  Early stopping at epoch {epoch} "
                      f"(best: epoch {best_epoch})")
                break

    # Test evaluation
    print(f"\n{'='*60}")
    print(f"  Loading best model from epoch {best_epoch}...")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt['state_dict'])
    _, test_metrics, _ = eval_epoch(model, test_loader, criterion, device, args.task)
    print(f"  TEST RESULTS:")
    for k, v in test_metrics.items():
        print(f"    {k}: {v:.4f}")

    # Save results
    # Convert numpy scalars to Python floats for JSON serialisation
    def to_py(obj):
        if isinstance(obj, dict):
            return {k: to_py(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [to_py(v) for v in obj]
        if hasattr(obj, 'item'):
            return obj.item()
        return obj

    results = to_py(dict(args=vars(args), best_epoch=best_epoch,
                         test_metrics=test_metrics, history=history))
    log_path = os.path.join(LOG_DIR,
        f"{args.model}_{args.dataset}_{args.task}_{args.split}_fold{args.fold}_seed{args.seed}.json")
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved -> {log_path}")
    print(f"  Checkpoint   -> {ckpt_path}")


if __name__ == '__main__':
    main()
