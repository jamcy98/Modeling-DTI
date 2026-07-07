"""
Generate: Objective 3 Analysis Plan — H-GNN-RNN-DTI
Attention-based interpretability layer: attribution, visualization, and case study validation.
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# ── Page margins ───────────────────────────────────────────────────────────────
sec = doc.sections[0]
sec.top_margin    = Cm(2.5)
sec.bottom_margin = Cm(2.5)
sec.left_margin   = Cm(3.0)
sec.right_margin  = Cm(2.5)

# ── Colour palette ─────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x1F, 0x49, 0x7D)
TEAL   = RGBColor(0x00, 0x70, 0x78)
GREEN  = RGBColor(0x19, 0x76, 0x2E)
ORANGE = RGBColor(0xC5, 0x5A, 0x11)
RED    = RGBColor(0xC0, 0x00, 0x00)
GREY   = RGBColor(0x59, 0x59, 0x59)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)

# ── Helpers ────────────────────────────────────────────────────────────────────

def h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = NAVY
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '1F497D')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p

def h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13)
    run.font.color.rgb = TEAL
    return p

def h3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = NAVY
    return p

def body(text, indent=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(4)
    if indent:
        p.paragraph_format.left_indent = Cm(0.8)
    run = p.add_run(text)
    run.font.size = Pt(11)
    run.font.color.rgb = GREY
    return p

def bullet(text, level=0, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    p.paragraph_format.left_indent  = Cm(0.8 + level * 0.6)
    if bold_prefix:
        r = p.add_run(bold_prefix + "  ")
        r.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = GREY
    run = p.add_run(text)
    run.font.size = Pt(11)
    run.font.color.rgb = GREY
    return p

def todo(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    p.paragraph_format.left_indent  = Cm(0.8)
    r1 = p.add_run("○  ")
    r1.bold = True
    r1.font.color.rgb = ORANGE
    r1.font.size = Pt(11)
    r2 = p.add_run(text)
    r2.font.size = Pt(11)
    r2.font.color.rgb = GREY
    return p

def done(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    p.paragraph_format.left_indent  = Cm(0.8)
    r1 = p.add_run("✓  ")
    r1.bold = True
    r1.font.color.rgb = GREEN
    r1.font.size = Pt(11)
    r2 = p.add_run(text)
    r2.font.size = Pt(11)
    r2.font.color.rgb = GREY
    return p

def callout(text, kind="info"):
    colour = {"info": TEAL, "result": GREEN, "warn": ORANGE, "danger": RED}[kind]
    hex_col = f"{colour[0]:02X}{colour[1]:02X}{colour[2]:02X}"
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.left_indent  = Cm(1.0)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '12')
    left.set(qn('w:space'), '6')
    left.set(qn('w:color'), hex_col)
    pBdr.append(left)
    pPr.append(pBdr)
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.italic = True
    run.font.color.rgb = GREY
    return p

def add_table(headers, rows, col_widths=None):
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = 'Table Grid'
    hdr = tbl.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.paragraphs[0].clear()
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = WHITE
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), '1F497D')
        tcPr.append(shd)
    for ri, row_data in enumerate(rows):
        row = tbl.rows[ri + 1]
        fill = 'F2F7FF' if ri % 2 == 0 else 'FFFFFF'
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            cell.paragraphs[0].clear()
            run = cell.paragraphs[0].add_run(str(val))
            run.font.size = Pt(10)
            run.font.color.rgb = GREY
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear')
            shd.set(qn('w:color'), 'auto')
            shd.set(qn('w:fill'), fill)
            tcPr.append(shd)
    if col_widths:
        for ri, row in enumerate(tbl.rows):
            for ci, cell in enumerate(row.cells):
                cell.width = Inches(col_widths[ci])
    doc.add_paragraph()
    return tbl

def page_break():
    doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ══════════════════════════════════════════════════════════════════════════════

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(40)
run = p.add_run("Objective 3 — Analysis Plan")
run.bold = True
run.font.size = Pt(22)
run.font.color.rgb = NAVY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Attention-Based Interpretability Layer for")
run.font.size = Pt(14)
run.font.color.rgb = TEAL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Drug–Target Interaction Prediction")
run.font.size = Pt(14)
run.font.color.rgb = TEAL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(12)
run = p.add_run("H-GNN-RNN-DTI  |  USM  |  Assoc. Prof. Dr. Nurul Hashimah")
run.font.size = Pt(11)
run.font.color.rgb = GREY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("2026")
run.font.size = Pt(11)
run.font.color.rgb = GREY

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 0 — OBJECTIVE STATEMENT & RESEARCH QUESTION
# ══════════════════════════════════════════════════════════════════════════════

h1("0. Objective Statement and Research Question")

body(
    "Objective 3 — To implement and benchmark an attention-based interpretability layer that "
    "demonstrates the model's ability to generate both quantitative and visual explanations of "
    "DTI/DTA predictions. This will create an actionable tool for guiding structure–activity "
    "relationship (SAR) studies and providing chemically and biologically meaningful rationales "
    "for model decisions."
)

callout(
    "RQ3: Can the attention-enhanced H-GNN-RNN-DTI model generate interpretable, biologically "
    "meaningful insights into drug–target interactions that are consistent with known binding "
    "mechanisms?",
    "info"
)

h2("Scope and Deliverables")

body(
    "This objective has three components mirroring the proposal §3.7: (1) Attention-Based "
    "Attribution — extract and analyse cross-attention weights from the Gated Cross-Attention "
    "module to attribute predictions to individual drug atoms and protein residues; "
    "(2) Visualization — produce heatmaps, molecular highlight plots, and graph-based Grad-CAM "
    "maps; (3) Case Study Validation — compare model-predicted binding hotspots against "
    "experimentally validated binding sites from the Protein Data Bank (PDB)."
)

add_table(
    ["Component", "Proposal Section", "Key Output"],
    [
        ["3.1  Attribution Extraction", "§3.7.1", "Per-atom and per-residue importance scores"],
        ["3.2  Graph Grad-CAM",          "§3.7.1", "Gradient-weighted node importance (drug GNN)"],
        ["3.3  Visualization",           "§3.7.2", "Molecule highlight plots + sequence heatmaps"],
        ["3.4  Quantitative Metrics",    "§3.7 (implied)", "Faithfulness, consistency, specificity scores"],
        ["3.5  Case Study Validation",   "§3.7.3", "PDB-verified binding hotspot overlap report"],
        ["3.6  Reporting",               "Expected Outcome §3", "Interpretability section in paper"],
    ],
    col_widths=[2.0, 1.4, 3.2]
)

h2("Model Configuration")

body(
    "All interpretability experiments run on the C3 configuration (ESM-2 150M + 1:5 ratio + "
    "BindingDB pretraining) — the best overall AUROC model from Objective 2. The best seed "
    "checkpoint from each dataset/split is used for attribution analysis."
)

add_table(
    ["Setting", "Value"],
    [
        ["Embedding", "ESM-2 150M (480-dim → projected to 320 inside model)"],
        ["Negative ratio", "1:5"],
        ["Pretraining", "BindingDB 49,499 pairs (pretrain epoch 42)"],
        ["Primary datasets", "luo_17 (cold_target best), yamanishi_e (all 4 splits)"],
        ["Secondary dataset", "davis (DTA — for affinity regression interpretability)"],
        ["Seeds analysed", "Best seed per split (checkpoint with highest val AUROC)"],
    ],
    col_widths=[2.4, 4.2]
)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — PHASE 1: ATTENTION WEIGHT EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

h1("Phase 1 — Attention Weight Extraction")

body(
    "The Gated Cross-Attention module in model/fusion.py computes bidirectional cross-attention "
    "between drug atom embeddings and protein residue embeddings. This phase instruments the "
    "module to capture and return these attention weight matrices for any drug–target pair."
)

h2("Step 1.1 — Instrument GatedCrossAttention")

callout(
    "File to modify: model/fusion.py — GatedCrossAttention.forward(). "
    "Currently the module discards attention weights after the gating step. "
    "Add a return_weights=False argument; when True, return (output, attn_d2p, attn_p2d).",
    "warn"
)

h3("Implementation Details")
bullet("Drug→Protein attention (attn_d2p): shape (B, N_atoms, L_residues) — each row is a drug atom's attention distribution over protein residues.", 0, "Shape:")
bullet("Protein→Drug attention (attn_p2d): shape (B, L_residues, N_atoms) — each row is a residue's attention over drug atoms.", 0, "Shape:")
bullet("Multi-head attention: average across heads before storing, or store all heads and aggregate downstream.", 0, "Heads:")
bullet("Gating weights (g_d, g_p) from the sigmoid gate also capture cross-modal information flow — optionally store these as secondary attribution signals.", 0, "Gate:")

h3("Code Sketch")
p = doc.add_paragraph()
p.paragraph_format.left_indent = Cm(0.8)
p.paragraph_format.space_before = Pt(4)
run = p.add_run(
    "def forward(self, drug_emb, prot_emb, return_weights=False):\n"
    "    # ... existing cross-attention computation ...\n"
    "    attn_d2p = F.softmax(scores_d2p / math.sqrt(d_k), dim=-1)  # (B, N, L)\n"
    "    attn_p2d = F.softmax(scores_p2d / math.sqrt(d_k), dim=-1)  # (B, L, N)\n"
    "    if return_weights:\n"
    "        return fused_repr, attn_d2p.detach(), attn_p2d.detach()\n"
    "    return fused_repr"
)
run.font.name = 'Courier New'
run.font.size = Pt(9)
run.font.color.rgb = NAVY

h2("Step 1.2 — Inference Attribution Pipeline")

body(
    "Create a new script: interpret/extract_attention.py. This loads a trained checkpoint, "
    "accepts a (drug_smiles, protein_sequence) pair, runs a forward pass with return_weights=True, "
    "and returns atom-level and residue-level raw attention scores."
)

todo("Create interpret/ directory with __init__.py")
todo("Script: interpret/extract_attention.py — load checkpoint, build graph, run inference, return weights")
todo("Output: attention_weights.npz — arrays attn_d2p (N_atoms × L_residues), attn_p2d (L_residues × N_atoms), prediction score")
todo("Support both DTI (binary logit) and DTA (affinity scalar) task heads")

h3("Atom Importance Score (Drug)")
body(
    "Aggregate the drug atom's column in attn_p2d (how much each protein residue attends to each "
    "drug atom) and average over residue positions: atom_importance[i] = mean over j of attn_p2d[j,i]. "
    "Alternatively use max-pooling for sparse attribution. Normalize to [0, 1]."
)

h3("Residue Importance Score (Protein)")
body(
    "Aggregate the protein residue's row in attn_d2p (how much each drug atom attends to each "
    "residue) and average over atom positions: residue_importance[j] = mean over i of attn_d2p[i,j]. "
    "Normalize to [0, 1]."
)

h2("Step 1.3 — Sanity Checks and Validation")

callout(
    "Before running downstream analyses, verify: (a) attention weights are non-uniform (not flat 1/N), "
    "(b) high-confidence correct predictions have higher peak attribution than low-confidence or wrong "
    "predictions, (c) permuting input atoms changes the atom scores (input-sensitivity check).",
    "warn"
)

add_table(
    ["Check", "Method", "Pass Criterion"],
    [
        ["Non-uniformity",  "Compute entropy of attn_d2p rows; compare to max-entropy uniform baseline", "Mean entropy < 0.8 × log(L)"],
        ["Input sensitivity", "Permute atom order; check that atom scores permute consistently",      "Spearman ρ > 0.8 before/after reordering"],
        ["Prediction coherence", "Rank pairs by prediction confidence; compare mean peak attribution", "Higher confidence → higher peak score"],
        ["Gradient consistency", "Compare attention attribution vs. simple gradient norm at input",   "Pearson r > 0.5 on held-out set"],
    ],
    col_widths=[1.5, 3.0, 2.1]
)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — PHASE 2: GRAPH GRAD-CAM
# ══════════════════════════════════════════════════════════════════════════════

h1("Phase 2 — Graph Grad-CAM Implementation")

body(
    "Attention weights reflect the model's routing of information but are not directly tied to "
    "the prediction output. Gradient-weighted Class Activation Mapping (Grad-CAM) addresses this "
    "by computing the gradient of the prediction score w.r.t. the intermediate node embeddings, "
    "giving a saliency measure grounded in the loss landscape."
)

callout(
    "Reference: Grad-CAM for GNNs — GNNExplainer (Ying et al. 2019) and graph-Grad-CAM variants. "
    "Proposal §3.7 explicitly lists 'graph-based variant of Grad-CAM' as the visualization method.",
    "info"
)

h2("Step 2.1 — Drug Graph Grad-CAM")

h3("Algorithm")
bullet("Forward pass through DrugEncoder; capture node embeddings at each GAT layer (register forward hooks on all 3 GAT conv layers).", 0, "1.")
bullet("Compute prediction score (DTI logit or DTA affinity). Backpropagate to obtain gradients at each layer's node embeddings.", 0, "2.")
bullet("Grad-CAM score per node: cam[i] = ReLU( mean_over_channels(grad[i] * activation[i]) ). Use the last GAT layer embeddings.", 0, "3.")
bullet("Normalize to [0,1] across all atoms in the molecule.", 0, "4.")
bullet("Compare with attention-based atom importance: do the two methods agree on which atoms matter?", 0, "5.")

h3("Implementation")
todo("Create interpret/grad_cam.py — register hooks, compute gradients, return per-node scores")
todo("Requires model.eval() but with gradient tracking: use torch.enable_grad() in inference")
todo("Handle batched inference carefully — compute per-sample Grad-CAM, not batch-averaged")

h2("Step 2.2 — Protein Residue Grad-CAM")

body(
    "The ProteinEncoder outputs per-residue embeddings (after BiGRU) before attention pooling. "
    "Compute gradients of the prediction w.r.t. these per-residue hidden states to get residue "
    "saliency scores. This complements the cross-attention residue importance from Phase 1."
)

todo("Hook the BiGRU hidden state output (before attention pooling) in ProteinEncoder")
todo("Compute gradient norm per residue position → residue_saliency[j] = ||grad_h[j]||_2")
todo("Normalize and compare against cross-attention residue_importance[j]")

h2("Step 2.3 — Ensemble Attribution")

body(
    "Combine the two attribution signals for each modality into an ensemble score: "
    "atom_ensemble = alpha * attn_importance + (1-alpha) * gradcam_score, where alpha=0.5 "
    "by default. Report both individual and ensemble scores in the paper."
)

add_table(
    ["Attribution Method", "Drug Atoms", "Protein Residues", "Grounded in Prediction?"],
    [
        ["Cross-attention (Phase 1)", "Yes (attn_p2d column sum)", "Yes (attn_d2p row sum)", "Indirectly"],
        ["Grad-CAM (Phase 2)",        "Yes (GAT layer grad)",      "Yes (BiGRU hidden grad)", "Directly"],
        ["Ensemble (alpha=0.5)",      "Yes",                        "Yes",                    "Combined"],
    ],
    col_widths=[2.2, 1.6, 1.8, 1.6]
)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — PHASE 3: VISUALIZATION MODULE
# ══════════════════════════════════════════════════════════════════════════════

h1("Phase 3 — Visualization Module")

body(
    "Visualizations are the primary output of the interpretability framework — they make "
    "attribution scores communicable to chemists and biologists without domain ML knowledge. "
    "Three plot types are required: (1) molecular atom coloring, (2) protein sequence heatmap, "
    "and (3) cross-attention interaction matrix."
)

h2("Step 3.1 — Drug Molecule Highlight Plot")

body(
    "Use RDKit's drawing utilities to produce a 2D molecular structure diagram where each atom "
    "is colored by its ensemble attribution score. High-importance atoms appear red/orange; "
    "low-importance atoms appear grey/white."
)

h3("Implementation")
todo("Script: interpret/visualize_drug.py")
todo("Use rdkit.Chem.Draw.rdMolDraw2D with atom highlight colors from a matplotlib colormap (e.g., RdYlGn_r)")
todo("Overlay atom importance scores as a continuous color scale; include colorbar in figure")
todo("Save as PNG (300 dpi) and SVG for paper inclusion")
todo("Also produce a table of top-5 atoms by importance: atom index, element, importance score, SMARTS substructure match")

h3("Functional Group Annotation")
body(
    "After ranking atoms by importance, map high-importance clusters to known pharmacophoric "
    "groups (hydrogen bond donors/acceptors, hydrophobic regions, aromatic rings, charged groups) "
    "using RDKit's GetSubstructMatches with SMARTS patterns. Report which pharmacophore types "
    "the model consistently attends to across multiple drug-target pairs."
)

h2("Step 3.2 — Protein Sequence Heatmap")

body(
    "Visualize residue importance as a 1D heatmap aligned to the protein sequence. Annotate "
    "known functional regions (active site, binding pocket) if available from UniProt annotations."
)

h3("Implementation")
todo("Script: interpret/visualize_protein.py")
todo("Plot residue_importance as a bar chart or 1D heatmap using seaborn/matplotlib")
todo("Color scale: white (unimportant) → deep blue (highly important)")
todo("Annotate x-axis with secondary structure elements if available (helix/sheet/loop from PDB DSSP)")
todo("For luo_17 targets, cross-reference UniProt binding site annotations (BioMart / UniProt REST API)")

h2("Step 3.3 — Drug-Protein Cross-Attention Matrix")

body(
    "Visualize the full attn_d2p matrix (N_atoms × L_residues) as a 2D heatmap. This reveals "
    "which drug atoms interact with which protein regions, exposing the learned binding interface."
)

todo("Script: interpret/visualize_cross_attention.py")
todo("Use seaborn.heatmap with atom SMILES labels on y-axis and residue indices on x-axis")
todo("Downsample long sequences (>512 residues) by max-pooling over 5-residue windows")
todo("Highlight rows/columns that exceed 2× mean attention (putative binding contacts)")

h2("Step 3.4 — Batch Visualization Pipeline")

body(
    "For the paper, select 3–5 representative drug-target pairs per dataset and generate "
    "all three plot types for each. Automate via a master script that calls the three "
    "visualize_*.py scripts for each pair."
)

todo("Script: interpret/run_visualization.py — loop over selected pairs, call all three scripts, output to paper/figures/interpretability/")
todo("Pair selection criteria: correct predictions with highest confidence, covering diverse chemical scaffolds")

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — PHASE 4: QUANTITATIVE INTERPRETABILITY METRICS
# ══════════════════════════════════════════════════════════════════════════════

h1("Phase 4 — Quantitative Interpretability Metrics")

body(
    "Qualitative visualizations must be supported by quantitative metrics that can be reported "
    "in a table. Three metric families are proposed: faithfulness (does masking important atoms "
    "hurt the prediction?), consistency (do the same atoms/residues get high scores across seeds?), "
    "and specificity (are the attributed features chemically/biologically meaningful?)."
)

h2("Step 4.1 — Faithfulness: Atom Masking Experiment")

body(
    "Mask the top-K% highest-importance atoms in the drug graph by zeroing their node features. "
    "Measure the drop in prediction confidence. If the attribution is faithful, masking important "
    "atoms should cause a larger drop than masking random atoms."
)

h3("Protocol")
add_table(
    ["K%", "Expected Outcome (faithful model)"],
    [
        ["Top 10% atoms masked", "Prediction confidence drops by >20% on average"],
        ["Top 25% atoms masked", "Prediction confidence drops by >40% on average"],
        ["Random 10% atoms masked (control)", "Smaller drop than Top 10%"],
        ["Random 25% atoms masked (control)", "Smaller drop than Top 25%"],
    ],
    col_widths=[2.5, 4.5]
)
callout(
    "Metric: Faithfulness Score = AUC of the confidence-drop vs. K% curve. "
    "Higher score = more faithful attribution. Report for both attention and Grad-CAM methods.",
    "info"
)
todo("Script: interpret/faithfulness.py — systematic masking experiment over 100 drug-target pairs per dataset")
todo("Report mean ± std of faithfulness score for each attribution method (attention, Grad-CAM, ensemble)")

h2("Step 4.2 — Consistency: Cross-Seed Agreement")

body(
    "For each drug-target pair, run attribution extraction using checkpoints from all 5 seeds. "
    "Compute Spearman rank correlation between the atom importance vectors from different seeds. "
    "High consistency = the attribution is a stable model property, not a training-run artifact."
)

todo("Run extract_attention.py for all 5 seeds on 20 representative pairs per split")
todo("Compute pairwise Spearman ρ between seed pairs → report mean ± std for each dataset/split")
todo("Flag pairs where consistency < 0.5 as potentially unreliable")

h2("Step 4.3 — Specificity: Pharmacophore Alignment Score")

body(
    "Quantify whether high-importance atoms correspond to known pharmacophoric features. "
    "Use RDKit's pharmacophore detection (GetPharmacophoreDescriptors or SMARTS matching) to "
    "label each atom as pharmacophoric or not. Compute precision@K: of the top-K atoms by "
    "importance, what fraction are pharmacophoric?"
)

add_table(
    ["Metric", "Description", "Target Value"],
    [
        ["Pharmacophore Precision@5", "% of top-5 atoms matching known pharmacophores", "> 60%"],
        ["Binding Pocket Recall",     "% of known binding-pocket residues in top-25% residue scores", "> 50%"],
        ["Consistency ρ (cross-seed)", "Mean Spearman ρ between seed pairs", "> 0.7"],
        ["Faithfulness AUC",          "AUC of confidence-drop vs. K% curve", "> 0.6"],
    ],
    col_widths=[2.2, 3.3, 1.6]
)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — PHASE 5: CASE STUDY VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

h1("Phase 5 — Case Study Validation")

body(
    "The proposal §3.7.3 requires validating predicted binding hotspots against experimentally "
    "validated binding sites from crystal structures in the PDB. This phase selects well-characterised "
    "drug-target pairs, retrieves PDB structures, annotates binding sites, and computes overlap "
    "between model attribution and experimental binding residues."
)

h2("Step 5.1 — Case Study Pair Selection")

h3("Selection Criteria")
bullet("The drug-target pair must be present in luo_17 or yamanishi_e (or davis for DTA).", 0)
bullet("The model must predict the pair correctly (true positive) with high confidence (top 10% by predicted probability).", 0)
bullet("A PDB crystal structure of the complex must exist (drug bound to target protein).", 0)
bullet("The pair should cover diverse chemical scaffolds — aim for at least one kinase inhibitor, one GPCR ligand, and one enzyme inhibitor.", 0)

h3("Candidate Pairs from luo_17 (DrugBank dataset)")
body(
    "luo_17 uses DrugBank IDs and UniProt targets. Query PDB for co-crystal structures using "
    "the PDB REST API (search by UniProt accession + small molecule ligand). "
    "Target 5–8 pairs total across both datasets."
)
todo("Script: interpret/select_case_studies.py — query PDB REST API, filter by model confidence, output candidate list")
todo("Manual review: confirm ligand in crystal matches the drug SMILES in dataset")

add_table(
    ["Dataset", "Target Type", "Example Pairs (illustrative)"],
    [
        ["luo_17",       "Kinase (DrugBank)",   "Imatinib/ABL1, Erlotinib/EGFR — confirmed co-crystals in PDB"],
        ["luo_17",       "GPCR (DrugBank)",     "Risperidone/DRD2 or similar — check PDB 6CM4 etc."],
        ["yamanishi_e",  "Enzyme (Enzymes subset)", "Acetaminophen/COX-1 analog — verify SMILES match"],
        ["davis",        "Kinase (DTA)",        "Staurosporine/PKCα — broad-spectrum binding for affinity case"],
    ],
    col_widths=[1.4, 2.0, 3.6]
)

h2("Step 5.2 — PDB Binding Site Annotation")

body(
    "For each selected pair, extract the binding site residues from the PDB structure: "
    "residues within 4 Å of any ligand heavy atom. This gives the ground-truth set of binding residues."
)

todo("Use Biopython (Bio.PDB) to parse PDB structure and extract residues within 4 Å of ligand")
todo("Map PDB residue indices to protein sequence indices (handle insertions/deletions via sequence alignment)")
todo("Store as: binding_residues = {uniprot_id: set(residue_indices)} for each case study target")

h2("Step 5.3 — Quantitative Overlap Evaluation")

body(
    "Compare the model's top-K% residues by importance score against the PDB binding residues. "
    "Compute precision, recall, and F1 at multiple K thresholds."
)

add_table(
    ["Metric", "Formula", "Interpretation"],
    [
        ["Precision@K%", "TP / (TP + FP) where TP = top-K% ∩ binding residues", "Are high-importance residues in the binding site?"],
        ["Recall@K%",    "TP / |binding residues|",                               "What fraction of binding residues are captured?"],
        ["F1@K%",        "2 × P × R / (P + R)",                                  "Balance between precision and recall"],
        ["AUROC (residue)", "ROC curve treating binding residue as positive class", "Overall discriminative power of attribution"],
    ],
    col_widths=[1.6, 2.8, 2.7]
)

callout(
    "Report results at K=10%, K=25%, K=50% and the full AUROC. "
    "Target: mean Precision@25% > 0.5 and Recall@50% > 0.6 across case studies.",
    "info"
)

todo("Script: interpret/evaluate_case_studies.py — compute all metrics for each pair, save to paper/case_study_results.csv")
todo("Statistical test: is the model attribution significantly better than random at each K threshold (paired t-test vs. uniform baseline)?")

h2("Step 5.4 — Qualitative Write-up")

body(
    "For each case study pair, write a 1–2 paragraph analysis including: "
    "(a) the predicted interaction class/affinity, (b) the top-5 drug atoms and their functional group identity, "
    "(c) the top-10 protein residues and whether they match the PDB binding site, "
    "(d) comparison against the crystal structure image (if publishable). "
    "These form the qualitative component of Section 3.7.3 in the paper."
)

todo("Prepare 3–5 case study write-ups for the interpretability section of the thesis/paper")
todo("Include: molecular structure with atom highlighting, sequence heatmap, overlap summary table")

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — PHASE 6: COMPARISON WITH EXISTING INTERPRETABILITY METHODS
# ══════════════════════════════════════════════════════════════════════════════

h1("Phase 6 — Benchmarking Against Baseline Interpretability Methods")

body(
    "To demonstrate that the cross-attention attribution provides genuine insight (not just a "
    "plausible-looking map), compare it against two standard baselines: (1) random attribution "
    "(lower bound) and (2) integrated gradients at the input feature level."
)

h2("Step 6.1 — Random Attribution Baseline")

body(
    "Assign uniform random importance scores to atoms and residues. Use 100 random seeds per "
    "pair. This sets the floor for all quantitative metrics."
)

h2("Step 6.2 — Input Gradient Baseline")

body(
    "Compute the gradient of the prediction w.r.t. the raw input atom features (before the GAT). "
    "The L2 norm of the gradient at each atom position gives a naive saliency score. "
    "This is a model-agnostic baseline that requires no architectural modification."
)

todo("Implement in interpret/input_gradient.py — requires autograd at raw input node features (no hooks needed)")

h2("Step 6.3 — Comparison Table")

add_table(
    ["Method", "Requires Architecture Change?", "Grounded in Prediction?", "Expected Precision@25%"],
    [
        ["Random (baseline)",        "No",  "No",  "~25% (chance)"],
        ["Input gradient",           "No",  "Yes", "30–40% (target)"],
        ["Cross-attention (Phase 1)","Yes", "Indirectly", "40–55% (target)"],
        ["Grad-CAM (Phase 2)",       "Yes", "Yes", "45–60% (target)"],
        ["Ensemble (Phase 2.3)",     "Yes", "Yes", "50–65% (target)"],
    ],
    col_widths=[2.2, 1.9, 1.7, 1.8]
)

callout(
    "If ensemble Precision@25% is < 40%, investigate whether the attribution is model-meaningful "
    "or whether the GCA module's attention weights are not strongly informative (flat attention "
    "over long protein sequences is a known failure mode).",
    "danger"
)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — PHASE 7: REPORTING AND PAPER SECTION
# ══════════════════════════════════════════════════════════════════════════════

h1("Phase 7 — Reporting: Paper Section 3.7 and Evaluation Report")

body(
    "All results feed into the paper's interpretability section and into evaluation_report.md "
    "Section 3.11 (new section for Objective 3). The goal is a self-contained, reproducible "
    "interpretability analysis that can stand alongside the predictive performance results."
)

h2("Step 7.1 — Evaluation Report Section 3.11")

h3("Subsections to Write")
bullet("3.11.1  Attribution Extraction — describe the cross-attention weight extraction pipeline", 0)
bullet("3.11.2  Graph Grad-CAM — describe the GNN Grad-CAM implementation", 0)
bullet("3.11.3  Visualization Gallery — 2–3 key figures (molecule highlight, sequence heatmap, cross-attention matrix)", 0)
bullet("3.11.4  Quantitative Metrics — faithfulness, consistency, pharmacophore precision tables", 0)
bullet("3.11.5  Case Study Validation — 3–5 pair analyses with PDB comparison", 0)
bullet("3.11.6  Baseline Comparison — attribution methods ranked by precision@K", 0)

h2("Step 7.2 — Summary Tables for Paper")

add_table(
    ["Table", "Content", "Location"],
    [
        ["Table 21", "Quantitative interpretability metrics (all attribution methods, both datasets)", "Section 3.11.4"],
        ["Table 22", "Case study binding site overlap results (precision/recall/F1 per pair)", "Section 3.11.5"],
        ["Table 23", "Attribution method comparison (vs. random and input gradient baselines)", "Section 3.11.6"],
    ],
    col_widths=[1.2, 4.0, 1.6]
)

h2("Step 7.3 — Figures for Paper")

add_table(
    ["Figure", "Description"],
    [
        ["Fig. 3.X",  "Example drug molecule with atom importance coloring (luo_17 case study)"],
        ["Fig. 3.X+1","Protein sequence heatmap for the same pair — known binding residues annotated"],
        ["Fig. 3.X+2","Cross-attention matrix (drug atoms × protein residues) — binding interface heatmap"],
        ["Fig. 3.X+3","PDB crystal structure overlaid with top-10 model-predicted binding residues"],
        ["Fig. 3.X+4","Faithfulness curve: prediction confidence vs. % atoms masked (all methods)"],
    ],
    col_widths=[1.4, 5.2]
)

h2("Step 7.4 — Commit and Version Control")

todo("Commit all interpret/ scripts and paper/figures/interpretability/ after each phase")
todo("Tag the commit with 'obj3-phaseN-complete' for traceability")
todo("Update evaluation_report.md Section 3.11 incrementally as each phase completes")

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — EXECUTION TIMELINE AND DEPENDENCIES
# ══════════════════════════════════════════════════════════════════════════════

h1("Execution Timeline and Dependencies")

body(
    "The phases are largely sequential: Phase 1 (extraction) must complete before Phases 2–6. "
    "Visualization (Phase 3) and Quantitative Metrics (Phase 4) can run in parallel once "
    "attribution scores exist. Case Study Validation (Phase 5) has an external dependency on "
    "PDB structure retrieval."
)

add_table(
    ["Phase", "Prerequisite", "Est. Duration", "Key Risk"],
    [
        ["Phase 1 — Extraction",      "C3 checkpoints (done)",       "1–2 days",  "GCA module may not store weights; requires refactoring"],
        ["Phase 2 — Grad-CAM",        "Phase 1 complete",            "1–2 days",  "Memory: per-sample gradient computation on long proteins"],
        ["Phase 3 — Visualization",   "Phase 1 or 2 complete",       "1–2 days",  "RDKit version compatibility; SVG export quality"],
        ["Phase 4 — Quant. Metrics",  "Phase 1 + 2 complete",        "2–3 days",  "Masking experiment is slow (100 pairs × 5 K-values × forward pass)"],
        ["Phase 5 — Case Studies",    "Phase 3 + PDB retrieval",     "3–4 days",  "PDB API rate limits; sequence alignment errors"],
        ["Phase 6 — Baselines",       "Phase 1 complete",            "1 day",     "Input gradient baseline may have very different scale"],
        ["Phase 7 — Reporting",       "Phases 3–6 complete",         "2–3 days",  "Figure quality for publication (DPI, font sizes)"],
    ],
    col_widths=[2.2, 2.0, 1.3, 2.1]
)

callout(
    "Critical path: Phase 1 → Phase 2 → Phase 4 → Phase 5 → Phase 7. "
    "Total estimated duration: 11–17 working days assuming GPU access for forward passes.",
    "warn"
)

h2("Dependencies and Tools")

add_table(
    ["Tool / Library", "Purpose", "Already Installed?"],
    [
        ["torch.autograd",        "Gradient computation for Grad-CAM",             "Yes (PyTorch)"],
        ["rdkit.Chem.Draw",       "2D molecular visualization with atom colors",    "Yes (RDKit)"],
        ["seaborn / matplotlib",  "Sequence heatmaps and cross-attention matrix",   "Yes"],
        ["Bio.PDB (Biopython)",   "PDB structure parsing and binding site extraction", "Check: pip install biopython"],
        ["requests / PDB REST",   "PDB structure and annotation retrieval",         "Check: pip install requests"],
        ["scipy.stats",           "Spearman correlation, paired t-tests",           "Yes (scipy)"],
    ],
    col_widths=[2.0, 3.0, 1.6]
)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — EXPECTED OUTCOMES AND SUCCESS CRITERIA
# ══════════════════════════════════════════════════════════════════════════════

h1("Expected Outcomes and Success Criteria")

body(
    "Objective 3 is complete when all three components of the proposal §3.7 are delivered: "
    "attribution extraction (§3.7.1), visualization (§3.7.2), and case study validation (§3.7.3)."
)

h2("Minimum Viable Outcome")

done("GatedCrossAttention instrumented to return attention weights without degrading prediction performance")
done("Per-atom and per-residue importance scores computed for all selected case study pairs")
done("At least 3 drug molecule highlight plots and 3 protein sequence heatmaps generated")
done("Quantitative faithfulness and consistency metrics computed and reported")
done("At least 3 case study pairs validated against PDB binding sites (Precision@25% > 40%)")
done("Evaluation report Section 3.11 fully written with all tables and figures")

h2("Stretch Goals")

todo("Extend case studies to DAVIS DTA dataset — map affinity-weighted attention to binding free energy contributions")
todo("3D protein structure visualization: project residue importance onto PDB RCSB 3D viewer (PyMOL script or NGL Viewer)")
todo("Interactive HTML report: plotly-based interactive cross-attention matrix + molecule viewer")
todo("Comparison with NHGNN-DTA (He et al. 2023) and MutualDTA (Yuan et al. 2025) — two published interpretable DTI models")

h2("Failure Modes and Contingencies")

add_table(
    ["Risk", "Likelihood", "Contingency"],
    [
        ["Cross-attention is too flat (uniform over residues)",
         "Medium — long proteins dilute attention",
         "Switch to Grad-CAM as primary attribution; report attention as secondary"],
        ["PDB structures not available for dataset pairs",
         "Low–Medium — luo_17 is DrugBank-based",
         "Use AlphaFold2 structures + predicted binding pockets from FPocket"],
        ["Interpretation metrics low (Precision@25% < 35%)",
         "Low — model has strong AUROC so representations are meaningful",
         "Report negative result transparently; analyse why (attention vs. gradient divergence)"],
        ["GPU memory issues with per-sample Grad-CAM",
         "Medium — long protein sequences",
         "Process single samples (batch_size=1), or truncate proteins at 512 residues"],
    ],
    col_widths=[2.4, 1.4, 3.3]
)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — FILE STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════

h1("Proposed File Structure")

p = doc.add_paragraph()
p.paragraph_format.left_indent = Cm(0.8)
p.paragraph_format.space_before = Pt(4)
run = p.add_run(
    "Modeling-DTI/\n"
    "├── interpret/\n"
    "│   ├── __init__.py\n"
    "│   ├── extract_attention.py      # Phase 1: attention weight extraction\n"
    "│   ├── grad_cam.py               # Phase 2: graph Grad-CAM\n"
    "│   ├── visualize_drug.py         # Phase 3: atom coloring\n"
    "│   ├── visualize_protein.py      # Phase 3: residue heatmap\n"
    "│   ├── visualize_cross_attention.py  # Phase 3: interaction matrix\n"
    "│   ├── run_visualization.py      # Phase 3: batch pipeline\n"
    "│   ├── faithfulness.py           # Phase 4: masking experiment\n"
    "│   ├── consistency.py            # Phase 4: cross-seed agreement\n"
    "│   ├── pharmacophore_precision.py # Phase 4: specificity\n"
    "│   ├── select_case_studies.py    # Phase 5: pair selection\n"
    "│   ├── retrieve_pdb.py           # Phase 5: PDB download + binding site\n"
    "│   ├── evaluate_case_studies.py  # Phase 5: overlap metrics\n"
    "│   └── input_gradient.py         # Phase 6: baseline\n"
    "├── paper/\n"
    "│   ├── figures/\n"
    "│   │   └── interpretability/     # All plots from Phase 3\n"
    "│   ├── case_study_results.csv    # Phase 5 output\n"
    "│   └── evaluation_report.md      # Section 3.11 added here\n"
    "└── model/\n"
    "    └── fusion.py                 # Modified: return_weights argument"
)
run.font.name = 'Courier New'
run.font.size = Pt(9)
run.font.color.rgb = NAVY

body(
    "All scripts under interpret/ are standalone — they import from model/ and data/ but do not "
    "modify training code. The model/fusion.py change is backward-compatible (default return_weights=False)."
)

h2("Summary of Objective 3 vs. Proposal Mapping")

add_table(
    ["Proposal §3.7 Element", "This Plan", "Phase"],
    [
        ["Attention-Based Attribution — cross-attention weights quantify atom/residue contribution",
         "Phase 1: extract_attention.py — attn_d2p, attn_p2d → importance scores",
         "1"],
        ["Graph-based Grad-CAM for molecular substructures",
         "Phase 2: grad_cam.py — GAT layer hooks + gradient × activation",
         "2"],
        ["Heatmaps and saliency maps overlaid on molecular graphs / protein sequences",
         "Phase 3: visualize_drug.py, visualize_protein.py, visualize_cross_attention.py",
         "3"],
        ["Quantitative attribution metrics (faithfulness, consistency, specificity)",
         "Phase 4: faithfulness.py, consistency.py, pharmacophore_precision.py",
         "4"],
        ["Case study validation against PDB crystal structures",
         "Phase 5: select_case_studies.py → retrieve_pdb.py → evaluate_case_studies.py",
         "5"],
        ["Baseline comparison to establish attribution quality",
         "Phase 6: input_gradient.py vs. attention vs. Grad-CAM",
         "6"],
        ["Paper section on interpretability findings",
         "Phase 7: evaluation_report.md Section 3.11 + figures",
         "7"],
    ],
    col_widths=[2.7, 3.0, 0.5]
)

callout(
    "Objective 3 is the final research objective. On completion, all three research questions "
    "(RQ1: fusion architecture, RQ2: cold-start representation, RQ3: interpretability) will have "
    "been fully addressed and reported.",
    "result"
)

# ══════════════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════════════

out_path = r"paper\Objective3_Analysis_Plan.docx"
doc.save(out_path)
print(f"Saved: {out_path}")
