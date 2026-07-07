"""
Phase 3.3 — Drug-Protein Interaction Heatmap

Since GatedCrossAttention operates on global (B,H) vectors (not per-atom x per-residue),
this module computes a pseudo-interaction matrix as the outer product of drug atom
scores and protein residue scores:

    interaction[i, j] = drug_score[i] * protein_score[j]

This reveals the joint attribution surface — which drug atom + protein residue combinations
are jointly important.  The outer product is a valid visualisation for interpretability
papers (e.g. used in MutualDTA, Yuan et al. 2025).

Outputs:
    {out_stem}_matrix.png   — 2D heatmap (atoms x residues)
    {out_stem}_joint.png    — drug bar (top) + protein bar (left) + matrix composite
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import matplotlib.cm as cm

from rdkit import Chem


_CMAP_MATRIX = cm.get_cmap('YlOrRd')  # white→yellow→red: high joint importance = red


def compute_interaction_matrix(drug_scores, protein_scores):
    """
    Outer product of normalised drug and protein importance vectors.

    Returns (N_atoms, L_residues) matrix, values in [0, 1].
    """
    d = np.asarray(drug_scores,    dtype=float).reshape(-1)
    p = np.asarray(protein_scores, dtype=float).reshape(-1)
    mat = np.outer(d, p)
    lo, hi = mat.min(), mat.max()
    if hi > lo:
        mat = (mat - lo) / (hi - lo)
    return mat


def visualize_interaction_matrix(
    drug_scores,
    protein_scores,
    out_stem,
    mol=None,
    sequence=None,
    title=None,
    max_residues=100,
    dpi=300,
):
    """
    Plot the drug-protein interaction pseudo-matrix.

    Args:
        drug_scores    : (N_atoms,) normalised importance scores
        protein_scores : (L_residues,) normalised importance scores
        out_stem       : output path stem (no extension)
        mol            : RDKit Mol (optional — adds atom element labels on y-axis)
        sequence       : protein sequence string (optional — adds residue labels on x-axis)
        title          : figure title
        max_residues   : truncate protein axis to this many residues (visual clarity)
        dpi            : output resolution

    Saves {out_stem}_matrix.png
    """
    d_scores = np.asarray(drug_scores,    dtype=float)
    p_scores = np.asarray(protein_scores, dtype=float)
    N = len(d_scores)
    L = min(len(p_scores), max_residues)
    p_scores = p_scores[:L]

    mat = compute_interaction_matrix(d_scores, p_scores)   # (N, L)

    # Atom labels (y-axis): element + index
    if mol is not None:
        atom_labels = [f"{a.GetSymbol()}{a.GetIdx()}" for a in mol.GetAtoms()]
    else:
        atom_labels = [f"A{i}" for i in range(N)]

    # Residue labels (x-axis): AA + position
    if sequence is not None:
        seq = list(str(sequence))[:L]
        res_labels = [f"{aa}{i}" for i, aa in enumerate(seq)]
    else:
        res_labels = [str(i) for i in range(L)]

    # ── Simple matrix heatmap ─────────────────────────────────────────────────
    fig_w = max(10, 0.15 * L + 2)
    fig_h = max(4,  0.35 * N + 1)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    im = ax.imshow(mat, aspect='auto', cmap=_CMAP_MATRIX,
                   vmin=0, vmax=1, origin='upper')

    # Axis ticks
    x_step = max(1, L // 20)
    ax.set_xticks(range(0, L, x_step))
    ax.set_xticklabels(res_labels[::x_step], rotation=90, fontsize=6)
    ax.set_yticks(range(N))
    ax.set_yticklabels(atom_labels, fontsize=8)
    ax.set_xlabel('Protein Residue', fontsize=10)
    ax.set_ylabel('Drug Atom',       fontsize=10)

    if title:
        ax.set_title(title, fontsize=12, fontweight='bold', pad=8)

    # Highlight rows/columns exceeding 2× mean (putative binding contacts)
    threshold = 2 * mat.mean()
    hot_atoms = np.where(mat.max(axis=1) > threshold)[0]
    hot_res   = np.where(mat.max(axis=0) > threshold)[0]
    for r in hot_atoms:
        ax.axhline(r - 0.5, color='dodgerblue', linewidth=0.4, alpha=0.5)
        ax.axhline(r + 0.5, color='dodgerblue', linewidth=0.4, alpha=0.5)

    cbar = fig.colorbar(im, ax=ax, shrink=0.5)
    cbar.set_label('Joint Importance', fontsize=9)
    cbar.ax.tick_params(labelsize=7)

    plt.tight_layout()
    mat_path = out_stem + '_matrix.png'
    fig.savefig(mat_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved interaction matrix: {mat_path}")

    # ── Composite: drug bar (top) + protein bar (bottom) + matrix ─────────────
    joint_path = _save_joint_figure(d_scores, p_scores, mat, atom_labels, res_labels,
                                    out_stem + '_joint.png', title=title, dpi=dpi)

    return {
        'matrix':     mat,
        'hot_atoms':  hot_atoms.tolist(),
        'hot_res':    hot_res.tolist(),
        'matrix_png': mat_path,
        'joint_png':  joint_path,
    }


def _save_joint_figure(d_scores, p_scores, mat, atom_labels, res_labels,
                       path, title=None, dpi=200):
    """
    Three-panel composite:
      - Top row: drug atom bar chart
      - Bottom-left: protein residue bar chart (rotated)
      - Bottom-right: interaction matrix
    """
    N = len(d_scores)
    L = len(p_scores)

    fig = plt.figure(figsize=(max(10, 0.15 * L + 2), max(6, 0.35 * N + 3)))
    gs  = gridspec.GridSpec(2, 2, figure=fig,
                            width_ratios=[1, max(3, L // 5)],
                            height_ratios=[1, max(2, N // 3)],
                            hspace=0.05, wspace=0.05)

    ax_drug = fig.add_subplot(gs[0, 1])
    ax_prot = fig.add_subplot(gs[1, 0])
    ax_mat  = fig.add_subplot(gs[1, 1])

    # Drug bar (top)
    drug_colors = plt.cm.coolwarm(d_scores)
    ax_drug.bar(range(L), np.ones(L) * 0.0, bottom=0)  # placeholder for width
    ax_drug.bar(range(N), d_scores, color=drug_colors)
    ax_drug.set_xlim(-0.5, max(L, N) - 0.5)
    ax_drug.set_xticks([])
    ax_drug.set_ylabel('Drug Score', fontsize=8)
    ax_drug.tick_params(labelsize=7)
    if title:
        ax_drug.set_title(title, fontsize=11, fontweight='bold')

    # Protein bar (left, horizontal)
    prot_colors = plt.cm.Blues(p_scores)
    ax_prot.barh(range(L), p_scores, color=prot_colors)
    ax_prot.invert_yaxis()
    ax_prot.set_ylim(-0.5, L - 0.5)
    ax_prot.set_yticks([])
    ax_prot.set_xlabel('Protein Score', fontsize=8)
    ax_prot.tick_params(labelsize=7)

    # Matrix
    ax_mat.imshow(mat.T, aspect='auto', cmap=_CMAP_MATRIX, vmin=0, vmax=1, origin='upper')
    x_step = max(1, N // 8)
    y_step = max(1, L // 15)
    ax_mat.set_xticks(range(0, N, x_step))
    ax_mat.set_xticklabels(atom_labels[::x_step], rotation=90, fontsize=6)
    ax_mat.set_yticks(range(0, L, y_step))
    ax_mat.set_yticklabels(res_labels[::y_step], fontsize=6)
    ax_mat.set_xlabel('Drug Atom', fontsize=8)
    ax_mat.set_ylabel('Residue',   fontsize=8)

    # Hide unused top-left quadrant
    fig.add_subplot(gs[0, 0]).axis('off')

    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved joint figure: {path}")
    return path


def print_hot_contacts(mat, atom_labels, res_labels, top_k=10):
    """Print the top-k highest joint-importance drug-residue contacts."""
    flat = mat.flatten()
    top_flat = np.argsort(flat)[-top_k:][::-1]
    N, L = mat.shape
    print(f"\n-- Top-{top_k} Joint Contacts --")
    print(f"{'Rank':<5} {'Atom':<10} {'Residue':<10} {'JointScore':<12}")
    print('-' * 40)
    for rank, fi in enumerate(top_flat, 1):
        ai = fi // L
        ri = fi %  L
        print(f"{rank:<5} {atom_labels[ai]:<10} {res_labels[ri]:<10} {mat[ai, ri]:.4f}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    ap = argparse.ArgumentParser(description="Phase 3.3: drug-protein interaction heatmap")
    ap.add_argument('--npz',       required=True,  help=".npz from extract_attention.py or combined")
    ap.add_argument('--smiles',    default=None,   help="Drug SMILES (for atom labels)")
    ap.add_argument('--sequence',  default=None,   help="Protein amino-acid sequence")
    ap.add_argument('--drug_key',  default='atom_importance')
    ap.add_argument('--prot_key',  default='residue_weights')
    ap.add_argument('--out',       default=None)
    ap.add_argument('--title',     default=None)
    args = ap.parse_args()

    data = np.load(args.npz, allow_pickle=True)
    d_scores = data[args.drug_key]
    p_scores = data[args.prot_key]
    if p_scores is None or (len(p_scores) == 1 and p_scores[0] == -1):
        print("No protein residue scores in .npz.  Run with --sequence to get per-residue weights.")
        sys.exit(1)

    mol = Chem.MolFromSmiles(args.smiles) if args.smiles else None
    out_stem = args.out or args.npz.replace('.npz', '_interaction')
    res = visualize_interaction_matrix(
        d_scores, p_scores, out_stem=out_stem,
        mol=mol, sequence=args.sequence, title=args.title)

    atom_labels = ([f"{a.GetSymbol()}{a.GetIdx()}" for a in mol.GetAtoms()]
                   if mol else [f"A{i}" for i in range(len(d_scores))])
    seq = list(str(args.sequence))[:len(p_scores)] if args.sequence else None
    res_labels = ([f"{aa}{i}" for i, aa in enumerate(seq)]
                  if seq else [str(i) for i in range(len(p_scores))])
    print_hot_contacts(res['matrix'], atom_labels, res_labels, top_k=10)
