"""
GSRF-DTI re-implementation (Zhu et al., 2024, BMC Biology).

Core idea: GraphSAGE on a heterogeneous network (DDI + PPI + DTI) learns drug
and protein node embeddings; a Random Forest classifier operates on the
concatenated pair embeddings.

Key simplifications vs. original:
  - Use pre-computed molecular graph features (mean-pooled atom features, 65-dim)
    and ESM-2 protein embeddings (1280-dim) as node features instead of DeepWalk.
  - GraphSAGE trained end-to-end with BCELoss on DTI pairs instead of their
    separate self-supervised DeepWalk → supervised GraphSAGE pipeline.
  - DDI and PPI edges come from Luo's mat_drug_drug.txt / mat_protein_protein.txt.
  - RF trained on [drug_emb || prot_emb || drug_emb * prot_emb] features.

Usage:
    python baselines/gsrf_dti.py --split random --seed 42
    python baselines/gsrf_dti.py --split cold_drug --seed 42
"""

import os, sys, json, argparse, random, time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_LUO   = os.path.join(ROOT, "Dataset", "raw", "luo_17")
PROC      = os.path.join(ROOT, "Dataset", "processed")
LOG_DIR   = os.path.join(ROOT, "logs")


# ── Data loading ───────────────────────────────────────────────────────────────

def load_id_map(path, limit=None):
    """
    Return {id_str: row_index} from a dict-map file (ID:Name per line).
    Only the first `limit` non-empty lines are used (to match the matrix size).
    """
    id_map = {}
    with open(path) as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            stripped = line.strip()
            if not stripped:
                continue
            id_str = stripped.split(":")[0]
            id_map[id_str] = i
    return id_map


def load_adj_matrix(path):
    """Load a space-separated 0/1 adjacency matrix."""
    rows = []
    with open(path) as f:
        for line in f:
            rows.append([int(x) for x in line.strip().split()])
    return np.array(rows, dtype=np.float32)


def build_edge_index(adj, row_offset=0, col_offset=0, directed=False):
    """Convert dense adjacency matrix to COO edge list."""
    src_list, dst_list = [], []
    r, c = np.where(adj > 0)
    for i, j in zip(r, c):
        src_list.append(int(i) + row_offset)
        dst_list.append(int(j) + col_offset)
        if not directed:
            src_list.append(int(j) + col_offset)
            dst_list.append(int(i) + row_offset)
    return torch.tensor([src_list, dst_list], dtype=torch.long)


def load_node_features(drug_id_map, prot_id_map, proj_dim=128):
    """
    Load and project node features.
      - Drugs : mean-pool atom features from PyG drug graphs (65-dim).
      - Proteins: mean-pool ESM-2 residue embeddings (1280-dim).
    Returns:
      drug_feats [n_drugs, 65], prot_feats [n_prots, 1280]
    """
    # Drugs
    graphs = torch.load(
        os.path.join(PROC, "drug_graphs", "luo_17_drug_graphs.pt"),
        weights_only=False
    )
    n_drugs = len(drug_id_map)
    drug_feat_dim = next(iter(graphs.values())).x.shape[1]
    drug_feats = torch.zeros(n_drugs, drug_feat_dim)
    for drug_id, idx in drug_id_map.items():
        if drug_id in graphs:
            drug_feats[idx] = graphs[drug_id].x.mean(0)

    # Proteins
    emb_path = os.path.join(PROC, "protein_embeddings", "luo_17_protein_embeddings.npy")
    id_path  = os.path.join(PROC, "protein_embeddings", "luo_17_protein_ids.json")
    emb = np.load(emb_path)
    with open(id_path) as f:
        prot_ids = json.load(f)
    prot_id_to_emb_idx = {pid: i for i, pid in enumerate(prot_ids)}

    n_prots = len(prot_id_map)
    if emb.ndim == 3:
        emb = emb.mean(1)  # (N, L, 1280) → (N, 1280)
    prot_feat_dim = emb.shape[1]
    prot_feats = torch.zeros(n_prots, prot_feat_dim)
    for prot_id, idx in prot_id_map.items():
        if prot_id in prot_id_to_emb_idx:
            prot_feats[idx] = torch.tensor(emb[prot_id_to_emb_idx[prot_id]], dtype=torch.float32)

    return drug_feats, prot_feats


def load_split(split, drug_id_map, prot_id_map):
    split_path = os.path.join(
        PROC, "splits",
        f"luo_17_dti_labels_1to1_{split}_split.json"
    )
    labels_path = os.path.join(PROC, "labels", "luo_17_dti_labels_1to1.csv")
    df = pd.read_csv(labels_path)

    with open(split_path) as f:
        splits = json.load(f)
    s = splits["fold_0"]

    def to_pairs(indices):
        rows = df.iloc[indices]
        pairs, labels = [], []
        for _, row in rows.iterrows():
            d = drug_id_map.get(row["drug_id"])
            p = prot_id_map.get(row["protein_id"])
            if d is not None and p is not None:
                pairs.append((d, p))
                labels.append(int(row["label"]))
        return pairs, labels

    return to_pairs(s["train"]), to_pairs(s["val"]), to_pairs(s["test"])


# ── Model ──────────────────────────────────────────────────────────────────────

class ProjectionHead(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.proj = nn.Linear(in_dim, out_dim)
        self.bn   = nn.BatchNorm1d(out_dim)

    def forward(self, x):
        return torch.relu(self.bn(self.proj(x)))


class GSRF_GNN(nn.Module):
    """2-layer GraphSAGE for node embedding."""
    def __init__(self, drug_dim, prot_dim, proj_dim=128, hidden=256):
        super().__init__()
        self.drug_proj = ProjectionHead(drug_dim, proj_dim)
        self.prot_proj = ProjectionHead(prot_dim, proj_dim)
        self.sage1 = SAGEConv(proj_dim, hidden)
        self.sage2 = SAGEConv(hidden, hidden)
        self.bn1   = nn.BatchNorm1d(hidden)
        self.drop  = nn.Dropout(0.3)
        # DTI prediction head (used during GNN training only)
        self.dti_head = nn.Linear(hidden * 3, 1)

    def encode(self, drug_raw, prot_raw, edge_index):
        # Project to common dim
        drug_emb = self.drug_proj(drug_raw)
        prot_emb = self.prot_proj(prot_raw)
        x = torch.cat([drug_emb, prot_emb], dim=0)

        x = torch.relu(self.bn1(self.sage1(x, edge_index)))
        x = self.drop(x)
        x = self.sage2(x, edge_index)
        return x

    def forward(self, drug_raw, prot_raw, edge_index, drug_idx, prot_idx):
        emb = self.encode(drug_raw, prot_raw, edge_index)
        d_emb = emb[drug_idx]
        p_emb = emb[prot_idx]
        pair_feat = torch.cat([d_emb, p_emb, d_emb * p_emb], dim=-1)
        return self.dti_head(pair_feat).squeeze(-1)


# ── Training ───────────────────────────────────────────────────────────────────

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def run_gsrf(split, seed, epochs=100, lr=1e-3, proj_dim=128, hidden=256, n_estimators=200):
    set_seed(seed)
    device = torch.device("cpu")

    # Load raw adjacency matrices first (to get n_drugs, n_prots)
    print("Loading adjacency matrices...")
    adj_dd = load_adj_matrix(os.path.join(RAW_LUO, "mat_drug_drug.txt"))
    adj_pp = load_adj_matrix(os.path.join(RAW_LUO, "mat_protein_protein.txt"))
    n_drugs, n_prots = adj_dd.shape[0], adj_pp.shape[0]  # 708, 1512

    # Load ID maps (limit to matrix size — dict files may contain extra entries)
    drug_id_map = load_id_map(os.path.join(RAW_LUO, "drug_dict_map.txt"),  limit=n_drugs)
    prot_id_map = load_id_map(os.path.join(RAW_LUO, "protein_dict_map.txt"), limit=n_prots)

    # Load node features
    print("Loading node features...")
    drug_feats, prot_feats = load_node_features(drug_id_map, prot_id_map, proj_dim)
    drug_feats = drug_feats.to(device)
    prot_feats = prot_feats.to(device)

    # Load splits
    print(f"Loading split: {split}...")
    (train_pairs, train_labels), (val_pairs, val_labels), (test_pairs, test_labels) = \
        load_split(split, drug_id_map, prot_id_map)

    # Build graph edges
    # DDI: within drug nodes (0..n_drugs-1)
    ddi_edges = build_edge_index(adj_dd, row_offset=0, col_offset=0)
    # PPI: within protein nodes (n_drugs..n_drugs+n_prots-1)
    ppi_edges = build_edge_index(adj_pp, row_offset=n_drugs, col_offset=n_drugs)

    # DTI edges from training set only (drug_node → protein_node)
    train_d_nodes = [d for d, p in train_pairs]
    train_p_nodes = [p + n_drugs for d, p in train_pairs]
    dti_edges = torch.tensor([
        train_d_nodes + train_p_nodes,
        train_p_nodes + train_d_nodes
    ], dtype=torch.long)

    # Combine all edges
    edge_index = torch.cat([ddi_edges, ppi_edges, dti_edges], dim=1).to(device)

    print(f"  Graph: {n_drugs} drugs + {n_prots} proteins = {n_drugs + n_prots} nodes")
    print(f"  Edges: DDI={ddi_edges.shape[1]//2}, PPI={ppi_edges.shape[1]//2}, "
          f"DTI-train={len(train_pairs)}")
    print(f"  Train={len(train_pairs)}, Val={len(val_pairs)}, Test={len(test_pairs)}")

    # Build model
    model = GSRF_GNN(
        drug_dim=drug_feats.shape[1],
        prot_dim=prot_feats.shape[1],
        proj_dim=proj_dim,
        hidden=hidden
    ).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Parameters: {n_params:,}")

    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss()
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    # Prepare tensors
    train_d = torch.tensor([d for d, p in train_pairs], dtype=torch.long, device=device)
    train_p = torch.tensor([p for d, p in train_pairs], dtype=torch.long, device=device)
    train_y = torch.tensor(train_labels, dtype=torch.float32, device=device)

    val_d   = torch.tensor([d for d, p in val_pairs], dtype=torch.long, device=device)
    val_p   = torch.tensor([p for d, p in val_pairs], dtype=torch.long, device=device)
    val_y   = np.array(val_labels)

    # Train GNN
    best_auroc = 0.0
    best_state = None
    patience   = 20
    pat_cnt    = 0

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(drug_feats, prot_feats, edge_index, train_d, train_p)
        loss = criterion(logits, train_y)
        loss.backward()
        optimizer.step()
        scheduler.step()

        if epoch % 10 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                val_logits = model(drug_feats, prot_feats, edge_index, val_d, val_p)
                val_probs  = torch.sigmoid(val_logits).cpu().numpy()
            if len(np.unique(val_y)) > 1:
                auroc = roc_auc_score(val_y, val_probs)
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

    # Load best model and extract embeddings
    if best_state:
        model.load_state_dict(best_state)
    model.eval()

    with torch.no_grad():
        all_emb = model.encode(drug_feats, prot_feats, edge_index).cpu().numpy()

    drug_emb = all_emb[:n_drugs]
    prot_emb = all_emb[n_drugs:]

    def pair_features(pairs):
        if not pairs:
            return np.empty((0, hidden * 3))
        d_idx = [d for d, p in pairs]
        p_idx = [p for d, p in pairs]
        d = drug_emb[d_idx]
        p = prot_emb[p_idx]
        return np.concatenate([d, p, d * p], axis=1)

    X_train = pair_features(train_pairs)
    X_val   = pair_features(val_pairs)
    X_test  = pair_features(test_pairs)
    y_train = np.array(train_labels)
    y_val   = np.array(val_labels)
    y_test  = np.array(test_labels)

    # Train Random Forest
    print("  Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=n_estimators, n_jobs=-1, random_state=seed)
    rf.fit(X_train, y_train)

    def evaluate(X, y, tag):
        if len(X) == 0 or len(np.unique(y)) < 2:
            print(f"  {tag}: insufficient data")
            return {}
        probs = rf.predict_proba(X)[:, 1]
        preds = (probs > 0.5).astype(int)
        metrics = dict(
            auroc = round(roc_auc_score(y, probs), 4),
            auprc = round(average_precision_score(y, probs), 4),
            f1    = round(f1_score(y, preds, zero_division=0), 4),
        )
        print(f"  {tag}: " + "  ".join(f"{k}={v}" for k, v in metrics.items()))
        return metrics

    print(f"\n{'='*50}")
    print(f"  GSRF-DTI | luo_17 | {split} | seed={seed}")
    val_metrics  = evaluate(X_val,  y_val,  "Val ")
    test_metrics = evaluate(X_test, y_test, "Test")

    # Save
    os.makedirs(LOG_DIR, exist_ok=True)
    result = dict(
        model="gsrf_dti", dataset="luo_17", split=split, seed=seed,
        val_metrics=val_metrics, test_metrics=test_metrics
    )
    out_path = os.path.join(LOG_DIR, f"gsrf_dti_luo_17_dti_{split}_fold0_seed{seed}.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Saved -> {out_path}")
    return test_metrics


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split",  default="random",
                        choices=["random", "cold_drug", "cold_target", "cold_pair"])
    parser.add_argument("--seed",   type=int, default=42)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--lr",     type=float, default=1e-3)
    parser.add_argument("--hidden", type=int, default=256)
    parser.add_argument("--proj",   type=int, default=128)
    parser.add_argument("--rf_trees", type=int, default=200)
    args = parser.parse_args()

    run_gsrf(
        split=args.split,
        seed=args.seed,
        epochs=args.epochs,
        lr=args.lr,
        proj_dim=args.proj,
        hidden=args.hidden,
        n_estimators=args.rf_trees,
    )
