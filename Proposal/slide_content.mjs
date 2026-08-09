// Shared slide-content data model for the PhD proposal defense deck.
// Consumed by build_pptx.mjs (PowerPoint) and build_beamer.mjs (LaTeX Beamer).
// Each equation carries two renderings: `p` (unicode plain-text, for PPTX) and `t` (real LaTeX, for Beamer).

export const META = {
  title: 'Enhanced Drug-Target Interaction Prediction Through Hybrid Deep Learning Approaches',
  shortTitle: 'H-GNN-RNN-DTI',
  presenter: 'Jamila Abdul-Hadi',
  matric: '24100625',
  supervisor: 'Assoc. Prof. Dr. Nurul Hashimah Ahamed Hassain Malim',
  school: 'School of Computer Sciences, Universiti Sains Malaysia',
  program: 'PhD Research Proposal Defense — Semester 2, 2025/2026',
};

// bullets: string = level-0 item; [text, level] = indented item
// eqs: {p, t} pairs
// notes: detailed speaker talking points

export const SLIDES = [
// ---------------------------------------------------------------- 1
{
  layout: 'title',
  notes: `Welcome the panel. State your name, matric number, program (PhD), and supervisor. Give the title once, clearly and slowly — it is dense ("hybrid deep learning", "drug-target interaction") so let it land. One-sentence framing before you advance: "Today I will walk through the problem motivating this work, the three research objectives, and — in most depth — the methodology I am proposing, including the mathematical formulation of the model." This tells the panel your talk is methodology-heavy on purpose, so they calibrate their expectations and questions accordingly. Keep this slide on screen for no more than 45-60 seconds.`
},
// ---------------------------------------------------------------- 2
{
  sec: 'Overview', title: 'Presentation Outline',
  bullets: [
    '1. Motivation & Problem Statement',
    '2. Research Questions and Objectives',
    '3. Scope of the Research',
    '4. Research Design — Three Pillars',
    '5. Methodology: Data Collection & Preprocessing',
    '6. Methodology: The H-GNN-RNN-DTI Architecture (mathematical formulation)',
    '7. Methodology: Training Strategy',
    '8. Methodology: Evaluation Protocol',
    '9. Methodology: Interpretability Framework',
    '10. Expected Outcomes, Timeline & Summary',
  ],
  notes: `Tell the panel explicitly that items 5-9 (all methodology) are the bulk of the talk, consistent with the "Chapter 3" emphasis of a proposal defense — this is the chapter examiners scrutinize hardest, because it is the chapter that has not been executed yet and is the basis on which they will judge feasibility. Signpost that you will slow down for the architecture and speed through items 1-4 since they are largely uncontested background. If your defense has a strict time budget (e.g., 20 minutes), mention it here and say you will keep to it, which reassures the panel you have rehearsed pacing.`
},
// ---------------------------------------------------------------- 3
{
  sec: 'Introduction', title: 'Motivation — The Drug Discovery Bottleneck',
  bullets: [
    'A single new chemistry-based drug costs ~US$2.6 billion and ~15 years to reach approval (Khojasteh et al., 2023)',
    'PubChem alone lists tens of millions of candidate compounds — exhaustive wet-lab testing against all targets is physically and economically infeasible',
    'Wet-lab assays and physics-based docking are accurate but slow, expensive, and require 3D target structures that are often unavailable',
    'Computational DTI prediction reframes discovery as a data-driven pattern-recognition problem — enabling virtual screening at scale',
    'Deep learning models drugs as molecular graphs and proteins as biological sequences — a natural fit for GNNs and RNNs respectively',
  ],
  notes: `Open with the economic hook — $2.6B / 15 years — because it is the single number that justifies the entire thesis to a non-specialist panel member. Then pivot to the technical framing: two heterogeneous data modalities (graph-structured drugs, sequence-structured proteins) is the crux that motivates a hybrid architecture rather than a single-paradigm model. If asked "why not just use a Transformer for everything," your answer is: SMILES-as-text throws away explicit bond topology that a graph encoder recovers for free, and a molecular graph representation has been repeatedly shown (GraphDTA, MGraphDTA) to outperform sequence-only drug encodings. Keep this slide brief — under 90 seconds — it is scene-setting, not the contribution.`
},
// ---------------------------------------------------------------- 4
{
  sec: 'Introduction', title: 'Problem Statement — Four Persistent Gaps',
  bullets: [
    'Weak cross-modal feature integration — GSRF-DTI, TTModel use static, late concatenation; no iterative drug↔protein interaction before prediction',
    'Limited multimodal representation learning — network/KG-level features substitute for direct GNN + RNN encoding of raw structure and sequence',
    'Poor cold-start generalization — models memorize seen drug/target patterns rather than learning transferable biochemical principles',
    'Black-box interpretability — Random Forest / KG-embedding backbones give no atom- or residue-level attribution for predictions',
    'Unaddressed class imbalance — confirmed interactions are vastly outnumbered by unlabeled/negative pairs, biasing training (Zhu et al. 2024, explicit future-work gap)',
  ],
  notes: `These five items map directly onto Objectives 1-3 in the next slides — say so explicitly ("Gap 1 motivates Objective 1; Gaps 2-3 motivate Objective 2; Gap 4 motivates Objective 3; Gap 5 is addressed as a training-strategy component across all objectives"). This is the single most important framing move in the whole talk: it shows the panel your objectives were derived from a gap analysis, not chosen arbitrarily. Cite that Zhu et al. (2024) — the GSRF-DTI authors themselves — flagged data imbalance as unresolved future work; using the original authors' own admission is more persuasive than your own critique of their paper.`
},
// ---------------------------------------------------------------- 5
{
  sec: 'Introduction', title: 'Why Existing Hybrid Models Fall Short',
  tbl: {
    head: ['Model', 'Fusion Strategy', 'Key Limitation'],
    rows: [
      ['GSRF-DTI (Zhu et al. 2024)', 'DeepWalk features → concatenation → Random Forest', 'No GNN/RNN encoders; static late fusion; no interpretability beyond feature importance'],
      ['TTModel (Li et al. 2024)', 'Knowledge-graph + textual/type embeddings', 'Ignores molecular graph topology and raw protein sequence entirely'],
      ['DTKGIN (Luo et al. 2024)', 'Intent-graph representation', 'Best cold-start baseline, but no dynamic attention fusion between structure and sequence'],
    ]
  },
  notes: `This slide is your literature-positioning move — use it to pre-empt the inevitable "how is this different from X" question. Walk left to right per row: what they fused, why it caps performance. Land on DTKGIN specifically since it is your strongest baseline (best cold-start results in the field) — acknowledge that directly ("DTKGIN is the state of the art we most need to beat") rather than letting an examiner surface it as a gotcha. Your architecture's distinguishing claim is the *combination* — GNN + RNN + dynamic gated cross-attention + pretrained embeddings + intrinsic interpretability — no existing model has all five simultaneously.`
},
// ---------------------------------------------------------------- 6
{
  sec: 'Introduction', title: 'Research Questions',
  bullets: [
    'RQ1 — How can a Gated Cross-Attention fusion mechanism effectively integrate GNN-based drug and RNN-based protein representations, and how does this improve DTI prediction over static concatenation?',
    'RQ2 — To what extent do pre-trained molecular/protein language embeddings combined with imbalance-aware learning improve generalization to unseen drugs, targets, and cross-dataset scenarios?',
    'RQ3 — Can an attention-enhanced hybrid model provide interpretable, biologically meaningful insight into key binding residues and pharmacophoric features?',
  ],
  notes: `Read each RQ once, slowly — do not paraphrase live, since the wording is precise and was likely scrutinized by your supervisor already. After RQ1, note it is answerable quantitatively (AUROC/AUPR delta vs. concatenation ablation — a controlled, isolatable comparison). After RQ2, note "generalization" is operationalized later via four explicit train/test split protocols, not left vague. After RQ3, flag that interpretability will be validated against real crystal-structure binding sites, not just visually inspected — this pre-empts "how do you know the attention maps mean anything" questions.`
},
// ---------------------------------------------------------------- 7
{
  sec: 'Introduction', title: 'Research Aim & Objectives',
  bullets: [
    'Aim — Design an enhanced hybrid deep learning model combining GNNs and RNNs through a novel dynamic cross-modal fusion mechanism to improve DTI prediction, addressing the four identified gaps.',
    'O1 — Design and evaluate a hybrid model with an advanced cross-modal fusion mechanism, achieving statistically significant improvement over concatenation-based fusion baselines.',
    'O2 — Develop an imbalance-aware, foundation-model-pretrained representation learning strategy that measurably improves performance on unseen drugs, unseen targets, and cross-dataset transfer (cold-start).',
    'O3 — Implement and benchmark an attention-based interpretability layer producing quantitative and visual explanations, validated against known binding sites, to support SAR studies.',
  ],
  notes: `Emphasize the word "statistically significant" in O1 and "measurably" in O2 — these are falsifiable, testable claims, not aspirational language, and a good proposal defense rewards objectives that can fail a hypothesis test. Preview here (one sentence) that your evaluation protocol later includes 5-seed runs with paired significance testing specifically to make O1 and O2 checkable, not just "the numbers went up." This is the slide to slow down on if you sense the panel is not yet oriented — everything after this slide is in service of these three objectives.`
},
// ---------------------------------------------------------------- 8
{
  sec: 'Introduction', title: 'Scope of the Research',
  cols: {
    l: { h: 'In Scope', items: [
      'Binary DTI classification + continuous DTA regression (pKd/pKi/pIC50)',
      'SMILES → molecular graphs (RDKit); FASTA → ESM-2 embeddings',
      'Benchmarks: BindingDB, DAVIS, KIBA, DrugBank, ChEMBL, Luo_17, Yamanishi_08',
      'H-GAT + BiLSTM/BiGRU + Gated Cross-Attention architecture',
      'Cold-start evaluation (unseen drug / target / pair) + cross-dataset transfer',
      'Attention-based interpretability with case-study validation',
    ]},
    r: { h: 'Out of Scope', items: [
      'Wet-lab / experimental validation of predicted interactions',
      'Non-small-molecule ligands (e.g., peptide or antibody therapeutics)',
      'Large-scale industrial / production deployment',
      '3D structure-based docking simulation',
    ]},
  },
  notes: `State the out-of-scope list with confidence, not apology — a well-bounded scope is a strength in a proposal defense, not a weakness. If asked "why not validate experimentally," the honest and sufficient answer is: this is a computational methods PhD, wet-lab validation would require a different supervisory team, budget, and ethics approval, and the interpretability case studies (against PDB crystal structures) provide a proxy validation that is standard practice in this subfield (cite EHIGN, GraphATT-DTA as precedent).`
},
// ---------------------------------------------------------------- 9
{
  sec: 'Research Design', title: 'Research Design — Three Pillars',
  bullets: [
    'Quantitative, computational, experimental design — build, train, benchmark, ablate, interpret',
    'Pillar 1 (→ O1): Dynamic cross-modal feature integration — H-GAT drug encoder + BiGRU protein encoder + Gated Cross-Attention',
    'Pillar 2 (→ O2): Transfer learning for cold-start generalization — pretrained embeddings + imbalance-aware training + rigorous split protocols',
    'Pillar 3 (→ O3): Intrinsic explainability — attention attribution + Grad-CAM-style visualization + case-study validation',
    'Pipeline: Data Collection → Preprocessing → Encoders → Fusion → Prediction Head → Training → Evaluation → Interpretability',
  ],
  notes: `This is the map you will keep returning to. Say explicitly: "Everything from this point forward in the methodology section is organized around these three pillars." The pipeline bullet is the flowchart from the proposal (Fig. 3.1) condensed to one line — if you have the actual flowchart figure, show it here instead of/alongside the text. Keep this slide to under a minute; it is a table of contents for the methodology, not new content.`
},
// ---------------------------------------------------------------- 10
{
  sec: 'Methodology · Data', title: 'Data Collection — Benchmark Datasets',
  tbl: {
    head: ['Dataset', 'Scale', 'Task', 'Key Feature'],
    rows: [
      ['BindingDB', 'Large', 'DTI / DTA', 'Extensive Ki, Kd, IC50 affinity data across diverse targets'],
      ['DAVIS', 'Medium', 'DTA', 'Kinase-focused affinity regression benchmark'],
      ['KIBA', 'Medium', 'DTA', 'Composite KIBA-score affinity regression benchmark'],
      ['DrugBank', 'Supplementary', 'DTI / pretraining', 'Generalizability testing and self-supervised pretraining source'],
      ['ChEMBL', 'Large', 'DTI & DTA', 'Comprehensive bioactivity database; supports both tasks'],
      ['Luo_17', 'Large', 'DTI (binary)', 'Heterogeneous network with drug-drug / protein-protein relations'],
      ['Yamanishi_08', 'Small', 'DTI (binary)', 'Gold-standard curated set — enzyme, ion channel, GPCR, nuclear receptor'],
    ]
  },
  notes: `Do not read every cell — group verbally instead: "DAVIS and KIBA give us the regression/affinity side of the work; Luo_17 and Yamanishi_08 give us the classification side and are the datasets used by our three main baselines, GSRF-DTI, TTModel and DTKGIN, which lets us compare like-for-like; BindingDB and ChEMBL are large enough to support the cold-start and cross-dataset transfer experiments; DrugBank additionally supplies unlabeled molecules for self-supervised pretraining." That one sentence turns a dry table into a rationale.`
},
// ---------------------------------------------------------------- 11
{
  sec: 'Methodology · Data', title: 'Preprocessing I — Drug Representation',
  bullets: [
    'SMILES strings parsed with RDKit; duplicates removed; molecules mapped to dataset identifiers',
    'Atom (node) features: atomic number, degree, hybridization, aromaticity, formal charge',
    'Bond (edge) features: bond type, conjugation, ring membership',
    'Pre-trained ChemBERTa embeddings (seyonec/ChemBERTa-zinc-base-v1) fused in as additional node/molecule features for transfer learning',
  ],
  eqs: [
    { p: 'G_d = (V, E)          V = atoms (nodes),  E = bonds (edges)', t: '\\mathcal{G}_d = (V, E), \\qquad V = \\text{atoms},\\; E = \\text{bonds}' },
  ],
  notes: `Keep this fast — this is standard cheminformatics pipeline, low examiner risk. The one thing worth pausing on: ChemBERTa fusion is not just "extra features," it is the transfer-learning lever for Objective 2 (cold-start) — a molecule's ChemBERTa embedding encodes chemical semantics learned from ~77M SMILES strings, so even a drug never seen during DTI training has a meaningful representation. Say that sentence explicitly since it is the bridge to the cold-start story two objectives later.`
},
// ---------------------------------------------------------------- 12
{
  sec: 'Methodology · Data', title: 'Preprocessing II — Protein Representation',
  bullets: [
    'FASTA amino-acid sequences tokenized and embedded via pre-trained ESM-2 (facebook/esm2_t6_8M_UR50D, 320-dim; 650M/1280-dim variant for Luo_17)',
    'Residue-level contextual embeddings capture local chemistry and long-range evolutionary dependencies from large-scale unsupervised pretraining',
    'Sequences padded/truncated to a fixed maximum length (e.g., 1200 residues) for batch processing',
    'Two operating modes: full residue sequence (B,L,320) for the BiGRU path, or mean-pooled (B,320) for a lightweight linear-projection path',
  ],
  notes: `Explain the two-mode design as an engineering necessity, not an inconsistency: some datasets/experiments need the full sequential signal for the BiGRU, others (ablations, faster iteration) use the cheaper mean-pooled projection — the encoder auto-selects based on input tensor shape. If asked why ESM-2 over ProtT5 or a simple one-hot/BLOSUM encoding: ESM-2 is self-supervised on hundreds of millions of sequences and has been repeatedly shown to transfer well to downstream structure/function tasks, which is precisely the property needed for cold-start generalization to unseen proteins (Objective 2).`
},
// ---------------------------------------------------------------- 13
{
  sec: 'Methodology · Data', title: 'Preprocessing III — Labels & Data Splitting',
  bullets: [
    'Positive labels = experimentally validated interactions; negatives via unknown-negative sampling to minimize false-negative contamination',
    'Stratified negative sampling ratios (e.g., 1:1, 1:10) + imbalance-aware losses (weighted BCE, focal loss)',
    'Regression targets standardized via −log10 transform: Kd/Ki/IC50 → pKd/pKi/pIC50',
    'Warm-start: random 10-fold CV  ·  Cold-drug: drug-disjoint  ·  Cold-target: target-disjoint  ·  Cold-pair: pair-disjoint  ·  Cross-dataset: train on one benchmark, test on another',
  ],
  notes: `This slide quietly sets up the entire evaluation-protocol section — flag that explicitly ("the four split protocols listed here are the same four you will see again in the evaluation section, applied consistently across every experiment"). On negative sampling: be ready for "how do you know your negatives are true negatives" — the honest answer is you don't, absolutely; you use the field-standard mitigation (unknown-negative sampling with careful ratio control) and this is exactly the kind of label noise that motivates using focal loss / weighted BCE rather than plain BCE.`
},
// ---------------------------------------------------------------- 14
{
  sec: 'Methodology · Architecture', title: 'H-GNN-RNN-DTI — System Overview',
  bullets: [
    'Symmetric dual-branch network: structural drug branch ‖ sequential protein branch',
    'Component 1 — Modality-specific encoders: Hierarchical GAT (drug) and BiGRU (protein)',
    'Component 2 — Gated Cross-Attention Fusion: dynamic, bidirectional drug↔protein interaction',
    'Component 3 — Task-specific prediction heads: DTI classification (sigmoid/softmax) and DTA regression (linear)',
    'End-to-end differentiable — trained jointly, not as separately-tuned stages',
  ],
  notes: `Show the architecture diagram here if available (Fig. 3.3 in the proposal). This is the slide where you say "I will now walk through each of these three components in detail, with the mathematical formulation, over the next several slides" — an explicit verbal signpost matters because the next 8-9 slides are dense and the panel needs to know they are still inside one coherent explanation, not jumping topics. Point out the symmetry deliberately: the drug and protein branches are structurally parallel (encode → attend → gate → pool), which is a design choice, not an accident — it keeps the fusion mechanism well-defined in both directions.`
},
// ---------------------------------------------------------------- 15
{
  sec: 'Methodology · Drug Encoder', title: 'Drug Encoder (I) — Graph Attention Message Passing',
  bullets: [
    'Node initialization fuses physicochemical descriptors with ChemBERTa semantics',
    'Hierarchical GAT: 3 stacked layers, 8 attention heads per layer',
    'At each layer, every atom aggregates a learned, attention-weighted message from its bonded neighbors',
  ],
  eqs: [
    { p: 'h_i^(0) = W_0 [x_i ‖ c_i] + b_0', t: 'h_i^{(0)} = W_0\\,[x_i \\,\\Vert\\, c_i] + b_0' },
    { p: 'e_ij^(l,k) = LeakyReLU( a_k^T [W_k h_i^(l) ‖ W_k h_j^(l) ‖ W_e b_ij] )', t: 'e_{ij}^{(l,k)} = \\mathrm{LeakyReLU}\\!\\left(a_k^{\\top}\\big[W_k h_i^{(l)} \\,\\Vert\\, W_k h_j^{(l)} \\,\\Vert\\, W_e b_{ij}\\big]\\right)' },
    { p: 'α_ij^(l,k) = exp(e_ij^(l,k)) / Σ_{u∈N(i)} exp(e_iu^(l,k))', t: '\\alpha_{ij}^{(l,k)} = \\dfrac{\\exp\\!\\big(e_{ij}^{(l,k)}\\big)}{\\sum_{u \\in \\mathcal{N}(i)} \\exp\\!\\big(e_{iu}^{(l,k)}\\big)}' },
    { p: 'h_i^(l+1) = ‖_{k=1}^{K} σ( Σ_{j∈N(i)∪{i}} α_ij^(l,k) W_k^(l) h_j^(l) )', t: 'h_i^{(l+1)} = \\mathop{\\Big\\Vert}\\limits_{k=1}^{K} \\sigma\\!\\left(\\sum_{j \\in \\mathcal{N}(i)\\cup\\{i\\}} \\alpha_{ij}^{(l,k)} W_k^{(l)} h_j^{(l)}\\right)' },
  ],
  notes: `Walk the four equations top to bottom as a story, not a wall of symbols: (1) each atom starts with a feature vector that is chemistry-plus-ChemBERTa; (2) for every bonded neighbor pair we score how relevant that neighbor is, conditioned on bond features b_ij — this is why it's a *graph attention* network and not plain message passing; (3) that score is normalized with softmax over the neighborhood so attention weights sum to 1; (4) the new atom representation is the attention-weighted sum of neighbor messages, computed independently across K=8 heads and concatenated — multi-head so the model can attend to different chemical relationships (e.g., one head tracks aromaticity, another tracks charge) simultaneously. Stacking 3 layers means information from a 3-bond neighborhood reaches every atom, which is enough to capture functional groups and small rings without over-smoothing.`
},
// ---------------------------------------------------------------- 16
{
  sec: 'Methodology · Drug Encoder', title: 'Drug Encoder (II) — Hierarchical Readout',
  bullets: [
    'After L=3 message-passing layers, atom-level states are aggregated into one molecule-level vector',
    'Mean pooling captures overall composition; max pooling captures the single most salient substructure',
    'Both are concatenated with a molecule-level ChemBERTa embedding before a final MLP projection',
  ],
  eqs: [
    { p: 'z_mean = (1/|V|) Σ_i h_i^(L)', t: 'z_{\\text{mean}} = \\frac{1}{|V|}\\sum_{i \\in V} h_i^{(L)}' },
    { p: 'z_max = max_i h_i^(L)', t: 'z_{\\text{max}} = \\max_{i \\in V} h_i^{(L)}' },
    { p: 'z_d = MLP( [z_mean ‖ z_max ‖ c_mol] )', t: 'z_d = \\mathrm{MLP}\\big([z_{\\text{mean}} \\,\\Vert\\, z_{\\text{max}} \\,\\Vert\\, c_{\\text{mol}}]\\big)' },
  ],
  notes: `The rationale for combining mean AND max pooling (not just one): mean pooling is a smooth summary that reflects the whole molecule's composition, but a small binding-relevant motif (e.g. one halogen substituent) can get diluted by averaging over a large molecule — max pooling preserves that single strongest signal per feature dimension. This dual-pooling-plus-pretrained-embedding readout is what CLAUDE.md/config.py calls the "mean/max pooling + ChemBERTa fusion" drug encoder design — if asked for an ablation, note that GNN-only vs. full-model comparisons in your evaluation protocol will directly test whether this fusion adds value over the GAT layers alone.`
},
// ---------------------------------------------------------------- 17
{
  sec: 'Methodology · Protein Encoder', title: 'Protein Encoder (I) — Bidirectional GRU',
  bullets: [
    'Input: ESM-2 contextual embeddings per residue, x_t ∈ ℝ^320 (or ℝ^1280 → projected for Luo_17)',
    '2 stacked layers, forward and backward GRU passes combined at every position',
    'Captures both N-to-C and C-to-N contextual dependencies — binding-relevant residues can depend on either direction',
  ],
  eqs: [
    { p: 'r_t = σ(W_r x_t + U_r h_{t-1}→ + b_r)', t: 'r_t = \\sigma\\!\\left(W_r x_t + U_r \\overrightarrow{h}_{t-1} + b_r\\right)' },
    { p: 'u_t = σ(W_u x_t + U_u h_{t-1}→ + b_u)', t: 'u_t = \\sigma\\!\\left(W_u x_t + U_u \\overrightarrow{h}_{t-1} + b_u\\right)' },
    { p: 'ĥ_t = tanh(W_h x_t + U_h(r_t ⊙ h_{t-1}→) + b_h)', t: '\\hat{h}_t = \\tanh\\!\\left(W_h x_t + U_h(r_t \\odot \\overrightarrow{h}_{t-1}) + b_h\\right)' },
    { p: 'h_t→ = (1−u_t) ⊙ h_{t-1}→ + u_t ⊙ ĥ_t     (backward h_t← symmetric)', t: '\\overrightarrow{h}_t = (1-u_t)\\odot \\overrightarrow{h}_{t-1} + u_t \\odot \\hat{h}_t \\qquad (\\text{backward } \\overleftarrow{h}_t \\text{ symmetric})' },
    { p: 'h_t = [h_t→ ‖ h_t←]', t: 'h_t = \\big[\\overrightarrow{h}_t \\,\\Vert\\, \\overleftarrow{h}_t\\big]' },
  ],
  notes: `You do not need to derive the GRU gates from scratch live — say "this is the standard GRU update, reset gate r_t and update gate u_t, run in both directions" and spend your time on WHY bidirectional matters here: a residue's role in binding is influenced by residues on both sides of it in the folded structure's local context, and BiGRU is a lightweight way to approximate that without full 3D structure. If asked "why GRU not LSTM": GRU has fewer parameters, trains faster, and prior DTI literature (Zhijian et al. 2022) shows comparable performance to LSTM for protein sequence modeling at lower cost — your config also supports BiLSTM as a swappable variant for the ablation study.`
},
// ---------------------------------------------------------------- 18
{
  sec: 'Methodology · Protein Encoder', title: 'Protein Encoder (II) — Attention Pooling',
  bullets: [
    'All T residue-level hidden states are combined into one protein-level vector',
    'A learned attention vector scores each position\'s relevance before weighted summation',
    'Down-weights padding/low-information residues; up-weights residues near probable binding regions',
  ],
  eqs: [
    { p: 'u_t = tanh(W_p h_t + b_p)', t: 'u_t = \\tanh(W_p h_t + b_p)' },
    { p: 'β_t = exp(u_t^T v_p) / Σ_τ exp(u_τ^T v_p)', t: '\\beta_t = \\dfrac{\\exp(u_t^{\\top} v_p)}{\\sum_{\\tau=1}^{T} \\exp(u_\\tau^{\\top} v_p)}' },
    { p: 'z_p = Σ_{t=1}^{T} β_t h_t', t: 'z_p = \\sum_{t=1}^{T} \\beta_t\\, h_t' },
  ],
  notes: `This attention-pooling weight β_t is not decorative — it is reused later, verbatim, as part of the interpretability layer in Objective 3: high-β residues are exactly the residues you will visualize as candidate binding-relevant positions in the case studies. Make that forward-reference explicit here so when interpretability comes up nine slides later, the panel already has the mechanism in mind rather than seeing it as a bolt-on afterthought.`
},
// ---------------------------------------------------------------- 19
{
  sec: 'Methodology · Fusion', title: 'Gated Cross-Attention (I) — Bidirectional Cross-Modal Attention',
  bullets: [
    'Core architectural contribution — replaces static concatenation with dynamic, learned interaction',
    'Atom-level states H_d ∈ ℝ^(n×d) and residue-level states H_p ∈ ℝ^(m×d) attend to each other directly',
    'Scaled dot-product attention, computed in both directions simultaneously',
  ],
  eqs: [
    { p: 'Q_d=H_d W_Q^d,  K_p=H_p W_K^p,  V_p=H_p W_V^p', t: 'Q_d = H_d W_Q^{d}, \\quad K_p = H_p W_K^{p}, \\quad V_p = H_p W_V^{p}' },
    { p: 'A_{d→p} = softmax( Q_d K_p^T / √d_k ) V_p', t: 'A_{d\\to p} = \\mathrm{softmax}\\!\\left(\\dfrac{Q_d K_p^{\\top}}{\\sqrt{d_k}}\\right) V_p' },
    { p: 'Q_p=H_p W_Q^p,  K_d=H_d W_K^d,  V_d=H_d W_V^d', t: 'Q_p = H_p W_Q^{p}, \\quad K_d = H_d W_K^{d}, \\quad V_d = H_d W_V^{d}' },
    { p: 'A_{p→d} = softmax( Q_p K_d^T / √d_k ) V_d', t: 'A_{p\\to d} = \\mathrm{softmax}\\!\\left(\\dfrac{Q_p K_d^{\\top}}{\\sqrt{d_k}}\\right) V_d' },
  ],
  notes: `This is the slide to slow down the most — it is the answer to RQ1 and the core of Objective 1. Say explicitly: "In GSRF-DTI and TTModel, drug and protein features never interact until they are concatenated right before the classifier — there is no mechanism for a drug atom to 'ask' which protein residues are relevant to it. Here, every drug atom computes a query against every protein residue's key, producing an attention-weighted mixture A_{d→p} of protein information most relevant to that atom — and symmetrically for A_{p→d}." This bidirectionality is what "dynamic" and "cross-modal" mean concretely, not just as buzzwords — be ready to write Q,K,V on a whiteboard if asked.`
},
// ---------------------------------------------------------------- 20
{
  sec: 'Methodology · Fusion', title: 'Gated Cross-Attention (II) — Adaptive Gating',
  bullets: [
    'A sigmoid gate learns, per feature dimension, how much cross-modal signal to trust vs. preserve',
    'Prevents the cross-attention output from overwriting informative but modality-specific features',
    'Applied symmetrically to both drug and protein branches',
  ],
  eqs: [
    { p: 'g_d = σ(W_g^d [H_d ‖ A_{d→p}] + b_g^d)', t: 'g_d = \\sigma\\!\\left(W_g^{d}\\,[H_d \\,\\Vert\\, A_{d\\to p}] + b_g^{d}\\right)' },
    { p: 'H_d\' = g_d ⊙ H_d + (1−g_d) ⊙ A_{d→p}', t: "H_d' = g_d \\odot H_d + (1-g_d)\\odot A_{d\\to p}" },
    { p: 'g_p = σ(W_g^p [H_p ‖ A_{p→d}] + b_g^p)', t: 'g_p = \\sigma\\!\\left(W_g^{p}\\,[H_p \\,\\Vert\\, A_{p\\to d}] + b_g^{p}\\right)' },
    { p: 'H_p\' = g_p ⊙ H_p + (1−g_p) ⊙ A_{p→d}', t: "H_p' = g_p \\odot H_p + (1-g_p)\\odot A_{p\\to d}" },
  ],
  notes: `Why gate instead of just using the cross-attention output directly? Because not every atom has a meaningful protein-side counterpart — e.g. a methyl group governing solubility may have no specific residue relevance — and forcing every atom's representation to be entirely replaced by cross-modal information would inject noise. The gate is a learned, per-dimension interpolation between "trust my own modality" and "trust the cross-modal signal," conditioned on both. This is the specific mechanism that justifies the word "Gated" in Gated Cross-Attention, and it is the ablation-testable difference versus a plain cross-attention-only variant.`
},
// ---------------------------------------------------------------- 21
{
  sec: 'Methodology · Fusion', title: 'Global Fusion & Joint Representation',
  bullets: [
    'Gated atom/residue states are pooled back to single drug and protein vectors',
    'A second, global-level gate fuses the two into one joint drug-target representation',
  ],
  eqs: [
    { p: 'z_d\' = READOUT(H_d\'),   z_p\' = READOUT(H_p\')', t: "z_d' = \\mathrm{READOUT}(H_d'), \\qquad z_p' = \\mathrm{READOUT}(H_p')" },
    { p: 'g = σ(W_f [z_d\' ‖ z_p\'] + b_f)', t: "g = \\sigma\\!\\left(W_f\\,[z_d' \\,\\Vert\\, z_p'] + b_f\\right)" },
    { p: 'z = g ⊙ z_d\' + (1−g) ⊙ z_p\'', t: "z = g \\odot z_d' + (1-g)\\odot z_p'" },
  ],
  notes: `One sentence is enough here: "the local, fine-grained gating from the previous slide happens at the atom/residue level; this global gate happens once more at the pooled molecule/protein level, so the model can additionally decide, per drug-target pair, whether the interaction is more drug-driven or more protein-driven." z is the single vector that everything downstream — both prediction heads — consumes.`
},
// ---------------------------------------------------------------- 22
{
  sec: 'Methodology · Prediction', title: 'Prediction Head — Multi-Task Output',
  bullets: [
    'Shared MLP trunk with dropout and residual connections for stability',
    'Task-specific output layer: classification head (DTI) or regression head (DTA)',
    'Same underlying architecture serves both prediction tasks in the study scope',
  ],
  eqs: [
    { p: 'h_1 = Dropout(ReLU(W_1 z + b_1)),   h_2 = ReLU(W_2 h_1 + b_2)', t: 'h_1 = \\mathrm{Dropout}\\big(\\mathrm{ReLU}(W_1 z + b_1)\\big), \\qquad h_2 = \\mathrm{ReLU}(W_2 h_1 + b_2)' },
    { p: 'DTI:  ŷ = softmax(W_o h_2 + b_o) ∈ ℝ²   (interaction probability)', t: '\\text{DTI:}\\quad \\hat{y} = \\mathrm{softmax}(W_o h_2 + b_o) \\in \\mathbb{R}^2' },
    { p: 'DTA:  ŷ = W_o h_2 + b_o ∈ ℝ   (continuous pKd / pKi / pIC50)', t: '\\text{DTA:}\\quad \\hat{y} = W_o h_2 + b_o \\in \\mathbb{R}' },
  ],
  notes: `Emphasize "shared trunk, swapped head" — this is a deliberate design economy: the expensive part of the model (encoders + fusion) is task-agnostic, and only the last layer changes between the classification and regression objectives named in the Scope slide. This closes the architecture walkthrough — pause here and ask if there are questions before moving into Training Strategy, since this is a natural chapter break.`
},
// ---------------------------------------------------------------- 23
{
  sec: 'Methodology · Training', title: 'Training Strategy (I) — Self-Supervised Pretraining',
  bullets: [
    'Drug and protein encoders optionally pretrained on large unlabeled corpora (e.g., DrugBank) before DTI fine-tuning',
    'Contrastive learning and masked-feature prediction objectives learn transferable structure without requiring interaction labels',
    'Directly targets Objective 2 — cold-start generalization to drugs/targets with few or no labeled interactions',
  ],
  eqs: [
    { p: 'L_contrastive = −log[ exp(sim(z_i,z_i⁺)/τ) / Σ_j exp(sim(z_i,z_j)/τ) ]', t: '\\mathcal{L}_{\\text{contrastive}} = -\\log \\dfrac{\\exp(\\mathrm{sim}(z_i, z_i^{+})/\\tau)}{\\sum_{j} \\exp(\\mathrm{sim}(z_i, z_j)/\\tau)}' },
  ],
  notes: `Frame this as the second lever for cold-start (the first being ChemBERTa/ESM-2 initialization already covered in preprocessing). The logic chain: labeled DTI data is comparatively small and biased toward well-studied drugs/targets; unlabeled molecular/protein data is abundant; self-supervised pretraining on the abundant unlabeled data teaches the encoders general biochemical structure before they ever see a single interaction label, so at DTI fine-tuning time the model already "understands" a novel drug's chemistry even if it never saw that exact drug in training.`
},
// ---------------------------------------------------------------- 24
{
  sec: 'Methodology · Training', title: 'Training Strategy (II) — Imbalance-Aware Losses',
  bullets: [
    'Focal loss down-weights easy negatives, focusing gradient on hard/ambiguous pairs',
    'Weighted BCE offered as an alternative/ablation baseline for classification',
    'DTA regression trained with standard MSE on the standardized affinity targets',
  ],
  eqs: [
    { p: 'FL(p_t) = −α_t (1−p_t)^γ log(p_t)', t: '\\mathrm{FL}(p_t) = -\\alpha_t (1-p_t)^{\\gamma} \\log(p_t)' },
    { p: 'L_wbce = −[ w_1 y log(ŷ) + w_0 (1−y) log(1−ŷ) ]', t: '\\mathcal{L}_{\\text{wbce}} = -\\big[w_1\\, y \\log(\\hat{y}) + w_0 (1-y) \\log(1-\\hat{y})\\big]' },
    { p: 'L_mse = (1/N) Σ_{i=1}^N (y_i − ŷ_i)²', t: '\\mathcal{L}_{\\text{mse}} = \\frac{1}{N}\\sum_{i=1}^{N} (y_i - \\hat{y}_i)^2' },
  ],
  notes: `Explain γ and α_t concretely: γ (the focusing parameter) exponentially shrinks the loss contribution of well-classified examples — so once the model is confidently correct on an easy negative, that example essentially stops contributing gradient, freeing capacity to focus on ambiguous drug-target pairs near the decision boundary. α_t is the standard class-balance term compensating for the 1:10 (or worse) positive:negative sampling ratio. This is one of the ablation axes in your evaluation protocol — you compare focal loss vs. weighted BCE directly, not just assume focal loss is better.`
},
// ---------------------------------------------------------------- 25
{
  sec: 'Methodology · Training', title: 'Training Strategy (III) — Optimization & Regularization',
  bullets: [
    'AdamW optimizer with decoupled weight decay, trained end-to-end',
    'Cosine learning-rate schedule with warmup; early stopping on validation loss',
    'Dropout regularization throughout; 10-fold cross-validation + held-out test set',
    'Ablation studies isolate each component: GNN-only, RNN-only, concatenation-fusion, no-pretraining variants',
  ],
  eqs: [
    { p: 'θ* = argmin_θ  E_(x,y)~D[ L(f_θ(x), y) ] + λ‖θ‖²', t: '\\theta^{*} = \\arg\\min_{\\theta} \\; \\mathbb{E}_{(x,y)\\sim\\mathcal{D}}\\big[\\mathcal{L}(f_\\theta(x), y)\\big] + \\lambda\\lVert\\theta\\rVert^2' },
    { p: 'η_t = η_min + ½(η_max − η_min)(1 + cos(tπ/T))', t: '\\eta_t = \\eta_{\\min} + \\tfrac{1}{2}(\\eta_{\\max}-\\eta_{\\min})\\big(1+\\cos(t\\pi/T)\\big)' },
  ],
  notes: `Keep this practical and brisk — this is standard modern deep-learning training hygiene, low examiner scrutiny, but the ablation list at the bottom is important: name it as the mechanism by which O1's "statistically significant improvement over concatenation" claim gets tested (the concatenation-fusion variant IS the ablation baseline for that exact claim). This slide is your evidence that the training protocol is not ad hoc.`
},
// ---------------------------------------------------------------- 26
{
  sec: 'Methodology · Evaluation', title: 'Evaluation Protocol (I) — Performance Metrics',
  bullets: [
    'Classification (DTI): threshold-independent metrics preferred given class imbalance',
    'Regression (DTA): standard error and correlation metrics on the continuous affinity scale',
  ],
  eqs: [
    { p: 'AUC-ROC = ∫₀¹ TPR d(FPR)          AUPR = ∫₀¹ Precision d(Recall)', t: '\\mathrm{AUC\\text{-}ROC} = \\int_0^1 \\mathrm{TPR}\\, d(\\mathrm{FPR}), \\qquad \\mathrm{AUPR} = \\int_0^1 \\mathrm{Precision}\\, d(\\mathrm{Recall})' },
    { p: 'RMSE = √[ (1/N) Σ(y_i−ŷ_i)² ]          MAE = (1/N) Σ|y_i−ŷ_i|', t: '\\mathrm{RMSE} = \\sqrt{\\tfrac{1}{N}\\sum (y_i-\\hat{y}_i)^2}, \\qquad \\mathrm{MAE} = \\tfrac{1}{N}\\sum |y_i-\\hat{y}_i|' },
    { p: 'PCC = Σ(y_i−ȳ)(ŷ_i−ŷ̄) / √[Σ(y_i−ȳ)² Σ(ŷ_i−ŷ̄)²]', t: '\\mathrm{PCC} = \\dfrac{\\sum (y_i-\\bar{y})(\\hat{y}_i-\\bar{\\hat{y}})}{\\sqrt{\\sum (y_i-\\bar{y})^2 \\sum (\\hat{y}_i-\\bar{\\hat{y}})^2}}' },
  ],
  notes: `If pressed on "why not accuracy" for classification: accuracy is misleading under class imbalance (a trivial always-negative classifier scores high accuracy but is useless) — AUC-ROC and especially AUPR are the field-standard choice because AUPR is more sensitive to performance on the minority (positive-interaction) class, which is exactly what matters for virtual screening. State that you will report AUPR as the primary metric and AUC-ROC as secondary/comparative.`
},
// ---------------------------------------------------------------- 27
{
  sec: 'Methodology · Evaluation', title: 'Evaluation Protocol (II) — Cold-Start Splits',
  tbl: {
    head: ['Setting', 'Definition', 'What it Tests'],
    rows: [
      ['S1 — Warm-start', 'Random split, 10-fold CV; drugs & targets may repeat across train/test', 'Baseline performance (upper bound)'],
      ['S2 — Cold-drug', 'Drug-disjoint split; test drugs never seen in training', 'Generalization to novel compounds'],
      ['S3 — Cold-target', 'Target-disjoint split; test proteins never seen in training', 'Generalization to novel targets'],
      ['S4 — Cold-pair', 'Pair-disjoint split; individual drugs/targets may repeat, but not the pair', 'Generalization to novel interaction patterns'],
    ]
  },
  notes: `Present S1→S4 explicitly as increasing difficulty, in that order, and say so: "S1 is the easiest and most optimistic setting — most of the deep learning DTI literature over-reports on S1 alone. S2 and S3 are the true cold-start tests this thesis is built around. S4 is the hardest and most realistic: in real virtual screening you are almost always asking about a pair you've never seen." This directly operationalizes RQ2/Objective 2, and it is the natural place to mention cross-dataset transfer (train on one benchmark, e.g. BindingDB, test on another, e.g. DAVIS) as an even more stringent generalization test beyond these four.`
},
// ---------------------------------------------------------------- 28
{
  sec: 'Methodology · Evaluation', title: 'Evaluation Protocol (III) — Ablation & Statistical Rigor',
  bullets: [
    'Ablation variants: GNN-only, RNN-only, concatenation-fusion, no-pretraining, alternative pooling strategies',
    'Cross-dataset transfer: train on one benchmark (e.g. BindingDB), evaluate on another (e.g. DAVIS)',
    'Every configuration run across multiple random seeds; report mean ± standard deviation',
    'Paired significance testing (e.g. paired t-test) against baselines — not point-estimate comparison alone',
  ],
  eqs: [
    { p: 't = d̄ / (s_d / √n)          d_i = metric_hgnn,i − metric_baseline,i', t: 't = \\dfrac{\\bar{d}}{s_d/\\sqrt{n}}, \\qquad d_i = \\text{metric}_{\\text{hgnn},i} - \\text{metric}_{\\text{baseline},i}' },
  ],
  notes: `This slide is your defense against "your numbers might just be noise/seed luck." Say explicitly that every headline comparison in the thesis will be backed by multi-seed mean±std and a paired test on per-seed differences (d_i), not a single lucky run — this is what turns O1's "statistically significant improvement" from a slogan into an actual, checkable claim with a p-value. If you already have preliminary ablation numbers from pilot runs, this is the moment to mention them briefly as evidence the protocol is already implemented and working, not just planned.`
},
// ---------------------------------------------------------------- 29
{
  sec: 'Methodology · Interpretability', title: 'Interpretability & Explainability Framework',
  bullets: [
    'Attention-based attribution: cross-attention weights double as an atom/residue importance signal, at no extra training cost',
    'Visualization: heatmaps + graph-based Grad-CAM overlays on molecular graphs and protein sequences',
    'Validation: predicted binding hotspots compared against known crystal structures (Protein Data Bank) in case studies',
  ],
  eqs: [
    { p: 'I(v) = Σ_r A_{d→p}[v,r]        I(r) = Σ_v A_{d→p}[v,r]', t: 'I(v) = \\sum_{r} A_{d\\to p}[v,r], \\qquad I(r) = \\sum_{v} A_{d\\to p}[v,r]' },
    { p: 'L_c^Grad-CAM = ReLU( Σ_k α_k^c A^k ),   α_k^c = (1/Z) Σ_ij ∂y^c/∂A_ij^k', t: "L_c^{\\text{Grad-CAM}} = \\mathrm{ReLU}\\Big(\\sum_k \\alpha_k^c A^k\\Big), \\qquad \\alpha_k^c = \\tfrac{1}{Z}\\sum_{i,j} \\frac{\\partial y^c}{\\partial A_{ij}^k}" },
  ],
  notes: `This answers RQ3 and delivers Objective 3. The key sentence: "Interpretability here is intrinsic, not post-hoc — the same attention matrix A_{d→p} that performs the fusion is directly summed to produce atom and residue importance scores, so there is no separate, potentially unfaithful surrogate explainer bolted on afterward." Grad-CAM adds a gradient-weighted refinement on top for sharper, class-discriminative localization. Close with the validation strategy: pick 2-3 well-characterized drug-target complexes with known crystal structures (e.g. a kinase-inhibitor pair), show that the model's attention hotspots overlap with the experimentally known binding pocket — this is your answer to "how do you know the attention weights are meaningful and not just noise."`
},
// ---------------------------------------------------------------- 30
{
  sec: 'Outcomes', title: 'Expected Outcomes & Contributions',
  bullets: [
    'A robust hybrid GNN-RNN model with a dynamic, gated cross-modal fusion mechanism (methodological contribution)',
    'Statistically significant predictive improvement over GSRF-DTI, TTModel, DTKGIN and single-modality baselines, including in cold-start settings (empirical contribution)',
    'An intrinsically interpretable DTI framework producing biologically meaningful, case-study-validated explanations (translational contribution)',
    'A fully reproducible pipeline — public source code, trained models, and experimental configurations (open-science contribution)',
  ],
  notes: `Map each bullet back to O1/O2/O3 one more time in one breath — repetition here is intentional, it is the last chance to reinforce that every objective has a concrete, checkable deliverable. If your program expects publications, mention target venues/timing briefly (e.g., an architecture paper after Pillar 1 is validated, a cold-start/generalization paper after Pillar 2).`
},
// ---------------------------------------------------------------- 31
{
  sec: 'Outcomes', title: 'Research Timeline (Illustrative)',
  bullets: [
    'Phase 1 — Literature synthesis, data acquisition & preprocessing pipeline, baseline reproduction',
    'Phase 2 — H-GAT + BiGRU encoders implemented and unit-validated independently (→ Objective 1 groundwork)',
    'Phase 3 — Gated Cross-Attention fusion integrated; full-model training, ablations, cold-start evaluation (→ Objectives 1 & 2)',
    'Phase 4 — Interpretability layer, case-study validation, cross-dataset transfer experiments (→ Objective 3)',
    'Phase 5 — Manuscript preparation, thesis writing, and defense',
  ],
  notes: `IMPORTANT — this slide is deliberately phase-based, not calendar-dated, because the exact semester/year Gantt chart lives in Figure 3.5 of the written proposal and was not available as extractable text for this deck. Before presenting, replace this slide's bullets with (or overlay them on) your actual Gantt chart image from the proposal document so the dates match exactly what the panel already has in front of them in the written document — consistency between the slide and the proposal document is something examiners do check.`
},
// ---------------------------------------------------------------- 32
{
  sec: 'Summary', title: 'Summary — Key Takeaways',
  bullets: [
    'Gap: cross-modal fusion is shallow, cold-start generalization is weak, interpretability is absent',
    'Response: H-GNN-RNN-DTI — H-GAT drug encoder + BiGRU protein encoder + novel Gated Cross-Attention fusion',
    'Rigor: cold-start/cross-dataset evaluation, multi-seed statistical testing, ablation-isolated claims',
    'Payoff: measurable accuracy gains, principled generalization, and biologically grounded interpretability',
  ],
  notes: `This is your closing thesis statement, delivered in four beats: problem, solution, how you will prove it, why it matters. Say it slowly and make eye contact with the panel — this is the sentence you want them to remember when they write their evaluation. Then transition directly to the Q&A slide.`
},
// ---------------------------------------------------------------- 33
{
  layout: 'closing',
  notes: `Thank the panel. Before opening the floor, it is worth having quick, rehearsed answers ready for the most likely questions: (1) "How does this differ from GraphDTA/DeepDTA/MolTrans?" — those use single-modality or shallow fusion; this proposal's contribution is the bidirectional gated cross-attention specifically. (2) "What if the Gated Cross-Attention doesn't beat concatenation?" — that is precisely why the ablation is pre-registered as part of the methodology; a null result on O1 is still a defensible, publishable finding if rigorously tested. (3) "Compute budget / feasibility?" — name the hardware (A100 GPU) and note the encoders can be validated independently before full joint training, de-risking the schedule. (4) "How do you pick negative samples reliably?" — restate the unknown-negative sampling strategy and that this is a field-wide open problem, not unique to this work. Stay calm, refer back to the relevant slide number when answering rather than re-explaining from scratch.`
},
];
