"""
Generate: Objective 2 Analysis Plan — H-GNN-RNN-DTI
Robust representation learning, pretraining strategy, and imbalance-aware learning
to improve cold-start generalisation.
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

def gap(text):
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

def callout(text, kind="info"):
    colour = {"info": TEAL, "result": GREEN, "warn": ORANGE}[kind]
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
run = p.add_run("Objective 2 — Analysis Plan")
run.bold = True
run.font.size = Pt(22)
run.font.color.rgb = NAVY

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Robust Representation Learning, Pretraining Strategy,")
run.font.size = Pt(14)
run.font.color.rgb = TEAL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("and Imbalance-Aware Learning for Cold-Start Generalisation")
run.font.size = Pt(14)
run.font.color.rgb = TEAL

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run(
    "H-GNN-RNN-DTI Research Project\n"
    "Universiti Sains Malaysia  |  School of Computer Sciences\n"
    "Supervisor: Assoc. Prof. Dr. Nurul Hashimah\n"
    "Prepared: July 2026"
)
run.font.size = Pt(11)
run.font.color.rgb = GREY

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 0. DOCUMENT OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

h1("Document Overview")

body(
    "This document is the step-by-step analysis plan for Objective 2 of the "
    "H-GNN-RNN-DTI research project. It specifies what experiments to run, why each "
    "experiment is necessary, what results are expected, and how the evidence will be "
    "analysed. The plan builds directly on the completed Objective 1 experiments — "
    "which established the H-GNN-RNN-DTI baseline — and addresses the remaining "
    "research questions about cold-start generalisation, pretraining, and imbalance-aware "
    "learning."
)

body(
    "The document is structured in five experimental phases, each corresponding to one "
    "research sub-question of Objective 2. Each phase describes the exact experiments to "
    "run, the datasets and splits to use, the metrics to report, and the statistical tests "
    "to apply. Phases can be executed in order or partially in parallel once Phase 1 is "
    "complete."
)

callout(
    "How to read this document:  ✓ marks completed tasks (inherited from Objective 1).  "
    "○ marks items that must still be run for Objective 2.",
    kind="info"
)

# ══════════════════════════════════════════════════════════════════════════════
# 1. WHAT IS OBJECTIVE 2?
# ══════════════════════════════════════════════════════════════════════════════

h1("1.  What is Objective 2?")

body(
    "Objective 2 from the research proposal states:"
)

callout(
    '"To develop a robust representation learning and pretraining strategy that integrates '
    'imbalance-aware learning and foundation-model-based embeddings, with the aim of '
    'significantly enhancing predictive performance on unseen drugs, unseen targets, and '
    'cross-dataset conditions, thereby mitigating the cold-start generalisation problem."',
    kind="info"
)

body(
    "In plain terms, Objective 2 asks three related questions:"
)

bullet(
    "Which foundation model embedding gives the best protein and drug representations? "
    "The current model uses ESM-2 (8M or 650M parameters) for proteins and ChemBERTa "
    "for drugs. Are there better choices — for example, ProtT5 for proteins or MoLFormer "
    "for drugs — and does the choice matter more on cold-start splits?",
    bold_prefix="Q1."
)
bullet(
    "Which imbalance-aware training strategy produces the most reliable predictions "
    "when positive interactions are far outnumbered by negatives? The current model uses "
    "Focal Loss at a 1:1 sampling ratio. Do different loss functions or sampling ratios "
    "improve AUPRC on hard cold splits?",
    bold_prefix="Q2."
)
bullet(
    "Can self-supervised pretraining on a large unlabelled dataset (BindingDB, ChEMBL, "
    "DrugBank) be used to initialise the drug and protein encoders so that fine-tuning "
    "on smaller target datasets (Davis, KIBA, Yamanishi_e, Luo_17) gives better cold-start "
    "performance and meaningful cross-dataset transfer?",
    bold_prefix="Q3."
)

body(
    "Objective 1 established that the H-GNN-RNN-DTI architecture outperforms simple "
    "concatenation on small datasets and has competitive performance on large ones. "
    "However, the cross-dataset transfer experiment (luo_17 → yamanishi_e) gave "
    "near-random performance (AUROC 0.508 ± 0.020), confirming that the model does not "
    "generalise to unseen molecular distributions without additional strategies. "
    "Objective 2 exists to provide those strategies."
)

callout(
    "Objective 2 does not change the model architecture. It changes how the model is "
    "initialised (pretraining), what embeddings it receives (foundation models), "
    "and how imbalanced training data is handled (loss function and sampling). "
    "The Gated Cross-Attention core remains fixed.",
    kind="info"
)

# ══════════════════════════════════════════════════════════════════════════════
# 2. STARTING POINT — WHAT OBJECTIVE 1 GAVE US
# ══════════════════════════════════════════════════════════════════════════════

h1("2.  Starting Point — Objective 1 Baseline")

body(
    "Before planning new experiments, it is important to record exactly what is already "
    "available. The following items from Objective 1 are complete and serve as the "
    "baseline for all Objective 2 comparisons."
)

h2("2.1  Completed Infrastructure")

done("H-GNN-RNN-DTI model implemented: 3-layer H-GAT (8 heads) + 2-layer BiGRU + Gated Cross-Attention.")
done("ConcatBaseline implemented: same encoders, cross-attention replaced by MLP on concatenation.")
done("Training pipeline: Adam optimiser, cosine LR annealing, early stopping, gradient clipping.")
done("Focal Loss (DTI) and MSE Loss (DTA) implemented and tested.")
done("Four split types prepared for all datasets: random, cold_drug, cold_target, cold_pair.")
done("Drug graphs (RDKit + ChemBERTa) preprocessed for Davis, KIBA, Luo_17, Yamanishi_e.")
done("Protein ESM-2 embeddings preprocessed: ESM-2 8M for small datasets, 650M for Luo_17.")
done("1:1 negative sampling implemented for all DTI datasets.")

h2("2.2  Baseline Numbers (Objective 1 Results)")

body("These results are the floor that Objective 2 experiments must beat.")

h3("DTI Cold-Start Performance — H-GNN-RNN-DTI (AUROC, mean ± std, 5 seeds)")

add_table(
    headers=["Dataset", "Random", "Cold-Drug", "Cold-Target", "Cold-Pair"],
    rows=[
        ["yamanishi_e", "0.756 ± 0.125", "0.774 ± 0.011", "0.438 ± 0.045", "0.746 ± 0.054"],
        ["luo_17",      "0.946 ± 0.005", "0.913 ± 0.009", "0.778 ± 0.014", "0.948 ± 0.002"],
    ],
    col_widths=[1.2, 1.3, 1.3, 1.3, 1.3]
)

h3("DTA Regression Performance — H-GNN-RNN-DTI (mean ± std, 5 seeds)")

add_table(
    headers=["Dataset", "MSE ↓", "RMSE ↓", "Pearson r ↑", "R² ↑"],
    rows=[
        ["Davis", "0.379 ± 0.011", "0.615 ± 0.009", "0.721 ± 0.013", "0.508 ± 0.014"],
        ["KIBA",  "0.274 ± 0.014", "0.523 ± 0.013", "0.787 ± 0.012", "0.613 ± 0.019"],
    ],
    col_widths=[1.2, 1.3, 1.3, 1.4, 1.1]
)

h3("Cross-Dataset Transfer Baseline (luo_17 → yamanishi_e, 5 seeds)")

add_table(
    headers=["Scenario", "AUROC", "Interpretation"],
    rows=[
        ["luo_17 (in-domain)",     "0.946 ± 0.005", "Strong; used as source dataset."],
        ["yamanishi_e (in-domain)","0.756 ± 0.112", "Reasonable; used as target dataset."],
        ["luo_17 → yamanishi_e",   "0.508 ± 0.020", "Near-random — no cross-dataset transfer."],
    ],
    col_widths=[2.2, 1.3, 2.5]
)

callout(
    "The 0.508 cross-dataset AUROC is the central motivation for Objective 2. "
    "Phase 3 (pretraining) directly targets improving this number.",
    kind="warn"
)

h2("2.3  Known Weaknesses to Address")

add_table(
    headers=["Weakness", "Phase That Addresses It"],
    rows=[
        ["ESM-2 8M may be too small for cold-target generalisation "
         "(unseen protein sequences).", "Phase 1 — Embedding Comparison"],
        ["1:1 negative sampling and Focal Loss may not be optimal for "
         "highly imbalanced real-world data.", "Phase 2 — Imbalance-Aware Learning"],
        ["No cross-dataset transfer (AUROC 0.508); model overfits to source "
         "distribution.", "Phase 3 — Pretraining Strategy"],
        ["Cold-target anomaly: Concat beats H-GNN on luo_17 cold_target "
         "(0.813 vs 0.778).", "Phase 1 + Phase 3"],
        ["BindingDB and ChEMBL not used; no large-scale evaluation.", "Phase 3 + Phase 4"],
    ],
    col_widths=[3.5, 2.7]
)

# ══════════════════════════════════════════════════════════════════════════════
# 3. PHASE 1 — FOUNDATION MODEL EMBEDDING COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("3.  Phase 1 — Foundation Model Embedding Comparison")

body(
    "The current model uses ChemBERTa (drug embeddings concatenated to atom features) "
    "and ESM-2 (protein sequence embeddings). The proposal notes that 'pre-trained "
    "foundation models learn robust and contextual representations that can significantly "
    "improve generalisation to new data.' Phase 1 tests whether alternative or larger "
    "foundation models improve cold-start performance."
)

h2("3.1  Research Question")

callout(
    "Q1: Which foundation model embedding produces the best DTI and DTA predictions, "
    "especially on cold-drug and cold-target splits?",
    kind="info"
)

h2("3.2  Models to Compare")

h3("Protein Encoders")

add_table(
    headers=["Encoder", "Model ID", "Embedding Dim", "Notes"],
    rows=[
        ["ESM-2 8M (current baseline)",   "facebook/esm2_t6_8M_UR50D",       "320",  "Already done for all datasets. Fast on CPU."],
        ["ESM-2 150M",                    "facebook/esm2_t12_35M_UR50D",      "480",  "Moderate size; balance of quality and speed."],
        ["ESM-2 650M (current for Luo_17)","facebook/esm2_t33_650M_UR50D",   "1280", "Highest quality ESM-2 used so far. Slow on CPU."],
        ["ProtT5-XL-UniRef50",            "Rostlab/prot_t5_xl_uniref50",      "1024", "Trained on UniRef50; state-of-the-art for sequences. Needs GPU."],
    ],
    col_widths=[1.7, 2.3, 1.0, 2.2]
)

h3("Drug Encoders")

add_table(
    headers=["Encoder", "Model ID / Method", "Notes"],
    rows=[
        ["ChemBERTa (current baseline)", "seyonec/ChemBERTa-zinc-base-v1",
         "Already integrated as node-feature augmentation."],
        ["MoLFormer-XL",                "ibm/MoLFormer-XL-both-10pct",
         "Trained on 1.1B SMILES from PubChem + ZINC. Stronger chemical generalism."],
        ["No pre-trained augmentation",  "RDKit features only",
         "Ablation: remove ChemBERTa to measure its contribution."],
    ],
    col_widths=[1.7, 2.5, 2.0]
)

h2("3.3  Experimental Design")

body(
    "For each embedding combination, train and evaluate H-GNN-RNN-DTI using the same "
    "training setup as Objective 1 (Adam, cosine LR, early stopping, 5 seeds). "
    "Test on the two most informative datasets for cold-start: Yamanishi_e and Luo_17."
)

add_table(
    headers=["Experiment ID", "Drug Encoder", "Protein Encoder", "Datasets", "Splits"],
    rows=[
        ["P1-A (baseline)", "ChemBERTa",        "ESM-2 8M",  "yamanishi_e, luo_17", "all 4 splits"],
        ["P1-B",            "ChemBERTa",        "ESM-2 150M","yamanishi_e, luo_17", "all 4 splits"],
        ["P1-C",            "ChemBERTa",        "ESM-2 650M","yamanishi_e, luo_17", "all 4 splits"],
        ["P1-D",            "ChemBERTa",        "ProtT5",    "yamanishi_e, luo_17", "all 4 splits"],
        ["P1-E",            "MoLFormer-XL",     "ESM-2 8M",  "yamanishi_e",         "all 4 splits"],
        ["P1-F",            "MoLFormer-XL",     "ESM-2 650M","yamanishi_e",         "all 4 splits"],
        ["P1-G (ablation)", "RDKit only",       "ESM-2 8M",  "yamanishi_e",         "all 4 splits"],
    ],
    col_widths=[1.0, 1.2, 1.2, 1.5, 1.3]
)

callout(
    "Priority: Start with P1-B (ESM-2 150M) and P1-C (ESM-2 650M), since protein "
    "quality is the most likely bottleneck on cold-target splits. P1-D (ProtT5) "
    "requires a GPU — defer until GPU access is available.",
    kind="warn"
)

h2("3.4  Expected Deliverables")

bullet("Per-experiment AUROC/AUPRC/F1 tables (5 seeds each) for all 4 splits on both datasets.")
bullet("Statistical comparison table: each variant vs. P1-A baseline using paired t-test (df=4).")
bullet("Recommendation on best protein encoder and best drug encoder for the rest of Objective 2.")

h2("3.5  Metrics and Success Criteria")

body(
    "Primary: AUROC on cold_drug and cold_target splits (most directly affected by "
    "embedding quality). Secondary: AUPRC (important when interactions are sparse). "
    "Success: at least one embedding variant achieves statistically significant improvement "
    "(p < 0.05) over P1-A on either cold_drug or cold_target."
)

h2("3.6  Infrastructure Steps")

gap("Install ProtT5 and MoLFormer via HuggingFace Transformers (pip install transformers).")
gap("Modify 11_preprocess_proteins.py to accept --esm_model argument; add ProtT5 branch.")
gap("Modify 10_preprocess_drugs.py to accept --drug_model argument; add MoLFormer branch.")
gap("Re-run preprocessing for each new embedding variant (outputs saved to separate .pt files).")
gap("Run train.py pointing to the new embedding files; no architecture changes required.")

# ══════════════════════════════════════════════════════════════════════════════
# 4. PHASE 2 — IMBALANCE-AWARE LEARNING
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("4.  Phase 2 — Imbalance-Aware Learning")

body(
    "DTI datasets are inherently imbalanced: only a tiny fraction of all possible "
    "drug–protein pairs are experimentally confirmed to interact. The proposal identifies "
    "this as a critical limitation: 'severe class imbalance, where true interactions are "
    "far outnumbered by non-interactions, can lead to model overfitting and a false sense "
    "of accuracy.' Phase 2 systematically tests strategies to mitigate this."
)

h2("4.1  Research Question")

callout(
    "Q2: Which combination of loss function and negative sampling ratio produces the "
    "most reliable predictions on highly imbalanced cold-split settings, as measured "
    "by AUPRC (which is more sensitive than AUROC to imbalance)?",
    kind="info"
)

h2("4.2  Current Approach and Its Limitations")

body(
    "The Objective 1 baseline used:"
)
bullet("Focal Loss with γ = 2.0 and α = 0.25 (down-weights easy negatives).")
bullet("1:1 negative sampling ratio (equal positives and negatives in training).")

body(
    "The 1:1 ratio is unrealistically balanced compared to the true data distribution, "
    "where real DTI datasets may have thousands of negatives for every positive. "
    "A model trained on 1:1 data may be over-confident on the positive class and "
    "under-perform in the realistic 1:many scenario."
)

h2("4.3  Strategies to Test")

h3("Loss Function Variants")

add_table(
    headers=["Loss", "Formula / Description", "When It Helps"],
    rows=[
        ["Focal Loss (current)", "FL(p) = −α(1−p)^γ · log(p),  γ=2, α=0.25",
         "Hard-to-classify samples get more weight. Good for moderate imbalance."],
        ["Weighted BCE", "BCE with class weight w_pos = N_neg / N_pos",
         "Simple rebalancing; standard baseline for imbalance."],
        ["Focal Loss γ-sweep", "γ ∈ {1, 2, 3, 5}; α fixed at 0.25",
         "Higher γ focuses more on hard negatives in extreme imbalance."],
        ["Asymmetric Loss (ASL)", "Separate γ for positives and negatives",
         "State-of-the-art for multi-label; reduces contribution of easy negatives."],
    ],
    col_widths=[1.5, 2.5, 2.2]
)

h3("Negative Sampling Ratio Variants")

add_table(
    headers=["Ratio (pos:neg)", "Imbalance Factor", "Expected Effect"],
    rows=[
        ["1:1 (current baseline)", "1×",   "Balanced; good for small datasets."],
        ["1:5",                    "5×",   "Moderate imbalance; more realistic."],
        ["1:10",                   "10×",  "High imbalance; matches proposal recommendation. Tests robustness."],
        ["1:20",                   "20×",  "Extreme imbalance; stress test. Only on larger datasets."],
    ],
    col_widths=[1.5, 1.2, 3.5]
)

h2("4.4  Experimental Design")

body(
    "Test on Yamanishi_e (small, where imbalance matters most) and Luo_17 (larger, "
    "provides a reference). Use the best embedding from Phase 1. Run 5 seeds per "
    "configuration; evaluate on all 4 splits."
)

add_table(
    headers=["Experiment ID", "Loss Function", "Neg:Pos Ratio", "Dataset"],
    rows=[
        ["P2-A (baseline)", "Focal (γ=2, α=0.25)", "1:1",  "yamanishi_e, luo_17"],
        ["P2-B",            "Weighted BCE",         "1:1",  "yamanishi_e"],
        ["P2-C",            "Focal (γ=1)",          "1:1",  "yamanishi_e"],
        ["P2-D",            "Focal (γ=3)",          "1:1",  "yamanishi_e"],
        ["P2-E",            "Focal (γ=5)",          "1:1",  "yamanishi_e"],
        ["P2-F",            "Focal (γ=2, α=0.25)", "1:5",  "yamanishi_e, luo_17"],
        ["P2-G",            "Focal (γ=2, α=0.25)", "1:10", "yamanishi_e, luo_17"],
        ["P2-H (best combo)","Best from P2-B/D/E",  "1:5 or 1:10", "both datasets"],
    ],
    col_widths=[1.1, 1.8, 1.2, 2.1]
)

callout(
    "Priority order: P2-F and P2-G first (ratio change is cheap — no retraining of "
    "embeddings needed; just change 12_preprocess_labels.py --ratio flag). "
    "Then P2-B (weighted BCE) as a sanity check against focal loss.",
    kind="info"
)

h2("4.5  Primary Metric — AUPRC")

body(
    "AUROC is not sensitive to class imbalance because it evaluates ranking quality "
    "across all thresholds equally. AUPRC (Area Under the Precision-Recall Curve) "
    "is the correct metric when positives are rare: a random classifier scores "
    "AUPRC = prevalence (e.g., 0.05 for 1:20 data), so any improvement above this "
    "is meaningful. The existing code already reports AUPRC — use it as the "
    "primary metric in Phase 2."
)

h2("4.6  Infrastructure Steps")

gap("Modify 12_preprocess_labels.py to accept --ratio argument (e.g., --ratio 1to5, 1to10).")
gap("Add AsymmetricLoss to model/losses.py if P2 results suggest it is worth testing.")
gap("Add γ as a command-line argument to train.py (currently hardcoded in config.py).")
gap("Run statistical comparison: each P2 variant vs. P2-A using paired t-test on AUPRC (df=4).")

# ══════════════════════════════════════════════════════════════════════════════
# 5. PHASE 3 — SELF-SUPERVISED PRETRAINING STRATEGY
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("5.  Phase 3 — Self-Supervised Pretraining Strategy")

body(
    "This is the most technically ambitious phase and the one most directly tied to "
    "Objective 2's core claim. The proposal states: 'The drug and protein encoders are "
    "optionally pre-trained on large-scale unlabelled datasets (e.g., DrugBank) using "
    "techniques such as contrastive learning and masked feature prediction. This enables "
    "the model to learn high-quality, transferable representations that improve downstream "
    "DTI prediction performance.' Phase 3 designs and evaluates this pretraining pipeline."
)

h2("5.1  Research Question")

callout(
    "Q3: Does pretraining the drug and protein encoders on a large dataset before "
    "fine-tuning on a target dataset significantly improve performance on cold-drug, "
    "cold-target, and cross-dataset scenarios?",
    kind="info"
)

h2("5.2  Why Pretraining Is Expected to Help")

body(
    "The cross-dataset experiment in Objective 1 showed AUROC = 0.508 when transferring "
    "luo_17 → yamanishi_e. This happened because the model was a discriminative classifier: "
    "it learned which specific molecules in luo_17 interact, not general binding principles. "
    "Pretraining changes this by first training the encoders in a self-supervised manner — "
    "no interaction labels needed — so they learn general structural and sequence features "
    "before ever seeing interaction data."
)

bullet("A drug encoder pretrained on BindingDB learns that similar scaffolds have similar "
       "binding properties, even without interaction labels.")
bullet("A protein encoder pretrained on UniProt or BindingDB protein sequences learns "
       "general motif patterns that transfer across protein families.")
bullet("When fine-tuned on Davis, KIBA, or Yamanishi_e, the pretrained encoders start "
       "from a better position — especially for cold entities not seen during fine-tuning.")

h2("5.3  Pretraining Strategies to Implement")

h3("Strategy A — Supervised Pretraining on BindingDB")

body(
    "The simplest and most practical approach: train the full H-GNN-RNN-DTI model "
    "(both encoders + cross-attention) on BindingDB as a DTI classification task, "
    "using all available interaction labels. Then freeze or fine-tune on the target "
    "dataset. This is analogous to how ImageNet pretraining works for computer vision."
)

bullet("Pretraining data: BindingDB (~700K–1M+ labelled drug–protein pairs after cleaning).")
bullet("Pretraining task: binary DTI classification with Focal Loss.")
bullet("Fine-tuning: replace the final classifier head; fine-tune all layers on the target "
       "dataset with a lower learning rate (e.g., lr = 1e-5 instead of 1e-4).")
bullet("Comparison: fine-tuned model vs. from-scratch model on all 4 splits, 5 seeds.")

h3("Strategy B — Contrastive Pretraining (Drug Encoder)")

body(
    "Contrastive learning trains the drug encoder to produce similar embeddings for "
    "chemically similar drugs and different embeddings for dissimilar drugs — without "
    "needing interaction labels. This is implemented using a molecular graph "
    "contrastive framework:"
)

bullet("Data augmentation: for each drug graph, create two augmented views "
       "(randomly mask atoms, permute edges, or add noise to features).")
bullet("Loss: InfoNCE (NT-Xent) loss — the encoder must identify the two views of the "
       "same molecule from a batch of other molecules.")
bullet("After pretraining the drug encoder, attach the pretrained weights to "
       "H-GNN-RNN-DTI and fine-tune end-to-end on the target dataset.")
bullet("Note: ESM-2 already serves as a pretrained protein encoder, so contrastive "
       "pretraining is primarily useful for the drug (GAT) encoder.")

h3("Strategy C — Masked Feature Prediction (Drug Encoder)")

body(
    "Masked feature prediction is an alternative self-supervised approach: randomly mask "
    "the atom features of some nodes in the molecular graph and train the GAT to "
    "reconstruct the masked features. This forces the encoder to learn chemically "
    "meaningful node representations. After pretraining, use as encoder initialisation."
)

callout(
    "Recommendation: Implement Strategy A first. It reuses the existing train.py pipeline "
    "almost unchanged and provides the clearest scientific story. Add Strategy B if time "
    "and GPU access allow. Strategy C is optional/exploratory.",
    kind="info"
)

h2("5.4  Pretraining Datasets")

add_table(
    headers=["Dataset", "Size", "Task", "Availability", "Priority"],
    rows=[
        ["BindingDB",  "~1M+ pairs", "DTI (Ki, Kd, IC50)",
         "Preprocessed labels already exist; drug graphs and protein embeddings needed.",
         "High"],
        ["ChEMBL",     "~2M+ pairs", "DTI & DTA",
         "Label files exist; large-scale preprocessing needed.",
         "Medium"],
        ["DrugBank",   "~10K pairs", "DTI",
         "Smaller but high quality; good for contrastive pretraining.",
         "Medium"],
        ["UniProt sequences", "Millions of sequences", "Self-supervised protein only",
         "Protein sequences only — no interaction labels. For contrastive protein pretraining.",
         "Low (ESM-2 already covers this)"],
    ],
    col_widths=[1.2, 1.0, 1.2, 2.4, 0.9]
)

h2("5.5  Fine-Tuning Protocol")

body(
    "After pretraining, the model is fine-tuned on each target dataset. To prevent "
    "catastrophic forgetting of pretraining knowledge, use the following protocol:"
)

add_table(
    headers=["Setting", "Pretraining", "Fine-tuning"],
    rows=[
        ["Learning rate",    "1e-4 (standard)",    "1e-5 (10× lower)"],
        ["Epochs",           "50–100 on BindingDB", "50–100 on target dataset"],
        ["Early stopping",   "Validation AUROC",    "Validation AUROC (DTI) or MSE (DTA)"],
        ["Classifier head",  "Trained on BindingDB", "Reset and retrained from scratch"],
        ["Encoder layers",   "Trained from scratch", "Optionally frozen for first 10 epochs"],
    ],
    col_widths=[1.5, 2.2, 2.2]
)

h2("5.6  Experimental Design")

add_table(
    headers=["Experiment ID", "Pretrain Strategy", "Pretrain Data", "Fine-tune On", "Comparison"],
    rows=[
        ["P3-A (baseline)", "None (from scratch)", "—",
         "yamanishi_e, luo_17", "vs. P3-B, P3-C"],
        ["P3-B",            "Supervised (Strategy A)", "BindingDB",
         "yamanishi_e, luo_17", "vs. P3-A (does pretraining help?)"],
        ["P3-C",            "Supervised (Strategy A)", "ChEMBL",
         "yamanishi_e",         "vs. P3-B (which source is better?)"],
        ["P3-D",            "Supervised (Strategy A)", "BindingDB",
         "Davis, KIBA",         "vs. P3-A (does pretraining help on DTA?)"],
        ["P3-E (cross-dataset)", "BindingDB fine-tune", "BindingDB → yamanishi_e",
         "yamanishi_e",         "vs. Obj 1 baseline (0.508 AUROC cross-dataset)"],
        ["P3-F (optional)", "Contrastive drug (B)", "BindingDB drug graphs",
         "yamanishi_e",         "vs. P3-A (contrastive vs. supervised pretraining)"],
    ],
    col_widths=[1.0, 1.5, 1.3, 1.4, 1.8]
)

callout(
    "The most important experiment is P3-E: training on BindingDB and directly "
    "evaluating on yamanishi_e (no fine-tuning on yamanishi_e). The Objective 1 "
    "baseline (luo_17 → yamanishi_e) gave AUROC 0.508. If BindingDB pretraining "
    "raises this above 0.6 or 0.7, it demonstrates meaningful transfer learning.",
    kind="result"
)

h2("5.7  Infrastructure Steps")

gap("Run 10b_preprocess_large_drugs.py on BindingDB (chunked drug graph generation — GPU recommended).")
gap("Run 11_preprocess_proteins.py on BindingDB protein sequences with ESM-2 (GPU recommended).")
gap("Run 12_preprocess_labels.py and 13_preprocess_splits.py for BindingDB.")
gap("Modify train.py to accept --pretrain_checkpoint argument for loading encoder weights before fine-tuning.")
gap("Add a --freeze_encoders N flag to optionally freeze encoder for the first N epochs of fine-tuning.")
gap("Save pretrained encoder checkpoints separately so they can be reused across multiple fine-tuning runs.")

# ══════════════════════════════════════════════════════════════════════════════
# 6. PHASE 4 — COLD-START AND CROSS-DATASET EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("6.  Phase 4 — Cold-Start and Cross-Dataset Evaluation")

body(
    "Phase 4 brings together the best settings from Phases 1, 2, and 3 and runs "
    "the comprehensive cold-start and cross-dataset evaluation specified in the proposal. "
    "The goal is to demonstrate that the Objective 2 improvements produce statistically "
    "significant gains on unseen drugs, unseen targets, and across-distribution scenarios."
)

h2("6.1  Research Question")

callout(
    "Do the combined improvements from Phase 1–3 (best embedding + best imbalance "
    "strategy + pretraining) produce a significantly better model than the Objective 1 "
    "baseline on cold-start and cross-dataset metrics?",
    kind="info"
)

h2("6.2  Cold-Start Evaluation Protocol")

body(
    "The same four split types used in Objective 1 are reused, following the DTKGIN "
    "protocol (Luo et al., 2024) described in the proposal:"
)

add_table(
    headers=["Setting", "Label", "What the Model Faces", "Key Metric"],
    rows=[
        ["Warm-start (random)", "S1", "Both drugs and proteins may appear in training.",
         "AUROC — general performance."],
        ["Cold-drug",           "S2", "All test drugs are completely new; not seen during training.",
         "AUROC + AUPRC — key for drug discovery."],
        ["Cold-target",         "S3", "All test proteins are completely new.",
         "AUROC + AUPRC — key for new disease targets."],
        ["Cold-pair",           "S4", "Drug–target pair is new; individuals may appear.",
         "AUROC — hardest general setting."],
    ],
    col_widths=[1.6, 0.6, 2.6, 1.9]
)

h2("6.3  Cross-Dataset Transfer Evaluation")

body(
    "The proposal specifies: 'The model trained on one benchmark dataset (e.g., BindingDB) "
    "will be tested on another (e.g., DAVIS) to assess its ability to generalise across "
    "different experimental protocols and domain shifts.' The following transfer pairs are "
    "planned:"
)

add_table(
    headers=["Source (train)", "Target (test)", "Baseline AUROC", "Expected After Pretraining"],
    rows=[
        ["luo_17",     "yamanishi_e", "0.508 ± 0.020", "Target: > 0.65"],
        ["BindingDB",  "yamanishi_e", "—  (new)",       "Target: > 0.70"],
        ["BindingDB",  "luo_17",      "—  (new)",       "Target: > 0.85"],
        ["BindingDB",  "Davis",       "—  (new)",       "Target: Pearson r > 0.65"],
        ["BindingDB",  "KIBA",        "—  (new)",       "Target: Pearson r > 0.70"],
    ],
    col_widths=[1.4, 1.3, 1.5, 2.5]
)

callout(
    "These are aspirational targets based on transfer learning improvements reported "
    "in the literature (e.g., iNGNN-DTI, MutualDTA). Actual results may differ. "
    "Even a result of AUROC 0.60 cross-dataset would be publishable progress over "
    "the near-random 0.508 baseline.",
    kind="warn"
)

h2("6.4  Slice-Aware Benchmarking")

body(
    "The proposal introduces 'slice-aware benchmarking' — evaluating performance across "
    "biologically meaningful subgroups rather than just overall metrics. This is done "
    "post-hoc: after evaluating the best model, stratify the test set and compute "
    "metrics within each slice."
)

add_table(
    headers=["Slice Dimension", "How to Partition", "Why It Matters"],
    rows=[
        ["Drug scaffold family",  "Use RDKit Murcko scaffold clustering",
         "Reveals if model generalises to novel chemical scaffolds or memorises known ones."],
        ["Protein family",        "Use UniProt protein family annotations",
         "Shows if model performs equally on kinases, GPCRs, enzymes, etc."],
        ["Binding affinity range","pKd bins: weak (≤5), moderate (5–7), strong (>7)",
         "Identifies if model struggles with high-affinity predictions."],
        ["Dataset split origin",  "cold_drug vs. cold_target vs. cold_pair",
         "Already implemented — confirms cold split trends hold post-Objective 2."],
    ],
    col_widths=[1.5, 2.0, 2.7]
)

h2("6.5  Final Comprehensive Comparison Table")

body(
    "At the end of Phase 4, all results are assembled into a single comparison table "
    "covering all four main baselines and the best Objective 2 model:"
)

add_table(
    headers=["Model", "Random", "Cold-Drug", "Cold-Target", "Cold-Pair", "Cross-Dataset"],
    rows=[
        ["GSRF-DTI (Zhu et al., 2024)",  "0.767", "0.775", "0.362 ‼", "0.859", "N/A"],
        ["DTKGIN (Luo et al., 2024)",     "0.869", "0.747", "0.557",   "0.863", "N/A"],
        ["H-GNN-RNN-DTI (Obj. 1)",        "0.756", "0.774", "0.438",   "0.746", "0.508"],
        ["H-GNN-RNN-DTI + Obj. 2 best",   "TBD",   "TBD",   "TBD",    "TBD",   "TBD"],
    ],
    col_widths=[2.2, 0.9, 0.9, 0.9, 0.9, 1.2]
)

body("Yamanishi_e AUROC shown. Cross-dataset = luo_17 → yamanishi_e.")

# ══════════════════════════════════════════════════════════════════════════════
# 7. PHASE 5 — STATISTICAL ANALYSIS AND ABLATION
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("7.  Phase 5 — Statistical Analysis and Full Ablation")

body(
    "Phase 5 quantifies the isolated contribution of each Objective 2 component and "
    "tests whether improvements are statistically significant. This is required for "
    "the research paper to claim that each component adds value independently."
)

h2("7.1  Ablation Matrix")

body(
    "Run the following six model configurations for 5 seeds each, on yamanishi_e "
    "(all 4 splits) and luo_17 (all 4 splits). Each configuration adds one component "
    "over the previous row:"
)

add_table(
    headers=["Config", "Embedding", "Loss / Ratio", "Pretraining", "Expected vs. Baseline"],
    rows=[
        ["C0 — Obj. 1 baseline", "ChemBERTa + ESM-2 8M",  "Focal γ=2 / 1:1", "None",     "—"],
        ["C1 — Better embedding", "Best from Phase 1",     "Focal γ=2 / 1:1", "None",     "+Δ_embed"],
        ["C2 — Better imbalance", "Best from Phase 1",     "Best from Phase 2","None",     "+Δ_imbal"],
        ["C3 — Pretraining",      "Best from Phase 1",     "Best from Phase 2","BindingDB","Best overall"],
        ["C4 — Contrastive (opt.)","Best from Phase 1",    "Best from Phase 2","Contrastive","vs. C3"],
        ["C5 — All components",   "Best from Phase 1",     "Best from Phase 2","BindingDB + contrastive","Ceiling"],
    ],
    col_widths=[1.5, 1.7, 1.5, 1.3, 1.2]
)

h2("7.2  Statistical Testing Protocol")

body(
    "The same paired t-test framework used in Objective 1 applies:"
)

bullet("n = 5 seeds per configuration (same seeds as Obj. 1: seeds 1–5).")
bullet("Test: scipy.stats.ttest_rel(config_X, config_0) for each metric and split.")
bullet("α = 0.05 two-tailed; df = 4. Report t-statistic and p-value.")
bullet("Significance indicators: ✓✓ p < 0.01,  ✓ p < 0.05,  n.s. not significant.")
bullet("Metrics: AUROC and AUPRC for DTI; MSE and Pearson r for DTA.")

h2("7.3  Reporting Format")

body(
    "For each dataset and split, produce a table with all six configurations "
    "and their statistical significance relative to C0 (Objective 1 baseline). "
    "This directly answers Objective 2's research question: which combination "
    "most significantly improves cold-start generalisation?"
)

callout(
    "If C1 alone (better embedding) already gives p < 0.05 improvement, report that "
    "as the minimum viable Objective 2 result. Each additional component (C2, C3) "
    "either adds further improvement or confirms that its contribution is marginal.",
    kind="info"
)

h2("7.4  Analysis Script")

body(
    "Extend compute_dta_stats.py into a new script compute_objective2_stats.py that:"
)

bullet("Loads results for all six configurations (each has 5 seed JSON files).")
bullet("Computes mean ± std (ddof=1) for all metrics across seeds.")
bullet("Runs paired t-tests for each configuration vs. C0 on each metric and split.")
bullet("Outputs a formatted LaTeX-ready table for the research paper.")
gap("Write compute_objective2_stats.py after all Phase 1–4 results are collected.")

# ══════════════════════════════════════════════════════════════════════════════
# 8. EXECUTION ROADMAP
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("8.  Execution Roadmap")

body(
    "The phases can be partially parallelised. The dependency chain is: "
    "Phase 1 must complete before Phase 5 (which requires knowing the best embedding). "
    "Phase 2 and Phase 1 can run in parallel since they only share the embedding preprocessing. "
    "Phase 3 depends on BindingDB preprocessing, which requires GPU access."
)

add_table(
    headers=["Phase", "Task", "Prerequisite", "Estimated Effort", "GPU Needed?"],
    rows=[
        ["1A", "Re-preprocess proteins with ESM-2 150M",
         "None", "~2–4h CPU", "No"],
        ["1B", "Re-preprocess proteins with ESM-2 650M (yamanishi_e)",
         "None", "~4–8h CPU", "Recommended"],
        ["1C", "Train P1-B, P1-C configs (5 seeds × 2 datasets × 4 splits)",
         "Phase 1A/1B", "~2–4 days CPU", "Strongly recommended"],
        ["1D", "Install ProtT5; preprocess proteins; train P1-D",
         "Phase 1C", "~1 week CPU", "Yes (ProtT5 inference)"],
        ["2A", "Modify label sampling ratio; train P2-F, P2-G (1:5, 1:10)",
         "Phase 1 results", "~1–2 days CPU", "No"],
        ["2B", "Implement Weighted BCE; train P2-B",
         "None", "~1 day CPU", "No"],
        ["3A", "Preprocess BindingDB drug graphs and proteins",
         "GPU access", "~1–2 days GPU", "Yes"],
        ["3B", "Pretrain H-GNN-RNN-DTI on BindingDB (supervised)",
         "Phase 3A", "~1–3 days GPU", "Yes"],
        ["3C", "Fine-tune on yamanishi_e, luo_17, Davis, KIBA (P3-B/D/E)",
         "Phase 3B", "~2–4 days CPU/GPU", "Recommended"],
        ["4",  "Slice-aware benchmarking and cross-dataset table",
         "Phases 1–3 complete", "~1 day", "No"],
        ["5",  "Statistical ablation and final tables",
         "All phases complete", "~1 day (scripting)", "No"],
    ],
    col_widths=[0.6, 2.2, 1.5, 1.3, 1.0]
)

callout(
    "The single most important accelerator: GPU access. Phases 1D, 3A, and 3B all "
    "require GPU. Without GPU, ProtT5 and BindingDB preprocessing are impractical. "
    "Request access to USM HPC cluster or use Google Colab Pro before starting Phase 3.",
    kind="warn"
)

h2("8.1  Minimum Viable Objective 2")

body(
    "If GPU access is delayed, the following experiments can be completed on CPU "
    "and still constitute a publishable Objective 2 result:"
)

bullet("Phase 1: ESM-2 8M vs. ESM-2 150M vs. ESM-2 650M comparison on yamanishi_e "
       "(ESM-2 650M inference is slow but feasible on CPU for small datasets).")
bullet("Phase 2: Negative sampling ratio comparison (1:1 vs. 1:5 vs. 1:10) — "
       "no GPU required, just relabelling.")
bullet("Phase 5: Ablation of embedding size + imbalance strategy — two components, "
       "both testable without BindingDB.")

callout(
    "Minimum viable Objective 2: ESM-2 size sweep + negative ratio sweep + "
    "statistical testing = 3 × 2 × 5 seeds × 2 datasets × 4 splits. "
    "This is ~240 training runs, roughly 8–12 days on CPU.",
    kind="info"
)

# ══════════════════════════════════════════════════════════════════════════════
# 9. CURRENT STATUS
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("9.  Current Status")

body(
    "The following status reflects the state of the project at the time this "
    "document was written (July 2026). All Phase 1–5 items for Objective 2 are "
    "yet to be run."
)

h2("9.1  Completed (From Objective 1)")

done("H-GNN-RNN-DTI model architecture fully implemented and tested.")
done("All four datasets preprocessed with ESM-2 8M and ChemBERTa: Davis, KIBA, Luo_17, Yamanishi_e.")
done("All four split types generated and tested (random, cold_drug, cold_target, cold_pair).")
done("Focal Loss (γ=2, α=0.25) at 1:1 ratio implemented and evaluated.")
done("Baseline AUROC/AUPRC/F1 results for all 8 DTI configurations (5 seeds each).")
done("Baseline MSE/MAE/RMSE/R²/Pearson/Spearman for Davis and KIBA DTA (5 seeds each).")
done("Cross-dataset baseline: luo_17 → yamanishi_e AUROC 0.508 ± 0.020.")
done("Statistical testing framework (paired t-test, ddof=1) implemented in compute_dta_stats.py.")
done("BindingDB and ChEMBL label files and split files generated (preprocessing not yet run).")
done("Evaluation report (paper/evaluation_report.md) with all Objective 1 results.")

h2("9.2  Not Yet Started (Objective 2)")

gap("Phase 1: ESM-2 150M protein preprocessing.")
gap("Phase 1: ESM-2 650M protein preprocessing for yamanishi_e (only Luo_17 has it currently).")
gap("Phase 1: ProtT5 protein preprocessing (requires GPU).")
gap("Phase 1: MoLFormer drug preprocessing and comparison.")
gap("Phase 1: Training all P1-B through P1-G configurations.")
gap("Phase 2: Negative sampling ratio experiments (1:5, 1:10).")
gap("Phase 2: Weighted BCE loss comparison.")
gap("Phase 2: Focal Loss γ-sweep (γ ∈ {1, 3, 5}).")
gap("Phase 3: BindingDB drug graph preprocessing (10b_preprocess_large_drugs.py).")
gap("Phase 3: BindingDB protein embedding generation (11_preprocess_proteins.py).")
gap("Phase 3: Supervised pretraining on BindingDB.")
gap("Phase 3: Fine-tuning experiments (P3-B through P3-F).")
gap("Phase 4: Cross-dataset evaluation with BindingDB as source.")
gap("Phase 4: Slice-aware benchmarking.")
gap("Phase 5: Full ablation statistical table.")
gap("compute_objective2_stats.py — script to aggregate all Phase 1–4 results.")

# ══════════════════════════════════════════════════════════════════════════════
# 10. GAPS AND RISKS
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("10.  Gaps and Risks")

h2("10.1  GPU Dependency")

body(
    "Phase 3 (BindingDB pretraining) and Phase 1D (ProtT5) are GPU-dependent. "
    "On CPU, processing one million BindingDB drug graphs would take weeks. "
    "This is the largest risk to the Objective 2 timeline."
)
bullet("Mitigation: apply for USM HPC cluster allocation early.")
bullet("Mitigation: use Google Colab Pro (A100 GPU, ~$10/month) for preprocessing batches.")
bullet("Mitigation: use the minimum viable plan (CPU-feasible experiments) while "
       "waiting for GPU access.")

h2("10.2  BindingDB Data Quality")

body(
    "BindingDB contains measurements from multiple assay types (Ki, Kd, IC50, EC50) "
    "with different units and scales. Mixing these without careful normalisation can "
    "introduce noise that harms pretraining."
)
bullet("Mitigation: use only Kd and Ki measurements (most directly comparable to Davis/KIBA).")
bullet("Mitigation: convert all values to pKi/pKd using −log10 transformation.")
bullet("Mitigation: filter out entries with pIC50 < 4 (very weak, likely false negatives).")

h2("10.3  Catastrophic Forgetting During Fine-Tuning")

body(
    "After pretraining on BindingDB, fine-tuning on a small dataset (e.g., yamanishi_e "
    "with 890 pairs) may overwrite the pretrained representations, losing the benefit "
    "of pretraining. This is the standard 'catastrophic forgetting' problem."
)
bullet("Mitigation: use a lower learning rate for fine-tuning (1e-5 vs. 1e-4).")
bullet("Mitigation: freeze encoder layers for the first 10 epochs of fine-tuning.")
bullet("Mitigation: use learning rate warm-up over 5 epochs to allow gradual adaptation.")

h2("10.4  Hyperparameter Proliferation")

body(
    "Each phase introduces new hyperparameters (embedding dimension, γ, sampling ratio, "
    "fine-tuning LR). Running a full grid search across all combinations is infeasible. "
    "Use a sequential strategy: fix the best setting from each phase before tuning the next."
)
bullet("Phase 1: fix the best embedding model.")
bullet("Phase 2: fix the best loss/ratio (using the Phase 1 embedding).")
bullet("Phase 3: fix the pretraining protocol (using Phase 1+2 settings).")

# ══════════════════════════════════════════════════════════════════════════════
# 11. EXPECTED OUTCOMES
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("11.  Expected Outcomes")

body(
    "Based on the literature and the Objective 1 results, the following outcomes are "
    "anticipated for each phase. These are hypotheses to test, not guarantees."
)

h2("11.1  Phase 1 — Embedding Comparison")

add_table(
    headers=["Hypothesis", "Reasoning", "Risk"],
    rows=[
        ["ESM-2 150M or 650M will outperform ESM-2 8M on cold-target splits.",
         "Larger models capture more evolutionary information; cold-target "
         "relies entirely on the protein encoder's ability to generalise.",
         "Medium: ESM-2 8M may already capture enough for the small yamanishi_e proteins."],
        ["ProtT5 will outperform ESM-2 on both cold-drug and cold-target.",
         "ProtT5 is specifically trained on protein sequences for downstream tasks; "
         "it may generalise better to unseen protein families.",
         "High: ProtT5 requires GPU; results are uncertain without empirical testing."],
        ["MoLFormer will outperform ChemBERTa on cold-drug splits.",
         "MoLFormer is trained on 1.1B molecules vs. ChemBERTa's 77M; "
         "richer chemical knowledge should improve generalisation to new scaffolds.",
         "Medium: ChemBERTa may already be sufficient for the datasets tested."],
    ],
    col_widths=[2.0, 2.5, 1.7]
)

h2("11.2  Phase 2 — Imbalance-Aware Learning")

add_table(
    headers=["Hypothesis", "Reasoning", "Risk"],
    rows=[
        ["1:5 or 1:10 negative sampling will improve AUPRC on cold-drug splits.",
         "A model trained on 1:1 data is not calibrated for realistic imbalance. "
         "More negatives during training should improve precision at low recall.",
         "Low: the proposal explicitly recommends these ratios."],
        ["Focal Loss with γ=3 will outperform γ=2 on the most imbalanced splits.",
         "Higher γ focuses more strongly on hard-to-classify samples, "
         "which are more common under 1:10 sampling.",
         "Medium: optimal γ depends on the specific imbalance level."],
        ["Weighted BCE will underperform Focal Loss when combined with 1:10 sampling.",
         "Focal Loss is specifically designed for extreme imbalance; "
         "BCE rebalancing is less adaptive.",
         "Low-medium: weighted BCE is a well-established strong baseline."],
    ],
    col_widths=[2.0, 2.5, 1.7]
)

h2("11.3  Phase 3 — Pretraining")

add_table(
    headers=["Hypothesis", "Reasoning", "Risk"],
    rows=[
        ["Supervised pretraining on BindingDB will improve cold-drug AUROC "
         "on yamanishi_e by ≥ 0.05.",
         "BindingDB contains hundreds of thousands of diverse drug–protein interactions; "
         "the drug encoder should learn scaffold-independent binding features.",
         "Medium: if BindingDB and yamanishi_e have very different molecular distributions, "
         "pretraining may not transfer."],
        ["Cross-dataset AUROC (BindingDB → yamanishi_e) will exceed 0.60.",
         "Pretraining on a larger, more diverse dataset should learn more general "
         "binding representations than luo_17-only training.",
         "Medium: the yamanishi_e enzyme family is very specific; "
         "generic binding pretraining may not capture enzyme-specific features."],
        ["DTA fine-tuning (P3-D) will improve Davis Pearson r by ≥ 0.02.",
         "BindingDB contains affinity data (Ki, Kd); a model pretrained on "
         "affinity prediction should generalise better.",
         "Low: affinity values are noisier in BindingDB than in Davis."],
    ],
    col_widths=[2.0, 2.5, 1.7]
)

h2("11.4  Final Objective 2 Contribution")

callout(
    "Success criteria for Objective 2: the best Objective 2 configuration achieves "
    "statistically significant improvement (p < 0.05, paired t-test, 5 seeds) over "
    "the Objective 1 baseline on at least two of: (1) yamanishi_e cold-drug AUROC, "
    "(2) yamanishi_e cold-target AUROC, (3) luo_17 cold-target AUROC, "
    "(4) cross-dataset AUROC. Meeting this criteria satisfies the proposal's objective "
    "of 'significantly enhancing predictive performance on unseen drugs, unseen targets, "
    "and cross-dataset conditions.'",
    kind="result"
)

# ══════════════════════════════════════════════════════════════════════════════
# 12. CONCLUSION
# ══════════════════════════════════════════════════════════════════════════════

page_break()
h1("12.  Conclusion")

body(
    "Objective 2 is the generalisation objective of the H-GNN-RNN-DTI project. "
    "It takes the validated H-GNN-RNN-DTI architecture from Objective 1 and asks "
    "how to make it better at handling novel drugs, novel proteins, and completely "
    "new datasets — the three most practically important scenarios in real drug discovery."
)

body(
    "The analysis plan is structured in five phases:"
)

bullet("Phase 1 — Foundation Model Embedding Comparison: identifies the best protein "
       "and drug encoders by systematically testing ESM-2 (8M, 150M, 650M), ProtT5, "
       "ChemBERTa, and MoLFormer. This directly addresses the representation quality bottleneck.")
bullet("Phase 2 — Imbalance-Aware Learning: tests negative sampling ratios (1:1, 1:5, 1:10) "
       "and loss function variants (Focal Loss γ-sweep, Weighted BCE) to address class "
       "imbalance, which is a persistent challenge in DTI prediction.")
bullet("Phase 3 — Self-Supervised Pretraining: implements and evaluates supervised "
       "pretraining on BindingDB followed by fine-tuning on target datasets. This is "
       "the primary mechanism for improving cross-dataset transfer.")
bullet("Phase 4 — Cold-Start and Cross-Dataset Evaluation: assembles the best settings "
       "from Phases 1–3 into a comprehensive evaluation across all four split types and "
       "multiple source–target dataset pairs, including the key BindingDB → yamanishi_e "
       "cross-dataset transfer.")
bullet("Phase 5 — Statistical Ablation: isolates the contribution of each component "
       "and reports significance for all 8 configurations against the Objective 1 baseline.")

body(
    "The minimum viable Objective 2 — embedding size comparison and negative ratio "
    "sweep — can be completed on CPU in approximately 8–12 days. The full Objective 2, "
    "including BindingDB pretraining, requires GPU access. Securing GPU access should "
    "be the first priority action item."
)

callout(
    "Objective 2 does not require changing the model architecture. It requires changing "
    "what the model is initialised with, what it reads as input, and how it is trained "
    "to handle imbalanced data. The modular design of the codebase means each of these "
    "changes can be made with small, targeted modifications to the preprocessing scripts "
    "and the train.py training loop.",
    kind="result"
)

# ══════════════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════════════

out_path = r"paper\Objective2_Analysis_Plan.docx"
doc.save(out_path)
print(f"Saved: {out_path}")
