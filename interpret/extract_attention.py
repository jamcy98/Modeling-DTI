"""
Phase 1 — Attention Weight Extraction

Extracts per-residue attention weights (from ProteinEncoder's AttentionPooling),
per-atom input-gradient saliency (drug GNN), and the GCA gate value for a single
drug–target pair.

Usage (from repo root):
    python -m interpret.extract_attention \
        --checkpoint checkpoints/hgnn_rnn_dti_phase3_ft_esm150m_1to5_luo_17_dti_cold_target_fold0_seed1.pt \
        --drug_id DB00619 \
        --protein_id P00533 \
        --dataset luo_17 \
        --emb_tag esm150m \
        --device cpu \
        --out results/attribution_example.npz

    # OR with raw SMILES / sequence:
    python -m interpret.extract_attention \
        --checkpoint <ckpt> --smiles "CC1=CC..." --sequence "MKTAY..." \
        --esm_tag esm150m --device cpu

Outputs a .npz file with keys:
    atom_importance     (N_atoms,)      — input-gradient saliency, normalised [0,1]
    residue_weights     (L,)            — AttentionPooling weights, sum to 1
    gate_mean           scalar          — mean GCA gate (>0.5 = drug context dominates)
    gate                (H,)            — full gate vector
    node_emb            (N_atoms, H)    — post-GAT atom embeddings (for Phase 2)
    bigru_hidden        (L, 2H)         — per-residue BiGRU states (for Phase 2)
    prediction          scalar          — raw logit (DTI) or affinity score (DTA)
    prediction_prob     scalar          — sigmoid(logit) for DTI, same as prediction for DTA
"""

import os
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')  # avoid OpenMP conflict on Windows
import sys
import json
import argparse
import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.data import Batch

# ── Make sure repo root is on path ───────────────────────────────────────────
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from model.hgnn_rnn_dti import HGNN_RNN_DTI
from config import MODEL as MODEL_CFG, DATASETS


# ── Drug graph builder (mirrors Dataset/10_preprocess_drugs.py) ───────────────

def _smiles_to_graph(smiles):
    """SMILES → PyG Data object, same feature set as preprocessing pipeline."""
    from rdkit import Chem
    from torch_geometric.data import Data

    ATOM_LIST = [
        "C","N","O","S","F","Si","P","Cl","Br","Mg","Na","Ca","Fe","As","Al",
        "I","B","V","K","Tl","Yb","Sb","Sn","Ag","Pd","Co","Se","Ti","Zn",
        "H","Li","Ge","Cu","Au","Ni","Cd","In","Mn","Zr","Cr","Pt","Hg","Pb","other"
    ]
    DEGREE_LIST = list(range(11))
    HYB_MAP = {
        Chem.rdchem.HybridizationType.S: 0,
        Chem.rdchem.HybridizationType.SP: 1,
        Chem.rdchem.HybridizationType.SP2: 2,
        Chem.rdchem.HybridizationType.SP3: 3,
        Chem.rdchem.HybridizationType.SP3D: 4,
        Chem.rdchem.HybridizationType.SP3D2: 5,
    }

    def one_hot(v, choices):
        enc = [0] * len(choices)
        enc[choices.index(v) if v in choices else len(choices) - 1] = 1
        return enc

    def atom_feat(a):
        sym = a.GetSymbol() if a.GetSymbol() in ATOM_LIST else "other"
        hyb_enc = [0] * 6; hyb_enc[HYB_MAP.get(a.GetHybridization(), 5)] = 1
        return (one_hot(sym, ATOM_LIST) + one_hot(min(a.GetDegree(), 10), DEGREE_LIST)
                + hyb_enc + [int(a.GetIsAromatic()), int(a.IsInRing()),
                              a.GetFormalCharge(), a.GetTotalNumHs()])

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit cannot parse SMILES: {smiles!r}")

    x = torch.tensor([atom_feat(a) for a in mol.GetAtoms()], dtype=torch.float)
    edges, attrs = [], []
    for b in mol.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        bf = [int(b.GetBondTypeAsDouble() == v) for v in (1.0, 1.5, 2.0, 3.0)]
        bf += [int(b.GetIsConjugated()), int(b.IsInRing())]
        edges += [[i, j], [j, i]]; attrs += [bf, bf]

    if edges:
        ei = torch.tensor(edges, dtype=torch.long).t().contiguous()
        ea = torch.tensor(attrs, dtype=torch.float)
    else:
        ei = torch.zeros((2, 0), dtype=torch.long)
        ea = torch.zeros((0, 6), dtype=torch.float)

    return Data(x=x, edge_index=ei, edge_attr=ea, smiles=smiles, num_nodes=x.size(0))


# ── Checkpoint loader ─────────────────────────────────────────────────────────

def load_model(ckpt_path, device):
    """Load HGNN_RNN_DTI from checkpoint. Reads task/dims from 'args' when present."""
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)

    # Locate the model state dict (training code saves under different keys)
    state = (ckpt.get('state_dict')
             or ckpt.get('model_state_dict')
             or (ckpt if 'drug_encoder.input_proj.0.weight' in ckpt else None))
    if state is None:
        raise ValueError(f"Cannot find model weights in checkpoint: {list(ckpt.keys())}")

    # Prefer explicit args saved at training time
    args = ckpt.get('args', {})

    task = args.get('task', None)
    if task is None:
        head_w = state.get('head.3.weight')
        task = 'dta' if (head_w is not None and head_w.shape[0] == 1) else 'dti'

    hidden_dim = args.get('hidden_dim', None)
    if hidden_dim is None:
        w = state.get('drug_encoder.output_proj.0.weight') or \
            state.get('drug_encoder.output_proj_no_cb.0.weight')
        hidden_dim = w.shape[0] if w is not None else MODEL_CFG.get('hidden_dim', 256)

    prot_proj_w = state.get('prot_input_proj.weight')
    esm_dim = prot_proj_w.shape[1] if prot_proj_w is not None else 320

    model = HGNN_RNN_DTI(
        task=task,
        node_feat_dim=MODEL_CFG.get('node_feat_dim', 65),
        esm_dim=esm_dim,
        hidden_dim=hidden_dim,
        gat_layers=MODEL_CFG.get('gat_layers', 3),
        gat_heads=MODEL_CFG.get('gat_heads', 8),
        gru_layers=MODEL_CFG.get('gru_layers', 2),
        chemberta_dim=MODEL_CFG.get('chemberta_dim', 768),
        fusion_heads=MODEL_CFG.get('fusion_heads', 8),
        dropout=0.0,
    ).to(device)

    model.load_state_dict(state, strict=False)
    model.eval()
    print(f"  Loaded {task.upper()} model | esm_dim={esm_dim} | hidden_dim={hidden_dim}")
    return model


# ── Drug graph lookup / build ─────────────────────────────────────────────────

def get_drug_graph(smiles=None, drug_id=None, dataset=None, device='cpu'):
    """Return a batched PyG Data object for a single drug."""
    if smiles is not None:
        graph = _smiles_to_graph(smiles)
    elif drug_id is not None and dataset is not None:
        graphs_path = os.path.join(
            _REPO, 'Dataset', 'processed', 'drug_graphs',
            f'{dataset}_drug_graphs.pt'
        )
        graphs = torch.load(graphs_path, map_location='cpu', weights_only=False)
        if drug_id not in graphs:
            raise KeyError(f"Drug '{drug_id}' not found in {dataset} drug graph cache.")
        graph = graphs[drug_id]
    else:
        raise ValueError("Provide either --smiles or both --drug_id and --dataset.")

    # Fake batch index (single molecule)
    graph.batch = torch.zeros(graph.num_nodes, dtype=torch.long)
    return Batch.from_data_list([graph]).to(device)


# ── Protein embedding lookup ──────────────────────────────────────────────────

def get_protein_emb(sequence=None, protein_id=None, dataset=None,
                    emb_tag='esm150m', device='cpu'):
    """Return a (1, L, D) protein embedding tensor."""
    if sequence is not None:
        # Encode on-the-fly using ESM-2
        print("  Encoding protein sequence with ESM-2 (on-the-fly)...")
        emb = _encode_sequence_esm2(sequence, emb_tag, device)  # (L, D)
        return emb.unsqueeze(0).to(device)  # (1, L, D)
    elif protein_id is not None and dataset is not None:
        proc_dir = os.path.join(_REPO, 'Dataset', 'processed', 'protein_embeddings')
        if emb_tag and emb_tag != 'esm8m':
            emb_path = os.path.join(proc_dir, f'{dataset}_{emb_tag}_protein_embeddings.npy')
            id_path  = os.path.join(proc_dir, f'{dataset}_{emb_tag}_protein_ids.json')
            if not os.path.exists(id_path):
                id_path = os.path.join(proc_dir, f'{dataset}_protein_ids.json')
        else:
            emb_path = os.path.join(proc_dir, f'{dataset}_protein_embeddings.npy')
            id_path  = os.path.join(proc_dir, f'{dataset}_protein_ids.json')

        embeddings = np.load(emb_path)
        with open(id_path) as f:
            protein_ids = json.load(f)

        if protein_id not in protein_ids:
            raise KeyError(f"Protein '{protein_id}' not found in {dataset} embedding cache.")

        idx = protein_ids.index(protein_id)
        emb = torch.tensor(embeddings[idx], dtype=torch.float)  # (D,) mean-pooled or (L, D) sequence
        # Add batch dimension → (1, D) or (1, L, D)
        emb = emb.unsqueeze(0)
        if emb.dim() == 2:
            print("  NOTE: protein embeddings are mean-pooled — per-residue weights unavailable.")
            print("        For per-residue attribution, use --sequence instead.")
        return emb.to(device)
    else:
        raise ValueError("Provide either --sequence or both --protein_id and --dataset.")


def _encode_sequence_esm2(sequence, emb_tag, device):
    """Encode a single protein sequence using ESM-2."""
    model_name_map = {
        'esm150m': 'facebook/esm2_t30_150M_UR50D',
        'esm8m':   'facebook/esm2_t6_8M_UR50D',
        'esm650m': 'facebook/esm2_t33_650M_UR50D',
    }
    model_name = model_name_map.get(emb_tag, 'facebook/esm2_t6_8M_UR50D')
    from transformers import AutoTokenizer, EsmModel
    tok = AutoTokenizer.from_pretrained(model_name)
    esm = EsmModel.from_pretrained(model_name).to(device).eval()
    with torch.no_grad():
        inputs = tok(sequence, return_tensors='pt', truncation=True,
                     max_length=1024).to(device)
        out = esm(**inputs)
        # (1, L+2, D) → remove CLS/EOS tokens → (L, D)
        hidden = out.last_hidden_state.squeeze(0)[1:-1]
    return hidden.cpu()


# ── Per-atom input gradient saliency ─────────────────────────────────────────

def compute_atom_saliency(model, drug_batch, protein_emb, task):
    """
    Compute per-atom saliency via gradient of prediction score w.r.t. input node features.

    Returns:
        atom_importance  (N_atoms,)  — L2 norm of gradient, normalised to [0,1]
        raw_grad         (N_atoms, feat_dim)
    """
    # Clone and enable gradients on input atom features
    x_orig = drug_batch.x.clone().detach().requires_grad_(True)
    drug_batch = drug_batch.clone()
    drug_batch.x = x_orig

    model.eval()
    with torch.enable_grad():
        # Project protein if needed
        prot = protein_emb.clone()
        if prot.shape[-1] != 320:
            prot = model.prot_input_proj(prot)

        drug_repr = model.drug_encoder(drug_batch)
        prot_repr = model.protein_encoder(prot)
        fused = model.fusion(drug_repr, prot_repr)
        logits = model.head(fused)

        if task == 'dti':
            # Gradient of positive-class logit
            score = logits[0, 1]
        else:
            score = logits[0, 0]

        score.backward()

    grad = x_orig.grad  # (N_atoms, feat_dim)
    if grad is None:
        return torch.zeros(drug_batch.num_nodes), None

    importance = grad.norm(dim=-1)  # (N_atoms,)
    # Normalise to [0, 1]
    lo, hi = importance.min(), importance.max()
    if hi > lo:
        importance = (importance - lo) / (hi - lo)
    return importance.detach(), grad.detach()


# ── Main extraction function ──────────────────────────────────────────────────

def extract(
    ckpt_path,
    smiles=None, drug_id=None,
    sequence=None, protein_id=None,
    dataset=None,
    emb_tag='esm150m',
    device='cpu',
    out_path=None,
):
    """
    Full Phase 1 extraction pipeline.

    Returns a dict with all attribution data. Optionally saves to .npz.
    """
    device = torch.device(device)
    print(f"\n[extract_attention] Loading checkpoint: {ckpt_path}")
    model = load_model(ckpt_path, device)

    print("  Building drug graph...")
    drug_batch = get_drug_graph(smiles=smiles, drug_id=drug_id,
                                dataset=dataset, device=device)
    n_atoms = drug_batch.num_nodes

    print("  Loading protein embedding...")
    protein_emb = get_protein_emb(sequence=sequence, protein_id=protein_id,
                                  dataset=dataset, emb_tag=emb_tag, device=device)

    # ── Attention weights (no gradients needed) ──────────────────────────────
    print("  Running attention weight extraction...")
    with torch.no_grad():
        prot_for_attn = protein_emb.clone()
        if prot_for_attn.shape[-1] != 320:
            prot_for_attn = model.prot_input_proj(prot_for_attn)

        weights_dict = model.get_attention_weights(drug_batch, prot_for_attn)

    logits = weights_dict['logits']
    residue_weights = weights_dict['residue_weights']  # (1, L) or None
    gate = weights_dict['gate']                        # (1, H)
    node_emb = weights_dict['node_emb']                # (N, H)
    bigru_hidden = weights_dict['bigru_hidden']         # (1, L, 2H) or None

    # Prediction value
    if model.task == 'dti':
        prob = torch.softmax(logits, dim=-1)[0, 1].item()
        pred = logits[0, 1].item()
    else:
        prob = logits[0, 0].item()
        pred = logits[0, 0].item()

    print(f"  Prediction: {pred:.4f}  (prob={prob:.4f})")

    # Gate summary
    gate_vec = gate[0]  # (H,)
    gate_mean = gate_vec.mean().item()
    print(f"  Gate mean: {gate_mean:.3f}  ({'drug context dominates' if gate_mean > 0.5 else 'protein context dominates'})")

    # ── Per-atom saliency via input gradients ─────────────────────────────────
    print("  Computing per-atom input-gradient saliency...")
    atom_importance, _ = compute_atom_saliency(model, drug_batch, protein_emb, model.task)

    # ── Residue weights ───────────────────────────────────────────────────────
    if residue_weights is not None:
        res_w = residue_weights[0].cpu().numpy()  # (L,)
        print(f"  Residue weights: L={len(res_w)}, top-5 positions={np.argsort(res_w)[-5:][::-1].tolist()}")
    else:
        res_w = None
        print("  WARNING: residue weights unavailable (mean-pooled protein path).")

    # ── Package results ───────────────────────────────────────────────────────
    result = {
        'atom_importance':  atom_importance.cpu().numpy(),     # (N,)
        'residue_weights':  res_w,                              # (L,) or None
        'gate_mean':        np.float32(gate_mean),
        'gate':             gate_vec.cpu().numpy(),             # (H,)
        'node_emb':         node_emb.cpu().numpy(),             # (N, H)
        'bigru_hidden':     bigru_hidden[0].cpu().numpy() if bigru_hidden is not None else None,  # (L, 2H)
        'prediction':       np.float32(pred),
        'prediction_prob':  np.float32(prob),
        'n_atoms':          n_atoms,
        'task':             model.task,
    }

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        # numpy savez can't handle None — use sentinel -1 array
        save_dict = {k: v if v is not None else np.array([-1]) for k, v in result.items()
                     if not isinstance(v, str)}
        save_dict['task'] = np.array([model.task])
        np.savez_compressed(out_path, **save_dict)
        print(f"  Saved attribution to: {out_path}")

    return result


# ── Sanity check helpers ──────────────────────────────────────────────────────

def sanity_check(result):
    """
    Run the three sanity checks from the Phase 1 plan and print a report.
    """
    import scipy.stats as stats

    print("\n-- Sanity Checks --------------------------------------------------")

    # 1. Non-uniformity of residue weights
    rw = result.get('residue_weights')
    if rw is not None:
        L = len(rw)
        entropy = -np.sum(rw * np.log(rw + 1e-12))
        max_entropy = np.log(L)
        ratio = entropy / max_entropy if max_entropy > 0 else 1.0
        flag = "PASS" if ratio < 0.8 else "WARN"
        print(f"  [Non-uniformity] entropy/max_entropy = {ratio:.3f}  [{flag}]")
        print(f"    (< 0.8 means attention is not flat over {L} residues)")
    else:
        print("  [Non-uniformity] SKIP — no residue weights available")

    # 2. Atom saliency non-zero
    ai = result.get('atom_importance')
    if ai is not None:
        nonzero = np.sum(ai > 0.01) / len(ai)
        flag = "PASS" if nonzero > 0.2 else "WARN"
        print(f"  [Atom saliency]  fraction of atoms with importance > 0.01 = {nonzero:.2f}  [{flag}]")

    # 3. Gate meaning
    gm = float(result.get('gate_mean', 0.5))
    print(f"  [Gate]           mean gate = {gm:.3f}  "
          f"({'drug context' if gm > 0.5 else 'protein context'} dominates in fusion)")

    print("--------------------------------------------------------------------")


# ── CLI --------------------------------------------------------------------───

def main():
    ap = argparse.ArgumentParser(description="Phase 1: extract attention weights from H-GNN-RNN-DTI")
    ap.add_argument('--checkpoint', required=True, help="Path to trained .pt checkpoint")

    # Drug input (one of two modes)
    drug_grp = ap.add_mutually_exclusive_group(required=True)
    drug_grp.add_argument('--smiles',   help="Raw SMILES string")
    drug_grp.add_argument('--drug_id',  help="Drug ID in preprocessed dataset")

    # Protein input (one of two modes)
    prot_grp = ap.add_mutually_exclusive_group(required=True)
    prot_grp.add_argument('--sequence',    help="Raw amino-acid sequence string")
    prot_grp.add_argument('--protein_id',  help="Protein ID in preprocessed dataset")

    ap.add_argument('--dataset',  default=None, help="Dataset name (required with --drug_id / --protein_id)")
    ap.add_argument('--emb_tag',  default='esm150m', help="Protein embedding variant tag (default: esm150m)")
    ap.add_argument('--device',   default='cpu')
    ap.add_argument('--out',      default=None, help="Output .npz path")
    ap.add_argument('--sanity',   action='store_true', help="Run sanity checks after extraction")

    args = ap.parse_args()

    result = extract(
        ckpt_path=args.checkpoint,
        smiles=args.smiles,
        drug_id=args.drug_id,
        sequence=args.sequence,
        protein_id=args.protein_id,
        dataset=args.dataset,
        emb_tag=args.emb_tag,
        device=args.device,
        out_path=args.out,
    )

    if args.sanity:
        sanity_check(result)

    # Brief summary
    ai = result['atom_importance']
    rw = result['residue_weights']
    print(f"\n-- Attribution Summary ----------------------------------------------")
    print(f"  Drug: {result['n_atoms']} atoms | top atom index: {int(np.argmax(ai))}, score: {ai.max():.3f}")
    if rw is not None:
        print(f"  Protein: {len(rw)} residues | top residue index: {int(np.argmax(rw))}, weight: {rw.max():.4f}")
    print(f"  Prediction: {result['prediction']:.4f} (prob={result['prediction_prob']:.4f})")
    print(f"  Gate mean: {result['gate_mean']:.3f}")
    print("--------------------------------------------------------------------")


if __name__ == '__main__':
    main()
