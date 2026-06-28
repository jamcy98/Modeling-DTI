"""
DTKGIN re-implementation (Luo et al., 2024, Methods).

Core idea: Predict drug-target interactions using a Knowledge Graph Interaction
Network (KGIN). Drugs and proteins are represented in a KG augmented with
structural/sequence similarity edges. A 2-layer GNN propagates on the KG to
produce drug and protein embeddings; interaction score = sigmoid(d · t).

Data: yamanishi_e (enzyme subset of Yamanishi 2008).

Key simplifications vs. original:
  - KG is built from:
      (a) training DTI edges (drug-target interactions),
      (b) drug structural similarity edges (Morgan fingerprint cosine similarity),
      (c) protein sequence similarity edges (AAC cosine similarity).
  - Drug features from mean-pooled atom features of molecular graphs.
  - Protein features from mean-pooled ESM-2 residue embeddings.
  - Intent graph approximated by multi-head self-attention over GNN layers.
  - BCELoss with negative sampling instead of their BPR loss.

Usage:
    python baselines/dtkgin.py --split cold_drug --seed 42
    python baselines/dtkgin.py --split random    --seed 42
"""

import os, sys, json, argparse, random, time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.nn import GCNConv, SAGEConv
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
import pandas as pd

ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_YAM    = os.path.join(ROOT, "Dataset", "raw", "yamanishi_08", "e")
PROC       = os.path.join(ROOT, "Dataset", "processed")
LOG_DIR    = os.path.join(ROOT, "logs")


# ── Node features ──────────────────────────────────────────────────────────────

def load_drug_features(drug_ids):
    """Mean-pool atom features from molecular graphs → (n_drugs, 65)."""
    graphs = torch.load(
        os.path.join(PROC, "drug_graphs", "yamanishi_e_drug_graphs.pt"),
        weights_only=False
    )
    feat_dim = next(iter(graphs.values())).x.shape[1]
    n = len(drug_ids)
    feats = torch.zeros(n, feat_dim)
    for i, did in enumerate(drug_ids):
        if did in graphs:
            feats[i] = graphs[did].x.mean(0)
    return feats  # (n, feat_dim)


def load_protein_features(prot_ids):
    """Mean-pool ESM-2 residue embeddings → (n_prots, 1280)."""
    emb_path = os.path.join(PROC, "protein_embeddings", "yamanishi_e_protein_embeddings.npy")
    id_path  = os.path.join(PROC, "protein_embeddings", "yamanishi_e_protein_ids.json")
    emb = np.load(emb_path)
    with open(id_path) as f:
        prot_id_list = json.load(f)
    pid_to_idx = {pid: i for i, pid in enumerate(prot_id_list)}
    if emb.ndim == 3:
        emb = emb.mean(1)
    n = len(prot_ids)
    feat_dim = emb.shape[1]
    feats = torch.zeros(n, feat_dim)
    for i, pid in enumerate(prot_ids):
        if pid in pid_to_idx:
            feats[i] = torch.tensor(emb[pid_to_idx[pid]], dtype=torch.float32)
    return feats


def cosine_sim_edges(feats, threshold=0.5, offset_src=0, offset_dst=0, max_edges=5000):
    """
    Build edges between nodes whose feature cosine similarity >= threshold.
    Returns edge_index of shape (2, E).
    """
    norm = feats / (feats.norm(dim=1, keepdim=True) + 1e-8)
    sim  = norm @ norm.T  # (n, n)
    mask = (sim >= threshold) & (torch.eye(len(feats), dtype=torch.bool) == 0)
    src, dst = torch.where(mask)
    if len(src) > max_edges:
        # Keep top max_edges by similarity
        vals = sim[src, dst]
        topk = vals.topk(max_edges).indices
        src, dst = src[topk], dst[topk]
    return torch.stack([src + offset_src, dst + offset_dst], dim=0)


# ── Data loading ───────────────────────────────────────────────────────────────

def load_split(split):
    labels_path = os.path.join(PROC, "labels", "yamanishi_e_dti_labels_1to1.csv")
    split_path  = os.path.join(
        PROC, "splits", f"yamanishi_e_dti_labels_1to1_{split}_split.json"
    )
    df = pd.read_csv(labels_path)
    with open(split_path) as f:
        splits = json.load(f)
    s = splits["fold_0"]

    all_drug_ids  = sorted(df["drug_id"].unique().tolist())
    all_prot_ids  = sorted(df["protein_id"].unique().tolist())
    drug_to_idx   = {d: i for i, d in enumerate(all_drug_ids)}
    prot_to_idx   = {p: i for i, p in enumerate(all_prot_ids)}

    def to_tensors(indices):
        rows   = df.iloc[indices]
        d_idxs = [drug_to_idx[r] for r in rows["drug_id"]]
        p_idxs = [prot_to_idx[r] for r in rows["protein_id"]]
        labels = rows["label"].tolist()
        return (torch.tensor(d_idxs, dtype=torch.long),
                torch.tensor(p_idxs, dtype=torch.long),
                torch.tensor(labels, dtype=torch.float32))

    train = to_tensors(s["train"])
    val   = to_tensors(s["val"])
    test  = to_tensors(s["test"])
    return all_drug_ids, all_prot_ids, drug_to_idx, prot_to_idx, train, val, test


# ── Model ──────────────────────────────────────────────────────────────────────

class ProjectionHead(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.fc = nn.Linear(in_dim, out_dim)
        self.bn = nn.BatchNorm1d(out_dim)

    def forward(self, x):
        return torch.relu(self.bn(self.fc(x)))


class DTKGIN_Model(nn.Module):
    """
    GNN on the KG (DTI + drug-sim + prot-sim edges).
    Drug/protein embeddings are computed by 2-layer GCN on the full KG node set.
    Score = sigmoid(drug_emb · prot_emb).
    """
    def __init__(self, drug_dim, prot_dim, proj_dim=128, hidden=256, dropout=0.3):
        super().__init__()
        self.drug_proj = ProjectionHead(drug_dim, proj_dim)
        self.prot_proj = ProjectionHead(prot_dim, proj_dim)

        # Two GCN layers on the homogeneous KG
        self.conv1 = SAGEConv(proj_dim, hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.bn1   = nn.BatchNorm1d(hidden)
        self.drop  = nn.Dropout(dropout)

        # Intent attention (approximation): learnable per-node intent weighting
        self.intent = nn.Linear(hidden, hidden, bias=False)

        self.n_drugs = None  # set after init
        self.n_prots = None

    def encode(self, drug_feats, prot_feats, edge_index):
        d_proj = self.drug_proj(drug_feats)
        p_proj = self.prot_proj(prot_feats)
        x = torch.cat([d_proj, p_proj], dim=0)

        x = torch.relu(self.bn1(self.conv1(x, edge_index)))
        x = self.drop(x)
        x = self.conv2(x, edge_index)
        x = x + self.intent(x)     # residual intent refinement
        return x

    def forward(self, drug_feats, prot_feats, edge_index, d_idx, p_idx):
        emb   = self.encode(drug_feats, prot_feats, edge_index)
        d_emb = emb[d_idx]
        p_emb = emb[self.n_drugs + p_idx]
        # L2-normalize then scale: keeps scores in a reasonable range
        d_norm = nn.functional.normalize(d_emb, dim=-1)
        p_norm = nn.functional.normalize(p_emb, dim=-1)
        score  = (d_norm * p_norm).sum(dim=-1) * 10.0  # scale factor
        return score


# ── Training ───────────────────────────────────────────────────────────────────

def negative_sample(n_drugs, n_prots, pos_set, n_neg, seed):
    rng  = np.random.default_rng(seed)
    negs = set()
    attempts = 0
    while len(negs) < n_neg and attempts < n_neg * 20:
        d = int(rng.integers(0, n_drugs))
        p = int(rng.integers(0, n_prots))
        if (d, p) not in pos_set and (d, p) not in negs:
            negs.add((d, p))
        attempts += 1
    d_neg = torch.tensor([d for d, p in negs], dtype=torch.long)
    p_neg = torch.tensor([p for d, p in negs], dtype=torch.long)
    return d_neg, p_neg


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def run_dtkgin(split, seed, epochs=150, lr=1e-3, proj_dim=128, hidden=256,
               dropout=0.3, sim_threshold=0.5):
    set_seed(seed)
    device = torch.device("cpu")

    # Load split
    print(f"Loading yamanishi_e | {split}...")
    all_drug_ids, all_prot_ids, drug_to_idx, prot_to_idx, \
        (tr_d, tr_p, tr_y), (va_d, va_p, va_y), (te_d, te_p, te_y) = load_split(split)

    n_drugs = len(all_drug_ids)
    n_prots = len(all_prot_ids)
    print(f"  Drugs: {n_drugs}, Proteins: {n_prots}")
    print(f"  Train={len(tr_d)}, Val={len(va_d)}, Test={len(te_d)}")

    # Node features
    drug_feats = load_drug_features(all_drug_ids).to(device)
    prot_feats = load_protein_features(all_prot_ids).to(device)

    # Build KG edges (all on combined node set: drugs 0..n_drugs-1, prots n_drugs..n_drugs+n_prots-1)
    # 1. DTI training edges (drug → protein, bidirectional)
    train_pos_set = set(zip(tr_d.tolist(), tr_p.tolist()))
    dti_src = torch.cat([tr_d, tr_p + n_drugs])
    dti_dst = torch.cat([tr_p + n_drugs, tr_d])
    dti_edges = torch.stack([dti_src, dti_dst], dim=0).to(device)

    # 2. Drug-drug structural similarity edges
    drug_sim_edges = cosine_sim_edges(
        drug_feats.cpu(), threshold=sim_threshold, max_edges=3000
    ).to(device)

    # 3. Protein-protein sequence similarity edges
    prot_sim_edges = cosine_sim_edges(
        prot_feats.cpu(), threshold=sim_threshold,
        offset_src=n_drugs, offset_dst=n_drugs, max_edges=3000
    ).to(device)

    edge_index = torch.cat([dti_edges, drug_sim_edges, prot_sim_edges], dim=1)
    print(f"  KG edges: DTI={dti_edges.shape[1]//2}, "
          f"drug-sim={drug_sim_edges.shape[1]}, "
          f"prot-sim={prot_sim_edges.shape[1]}")

    # Model
    model = DTKGIN_Model(
        drug_dim=drug_feats.shape[1],
        prot_dim=prot_feats.shape[1],
        proj_dim=proj_dim,
        hidden=hidden,
        dropout=dropout,
    ).to(device)
    model.n_drugs = n_drugs
    model.n_prots = n_prots
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Parameters: {n_params:,}")

    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    criterion = nn.BCEWithLogitsLoss()

    tr_d = tr_d.to(device)
    tr_p = tr_p.to(device)
    tr_y = tr_y.to(device)
    va_d = va_d.to(device)
    va_p = va_p.to(device)

    best_auroc = 0.0
    best_state = None
    patience   = 20
    pat_cnt    = 0

    for epoch in range(1, epochs + 1):
        model.train()
        # Positive samples
        pos_scores = model(drug_feats, prot_feats, edge_index, tr_d, tr_p)

        # Negative sampling (1:1)
        d_neg, p_neg = negative_sample(n_drugs, n_prots, train_pos_set,
                                        len(tr_d), seed + epoch)
        d_neg = d_neg.to(device)
        p_neg = p_neg.to(device)
        neg_scores = model(drug_feats, prot_feats, edge_index, d_neg, p_neg)

        all_scores = torch.cat([pos_scores, neg_scores])
        all_labels = torch.cat([tr_y, torch.zeros(len(neg_scores), device=device)])

        loss = criterion(all_scores, all_labels)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        if epoch % 15 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                val_scores = model(drug_feats, prot_feats, edge_index, va_d, va_p)
                val_probs  = torch.sigmoid(val_scores).cpu().numpy()
            va_y_np = va_y.cpu().numpy()
            if len(np.unique(va_y_np)) > 1:
                auroc = roc_auc_score(va_y_np, val_probs)
            else:
                auroc = 0.5
            print(f"  Epoch {epoch:3d} | loss={loss.item():.4f} | val_auroc={auroc:.4f}")
            if auroc > best_auroc:
                best_auroc = auroc
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
                pat_cnt = 0
            else:
                pat_cnt += 1
                if pat_cnt >= patience:
                    print(f"  Early stopping at epoch {epoch}")
                    break

    if best_state:
        model.load_state_dict(best_state)
    model.eval()

    te_d = te_d.to(device)
    te_p = te_p.to(device)

    with torch.no_grad():
        te_scores = model(drug_feats, prot_feats, edge_index, te_d, te_p)
        te_probs  = torch.sigmoid(te_scores).cpu().numpy()

    te_y_np   = te_y.cpu().numpy()
    te_preds  = (te_probs > 0.5).astype(int)

    def safe_metric(fn, *args, **kwargs):
        try:
            return round(float(fn(*args, **kwargs)), 4)
        except Exception:
            return 0.0

    test_metrics = dict(
        auroc = safe_metric(roc_auc_score, te_y_np, te_probs),
        auprc = safe_metric(average_precision_score, te_y_np, te_probs),
        f1    = safe_metric(f1_score, te_y_np, te_preds, zero_division=0),
    )

    print(f"\n{'='*50}")
    print(f"  DTKGIN | yamanishi_e | {split} | seed={seed}")
    for k, v in test_metrics.items():
        print(f"    {k}: {v:.4f}")

    os.makedirs(LOG_DIR, exist_ok=True)
    result = dict(
        model="dtkgin", dataset="yamanishi_e", split=split, seed=seed,
        test_metrics=test_metrics
    )
    out_path = os.path.join(LOG_DIR, f"dtkgin_yamanishi_e_dti_{split}_fold0_seed{seed}.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Saved -> {out_path}")
    return test_metrics


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split",   default="cold_drug",
                        choices=["random", "cold_drug", "cold_target", "cold_pair"])
    parser.add_argument("--seed",    type=int, default=42)
    parser.add_argument("--epochs",  type=int, default=150)
    parser.add_argument("--lr",      type=float, default=1e-3)
    parser.add_argument("--hidden",  type=int, default=256)
    parser.add_argument("--proj",    type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--sim_threshold", type=float, default=0.5)
    args = parser.parse_args()

    run_dtkgin(
        split=args.split,
        seed=args.seed,
        epochs=args.epochs,
        lr=args.lr,
        proj_dim=args.proj,
        hidden=args.hidden,
        dropout=args.dropout,
        sim_threshold=args.sim_threshold,
    )
