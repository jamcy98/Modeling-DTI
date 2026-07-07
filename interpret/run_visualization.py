"""
Phase 3.4 — Batch Visualization Pipeline

Runs Phase 1 + Phase 2 + all three visualizations for a list of drug-target pairs,
saving everything to paper/figures/interpretability/.

Usage:
    python -m interpret.run_visualization \
        --checkpoint checkpoints/hgnn_rnn_dti_phase3_ft_esm150m_1to5_luo_17_dti_cold_target_fold0_seed1_best.pt \
        --dataset luo_17 --emb_tag esm150m \
        --pairs DB00150,P19838 DB00619,P00533 \
        --device cpu

    # Or pass a CSV file:
    python -m interpret.run_visualization --pairs_csv case_studies.csv --checkpoint ...

case_studies.csv format (no header):
    drug_id,protein_id[,smiles,sequence]

Outputs per pair (in paper/figures/interpretability/):
    {drug_id}_{protein_id}/
        attribution.npz        — Phase 1 + Phase 2 scores
        drug.png               — atom highlight plot
        drug.svg
        drug_bar.png           — atom importance bar chart
        protein.png            — residue heatmap
        interaction_matrix.png — joint importance pseudo-matrix
        interaction_joint.png  — composite panel
        report.txt             — text summary
"""

import os
import sys
import json
import argparse
import numpy as np

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from rdkit import Chem

from interpret.extract_attention import load_model, get_drug_graph, get_protein_emb, extract
from interpret.grad_cam          import compute_all_grad_cam, ensemble_attribution
from interpret.visualize_drug    import (visualize_drug_attribution,
                                         print_top_atom_table)
from interpret.visualize_protein import (visualize_protein_attribution,
                                          print_top_residue_table)
from interpret.visualize_cross_attention import (visualize_interaction_matrix,
                                                  print_hot_contacts)


FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'paper', 'figures', 'interpretability')


def run_pair(
    model,
    drug_id=None, protein_id=None,
    smiles=None,  sequence=None,
    dataset=None, emb_tag='esm150m',
    device='cpu',
    out_dir=None,
    pair_label=None,
):
    """
    Run full Phase 1 + 2 + 3 pipeline for a single drug-target pair.

    Returns dict summarising all outputs.
    """
    label = pair_label or f"{drug_id or 'drug'}_{protein_id or 'prot'}"
    if out_dir is None:
        out_dir = os.path.join(FIG_DIR, label)
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"  Pair: {label}")
    print(f"{'='*60}")

    # ── Phase 1: extract attention weights ────────────────────────────────────
    drug_batch = get_drug_graph(smiles=smiles, drug_id=drug_id, dataset=dataset, device=device)
    prot_emb   = get_protein_emb(sequence=sequence, protein_id=protein_id,
                                  dataset=dataset, emb_tag=emb_tag, device=device)

    # Input-gradient saliency + GCA gate + residue weights (if sequence mode)
    from interpret.extract_attention import compute_atom_saliency
    model.eval()

    with torch.no_grad():
        prot_for_attn = prot_emb.clone()
        if prot_for_attn.shape[-1] != 320:
            prot_for_attn = model.prot_input_proj(prot_for_attn)
        attn_dict = model.get_attention_weights(drug_batch, prot_for_attn)

    atom_imp, _ = compute_atom_saliency(model, drug_batch, prot_emb, model.task)
    atom_imp    = atom_imp.numpy()

    residue_weights = (attn_dict['residue_weights'][0].numpy()
                       if attn_dict['residue_weights'] is not None else None)
    gate_mean       = attn_dict['gate'][0].mean().item()
    logits          = attn_dict['logits']

    if model.task == 'dti':
        prob = torch.softmax(logits, dim=-1)[0, 1].item()
        pred = logits[0, 1].item()
    else:
        prob = pred = logits[0, 0].item()

    # ── Phase 2: Grad-CAM ─────────────────────────────────────────────────────
    prot_seq_for_cam = prot_emb if prot_emb.dim() == 3 else None
    cam_result = compute_all_grad_cam(
        model, drug_batch, prot_emb, model.task,
        protein_emb_seq=prot_seq_for_cam,
        layer_idx=-1,
    )
    drug_cam    = cam_result['drug_cam'].numpy()
    protein_cam = cam_result['protein_cam'].numpy() if cam_result['protein_cam'] is not None else None
    prot_gn     = cam_result['protein_grad_norm'].numpy() if cam_result['protein_grad_norm'] is not None else None

    # ── Ensemble ──────────────────────────────────────────────────────────────
    drug_ensemble = ensemble_attribution(atom_imp, drug_cam, alpha=0.5)

    prot_ensemble = None
    if residue_weights is not None and protein_cam is not None:
        prot_ensemble = ensemble_attribution(residue_weights, protein_cam, alpha=0.5)
    elif protein_cam is not None:
        prot_ensemble = protein_cam
    elif residue_weights is not None:
        prot_ensemble = residue_weights

    # Save full attribution arrays
    npz_path = os.path.join(out_dir, 'attribution.npz')
    save_dict = {
        'atom_importance': atom_imp,
        'drug_cam':        drug_cam,
        'drug_ensemble':   drug_ensemble,
        'gate_mean':       np.float32(gate_mean),
        'prediction':      np.float32(pred),
        'prediction_prob': np.float32(prob),
    }
    if residue_weights is not None:
        save_dict['residue_weights'] = residue_weights
    if protein_cam is not None:
        save_dict['protein_cam']  = protein_cam
    if prot_gn is not None:
        save_dict['protein_grad_norm'] = prot_gn
    if prot_ensemble is not None:
        save_dict['prot_ensemble']  = prot_ensemble
    np.savez_compressed(npz_path, **save_dict)
    print(f"  Saved attribution.npz: {npz_path}")

    # ── Get RDKit mol + SMILES ────────────────────────────────────────────────
    mol_smiles = smiles
    if mol_smiles is None and hasattr(drug_batch, 'smiles'):
        s = drug_batch.smiles
        mol_smiles = s[0] if isinstance(s, (list, tuple)) else str(s)
    mol = Chem.MolFromSmiles(mol_smiles) if mol_smiles else None

    # ── Phase 3.1: Drug visualisation ────────────────────────────────────────
    if mol is not None:
        drug_stem = os.path.join(out_dir, 'drug')
        drug_title = f"{label}  |  {model.task.upper()}  |  prob={prob:.3f}"
        visualize_drug_attribution(mol, drug_ensemble, out_stem=drug_stem,
                                    title=drug_title, method_label='Ensemble')
        top_atoms = print_top_atom_table(mol, drug_ensemble, top_k=5, label=f'({label})')
    else:
        print("  WARNING: no SMILES available — skipping drug visualisation")
        top_atoms = []

    # ── Phase 3.2: Protein visualisation ─────────────────────────────────────
    prot_scores = prot_ensemble if prot_ensemble is not None else None
    if prot_scores is not None:
        prot_stem  = os.path.join(out_dir, 'protein')
        prot_title = f"{label} — Protein Residue Attribution"
        visualize_protein_attribution(prot_scores, out_stem=prot_stem,
                                       sequence=sequence,
                                       title=prot_title,
                                       method_label='Ensemble')
        top_res = print_top_residue_table(prot_scores, sequence=sequence,
                                           top_k=10, label=f'({label})')

        # Multi-method comparison if we have multiple signals
        if residue_weights is not None and protein_cam is not None:
            from interpret.visualize_protein import compare_attribution_methods
            methods_dict = {'AttnPool': residue_weights, 'GradCAM': protein_cam}
            if prot_gn is not None:
                methods_dict['GradNorm'] = prot_gn
            compare_attribution_methods(methods_dict,
                                         out_stem=prot_stem,
                                         sequence=sequence,
                                         title=prot_title)
    else:
        print("  NOTE: no protein residue scores available (mean-pooled embeddings).")
        top_res = []

    # ── Phase 3.3: Interaction matrix ─────────────────────────────────────────
    if prot_scores is not None:
        mat_stem = os.path.join(out_dir, 'interaction')
        mat_title = f"{label} — Drug-Protein Interaction Map"
        mat_result = visualize_interaction_matrix(
            drug_ensemble, prot_scores,
            out_stem=mat_stem,
            mol=mol, sequence=sequence,
            title=mat_title,
        )
        atom_labels = ([f"{a.GetSymbol()}{a.GetIdx()}" for a in mol.GetAtoms()]
                       if mol else [f"A{i}" for i in range(len(drug_ensemble))])
        seq_list = list(str(sequence))[:len(prot_scores)] if sequence else None
        res_labels = ([f"{aa}{i}" for i, aa in enumerate(seq_list)]
                      if seq_list else [str(i) for i in range(len(prot_scores))])
        print_hot_contacts(mat_result['matrix'], atom_labels, res_labels, top_k=5)
    else:
        mat_result = None
        print("  Skipping interaction matrix (no protein residue scores).")

    # ── Text report ───────────────────────────────────────────────────────────
    report_lines = [
        f"Pair: {label}",
        f"Task: {model.task.upper()}",
        f"Prediction: {pred:.4f}  (prob={prob:.4f})",
        f"Gate mean: {gate_mean:.3f}  ({'drug context' if gate_mean > 0.5 else 'protein context'} dominates)",
        f"N atoms: {len(drug_ensemble)}",
        f"Top-5 atoms (ensemble): {[r['Atom'] for r in top_atoms]}" if top_atoms else "No mol available",
        f"Protein residue scores available: {prot_scores is not None}",
    ]
    if top_res:
        report_lines.append(f"Top-5 residues (ensemble): {top_res[:5]}")
    if mat_result:
        report_lines.append(f"Hot atoms (>2x mean): {mat_result['hot_atoms']}")
        report_lines.append(f"Hot residues (>2x mean): {mat_result['hot_res'][:10]}")

    rpt_path = os.path.join(out_dir, 'report.txt')
    with open(rpt_path, 'w') as f:
        f.write('\n'.join(report_lines))
    print(f"  Saved report: {rpt_path}")

    return {
        'label':        label,
        'prediction':   pred,
        'prob':         prob,
        'drug_ensemble': drug_ensemble,
        'prot_ensemble': prot_ensemble,
        'out_dir':      out_dir,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Phase 3.4: batch visualization pipeline")
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--dataset',    default=None)
    ap.add_argument('--emb_tag',    default='esm150m')
    ap.add_argument('--device',     default='cpu')
    ap.add_argument('--out_dir',    default=FIG_DIR)

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--pairs',     nargs='+', metavar='DRUG_ID,PROT_ID',
                        help="Space-separated pairs, each as DRUG_ID,PROT_ID")
    group.add_argument('--pairs_csv', metavar='CSV',
                        help="CSV file: drug_id,protein_id[,smiles,sequence]")

    args = ap.parse_args()

    print(f"Loading model from {args.checkpoint} ...")
    device = torch.device(args.device)
    model  = load_model(args.checkpoint, device)

    # Parse pairs
    pairs = []
    if args.pairs:
        for p in args.pairs:
            parts = p.split(',')
            pairs.append({'drug_id': parts[0], 'protein_id': parts[1],
                           'smiles': None, 'sequence': None})
    else:
        import csv
        with open(args.pairs_csv) as f:
            for row in csv.reader(f):
                pairs.append({
                    'drug_id':   row[0].strip() if len(row) > 0 else None,
                    'protein_id': row[1].strip() if len(row) > 1 else None,
                    'smiles':     row[2].strip() if len(row) > 2 else None,
                    'sequence':   row[3].strip() if len(row) > 3 else None,
                })

    results = []
    for pair in pairs:
        try:
            res = run_pair(
                model,
                drug_id=pair.get('drug_id'),
                protein_id=pair.get('protein_id'),
                smiles=pair.get('smiles'),
                sequence=pair.get('sequence'),
                dataset=args.dataset,
                emb_tag=args.emb_tag,
                device=args.device,
                out_dir=os.path.join(args.out_dir,
                                     f"{pair.get('drug_id','drug')}_{pair.get('protein_id','prot')}"),
            )
            results.append(res)
        except Exception as e:
            print(f"  ERROR processing pair {pair}: {e}")
            import traceback; traceback.print_exc()

    print(f"\nDone. Processed {len(results)}/{len(pairs)} pairs.")
    print(f"Figures saved to: {args.out_dir}")


if __name__ == '__main__':
    main()
