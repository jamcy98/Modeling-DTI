// Part 1: Helpers + Title + Abstract + Introduction + Background + Math
import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, PageBreak,
  ShadingType
} from 'docx';
import fs from 'fs';

export const FONT = 'Times New Roman';
export const CODE = 'Courier New';
export const SZ = 24; // 12pt
export const SZ_SM = 20; // 10pt
export const SZ_LG = 32; // 16pt

export function p(text, opts = {}) {
  const { bold=false, italic=false, center=false, sz=SZ, noIndent=false } = opts;
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: sz, bold, italics: italic })],
    alignment: center ? AlignmentType.CENTER : AlignmentType.JUSTIFIED,
    spacing: { before: 100, after: 100, line: 360 },
    indent: noIndent ? {} : { firstLine: 720 }
  });
}

export function pRuns(runs, opts = {}) {
  const { center=false, noIndent=false } = opts;
  return new Paragraph({
    children: runs,
    alignment: center ? AlignmentType.CENTER : AlignmentType.JUSTIFIED,
    spacing: { before: 100, after: 100, line: 360 },
    indent: noIndent ? {} : { firstLine: 720 }
  });
}

export function tr(text, opts = {}) {
  const { bold=false, italic=false, sz=SZ } = opts;
  return new TextRun({ text, font: FONT, size: sz, bold, italics: italic });
}

export function eq(text, label='') {
  return new Paragraph({
    children: [
      new TextRun({ text: '    ' + text, font: CODE, size: SZ }),
      ...(label ? [new TextRun({ text: '   ' + label, font: FONT, size: SZ, italics: true })] : [])
    ],
    alignment: AlignmentType.LEFT,
    spacing: { before: 80, after: 80 },
    indent: { left: 720 }
  });
}

export function h1(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 32, bold: true })],
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    spacing: { before: 480, after: 240 }
  });
}

export function h2(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 28, bold: true })],
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 360, after: 180 }
  });
}

export function h3(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 24, bold: true })],
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 120 }
  });
}

export function h4(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 24, bold: true, italics: true })],
    spacing: { before: 180, after: 80 }
  });
}

export function bul(text, lvl=0) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: SZ })],
    bullet: { level: lvl },
    spacing: { before: 60, after: 60 },
    indent: { left: 720 * (lvl + 1) }
  });
}

export function sp() {
  return new Paragraph({ children: [new TextRun({ text: '' })], spacing: { before: 60, after: 60 } });
}

export function pb() {
  return new Paragraph({ children: [new PageBreak()], spacing: { before: 0, after: 0 } });
}

export function cap(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: SZ_SM, bold: true, italics: true })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 200 }
  });
}

export function ascii(lines) {
  return lines.map(l => new Paragraph({
    children: [new TextRun({ text: l, font: CODE, size: 18 })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0 }
  }));
}

export function createTable(headers, rows, colW) {
  const makeTC = (text, isHdr, idx) => new TableCell({
    children: [new Paragraph({
      children: [new TextRun({ text: String(text ?? '—'), font: FONT, size: isHdr ? 18 : 16, bold: isHdr })],
      spacing: { before: 40, after: 40 }
    })],
    width: colW ? { size: colW[idx], type: WidthType.DXA } : { size: Math.floor(9360 / headers.length), type: WidthType.DXA },
    shading: isHdr ? { fill: 'BFBFBF', type: ShadingType.CLEAR } : undefined,
    margins: { top: 40, bottom: 40, left: 60, right: 60 }
  });

  return new Table({
    rows: [
      new TableRow({ children: headers.map((h, i) => makeTC(h, true, i)), tableHeader: true }),
      ...rows.map((row, ri) => new TableRow({
        children: row.map((cell, ci) => {
          const tc = makeTC(cell, false, ci);
          return tc;
        })
      }))
    ],
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2 },
      bottom: { style: BorderStyle.SINGLE, size: 2 },
      left: { style: BorderStyle.SINGLE, size: 1 },
      right: { style: BorderStyle.SINGLE, size: 1 },
      insideH: { style: BorderStyle.SINGLE, size: 1 },
      insideV: { style: BorderStyle.SINGLE, size: 1 }
    }
  });
}

// ============================================================
// SECTION: TITLE PAGE
// ============================================================
export const titlePage = [
  sp(), sp(), sp(),
  new Paragraph({
    children: [new TextRun({ text: 'A Comprehensive Review of Hybrid Deep Learning Approaches for Drug–Target Interaction Prediction: Architectures, Fusion Mechanisms, and Evaluation Frameworks', font: FONT, size: 32, bold: true })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 480 }
  }),
  new Paragraph({ children: [new TextRun({ text: 'Jamila Abdul-Hadi', font: FONT, size: 26, bold: true })], alignment: AlignmentType.CENTER, spacing: { after: 120 } }),
  new Paragraph({ children: [new TextRun({ text: 'School of Computer Sciences, Universiti Sains Malaysia, 11800 Penang, Malaysia', font: FONT, size: 22, italics: true })], alignment: AlignmentType.CENTER, spacing: { after: 100 } }),
  new Paragraph({ children: [new TextRun({ text: 'Supervisor: Assoc. Prof. Dr. Nurul Hashimah Ahamed Hassain Malim', font: FONT, size: 22, italics: true })], alignment: AlignmentType.CENTER, spacing: { after: 100 } }),
  new Paragraph({ children: [new TextRun({ text: 'Correspondence: jamcy98@gmail.com', font: FONT, size: 22 })], alignment: AlignmentType.CENTER, spacing: { after: 360 } }),
  new Paragraph({ children: [new TextRun({ text: 'Date: May 2026', font: FONT, size: 22 })], alignment: AlignmentType.CENTER, spacing: { after: 360 } }),
  pb()
];

// ============================================================
// SECTION: ABSTRACT
// ============================================================
export const abstractSection = [
  h1('Abstract'),
  p('Drug–target interaction (DTI) prediction is a cornerstone of modern computational drug discovery. Over the past decade, the field has evolved from physics-based molecular docking and ligand similarity methods through classical machine learning to sophisticated hybrid multimodal deep learning frameworks. This review provides a systematic and critical analysis of over thirty prominent DTI prediction models, organized by architectural paradigm: CNN-based, GNN-based, RNN-based, Transformer-based, knowledge graph-based, and hybrid multimodal approaches. For each model category and individual model, we present conceptual architecture sketches, key mathematical formulations, benchmark performance data, and critical limitation analysis. We construct four comparative tables covering model taxonomy, benchmark performance across established datasets (DAVIS, KIBA, BindingDB, Yamanishi_08, Luo_17), cold-start generalization (warm, cold-drug, cold-target settings), and interpretability mechanisms. Recurring limitations across the literature include static cross-modal feature fusion, inadequate cold-start generalization, data imbalance, and black-box predictions. We synthesize these into a structured research gap analysis and propose future directions centered on dynamic gated attention fusion, foundation model integration, multimodal self-supervised pretraining, and biologically grounded interpretability. The proposed H-GNN-RNN-DTI architecture (Abdul-Hadi, 2025) is analyzed as a representative next-generation framework that addresses these gaps through a novel Gated Cross-Attention mechanism, imbalance-aware training, and intrinsic attention-based interpretability.', { noIndent: true }),
  sp(),
  p('Keywords: drug–target interaction, graph neural network, recurrent neural network, hybrid deep learning, cross-modal attention, cold-start generalization, molecular graph, protein sequence, interpretability, drug discovery.', { noIndent: true }),
  pb()
];

// ============================================================
// SECTION 1: INTRODUCTION
// ============================================================
export const introSection = [
  h1('1. Introduction'),
  p('Identifying interactions between small-molecule drugs and their biological target proteins is fundamental to modern drug discovery. Accurate drug–target interaction (DTI) prediction accelerates target identification, lead optimization, drug repurposing, and adverse effect characterization. Conventional drug development from compound identification to clinical approval spans 10–15 years at costs exceeding $2.6 billion per approved therapy (Khojasteh et al., 2023; Tanoli et al., 2025), motivating computational approaches that prioritize candidates before resource-intensive laboratory validation.'),
  p('Early computational methods included molecular docking—simulating physical binding via scoring functions—and ligand-based QSAR models. These suffer from high computational cost, 3D structure dependence, and inability to handle novel scaffolds (Lu et al., 2025; Lee et al., 2024). Classical machine learning with hand-crafted molecular fingerprints improved scalability but required extensive feature engineering and struggled with data sparsity (He et al., 2017; Shi et al., 2019; Dhannoon, 2024). Deep learning transformed the field by enabling automatic, end-to-end feature extraction: CNNs from character-level sequence encodings (DeepDTA; Öztürk et al., 2018); GNNs from molecular topology (GraphDTA; Nguyen et al., 2021); RNNs from protein primary sequences (GDGRU-DTA; Zhijian et al., 2022); and Transformers from long-range context (TransformerCPI; Chen et al., 2020).'),
  p('The dominant paradigm is now hybrid multimodal architecture, which integrates complementary drug and protein encoders with cross-modal fusion. Drug–target binding is inherently a cross-modal phenomenon: molecular topology determines which binding pocket a compound occupies, while protein sequence and fold determine pocket geometry. Single-modality models produce incomplete representations—a feature bottleneck—that limits predictive accuracy (Yang et al., 2024; Zuo et al., 2025). Hybrid models pairing GNNs for drug encoding with RNNs or Transformers for protein encoding have achieved state-of-the-art performance.'),
  p('Despite progress, four critical challenges persist. First, many models employ static, concatenation-based fusion that fails to capture fine-grained cross-modal interactions between drug substructures and protein residues (Zhu et al., 2024; Sun et al., 2024). Second, cold-start generalization—predicting DTIs for novel drugs or targets—degrades severely due to data sparsity and distribution shift (Minh et al., 2022; Talo & Bozdag, 2025). Third, model interpretability remains limited, restricting utility in structure–activity relationship (SAR) studies (Panahandeh & Mansouri, 2025; Vefghi et al., 2025). Fourth, severe class imbalance (few known positives vs. vast unknown pairs) introduces systematic prediction bias (Bagherian et al., 2021; Suruliandi et al., 2024).'),
  p('This review makes the following contributions:'),
  bul('A systematic taxonomy tracing DTI computational methodology from molecular docking to hybrid deep learning.'),
  bul('Critical reviews of 36 models organized by architectural paradigm with mathematical formulations, architecture conceptual sketches, and limitation analysis.'),
  bul('Four comparative tables: model taxonomy, benchmark performance (DAVIS, KIBA, BindingDB, Yamanishi_08, Luo_17), cold-start evaluation (S1/S2/S3), and interpretability features.'),
  bul('A structured synthesis of research gaps and future research directions.'),
  bul('Contextual positioning of the proposed H-GNN-RNN-DTI architecture as a next-generation response to identified limitations.'),
  pb()
];

// ============================================================
// SECTION 2: BACKGROUND
// ============================================================
export const backgroundSection = [
  h1('2. Background'),
  h2('2.1 Biological Foundations'),
  p('Drug–target interactions describe non-covalent binding events between small-molecule drugs and protein macromolecules. Binding affinity, quantified as dissociation constant K_d, inhibitory constant K_i, or half-maximal inhibitory concentration IC₅₀, governs therapeutic efficacy. DTI prediction tasks are cast as either binary classification (interaction vs. no interaction) or regression (affinity value estimation, e.g., pK_d = −log₁₀(K_d)). Target protein classes include enzymes, ion channels, G-protein coupled receptors (GPCRs), nuclear receptors, and transporter proteins—categories formalized in the Yamanishi_08 benchmark.'),
  p('Drug molecules are canonically encoded as SMILES strings or molecular graphs G = (V, E), where V represents atoms as nodes with feature vectors (atomic number, valence, aromaticity, formal charge, hybridization) and E represents covalent bonds as edges with features (bond type, conjugation, ring membership). Protein primary sequences are encoded as ordered amino acid strings x = (x₁, x₂, ..., x_T), where T may range from tens to thousands of residues.'),
  h2('2.2 Taxonomy of Computational DTI Methods'),
  p('Five generations of computational DTI methodology have emerged, each addressing predecessor limitations:'),
  h3('2.2.1 Molecular Docking'),
  p('Physics-based simulation of drug–protein binding geometry using force-field scoring functions (AutoDock Vina, Glide). Provides atomistic binding pose predictions but requires high-resolution 3D protein structures, costs hours per compound, and cannot scale to millions of candidates (Dai et al., 2025; Lu et al., 2025).'),
  h3('2.2.2 Ligand-Based and QSAR Methods'),
  p('Infer activity from molecular similarity to known active compounds using fingerprints (ECFP, MACCS) and QSAR descriptors. Eliminates structure dependence but fails for targets with sparse known binders (cold-start) and cannot generalize to novel chemotypes (Lee et al., 2024; Chen et al., 2016).'),
  h3('2.2.3 Classical Machine Learning and Network-Based Methods'),
  p('SVMs, Random Forests, Gradient Boosting, and Multilayer Perceptrons applied to hand-crafted molecular descriptors and protein physicochemical features. Network-based methods exploit heterogeneous biological network topology via random walks, matrix factorization, and label propagation but suffer from cold-start for novel entities (Wu et al., 2018; Cao et al., 2024; Xuan et al., 2019).'),
  h3('2.2.4 Deep Learning Models'),
  p('End-to-end feature learning from raw biological data eliminates manual feature engineering. CNNs (DeepDTA), GNNs (GraphDTA), RNNs (GDGRU-DTA), and Transformers (TransformerCPI, MolTrans) each capture distinct aspects of molecular and sequence information but face limitations as single-modality encoders (Vefghi et al., 2025; Panahandeh & Mansouri, 2025).'),
  h3('2.2.5 Hybrid Multimodal Deep Learning'),
  p('The current state of the art combines GNNs for drug topology with RNNs, CNNs, or Transformers for protein sequences, fusing modalities through concatenation, attention, bilinear interaction, or gated mechanisms. Foundation model embeddings (ChemBERTa for drugs, ESM-2/ProtT5 for proteins) pre-trained on large corpora further improve cold-start generalization. Interpretability mechanisms—attention visualization, Grad-CAM, mutual attribution—are integrated to support SAR analysis (Talo & Bozdag, 2025; Sun et al., 2024; Yuan et al., 2025).'),
  h2('2.3 Benchmark Datasets'),
  p('The following datasets are used as evaluation benchmarks across the reviewed literature:', { noIndent: true }),
  bul('DAVIS: 30,056 K_d measurements for 442 kinases and 68 inhibitors. Standard DTA regression benchmark (CI, RMSE). Widely used since BindingDB splits may yield optimistic results.'),
  bul('KIBA: 52,498 bioactivity values integrating K_i, K_d, IC₅₀ across 467 targets and 229 drugs. DTA regression benchmark.'),
  bul('BindingDB: Millions of binding affinities across diverse targets. Used for large-scale training and generalizability testing (BindingDB-random, BindingDB-cold-drug, BindingDB-cold-target splits).'),
  bul('ChEMBL: Comprehensive manually curated bioactivity database (~2M compounds). Used for pretraining and large-scale experiments.'),
  bul('Yamanishi_08: Gold-standard binary DTI dataset with four target classes (enzyme: 664 pairs, ion channel: 1476 pairs, GPCR: 635 pairs, nuclear receptor: 90 pairs). Widely used for cold-start evaluation (S1 warm, S2 cold-drug, S3 cold-target).'),
  bul('Luo_17: Larger heterogeneous network DTI dataset integrating drug–drug, protein–protein, and DTI networks (1,923 drugs, 3,770 targets, 37,554 interactions). Used in GSRF-DTI and network-based benchmarks.'),
  bul('DrugBank: Curated database of approved and experimental drugs with annotated targets. Used for feature sourcing, generalizability testing, and pretraining.'),
  pb()
];

// ============================================================
// SECTION 3: MATHEMATICAL FOUNDATIONS
// ============================================================
export const mathSection = [
  h1('3. Mathematical Foundations'),
  h2('3.1 Graph Neural Network Formulations'),
  p('Let G = (V, E) be a molecular graph with atom node set V and bond edge set E. Node v has initial feature vector hᵥ⁻⁻⁻⁻ = h_v⁰. GNNs iterate message passing across L layers:', { noIndent: true }),
  h3('3.1.1 General Message Passing Framework'),
  eq('m_v^(l) = AGGREGATE^(l)( { h_u^(l-1), e_uv : u in N(v) } )', '... (1)'),
  eq('h_v^(l) = UPDATE^(l)( h_v^(l-1), m_v^(l) )', '... (2)'),
  p('where N(v) is the neighborhood of v, e_uv are edge features, and l is the layer index.', { noIndent: true }),
  h3('3.1.2 Graph Convolutional Network (GCN)'),
  eq('H^(l+1) = sigma( D~^(-1/2) A~ D~^(-1/2) H^(l) W^(l) )', '... (3)'),
  p('where A~ = A + I_N (adjacency with self-loops), D~ is the diagonal degree matrix of A~, W^(l) is a learnable weight matrix, and sigma is a nonlinear activation (Kipf & Welling, 2017). GCN performs symmetric normalization of neighbor aggregation.', { noIndent: true }),
  h3('3.1.3 Graph Attention Network (GAT)'),
  eq('e_ij = LeakyReLU( a^T [W h_i || W h_j] )', '... (4)'),
  eq('alpha_ij = exp(e_ij) / SUM_{k in N(i)} exp(e_ik)', '... (5)'),
  eq('h_v^(l+1) = sigma( SUM_{j in N(v)} alpha_vj * W * h_j^(l) )', '... (6)'),
  p('where a is a learnable attention vector, W is a weight matrix, and || denotes vector concatenation. Multi-head GAT computes K parallel attention functions and concatenates their outputs (Velickovic et al., 2018). H-GNN-RNN-DTI employs a hierarchical variant (H-GAT) with 3 layers and 8 attention heads per layer.', { noIndent: true }),
  h3('3.1.4 GraphSAGE'),
  eq('h_v^(l) = sigma( W^(l) * [ h_v^(l-1) || MEAN_{u in N(v)} h_u^(l-1) ] )', '... (7)'),
  p('Concatenates ego representation with mean of neighbor representations, enabling inductive learning (Hamilton et al., 2017). Employed by GSRF-DTI for drug–target pair network encoding.', { noIndent: true }),
  h3('3.1.5 Graph Readout (Attention Pooling)'),
  eq('h_G = SUM_{v in V} softmax( w^T h_v^(L) ) * h_v^(L)', '... (8)'),
  p('Maps node embeddings to a graph-level representation through attention-weighted pooling. H-GNN-RNN-DTI applies this readout followed by an MLP to produce the drug embedding z_d.', { noIndent: true }),
  h2('3.2 Recurrent Neural Network Formulations'),
  p('Protein sequences x = (x₁, ..., x_T) are processed recurrently, where each x_t is an amino acid residue embedding:', { noIndent: true }),
  h3('3.2.1 LSTM Equations'),
  eq('f_t = sigma( W_f [h_{t-1}, x_t] + b_f )   [forget gate]', '... (9)'),
  eq('i_t = sigma( W_i [h_{t-1}, x_t] + b_i )   [input gate]', '... (10)'),
  eq('o_t = sigma( W_o [h_{t-1}, x_t] + b_o )   [output gate]', '... (11)'),
  eq('c~_t = tanh( W_c [h_{t-1}, x_t] + b_c )   [candidate cell]', '... (12)'),
  eq('c_t = f_t ⊙ c_{t-1} + i_t ⊙ c~_t         [cell state]', '... (13)'),
  eq('h_t = o_t ⊙ tanh(c_t)                     [hidden state]', '... (14)'),
  p('The multiplicative gates control information flow, enabling LSTMs to capture long-range dependencies that vanilla RNNs lose to gradient vanishing (Mienye et al., 2024).', { noIndent: true }),
  h3('3.2.2 GRU Equations'),
  eq('z_t = sigma( W_z [h_{t-1}, x_t] + b_z )   [update gate]', '... (15)'),
  eq('r_t = sigma( W_r [h_{t-1}, x_t] + b_r )   [reset gate]', '... (16)'),
  eq('h~_t = tanh( W [r_t ⊙ h_{t-1}, x_t] + b ) [candidate]', '... (17)'),
  eq('h_t = (1 - z_t) ⊙ h_{t-1} + z_t ⊙ h~_t  [hidden state]', '... (18)'),
  p('GRUs use two gates instead of three, offering comparable expressiveness to LSTMs with lower computational cost. Bidirectional GRU processes sequences in both directions:', { noIndent: true }),
  eq('h_t = [ h_t(forward) || h_t(backward) ]', '... (19)'),
  h2('3.3 Attention Mechanisms'),
  h3('3.3.1 Scaled Dot-Product Attention'),
  eq('Attention(Q, K, V) = softmax( Q K^T / sqrt(d_k) ) V', '... (20)'),
  p('where Q (queries), K (keys), V (values) are linear projections and d_k is the key dimension (Vaswani et al., 2017).', { noIndent: true }),
  h3('3.3.2 Multi-Head Attention'),
  eq('head_i = Attention( Q W_i^Q, K W_i^K, V W_i^V )', '... (21a)'),
  eq('MultiHead(Q,K,V) = Concat(head_1,...,head_h) W^O', '... (21b)'),
  h3('3.3.3 Bidirectional Cross-Modal Attention (Drug ↔ Protein)'),
  p('Let h_d in R^(n x d) be drug atom embeddings and h_p in R^(m x d) be protein residue embeddings:', { noIndent: true }),
  eq('A_{d->p} = softmax( Q_d K_p^T / sqrt(d_k) ) V_p   [drug queries protein]', '... (22)'),
  eq('A_{p->d} = softmax( Q_p K_d^T / sqrt(d_k) ) V_d   [protein queries drug]', '... (23)'),
  h3('3.3.4 Gated Cross-Attention Fusion (H-GNN-RNN-DTI)'),
  eq('G_d = sigma( W_g [h_d || A_{d->p}] + b_g )', '... (24)'),
  eq("h_d' = G_d ⊙ A_{d->p} + (1 - G_d) ⊙ h_d", '... (25)'),
  eq('G_p = sigma( W_g\' [h_p || A_{p->d}] + b_g\' )', '... (26)'),
  eq("h_p' = G_p ⊙ A_{p->d} + (1 - G_p) ⊙ h_p", '... (27)'),
  eq('h_fused = sigma( W_f [z_d || z_p] + b_f )', '... (28)'),
  p('Gates G_d, G_p in (0,1)^d adaptively balance cross-modal enrichment with original modality preservation, overcoming the information loss of static concatenation.', { noIndent: true }),
  h2('3.4 Loss Functions'),
  h3('3.4.1 Focal Loss (for class imbalance)'),
  eq('FL(p_t) = -alpha_t (1 - p_t)^gamma log(p_t)', '... (29)'),
  p('where p_t = p if y=1 else (1-p), gamma (typically 2.0) focuses on hard examples, and alpha_t addresses class frequency. Employed in H-GNN-RNN-DTI.', { noIndent: true }),
  h3('3.4.2 Weighted Binary Cross-Entropy'),
  eq('L_wBCE = -(1/N) SUM_i [ w+ y_i log(p_i) + w- (1-y_i) log(1-p_i) ]', '... (30)'),
  h3('3.4.3 Mean Squared Error (Regression)'),
  eq('L_MSE = (1/N) SUM_{i=1}^{N} (y_hat_i - y_i)^2', '... (31)'),
  h2('3.5 Evaluation Metrics'),
  h3('3.5.1 AUC-ROC and AUPR (Classification)'),
  eq('AUC-ROC = integral_0^1 TPR(FPR) d(FPR)', '... (32)'),
  eq('AUPR = integral_0^1 Precision(Recall) d(Recall)', '... (33)'),
  p('AUPR is preferred for imbalanced datasets; it is more sensitive to positive-class performance than AUC-ROC.', { noIndent: true }),
  h3('3.5.2 RMSE, MAE (Regression)'),
  eq('RMSE = sqrt( (1/N) SUM (y_hat_i - y_i)^2 )', '... (34)'),
  eq('MAE  = (1/N) SUM |y_hat_i - y_i|', '... (35)'),
  h3('3.5.3 Concordance Index (CI)'),
  eq('CI = SUM_{delta_x > delta_y} h(b_y - b_x) / Z', '... (36)'),
  p('where b_x, b_y are predicted values, delta_x, delta_y are experimental affinities, and Z normalizes over all valid pairs. CI = 1.0 indicates perfect ranking.', { noIndent: true }),
  h3('3.5.4 Pearson Correlation Coefficient (PCC)'),
  eq("PCC = SUM(y_hat - y_hat_mean)(y - y_mean) / sqrt( SUM(y_hat-y_hat_mean)^2 * SUM(y-y_mean)^2 )", '... (37)'),
  pb()
];
