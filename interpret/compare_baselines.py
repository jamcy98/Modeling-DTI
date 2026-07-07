"""
Phase 6 -- Baseline Attribution Comparison

Compares four attribution methods against each other and a random baseline:

Drug (atom) attributions:
    random     -- uniform random scores (null hypothesis)
    input_grad -- Phase 1: input-gradient saliency ||grad_x||_2
    drug_cam   -- Phase 2: Graph Grad-CAM on last ResidualGATBlock
    ensemble   -- 0.5*input_grad + 0.5*drug_cam

Protein (residue) attributions (when 3D embeddings available):
    random      -- uniform random
    attn_pool   -- AttentionPooling softmax weights
    protein_cam -- BiGRU Grad-CAM
    ensemble    -- 0.5*attn_pool + 0.5*protein_cam

Metrics used:
    - Faithfulness AUC (drug, from Phase 4 atom-masking)
    - Pharmacophore mean average precision (drug, from Phase 4)
    - PDB AUROC / Precision@K (protein, from Phase 5 DHFR case)
    - Spearman rho between each method and ensemble (stability proxy)

Usage:
    python -m interpret.compare_baselines \
        --checkpoint checkpoints/hgnn_rnn_dti_yamanishi_e_dti_cold_drug_fold0_seed1_best.pt \
        --drug_smiles "CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)N[C@@H](CCC(=O)O)C(=O)O" \
        --protein_id P00374 \
        --dataset yamanishi_e \
        --pdb_npz paper/figures/interpretability/case_studies_cd/cs_D00142_P00374.npz \
        --device cpu
"""

import os
import sys
import json
import numpy as np
import torch

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from scipy.integrate import trapezoid as _trapz

from interpret.extract_attention import (load_model, _smiles_to_graph,
                                          compute_atom_saliency)
from interpret.grad_cam import (compute_all_grad_cam, ensemble_attribution,
                                 drug_grad_cam, protein_grad_cam)
from interpret.metrics import (compute_faithfulness, compute_pharmacophore_precision,
                                _get_pred_score)


# ── Drug attributions ─────────────────────────────────────────────────────────

def compute_drug_attributions(model, drug_batch, protein_emb, task, seed=0):
    """
    Returns dict: method -> (N_atoms,) normalised [0,1] scores.
    """
    N = drug_batch.x.shape[0]
    rng = np.random.RandomState(seed)

    # Random baseline
    rand = rng.rand(N).astype(np.float32)
    rand = rand / rand.max() if rand.max() > 0 else rand

    # Input gradient (Phase 1)
    atom_imp, _ = compute_atom_saliency(model, drug_batch, protein_emb, task)
    atom_imp = atom_imp.numpy()

    # Grad-CAM on last GAT block (Phase 2)
    cam_res = compute_all_grad_cam(model, drug_batch, protein_emb, task)
    drug_cam = cam_res['drug_cam'].numpy()

    # Ensemble
    ens = ensemble_attribution(atom_imp, drug_cam, alpha=0.5)

    return {
        'random':     rand,
        'input_grad': atom_imp,
        'drug_cam':   drug_cam,
        'ensemble':   ens,
    }


# ── Protein attributions (if per-residue embeddings available) ────────────────

def compute_protein_attributions(model, drug_batch, protein_emb_3d, task, seed=0):
    """
    Returns dict: method -> (L,) normalised scores.
    Requires 3D protein embeddings (B, L, D).
    """
    L = protein_emb_3d.shape[1]
    rng = np.random.RandomState(seed)

    # Random
    rand = rng.rand(L).astype(np.float32)
    rand = rand / rand.max()

    # Get attention weights + Grad-CAM
    with torch.no_grad():
        prot_proj = protein_emb_3d
        if (hasattr(model, 'prot_input_proj') and model.prot_input_proj is not None
                and prot_proj.shape[-1] == model.prot_input_proj.weight.shape[1]):
            prot_proj = model.prot_input_proj(prot_proj)
        attn_dict = model.get_attention_weights(drug_batch, prot_proj)

    attn_w = (attn_dict['residue_weights'][0].numpy()
              if attn_dict['residue_weights'] is not None else None)

    cam_res = compute_all_grad_cam(
        model, drug_batch, protein_emb_3d, task,
        protein_emb_seq=protein_emb_3d, layer_idx=-1)
    prot_cam = cam_res['protein_cam'].numpy() if cam_res['protein_cam'] is not None else None

    prot_ens = None
    if attn_w is not None and prot_cam is not None:
        prot_ens = ensemble_attribution(attn_w, prot_cam, alpha=0.5)
    elif attn_w is not None:
        prot_ens = attn_w
    elif prot_cam is not None:
        prot_ens = prot_cam

    return {
        'random':      rand,
        'attn_pool':   attn_w,
        'protein_cam': prot_cam,
        'ensemble':    prot_ens,
    }


# ── Evaluate drug methods ─────────────────────────────────────────────────────

def evaluate_drug_methods(model, drug_batch, protein_emb, mol, task,
                           attributions, k_fracs, n_random=10):
    """
    Run faithfulness + pharmacophore for each drug attribution method.
    Returns dict: method -> {faithfulness, pharmacophore}
    """
    results = {}
    for method, scores in attributions.items():
        print(f'    Evaluating drug method: {method}')
        faith = compute_faithfulness(model, drug_batch, protein_emb, task,
                                      atom_scores=scores, k_fracs=k_fracs,
                                      n_random=n_random)
        pharm = compute_pharmacophore_precision(mol, scores, k_fracs=k_fracs)
        results[method] = {'faithfulness': faith, 'pharmacophore': pharm}
    return results


# ── Evaluate protein methods against PDB binding site ────────────────────────

def evaluate_protein_methods(attributions, binding_0idx, n_residues, k_fracs):
    """
    AUROC + Precision@K + Recall@K for each protein attribution method.
    Returns dict: method -> {auroc, precision, recall}
    """
    binding_set = set(binding_0idx)
    y_true = np.zeros(n_residues)
    for idx in binding_set:
        if 0 <= idx < n_residues:
            y_true[idx] = 1

    results = {}
    for method, scores in attributions.items():
        if scores is None:
            results[method] = None
            continue
        sc = np.asarray(scores)[:n_residues]

        if y_true.sum() in (0, n_residues):
            auroc = None
        else:
            auroc = float(roc_auc_score(y_true, sc))

        prec, rec = [], []
        for frac in k_fracs:
            k = max(1, int(round(frac * n_residues)))
            top_k = set(np.argsort(sc)[::-1][:k].tolist())
            prec.append(float(len(top_k & binding_set) / k))
            rec.append(float(len(top_k & binding_set) / len(binding_set)) if binding_set else 0.0)

        results[method] = {'auroc': auroc, 'precision': prec, 'recall': rec}
    return results


# ── Stability: pairwise Spearman rho ─────────────────────────────────────────

def pairwise_spearman(attributions):
    """Compute pairwise Spearman rho between all attribution method pairs."""
    methods = [m for m, s in attributions.items() if s is not None]
    matrix = {}
    for m1 in methods:
        for m2 in methods:
            if m1 <= m2:
                rho, _ = spearmanr(attributions[m1], attributions[m2])
                matrix[(m1, m2)] = float(rho)
    return matrix


# ── Plotting ─────────────────────────────────────────────────────────────────

_COLORS = {
    'random':      '#aaaaaa',
    'input_grad':  '#1f77b4',
    'drug_cam':    '#ff7f0e',
    'ensemble':    '#d62728',
    'attn_pool':   '#2ca02c',
    'protein_cam': '#9467bd',
}
_LABELS = {
    'random':      'Random',
    'input_grad':  'Input Grad (Phase 1)',
    'drug_cam':    'Grad-CAM (Phase 2)',
    'ensemble':    'Ensemble (P1+P2)',
    'attn_pool':   'Attn Pool',
    'protein_cam': 'Protein GradCAM',
}


def plot_drug_comparison(drug_eval, k_fracs, out_path, title=None, dpi=200):
    """Two-panel bar chart: faithfulness AUC and pharmacophore AP."""
    methods = list(drug_eval.keys())
    colors  = [_COLORS.get(m, 'grey') for m in methods]
    labels  = [_LABELS.get(m, m) for m in methods]

    faith_aucs = [drug_eval[m]['faithfulness']['faithfulness_auc'] for m in methods]
    rand_aucs  = [drug_eval[m]['faithfulness']['random_auc']       for m in methods]
    pharm_aps  = [drug_eval[m]['pharmacophore']['average_precision']  for m in methods]

    x = np.arange(len(methods))
    w = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # Panel 1: Faithfulness AUC
    ax = axes[0]
    ax.bar(x - w/2, faith_aucs, w, color=colors, alpha=0.85, label='Attribution AUC')
    ax.bar(x + w/2, rand_aucs,  w, color=colors, alpha=0.40, label='Random AUC', hatch='//')
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=8)
    ax.set_ylabel('Faithfulness AUC', fontsize=10)
    ax.set_title('Faithfulness (atom masking AUC)', fontsize=10)
    ax.legend(fontsize=8)

    # Annotate advantage
    for xi, (fa, ra) in enumerate(zip(faith_aucs, rand_aucs)):
        adv = fa - ra
        ax.text(xi, max(fa, ra) + 0.003, f'{adv:+.3f}', ha='center', fontsize=7,
                color='green' if adv > 0 else 'red')

    # Panel 2: Pharmacophore AP
    ax2 = axes[1]
    bars = ax2.bar(x, pharm_aps, color=colors, alpha=0.85)
    ax2.set_xticks(x); ax2.set_xticklabels(labels, rotation=15, ha='right', fontsize=8)
    ax2.set_ylabel('Mean Avg. Precision', fontsize=10)
    ax2.set_title('Pharmacophore Precision@K (averaged)', fontsize=10)
    ax2.set_ylim(0, max(pharm_aps) * 1.25 + 0.05)
    for bar, v in zip(bars, pharm_aps):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                 f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    fig.suptitle((title or '') + ' -- Drug Attribution Comparison', fontsize=11, fontweight='bold')
    plt.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved drug comparison: {out_path}')


def plot_protein_comparison(prot_eval, k_fracs, out_path, title=None, dpi=200):
    """Bar chart: AUROC and P@20% for each residue attribution method."""
    methods = [m for m, v in prot_eval.items() if v is not None]
    colors  = [_COLORS.get(m, 'grey') for m in methods]
    labels  = [_LABELS.get(m, m) for m in methods]

    aurocs = [prot_eval[m]['auroc'] if prot_eval[m]['auroc'] is not None else 0.0
              for m in methods]

    # P@20% index
    k20_idx = next((i for i, f in enumerate(k_fracs) if abs(f - 0.20) < 1e-6), 3)
    p20s = [prot_eval[m]['precision'][k20_idx] if prot_eval[m] else 0.0
            for m in methods]

    x = np.arange(len(methods))
    w = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    for ax, vals, ylabel, title_suffix, random_base in [
        (axes[0], aurocs, 'AUROC', 'Binding Site AUROC', 0.5),
        (axes[1], p20s,   'Precision@20%', 'Precision@20%', None),
    ]:
        bars = ax.bar(x, vals, color=colors, alpha=0.85)
        if random_base is not None:
            ax.axhline(random_base, color='grey', linestyle='--', linewidth=1.2,
                       label=f'Random ({random_base:.2f})')
            ax.legend(fontsize=8)
        ax.set_xticks(x); ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=8)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title_suffix, fontsize=10)
        ax.set_ylim(0, max(max(vals) * 1.25, 0.6) + 0.05)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                    f'{v:.3f}', ha='center', va='bottom', fontsize=8)

    fig.suptitle((title or '') + ' -- Protein Attribution Comparison (DHFR)',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved protein comparison: {out_path}')


# ── Print summary table ───────────────────────────────────────────────────────

def print_comparison_summary(drug_eval, prot_eval=None, k_fracs=None, label=''):
    w = 72
    print('\n' + '=' * w)
    print(f'  Phase 6 Attribution Method Comparison  {label}')
    print('=' * w)

    print('\n[Drug Attributions]')
    print(f"{'Method':<16} {'FaithAUC':>9} {'RandAUC':>9} {'Adv':>7} {'PharmAP':>9}")
    print('-' * 52)
    for m, res in drug_eval.items():
        fa  = res['faithfulness']['faithfulness_auc']
        ra  = res['faithfulness']['random_auc']
        adv = res['faithfulness']['faithfulness_advantage']
        ap  = res['pharmacophore']['average_precision']
        flag = '*' if adv > 0 else ' '
        print(f"  {_LABELS.get(m,m):<14} {fa:>+9.4f} {ra:>9.4f} {adv:>+7.4f}{flag} {ap:>9.4f}")

    if prot_eval:
        k20_idx = next((i for i, f in enumerate(k_fracs or []) if abs(f-0.20) < 1e-6), 3)
        print('\n[Protein Attributions vs. DHFR PDB binding site]')
        print(f"{'Method':<16} {'AUROC':>7} {'P@10%':>7} {'P@20%':>7} {'R@20%':>7}")
        print('-' * 44)
        for m, res in prot_eval.items():
            if res is None:
                print(f"  {_LABELS.get(m,m):<14}  N/A")
                continue
            auc = res['auroc'] if res['auroc'] is not None else float('nan')
            p10_idx = next((i for i, f in enumerate(k_fracs or []) if abs(f-0.10) < 1e-6), 1)
            p10 = res['precision'][p10_idx] if len(res['precision']) > p10_idx else 0
            p20 = res['precision'][k20_idx] if len(res['precision']) > k20_idx else 0
            r20 = res['recall'][k20_idx]    if len(res['recall'])    > k20_idx else 0
            print(f"  {_LABELS.get(m,m):<14} {auc:>7.4f} {p10:>7.3f} {p20:>7.3f} {r20:>7.3f}")

    print('=' * w + '\n')


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    from rdkit import Chem
    from torch_geometric.data import Batch

    ap = argparse.ArgumentParser(description='Phase 6: attribution baseline comparison')
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--device',      default='cpu')
    ap.add_argument('--out_dir',     default=None)

    # Drug input: prefer --drug_id (loads preprocessed graph with ChemBERTa);
    # fallback --drug_smiles (adds ChemBERTa on-the-fly via HuggingFace)
    drug_grp = ap.add_mutually_exclusive_group(required=True)
    drug_grp.add_argument('--drug_id',    help='Drug ID in dataset (loads preprocessed graph)')
    drug_grp.add_argument('--drug_smiles', help='Drug SMILES string (adds ChemBERTa on-the-fly)')

    # Protein for drug-side evaluation (any protein embedding will do)
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument('--protein_id', help='Protein ID in dataset')
    grp.add_argument('--prot_emb_npy', help='Pre-computed protein embedding .npy')
    ap.add_argument('--dataset',    default=None)
    ap.add_argument('--emb_tag',    default='esm8m')

    # For protein comparison (optional — requires 3D embeddings + PDB case study)
    ap.add_argument('--pdb_npz',    default=None,
                    help='.npz from Phase 5 (contains binding_0idx + prot_ensemble etc.)')
    ap.add_argument('--protein_sequence', default=None,
                    help='Protein AA sequence for on-the-fly ESM-2 encoding')

    ap.add_argument('--k_fracs', nargs='+', type=float,
                    default=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40])
    ap.add_argument('--n_random', type=int, default=10)
    args = ap.parse_args()

    from interpret.extract_attention import get_drug_graph, get_protein_emb

    device = torch.device(args.device)
    out_dir = args.out_dir or os.path.join(
        _REPO, 'paper', 'figures', 'interpretability', 'baseline_comparison')
    os.makedirs(out_dir, exist_ok=True)

    print(f'Loading model from {args.checkpoint} ...')
    model = load_model(args.checkpoint, device)

    # ── Build drug batch ──────────────────────────────────────────────────────
    # Prefer --drug_id: loads preprocessed graph that includes ChemBERTa embedding,
    # ensuring the same encoder path used during training.
    if args.drug_id:
        if not args.dataset:
            raise ValueError('--dataset required when using --drug_id')
        drug_batch = get_drug_graph(drug_id=args.drug_id, dataset=args.dataset, device=args.device)
        _smi_raw = drug_batch.smiles if hasattr(drug_batch, 'smiles') else None
        smiles = (_smi_raw[0] if isinstance(_smi_raw, (list, tuple)) else _smi_raw)
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        if mol is None:
            raise ValueError(f'Could not get SMILES for drug_id={args.drug_id}')
    else:
        # Fallback: build from SMILES and attach ChemBERTa on-the-fly
        drug_data = _smiles_to_graph(args.drug_smiles)
        # Attach ChemBERTa embedding so the correct encoder path is used
        try:
            from transformers import AutoTokenizer, AutoModel
            _cb_name = 'seyonec/ChemBERTa-zinc-base-v1'
            print(f'  Loading ChemBERTa for SMILES-mode ({_cb_name}) ...')
            _cb_tok = AutoTokenizer.from_pretrained(_cb_name)
            _cb_mod = AutoModel.from_pretrained(_cb_name).eval()
            with torch.no_grad():
                toks = _cb_tok(args.drug_smiles, return_tensors='pt', truncation=True, max_length=512)
                cb_emb = _cb_mod(**toks).last_hidden_state[:, 0, :]  # (1, 768) CLS
            drug_data.chemberta = cb_emb
        except Exception as e:
            print(f'  WARNING: ChemBERTa on-the-fly failed ({e}); using no-ChemBERTa fallback.')
        drug_batch = Batch.from_data_list([drug_data]).to(device)
        mol = Chem.MolFromSmiles(args.drug_smiles)

    N = drug_batch.x.shape[0]
    print(f'  Drug: {N} atoms  (ChemBERTa attached: {hasattr(drug_batch, "chemberta") and drug_batch.chemberta is not None})')

    # ── Protein embedding for drug-side eval ──────────────────────────────────
    if args.prot_emb_npy:
        prot_emb = torch.tensor(np.load(args.prot_emb_npy), dtype=torch.float32
                                ).unsqueeze(0).to(device)
    else:
        prot_emb = get_protein_emb(protein_id=args.protein_id, dataset=args.dataset,
                                    emb_tag=args.emb_tag, device=args.device)

    # ── Compute drug attributions ──────────────────────────────────────────────
    print('\n[1] Computing drug attributions ...')
    drug_attrs = compute_drug_attributions(model, drug_batch, prot_emb, model.task)

    # ── Evaluate drug methods ──────────────────────────────────────────────────
    print('\n[2] Evaluating drug attribution methods (faithfulness + pharmacophore) ...')
    drug_eval = evaluate_drug_methods(
        model, drug_batch, prot_emb, mol, model.task,
        drug_attrs, k_fracs=args.k_fracs, n_random=args.n_random)

    # ── Protein comparison (optional) ──────────────────────────────────────────
    prot_eval = None
    if args.pdb_npz and args.protein_sequence:
        print('\n[3] Computing protein attributions (on-the-fly ESM-2) ...')
        from interpret.evaluate_case_studies import encode_sequence_esm2

        esm_dim = (model.prot_input_proj.weight.shape[1]
                   if hasattr(model, 'prot_input_proj') and model.prot_input_proj is not None
                   else 320)
        prot_3d = encode_sequence_esm2(args.protein_sequence, esm_dim, device=args.device)
        prot_attrs = compute_protein_attributions(model, drug_batch, prot_3d, model.task)

        # Load binding site from npz
        npz = np.load(args.pdb_npz, allow_pickle=True)
        binding_0idx = npz['binding_0idx'].tolist()
        n_res = prot_3d.shape[1]
        print(f'  Binding residues from PDB npz: {len(binding_0idx)} / {n_res}')

        prot_eval = evaluate_protein_methods(prot_attrs, binding_0idx, n_res, args.k_fracs)

    elif args.pdb_npz:
        # Load pre-computed protein attributions from Phase 5 npz
        print('\n[3] Loading protein attributions from Phase 5 npz ...')
        npz = np.load(args.pdb_npz, allow_pickle=True)
        binding_0idx = npz['binding_0idx'].tolist()
        n_res = len(npz['prot_ensemble'])

        prot_attrs = {
            'random':      np.random.RandomState(42).rand(n_res),
            'attn_pool':   (npz['attn_weights']  if len(npz.get('attn_weights', [-1])) > 1 else None),
            'protein_cam': (npz['protein_cam']   if len(npz.get('protein_cam',  [-1])) > 1 else None),
            'ensemble':    npz['prot_ensemble'],
        }
        prot_attrs['random'] = prot_attrs['random'] / prot_attrs['random'].max()

        prot_eval = evaluate_protein_methods(prot_attrs, binding_0idx, n_res, args.k_fracs)
    else:
        print('\n[3] Skipping protein comparison (no --pdb_npz provided).')

    # ── Spearman stability ─────────────────────────────────────────────────────
    print('\n[4] Pairwise Spearman rho (drug attribution stability) ...')
    drug_rho = pairwise_spearman(drug_attrs)
    print('  Drug method correlations:')
    for (m1, m2), rho in sorted(drug_rho.items()):
        if m1 != m2:
            print(f'    {_LABELS.get(m1,m1):<18} vs {_LABELS.get(m2,m2):<18}: rho={rho:.4f}')

    # ── Plots ──────────────────────────────────────────────────────────────────
    pair_label = f'{args.protein_id or "prot"}'
    plot_drug_comparison(
        drug_eval, args.k_fracs,
        out_path=os.path.join(out_dir, f'drug_comparison_{pair_label}.png'),
        title=f'Drug: {(args.drug_id or args.drug_smiles[:30]+"...")}',
    )
    if prot_eval:
        plot_protein_comparison(
            prot_eval, args.k_fracs,
            out_path=os.path.join(out_dir, f'protein_comparison_{pair_label}.png'),
            title=f'Protein: {pair_label}',
        )

    # ── Print summary ──────────────────────────────────────────────────────────
    print_comparison_summary(drug_eval, prot_eval, args.k_fracs, label=f'({pair_label})')

    # ── Save JSON ──────────────────────────────────────────────────────────────
    out = {
        'checkpoint':  args.checkpoint,
        'drug_smiles': args.drug_smiles,
        'protein_id':  args.protein_id,
        'drug_methods': {},
        'protein_methods': {},
        'spearman_rho': {f'{m1}_vs_{m2}': rho for (m1, m2), rho in drug_rho.items()},
    }
    for m, res in drug_eval.items():
        out['drug_methods'][m] = {
            'faithfulness_auc':     res['faithfulness']['faithfulness_auc'],
            'faithfulness_advantage': res['faithfulness']['faithfulness_advantage'],
            'pharmacophore_ap':     res['pharmacophore']['average_precision'],
        }
    if prot_eval:
        k20 = next((i for i, f in enumerate(args.k_fracs) if abs(f-0.20) < 1e-6), 3)
        for m, res in prot_eval.items():
            if res is None:
                continue
            out['protein_methods'][m] = {
                'auroc':        res['auroc'],
                'precision_20': res['precision'][k20] if len(res['precision']) > k20 else None,
                'recall_20':    res['recall'][k20]    if len(res['recall'])    > k20 else None,
            }

    json_path = os.path.join(out_dir, f'comparison_{pair_label}.json')
    with open(json_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\n  Saved comparison JSON: {json_path}')
    print(f'  Figures: {out_dir}')


if __name__ == '__main__':
    main()
