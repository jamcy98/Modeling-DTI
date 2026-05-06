// Part 2: Architecture Overviews + Model Reviews
import { h1, h2, h3, h4, p, eq, bul, sp, pb, cap, ascii, tr, pRuns } from './generate_review_p1.mjs';
import { Paragraph, TextRun, AlignmentType } from 'docx';

const FONT = 'Times New Roman';
const CODE = 'Courier New';
const SZ = 24;

// ============================================================
// SECTION 4: ARCHITECTURE OVERVIEWS (CONCEPTUAL SKETCHES)
// ============================================================
export const archSection = [
  h1('4. Conceptual Architecture Overviews'),
  p('This section presents conceptual data-flow sketches for six architectural paradigms. These ASCII-art diagrams illustrate the general design philosophy and information flow without referencing specific paper figures.'),

  h2('4.1 CNN-Based Models (DeepDTA, DTI-RCNN)'),
  ...ascii([
    '   DRUG SMILES string  →  Character Embedding  →  Conv1D Blocks (filters k)  →  MaxPool  →  d_D',
    '   PROTEIN FASTA seq.  →  Character Embedding  →  Conv1D Blocks (filters k)  →  MaxPool  →  d_P',
    '                                      |                              |',
    '                          Concatenate([d_D, d_P]) ──► FC Layers ──► Sigmoid/Linear ──► DTI Score'
  ]),
  sp(),
  p('Key design: Treats sequences as 1D signals; multiple filter widths capture n-gram patterns at different scales. Simple and fast but ignores molecular graph topology and long-range sequence context.', { noIndent: true }),

  h2('4.2 GNN-Based Models (GraphDTA, SaeGraphDTI)'),
  ...ascii([
    '   SMILES → RDKit Graph G=(V,E) → Atom/Bond Features → GNN Layers (GCN/GAT/GIN) → READOUT → d_drug',
    '   PROTEIN FASTA  → One-Hot / Embedding → CNN/RNN Encoder → d_protein',
    '                         |                          |',
    '         Concatenate([d_drug, d_protein]) → FC → Affinity / Interaction'
  ]),
  sp(),
  p('Key design: Molecular topology encoded natively through iterative message passing. Atom-level features propagated through bond neighborhoods. Protein still encoded as sequence; fusion is typically concatenation.', { noIndent: true }),

  h2('4.3 Transformer-Based Models (TransformerCPI, MolTrans, EmbedDTI)'),
  ...ascii([
    '   DRUG tokens     → [CLS, tok1, tok2, ...] → Transformer Encoder (Multi-Head Self-Attn) → d_drug',
    '   PROTEIN tokens  → [CLS, aa1, aa2, ...]   → Transformer Encoder (Multi-Head Self-Attn) → d_prot',
    '                         |                              |',
    '   Cross-Attention(d_drug, d_prot) or Bilinear Interaction → MLP → DTI Score'
  ]),
  sp(),
  p('Key design: Self-attention models all-pair token dependencies in parallel. Pre-trained encoders (ChemBERTa, ESM-2) provide rich initialization. Cross-attention enables inter-modal interaction modeling.', { noIndent: true }),

  h2('4.4 Knowledge Graph-Based Models (TTModel, DTKGIN)'),
  ...ascii([
    '   Biomedical KG: {Drug, Protein, Disease, Pathway, ...} + Relation Triples',
    '   Entity Embedding: E_drug, E_protein (via TransE / RotatE / intent-GNN)',
    '   Relation Embedding: R_dti',
    '         |                |',
    '   Inner Product (E_drug, E_protein) → Sigmoid → Interaction Score'
  ]),
  sp(),
  p('Key design: Leverages heterogeneous biomedical relational context. DTKGIN adds latent intent nodes for finer DTI granularity. Limitation: no direct molecular graph or sequence encoding.', { noIndent: true }),

  h2('4.5 Hybrid GNN + RNN Models (DeepGS/GAT+BiGRU, H-GNN-RNN-DTI)'),
  ...ascii([
    ' ┌─────── DRUG BRANCH ──────────┐  ┌──────── PROTEIN BRANCH ──────────┐',
    ' │ SMILES → Mol.Graph           │  │ FASTA → Tokenize                 │',
    ' │   → H-GAT (3L, 8 heads)      │  │   → ESM-2 embeddings             │',
    ' │   → Attention Readout        │  │   → BiLSTM/BiGRU (2L)            │',
    ' │   → h_d in R^(n x d)         │  │   → Attention Pooling            │',
    ' └──────────────────────────────┘  │   → h_p in R^(m x d)             │',
    '                |                  └──────────────────────────────────┘',
    '                |                                |',
    '      ┌─────────────────────────────────────────────────┐',
    '      │         GATED CROSS-ATTENTION FUSION             │',
    '      │  A_{d->p} = softmax(Q_d K_p^T / sqrt(d)) V_p   │',
    '      │  G_d = sigma(W_g[h_d||A_{d->p}])                │',
    '      │  h_d\' = G_d⊙A_{d->p} + (1-G_d)⊙h_d            │',
    '      │  (symmetric for protein branch)                 │',
    '      │  h_fused = sigma(W_f [z_d || z_p] + b_f)       │',
    '      └─────────────────────────────────────────────────┘',
    '                         |',
    '           ┌─────────────────────────┐',
    '           │      PREDICTION HEAD    │',
    '           │  MLP → Sigmoid (class.) │',
    '           │  MLP → Linear (regress) │',
    '           └─────────────────────────┘'
  ]),
  cap('Figure 1. Conceptual architecture of the proposed H-GNN-RNN-DTI (Abdul-Hadi, 2025). The Gated Cross-Attention Fusion Module enables adaptive bidirectional cross-modal interaction between drug and protein representations, overcoming the limitations of static concatenation.'),
  pb()
];

// ============================================================
// SECTION 5: DETAILED MODEL REVIEWS
// ============================================================

function modelBlock(name, year, authors, ref, category, archDesc, keyInnovation, mathDesc, datasets, metrics, limitations) {
  return [
    h3(`${name} (${authors}, ${year})`),
    p(`Category: ${category}`, { noIndent: true }),
    p(`Architecture: ${archDesc}`),
    p(`Key Innovation: ${keyInnovation}`),
    p(`Key Mathematical Component: ${mathDesc}`, { noIndent: true }),
    p(`Datasets: ${datasets}`, { noIndent: true }),
    p(`Reported Performance: ${metrics}`, { noIndent: true }),
    p(`Limitations: ${limitations}`),
    sp()
  ];
}

export const modelReviewSection = [
  h1('5. Detailed Model Reviews'),
  p('Models are organized by architectural paradigm, progressing from early baselines to current state-of-the-art hybrid frameworks. For each model we present: architecture overview, key innovation, representative mathematical formulation, evaluation datasets, reported performance, and critical limitations.'),

  // ─── 5.1 CNN-Based Baselines ───────────────────────────────────────────
  h2('5.1 CNN-Based Baselines'),

  ...modelBlock(
    'DeepDTA', 2018, 'Öztürk et al.', '(Öztürk et al., 2018)',
    'CNN (SMILES + Protein Sequence)',
    'DeepDTA encodes both drug SMILES strings and protein amino acid sequences as character-level inputs, feeding them into independent 1D convolutional blocks with multiple filter widths (4, 6, 8) to capture local n-gram patterns. The resulting fixed-length embeddings are concatenated and passed through fully connected layers to predict continuous binding affinity values.',
    'First deep learning model demonstrating that raw character sequences—without hand-crafted features or 3D structures—suffice for competitive DTA prediction, establishing CNN sequence encoding as a baseline paradigm.',
    'Convolution: h = ReLU(W * x + b), where * is 1D convolution over character embeddings. Multiple filter widths capture n-grams of different lengths. Global max pooling reduces each filter map to a scalar.',
    'DAVIS (30,056 pairs), KIBA (52,498 pairs)',
    'DAVIS: CI = 0.878, MSE = 0.261; KIBA: CI = 0.863, MSE = 0.194',
    'Ignores molecular graph topology; treats SMILES as plain text, losing structural information. CNN protein encoder captures only local context, missing long-range residue dependencies. Static concatenation fusion prevents cross-modal interaction. No interpretability beyond feature importance.'
  ),

  ...modelBlock(
    'DTI-RCNN', 2025, 'Bian et al.', '(Bian et al., 2025)',
    'CNN + LSTM Hybrid',
    'DTI-RCNN combines CNNs for local feature extraction from SMILES strings and protein sequences with LSTM layers for modeling sequential dependencies between extracted feature maps. This hybrid captures both local patterns (via CNN) and temporal dependencies (via LSTM), specifically designed to account for gene–drug relationship contexts in interaction prediction.',
    'Hybrid CNN–LSTM integration to simultaneously capture local motif patterns and long-range sequential dependencies, particularly targeting gene–drug relational contexts missed by pure CNN or RNN models.',
    'Feature maps from CNN: F = MaxPool(ReLU(W_c * x)). LSTM applied over stacked feature maps: h_t = LSTM(h_{t-1}, F_t). Final classification: y = sigma(W_fc * h_T + b).',
    'Benchmark DTI datasets (Human, C. elegans)',
    'AUC competitive with attention-based models; specific values model-variant dependent',
    'SMILES encoding remains character-level; CNN misses molecular topology. LSTM adds computational cost. Concatenation fusion is static. Limited interpretability.'
  ),

  // ─── 5.2 GNN-Based Models ──────────────────────────────────────────────
  h2('5.2 GNN-Based Models'),

  ...modelBlock(
    'GraphDTA', 2021, 'Nguyen et al.', '(Nguyen et al., 2021)',
    'GNN (Drug) + CNN (Protein)',
    'GraphDTA represents drug molecules as molecular graphs and systematically compares four GNN variants—GCN, GAT, GIN, and GAT-GCN—for drug encoding. Protein sequences are encoded using a CNN with multiple filter widths. The drug graph embedding (via global mean pooling) is concatenated with the protein sequence embedding and passed through dense layers for affinity prediction.',
    'First systematic benchmarking of GNN variants for molecular graph encoding in DTA, demonstrating that graph-based drug representation consistently outperforms character-level CNN encoding (SMILES) across multiple GNN architectures.',
    'GAT variant: h_v^(l+1) = ELU(SUM_{j in N(v)} alpha_vj * W h_j^(l)), where alpha_vj is the attention coefficient from Eq. (5)-(6). Global mean pooling: h_G = (1/|V|) SUM_{v} h_v^(L).',
    'DAVIS, KIBA',
    'DAVIS: CI = 0.893 (GAT), RMSE = 0.229; KIBA: CI = 0.891 (GAT), RMSE = 0.139',
    'CNN protein encoder ignores long-range residue dependencies; static concatenation fusion. No cross-modal attention between drug and protein representations. Limited interpretability. No cold-start evaluation.'
  ),

  ...modelBlock(
    'SaeGraphDTI', 2025, 'Zhang et al.', '(Q. Zhang et al., 2025)',
    'Sequence Attribute Extraction + GNN',
    'SaeGraphDTI integrates drug molecular graph encoding via GNN with protein sequence attribute extraction modules that identify residue-level physicochemical features (charge, hydrophobicity, polarity). These modality-specific representations are fused through a learned weighting mechanism and fed into a classification head for binary DTI prediction.',
    'Explicit residue-level physicochemical attribute extraction as a complement to raw sequence encoding, providing richer protein features beyond amino acid identity that improve DTI discrimination.',
    'Attribute-enhanced protein encoding: h_p = CONCAT(h_seq, h_attr), where h_attr captures residue physicochemical features. Drug GNN encoding follows Eq. (1)-(2). Fusion: h_fused = W_f [h_G || h_p].',
    'BindingDB, DAVIS',
    'AUC = 0.91+, AUPR competitive with state-of-the-art on BindingDB',
    'Attribute extraction is heuristic and may not fully capture structural binding context. Concatenation-based fusion limits cross-modal interaction. No explicit cold-start evaluation or interpretability analysis reported.'
  ),

  // ─── 5.3 Attention-Enhanced Models ─────────────────────────────────────
  h2('5.3 Attention-Enhanced Models'),

  ...modelBlock(
    'AttentionDTI', 2019, 'Zhao et al.', '(Zhao et al., 2019)',
    'Attention over Molecular Fingerprints + Protein Descriptors',
    'AttentionDTI applies an attention mechanism over molecular fingerprint features and protein composition descriptors to selectively weight informative drug and protein features. The attention layer learns which molecular substructures and amino acid compositions are most discriminative for predicting binary DTI, providing a degree of feature-level interpretability.',
    'Introduced learned attention weighting over hand-crafted molecular and protein features for DTI, establishing attention as a mechanism for feature selection and preliminary interpretability in the field.',
    'Attention score: a_i = exp(e_i) / SUM_j exp(e_j), where e_i = tanh(W_a h_i + b_a). Attended features: h_att = SUM_i a_i * h_i. Classification: y = sigma(W_c h_att + b_c).',
    'Human (2,127 pairs), C. elegans (1,434 pairs)',
    'Human: AUC = 0.970, AUPR = 0.967; C. elegans: AUC = 0.966, AUPR = 0.960',
    'Fingerprint-based drug encoding loses structural 3D topology information. Protein represented as composition descriptors rather than raw sequence, discarding sequence-order information. Binary classification only; no affinity regression.'
  ),

  ...modelBlock(
    'HyperAttentionDTI', 2022, 'Zhao et al.', '(Q. Zhao et al., 2022)',
    'Sequence-Based CNN + Bidirectional Attention',
    'HyperAttentionDTI encodes drugs using CNN layers over SMILES and proteins using CNN layers over amino acid sequences, then applies a bidirectional attention mechanism between drug and protein sequence representations. The attention aligns drug tokens with protein tokens to highlight interaction-relevant positions before concatenation and classification.',
    'Bidirectional sequence-to-sequence attention between drug SMILES tokens and protein amino acid tokens, enabling finer cross-modal alignment than global concatenation while remaining computationally efficient.',
    'Bidirectional attention: A_dp = softmax(H_d H_p^T / sqrt(d)), A_pd = softmax(H_p H_d^T / sqrt(d)). Context vectors: c_d = A_dp H_p, c_p = A_pd H_d. Final: h = [h_d; c_d; h_p; c_p].',
    'DAVIS, KIBA, Human, C. elegans',
    'DAVIS: CI = 0.882; KIBA: CI = 0.876; Human: AUC = 0.967',
    'SMILES encoding remains character-level without graph topology. No pre-trained molecular or protein language model embeddings. Attention is cross-sequence but not cross-modal at the substructure/residue level.'
  ),

  ...modelBlock(
    'GSAML-DTA', 2022, 'Liao et al.', '(J. Liao et al., 2022)',
    'GNN + Self-Attention + Mutual Information',
    'GSAML-DTA combines GNN-based drug encoding with self-attention applied over both drug and protein representations. A mutual information module identifies which drug atom embeddings and protein residue embeddings are most informative for binding affinity prediction. The model provides interpretability by attributing binding affinity to specific atoms and residues.',
    'Integration of mutual information maximization as an interpretability and feature selection mechanism, explicitly attributing binding affinity to drug atom and protein residue contributions—pioneering XAI for DTA.',
    'GNN drug: h_G via Eq. (1)-(2). Protein self-attention: h_p = MHA(h_p, h_p, h_p). MI attribution: I(h_atom; y) = H(y) - H(y|h_atom), identifying high-MI atoms/residues as binding-relevant.',
    'DAVIS, KIBA',
    'DAVIS: RMSE = 0.234, CI = 0.891; KIBA: RMSE = 0.142, CI = 0.893',
    'Mutual information estimation is computationally approximate. Self-attention on protein does not capture long-range dependencies as effectively as Transformers. No cold-start evaluation. Foundation model embeddings not used.'
  ),

  ...modelBlock(
    'GraphATT-DTA', 2023, 'Bae & Nam', '(Bae & Nam, 2023)',
    'Graph Attention (Drug) + Sequence Attention (Protein)',
    'GraphATT-DTA applies graph attention networks to drug molecular graphs to identify important compound substructures, and sequence attention over protein amino acid encodings to highlight important protein subsequences. Attention weights from both branches are visualized to provide residue-level and atom-level interpretability for DTA predictions.',
    'Dual-branch attention interpretability providing simultaneous compound substructure and protein subsequence importance scores, making GraphATT-DTA one of the earlier models with explicit bidirectional XAI output.',
    'Drug: atom importance alpha_v = softmax(W_attn h_v^(L)), h_G = SUM_v alpha_v h_v. Protein: residue attn a_t = softmax(u^T tanh(W_s h_t)), h_P = SUM_t a_t h_t. Both used for visualization and fusion.',
    'DAVIS, KIBA',
    'DAVIS: CI = 0.896, MSE = 0.211; KIBA: CI = 0.893',
    'Graph attention identifies important substructures but lacks residue-level binding site validation against crystal structures. Protein attention does not model 3D folding. No cold-start evaluation reported.'
  ),

  ...modelBlock(
    'MutualDTA', 2025, 'Yuan et al.', '(Yuan et al., 2025)',
    'Pre-Trained Encoders + Mutual-Attention Fusion',
    'MutualDTA integrates pre-trained molecular language model embeddings (ChemBERTa) for drug encoding and ESM-2 protein language model embeddings for protein encoding. A Mutual-Attention module explicitly establishes pairwise relationships between drug atom embeddings and protein residue embeddings, enabling bidirectional attribution for interpretability.',
    'Leveraging state-of-the-art pre-trained language models for both drug and protein modalities combined with a Mutual-Attention module that explicitly links drug atom and protein residue embeddings for fine-grained interpretability—advancing XAI in DTA.',
    'Mutual attention: M = softmax(H_d W H_p^T). Drug context: C_d = M H_p. Protein context: C_p = M^T H_d. Fused: h = W_f [H_d + C_d || H_p + C_p] + b. Binding hotspots identified via M visualization.',
    'DAVIS, KIBA, BindingDB',
    'DAVIS: CI = 0.908, MSE = 0.198; KIBA: CI = 0.917',
    'Pre-trained models require large GPU memory for fine-tuning. Mutual attention is bilinear and quadratic in sequence lengths, limiting scalability to very long proteins. Cold-start performance not systematically reported.'
  ),

  ...modelBlock(
    'EHIGN', 2024, 'Yang et al.', '(Yang et al., 2024)',
    'Interaction-Based Inductive Bias GNN',
    'EHIGN (Enhancing Interaction-based Graph Neural Network) introduces an interaction-based inductive bias by explicitly modeling pairwise atom–atom interactions between drug and protein atoms in 3D space. The model uses geometric distance features between drug atoms and protein residues to learn physically consistent interaction representations, enabling prediction of binding affinity changes in protein variants (e.g., SARS-CoV-2 variants).',
    'Physical atom–atom interaction modeling as an explicit inductive bias in the GNN, allowing the model to capture binding site geometry changes across protein variants—critical for variant-aware drug design.',
    'Interaction tensor: I_{ij} = MLP([h_i || h_j || d_ij]), where d_ij is the geometric distance between drug atom i and protein residue j. GNN aggregates I_{ij} over neighborhoods. Binding affinity: y_hat = MLP(READOUT(I)).',
    'PDBbind (protein–ligand complexes), SARS-CoV-2 variant datasets',
    'PDBbind: RMSE = 1.31 Å-equivalent, competitive with structure-aware models; strong performance on variant binding prediction',
    'Requires 3D protein structures, limiting applicability to targets without experimental or AlphaFold structures. Training on PDBbind biases toward structurally characterized interactions. Computationally expensive for large-scale screening.'
  ),

  // ─── 5.4 Transformer-Based Models ─────────────────────────────────────
  h2('5.4 Transformer-Based Models'),

  ...modelBlock(
    'TransformerCPI', 2020, 'Chen et al.', '(Y. Chen et al., 2020)',
    'Transformer (Drug) + CNN (Protein)',
    'TransformerCPI applies a Transformer encoder with multi-head self-attention to drug SMILES token sequences, capturing global dependencies between distant molecular substructures. Protein sequences are encoded using a CNN. Cross-modal interaction is modeled through a multi-layer Transformer that integrates drug and protein embeddings, enabling compound–protein interaction (CPI) prediction.',
    'Application of Transformer self-attention to drug SMILES encoding, enabling global dependency modeling across the molecular token sequence—surpassing the local receptive field limitation of CNN-based drug encoders.',
    'Drug Transformer: H_d = TransEnc(Embed(SMILES)). MultiHead: see Eq. (21). Cross-modal layer: H_joint = TransEnc([H_d; H_p]). Classification: y = sigma(MLP(CLS token)).',
    'Human, C. elegans, DAVIS',
    'Human: AUC = 0.971; C. elegans: AUC = 0.974; DAVIS: CI = 0.886',
    'Quadratic self-attention cost limits scalability to long sequences. CNN protein encoder remains local. No pre-trained Transformer initialization (trained from scratch). No cold-start evaluation.'
  ),

  ...modelBlock(
    'MolTrans', 2021, 'Huang et al.', '(Huang et al., 2021)',
    'Augmented Transformer + Substructure Interaction',
    'MolTrans introduces an augmented Transformer that explicitly encodes drug substructure patterns via a frequency-based interaction mining module. Drug–protein interaction is modeled through a Transformer cross-attention block that aligns drug substructures with protein subsequences. The augmentation provides structural chemistry knowledge beyond raw sequence patterns.',
    'Frequency-based substructure mining to augment Transformer token representations with domain-specific structural patterns, improving interaction prediction without requiring molecular graphs.',
    'Substructure augmentation: E_sub = Embed(freq_mined_substructures). Augmented drug enc.: H_d = TransEnc([Embed(SMILES); E_sub]). Cross-modal Transformer: H_joint = TransEnc(Cross-Attn(H_d, H_p, H_p)).',
    'BindingDB, DAVIS, KIBA',
    'BindingDB (classification): AUC = 0.953, AUPR = 0.879; DAVIS: CI = 0.895',
    'Substructure mining is heuristic. Transformer pre-training from scratch on limited DTI data may underperform pre-trained language models. Quadratic attention cost. No explicit cold-start evaluation protocol.'
  ),

  ...modelBlock(
    'EmbedDTI', 2021, 'Jin et al.', '(Jin et al., 2021)',
    'Sequence Embeddings + GCN + Attention',
    'EmbedDTI uses pre-trained molecular embeddings for drug encoding via a Graph Convolutional Network and contextual protein sequence embeddings. An attention module identifies crucial drug–target interaction components by attending over drug atom embeddings and protein residue embeddings simultaneously, providing interpretability alongside prediction.',
    'Combined pre-trained embeddings with GCN and attention-based interpretability, providing both improved representational quality through transfer learning and biological insight into interaction loci.',
    'GCN drug: h_G = READOUT(GCN(G, E_pretrained)). Protein: h_P = Attn-Pool(BiLSTM(E_pretrained)). Cross-attention identifies key atoms/residues: see Eq. (22)-(23) cross-attention framework.',
    'DAVIS, Human, C. elegans',
    'DAVIS: CI = 0.891; Human: AUC = 0.969',
    'Pre-trained embeddings available at time of publication were less powerful than current foundation models (ESM-2, ChemBERTa). Cold-start generalization not evaluated. Interpretability validated qualitatively but not quantitatively against crystal structures.'
  ),

  // ─── 5.5 Knowledge Graph-Based Models ─────────────────────────────────
  h2('5.5 Knowledge Graph-Based Models'),

  ...modelBlock(
    'TTModel', 2024, 'Li et al.', '(N. Li et al., 2024)',
    'Knowledge Graph Embedding (Text + Type Information)',
    'TTModel is a KG embedding framework that integrates two complementary encoders: a relation triple encoder capturing structural (relation type) and textual (biomedical text description) features of drug–target triples, and a type triple encoder capturing latent entity-type information (e.g., drug class, target family). Combining these encoders improves prediction in sparse KG scenarios.',
    'Dual-encoder design that enriches KG embeddings with both biomedical textual descriptions and entity type information, substantially improving performance for sparse protein families (NR, GPCR) where structural features alone are insufficient.',
    'Relation triple: e_drt = MLP([E_d; E_r; E_t]). Type triple: e_dt = MLP([E_type_d; E_type_t]). Combined score: s(d,t) = sigma(MLP([e_drt; e_dt])). Trained with pairwise ranking loss.',
    'Yamanishi_08 (enzyme, IC, GPCR, NR), custom KG from DrugBank/UniProt',
    'GPCR: AUPR = 0.95; NR: AUPR = 0.93; Enzyme: AUPR = 0.97',
    'No direct molecular graph or amino acid sequence encoding; relies entirely on KG completeness. Performance degrades significantly for incomplete KGs. No dynamic cross-modal attention between drug and protein modalities. No cold-start formal evaluation.'
  ),

  ...modelBlock(
    'DTKGIN', 2024, 'Luo et al.', '(Luo et al., 2024)',
    'Knowledge Graph + Intent Graph Neural Network',
    'DTKGIN enriches the standard drug–target KG with latent intent nodes that represent coarse-grained interaction intents (e.g., inhibitory, activating). Drug and target embeddings are updated through relation-path-aware GNN aggregation over both the KG and intent graph, enabling the model to distinguish interaction purposes at a finer granularity. This improves cold-start scenario performance compared to standard KG methods.',
    'Introduction of latent intent nodes in the drug–target KG to capture interaction intent at varying granularities, enabling more robust cold-start generalization through richer relational structure.',
    'Intent-aware aggregation: h_d^(l) = AGG_GNN({h_n, r_dn : n in N_KG+intent(d)}). Prediction: s(d,t) = h_d^(L) * h_t^(L) (inner product). Intent node count tuned as hyperparameter (optimal ~8).',
    'Yamanishi_08 (cold-start: S1/S2/S3)',
    'S1 (warm): AUC=0.950, AUPR=0.941; S2 (cold-drug): AUC=0.894, AUPR=0.753; S3 (cold-target): AUC=0.851, AUPR=0.660',
    'No modality-specific encoders (GNN for molecular graphs, RNN for sequences). Inner product prediction lacks expressive cross-modal attention. Intent node count is dataset-specific. Pre-trained foundation model embeddings not incorporated.'
  ),

  // ─── 5.6 Network-Based Models ──────────────────────────────────────────
  h2('5.6 Network-Based Hybrid Models'),

  ...modelBlock(
    'GSRF-DTI', 2024, 'Zhu et al.', '(Zhu et al., 2024)',
    'DeepWalk + GraphSAGE + Random Forest',
    'GSRF-DTI constructs homogeneous drug–drug and target–target similarity networks from chemical and sequence features, then builds a drug–target pair network (DTP-NET). DeepWalk extracts topological feature embeddings from these networks. GraphSAGE learns representations from DTP-NET. A Random Forest classifier makes final interaction predictions, with binary interaction labels based on known DTI databases.',
    'Integration of network topological information (DeepWalk) with graph representation learning (GraphSAGE) and ensemble classification (Random Forest), achieving strong performance on large-scale heterogeneous network datasets.',
    'DeepWalk: random walk sequence → word2vec embedding h_v. GraphSAGE: h_v^(l) = sigma(W^(l) [h_v^(l-1) || MEAN_{u in N(v)} h_u^(l-1)]) per Eq. (7). RF classifier on [h_drug; h_target].',
    'Luo_17 (1,923 drugs, 3,770 targets)',
    'AUROC = 0.9818, AUPR = 0.9839 on Luo_17',
    'Static late-fusion (concatenation) prevents dynamic cross-modal interaction. No GNN molecular graph or RNN sequence encoding; relies on network-level similarity features. Random Forest lacks atom/residue-level interpretability. Acknowledged data imbalance limitation. No cold-start evaluation. No pre-trained embeddings.'
  ),

  ...modelBlock(
    'RSGCL-DTI', 2025, 'Bian et al.', '(Bian et al., 2025)',
    'Relational Similarity Graph + Contrastive Learning',
    'RSGCL-DTI constructs relational similarity graphs for both drugs and proteins based on structural and sequence similarity metrics. Graph contrastive learning is applied to learn robust, invariant representations by maximizing agreement between augmented views of the same drug or protein. These pretrained representations are fused for DTI prediction, improving generalization through self-supervised pretraining.',
    'Application of graph contrastive learning to DTI, using data augmentation and similarity graphs to learn transferable representations that generalize better to unseen drug–target pairs than supervised-only approaches.',
    'Contrastive loss: L_cl = -log( exp(sim(h_i, h_j)/tau) / SUM_{k!=i} exp(sim(h_i, h_k)/tau) ), where sim is cosine similarity, tau is temperature. Supervised loss added for DTI classification.',
    'BindingDB, Yamanishi_08',
    'BindingDB: AUC = 0.942, AUPR = 0.938; Yamanishi_08: AUC = 0.947',
    'Contrastive pretraining requires careful augmentation design for molecular graphs (not trivial). Cold-start performance improved but not systematically benchmarked across S1/S2/S3. Interpretability mechanisms not included.'
  ),

  // ─── 5.7 Advanced Multi-Modal Fusion Models ────────────────────────────
  h2('5.7 Advanced Multi-Modal Fusion Models'),

  ...modelBlock(
    'iNGNN-DTI', 2024, 'Sun et al.', '(Sun et al., 2024)',
    'Nested GNN + Cross-Attention + Pre-Trained Embeddings',
    'iNGNN-DTI employs a nested graph neural network architecture where an outer GNN processes the drug–protein interaction graph and inner GNNs process individual molecular and protein subgraphs. Cross-attention modules capture fine-grained pairwise interactions between drug substructures and protein regions. Pre-trained molecular and protein embeddings are used for initialization, enhancing representation quality and cold-start performance.',
    'Nested GNN design that models both intra-molecular topology and inter-molecular interaction context simultaneously, combined with cross-attention and pretrained embeddings—making iNGNN-DTI one of the most architecturally comprehensive DTI models.',
    'Outer GNN: h_pair = GNN_outer(G_interaction). Inner GNNs: h_d = GNN_d(G_drug), h_p = GNN_p(G_prot). Cross-attention between h_d and h_p per Eq. (22)-(23). Pre-trained init.: h_d^(0) from ChemBERTa, h_p^(0) from ESM-2.',
    'BindingDB, DAVIS',
    'BindingDB: AUC = 0.963, AUPR = 0.947; DAVIS: CI = 0.904',
    'Nested GNN is computationally expensive, limiting scalability. Protein graph construction requires secondary structure information (not always available). Performance on cold-start not comprehensively reported.'
  ),

  ...modelBlock(
    'Top-DTI', 2025, 'Talo & Bozdag', '(Talo & Bozdag, 2025)',
    'TDA + Large Language Models + GNN',
    'Top-DTI integrates Topological Data Analysis (TDA) features derived from persistent homology of molecular point clouds with Large Language Model semantic embeddings (BioBERT for drugs, ESM-2 for proteins) and GNN structural features. These heterogeneous feature types are fused through a multi-modal Transformer, with TDA providing topological invariants that capture global molecular shape beyond local GNN neighborhoods.',
    'Novel integration of TDA persistent homology features with LLM embeddings and GNN structural features, capturing topological invariants (connected components, loops, voids) that encode global molecular geometry inaccessible to local message-passing GNNs.',
    'TDA: Persistence diagram P = {(b_i, d_i)} from Vietoris-Rips filtration of atom coordinates. Persistence images converted to fixed-length vectors v_TDA. Fusion: h_fused = TransEnc([v_TDA; h_LLM; h_GNN]). Strong cold-start generalization via LLM initialization.',
    'BindingDB, DAVIS, Yamanishi_08',
    'Yamanishi_08 S2 (cold-drug): AUC = 0.921; S3 (cold-target): AUC = 0.883; DAVIS: CI = 0.906',
    'TDA computation is expensive for large molecular datasets. Requires atom coordinates (3D structure or conformation generation). LLMs require substantial GPU memory. TDA features may be redundant with GNN structural features in some cases.'
  ),

  ...modelBlock(
    'HMSA-DTI', 2024, 'Bian et al.', '(Bian et al., 2024)',
    'Hierarchical Multimodal Self-Attention GNN',
    'HMSA-DTI employs a hierarchical multimodal self-attention framework that captures both intra-modal and inter-modal dependencies across three input modalities: SMILES strings, molecular graphs, and protein sequences. Hierarchical attention first aggregates within each modality, then applies cross-modal attention between drug and protein representations, providing multi-scale interaction modeling.',
    'Three-modality hierarchical attention that integrates character-level SMILES, graph-level molecular structure, and protein sequence in a unified architecture—the only model to exploit all three drug representation types simultaneously.',
    'Intra-modal: h_SMILES = MHA(H_SMILES), h_graph = MHA(H_GNN), h_prot = MHA(H_prot). Inter-modal: h_dp = MHA([h_SMILES; h_graph], h_prot, h_prot). Final: h = W_f [h_SMILES; h_graph; h_dp].',
    'Yamanishi_08, BindingDB',
    'Yamanishi_08: AUC = 0.962, AUPR = 0.938',
    'Three-modality architecture increases training complexity and data requirements. SMILES and graph representations contain overlapping information, potentially creating redundancy. No formal cold-start evaluation in S2/S3 settings. Foundation model pretraining not incorporated.'
  ),

  ...modelBlock(
    'DeepGS (GAT+BiGRU)', 2022, 'Zhijian et al.', '(Zhijian et al., 2022)',
    'Graph Attention Network + Bidirectional GRU',
    'DeepGS is a prototypical GNN+RNN hybrid model. It employs a Graph Attention Network (GAT) for molecular graph encoding of drug molecules and a Bidirectional GRU (BiGRU) for protein sequence encoding. The GAT captures drug topology with attention-weighted neighbor aggregation, while the BiGRU captures both upstream and downstream sequence dependencies in protein amino acid chains. Representations are fused via concatenation.',
    'Clean and well-motivated GNN+RNN hybrid establishing GAT+BiGRU as an effective dual-branch architecture for DTI/DTA, demonstrating that pairing topology-aware drug encoding with context-aware protein sequence modeling outperforms single-architecture approaches.',
    'GAT drug: h_v = sigma(SUM_{j in N(v)} alpha_vj W h_j) per Eq. (4)-(6). BiGRU protein: h_t = [GRU_fwd(x_t); GRU_bwd(x_t)] per Eq. (15)-(19). Context: h_P = Attn-Pool(h_1,...,h_T). Final: y = MLP([h_G; h_P]).',
    'DAVIS, Yamanishi_08',
    'DAVIS: CI = 0.892; Yamanishi_08: AUC = 0.941',
    'Static concatenation fusion; no cross-modal attention between GAT atom embeddings and BiGRU residue embeddings. No pre-trained foundation model embeddings. Limited cold-start generalization evaluation. No explicit interpretability beyond GAT attention weights.'
  ),

  ...modelBlock(
    'GDGRU-DTA', 2022, 'Zhijian et al.', '(Zhijian et al., 2022)',
    'GNN + Double GRU (Drug + Protein)',
    'GDGRU-DTA employs GNN layers for drug molecular graph encoding and a double GRU architecture for both drug SMILES sequence and protein amino acid sequence encoding. This dual-level drug encoding captures both structural topology (via GNN) and sequential grammar of SMILES (via GRU), while the protein GRU encodes residue-level sequential dependencies.',
    'Double GRU strategy that applies RNN encoding to both SMILES character sequences and protein sequences simultaneously, complementing GNN structural encoding with sequential context at the character level—a unique dual-drug-representation approach.',
    'Drug: h_GNN (from Eq. 1-2), h_SMILES (from GRU over SMILES chars). Protein: h_prot (from GRU over amino acids). Final: h_fused = MLP([h_GNN; h_SMILES; h_prot]).',
    'DAVIS, KIBA',
    'DAVIS: CI = 0.889; KIBA: CI = 0.878',
    'SMILES GRU and GNN encode overlapping information. No cross-modal attention. Triple concatenation may introduce redundancy. No pre-trained embeddings. Cold-start not evaluated.'
  ),

  ...modelBlock(
    'MMDG-DTI', 2025, 'Hua et al.', '(Hua et al., 2025)',
    'Multimodal Feature Fusion + Domain Generalization',
    'MMDG-DTI addresses cross-dataset generalization through a domain generalization framework applied to multimodal drug–protein representations. Drug features are encoded from molecular graphs using GNN, and protein features from sequences using CNN/RNN. A domain adversarial training strategy aligns feature distributions across source datasets, enabling better transfer to unseen target datasets.',
    'Explicit domain generalization through adversarial training for DTI, enabling the model to learn domain-invariant multimodal representations that transfer across datasets with different experimental protocols—addressing a critical gap in cross-dataset transferability.',
    'Domain discriminator D: min_{theta_enc} max_{theta_D} L_DTI - lambda * L_domain. Domain loss: L_domain = BCE(D(h_fused), domain_label). Generalization: encoded features become domain-invariant while maintaining DTI prediction accuracy.',
    'BindingDB (train) → DAVIS, KIBA (test transfer)',
    'BindingDB->DAVIS CI = 0.878 (cross-dataset); intra-dataset DAVIS CI = 0.906',
    'Adversarial training can be unstable; requires careful tuning of lambda. Domain labels require access to multiple source datasets during training. Fusion is concatenation-based without dynamic cross-modal attention.'
  ),

  ...modelBlock(
    'GS-DTI', 2025, 'Yu et al.', '(Q. Yu et al., 2025)',
    'Graph-Structure-Aware Framework + LLM',
    'GS-DTI integrates graph-structure-aware drug encoding with Large Language Model embeddings for both drug (via SMILES LLM) and protein (via protein LLM) representations. A graph structure awareness module explicitly identifies local subgraph patterns (rings, functional groups) and globally relevant motifs in the molecular graph, combining structural and semantic LLM features for richer drug representation.',
    'Graph-structure-aware encoding that explicitly identifies and weights structurally significant local motifs (rings, functional groups) within the molecular graph, combining graph topology awareness with LLM semantic understanding in a unified framework.',
    'Structure-aware: h_motif = GNN(G) with motif-level pooling. LLM: h_LLM = LLM(SMILES). Drug: h_d = W_d [h_motif; h_LLM]. Protein: h_p = LLM(FASTA). Fusion: h_fused = CrossAttn(h_d, h_p).',
    'BindingDB, DAVIS, DrugBank',
    'BindingDB: AUC = 0.961, AUPR = 0.952; DAVIS: CI = 0.901',
    'LLM inference is computationally expensive. Motif identification is heuristic. Cross-dataset cold-start formally evaluated only partially. Interpretability limited to attention weights without biological validation against binding site data.'
  ),

  ...modelBlock(
    'IHDFN-DTI', 2025, 'Zhang et al.', '(Y. Zhang et al., 2025)',
    'Interpretable Hybrid Deep Feature Fusion Network',
    'IHDFN-DTI builds an interpretable hybrid model by combining GNN-based drug structural encoding with Transformer-based protein sequence encoding, fusing them through a multi-head cross-attention module. An intrinsic interpretability module attributes predictions to specific drug atom substructures and protein residue regions through attention weight analysis, validated against known binding sites.',
    'Interpretable hybrid fusion with explicit post-hoc validation of attention-based attribution against experimentally known binding sites, making IHDFN-DTI a methodologically rigorous XAI model for DTI.',
    'Drug: h_d = GNN(G) (Eq. 1-2). Protein: h_p = TransEnc(FASTA). Cross-attn: h_dp = MultiHead(h_d, h_p, h_p) (Eq. 21). Interpretability: attention map A_{dp} visualized as binding site heatmap. Validation: compare A_{dp} against PDB crystal contacts.',
    'DAVIS, KIBA, BindingDB',
    'DAVIS: CI = 0.905, RMSE = 0.219; KIBA: CI = 0.912; Interpretability accuracy: >80% overlap with known binding residues',
    'Cross-attention is quadratic in sequence lengths. Validation against PDB binding sites requires 3D structural data not always available. Cold-start generalization limited—no pre-trained foundation model initialization reported.'
  ),

  ...modelBlock(
    'SS-DTI', 2025, 'Chun et al.', '(Chun et al., 2025)',
    'Semantic + Structural Information Integration',
    'SS-DTI integrates semantic information from biomedical text descriptions of drugs and proteins (via text embeddings) with structural information from molecular graphs (GNN) and protein sequences (RNN). A learned fusion module combines semantic context with structural features, addressing cases where structural data alone is insufficient for accurate DTI prediction.',
    'Explicit integration of semantic (text-based) drug and protein descriptors with structural (graph/sequence) encodings, enriching representations with domain knowledge not encoded in molecular topology or amino acid sequence alone.',
    'Semantic: h_sem_d = BERT(drug_description), h_sem_p = BERT(prot_description). Structural: h_str_d = GNN(G), h_str_p = RNN(FASTA). Fusion: h_d = W_ds [h_sem_d; h_str_d], h_p = W_ps [h_sem_p; h_str_p]. Prediction: MLP([h_d; h_p]).',
    'BindingDB, Human',
    'Human: AUC = 0.974, AUPR = 0.971; BindingDB: AUC = 0.958',
    'Biomedical text descriptions may be incomplete or inconsistent. BERT semantic embeddings require large GPU memory. Fusion is concatenation-based without dynamic cross-modal interaction. Cold-start not formally evaluated.'
  ),

  ...modelBlock(
    'MINDG', 2024, 'Yang et al.', '(Yang et al., 2024)',
    'Multi-View Integrated Learning Algorithm',
    'MINDG employs an integrated learning algorithm that combines multiple drug and protein feature views (graph, sequence, physicochemical, network topology) using a weighted multi-view fusion strategy. Adaptive view weighting learns the relative importance of each feature type for a given drug–target pair, providing a flexible, data-driven multi-view DTI framework.',
    'Adaptive multi-view weighting that dynamically assigns importance to different feature types (graph, sequence, network, physicochemical) for each drug–target pair, enabling data-driven feature selection across heterogeneous modalities.',
    'Multi-view: H = {H_graph, H_seq, H_physchem, H_net}. Adaptive weights: w_k = softmax(MLP(H_k)). Fused: h = SUM_k w_k H_k. Classification: y = MLP(h).',
    'BindingDB, Yamanishi_08',
    'Yamanishi_08: AUC = 0.958, AUPR = 0.943',
    'Multi-view construction increases preprocessing complexity. Adaptive weighting adds parameters. Some feature views (network) face cold-start limitations. No cross-modal attention between drug and protein atom/residue embeddings.'
  ),

  ...modelBlock(
    'NHGNN-DTA', 2023, 'He et al.', '(He et al., 2023)',
    'Node-Adaptive Hybrid GNN',
    'NHGNN-DTA introduces a node-adaptive mechanism within the GNN drug encoder that dynamically adjusts the aggregation function based on local node (atom) properties—using different aggregation functions for atoms with different chemical environments (e.g., aromatic vs. aliphatic). This adaptability provides richer drug representations. Protein sequences are encoded using GRU with attention pooling.',
    'Node-adaptive GNN aggregation that applies different message-passing functions based on atom type and chemical environment, providing more expressive and chemically meaningful drug molecular representations than uniform aggregation.',
    'Adaptive aggregation: h_v^(l+1) = sigma(W_{type(v)} AGG_{type(v)}({h_u : u in N(v)})), where type(v) in {aromatic, aliphatic, ring, ...}. Protein: h_P = AttnPool(GRU(FASTA)). Prediction: MLP([h_G; h_P]).',
    'DAVIS, KIBA',
    'DAVIS: CI = 0.904, RMSE = 0.218; KIBA: CI = 0.916, RMSE = 0.131',
    'Node type categorization is heuristic. Adaptive weights increase parameter count. No cross-modal attention fusion. Foundation model embeddings not incorporated. Cold-start not evaluated.'
  ),

  ...modelBlock(
    'HiGraphDTI', 2024, 'Liu et al.', '(B. Liu et al., 2024)',
    'Hierarchical Graph Representation Learning',
    'HiGraphDTI constructs hierarchical molecular graph representations that capture both atom-level (local) and substructure-level (global) features through multiple pooling stages. A hierarchical GNN aggregates atom features into functional group embeddings, which are further aggregated into molecular-level representations. Protein sequences are encoded using a bidirectional encoder, with both hierarchical drug and protein representations fused for DTI/DTA prediction.',
    'Multi-scale hierarchical drug graph encoding that captures features at atom, functional group, and molecular levels, providing a coarse-to-fine structural representation that bridges local and global molecular understanding.',
    'Hierarchy level 1: h_atom = GNN_atom(G). Level 2: h_group = GNN_group(G_coarsened) where G_coarsened clusters atoms into functional groups. Level 3: h_mol = READOUT(h_group). Protein: h_prot = BiEncoder(FASTA). Prediction: MLP([h_mol; h_prot]).',
    'DAVIS, KIBA, BindingDB',
    'DAVIS: CI = 0.902; KIBA: CI = 0.908; BindingDB AUC = 0.953',
    'Coarsening (functional group identification) is heuristic. Hierarchical GNN is computationally expensive. Cross-modal attention between hierarchical levels and protein not explored. Cold-start not formally evaluated.'
  ),

  ...modelBlock(
    'MFCADTI', 2025, 'Quan et al.', '(Quan et al., 2025)',
    'Multiple Feature Cross-Attention Mechanism',
    'MFCADTI integrates multiple drug feature types (molecular graph, SMILES-derived fingerprints, physicochemical properties) and protein features (sequence embedding, physicochemical descriptors) through a cross-attention mechanism that enables each feature type to attend to others. This multi-source cross-attention fusion yields a rich, interaction-aware joint representation for DTI prediction.',
    'Multi-source cross-attention that enables each drug feature type to attend to each protein feature type and vice versa, modeling feature-type-specific cross-modal interactions that single cross-attention modules miss.',
    'Multi-source drug features: {h_graph, h_fp, h_phys}. Cross-attention each pair: A_{i,j} = Attn(h_i, h_j, h_j) for i in drug features, j in protein features. Fused: h = MLP(CONCAT(A_{i,j} for all i,j)). Prediction: sigmoid(MLP(h)).',
    'BindingDB, Yamanishi_08',
    'BindingDB: AUC = 0.964, AUPR = 0.950; Yamanishi_08: AUC = 0.960',
    'Multi-source feature construction increases preprocessing overhead. Cross-attention across all feature pairs grows quadratically. Cold-start performance reported only on warm-split settings. Foundation model embeddings not incorporated.'
  ),

  ...modelBlock(
    'ViDTA', 2024, 'Li et al.', '(M. Li et al., 2024)',
    'Virtual Graph Nodes + Attention-Based Feature Fusion',
    'ViDTA introduces virtual graph nodes as learnable global context nodes in the drug molecular graph. These virtual nodes aggregate information from all atom nodes in each message-passing iteration, acting as global receptors that overcome the limited receptive field of standard GNN message passing. Protein features are extracted using CNN encoders with attention pooling, and fused with the drug representation via an attention-based fusion module.',
    'Virtual graph node mechanism that creates global context nodes in the molecular graph, enabling all-node information exchange without the over-smoothing risk of deep GNN stacking—providing global molecular context while maintaining local structural detail.',
    'Virtual nodes: add V_virtual to G such that V_virtual is connected to all atoms. Message passing: h_virtual^(l) = AGG({h_v^(l-1) : v in V}) (global aggregation). h_v^(l) includes messages from h_virtual^(l-1). h_G = READOUT([h_atoms; h_virtual]).',
    'DAVIS, KIBA',
    'DAVIS: CI = 0.905; KIBA: CI = 0.914',
    'Virtual nodes increase graph size and message-passing cost. Optimal number of virtual nodes is a sensitive hyperparameter. Cross-modal fusion is attention-based but not gated. Cold-start not evaluated. Foundation model embeddings not used.'
  ),

  // ─── 5.8 Cold-Start Focused Models ─────────────────────────────────────
  h2('5.8 Cold-Start Focused Models'),

  ...modelBlock(
    'DrugBAN', 2023, 'Bai et al.', '(Bai et al., 2023)',
    'Bilinear Attention Network + Domain Adaptation',
    'DrugBAN uses a bilinear attention network (BAN) to compute pairwise interactions between drug atom embeddings (from GNN) and protein residue embeddings (from CNN/RNN), producing an interaction map that explicitly models atom-residue binding pairs. A domain adaptation module aligns feature distributions between known and novel drug–target pairs, explicitly targeting cold-start generalization.',
    'Bilinear attention network that computes a full pairwise drug atom-protein residue interaction matrix, providing fine-grained interaction modeling beyond global embedding similarity—combined with domain adaptation for cold-start scenarios.',
    'BAN: I = h_d^T W_B h_p, where W_B in R^(d_d x d_p) is a bilinear parameter matrix. Attended: c = SOFTMAX(I) * h_p. Domain adaptation: MMD(h_source, h_target) minimized during training to align distributions.',
    'BindingDB, Human, C. elegans (cold-drug and cold-target splits)',
    'BindingDB cold-drug: AUC = 0.919; cold-target: AUC = 0.903; warm: AUC = 0.953',
    'Bilinear interaction matrix is O(n*m) in atom and residue count. Domain adaptation requires access to target-domain data during training. Foundation model embeddings not incorporated in original implementation.'
  ),

  ...modelBlock(
    'CoaDTI', 2022, 'Wang et al.', '(Y. Wang et al., 2022)',
    'Co-Attention Network',
    'CoaDTI employs a co-attention mechanism that simultaneously learns attention weights for drug features conditioned on protein features, and attention weights for protein features conditioned on drug features. This conditional mutual attention allows drug and protein representations to refine each other iteratively, providing richer cross-modal interaction than one-directional attention.',
    'Conditional co-attention enabling drug and protein representations to mutually guide feature refinement in both directions simultaneously—a simpler precursor to the full cross-attention fusion used in more recent models.',
    'Co-attention: A_d = softmax(F_d W_c F_p^T) (drug attn conditioned on protein). A_p = softmax(F_p W_c F_d^T) (protein attn conditioned on drug). Refined: h_d\' = A_d F_d, h_p\' = A_p F_p. Prediction: MLP([h_d\'; h_p\']).',
    'Human, C. elegans, BindingDB',
    'Human: AUC = 0.971; BindingDB: AUC = 0.951',
    'Co-attention without gating may not adequately balance cross-modal vs. original modality information. Simpler drug/protein encoders (not GNN/RNN). Cold-start performance not systematically reported with S1/S2/S3 protocol.'
  ),

  ...modelBlock(
    'ICAN', 2023, 'Song et al.', '(Song et al., 2023)',
    'Interaction-Aware Cross-Attention Network',
    'ICAN introduces an interaction-aware cross-attention module that conditions the cross-attention computation on predicted interaction patterns (e.g., known binding pharmacophores). This interaction-conditioned attention focuses cross-modal feature alignment on interaction-relevant drug and protein regions, improving both accuracy and interpretability by explicitly modeling known pharmacophoric interaction types.',
    'Pharmacophore-conditioned cross-attention where known interaction type information guides the cross-modal alignment process, incorporating domain-specific interaction knowledge into the neural attention mechanism.',
    'Interaction-conditioned attn: K_p\' = K_p + Embed(interaction_type). A = softmax(Q_d (K_p\')^T / sqrt(d)). This pharmacophore conditioning focuses attention on known interaction-relevant regions.',
    'BindingDB, DrugBank',
    'BindingDB: AUC = 0.958, AUPR = 0.943',
    'Interaction-type conditioning requires pharmacophore annotations not always available. Framework is classification-focused. Cold-start formally evaluated but with limited datasets.'
  ),

  ...modelBlock(
    'BACPI', 2023, 'Ji et al.', '(Ji et al., 2023)',
    'Bilinear Attention Cross-Modal Protein Interaction',
    'BACPI employs bilinear attention to model pairwise cross-modal interactions between drug atoms and protein residues. Unlike standard attention, bilinear attention captures multiplicative relationships between modalities through a learnable weight matrix, providing more expressive cross-modal interaction modeling. A protein interaction network is additionally used to enrich protein representations through graph-based context.',
    'Bilinear cross-modal attention combined with protein–protein interaction (PPI) network-enriched protein representations, integrating both sequence and network topology for protein encoding alongside fine-grained drug-protein cross-modal interaction.',
    'Bilinear: B = h_d W_B h_p^T, where W_B in R^(d x d). Cross-modal context: c_d = softmax(B) h_p. PPI enrichment: h_p\' = GNN_PPI(h_p, PPI_graph). Prediction: MLP([c_d; h_p\']).',
    'Human, C. elegans, BindingDB',
    'Human: AUC = 0.973, AUPR = 0.969; BindingDB: AUC = 0.960',
    'PPI network enrichment requires external PPI database. Bilinear attention scales quadratically. Pre-trained language model embeddings not incorporated in original model. Cold-start with novel proteins not comprehensively evaluated.'
  ),

  ...modelBlock(
    'ColdDTA (Ouyang et al.)', 2025, 'Ouyang et al.', '(Ouyang et al., 2025)',
    'Pre-Trained Multi-View Molecular Representations for Cold-Start',
    'ColdDTA addresses the cold-start problem by pre-training a multi-view molecular encoder on large-scale unlabeled drug and protein databases. Multiple views of each molecule are generated through structural, chemical, and semantic augmentation, and contrastive learning aligns representations across views to produce robust, generalizable embeddings. These pre-trained embeddings significantly improve DTA prediction for novel drugs and targets.',
    'Multi-view pre-training via contrastive learning across structural, chemical, and semantic augmentations of molecular data—learning transferable representations that generalize to novel drugs and targets without task-specific interaction data.',
    'Multi-view drug: {G_drug, SMILES_drug, DESC_drug}. Views: v_1, v_2 = augment(molecule). Contrastive: L_cl = -log(exp(sim(z_1, z_2)/tau) / DENOM). Pre-trained encoders fine-tuned on downstream DTI/DTA tasks. Cold-start: novel drugs use pre-trained features directly.',
    'DAVIS, KIBA, BindingDB (cold-drug, cold-target splits)',
    'DAVIS cold-drug: CI = 0.873 (vs. 0.847 baseline); cold-target: CI = 0.856; warm: CI = 0.903',
    'Multi-view augmentation must be carefully designed to preserve molecular identity. Pre-training requires large-scale datasets and GPU hours. Fine-tuning may overfit for small downstream datasets. Interpretability not addressed.'
  ),

  pb()
];
