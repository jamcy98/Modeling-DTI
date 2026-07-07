"""
Phase 5 -- Case Study Validation

For selected drug-target pairs with known PDB co-crystal structures:
1. Download the PDB file from RCSB via HTTP
2. Parse ATOM/HETATM records; extract protein residues within 4A of the ligand
3. Encode the protein sequence on-the-fly with ESM-2 to get (1, L, D) residue embeddings
4. Run the model to get per-residue AttentionPooling weights + Grad-CAM
5. Evaluate attribution against PDB binding residues:
   Residue-level AUROC, Precision@K, Recall@K, Enrichment Factor
6. Generate annotated residue heatmap and save report

Usage:
    python -m interpret.evaluate_case_studies \
        --checkpoint checkpoints/hgnn_rnn_dti_yamanishi_e_dti_random_fold0_seed1_best.pt \
        --device cpu

    # or run one specific case study:
    python -m interpret.evaluate_case_studies \
        --checkpoint ... \
        --case dhfr_mtx \
        --out_dir paper/figures/interpretability/case_studies

Default case studies (yamanishi_e positive interactions with PDB validation):
    dhfr_mtx   : Methotrexate (D00142) vs DHFR (P00374) -- PDB 1U72 / MTX
    ada_ado    : Adenosine   (D00155) vs ADA  (P00813) -- PDB 3IAR / ADN
"""

import os
import sys
import json
import math
import struct
import urllib.request
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
from sklearn.metrics import roc_auc_score

from interpret.extract_attention import load_model, _smiles_to_graph
from interpret.grad_cam import compute_all_grad_cam, ensemble_attribution
from interpret.visualize_protein import visualize_protein_attribution


# ── Curated case study registry ───────────────────────────────────────────────

CASE_STUDIES = {
    'dhfr_mtx': {
        'name':       'Methotrexate vs DHFR',
        'drug_id':    'D00142',
        'protein_id': 'P00374',
        'dataset':    'yamanishi_e',
        'smiles':     'CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)N[C@@H](CCC(=O)O)C(=O)O',
        'sequence':   'MVGSLNCIVAVSQNMGIGKNGDLPWPPLRNEFRYFQRMTTTSSVEGKQNLVIMGKKTWFSIPEKNRPL'
                      'KGRINLVLSRELKEPPQGAHFLSRSLDDALKLTEQPELANKVDMVWIVGGSSVYKEAMNHPGHLKLF'
                      'VTRIMQDFESDTFFPEIDLEKYKLLPEYPGVLSDVQEEKGIKYKFEVYEKND',
        'pdb_id':     '1U72',
        'pdb_chain':  'A',
        'pdb_ligand': 'MTX',
        'cutoff_A':   4.5,
        # Canonical DHFR methotrexate binding residues (1-indexed PDB; from literature)
        # Asp21, Leu22, Glu30, Phe31, Ile60, Pro61, Leu67, Ile94, Thr136
        'lit_binding_1idx': [21, 22, 30, 31, 60, 61, 67, 94, 136],
        'note':       'Classic antifolate inhibitor; indole+glutamate moiety fills folate pocket',
    },
    'ada_ado': {
        'name':       'Adenosine vs ADA',
        'drug_id':    'D00155',
        'protein_id': 'P00813',
        'dataset':    'yamanishi_e',
        'smiles':     'C1[C@@H]([C@H](O[C@H]1N2C=NC3=C2NC=NC[C@H]3O)CO)O',
        'sequence':   None,  # loaded from dataset
        'pdb_id':     '3IAR',
        'pdb_chain':  'A',
        'pdb_ligand': '3D1',   # 3D1 = (3R)-3-amino-3,4-dihydro-7H-pyrrolo[2,3-d]pyrimidine; ADA inhibitor in 3IAR
        'cutoff_A':   4.5,
        # ADA active site residues (1-indexed, human ADA2 P00813 numbering)
        # His17, Leu58, Ile59, Glu182, Gly184, His214, Ala183, His256, Asp295, Cys262
        'lit_binding_1idx': [17, 58, 59, 182, 183, 184, 214, 256, 262, 295],
        'note':       'ADA hydrolyzes adenosine; Zn-coordinated active site',
    },
}

# ESM-2 model tags keyed by embedding dimension
_ESM2_TAGS = {
    320:  'facebook/esm2_t6_8M_UR50D',
    480:  'facebook/esm2_t12_35M_UR50D',
    640:  'facebook/esm2_t30_150M_UR50D',
    1280: 'facebook/esm2_t33_650M_UR50D',
}


# ── 1. PDB download ───────────────────────────────────────────────────────────

def download_pdb(pdb_id, out_dir):
    """Download PDB file from RCSB if not already cached."""
    os.makedirs(out_dir, exist_ok=True)
    pdb_file = os.path.join(out_dir, f'{pdb_id.upper()}.pdb')
    if os.path.exists(pdb_file):
        print(f'  PDB cached: {pdb_file}')
        return pdb_file
    url = f'https://files.rcsb.org/download/{pdb_id.upper()}.pdb'
    print(f'  Downloading {url} ...')
    try:
        urllib.request.urlretrieve(url, pdb_file)
        print(f'  Saved: {pdb_file}')
    except Exception as e:
        raise RuntimeError(f'Failed to download PDB {pdb_id}: {e}')
    return pdb_file


# ── 2. Minimal PDB parser + binding residue extraction ────────────────────────

def _parse_pdb_atoms(pdb_path, chain):
    """Parse ATOM records for a chain and HETATM records (all chains)."""
    protein_residues = {}  # (resnum, resname) -> list of (x, y, z)
    hetatm_atoms = {}      # resname -> list of (x, y, z)

    with open(pdb_path, 'r', errors='replace') as f:
        for line in f:
            rec = line[:6].strip()
            if rec == 'ATOM' and line[21] == chain:
                try:
                    resnum  = int(line[22:26])
                    resname = line[17:20].strip()
                    x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
                    key = (resnum, resname)
                    protein_residues.setdefault(key, []).append((x, y, z))
                except (ValueError, IndexError):
                    pass

            elif rec == 'HETATM':
                try:
                    resname = line[17:20].strip()
                    x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
                    hetatm_atoms.setdefault(resname, []).append((x, y, z))
                except (ValueError, IndexError):
                    pass

    return protein_residues, hetatm_atoms


def _dist(a, b):
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def extract_binding_residues(pdb_path, chain, ligand_resname, cutoff_A=4.5):
    """
    Return dict:
        binding_residues_1idx: list of 1-indexed residue numbers within cutoff_A of ligand
        all_residue_nums:      sorted list of all protein residue numbers in chain
        min_distances:         {resnum: min_dist_to_ligand}
        available_ligands:     set of HETATM residue names (for debugging)
    """
    prot_res, hetatm = _parse_pdb_atoms(pdb_path, chain)
    available = set(hetatm.keys())

    ligand_atoms = hetatm.get(ligand_resname)
    if ligand_atoms is None:
        alts = [k for k in available if 'HOH' not in k and 'WAT' not in k]
        raise ValueError(
            f"Ligand '{ligand_resname}' not found in HETATM of chain {chain}. "
            f"Available ligands: {sorted(alts)[:20]}"
        )

    all_resnums = sorted({key[0] for key in prot_res})
    binding_1idx = []
    min_dists = {}
    for resnum in all_resnums:
        # gather all atoms for this residue
        res_atoms = []
        for key, atoms in prot_res.items():
            if key[0] == resnum:
                res_atoms.extend(atoms)
        if not res_atoms:
            continue
        min_d = min(_dist(pa, la) for pa in res_atoms for la in ligand_atoms)
        min_dists[resnum] = min_d
        if min_d <= cutoff_A:
            binding_1idx.append(resnum)

    print(f'  PDB {pdb_path}: {len(all_resnums)} residues in chain {chain}, '
          f'{len(binding_1idx)} binding residues within {cutoff_A}A of {ligand_resname}')
    return {
        'binding_residues_1idx': sorted(binding_1idx),
        'all_residue_nums':      all_resnums,
        'min_distances':         min_dists,
        'available_ligands':     available,
    }


def map_pdb_to_seq_indices(pdb_resnums, seq_length, pdb_start=None):
    """
    Map PDB 1-indexed residue numbers to 0-indexed sequence positions.

    Strategy: sort PDB residue numbers and assign sequential positions starting at 0.
    If pdb_start is given, offset = pdb_start - 1.  Otherwise, assume PDB starts at
    the first residue number encountered.
    """
    sorted_resnums = sorted(pdb_resnums)
    if pdb_start is None:
        pdb_start = sorted_resnums[0]
    offset = pdb_start - 1  # PDB resnum -> 0-indexed: resnum - pdb_start
    # Build mapping: pdb_resnum -> seq_idx
    mapping = {}
    for rn in sorted_resnums:
        idx = rn - pdb_start  # 0-indexed
        if 0 <= idx < seq_length:
            mapping[rn] = idx
    return mapping


# ── 3. ESM-2 on-the-fly encoding ─────────────────────────────────────────────

def encode_sequence_esm2(sequence, esm_dim, device='cpu', max_len=1022):
    """
    Run ESM-2 on the protein sequence and return (1, L, D) residue embeddings.

    esm_dim : expected embedding dimension (selects the right ESM-2 variant)
    max_len : ESM-2 token limit (1022 residues + CLS + EOS = 1024 total)
    """
    from transformers import EsmModel, EsmTokenizer

    model_tag = _ESM2_TAGS.get(esm_dim)
    if model_tag is None:
        raise ValueError(f'Unknown esm_dim={esm_dim}. Expected one of {list(_ESM2_TAGS)}')

    print(f'  ESM-2 encoding with {model_tag} (dim={esm_dim}) ...')
    tokenizer = EsmTokenizer.from_pretrained(model_tag)
    esm = EsmModel.from_pretrained(model_tag).to(device)
    esm.eval()

    seq = sequence[:max_len]  # truncate if needed
    if len(sequence) > max_len:
        print(f'  WARNING: sequence truncated from {len(sequence)} to {max_len} residues')

    inputs = tokenizer(seq, return_tensors='pt', add_special_tokens=True).to(device)
    with torch.no_grad():
        out = esm(**inputs)
    # Remove CLS and EOS tokens: shape (1, L+2, D) -> (1, L, D)
    emb = out.last_hidden_state[:, 1:-1, :]
    print(f'  ESM-2 embedding shape: {tuple(emb.shape)}')
    return emb   # (1, L, D)


# ── 4. Per-residue attribution extraction ────────────────────────────────────

def get_residue_attribution(model, drug_graph, protein_emb_3d, task):
    """
    Extract per-residue attribution from model given a 3D protein embedding (1, L, D).

    Returns dict:
        attn_weights   : (L,) normalised AttentionPooling weights  (or None)
        protein_cam    : (L,) normalised BiGRU Grad-CAM            (or None)
        prot_ensemble  : (L,) 0.5*attn + 0.5*cam                   (or None)
        logits         : raw model output
        prob           : DTI interaction probability
    """
    model.eval()
    L = protein_emb_3d.shape[1]

    # Project if needed (prot_input_proj maps esm_dim -> hidden_dim)
    with torch.no_grad():
        prot_proj = protein_emb_3d
        if (hasattr(model, 'prot_input_proj') and model.prot_input_proj is not None
                and prot_proj.shape[-1] == model.prot_input_proj.weight.shape[1]):
            prot_proj = model.prot_input_proj(prot_proj)

        attn_dict = model.get_attention_weights(drug_graph, prot_proj)

    residue_weights = (attn_dict['residue_weights'][0].numpy()
                       if attn_dict['residue_weights'] is not None else None)

    # Grad-CAM on protein BiGRU
    cam_res = compute_all_grad_cam(
        model, drug_graph, protein_emb_3d, task,
        protein_emb_seq=protein_emb_3d,
        layer_idx=-1,
    )
    protein_cam  = cam_res['protein_cam'].numpy()  if cam_res['protein_cam']  is not None else None
    protein_gn   = cam_res['protein_grad_norm'].numpy() if cam_res['protein_grad_norm'] is not None else None

    logits = attn_dict['logits']
    if task == 'dti':
        prob = torch.softmax(logits, dim=-1)[0, 1].item()
    else:
        prob = logits[0, 0].item()

    # Ensemble
    prot_ensemble = None
    if residue_weights is not None and protein_cam is not None:
        prot_ensemble = ensemble_attribution(residue_weights, protein_cam, alpha=0.5)
    elif protein_cam is not None:
        prot_ensemble = protein_cam
    elif residue_weights is not None:
        prot_ensemble = residue_weights

    return {
        'attn_weights':   residue_weights,
        'protein_cam':    protein_cam,
        'protein_grad_norm': protein_gn,
        'prot_ensemble':  prot_ensemble,
        'logits':         logits,
        'prob':           prob,
    }


# ── 5. Evaluation metrics ─────────────────────────────────────────────────────

def precision_at_k(scores, binding_set_0idx, k):
    """Fraction of top-k residues that are in the binding set."""
    top_k = set(np.argsort(scores)[::-1][:k].tolist())
    return len(top_k & binding_set_0idx) / k if k > 0 else 0.0


def recall_at_k(scores, binding_set_0idx, k):
    """Fraction of binding residues recovered in top-k."""
    if not binding_set_0idx:
        return 0.0
    top_k = set(np.argsort(scores)[::-1][:k].tolist())
    return len(top_k & binding_set_0idx) / len(binding_set_0idx)


def enrichment_at_k(scores, binding_set_0idx, k, n_residues):
    """P@k divided by random baseline (|binding| / n_residues)."""
    random_base = len(binding_set_0idx) / n_residues if n_residues > 0 else 0
    p_at_k = precision_at_k(scores, binding_set_0idx, k)
    return p_at_k / random_base if random_base > 0 else 0.0


def evaluate_residue_attribution(scores, binding_set_0idx, n_residues, k_fracs=None):
    """
    Compute AUROC, Precision@K, Recall@K, and Enrichment@K for residue attribution.

    Returns dict with all metrics.
    """
    if k_fracs is None:
        k_fracs = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]

    scores = np.asarray(scores)
    n = n_residues

    # Binary labels
    y_true = np.zeros(n)
    for idx in binding_set_0idx:
        if 0 <= idx < n:
            y_true[idx] = 1

    if y_true.sum() == 0:
        print('  WARNING: no binding residues mapped to sequence — AUROC unavailable')
        auroc = None
    elif y_true.sum() == n:
        print('  WARNING: all residues are binding residues — AUROC unavailable')
        auroc = None
    else:
        auroc = float(roc_auc_score(y_true, scores[:n]))

    k_values, prec, rec, enrich = [], [], [], []
    for frac in k_fracs:
        k = max(1, int(round(frac * n)))
        k_values.append(k)
        prec.append(float(precision_at_k(scores, binding_set_0idx, k)))
        rec.append(float(recall_at_k(scores, binding_set_0idx, k)))
        enrich.append(float(enrichment_at_k(scores, binding_set_0idx, k, n)))

    return {
        'auroc':        auroc,
        'k_fracs':      k_fracs,
        'k_values':     k_values,
        'precision_at_k': prec,
        'recall_at_k':    rec,
        'enrichment_at_k': enrich,
        'n_binding':    int(y_true.sum()),
        'n_residues':   n,
        'random_base':  float(y_true.sum() / n if n > 0 else 0),
    }


# ── 6. Plots ──────────────────────────────────────────────────────────────────

def plot_case_study_results(eval_res, out_path, title=None, dpi=200):
    """Two-panel: Precision@K and Recall@K curves."""
    k_pct = [int(round(f * 100)) for f in eval_res['k_fracs']]
    rand  = eval_res['random_base']

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    for ax, metric, label in [
        (axes[0], eval_res['precision_at_k'], 'Precision@K'),
        (axes[1], eval_res['recall_at_k'],    'Recall@K'),
    ]:
        ax.plot(k_pct, metric, 'o-', color='#d62728', linewidth=2, label='Model attribution')
        if label == 'Precision@K':
            ax.axhline(rand, color='grey', linestyle='--', linewidth=1.2,
                       label=f'Random ({rand:.3f})')
        ax.set_xlabel('Top-k residues (%)', fontsize=11)
        ax.set_ylabel(label, fontsize=11)
        ax.set_ylim(0, 1.05)
        ax.tick_params(labelsize=9)
        ax.legend(fontsize=8)

    auroc_str = f'AUROC={eval_res["auroc"]:.3f}' if eval_res['auroc'] is not None else 'AUROC=N/A'
    suptitle = (title or 'Case Study') + f'  |  {auroc_str}'
    fig.suptitle(suptitle, fontsize=11, fontweight='bold')
    plt.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved evaluation plot: {out_path}')


# ── 7. Main case study runner ─────────────────────────────────────────────────

def run_case_study(
    case_cfg,
    model,
    esm_dim,
    pdb_cache_dir,
    out_dir,
    device='cpu',
):
    """
    Full Phase 5 pipeline for one case study.

    Returns results dict.
    """
    name       = case_cfg['name']
    drug_id    = case_cfg['drug_id']
    protein_id = case_cfg['protein_id']
    pdb_id     = case_cfg['pdb_id']
    chain      = case_cfg['pdb_chain']
    ligand     = case_cfg['pdb_ligand']
    cutoff     = case_cfg.get('cutoff_A', 4.5)
    sequence   = case_cfg.get('sequence')

    os.makedirs(out_dir, exist_ok=True)
    print(f'\n{"="*64}')
    print(f'  Case Study: {name}  ({drug_id} / {protein_id})')
    print(f'  PDB: {pdb_id} chain {chain} ligand {ligand}')
    print(f'{"="*64}')

    # Load sequence from dataset if not provided
    if sequence is None:
        import pandas as pd
        pairs_csv = os.path.join(_REPO, 'Dataset', 'raw', 'yamanishi_08', 'e', 'pairs.csv')
        df = pd.read_csv(pairs_csv)
        row = df[(df.drug_id == drug_id) & (df.protein_id == protein_id) & (df.label == 1)]
        if row.empty:
            raise ValueError(f'Pair ({drug_id}, {protein_id}) not found in yamanishi_e pairs.csv')
        sequence = row.iloc[0]['sequence']

    L = len(sequence)
    print(f'  Protein sequence length: {L} aa')

    # ── Drug graph ────────────────────────────────────────────────────────────
    smiles = case_cfg['smiles']
    from torch_geometric.data import Batch
    drug_data  = _smiles_to_graph(smiles)
    drug_batch = Batch.from_data_list([drug_data]).to(device)

    # ── PDB binding site ──────────────────────────────────────────────────────
    pdb_path = download_pdb(pdb_id, pdb_cache_dir)
    pdb_info = extract_binding_residues(pdb_path, chain, ligand, cutoff_A=cutoff)
    binding_1idx = pdb_info['binding_residues_1idx']

    # Map PDB 1-indexed residue numbers to 0-indexed sequence positions
    all_resnums = pdb_info['all_residue_nums']
    resnum_to_idx = map_pdb_to_seq_indices(all_resnums, L)
    binding_0idx  = set()
    for rn in binding_1idx:
        if rn in resnum_to_idx:
            binding_0idx.add(resnum_to_idx[rn])

    # Also include literature-reported binding residues if provided
    lit_binding_1idx = case_cfg.get('lit_binding_1idx', [])
    lit_binding_0idx = set()
    for rn in lit_binding_1idx:
        if rn in resnum_to_idx:
            lit_binding_0idx.add(resnum_to_idx[rn])
        elif 0 < rn <= L:
            lit_binding_0idx.add(rn - 1)  # fallback: 1-indexed → 0-indexed

    # Union of PDB and literature
    combined_binding = binding_0idx | lit_binding_0idx

    print(f'  PDB binding residues (4Å): {len(binding_0idx)} mapped (from {len(binding_1idx)} in PDB)')
    print(f'  Literature binding residues: {len(lit_binding_0idx)}')
    print(f'  Combined binding set: {len(combined_binding)} residues')

    # ── ESM-2 on-the-fly encoding ─────────────────────────────────────────────
    prot_emb_3d = encode_sequence_esm2(sequence, esm_dim, device=device)  # (1, L, D)

    # ── Per-residue attribution ────────────────────────────────────────────────
    attr = get_residue_attribution(model, drug_batch, prot_emb_3d, model.task)
    prob        = attr['prob']
    prot_ens    = attr['prot_ensemble']
    attn_w      = attr['attn_weights']
    protein_cam = attr['protein_cam']

    print(f'  DTI prediction probability: {prob:.4f}')

    if prot_ens is None:
        print('  ERROR: no per-residue attribution available (check model architecture)')
        return None

    # ── Evaluation ────────────────────────────────────────────────────────────
    eval_res = evaluate_residue_attribution(prot_ens, combined_binding, L)
    print(f'  AUROC vs. binding site: {eval_res["auroc"]}')

    # Separate evaluation by signal
    eval_attn = evaluate_residue_attribution(attn_w, combined_binding, L) if attn_w is not None else None
    eval_cam  = evaluate_residue_attribution(protein_cam, combined_binding, L) if protein_cam is not None else None

    # ── Visualisation ──────────────────────────────────────────────────────────
    case_key = f'{drug_id}_{protein_id}'
    vis_stem = os.path.join(out_dir, f'cs_{case_key}_protein')
    visualize_protein_attribution(
        prot_ens,
        out_stem=vis_stem,
        sequence=sequence,
        title=f'{name}  |  prob={prob:.3f}',
        method_label='Ensemble',
        known_binding=combined_binding,
    )

    plot_case_study_results(
        eval_res,
        out_path=os.path.join(out_dir, f'cs_{case_key}_eval.png'),
        title=name,
    )

    # ── Save .npz ──────────────────────────────────────────────────────────────
    npz_path = os.path.join(out_dir, f'cs_{case_key}.npz')
    np.savez_compressed(npz_path,
        prot_ensemble=prot_ens,
        attn_weights=attn_w if attn_w is not None else np.array([-1]),
        protein_cam=protein_cam if protein_cam is not None else np.array([-1]),
        binding_0idx=np.array(sorted(combined_binding)),
        pdb_binding_0idx=np.array(sorted(binding_0idx)),
        lit_binding_0idx=np.array(sorted(lit_binding_0idx)),
        prob=np.float32(prob),
    )
    print(f'  Saved .npz: {npz_path}')

    # ── Report ──────────────────────────────────────────────────────────────────
    report = [
        f'Case Study: {name}',
        f'Drug: {drug_id}  SMILES: {smiles[:60]}...',
        f'Protein: {protein_id}  Length: {L} aa',
        f'PDB: {pdb_id} chain {chain} ligand {ligand}  cutoff={cutoff}A',
        f'PDB binding residues (1-idx): {sorted(binding_1idx)[:20]}',
        f'Literature binding (1-idx): {sorted(lit_binding_1idx)}',
        f'Combined binding set (0-idx): {sorted(combined_binding)[:20]}',
        f'',
        f'Prediction probability: {prob:.4f}',
        f'',
        f'Evaluation (Ensemble attribution vs. combined binding set):',
        f'  AUROC:   {eval_res["auroc"]}',
        f'  N binding residues: {eval_res["n_binding"]} / {L}',
        f'  Random baseline P@k: {eval_res["random_base"]:.4f}',
    ]
    for frac, k, p, r, e in zip(eval_res['k_fracs'], eval_res['k_values'],
                                  eval_res['precision_at_k'], eval_res['recall_at_k'],
                                  eval_res['enrichment_at_k']):
        report.append(f'  k={k:3d} ({int(frac*100):3d}%): P@k={p:.3f}  R@k={r:.3f}  EF={e:.2f}x')

    if eval_attn:
        report.append(f'')
        report.append(f'AttentionPooling AUROC: {eval_attn["auroc"]}')
    if eval_cam:
        report.append(f'Grad-CAM AUROC: {eval_cam["auroc"]}')

    rpt_path = os.path.join(out_dir, f'cs_{case_key}_report.txt')
    with open(rpt_path, 'w') as f:
        f.write('\n'.join(report))
    print(f'  Saved report: {rpt_path}')

    return {
        'name':          name,
        'drug_id':       drug_id,
        'protein_id':    protein_id,
        'prob':          prob,
        'auroc':         eval_res['auroc'],
        'eval_ensemble': eval_res,
        'eval_attn':     eval_attn,
        'eval_cam':      eval_cam,
        'n_binding':     eval_res['n_binding'],
        'n_residues':    L,
        'out_dir':       out_dir,
    }


def print_case_study_summary(results):
    w = 64
    print('\n' + '=' * w)
    print('  Phase 5 Case Study Summary')
    print('=' * w)
    for res in results:
        if res is None:
            continue
        auroc_str = f'{res["auroc"]:.4f}' if res['auroc'] is not None else 'N/A'
        print(f'\n  {res["name"]}  ({res["drug_id"]} / {res["protein_id"]})')
        print(f'    Pred prob : {res["prob"]:.4f}')
        print(f'    AUROC     : {auroc_str}  (n_binding={res["n_binding"]}/{res["n_residues"]})')
        if res['eval_ensemble']:
            ev = res['eval_ensemble']
            for frac, k, p, r, e in zip(ev['k_fracs'], ev['k_values'],
                                          ev['precision_at_k'], ev['recall_at_k'],
                                          ev['enrichment_at_k']):
                if frac in (0.10, 0.20, 0.30):
                    print(f'    P@{int(frac*100):2d}%={p:.3f}  R@{int(frac*100):2d}%={r:.3f}  EF={e:.2f}x  (k={k})')
    print('=' * w + '\n')


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(description='Phase 5: case study validation against PDB binding sites')
    ap.add_argument('--checkpoint',  required=True,
                    help='Model checkpoint path (yamanishi_e or luo_17)')
    ap.add_argument('--case',        nargs='+', default=list(CASE_STUDIES.keys()),
                    help=f'Case study keys (default: all). Available: {list(CASE_STUDIES.keys())}')
    ap.add_argument('--device',      default='cpu')
    ap.add_argument('--out_dir',     default=None)
    ap.add_argument('--pdb_cache',   default=None,
                    help='Directory to cache downloaded PDB files')
    args = ap.parse_args()

    device = torch.device(args.device)

    print(f'Loading model from {args.checkpoint} ...')
    model = load_model(args.checkpoint, device)

    # Determine ESM-2 embedding dimension from model
    if hasattr(model, 'prot_input_proj') and model.prot_input_proj is not None:
        esm_dim = model.prot_input_proj.weight.shape[1]
    else:
        esm_dim = 320
    print(f'  ESM-2 dim: {esm_dim}')

    out_dir = args.out_dir or os.path.join(
        _REPO, 'paper', 'figures', 'interpretability', 'case_studies')
    pdb_cache = args.pdb_cache or os.path.join(out_dir, '_pdb_cache')

    results = []
    for case_key in args.case:
        if case_key not in CASE_STUDIES:
            print(f'  Unknown case: {case_key}. Available: {list(CASE_STUDIES.keys())}')
            continue
        try:
            res = run_case_study(
                CASE_STUDIES[case_key],
                model,
                esm_dim=esm_dim,
                pdb_cache_dir=pdb_cache,
                out_dir=out_dir,
                device=args.device,
            )
            results.append(res)
        except Exception as e:
            print(f'  ERROR in case {case_key}: {e}')
            import traceback
            traceback.print_exc()

    if results:
        print_case_study_summary(results)
        summary_path = os.path.join(out_dir, 'case_study_summary.json')
        safe = []
        for r in results:
            if r is None:
                continue
            sr = {k: v for k, v in r.items() if isinstance(v, (str, int, float, type(None)))}
            if r.get('eval_ensemble'):
                ev = r['eval_ensemble']
                sr['auroc'] = ev['auroc']
                sr['precision_at_20pct'] = ev['precision_at_k'][3] if len(ev['precision_at_k']) > 3 else None
                sr['recall_at_20pct']    = ev['recall_at_k'][3]    if len(ev['recall_at_k'])    > 3 else None
                sr['enrichment_at_20pct'] = ev['enrichment_at_k'][3] if len(ev['enrichment_at_k']) > 3 else None
            safe.append(sr)
        with open(summary_path, 'w') as f:
            json.dump(safe, f, indent=2)
        print(f'Summary saved to {summary_path}')

    print(f'\nDone. Figures: {out_dir}')


if __name__ == '__main__':
    main()
