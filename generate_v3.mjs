// generate_v3.mjs — Builds DTI_Review_Paper_v3.docx with all proper visual figures
import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  PageBreak, ShadingType, convertInchesToTwip
} from 'docx';
import fs from 'fs';

// ── Import content helpers and section content from part scripts ──────────
import {
  titlePage, abstractSection, introSection, backgroundSection, mathSection,
  p, h1, h2, h3, h4, bul, sp, pb, cap, eq, pRuns, tr, createTable, FONT, SZ
} from './generate_review_p1.mjs';

import { modelReviewSection } from './generate_review_p2.mjs';

import {
  tableSection, gapsSection, futureSection, conclusionSection, referenceSection
} from './generate_review_p3.mjs';

// ── Figure directory ──────────────────────────────────────────────────────
const FIGS = 'C:\\Users\\Jamila\\Modeling-DTI\\paper\\figures';

/** Embed a PNG figure. Width/height in points (1in = 72pt). */
function imgRun(file, wPt, hPt) {
  return new ImageRun({
    data: fs.readFileSync(`${FIGS}\\${file}`),
    transformation: { width: Math.round(wPt), height: Math.round(hPt) },
    type: 'png'
  });
}

/** Centered paragraph containing one figure */
function imgPara(file, wPt, hPt) {
  return new Paragraph({
    children: [imgRun(file, wPt, hPt)],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 }
  });
}

// Page text width ≈ 6.3 inches = 453.6 pt (with 1-inch margins on letter paper)
const PW = 454;
function scaledH(file_w, file_h, disp_w = PW) {
  return Math.round((file_h / file_w) * disp_w);
}

// ── Architecture Section (replaces all ASCII wireframes) ──────────────────
const archSection = [
  h1('4. Conceptual Architecture Overviews'),
  p('This section presents visual data-flow diagrams for six architectural paradigms. Each figure illustrates general design philosophy, data flow, and key component interactions for DTI/DTA models within that paradigm.'),

  // 4.1 CNN
  h2('4.1 CNN-Based Models (DeepDTA, DTI-RCNN)'),
  imgPara('fig4_cnn.png', PW, scaledH(1200,370)),
  cap('Figure 4. CNN-based DTI/DTA architecture (DeepDTA paradigm). Drug SMILES strings and protein FASTA sequences are independently encoded with 1D convolutional filter banks, concatenated, and passed through fully connected layers for affinity/interaction prediction. Key limitation: no molecular graph topology; static concatenation fusion.'),

  // 4.2 GNN
  h2('4.2 GNN-Based Models (GraphDTA, SaeGraphDTI)'),
  imgPara('fig5_gnn.png', PW, scaledH(1200,420)),
  cap('Figure 5. GNN-based DTI architecture (GraphDTA paradigm). Drug molecules encoded as molecular graphs via GCN/GAT/GIN; protein sequences encoded via CNN/RNN. Graph readout produces a fixed-length drug embedding; both embeddings are concatenated for prediction.'),

  // 4.3 Transformer
  h2('4.3 Transformer-Based Models (TransformerCPI, MolTrans, EmbedDTI)'),
  imgPara('fig6_transformer.png', PW, scaledH(1200,440)),
  cap('Figure 6. Transformer-based DTI architecture. Drug and protein tokens processed through independent Transformer encoders with multi-head self-attention. Cross-attention or bilinear interaction fuses representations. Pre-trained LM initialization (ChemBERTa, ESM-2) shown as BERT-style input embedding (inset).'),

  // 4.4 KG
  h2('4.4 Knowledge Graph-Based Models (TTModel, DTKGIN)'),
  imgPara('fig7_kg.png', PW, scaledH(1200,400)),
  cap('Figure 7. Knowledge graph-based DTI architecture (DTKGIN/TTModel paradigm). Heterogeneous biomedical entities (Drug, Protein, Disease, Pathway) embedded via GNN/TransE over the KG; interaction score predicted via inner product of drug–protein entity embeddings. DTKGIN adds latent intent nodes for finer interaction granularity.'),

  // 4.5 GNN+RNN (main architecture)
  h2('4.5 Hybrid GNN + RNN Architecture: The Proposed H-GNN-RNN-DTI'),
  p('The proposed H-GNN-RNN-DTI integrates a Hierarchical Graph Attention Network (H-GAT) for drug molecular graph encoding with a Bidirectional LSTM/GRU for protein sequence encoding, fusing them through a novel Gated Cross-Attention module that enables adaptive, bidirectional drug–protein interaction modeling.'),
  imgPara('fig3_architecture.png', PW, scaledH(1400,780)),
  cap('Figure 3. Conceptual architecture of the proposed H-GNN-RNN-DTI model (Abdul-Hadi, 2025). Drug Branch: H-GAT encoder (3 layers, 8 heads) with ChemBERTa initialization and attention-weighted readout. Protein Branch: BiLSTM/BiGRU (2 layers) with ESM-2 embeddings and attention pooling. Gated Cross-Attention Fusion Module (centre): bidirectional attention A_{d→p} and A_{p→d} regulated by learned gates G_d and G_p, producing h_fused. Prediction Head: MLP with focal loss (classification) or MSE (regression).'),
  sp(),
  pb()
];

// ── Cross-Attention figure for Section 3 ──────────────────────────────────
// We'll inject it into the mathSection by building a modified version.
const mathSectionWithFig = [
  ...mathSection.slice(0, mathSection.length - 1), // all except the final pb()
  h3('3.3.3 Cross-Modal Attention Mechanism — Visual Overview'),
  p('Figure 8 illustrates the bidirectional gated cross-attention mechanism, showing how drug atom embeddings (h_d) and protein residue embeddings (h_p) mutually attend to each other, regulated by learned gates, to produce enriched cross-modal representations.'),
  imgPara('fig8_crossattn.png', PW, scaledH(1050,540)),
  cap('Figure 8. Gated Cross-Attention mechanism. Drug and protein inputs each processed by modality-specific attention, then bidirectionally cross-attend (A_{d→p} and A_{p→d}). Gating (G_d, G_p) adaptively balances cross-modal enrichment with original modality preservation. Multiple attention outputs are combined for the final DTI prediction.'),
  sp(),
  pb()
];

// ── Background section with mind map ─────────────────────────────────────
const backgroundWithMindmap = [
  ...backgroundSection.slice(0, backgroundSection.length - 1), // all except final pb()
  h2('2.6 Taxonomy Visual Summary'),
  p('Figure 2 provides a mind-map visual summary of the six major DTI prediction paradigms reviewed in this paper, each branching into representative architectures and techniques.'),
  imgPara('fig2_mindmap.png', 380, scaledH(980,880,380)),
  cap('Figure 2. Mind map of DTI/DTA prediction method taxonomy. Central node: DTI Prediction Methods; six branches: Physics-Based, Classical ML, Deep Learning Architectures, Transformer + Foundation Models, Hybrid Multimodal DL, and Interpretable + Cold-Start Models.'),
  sp(),
  pb()
];

// ── Gaps section with visual summary ──────────────────────────────────────
const gapsWithFig = [
  ...gapsSection.slice(0, gapsSection.length - 1), // all except final pb()
  h2('7.7 Research Gaps — Visual Summary'),
  imgPara('fig11_gaps.png', PW, scaledH(1200,420)),
  cap('Figure 11. Summary of five primary research gaps identified across 36 reviewed DTI/DTA models, with severity indicators. The bottom bar indicates how the proposed H-GNN-RNN-DTI framework addresses each gap through gated cross-attention fusion, pretrained embeddings, focal loss, attention-based XAI, and standardized evaluation.'),
  sp(),
  pb()
];

// ── Future section with GAN figure ────────────────────────────────────────
const futureWithFig = [
  ...futureSection.slice(0, futureSection.length - 1),
  h2('8.8 GAN-Based Data Augmentation for Cold-Start Mitigation'),
  p('Generative Adversarial Networks (GANs) offer a promising approach to generating synthetic drug and protein sequence data to augment sparse training sets. As shown in Figure 10, a dual-path GAN architecture generates realistic drug and protein sequences via independent generators, validated by discriminators, with the authenticated features combined through co-processing for DTI prediction. This approach can substantially reduce cold-start degradation by generating plausible interaction partners for novel entities.'),
  imgPara('fig10_gan.png', PW, scaledH(1100,440)),
  cap('Figure 10. GAN-based data augmentation framework for DTI cold-start mitigation (adapted from literature paradigm). Independent generators synthesize drug and protein sequences from noise; discriminators enforce authenticity; co-processing fuses drug and protein features for DTI output.'),
  sp(),
  pb()
];

// ── Network-based figure injection into model review section ──────────────
// Insert network figure into the GSRF-DTI model block in modelReviewSection
// We inject it as a standalone section before the model reviews
const networkFigSection = [
  h2('5.0 Network-Based Similarity: Conceptual Illustration'),
  p('Before reviewing individual models, Figure 9 illustrates the foundational concept of network-based DTI prediction used by models such as GSRF-DTI and NGCN: drug–drug and target–target similarity networks are combined with a known DTI matrix to generate a predicted interaction matrix P(D,T).'),
  imgPara('fig9_network.png', PW, scaledH(1100,400)),
  cap('Figure 9. Network-based DTI prediction paradigm. (Left) Drug and target similarity networks; (centre) drug–target matrix R(D,T) and GNN-based encoding; (right) candidate target identification from predicted P(D,T). Basis of network-based methods including GSRF-DTI (Zhu et al., 2024) and NGCN (Cao et al., 2024).'),
  sp()
];

// ── Framework overview (add at top of paper after abstract) ───────────────
const frameworkFigSection = [
  imgPara('fig1_framework.png', PW, scaledH(1380,520)),
  cap('Figure 1. Framework overview of this comprehensive review. Five thematic pillars (Introduction, Related Databases, Encoding Methods, Research Methods, Model Evaluation) lead to identification of five research gaps, seven future directions, and conclusions.'),
  sp(),
  pb()
];

// ── Assemble complete document ────────────────────────────────────────────
const allChildren = [
  ...titlePage,
  ...abstractSection,
  ...frameworkFigSection,   // Fig 1 — overview framework
  ...introSection,
  ...backgroundWithMindmap, // Fig 2 — mind map taxonomy
  ...mathSectionWithFig,    // Fig 8 — cross-attention
  ...archSection,           // Figs 3–7 (replaces all ASCII wireframes)
  ...networkFigSection,     // Fig 9 — network-based illustration
  ...modelReviewSection,
  ...tableSection,
  ...gapsWithFig,           // Fig 11 — research gaps
  ...futureWithFig,         // Fig 10 — GAN augmentation
  ...conclusionSection,
  ...referenceSection
];

const doc = new Document({
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 }
      }
    },
    children: allChildren
  }],
  styles: {
    default: {
      document: { run: { font: 'Times New Roman', size: 24 } }
    }
  }
});

const buf = await Packer.toBuffer(doc);
fs.writeFileSync('C:\\Users\\Jamila\\Modeling-DTI\\paper\\DTI_Review_Paper_v3_final.docx', buf);
console.log(`Done. DTI_Review_Paper_v3_final.docx  (${(buf.length/1024).toFixed(1)} KB)`);
