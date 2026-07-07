"""
Phase 4 -- Quantitative Interpretability Metrics

Three metrics for evaluating explanation quality:

1. Faithfulness (atom masking AUC)
   Zero top-k atoms by attribution; compare prediction drop to random masking.
   A faithful explanation causes a larger drop than random.

2. Cross-seed Consistency (Spearman rho)
   Run Phase 1+2 across N seeds; Spearman rank correlation of atom attribution
   rankings between every seed pair.  High rho = stable, trustworthy explanations.

3. Pharmacophore Precision@K
   What fraction of the model's top-k atoms match pharmacophore SMARTS patterns?
   Compared to the random baseline (pharm_count / N_atoms).

Usage:
    python -m interpret.metrics \
        --checkpoint checkpoints/hgnn_rnn_dti_phase3_ft_esm150m_1to5_luo_17_dti_cold_target_fold0_seed1_best.pt \
        --dataset luo_17 --emb_tag esm150m \
        --pairs DB00150,P19838 \
        --ckpt_dir checkpoints --seeds 1 2 3 4 5 \
        --device cpu

    # Load pre-computed attributions from Phase 3 output:
    python -m interpret.metrics --npz paper/figures/interpretability/DB00150_P19838/attribution.npz \
        --smiles "..." --checkpoint ... --dataset luo_17
"""

import os
import sys
import json
import itertools
import numpy as np
import torch

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from scipy.integrate import trapezoid as _trapz


# ── Helper: run a forward pass and get a scalar score ─────────────────────────

def _get_pred_score(model, drug_batch, protein_emb, task):
    """Return scalar prediction score (P(interaction) for DTI, affinity for DTA)."""
    model.eval()
    with torch.no_grad():
        prot = protein_emb.clone()
        # Project from ESM dim → hidden dim if the model has a projection layer
        if (hasattr(model, 'prot_input_proj') and model.prot_input_proj is not None
                and prot.shape[-1] == model.prot_input_proj.weight.shape[1]):
            prot = model.prot_input_proj(prot)
        logits = model(drug_batch, prot)
    if task == 'dti':
        return torch.softmax(logits, dim=-1)[0, 1].item()
    else:
        return logits[0, 0].item()


def _mask_atoms(drug_batch, atom_idx):
    """Return a clone of drug_batch with features at atom_idx zeroed."""
    new_batch = drug_batch.clone()
    new_batch.x = drug_batch.x.clone()
    new_batch.x[atom_idx] = 0.0
    return new_batch


# ── Metric 1: Faithfulness ────────────────────────────────────────────────────

def compute_faithfulness(
    model,
    drug_batch,
    protein_emb,
    task,
    atom_scores,
    k_fracs=None,
    n_random=10,
    seed=42,
):
    """
    Atom masking faithfulness.

    Masks the top-k atoms (by attribution) and measures prediction drop vs.
    masking random k atoms.  A faithful explanation causes a larger drop.

    Returns
    -------
    dict with keys:
        orig_score, k_fracs, k_values,
        attribution_drops, random_drops,
        faithfulness_auc, random_auc,
        faithfulness_advantage  (>0 means attribution is better than random)
    """
    if k_fracs is None:
        k_fracs = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

    rng = np.random.RandomState(seed)
    N = drug_batch.x.shape[0]
    scores = np.asarray(atom_scores)
    ranked_idx = np.argsort(scores)[::-1].copy()   # copy: PyTorch rejects negative-stride arrays

    orig_score = _get_pred_score(model, drug_batch, protein_emb, task)

    k_values, attr_drops, rand_drops = [], [], []

    for frac in k_fracs:
        k = max(1, int(round(frac * N)))
        k_values.append(k)

        # Attribution-guided masking
        top_k = ranked_idx[:k]
        masked = _mask_atoms(drug_batch, top_k)
        masked_score = _get_pred_score(model, masked, protein_emb, task)
        attr_drops.append(float(orig_score - masked_score))

        # Random masking baseline (average over n_random draws)
        rd_list = []
        for _ in range(n_random):
            rand_idx = rng.choice(N, size=k, replace=False)
            rb = _mask_atoms(drug_batch, rand_idx)
            rd_list.append(float(orig_score - _get_pred_score(model, rb, protein_emb, task)))
        rand_drops.append(float(np.mean(rd_list)))

    # AUC via trapezoidal rule over fraction axis
    k_norm = [k / N for k in k_values]
    faith_auc = float(_trapz(attr_drops, k_norm))
    rand_auc  = float(_trapz(rand_drops,  k_norm))

    return {
        'orig_score':             orig_score,
        'k_fracs':                k_fracs,
        'k_values':               k_values,
        'attribution_drops':      [float(x) for x in attr_drops],
        'random_drops':           [float(x) for x in rand_drops],
        'faithfulness_auc':       faith_auc,
        'random_auc':             rand_auc,
        'faithfulness_advantage': float(faith_auc - rand_auc),
    }


# ── Metric 2: Cross-seed Consistency ─────────────────────────────────────────

def compute_cross_seed_consistency(
    ckpt_paths,
    drug_batch,
    protein_emb,
    task,
    device='cpu',
):
    """
    Load each checkpoint, extract ensemble atom attribution, compute Spearman rho.

    ckpt_paths : list of str (one checkpoint per seed)
    Returns
    -------
    dict with keys:
        n_seeds, n_pairs, per_pair_rho, mean_rho, std_rho, median_rho
    """
    from interpret.extract_attention import load_model, compute_atom_saliency
    from interpret.grad_cam import compute_all_grad_cam, ensemble_attribution

    all_scores = []
    valid_paths = []
    for path in ckpt_paths:
        if not os.path.exists(path):
            print(f"  [consistency] Checkpoint not found, skipping: {path}")
            continue
        try:
            m = load_model(path, torch.device(device))
            atom_imp, _ = compute_atom_saliency(m, drug_batch, protein_emb, task)
            atom_imp = atom_imp.numpy()
            cam_res  = compute_all_grad_cam(m, drug_batch, protein_emb, task)
            drug_cam = cam_res['drug_cam'].numpy()
            ens = ensemble_attribution(atom_imp, drug_cam, alpha=0.5)
            all_scores.append(ens)
            valid_paths.append(path)
            del m
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
        except Exception as e:
            print(f"  [consistency] Error loading {path}: {e}")

    if len(all_scores) < 2:
        return {
            'error': f'Need >= 2 valid seeds; got {len(all_scores)}',
            'n_seeds': len(all_scores),
        }

    pairs = list(itertools.combinations(range(len(all_scores)), 2))
    rhos  = []
    for i, j in pairs:
        rho, _ = spearmanr(all_scores[i], all_scores[j])
        rhos.append(float(rho))

    return {
        'n_seeds':      len(all_scores),
        'n_pairs':      len(pairs),
        'per_pair_rho': rhos,
        'mean_rho':     float(np.mean(rhos)),
        'std_rho':      float(np.std(rhos)),
        'median_rho':   float(np.median(rhos)),
        'valid_ckpts':  valid_paths,
    }


# ── Metric 3: Pharmacophore Precision@K ──────────────────────────────────────

_PHARM_SMARTS_STR = {
    'HBD':   '[#7H,#8H]',
    'HBA':   '[#7,#8,#9]',
    'Arom':  '[a]',
    'Hydro': '[c,s,C,S;!$([#7,#8,#9])]',
}


def compute_pharmacophore_precision(mol, atom_scores, k_fracs=None):
    """
    Pharmacophore precision@K: fraction of top-k atoms matching pharmacophore SMARTS.

    Random baseline is the proportion of pharmacophore atoms in the full molecule.

    Returns
    -------
    dict with keys:
        k_fracs, k_values, n_atoms,
        pharm_atom_counts, pharm_atom_indices,
        precision_by_class (dict class->list[float]),
        mean_precision_at_k (list[float]),
        average_precision (float, mean over k fracs),
        random_baseline (dict class->float)
    """
    if k_fracs is None:
        k_fracs = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50]

    from rdkit import Chem

    N = mol.GetNumAtoms()
    scores = np.asarray(atom_scores)
    ranked_idx = np.argsort(scores)[::-1].copy()

    # Build pharmacophore atom sets
    pharm_atoms = {}
    for name, smarts in _PHARM_SMARTS_STR.items():
        patt = Chem.MolFromSmarts(smarts)
        if patt is None:
            pharm_atoms[name] = set()
        else:
            matches = mol.GetSubstructMatches(patt)
            pharm_atoms[name] = set(int(idx) for m in matches for idx in m)

    k_values, prec_by_class = [], {name: [] for name in _PHARM_SMARTS_STR}

    for frac in k_fracs:
        k = max(1, int(round(frac * N)))
        k_values.append(k)
        top_k_set = set(ranked_idx[:k].tolist())

        for name, pharm_set in pharm_atoms.items():
            if len(pharm_set) == 0:
                prec_by_class[name].append(0.0)
            else:
                prec_by_class[name].append(float(len(top_k_set & pharm_set) / k))

    # Mean precision across non-empty classes
    nonempty = [name for name in _PHARM_SMARTS_STR if len(pharm_atoms[name]) > 0]
    mean_at_k = []
    for ki in range(len(k_fracs)):
        vals = [prec_by_class[n][ki] for n in nonempty]
        mean_at_k.append(float(np.mean(vals)) if vals else 0.0)

    random_baseline = {
        name: float(len(pharm_atoms[name]) / N) if N > 0 else 0.0
        for name in _PHARM_SMARTS_STR
    }

    return {
        'k_fracs':             k_fracs,
        'k_values':            k_values,
        'n_atoms':             N,
        'pharm_atom_counts':   {k: len(v) for k, v in pharm_atoms.items()},
        'pharm_atom_indices':  {k: sorted(v) for k, v in pharm_atoms.items()},
        'precision_by_class':  prec_by_class,
        'mean_precision_at_k': mean_at_k,
        'average_precision':   float(np.mean(mean_at_k)),
        'random_baseline':     random_baseline,
    }


# ── Plotting helpers ───────────────────────────────────────────────────────────

def plot_faithfulness(result, out_path, title=None, dpi=200):
    """Faithfulness curve: attribution vs random drop at each k%."""
    k_pct = [int(round(f * 100)) for f in result['k_fracs']]
    fig, ax = plt.subplots(figsize=(7, 4))

    ax.plot(k_pct, result['attribution_drops'], 'o-', color='#d62728',
            linewidth=2, label='Attribution-guided masking')
    ax.plot(k_pct, result['random_drops'],      's--', color='#1f77b4',
            linewidth=1.5, alpha=0.7, label='Random masking (baseline)')
    ax.axhline(0, color='grey', linewidth=0.8, linestyle=':')

    ax.set_xlabel('Atoms masked (%)', fontsize=11)
    ax.set_ylabel('Prediction score drop', fontsize=11)
    ax.legend(fontsize=9)

    adv = result['faithfulness_advantage']
    auc_str = f"Faith. AUC={result['faithfulness_auc']:.3f}  "
    auc_str += f"Rand AUC={result['random_auc']:.3f}  "
    auc_str += f"Adv={adv:+.3f}"
    ax.set_title((title + '\n' if title else '') + auc_str, fontsize=10)

    ax.tick_params(labelsize=9)
    plt.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved faithfulness plot: {out_path}")


def plot_pharmacophore_precision(result, out_path, title=None, dpi=200):
    """Precision@K grouped bar chart, one bar per pharmacophore class."""
    k_pct   = [f'{int(round(f*100))}%' for f in result['k_fracs']]
    classes = [c for c in _PHARM_SMARTS_STR if result['pharm_atom_counts'][c] > 0]
    if not classes:
        print("  [pharmacophore] No matching atoms — plot skipped.")
        return

    x = np.arange(len(k_pct))
    width = 0.8 / max(len(classes), 1)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    fig, ax = plt.subplots(figsize=(8, 4))
    for ci, cls in enumerate(classes):
        offset = (ci - len(classes) / 2 + 0.5) * width
        bars = ax.bar(x + offset, result['precision_by_class'][cls], width,
                      label=cls, color=colors[ci % len(colors)], alpha=0.85)
        # Random baseline dashed line
        rb = result['random_baseline'][cls]
        ax.axhline(rb, color=colors[ci % len(colors)], linestyle='--',
                   linewidth=0.9, alpha=0.6)

    ax.set_xticks(x)
    ax.set_xticklabels(k_pct, fontsize=9)
    ax.set_xlabel('Top-k atoms selected (%)', fontsize=11)
    ax.set_ylabel('Precision', fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.legend(title='Pharmacophore', fontsize=8, title_fontsize=9)
    avg_p = result['average_precision']
    ax.set_title((title + '\n' if title else '') + f'Mean Avg. Precision={avg_p:.3f}  (dashed=random baseline)',
                 fontsize=10)
    ax.tick_params(labelsize=9)
    plt.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved pharmacophore precision plot: {out_path}")


def plot_consistency(result, out_path, title=None, dpi=200):
    """Boxplot + individual points for per-pair Spearman rho."""
    if 'error' in result:
        print(f"  [consistency] {result['error']} — plot skipped.")
        return

    rhos = result['per_pair_rho']
    fig, ax = plt.subplots(figsize=(5, 4))

    bp = ax.boxplot(rhos, patch_artist=True, widths=0.4,
                    boxprops=dict(facecolor='#aec7e8', color='#1f77b4'),
                    medianprops=dict(color='#d62728', linewidth=2))
    # Jitter individual points
    jitter = np.random.default_rng(0).uniform(-0.15, 0.15, len(rhos))
    ax.scatter(1 + jitter, rhos, color='#1f77b4', s=30, zorder=5, alpha=0.8)
    ax.axhline(0.7, color='green', linestyle='--', linewidth=1.2,
               label='Target: rho=0.7')

    ax.set_xticks([1])
    ax.set_xticklabels(['Seed pairs'], fontsize=10)
    ax.set_ylabel('Spearman rho', fontsize=11)
    ax.set_ylim(-0.1, 1.05)
    ax.legend(fontsize=9)

    mean_rho = result['mean_rho']
    std_rho  = result['std_rho']
    ax.set_title((title + '\n' if title else '') +
                 f'Mean rho={mean_rho:.3f} +/- {std_rho:.3f}  (n={result["n_seeds"]} seeds)',
                 fontsize=10)
    plt.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved consistency plot: {out_path}")


# ── Print summary ─────────────────────────────────────────────────────────────

def print_metrics_summary(faith_res, pharm_res, cons_res=None, label=''):
    w = 58
    print('\n' + '=' * w)
    print(f'  Phase 4 Interpretability Metrics  {label}')
    print('=' * w)

    print('\n[1] Faithfulness (atom masking)')
    print(f"    Orig. pred score : {faith_res['orig_score']:.4f}")
    print(f"    Faithfulness AUC : {faith_res['faithfulness_auc']:+.4f}")
    print(f"    Random AUC       : {faith_res['random_auc']:+.4f}")
    adv = faith_res['faithfulness_advantage']
    flag = 'PASS' if adv > 0 else 'FAIL'
    print(f"    Advantage        : {adv:+.4f}  [{flag}]")
    print(f"    (k%, attr_drop, rand_drop):")
    for k, frac, ad, rd in zip(
            faith_res['k_values'], faith_res['k_fracs'],
            faith_res['attribution_drops'], faith_res['random_drops']):
        print(f"      k={k:2d} ({int(frac*100):3d}%):  attr={ad:+.4f}  rand={rd:+.4f}")

    print('\n[2] Pharmacophore Precision@K')
    print(f"    N atoms : {pharm_res['n_atoms']}")
    for name, cnt in pharm_res['pharm_atom_counts'].items():
        rb = pharm_res['random_baseline'][name]
        print(f"    {name:<6} atoms={cnt:2d}  random_baseline={rb:.3f}")
    print(f"    Avg. Precision (mean over k fracs): {pharm_res['average_precision']:.4f}")
    print(f"    Mean P@k by k:")
    for frac, mp in zip(pharm_res['k_fracs'], pharm_res['mean_precision_at_k']):
        print(f"      k={int(frac*100):3d}%:  {mp:.4f}")

    if cons_res is not None:
        print('\n[3] Cross-seed Consistency (Spearman rho)')
        if 'error' in cons_res:
            print(f"    {cons_res['error']}")
        else:
            flag = 'PASS' if cons_res['mean_rho'] >= 0.7 else 'FAIL'
            print(f"    N seeds : {cons_res['n_seeds']}")
            print(f"    Mean rho: {cons_res['mean_rho']:.4f} +/- {cons_res['std_rho']:.4f}  [{flag}]")
            print(f"    Median  : {cons_res['median_rho']:.4f}")
            for i, r in enumerate(cons_res['per_pair_rho']):
                print(f"    pair {i+1}: rho={r:.4f}")

    print('=' * w + '\n')


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(description='Phase 4: quantitative interpretability metrics')
    ap.add_argument('--checkpoint', required=True,
                    help='Path to best checkpoint (e.g. C3 seed1)')
    ap.add_argument('--dataset',    default=None)
    ap.add_argument('--emb_tag',    default='esm150m')
    ap.add_argument('--device',     default='cpu')

    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument('--pairs',    nargs='+', metavar='DRUG_ID,PROT_ID')
    grp.add_argument('--npz',      help='Pre-computed attribution .npz from Phase 3')

    ap.add_argument('--smiles',    default=None,
                    help='Drug SMILES (required if --npz given without drug lookup)')
    ap.add_argument('--drug_id',   default=None)
    ap.add_argument('--protein_id', default=None)

    # Cross-seed consistency
    ap.add_argument('--ckpt_dir',  default=None,
                    help='Directory containing per-seed checkpoints')
    ap.add_argument('--seeds',     nargs='+', type=int, default=[1, 2, 3, 4, 5])
    ap.add_argument('--ckpt_pattern', default=None,
                    help='Glob pattern for seed checkpoints, e.g. '
                         '"hgnn_rnn_dti_phase3_ft_esm150m_1to5_luo_17_dti_cold_target_fold0_seed{seed}_best.pt"')

    ap.add_argument('--out_dir',   default=None,
                    help='Output directory (default: paper/figures/interpretability/{pair})')
    ap.add_argument('--k_fracs',   nargs='+', type=float,
                    default=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50])
    ap.add_argument('--n_random',  type=int, default=10)
    args = ap.parse_args()

    from interpret.extract_attention import (load_model, get_drug_graph,
                                              get_protein_emb, compute_atom_saliency)
    from interpret.grad_cam import compute_all_grad_cam, ensemble_attribution
    from rdkit import Chem

    device = torch.device(args.device)

    print(f'Loading model from {args.checkpoint} ...')
    model = load_model(args.checkpoint, device)

    if args.npz:
        # Load pre-computed attributions
        data = np.load(args.npz, allow_pickle=True)
        drug_ens = data['drug_ensemble']
        drug_id  = str(data.get('drug_id', args.drug_id or 'drug'))
        prot_id  = str(data.get('protein_id', args.protein_id or 'prot'))
        pair_label = f'{drug_id}_{prot_id}'

        smiles_src = args.smiles
        if args.drug_id is not None:
            drug_batch = get_drug_graph(smiles=smiles_src, drug_id=args.drug_id,
                                         dataset=args.dataset, device=args.device)
        elif smiles_src is not None:
            drug_batch = get_drug_graph(smiles=smiles_src, device=args.device)
        else:
            raise ValueError('Provide --smiles or --drug_id when using --npz')

        # Verify atom count consistency between .npz and reconstructed graph
        n_graph = drug_batch.x.shape[0]
        n_npz   = len(drug_ens)
        if n_graph != n_npz:
            raise ValueError(
                f'Atom count mismatch: attribution .npz has {n_npz} atoms but '
                f'the drug graph has {n_graph}. Check that --smiles / --drug_id '
                f'matches the molecule used to compute the attribution.'
            )

        prot_emb = get_protein_emb(protein_id=args.protein_id, dataset=args.dataset,
                                    emb_tag=args.emb_tag, device=args.device)

        # Build RDKit mol for pharmacophore metric
        mol = None
        if smiles_src:
            mol = Chem.MolFromSmiles(smiles_src)
        if mol is None and hasattr(drug_batch, 'smiles'):
            s = drug_batch.smiles
            mol = Chem.MolFromSmiles(s[0] if isinstance(s, (list, tuple)) else str(s))

        all_pairs = [(drug_id, prot_id, drug_batch, prot_emb, mol, drug_ens)]

    else:
        # Parse pairs and compute attributions
        all_pairs = []
        for pair_str in args.pairs:
            parts = pair_str.split(',')
            drug_id = parts[0].strip()
            prot_id = parts[1].strip()
            smiles_src = parts[2].strip() if len(parts) > 2 else args.smiles

            drug_batch = get_drug_graph(smiles=smiles_src, drug_id=drug_id,
                                         dataset=args.dataset, device=args.device)
            prot_emb = get_protein_emb(protein_id=prot_id, dataset=args.dataset,
                                        emb_tag=args.emb_tag, device=args.device)

            # Compute ensemble attribution
            atom_imp, _ = compute_atom_saliency(model, drug_batch, prot_emb, model.task)
            atom_imp = atom_imp.numpy()
            cam_res  = compute_all_grad_cam(model, drug_batch, prot_emb, model.task)
            drug_cam = cam_res['drug_cam'].numpy()
            drug_ens = ensemble_attribution(atom_imp, drug_cam, alpha=0.5)

            mol = None
            if smiles_src:
                mol = Chem.MolFromSmiles(smiles_src)
            elif hasattr(drug_batch, 'smiles'):
                s = drug_batch.smiles
                mol = Chem.MolFromSmiles(s[0] if isinstance(s, (list, tuple)) else str(s))

            all_pairs.append((drug_id, prot_id, drug_batch, prot_emb, mol, drug_ens))

    for drug_id, prot_id, drug_batch, prot_emb, mol, drug_ens in all_pairs:
        pair_label = f'{drug_id}_{prot_id}'
        out_dir = args.out_dir or os.path.join(
            _REPO, 'paper', 'figures', 'interpretability', pair_label)
        os.makedirs(out_dir, exist_ok=True)

        print(f'\n{"="*60}\n  Pair: {pair_label}\n{"="*60}')

        # ── Faithfulness ─────────────────────────────────────────────────────
        print('\n[1] Computing faithfulness ...')
        faith_res = compute_faithfulness(
            model, drug_batch, prot_emb, model.task,
            atom_scores=drug_ens,
            k_fracs=args.k_fracs,
            n_random=args.n_random,
        )
        plot_faithfulness(
            faith_res,
            out_path=os.path.join(out_dir, 'metrics_faithfulness.png'),
            title=pair_label,
        )

        # ── Pharmacophore Precision ───────────────────────────────────────────
        print('\n[2] Computing pharmacophore precision ...')
        if mol is not None:
            pharm_res = compute_pharmacophore_precision(mol, drug_ens, k_fracs=args.k_fracs)
            plot_pharmacophore_precision(
                pharm_res,
                out_path=os.path.join(out_dir, 'metrics_pharmacophore.png'),
                title=pair_label,
            )
        else:
            print('  No RDKit mol available — pharmacophore metric skipped.')
            pharm_res = None

        # ── Cross-seed Consistency ────────────────────────────────────────────
        cons_res = None
        if args.ckpt_dir and args.ckpt_pattern:
            print('\n[3] Computing cross-seed consistency ...')
            ckpt_paths = []
            for s in args.seeds:
                fname = args.ckpt_pattern.replace('{seed}', str(s))
                ckpt_paths.append(os.path.join(args.ckpt_dir, fname))
            cons_res = compute_cross_seed_consistency(
                ckpt_paths, drug_batch, prot_emb, model.task, device=args.device)
            plot_consistency(
                cons_res,
                out_path=os.path.join(out_dir, 'metrics_consistency.png'),
                title=pair_label,
            )
        elif args.ckpt_dir:
            print('  --ckpt_pattern not provided — consistency metric skipped.')

        # ── Print summary ─────────────────────────────────────────────────────
        if pharm_res is not None:
            print_metrics_summary(faith_res, pharm_res, cons_res, label=f'({pair_label})')

        # ── Save JSON ─────────────────────────────────────────────────────────
        result_dict = {'pair': pair_label, 'task': model.task,
                       'faithfulness': faith_res}
        if pharm_res is not None:
            result_dict['pharmacophore'] = pharm_res
        if cons_res is not None:
            result_dict['consistency'] = cons_res

        json_path = os.path.join(out_dir, 'metrics.json')
        with open(json_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        print(f'\n  Saved metrics JSON: {json_path}')

    print(f'\nDone. Metrics saved to {args.out_dir or "paper/figures/interpretability/"}')


if __name__ == '__main__':
    main()
