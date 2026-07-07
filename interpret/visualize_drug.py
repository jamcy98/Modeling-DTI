"""
Phase 3.1 — Drug Molecule Highlight Plot

Draws a 2D molecular structure where each atom is colored by its attribution
score (Phase 1 input-gradient, Phase 2 Grad-CAM, or ensemble).

Output: PNG (300 dpi, molecule + colorbar) and SVG (vector).

Usage:
    from interpret.visualize_drug import visualize_drug_attribution, top_atom_table
    from rdkit import Chem

    mol = Chem.MolFromSmiles("CC1=CC=C(C=C1)NC(=O)C")
    scores = [0.1, 0.8, 0.3, ...]     # one per atom
    visualize_drug_attribution(mol, scores, out_stem="paper/figures/interpretability/drug_DB00619")
"""

import os
import io
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from PIL import Image

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D


# ── Color map ──────────────────────────────────────────────────────────────────
# Low importance → cool blue, high importance → warm red  (diverging, intuitive)
_CMAP = cm.get_cmap('coolwarm')


def _score_to_rgb(score, cmap=_CMAP):
    """Map scalar in [0,1] to (R, G, B) tuple expected by RDKit DrawMolecule."""
    r, g, b, _ = cmap(float(np.clip(score, 0, 1)))
    return (r, g, b)


# ── Core drawing function ──────────────────────────────────────────────────────

def draw_molecule_png(mol, atom_scores, width=600, height=400):
    """
    Render molecule to PNG bytes using RDKit Cairo renderer.

    atom_scores : array-like of length mol.GetNumAtoms(), values in [0,1]
    Returns     : bytes (PNG)
    """
    n = mol.GetNumAtoms()
    scores = np.asarray(atom_scores, dtype=float)
    assert len(scores) == n, f"atom_scores length {len(scores)} != {n} atoms"

    atom_colors  = {i: _score_to_rgb(scores[i]) for i in range(n)}
    atom_radii   = {i: 0.35 for i in range(n)}
    highlight    = list(range(n))

    drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
    opts = drawer.drawOptions()
    opts.addStereoAnnotation = False
    opts.addAtomIndices       = False
    rdMolDraw2D.PrepareMolForDrawing(mol)
    drawer.DrawMolecule(
        mol,
        highlightAtoms=highlight,
        highlightAtomColors=atom_colors,
        highlightAtomRadii=atom_radii,
    )
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def draw_molecule_svg(mol, atom_scores, width=600, height=400):
    """Render molecule to SVG string."""
    n = mol.GetNumAtoms()
    scores = np.asarray(atom_scores, dtype=float)
    atom_colors = {i: _score_to_rgb(scores[i]) for i in range(n)}
    atom_radii  = {i: 0.35 for i in range(n)}

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.addStereoAnnotation = False
    rdMolDraw2D.PrepareMolForDrawing(mol)
    drawer.DrawMolecule(
        mol,
        highlightAtoms=list(range(n)),
        highlightAtomColors=atom_colors,
        highlightAtomRadii=atom_radii,
    )
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


# ── Composite PNG (molecule + colorbar) ────────────────────────────────────────

def visualize_drug_attribution(
    mol_or_smiles,
    atom_scores,
    out_stem,
    title=None,
    method_label="Ensemble",
    save_svg=True,
    dpi=300,
):
    """
    Generate drug attribution figures.

    Args:
        mol_or_smiles : RDKit Mol object or SMILES string
        atom_scores   : array-like (N_atoms,), normalised [0,1]
        out_stem      : output path without extension (e.g. 'paper/figures/interpretability/drug_DB00619')
        title         : figure title (drug name / ID)
        method_label  : label for colorbar ('Ensemble', 'GradCAM', 'InputGrad')
        save_svg      : also save SVG alongside PNG
        dpi           : PNG resolution

    Saves:
        {out_stem}.png  — composite figure with molecule + colorbar
        {out_stem}.svg  — vector version (if save_svg=True)
    Returns:
        dict with 'top5_atoms' (indices of 5 most important atoms)
    """
    if isinstance(mol_or_smiles, str):
        mol = Chem.MolFromSmiles(mol_or_smiles)
        if mol is None:
            raise ValueError(f"Cannot parse SMILES: {mol_or_smiles!r}")
    else:
        mol = mol_or_smiles

    scores = np.asarray(atom_scores, dtype=float)
    n      = mol.GetNumAtoms()
    assert len(scores) == n

    os.makedirs(os.path.dirname(os.path.abspath(out_stem)) or '.', exist_ok=True)

    # ── Molecule PNG via RDKit Cairo ──────────────────────────────────────────
    png_bytes = draw_molecule_png(mol, scores)
    mol_img   = Image.open(io.BytesIO(png_bytes))

    # ── Composite figure ──────────────────────────────────────────────────────
    fig = plt.figure(figsize=(10, 5))
    gs  = fig.add_gridspec(1, 2, width_ratios=[8, 0.4], wspace=0.05)
    ax_mol = fig.add_subplot(gs[0])
    ax_cb  = fig.add_subplot(gs[1])

    ax_mol.imshow(mol_img)
    ax_mol.axis('off')
    if title:
        ax_mol.set_title(title, fontsize=13, fontweight='bold', pad=8)

    # Colorbar
    norm = mcolors.Normalize(vmin=0, vmax=1)
    sm   = plt.cm.ScalarMappable(cmap=_CMAP, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=ax_cb)
    cbar.set_label(f'{method_label} Score', fontsize=10)
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.ax.tick_params(labelsize=8)

    png_path = out_stem + '.png'
    fig.savefig(png_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved drug PNG: {png_path}")

    # ── SVG ──────────────────────────────────────────────────────────────────
    if save_svg:
        svg_path = out_stem + '.svg'
        svg_text = draw_molecule_svg(mol, scores)
        with open(svg_path, 'w') as f:
            f.write(svg_text)
        print(f"  Saved drug SVG: {svg_path}")

    # ── Atom importance bar (supplementary) ───────────────────────────────────
    _save_atom_bar(mol, scores, out_stem + '_bar.png', title=title,
                   method_label=method_label, dpi=dpi)

    top5 = np.argsort(scores)[-5:][::-1].tolist()
    return {'top5_atoms': top5, 'scores': scores}


def _save_atom_bar(mol, scores, path, title=None, method_label='Score', dpi=200):
    """Horizontal bar chart of per-atom importance scores."""
    n      = mol.GetNumAtoms()
    labels = [f"{a.GetSymbol()}{i}" for i, a in enumerate(mol.GetAtoms())]
    order  = np.argsort(scores)  # ascending for horizontal bar (lowest at bottom)
    sorted_scores = scores[order]
    sorted_labels = [labels[i] for i in order]
    colors = [_score_to_rgb(s) for s in sorted_scores]

    fig_h = max(3, 0.28 * n)
    fig, ax = plt.subplots(figsize=(6, fig_h))
    bars = ax.barh(sorted_labels, sorted_scores, color=colors, edgecolor='grey', linewidth=0.4)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel(f'{method_label} (normalised)', fontsize=10)
    ax.set_ylabel('Atom', fontsize=10)
    if title:
        ax.set_title(f'{title} — Atom Attribution', fontsize=11, fontweight='bold')
    ax.tick_params(labelsize=8)
    plt.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)


# ── Pharmacophore annotation ──────────────────────────────────────────────────

def top_atom_table(mol, atom_scores, top_k=5):
    """
    Return a table of top-k atoms with element, score, and pharmacophore class.

    Pharmacophore classes (simple SMARTS matching):
        HBD  — hydrogen bond donor  [NH,OH]
        HBA  — hydrogen bond acceptor  [N,O,F]
        Arom — aromatic ring atom
        Hydro — hydrophobic (C,S in ring or aliphatic)
        Charged — formal charge != 0
    """
    from rdkit.Chem import AllChem

    PHARM_SMARTS = {
        'HBD':    Chem.MolFromSmarts('[#7H,#8H]'),
        'HBA':    Chem.MolFromSmarts('[#7,#8,#9]'),
        'Arom':   Chem.MolFromSmarts('[a]'),
        'Hydro':  Chem.MolFromSmarts('[c,s,C,S;!$([#7,#8,#9])]'),
    }

    def atom_pharma(atom):
        classes = []
        if atom.GetFormalCharge() != 0:
            classes.append('Charged')
        idx = atom.GetIdx()
        for name, patt in PHARM_SMARTS.items():
            if patt is None:
                continue
            matches = mol.GetSubstructMatches(patt)
            if any(idx in m for m in matches):
                classes.append(name)
        return ','.join(classes) if classes else 'Other'

    scores = np.asarray(atom_scores)
    top_idx = np.argsort(scores)[-top_k:][::-1]
    rows = []
    for rank, i in enumerate(top_idx, 1):
        a = mol.GetAtomWithIdx(int(i))
        rows.append({
            'Rank':   rank,
            'Atom':   f"{a.GetSymbol()}{i}",
            'Index':  i,
            'Score':  f"{scores[i]:.4f}",
            'Pharma': atom_pharma(a),
        })
    return rows


def print_top_atom_table(mol, atom_scores, top_k=5, label=''):
    rows = top_atom_table(mol, atom_scores, top_k)
    header = f"\n-- Top-{top_k} Atoms by Attribution {label} --"
    print(header)
    print(f"{'Rank':<5} {'Atom':<8} {'Score':<8} {'Pharmacophore'}")
    print('-' * 40)
    for r in rows:
        print(f"{r['Rank']:<5} {r['Atom']:<8} {r['Score']:<8} {r['Pharma']}")
    return rows


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    ap = argparse.ArgumentParser(description="Phase 3.1: drug molecule attribution plot")
    ap.add_argument('--npz',    required=True,  help="Attribution .npz from extract_attention.py")
    ap.add_argument('--smiles', required=True,  help="Drug SMILES string")
    ap.add_argument('--method', default='ensemble',
                    choices=['atom_importance', 'drug_cam', 'ensemble'],
                    help="Which score column to visualise")
    ap.add_argument('--out',    default=None,   help="Output stem (no extension)")
    ap.add_argument('--title',  default=None)
    args = ap.parse_args()

    data = np.load(args.npz, allow_pickle=True)
    mol  = Chem.MolFromSmiles(args.smiles)

    if args.method == 'ensemble' and 'drug_cam' in data and 'atom_importance' in data:
        from interpret.grad_cam import ensemble_attribution
        scores = ensemble_attribution(data['atom_importance'], data['drug_cam'])
        label  = 'Ensemble'
    elif args.method in data:
        scores = data[args.method]
        label  = args.method
    else:
        scores = data['atom_importance']
        label  = 'InputGrad'

    out_stem = args.out or args.npz.replace('.npz', '_drug')
    visualize_drug_attribution(mol, scores, out_stem=out_stem,
                                title=args.title, method_label=label)
    print_top_atom_table(mol, scores, top_k=5)
