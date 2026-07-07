"""
Phase 3.2 — Protein Sequence Heatmap

Visualises per-residue attribution scores as a 1D colour heatmap aligned to the
protein sequence.  Long sequences (>100 residues) are split into rows.

Outputs:
    {out_stem}.png  — heatmap figure (300 dpi)
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm


_CMAP = cm.get_cmap('Blues')   # white→dark-blue; clean for residue attribution


def visualize_protein_attribution(
    residue_scores,
    out_stem,
    sequence=None,
    title=None,
    method_label='Attribution',
    row_width=50,
    dpi=300,
    known_binding=None,
):
    """
    Generate a protein sequence heatmap.

    Args:
        residue_scores  : array-like (L,), values in [0,1]
        out_stem        : output path without extension
        sequence        : amino-acid string of length L (for x-axis labels)
        title           : figure title
        method_label    : colorbar label
        row_width       : residues per row (50 fits comfortably in A4 width)
        dpi             : output resolution
        known_binding   : set/list of residue indices that are known binding-site residues
                          (drawn with red border for comparison)

    Saves {out_stem}.png
    """
    scores = np.asarray(residue_scores, dtype=float)
    L = len(scores)

    if sequence is not None:
        seq = list(str(sequence))[:L]
        # Pad to L if shorter
        seq += ['?'] * (L - len(seq))
    else:
        seq = [str(i) for i in range(L)]

    os.makedirs(os.path.dirname(os.path.abspath(out_stem)) or '.', exist_ok=True)

    n_rows = int(np.ceil(L / row_width))
    fig_h  = max(3, 1.2 * n_rows + 1.5)
    fig, axes = plt.subplots(n_rows, 1, figsize=(14, fig_h),
                              squeeze=False, constrained_layout=True)

    norm = mcolors.Normalize(vmin=0, vmax=1)

    for row in range(n_rows):
        ax   = axes[row, 0]
        lo   = row * row_width
        hi   = min(lo + row_width, L)
        seg  = scores[lo:hi]
        labs = seq[lo:hi]
        width = len(seg)

        # Draw colour boxes
        for i, (s, aa) in enumerate(zip(seg, labs)):
            color = _CMAP(norm(s))
            ax.add_patch(plt.Rectangle([i, 0], 1, 1, color=color))

            # Residue letter label
            text_col = 'white' if s > 0.6 else 'black'
            ax.text(i + 0.5, 0.5, aa, ha='center', va='center',
                    fontsize=6.5, color=text_col, fontweight='bold')

            # Known binding site: red border
            if known_binding and (lo + i) in known_binding:
                ax.add_patch(plt.Rectangle([i, 0], 1, 1,
                             fill=False, edgecolor='red', linewidth=1.5))

        # Position labels on x-axis
        tick_step = max(1, width // 10)
        ticks = list(range(0, width, tick_step))
        ax.set_xticks([t + 0.5 for t in ticks])
        ax.set_xticklabels([str(lo + t) for t in ticks], fontsize=7)
        ax.set_yticks([])
        ax.set_xlim(0, row_width)
        ax.set_ylim(0, 1)

        if row == 0 and title:
            ax.set_title(title, fontsize=12, fontweight='bold', pad=6)
        ax.set_ylabel(f"Rows {lo+1}-{hi}", fontsize=8, rotation=0,
                      labelpad=40, va='center')

    # Shared x-label
    axes[-1, 0].set_xlabel('Residue Position', fontsize=10)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=_CMAP, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes[:, 0], location='right', shrink=0.6, pad=0.01)
    cbar.set_label(f'{method_label} Score', fontsize=10)
    cbar.ax.tick_params(labelsize=8)

    if known_binding:
        from matplotlib.patches import Patch
        axes[0, 0].legend(
            handles=[Patch(facecolor='none', edgecolor='red', linewidth=1.5,
                           label='Known binding site')],
            loc='upper right', fontsize=8)

    png_path = out_stem + '.png'
    fig.savefig(png_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved protein heatmap: {png_path}")
    return png_path


def compare_attribution_methods(
    residue_scores_dict,
    out_stem,
    sequence=None,
    title=None,
    top_k=15,
    dpi=200,
):
    """
    Plot multiple attribution methods side-by-side for the same protein.

    residue_scores_dict : {'AttnPool': array, 'GradCAM': array, 'GradNorm': array, ...}
    """
    methods = list(residue_scores_dict.keys())
    L = len(next(iter(residue_scores_dict.values())))
    seq = list(str(sequence))[:L] if sequence else [str(i) for i in range(L)]

    n_methods = len(methods)
    fig, axes = plt.subplots(n_methods, 1, figsize=(14, 2.5 * n_methods),
                              squeeze=False, constrained_layout=True)
    norm = mcolors.Normalize(vmin=0, vmax=1)

    for mi, method in enumerate(methods):
        ax     = axes[mi, 0]
        scores = np.asarray(residue_scores_dict[method])
        # Show first 100 residues (or all if shorter)
        display_L = min(L, 100)
        seg   = scores[:display_L]
        labs  = seq[:display_L]

        for i, (s, aa) in enumerate(zip(seg, labs)):
            ax.add_patch(plt.Rectangle([i, 0], 1, 1, color=_CMAP(norm(s))))
            text_col = 'white' if s > 0.6 else 'black'
            ax.text(i + 0.5, 0.5, aa, ha='center', va='center',
                    fontsize=5.5, color=text_col)

        ax.set_xlim(0, display_L)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        tick_step = max(1, display_L // 10)
        ax.set_xticks([t + 0.5 for t in range(0, display_L, tick_step)])
        ax.set_xticklabels([str(t) for t in range(0, display_L, tick_step)], fontsize=7)
        ax.set_ylabel(method, fontsize=9, rotation=0, labelpad=50, va='center')

    if title:
        axes[0, 0].set_title(title, fontsize=12, fontweight='bold')
    axes[-1, 0].set_xlabel('Residue Position', fontsize=10)

    sm = plt.cm.ScalarMappable(cmap=_CMAP, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes[:, 0], location='right', shrink=0.5, pad=0.01)
    cbar.set_label('Normalised Score', fontsize=10)

    path = out_stem + '_comparison.png'
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved protein method comparison: {path}")
    return path


def print_top_residue_table(residue_scores, sequence=None, top_k=10, label=''):
    """Print ranked table of highest-scoring residues."""
    scores = np.asarray(residue_scores)
    L = len(scores)
    seq = list(str(sequence))[:L] if sequence else ['?' for _ in range(L)]

    top_idx = np.argsort(scores)[-top_k:][::-1]
    print(f"\n-- Top-{top_k} Residues by Attribution {label} --")
    print(f"{'Rank':<5} {'Pos':<6} {'AA':<5} {'Score':<8}")
    print('-' * 30)
    for rank, i in enumerate(top_idx, 1):
        print(f"{rank:<5} {i:<6} {seq[i]:<5} {scores[i]:.4f}")
    return top_idx.tolist()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    ap = argparse.ArgumentParser(description="Phase 3.2: protein residue heatmap")
    ap.add_argument('--npz',       required=True,  help=".npz from extract_attention.py")
    ap.add_argument('--method',    default='residue_weights',
                    choices=['residue_weights', 'protein_cam', 'ensemble'],
                    help="Score column to visualise")
    ap.add_argument('--sequence',  default=None,   help="Amino acid sequence string")
    ap.add_argument('--out',       default=None)
    ap.add_argument('--title',     default=None)
    args = ap.parse_args()

    data = np.load(args.npz, allow_pickle=True)
    scores = data.get(args.method) if args.method in data else data['residue_weights']
    if scores is None or (hasattr(scores, '__len__') and len(scores) == 1 and scores[0] == -1):
        print("No residue scores found in .npz (mean-pooled protein — need --sequence mode).")
        sys.exit(1)

    out_stem = args.out or args.npz.replace('.npz', '_protein')
    visualize_protein_attribution(
        scores, out_stem=out_stem,
        sequence=args.sequence,
        title=args.title,
        method_label=args.method,
    )
    print_top_residue_table(scores, sequence=args.sequence, top_k=10)
