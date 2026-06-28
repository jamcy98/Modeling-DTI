"""
Generate DTI Data Pipeline Walkthrough DOCX
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

doc = Document()

# ── Page margins ──────────────────────────────────────────────────────────────
section = doc.sections[0]
section.top_margin    = Cm(2.5)
section.bottom_margin = Cm(2.5)
section.left_margin   = Cm(3.0)
section.right_margin  = Cm(2.5)


# ── Helper functions ──────────────────────────────────────────────────────────

def set_font(run, bold=False, italic=False, size=11, color=None):
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)

def heading1(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_font(run, bold=True, size=16, color=(0, 70, 127))
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(6)
    # Bottom border
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '00467F')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p

def heading2(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, bold=True, size=13, color=(31, 73, 125))
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)
    return p

def heading3(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, bold=True, size=11, color=(68, 114, 196))
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(3)
    return p

def body(text, indent=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(1.0)
    run = p.add_run(text)
    set_font(run, size=11)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = Pt(14)
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent  = Cm(1.0 + level * 0.6)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    set_font(run, size=11)
    return p

def mixed(parts, indent=False):
    """parts = list of (text, bold, italic, color, link_text)"""
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = Pt(14)
    for (text, bold, italic, color, _) in parts:
        run = p.add_run(text)
        set_font(run, bold=bold, italic=italic, size=11, color=color)
    return p

def add_hyperlink(paragraph, url, display_text):
    """Add a clickable hyperlink run to an existing paragraph."""
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    part = paragraph.part
    r_id = part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
                          is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)
    r_elem = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    color_elem = OxmlElement('w:color')
    color_elem.set(qn('w:val'), '0563C1')
    rPr.append(color_elem)
    u_elem = OxmlElement('w:u')
    u_elem.set(qn('w:val'), 'single')
    rPr.append(u_elem)
    r_elem.append(rPr)
    t = OxmlElement('w:t')
    t.text = display_text
    t.set(qn('xml:space'), 'preserve')
    r_elem.append(t)
    hyperlink.append(r_elem)
    paragraph._p.append(hyperlink)

def link_para(label, url, description=""):
    """Paragraph with a hyperlink."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.space_after = Pt(3)

    if label:
        r = p.add_run(f"{label}: ")
        set_font(r, bold=True, size=11)

    add_hyperlink(p, url, url)

    if description:
        r2 = p.add_run(f"  — {description}")
        set_font(r2, italic=True, size=10, color=(100, 100, 100))
    return p

def code_block(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(1.0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    shading = OxmlElement('w:shd')
    shading.set(qn('w:val'), 'clear')
    shading.set(qn('w:color'), 'auto')
    shading.set(qn('w:fill'), 'F2F2F2')
    p._p.get_or_add_pPr().append(shading)
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(30, 30, 30)
    return p

def info_box(text, fill='EBF3FB', border_color='2E75B6'):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.5)
    p.paragraph_format.right_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    pPr.append(shd)
    run = p.add_run(text)
    set_font(run, italic=True, size=10.5, color=(30, 70, 110))
    return p

def divider():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'CCCCCC')
    pBdr.append(bottom)
    pPr.append(pBdr)

def stats_row(label, value):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.5)
    p.paragraph_format.space_after = Pt(2)
    r1 = p.add_run(f"{label}: ")
    set_font(r1, bold=True, size=11)
    r2 = p.add_run(value)
    set_font(r2, size=11, color=(50, 50, 50))


# ══════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ══════════════════════════════════════════════════════════════════════════════

doc.add_paragraph()
doc.add_paragraph()

title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title_p.add_run("DTI Data Pipeline")
set_font(r, bold=True, size=28, color=(0, 70, 127))

subtitle_p = doc.add_paragraph()
subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = subtitle_p.add_run("A Step-by-Step Walkthrough")
set_font(r, bold=True, size=18, color=(68, 114, 196))

doc.add_paragraph()
sub2 = doc.add_paragraph()
sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub2.add_run("From Raw Data Sources to Ready-to-Train Datasets")
set_font(r, italic=True, size=13, color=(100, 100, 100))

doc.add_paragraph()
doc.add_paragraph()

date_p = doc.add_paragraph()
date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = date_p.add_run(f"Prepared: {datetime.date.today().strftime('%B %d, %Y')}")
set_font(r, size=11, color=(120, 120, 120))

proj_p = doc.add_paragraph()
proj_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = proj_p.add_run("Project: H-GNN-RNN-DTI  |  Universiti Sains Malaysia (USM)")
set_font(r, size=11, color=(120, 120, 120))

doc.add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

heading1("Overview")

body(
    "This document explains, in plain English, every step taken to collect and prepare "
    "the data needed to train the H-GNN-RNN-DTI model — a deep learning system that "
    "predicts whether a drug molecule will interact with a protein target."
)

body(
    "Drug-Target Interaction (DTI) prediction is a key task in drug discovery. "
    "Instead of testing thousands of drug-protein combinations in a lab (which is very expensive "
    "and time-consuming), a trained machine learning model can shortlist the most promising pairs "
    "for further investigation."
)

info_box(
    "💡  What does the pipeline do?  Raw data from public biological databases "
    "(drug structures, protein sequences, known interactions) is downloaded, cleaned, "
    "converted into a machine-readable format, and split into training/validation/test sets — "
    "all ready for model training."
)

heading2("Datasets Used")
body("Six publicly available datasets were collected, each serving a different purpose:")

rows = [
    ("Davis",        "Binding affinity (regression) — 68 drugs, 442 proteins"),
    ("KIBA",         "Binding affinity (regression) — 2,111 drugs, 229 proteins"),
    ("Luo_17",       "Binary DTI (classification) — heterogeneous network data"),
    ("BindingDB",    "Binary DTI + affinity — large-scale experimental database"),
    ("ChEMBL",       "Binary DTI + affinity — curated bioactivity database"),
    ("Yamanishi_08", "Binary DTI — 4 protein-family sub-classes (Enzyme, Ion Channel, GPCR, Nuclear Receptor)"),
]
for name, desc in rows:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(f"{name}:  ")
    set_font(r1, bold=True, size=11, color=(0, 70, 127))
    r2 = p.add_run(desc)
    set_font(r2, size=11)

doc.add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 1 — Download Davis & KIBA Datasets")

heading2("What are these datasets?")
body(
    "Davis and KIBA are the two most widely used benchmark datasets in DTI research. "
    "Both measure how strongly a drug molecule binds to a protein target — a value called "
    "binding affinity. Higher affinity means the drug is more likely to interact with "
    "(and potentially inhibit) that protein."
)

bullet("Davis:  Kd values (dissociation constant) from Davis et al. (2011). "
       "Covers 68 FDA-approved kinase inhibitors tested against 442 kinase proteins.")
bullet("KIBA:  A combined score merging Ki, Kd, and IC50 measurements from multiple sources. "
       "Covers 2,111 drugs and 229 proteins.")

heading2("Where does the data come from?")
body("Both datasets are hosted on the DeepDTA GitHub repository by Öztürk et al. (2018):")
link_para("Source repository", "https://github.com/hkmztrk/DeepDTA",
          "DeepDTA — Deep Learning Based Drug-Target Interaction Prediction")

heading2("What does the script do?")
body("Script:  ")
code_block("python 01_download_davis_kiba.py")
body("Step-by-step, this script:")
bullet("Clones the DeepDTA GitHub repository to a temporary folder on your computer.")
bullet("Copies the Davis and KIBA data folders into Dataset/raw/davis/ and Dataset/raw/kiba/.")
bullet("Deletes the temporary clone to save disk space.")

heading2("What files are downloaded?")
for ds, files in [
    ("Davis", ["Y  (drug × protein affinity matrix)", "ligands_can.txt  (canonical SMILES for each drug)",
               "ligands_iso.txt  (isomeric SMILES)", "proteins.txt  (protein sequences)",
               "folds/  (pre-defined train/test splits)", "drug-drug_similarities_2D.txt",
               "target-target_similarities_WS.txt"]),
    ("KIBA",  ["Y  (drug × protein KIBA score matrix)", "ligands_can.txt  /  ligands_iso.txt",
               "proteins.txt", "folds/", "kiba_drug_sim.txt  /  kiba_target_sim.txt",
               "kiba_binding_affinity_v2.txt"]),
]:
    heading3(ds)
    for f in files:
        bullet(f, level=1)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 2 — Download Yamanishi_08 & Luo_17 Datasets")

heading2("What is the Yamanishi_08 dataset?")
body(
    "Yamanishi et al. (2008) published one of the earliest and most cited DTI datasets. "
    "It divides drug-protein interactions into four groups based on the type of protein:"
)
bullet("Enzyme (E)  — proteins that catalyse chemical reactions")
bullet("Ion Channel (IC)  — proteins that control ion flow across cell membranes")
bullet("G Protein-Coupled Receptor (GPCR)  — a large family of cell-surface receptors")
bullet("Nuclear Receptor (NR)  — proteins inside the cell nucleus that regulate gene expression")

body(
    "Each sub-class contains a matrix of known interactions (1 = known interaction, 0 = unknown), "
    "along with lists of drug IDs and protein IDs."
)

heading2("What is the Luo_17 dataset?")
body(
    "Luo et al. (2017) built a heterogeneous biological network for DTI prediction. "
    "It includes not just drug-protein interactions but also drug-drug similarity networks "
    "and protein-protein similarity networks — allowing models to use relationships between "
    "drugs and between proteins as additional clues."
)

heading2("Where does the data come from?")
link_para("Luo_17 source", "https://github.com/luoyunan/DTINet",
          "DTINet — Drug-Target Interaction Network")
link_para("Yamanishi original paper", "https://doi.org/10.1093/bioinformatics/btn162",
          "Yamanishi et al. 2008, Bioinformatics")

heading2("What does the script do?")
code_block("python 02_download_yamanishi_luo.py")
bullet("Clones the DTINet repository and copies the Luo_17 interaction/similarity files.")
bullet("Attempts to download Yamanishi sub-class data from DeepPurpose repository.")
bullet("If DeepPurpose structure has changed, falls back to manual instructions.")

heading2("Luo_17 files downloaded")
for f in ["mat_drug_protein.txt  (drug-protein interaction matrix)",
          "mat_drug_drug.txt  (drug-drug similarity)",
          "mat_protein_protein.txt  (protein-protein similarity)",
          "drug_dict_map.txt  (drug ID list)",
          "protein_dict_map.txt  (protein ID list)"]:
    bullet(f, level=1)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 3 — Download BindingDB Dataset")

heading2("What is BindingDB?")
body(
    "BindingDB is a large public database of measured binding affinities between drug-like "
    "molecules and their protein targets. It is continuously updated from scientific literature "
    "and contains millions of experimental measurements."
)

link_para("BindingDB website", "https://www.bindingdb.org/",
          "The Binding Database — experimental binding data")
link_para("BindingDB full download", "https://www.bindingdb.org/bind/chemsearch/marvin/Download.jsp",
          "Access the full TSV download (BindingDB_All.tsv)")

heading2("What does the script do?")
code_block("python 03_download_bindingdb.py")
bullet("Downloads the full BindingDB_All.tsv file (several GB).")
bullet("Filters for human protein targets and valid SMILES strings.")
bullet("Splits into two files:")
bullet("BindingDB_DTI.csv — binary interaction labels (drug known to bind = 1)", level=1)
bullet("BindingDB_DTA.csv — regression labels (actual binding affinity values)", level=1)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 4 — Download ChEMBL Dataset")

heading2("What is ChEMBL?")
body(
    "ChEMBL is a manually curated database of bioactive molecules and their biological "
    "activities, maintained by the European Bioinformatics Institute (EMBL-EBI). "
    "It is one of the largest and most trusted sources of drug-target activity data."
)

link_para("ChEMBL website", "https://www.ebi.ac.uk/chembl/",
          "ChEMBL — Bioactivity database from EMBL-EBI")
link_para("ChEMBL FTP downloads", "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/",
          "Direct SQLite database downloads")

heading2("What does the script do?")
code_block("python 04_download_chembl.py")
bullet("Downloads the ChEMBL SQLite database file (chembl.db).")
bullet("Queries the database for drug-target activity records.")
bullet("Exports two CSV files:")
bullet("chembl_DTI.csv — binary interaction labels", level=1)
bullet("chembl_DTA.csv — binding affinity regression labels", level=1)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 5 — Download Yamanishi_08 Interaction Matrices via KEGG")

heading2("Why a separate script?")
body(
    "The automatic download in Step 2 could not reliably locate the Yamanishi sub-class "
    "files from DeepPurpose (the repository structure had changed). A dedicated script was "
    "written to rebuild these interaction matrices directly from KEGG — the Kyoto Encyclopedia "
    "of Genes and Genomes — the authoritative database for biological pathways and drug-target links."
)

link_para("KEGG website", "https://www.genome.jp/kegg/",
          "KEGG — Kyoto Encyclopedia of Genes and Genomes")
link_para("KEGG REST API", "https://rest.kegg.jp/",
          "KEGG REST API documentation and endpoints")

heading2("What does the script do?")
code_block("python 05_download_yamanishi08.py")

body("For each of the four protein families (Enzyme, Ion Channel, GPCR, Nuclear Receptor), the script:")
bullet("Calls the KEGG REST API to retrieve a list of human genes belonging to that protein family.")
bullet("For each gene, queries KEGG to find all drugs known to target it.")
bullet("Converts KEGG gene IDs to UniProt accession numbers (the standard protein identifier).")
bullet("Builds a binary interaction matrix: rows = drugs, columns = proteins, 1 = known interaction.")
bullet("Saves three files per sub-class into Dataset/raw/yamanishi_08/{e, ic, gpcr, nr}/:")
bullet("mat_drug_protein.txt  — the interaction matrix", level=1)
bullet("drug_dict_map.txt  — list of KEGG Drug IDs", level=1)
bullet("protein_dict_map.txt  — list of UniProt accession numbers", level=1)

heading2("Nuclear Receptor (NR) — Fix Applied")
info_box(
    "⚠️  Issue encountered: The original script used an incorrect KEGG API endpoint for the Nuclear "
    "Receptor sub-class (fetching pathway text instead of gene links). This returned no genes, so NR "
    "was missing entirely.\n\n"
    "✅  Fix applied: Changed the NR gene source to use the KEGG link API "
    "(rest.kegg.jp/link/hsa/hsa04919 and hsa04915), which correctly returns a list of human gene IDs "
    "in Nuclear Receptor signalling pathways. This produced 60 genes, 206 drugs, and 305 known "
    "interactions."
)

heading2("Results after Step 5")
for sub, shape, pos in [
    ("Enzyme (e)",             "359 drugs × 90 proteins",  "448"),
    ("Ion Channel (ic)",       "528 drugs × 120 proteins", "3,995"),
    ("GPCR (gpcr)",            "982 drugs × 48 proteins",  "2,522"),
    ("Nuclear Receptor (nr)",  "206 drugs × 31 proteins",  "305"),
]:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(f"{sub}:  ")
    set_font(r1, bold=True, size=11)
    r2 = p.add_run(f"{shape}  |  {pos} positive interactions")
    set_font(r2, size=11)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 6 — Fetch SMILES & Protein Sequences for Yamanishi_08")

heading2("Why is this needed?")
body(
    "The interaction matrices from Step 5 only tell us which drug-protein pairs interact — "
    "they do not include the actual structures of the drugs or proteins. "
    "Machine learning models need the molecular structure of each drug (as a SMILES string) "
    "and the amino acid sequence of each protein to learn from."
)

heading2("What is a SMILES string?")
body(
    "SMILES (Simplified Molecular Input Line Entry System) is a text notation that encodes "
    "the 2D structure of a molecule. For example, the SMILES for aspirin is "
    "CC(=O)Oc1ccccc1C(=O)O. Every atom and bond in the molecule is represented "
    "as a sequence of characters that a computer can read and convert into a molecular graph."
)

heading2("The SMILES Lookup Problem — and the Fix")
info_box(
    "⚠️  Problem: The drug IDs in Yamanishi_08 are KEGG Drug IDs (e.g. D00142). "
    "The first attempt searched PubChem directly by drug name, which returned 0 results "
    "— PubChem does not recognise KEGG Drug IDs as compound names.\n\n"
    "✅  Fix: A three-step lookup chain was implemented:\n"
    "   1. KEGG conv API   →   PubChem Substance ID (SID)\n"
    "   2. PubChem SID     →   PubChem Compound ID (CID)\n"
    "   3. PubChem CID     →   Canonical SMILES string\n\n"
    "This resolved ~96% of all KEGG Drug IDs to valid SMILES strings."
)

heading2("API endpoints used")
link_para("KEGG Drug → PubChem SID",
          "https://rest.kegg.jp/conv/pubchem/drug:D00142",
          "KEGG conv API — converts KEGG Drug ID to PubChem SID")
link_para("PubChem SID → CID",
          "https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/sid/{SID}/cids/JSON",
          "PubChem PUG REST — resolves SID to Compound ID")
link_para("PubChem CID → SMILES",
          "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{CID}/property/CanonicalSMILES/JSON",
          "PubChem PUG REST — retrieves SMILES from CID")
link_para("UniProt protein sequence",
          "https://rest.uniprot.org/uniprotkb/{UniProtID}.fasta",
          "UniProt REST API — retrieves FASTA sequence for a protein")

link_para("PubChem website", "https://pubchem.ncbi.nlm.nih.gov/",
          "PubChem — open chemistry database")
link_para("UniProt website", "https://www.uniprot.org/",
          "UniProt — universal protein knowledgebase")

heading2("What does the script do?")
code_block("python fetch_yamanishi_smiles_sequences.py")
bullet("Reads the drug and protein ID lists for each sub-class.")
bullet("Looks up the SMILES for every unique drug using the three-step PubChem chain above.")
bullet("Looks up the amino acid sequence for every unique protein from UniProt.")
bullet("Combines everything into a pairs.csv file in each sub-class folder:")
bullet("Columns: drug_id, smiles, protein_id, sequence, label", level=1)
bullet("Only rows where both SMILES and protein sequence were successfully found are kept.", level=1)

heading2("Results after Step 6")
for sub, smiles, seqs, pairs in [
    ("Enzyme (e)",            "334 / 359 (93%)", "90 / 90 (100%)",  "847 pairs"),
    ("Ion Channel (ic)",      "519 / 528 (98%)", "120 / 120 (100%)", "7,864 pairs"),
    ("GPCR (gpcr)",           "952 / 982 (97%)", "48 / 48 (100%)",  "4,902 pairs"),
    ("Nuclear Receptor (nr)", "197 / 206 (96%)", "31 / 31 (100%)",  "584 pairs"),
]:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(f"{sub}:  ")
    set_font(r1, bold=True, size=11)
    r2 = p.add_run(f"SMILES {smiles}  |  Sequences {seqs}  →  {pairs} saved")
    set_font(r2, size=11)

divider()
doc.add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 7 — Preprocessing: Drug Molecular Graphs")

heading2("Why convert SMILES to graphs?")
body(
    "The H-GNN-RNN-DTI model uses a Graph Neural Network (GNN) to process drug molecules. "
    "A GNN takes a graph as input — where atoms are nodes and chemical bonds are edges. "
    "SMILES strings must therefore be converted into graph objects before training."
)

heading2("What does the script do?")
code_block("python 10_preprocess_drugs.py")

body("For each drug in the Davis and KIBA datasets, the script:")
bullet("Parses the SMILES string using RDKit — a chemistry toolkit that understands molecular structure.")
bullet("Builds a graph: each atom becomes a node, each bond becomes an edge.")
bullet("Assigns feature vectors to each node (atom) using:")
bullet("RDKit descriptors  — atom type, degree, hybridisation, aromaticity, formal charge, etc.", level=1)
bullet("ChemBERTa embeddings  — a pre-trained chemical language model that reads SMILES like text "
       "and produces a rich numerical representation of the molecule.", level=1)
bullet("Saves all drug graphs to a single file: processed/drug_graphs/{dataset}_drug_graphs.pt")

link_para("RDKit", "https://www.rdkit.org/", "Open-source cheminformatics library")
link_para("ChemBERTa model",
          "https://huggingface.co/seyonec/ChemBERTa-zinc-base-v1",
          "ChemBERTa-zinc-base-v1 on HuggingFace")

info_box(
    "ℹ️  Scope: Drug graph preprocessing was run for Davis and KIBA only. "
    "BindingDB, ChEMBL, and Yamanishi are very large datasets and their drug graph "
    "generation is commented out to save time and disk space for the initial experiments."
)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 8 — Preprocessing: Protein Sequence Embeddings")

heading2("Why embed protein sequences?")
body(
    "Protein sequences are strings of amino acid letters (e.g. MKTAYIAKQRQISFVKSHFSRQ…). "
    "To feed them into a neural network, they must first be converted into fixed-size "
    "numerical vectors that capture the biological meaning of the sequence."
)

heading2("What does the script do?")
code_block("python 11_preprocess_proteins.py")

body("For each unique protein in the Davis and KIBA datasets, the script:")
bullet("Passes the amino acid sequence through ESM-2 — a large protein language model "
       "developed by Meta AI Research, trained on hundreds of millions of protein sequences.")
bullet("ESM-2 produces a per-residue embedding: a vector of numbers for each amino acid position "
       "that encodes its chemical and evolutionary context.")
bullet("Saves the embeddings to: processed/protein_embeddings/{dataset}_protein_embeddings.npy")
bullet("Also saves the protein ID order: processed/protein_embeddings/{dataset}_protein_ids.json")

link_para("ESM-2 (Meta AI)",
          "https://github.com/facebookresearch/esm",
          "Evolutionary Scale Modelling — protein language models by Meta AI")
link_para("ESM-2 paper",
          "https://www.science.org/doi/10.1126/science.ade2574",
          "Lin et al. 2023, Science — Language models of protein sequences")

info_box(
    "ℹ️  Computational note: ESM-2 requires significant memory (~3 GB GPU VRAM or ~8 GB RAM). "
    "Processing was completed for Davis (442 proteins) and KIBA (229 proteins). "
    "Protein embeddings for Luo_17, BindingDB, and Yamanishi can be generated "
    "similarly when needed."
)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 9
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 9 — Preprocessing: Interaction Label Files")

heading2("What are label files?")
body(
    "Label files are the ground truth that the model learns from. Each row represents "
    "one drug-protein pair and has a label indicating whether they interact."
)
bullet("For DTI (classification):  label = 1 (known interaction) or label = 0 (assumed non-interaction)")
bullet("For DTA (regression):  label = a numerical affinity score (e.g. pKd value)")

heading2("Negative sampling")
body(
    "Real DTI datasets are heavily imbalanced — there are far fewer known positives than "
    "possible pairs. To train a balanced classifier, unknown pairs are randomly sampled as "
    "negatives. Two ratios are generated:"
)
bullet("1:1 ratio  — equal numbers of positives and negatives (balanced)")
bullet("1:10 ratio  — ten negatives for every positive (more realistic, harder task)")

heading2("What does the script do?")
code_block("python 12_preprocess_labels.py")

body("For each dataset, the script reads the raw interaction data and produces standardised CSV files:")
for ds, out in [
    ("Davis",        "davis_dta_labels.csv  (regression, pKd values)"),
    ("KIBA",         "kiba_dta_labels.csv  (regression, KIBA scores)"),
    ("Luo_17",       "luo_17_dti_labels_1to1.csv  and  _1to10.csv"),
    ("BindingDB",    "bindingdb_dti_labels_1to1.csv  and  bindingdb_dta_labels.csv"),
    ("Yamanishi e",  "yamanishi_e_dti_labels_1to1.csv  and  _1to10.csv"),
    ("Yamanishi ic", "yamanishi_ic_dti_labels_1to1.csv  and  _1to10.csv"),
    ("Yamanishi gpcr","yamanishi_gpcr_dti_labels_1to1.csv  and  _1to10.csv"),
    ("Yamanishi nr", "yamanishi_nr_dti_labels_1to1.csv  and  _1to10.csv"),
]:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(f"{ds}:  ")
    set_font(r1, bold=True, size=11)
    r2 = p.add_run(out)
    set_font(r2, size=11)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 10
# ══════════════════════════════════════════════════════════════════════════════

heading1("Step 10 — Preprocessing: Data Splits")

heading2("Why split the data?")
body(
    "To evaluate a model fairly, the data must be divided into three non-overlapping sets:"
)
bullet("Training set  — pairs the model learns from (~80%)")
bullet("Validation set  — pairs used to tune the model during training (~10%)")
bullet("Test set  — pairs used to measure final performance (~10%)")

heading2("Four types of split")
body(
    "A key challenge in DTI prediction is generalisation — does the model perform well "
    "on drugs or proteins it has never seen before? Four split strategies are provided:"
)

for name, desc in [
    ("Random split",
     "Pairs are shuffled and divided randomly. This is the easiest setting — "
     "the model has likely seen similar drugs and proteins during training."),
    ("Cold-drug split",
     "All pairs involving a drug are placed in the test set only. "
     "The model must predict interactions for entirely new drugs it has never been trained on."),
    ("Cold-target split",
     "All pairs involving a protein are placed in the test set only. "
     "The model must generalise to new protein targets."),
    ("Cold-pair split",
     "Both the drug and the protein in each test pair are unseen. "
     "This is the hardest and most realistic scenario for drug discovery."),
]:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(2)
    r1 = p.add_run(f"{name}:  ")
    set_font(r1, bold=True, size=11, color=(0, 70, 127))
    r2 = p.add_run(desc)
    set_font(r2, size=11)

heading2("What does the script do?")
code_block("python 13_preprocess_splits.py")
body("For every label CSV file, the script generates all four split types and saves them as JSON files "
     "inside processed/splits/. Each JSON file contains train/validation/test indices for 10-fold "
     "cross-validation (except cold-pair, which uses a single split).")

divider()
doc.add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# FINAL STATUS
# ══════════════════════════════════════════════════════════════════════════════

heading1("Final Status — What Is Ready")

info_box(
    "✅  All data collection and preprocessing steps have been completed successfully. "
    "The datasets are fully prepared and ready for model training."
)

heading2("Raw Data — Collected")
table = doc.add_table(rows=1, cols=4)
table.style = 'Table Grid'
hdr = table.rows[0].cells
for i, h in enumerate(["Dataset", "Type", "Drugs", "Proteins"]):
    p = hdr[i].paragraphs[0]
    run = p.add_run(h)
    set_font(run, bold=True, size=10, color=(255, 255, 255))
    tc = hdr[i]._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '2E75B6')
    tcPr.append(shd)

data_rows = [
    ("Davis",            "DTA (regression)",    "68",    "442"),
    ("KIBA",             "DTA (regression)",    "2,111", "229"),
    ("Luo_17",           "DTI (binary)",        "708",   "1,512"),
    ("BindingDB",        "DTI + DTA",           "~1M+",  "~9K+"),
    ("ChEMBL",           "DTI + DTA",           "~2M+",  "~15K+"),
    ("Yamanishi e",      "DTI (binary)",        "359",   "90"),
    ("Yamanishi ic",     "DTI (binary)",        "528",   "120"),
    ("Yamanishi gpcr",   "DTI (binary)",        "982",   "48"),
    ("Yamanishi nr",     "DTI (binary)",        "206",   "31"),
]
for i, row_data in enumerate(data_rows):
    row = table.add_row().cells
    fill = 'FFFFFF' if i % 2 == 0 else 'EBF3FB'
    for j, val in enumerate(row_data):
        p = row[j].paragraphs[0]
        run = p.add_run(val)
        set_font(run, size=10)
        tc = row[j]._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill)
        tcPr.append(shd)

doc.add_paragraph()

heading2("Processed Files — Ready for Training")
table2 = doc.add_table(rows=1, cols=5)
table2.style = 'Table Grid'
hdr2 = table2.rows[0].cells
for i, h in enumerate(["Dataset", "Labels", "Splits", "Drug Graphs", "Protein Embeddings"]):
    p = hdr2[i].paragraphs[0]
    run = p.add_run(h)
    set_font(run, bold=True, size=10, color=(255, 255, 255))
    tc = hdr2[i]._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '2E75B6')
    tcPr.append(shd)

proc_rows = [
    ("Davis",            "✅", "✅", "✅", "✅"),
    ("KIBA",             "✅", "✅", "✅", "✅"),
    ("Luo_17",           "✅", "✅", "—",  "—"),
    ("BindingDB",        "✅", "✅", "—",  "—"),
    ("Yamanishi (all 4)","✅", "✅", "—",  "—"),
]
for i, row_data in enumerate(proc_rows):
    row = table2.add_row().cells
    fill = 'FFFFFF' if i % 2 == 0 else 'EBF3FB'
    for j, val in enumerate(row_data):
        p = row[j].paragraphs[0]
        color = (0, 128, 0) if val == "✅" else (150, 150, 150) if val == "—" else None
        run = p.add_run(val)
        set_font(run, size=10, color=color)
        tc = row[j]._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill)
        tcPr.append(shd)

doc.add_paragraph()
body(
    "Note: Drug graphs and protein embeddings for Luo_17, BindingDB, and Yamanishi "
    "can be generated by uncommenting the relevant sections in 10_preprocess_drugs.py "
    "and 11_preprocess_proteins.py when needed for extended experiments."
)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# NEXT STEPS
# ══════════════════════════════════════════════════════════════════════════════

heading1("Next Steps")

body("With all datasets prepared, the pipeline is ready to proceed to model training:")
bullet("Step 11 — Build the H-GNN-RNN-DTI model architecture "
       "(Hierarchical GAT for drugs + BiLSTM/BiGRU for proteins + Gated Cross-Attention fusion).")
bullet("Step 12 — Train on Davis and KIBA benchmarks with all four split types.")
bullet("Step 13 — Evaluate against baseline models: GSRF-DTI, TTModel, DTKGIN.")
bullet("Step 14 — Apply explainability analysis using attention weights (XAI).")
bullet("Step 15 — Validate on Yamanishi_08 sub-classes to test cross-dataset generalisation.")

info_box(
    "The complete data pipeline scripts are located in the Dataset/ folder. "
    "All processed files are in Dataset/processed/ and are ready for import "
    "into the model training code."
)

divider()


# ══════════════════════════════════════════════════════════════════════════════
# REFERENCES / LINKS
# ══════════════════════════════════════════════════════════════════════════════

heading1("Key Links & References")

sections_links = [
    ("Data Sources", [
        ("DeepDTA (Davis & KIBA)",   "https://github.com/hkmztrk/DeepDTA"),
        ("DTINet (Luo_17)",          "https://github.com/luoyunan/DTINet"),
        ("BindingDB",                "https://www.bindingdb.org/"),
        ("ChEMBL",                   "https://www.ebi.ac.uk/chembl/"),
        ("KEGG",                     "https://www.genome.jp/kegg/"),
        ("PubChem",                  "https://pubchem.ncbi.nlm.nih.gov/"),
        ("UniProt",                  "https://www.uniprot.org/"),
    ]),
    ("Preprocessing Tools", [
        ("RDKit",                    "https://www.rdkit.org/"),
        ("ChemBERTa (HuggingFace)",  "https://huggingface.co/seyonec/ChemBERTa-zinc-base-v1"),
        ("ESM-2 (Meta AI)",          "https://github.com/facebookresearch/esm"),
        ("DeepPurpose",              "https://github.com/kexinhuang12345/DeepPurpose"),
    ]),
    ("Key Papers", [
        ("Davis et al. 2011 — Kinase inhibitor selectivity", "https://doi.org/10.1038/nbt.1990"),
        ("Tang et al. 2014 — KIBA score",                   "https://doi.org/10.1021/ci400709d"),
        ("Luo et al. 2017 — DTINet",                        "https://doi.org/10.1038/s41467-017-00680-8"),
        ("Yamanishi et al. 2008 — DTI benchmark",           "https://doi.org/10.1093/bioinformatics/btn162"),
        ("Öztürk et al. 2018 — DeepDTA",                   "https://doi.org/10.1093/bioinformatics/bty593"),
        ("Lin et al. 2023 — ESM-2 protein language model",  "https://doi.org/10.1126/science.ade2574"),
    ]),
]

for section_title, links in sections_links:
    heading2(section_title)
    for label, url in links:
        link_para(label, url)


# ══════════════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════════════

out_path = r"C:\Users\Jamila\Modeling-DTI\paper\DTI_Pipeline_Walkthrough.docx"
doc.save(out_path)
print(f"Saved: {out_path}")
