// Part 3: Tables + Gaps + Future + Conclusion + References
import { h1, h2, h3, p, bul, sp, pb, cap, createTable } from './generate_review_p1.mjs';

// ============================================================
// SECTION 6: COMPARATIVE TABLES
// ============================================================

export const tableSection = [
  h1('6. Comparative Analysis'),
  h2('6.1 Table 1: Model Taxonomy'),
  p('Table 1 provides a comprehensive taxonomy of 36 reviewed DTI/DTA prediction models, organized by architectural paradigm. Columns indicate: year, drug representation, protein representation, fusion strategy, primary evaluation datasets, best reported metric, and primary limitation.', { noIndent: true }),
  sp(),
  createTable(
    ['Model', 'Year', 'Drug Repr.', 'Protein Repr.', 'Fusion', 'Datasets', 'Best Metric', 'Primary Limitation'],
    [
      ['DeepDTA','2018','CNN (SMILES chars)','CNN (AA chars)','Concat','DAVIS, KIBA','CI=0.878 (DAVIS)','No graph topology; no long-range protein context'],
      ['DTI-RCNN','2025','CNN + LSTM (SMILES)','CNN + LSTM (seq)','Concat','Human, C.elegans','AUC competitive','SMILES lacks topology; static fusion'],
      ['GraphDTA','2021','GNN (mol. graph)','CNN (AA seq)','Concat','DAVIS, KIBA','CI=0.893 (DAVIS GAT)','CNN protein; static concat fusion'],
      ['SaeGraphDTI','2025','GNN + seq. attr.','Seq. attr. + phys.','Concat','BindingDB, DAVIS','AUC=0.91+','Heuristic attributes; concat fusion'],
      ['AttentionDTI','2019','Fingerprints','AA composition','Attention','Human, C.elegans','AUC=0.970 (Human)','Fingerprints lose topology; binary only'],
      ['HyperAttnDTI','2022','CNN (SMILES)','CNN (AA seq)','Bidir. Attn','DAVIS, KIBA, Human','CI=0.882 (DAVIS)','No graph; no pretrained embeddings'],
      ['GSAML-DTA','2022','GNN (mol. graph)','Self-Attn (seq)','Concat + MI','DAVIS, KIBA','CI=0.891 (DAVIS)','Approx. MI; no cold-start eval'],
      ['GraphATT-DTA','2023','GAT (mol. graph)','Seq. Attn','Concat (dual attn)','DAVIS, KIBA','CI=0.896 (DAVIS)','No residue-level binding validation'],
      ['MutualDTA','2025','ChemBERTa (LM)','ESM-2 (LM)','Mutual Attn','DAVIS, KIBA, BindingDB','CI=0.908 (DAVIS)','Quadratic attn; cold-start not systematic'],
      ['EHIGN','2024','GNN (3D geometry)','GNN (3D geometry)','Pairwise interact.','PDBbind','RMSE=1.31','Requires 3D structures; expensive'],
      ['TransformerCPI','2020','Transformer (SMILES)','CNN (AA seq)','Cross-Attn','Human, C.elegans, DAVIS','AUC=0.974 (C.eleg)','Quadratic cost; no pretraining'],
      ['MolTrans','2021','Aug. Transformer','CNN (AA seq)','Cross-Attn Transformer','BindingDB, DAVIS','AUC=0.953 (BindDB)','Heuristic substructures; no pretrained LM'],
      ['EmbedDTI','2021','GCN + pretrained emb','BiLSTM + pretrained','Cross-Attn','DAVIS, Human','CI=0.891 (DAVIS)','Older pretraining; limited cold-start'],
      ['TTModel','2024','KG entity emb. + text','KG entity emb. + text','Inner product','Yamanishi_08','AUPR=0.95 (GPCR)','No mol. graph/seq encoding; KG-dependent'],
      ['DTKGIN','2024','KG + intent GNN','KG + intent GNN','Inner product','Yamanishi_08','AUC=0.894 S2 (cold-drug)','No seq/graph encoders; no dynamic attn'],
      ['GSRF-DTI','2024','DeepWalk + GraphSAGE','DeepWalk + GraphSAGE','Concat (RF)','Luo_17','AUROC=0.9818','Static fusion; no GNN mol. graph; no XAI'],
      ['RSGCL-DTI','2025','GCL (graph contr.)','GCL (seq contr.)','Concat','BindingDB, Yamanishi','AUC=0.947 (Yaman)','Augmentation design; no cross-modal attn'],
      ['DeepGS (GAT+BiGRU)','2022','GAT (mol. graph)','BiGRU (AA seq)','Concat','DAVIS, Yamanishi','CI=0.892 (DAVIS)','Static concat; no pretrained embeddings'],
      ['GDGRU-DTA','2022','GNN + GRU (SMILES)','GRU (AA seq)','Concat','DAVIS, KIBA','CI=0.889 (DAVIS)','Redundant encoding; no cross-modal attn'],
      ['iNGNN-DTI','2024','Nested GNN (mol)','Nested GNN (prot)','Cross-Attn + pretrained','BindingDB, DAVIS','AUC=0.963 (BindDB)','Very expensive; limited cold-start report'],
      ['Top-DTI','2025','TDA + LLM + GNN','ESM-2 LLM','Multimodal Transformer','BindingDB, DAVIS, Yaman.','AUC=0.921 S2 (Yaman)','TDA expensive; requires 3D coordinates'],
      ['HMSA-DTI','2024','SMILES + graph (HMSA)','Seq. HMSA','Hierarchical MHA','Yamanishi_08, BindingDB','AUC=0.962 (Yaman)','3-modality redundancy; no foundation model'],
      ['MMDG-DTI','2025','GNN (mol. graph)','CNN/RNN (seq)','Concat + domain adv.','BindingDB->DAVIS','CI=0.906 (DAVIS)','Adversarial instability; concat fusion'],
      ['GS-DTI','2025','GNN + LLM (SMILES)','Protein LLM','Cross-Attn','BindingDB, DAVIS','AUC=0.961 (BindDB)','LLM cost; partial cold-start eval'],
      ['IHDFN-DTI','2025','GNN (mol. graph)','Transformer (seq)','Multi-head cross-attn','DAVIS, KIBA, BindingDB','CI=0.905 (DAVIS)','Quadratic attn; no foundation model init'],
      ['SS-DTI','2025','GNN + BERT (text)','RNN + BERT (text)','Concat','BindingDB, Human','AUC=0.974 (Human)','Text may be incomplete; no cold-start eval'],
      ['MINDG','2024','Multi-view (graph+seq)','Multi-view','Adaptive weighting','BindingDB, Yamanishi','AUC=0.958 (Yaman)','High preprocessing; no cross-modal attn'],
      ['NHGNN-DTA','2023','Node-adaptive GNN','GRU + Attn','Concat','DAVIS, KIBA','CI=0.904 (DAVIS)','Heuristic node types; no XAI; no cold-start'],
      ['HiGraphDTI','2024','Hierarchical GNN','Bi-encoder (seq)','Concat','DAVIS, KIBA, BindingDB','CI=0.902 (DAVIS)','Coarsening heuristic; expensive; no cold-start'],
      ['MFCADTI','2025','Multi-feat + cross-attn','Multi-feat + cross-attn','Multi-source cross-attn','BindingDB, Yamanishi','AUC=0.964 (BindDB)','Quadratic; warm-split only; no foundation model'],
      ['ViDTA','2024','GNN + virtual nodes','CNN + Attn','Attn-based fusion','DAVIS, KIBA','CI=0.905 (DAVIS)','Virtual node count sensitivity; no cold-start'],
      ['DrugBAN','2023','GNN (mol. graph)','CNN/RNN + PPI','Bilinear Attn + DA','BindingDB (cold splits)','AUC=0.919 cold-drug','Bilinear scales O(n*m); needs target-domain data'],
      ['CoaDTI','2022','CNN/fingerprint','CNN/seq','Co-Attn','Human, C.elegans, BindDB','AUC=0.971 (Human)','Simpler encoders; cold-start not systematic'],
      ['ICAN','2023','GNN (mol. graph)','Transformer (seq)','Pharmacophore-cond. CA','BindingDB, DrugBank','AUC=0.958 (BindDB)','Needs pharmacophore annotations; limited cold-start'],
      ['BACPI','2023','GNN (mol. graph)','GNN + PPI net','Bilinear Cross-Attn','Human, C.elegans, BindDB','AUC=0.973 (Human)','PPI database required; quadratic bilinear'],
      ['ColdDTA','2025','Multi-view pretr. emb','Multi-view pretr. emb','Concat (pretrained)','DAVIS, KIBA, BindingDB (cold)','CI=0.873 cold-drug','Multi-view augmentation design; no XAI'],
    ],
    [1200, 600, 1300, 1300, 1200, 1200, 900, 1800]
  ),
  cap('Table 1. Taxonomy of 36 reviewed DTI/DTA prediction models. Abbreviations: GNN = Graph Neural Network; RNN = Recurrent Neural Network; CNN = Convolutional Neural Network; LM = Language Model; KG = Knowledge Graph; CA = Cross-Attention; DA = Domain Adaptation; TDA = Topological Data Analysis; MI = Mutual Information; phys. = physicochemical; Yaman = Yamanishi_08; BindDB = BindingDB; S2 = cold-drug setting.'),
  pb(),

  h2('6.2 Table 2: Benchmark Performance Comparison'),
  p('Table 2 compares performance across common benchmark datasets. DAVIS and KIBA metrics are CI (higher is better) and RMSE (lower is better). Yamanishi_08 and Luo_17 metrics are AUC and AUPR. N/R = not reported.', { noIndent: true }),
  sp(),
  createTable(
    ['Model', 'DAVIS CI', 'DAVIS RMSE', 'KIBA CI', 'KIBA RMSE', 'Yaman. AUC', 'Luo_17 AUROC', 'BindingDB AUC'],
    [
      ['DeepDTA','0.878','0.261','0.863','0.194','N/R','N/R','N/R'],
      ['GraphDTA (GAT)','0.893','0.229','0.891','0.139','N/R','N/R','N/R'],
      ['AttentionDTI','N/R','N/R','N/R','N/R','0.970*','N/R','N/R'],
      ['HyperAttnDTI','0.882','N/R','0.876','N/R','0.967*','N/R','N/R'],
      ['TransformerCPI','0.886','N/R','N/R','N/R','0.971*','N/R','N/R'],
      ['MolTrans','0.895','N/R','N/R','N/R','N/R','N/R','0.953'],
      ['EmbedDTI','0.891','N/R','N/R','N/R','0.969*','N/R','N/R'],
      ['GSAML-DTA','0.891','0.234','0.893','0.142','N/R','N/R','N/R'],
      ['GraphATT-DTA','0.896','0.211','0.893','N/R','N/R','N/R','N/R'],
      ['MutualDTA','0.908','0.198','0.917','N/R','N/R','N/R','N/R'],
      ['EHIGN','N/R','N/R','N/R','N/R','N/R','N/R','N/R'],
      ['TTModel','N/R','N/R','N/R','N/R','0.95 (GPCR)†','N/R','N/R'],
      ['DTKGIN','N/R','N/R','N/R','N/R','0.925 (S1)','N/R','N/R'],
      ['GSRF-DTI','N/R','N/R','N/R','N/R','N/R','0.9818','N/R'],
      ['RSGCL-DTI','N/R','N/R','N/R','N/R','0.947','N/R','0.942'],
      ['DeepGS','0.892','N/R','N/R','N/R','0.941','N/R','N/R'],
      ['GDGRU-DTA','0.889','N/R','0.878','N/R','N/R','N/R','N/R'],
      ['iNGNN-DTI','0.904','N/R','N/R','N/R','N/R','N/R','0.963'],
      ['Top-DTI','0.906','N/R','N/R','N/R','0.921 (S2)','N/R','N/R'],
      ['HMSA-DTI','N/R','N/R','N/R','N/R','0.962','N/R','N/R'],
      ['MMDG-DTI','0.906','N/R','N/R','N/R','N/R','N/R','N/R'],
      ['GS-DTI','0.901','N/R','N/R','N/R','N/R','N/R','0.961'],
      ['IHDFN-DTI','0.905','0.219','0.912','N/R','N/R','N/R','N/R'],
      ['SS-DTI','N/R','N/R','N/R','N/R','N/R','N/R','0.958'],
      ['MINDG','N/R','N/R','N/R','N/R','0.958','N/R','N/R'],
      ['NHGNN-DTA','0.904','0.218','0.916','0.131','N/R','N/R','N/R'],
      ['HiGraphDTI','0.902','N/R','0.908','N/R','N/R','N/R','0.953'],
      ['MFCADTI','N/R','N/R','N/R','N/R','0.960','N/R','0.964'],
      ['ViDTA','0.905','N/R','0.914','N/R','N/R','N/R','N/R'],
      ['DrugBAN (warm)','N/R','N/R','N/R','N/R','N/R','N/R','0.953'],
      ['CoaDTI','N/R','N/R','N/R','N/R','N/R','N/R','0.951'],
      ['ColdDTA (warm)','0.903','N/R','N/R','N/R','N/R','N/R','N/R'],
    ],
    [1300, 800, 800, 800, 800, 800, 900, 900]
  ),
  cap('Table 2. Performance comparison on benchmark datasets. * = on Human or C. elegans dataset (AUC). † = AUPR on GPCR class of Yamanishi_08. N/R = not reported in the respective publication. S1 = warm-start setting, S2 = cold-drug. CI = Concordance Index; RMSE = Root Mean Squared Error; AUC = Area Under ROC Curve.'),
  pb(),

  h2('6.3 Table 3: Cold-Start Evaluation (Yamanishi_08 Protocol)'),
  p('Table 3 reports performance in the three standard cold-start settings defined for the Yamanishi_08 benchmark: S1 (warm-start), S2 (cold-drug: novel compounds), S3 (cold-target: novel proteins). AUC and AUPR values are reported where available. Models are sorted by S2 AUC (cold-drug) as it represents the most practically relevant generalization challenge.', { noIndent: true }),
  sp(),
  createTable(
    ['Model', 'Year', 'S1 AUC', 'S1 AUPR', 'S2 AUC (cold-drug)', 'S2 AUPR', 'S3 AUC (cold-target)', 'S3 AUPR', 'Cold-Start Strategy'],
    [
      ['Top-DTI','2025','0.952','0.931','0.921','0.898','0.883','0.841','LLM pretrained embeddings; TDA features'],
      ['RSGCL-DTI','2025','0.967','0.951','0.918','0.884','0.876','0.833','Graph contrastive pretraining'],
      ['DTKGIN','2024','0.950','0.941','0.894','0.753','0.851','0.660','Intent graph; relational path-aware GNN'],
      ['DrugBAN','2023','N/R','N/R','0.919*','N/R','0.903*','N/R','Bilinear attn; domain adaptation (BindingDB splits)'],
      ['HMSA-DTI','2024','0.962','0.938','0.887','0.821','0.843','0.772','Hierarchical multimodal self-attention'],
      ['MINDG','2024','0.958','0.943','0.872','0.803','0.831','0.761','Multi-view adaptive weighting'],
      ['MFCADTI','2025','0.960','0.942','0.866','0.790','0.824','0.748','Multi-source cross-attention'],
      ['GS-DTI','2025','0.943','N/R','0.861','N/R','0.819','N/R','LLM structure-aware embeddings'],
      ['ColdDTA','2025','0.903†','N/R','0.873†','N/R','0.856†','N/R','Multi-view contrastive pretraining (DAVIS CI scale)'],
      ['GSRF-DTI','2024','N/R','N/R','N/R','N/R','N/R','N/R','Not evaluated in cold-start settings'],
      ['TTModel','2024','N/R','N/R','N/R','N/R','N/R','N/R','Not formally evaluated in S1/S2/S3'],
      ['DeepDTA','2018','N/R','N/R','N/R','N/R','N/R','N/R','Baseline; no cold-start strategy'],
      ['GraphDTA','2021','N/R','N/R','N/R','N/R','N/R','N/R','Baseline; no cold-start strategy'],
      ['DeepGS','2022','0.941','0.912','0.843','0.751','0.812','0.709','Standard GNN+RNN; limited cold-start'],
    ],
    [1300, 600, 700, 700, 1000, 700, 1000, 700, 1600]
  ),
  cap('Table 3. Cold-start performance on Yamanishi_08 (S1: warm-start, S2: cold-drug, S3: cold-target). * = on BindingDB cold splits (different protocol). † = CI metric on DAVIS cold splits (not AUC). N/R = not reported. Models sorted by S2 AUC descending.'),
  pb(),

  h2('6.4 Table 4: Interpretability Features of Reviewed Models'),
  p('Table 4 characterizes the interpretability mechanisms of reviewed models, covering method type, granularity of attribution, biological validation approach, and visualization type. XAI = Explainable AI.', { noIndent: true }),
  sp(),
  createTable(
    ['Model', 'XAI Method', 'Drug Granularity', 'Protein Granularity', 'Biological Validation', 'Visualization'],
    [
      ['DeepDTA','None','None','None','None','None'],
      ['GraphDTA','None (GAT attn)','Atom (implicit)','None','None','None'],
      ['AttentionDTI','Feature attn weights','Fingerprint bits','AA composition','None','Attn score bar chart'],
      ['GSAML-DTA','Mutual information','Atom-level MI score','Residue-level MI','Literature comparison','Atom/residue MI heatmap'],
      ['GraphATT-DTA','GAT attn + seq attn','Atom/substructure','Protein subsequence','Qualitative case study','Mol. attention overlay; seq. attn heatmap'],
      ['MutualDTA','Mutual attention matrix M','Atom-level M_ij','Residue-level M_ij','PDB binding site comparison','Mutual attn heatmap on structure'],
      ['EHIGN','Atom-atom interaction map','Atom-level I_ij','Residue-level I_ij','SARS-CoV-2 variant binding validation','3D interaction map'],
      ['EmbedDTI','Cross-attn weights','Atom importance','Residue importance','Literature (qualitative)','Attn overlay on molecule/sequence'],
      ['HyperAttnDTI','Bidir. attn weights','SMILES token attn','AA sequence attn','None','Bidir. attn heatmap'],
      ['IHDFN-DTI','Cross-attn weights','Atom-level','Residue-level','PDB crystal structure comparison (>80% overlap)','Cross-attn heatmap; binding site overlay'],
      ['GSAML-DTA','Gradient + self-attn','Atom importance','Residue importance','Literature (quantitative)','Gradient heatmap on mol. graph'],
      ['GraphATT-DTA','Attention pooling weights','Node (atom) importance','Residue importance','Qualitative','Mol. graph coloring; sequence bar'],
      ['MINDG','Adaptive view weights','Feature-type importance','Feature-type importance','None','View weight radar chart'],
      ['iNGNN-DTI','Nested GNN cross-attn','Atom-substructure','Residue region','Literature (qualitative)','Nested graph attn overlay'],
      ['Top-DTI','LLM attn + TDA','Topological features','LLM residue attn','None (structural)','TDA diagram; LLM attn heatmap'],
      ['DrugBAN','Bilinear attn map','Atom-level I_ij','Residue-level I_ij','None formally','BAN attn heatmap'],
      ['CoaDTI','Co-attn weights','Feature-level','Feature-level','None','Co-attn weight matrix'],
      ['ICAN','Pharmacophore-cond. attn','Pharmacophore-level','Binding region','Literature pharmacophore','Cond. attn overlay'],
      ['BACPI','Bilinear cross-attn','Atom-level','Residue-level','Qualitative','Bilinear attn matrix'],
      ['DeepDTA','None','None','None','None','None'],
      ['GSRF-DTI','RF feature importance','Network feature','Network feature','None','Feature importance bar chart'],
      ['TTModel','None','KG entity level','KG entity level','None','None'],
      ['DTKGIN','None','Intent node level','Intent node level','None','Intent node visualization'],
      ['SS-DTI','BERT attn (semantic)','Substructure semantic','Residue semantic','None','BERT attn heatmap'],
      ['HMSA-DTI','Hierarchical MHA attn','Multi-scale','Multi-scale','None','Hierarchical attn map'],
    ],
    [1300, 1400, 1100, 1100, 1400, 1200]
  ),
  cap('Table 4. Interpretability features of reviewed DTI/DTA models. XAI = Explainable AI; attn = attention; mol. = molecular; seq. = sequence; PDB = Protein Data Bank; MI = Mutual Information; TDA = Topological Data Analysis; BAN = Bilinear Attention Network; KG = Knowledge Graph; RF = Random Forest.'),
  pb()
];

// ============================================================
// SECTION 7: RESEARCH GAPS
// ============================================================
export const gapsSection = [
  h1('7. Research Gaps and Open Challenges'),

  h2('7.1 Static Cross-Modal Feature Fusion'),
  p('The most pervasive limitation across reviewed models is reliance on static, concatenation-based fusion of drug and protein representations. Simple concatenation—[h_drug; h_protein]—treats the two modalities as independent and fails to model the fine-grained, context-dependent interactions between drug atomic substructures and protein binding residues. Drug–target binding is fundamentally an interaction phenomenon: specific drug functional groups bind specific protein binding pocket residues through hydrogen bonds, hydrophobic contacts, and electrostatic interactions. Static fusion cannot capture which parts of the drug are relevant to which parts of the protein. While models like iNGNN-DTI, MutualDTA, IHDFN-DTI, DrugBAN, and BACPI have introduced cross-attention and bilinear fusion, most architectures still rely on concatenation (Table 1, Fusion column). The proposed Gated Cross-Attention in H-GNN-RNN-DTI (Eq. 24–28) represents a principled solution, but its scalability and expressiveness relative to competing fusion mechanisms remain to be systematically benchmarked.'),

  h2('7.2 Cold-Start Generalization'),
  p('Cold-start generalization—predicting DTIs for novel drugs or proteins unseen during training—remains a fundamental challenge with substantial practical implications for drug repurposing and emerging disease research (Table 3). Table 3 reveals a consistent performance gap between warm-start (S1) and cold-drug/cold-target (S2/S3) settings across all reported models. DTKGIN, despite its innovative intent graph, shows a drop from AUC=0.950 (S1) to AUC=0.894 (S2) and 0.851 (S3). Top-DTI achieves the best cold-start performance (S2 AUC=0.921) through LLM pretrained embeddings. Most models lack systematic cold-start benchmarking or do not employ explicit cold-start strategies. The key insight from the literature is that pre-trained foundation model embeddings (ChemBERTa, ESM-2, ProtT5) provide transferable biochemical knowledge that substantially reduces cold-start degradation—a strategy absent in many reviewed models.'),

  h2('7.3 Data Imbalance and Negative Sampling'),
  p('DTI datasets suffer from severe class imbalance: experimentally confirmed positive interactions are vastly outnumbered by unknown or assumed-negative pairs. Standard negative sampling from unknown pairs introduces systematic label noise—many "negative" pairs may be actual interactions that simply lack experimental validation (Bagherian et al., 2021). GSRF-DTI explicitly acknowledges the need for "novel strategies to address data imbalance" as future work. Among reviewed models, only H-GNN-RNN-DTI explicitly employs focal loss (Eq. 29) and weighted BCE (Eq. 30) as imbalance-aware training strategies. Most models address imbalance superficially through negative sampling ratios without principled weighting. This gap represents a significant threat to model reliability in practical screening applications.'),

  h2('7.4 Interpretability and Biological Validation'),
  p('As shown in Table 4, the majority of reviewed models either lack interpretability mechanisms (DeepDTA, GDGRU-DTA) or provide attention weights without biological validation against experimentally determined binding sites. Among models with XAI, only IHDFN-DTI reports quantitative validation (>80% overlap with PDB binding site residues), EHIGN validates on SARS-CoV-2 variant binding, and MutualDTA compares attention maps against PDB structures. The remaining models provide qualitative case studies or no validation. Interpretability without validation is insufficient for medicinal chemistry applications where atomic-level binding rationale is required for structure–activity relationship studies and lead optimization. The gap between attention-based attributions and physically meaningful binding site identification requires systematic evaluation.'),

  h2('7.5 Benchmark Inconsistency and Evaluation Bias'),
  p('Comparison across models is hindered by inconsistent evaluation protocols. Different papers use different data splits (random 80/10/10 vs. 5-fold CV vs. Stratified), different negative sampling strategies, different dataset versions, and different metric definitions. Table 2 reveals numerous N/R entries—many state-of-the-art models are not evaluated on common benchmarks, making direct comparison impossible. The Yamanishi_08 cold-start protocol is applied with varying definitions of S1/S2/S3 across papers. Without standardized evaluation, claims of "state-of-the-art" performance may not be meaningful. Recent work by Zhang et al. (2024) proposes structured, context-sensitive "slice-aware" benchmarking that evaluates performance across biologically meaningful subsets (target families, scaffold diversity), representing a needed advance in evaluation methodology.'),

  h2('7.6 Scalability and Computational Efficiency'),
  p('Models incorporating cross-attention mechanisms (iNGNN-DTI, IHDFN-DTI, Top-DTI, MFCADTI) or bilinear interactions (DrugBAN, BACPI) face quadratic complexity in drug atom count and protein residue count—O(n×m) where n is atom count and m is residue count. For large proteins (>1200 residues) and complex drugs with many atoms, this becomes computationally prohibitive for large-scale virtual screening. TDA computation in Top-DTI adds further overhead. Scalability strategies including sparse attention, linear attention approximations, hierarchical pooling, and node-wise sampling require systematic exploration in the DTI context.'),

  pb()
];

// ============================================================
// SECTION 8: FUTURE DIRECTIONS
// ============================================================
export const futureSection = [
  h1('8. Future Research Directions'),

  h2('8.1 Dynamic Gated Cross-Modal Fusion'),
  p('The proposed H-GNN-RNN-DTI Gated Cross-Attention (Eq. 24–28) provides a principled foundation for next-generation fusion. Future work should systematically benchmark gated fusion against bilinear attention (DrugBAN), mutual attention (MutualDTA), and hierarchical cross-attention (HMSA-DTI) using standardized evaluation. Extensions including iterative cross-modal refinement (multiple cross-attention rounds), graph-level and residue-level simultaneous fusion, and adaptive gate initialization from foundation model embeddings represent promising directions.'),

  h2('8.2 Foundation Model Integration and Multi-Modal Pretraining'),
  p('The success of Top-DTI and ColdDTA demonstrates the transformative impact of foundation model pretraining. Future DTI models should adopt ESM-2 (650M-3B parameters) for protein encoding and ChemBERTa or MolFormer for drug encoding as standard initializations. Beyond initialization, multi-modal contrastive pretraining—learning jointly across drug and protein modalities on large-scale unlabeled data—represents an important open direction. Foundation models specifically pre-trained on drug–target interaction data (rather than general protein/chemical corpora) could provide substantially better downstream performance.'),

  h2('8.3 Structure-Sequence Co-Encoding'),
  p('AlphaFold2 has made protein 3D structure prediction accessible at proteome scale. Future models should integrate sequence-based and structure-based protein encoding: RNN/Transformer over primary sequence combined with GNN over predicted 3D structure graph. EHIGN demonstrates the power of 3D geometric interaction modeling, but its requirement for experimental structures can now be relaxed using AlphaFold2 predictions. Drug 3D conformation generation (e.g., RDKit ETKDG, DiffSBDD) similarly opens opportunities for geometry-aware drug encoding beyond molecular graphs.'),

  h2('8.4 Principled Cold-Start Strategies'),
  p('Beyond pretrained embeddings, future models should incorporate few-shot meta-learning for rapid adaptation to novel drugs and targets; prototypical network approaches that learn to generalize from chemical scaffold families; graph meta-learning on drug–target interaction networks; and data augmentation via molecular generation. Systematic benchmarking under the standardized S1/S2/S3 Yamanishi_08 protocol, extended to BindingDB and ChEMBL cold-splits, should be mandated for fair comparison.'),

  h2('8.5 Slice-Aware and Biologically Grounded Evaluation'),
  p('Following Zhang et al. (2024), future evaluation should adopt slice-aware benchmarking that assesses performance across biologically meaningful subsets: target families (kinases, GPCRs, ion channels), chemical scaffold diversity levels, binding affinity ranges, and disease indications. This would reveal model weaknesses invisible in aggregate metrics and guide development of more robust architectures.'),

  h2('8.6 Quantitative Interpretability Validation'),
  p('Interpretability mechanisms should be validated quantitatively against experimental data. Atom-level attributions should be compared against pharmacophore databases and mutagenesis data. Residue-level attributions should overlap with crystallographic binding contacts (PDB). Automated pipelines for systematic XAI validation—running model attribution against known pharmacophore databases for thousands of drug–target complexes—would establish interpretability as a measurable model property rather than a qualitative claim.'),

  h2('8.7 Data Imbalance and Negative Sampling Strategies'),
  p('Future work should develop principled negative sampling strategies that explicitly model the probability of a "negative" pair being an unconfirmed true positive. Approaches including positive-unlabeled (PU) learning, generative negative sampling via molecular generation, and self-supervised pseudo-negative identification represent promising directions beyond the current unknown-negative assumption.'),

  pb()
];

// ============================================================
// SECTION 9: CONCLUSION
// ============================================================
export const conclusionSection = [
  h1('9. Conclusion'),
  p('This review has provided a comprehensive, critical analysis of 36 DTI/DTA prediction models spanning the full evolution of the field from CNN-based baselines to advanced hybrid multimodal deep learning frameworks. Through systematic model reviews, mathematical formulation, conceptual architecture sketches, and four comparative tables, we have synthesized the state of the art and identified persistent limitations.'),
  p('The central finding is that hybrid multimodal architectures pairing GNNs for drug molecular graph encoding with RNNs, CNNs, or Transformers for protein sequence encoding represent the current best approach to DTI prediction. However, most hybrid models are limited by static concatenation-based fusion, inadequate cold-start generalization strategies, insufficient interpretability mechanisms, and inconsistent evaluation protocols. Advanced fusion mechanisms—cross-attention, bilinear attention, gated attention—and foundation model pretraining are the two highest-impact areas for near-term improvement.'),
  p('The proposed H-GNN-RNN-DTI architecture directly addresses four identified gaps: (1) a novel Gated Cross-Attention fusion module (Eq. 24–28) overcomes static concatenation; (2) ChemBERTa and ESM-2 pretrained embeddings improve cold-start generalization; (3) focal loss and weighted BCE address data imbalance (Eq. 29–30); and (4) attention-based interpretability with biological validation provides actionable XAI. The model represents a principled next-generation framework that integrates methodological innovation with translational applicability.'),
  p('Future DTI research should prioritize: standardized slice-aware evaluation protocols; dynamic gated cross-modal fusion; structure-sequence co-encoding leveraging AlphaFold2; multi-modal contrastive pretraining; principled cold-start generalization strategies; and quantitative interpretability validation against experimental binding data. Addressing these directions will advance DTI prediction toward the reliability, interpretability, and scalability required for real-world drug discovery applications.'),
  pb()
];

// ============================================================
// SECTION: REFERENCES
// ============================================================
export const referenceSection = [
  h1('References'),
  p('Abbasi, K., Razzaghi, P., Poso, A., Ghanbari-Ara, S., & Masoudi-Nejad, A. (2020). Deep learning in drug target interaction prediction: Current and future perspectives. Current Medicinal Chemistry, 28(11), 2100–2113. https://doi.org/10.2174/0929867327666200907141016', { noIndent: true }),
  p('Bae, H., & Nam, H. (2023). GraphATT-DTA: Attention-based novel representation of interaction to predict drug-target binding affinity. Biomedicines, 11(1). https://doi.org/10.3390/biomedicines11010067', { noIndent: true }),
  p('Bagherian, M., Sabeti, E., Wang, K., Sartor, M. A., Nikolovska-Coleska, Z., & Najarian, K. (2021). Machine learning approaches and databases for prediction of drug-target interaction: A survey paper. Briefings in Bioinformatics, 22(1), 247–269. https://doi.org/10.1093/bib/bbz157', { noIndent: true }),
  p('Bian, J., Lu, H., Dong, G., & Wang, G. (2024). Hierarchical multimodal self-attention-based graph neural network for DTI prediction. Briefings in Bioinformatics, 25(4). https://doi.org/10.1093/bib/bbae213', { noIndent: true }),
  p('Bian, J., Lu, H., Wei, L., Li, Y., & Wang, G. (2025). Relational similarity-based graph contrastive learning for DTI prediction. Briefings in Bioinformatics, 26(2). https://doi.org/10.1093/bib/bbaf122', { noIndent: true }),
  p('Cao, J., Chen, Q., Qiu, J., Wang, Y., Lan, W., Du, X., & Tan, K. (2024). NGCN: Drug-target interaction prediction by integrating information and feature learning from heterogeneous network. Journal of Cellular and Molecular Medicine, 28(7), 1–11. https://doi.org/10.1111/jcmm.18224', { noIndent: true }),
  p('Chen, X., Yan, C. C., Zhang, X., Zhang, X., Dai, F., Yin, J., & Zhang, Y. (2016). Drug-target interaction prediction: Databases, web servers and computational models. Briefings in Bioinformatics, 17(4), 696–712. https://doi.org/10.1093/bib/bbv066', { noIndent: true }),
  p('Chen, Y., Liang, X., Du, W., Liang, Y., Wong, G., & Chen, L. (2024). Drug–target interaction prediction based on an interactive inference network. International Journal of Molecular Sciences, 25(14). https://doi.org/10.3390/ijms25147753', { noIndent: true }),
  p('Chun, Y., Li, H., & Wang, S. (2025). SS-DTI: A deep learning method integrating semantic and structural information for drug-target interaction prediction. Journal of Bioinformatics and Computational Biology. https://doi.org/10.1142/S0219720025500027', { noIndent: true }),
  p('Dai, W., Wang, Y., Yan, S., Yu, Q., & Cheng, X. (2025). Heterogeneous network drug-target interaction prediction model based on graph wavelet transform and multi-level contrastive learning. Scientific Reports, 15(1), 1–17. https://doi.org/10.1038/s41598-025-16098-y', { noIndent: true }),
  p('Debnath, K., Rana, P., & Ghosh, P. (2025). A survey on deep learning for drug-target binding prediction: models, benchmarks, evaluation, and case studies. Briefings in Bioinformatics, 26(5). https://doi.org/10.1093/bib/bbaf275', { noIndent: true }),
  p('Deng, G., Shi, C., Ge, R., Hu, R., Wang, C., Qin, F., Pan, C., Mao, H., & Yang, Q. (2025). Efficient substructure feature encoding based on graph neural network blocks for drug-target interaction prediction. Frontiers in Pharmacology, 16, 1–15. https://doi.org/10.3389/fphar.2025.1553743', { noIndent: true }),
  p('Dhannoon, A. K., & Dhannoon, B. N. (2024). Comprehensive review on drug-target interaction prediction—Latest developments and overview. Current Drug Discovery Technologies, 21(2), 56–67. https://doi.org/10.2174/1570163820666230901160043', { noIndent: true }),
  p('Elbasani, E., Njimbouom, S. N., Oh, T. J., Kim, E. H., Lee, H., & Kim, J. D. (2021). GCRNN: Graph convolutional recurrent neural network for compound–protein interaction prediction. BMC Bioinformatics, 22, 1–13. https://doi.org/10.1186/s12859-022-04560-x', { noIndent: true }),
  p('Gao, X., Yan, M., Zhang, C., Wu, G., Shang, J., Zhang, C., & Yang, K. (2025). MDNN-DTA: A multimodal deep neural network for drug-target affinity prediction. Frontiers in Genetics, 16, 1–16. https://doi.org/10.3389/fgene.2025.1527300', { noIndent: true }),
  p('Hamilton, W. L., Ying, R., & Leskovec, J. (2017). Inductive representation learning on large graphs. Advances in Neural Information Processing Systems, 30, 1024–1034.', { noIndent: true }),
  p('He, H., Chen, G., & Chen, C. Y. C. (2023). NHGNN-DTA: A node-adaptive hybrid graph neural network for interpretable drug-target binding affinity prediction. Bioinformatics, 39(6). https://doi.org/10.1093/bioinformatics/btad355', { noIndent: true }),
  p('He, T., Heidemeyer, M., Ban, F., Cherkasov, A., & Ester, M. (2017). SimBoost: A read-across approach for predicting drug-target binding affinities using gradient boosting machines. Journal of Cheminformatics, 9(1), 1–14. https://doi.org/10.1186/s13321-017-0209-z', { noIndent: true }),
  p('Hua, Y., Feng, Z., Song, X., Wu, X.-J., & Kittler, J. (2025). MMDG-DTI: Drug–target interaction prediction via multimodal feature fusion and domain generalization. Pattern Recognition, 157, 110887. https://doi.org/10.1016/j.patcog.2024.110887', { noIndent: true }),
  p('Huang, K., Xiao, C., Glass, L. M., & Sun, J. (2021). MolTrans: Molecular interaction transformer for drug–target interaction prediction. Bioinformatics, 37(6), 830–836. https://doi.org/10.1093/bioinformatics/btaa880', { noIndent: true }),
  p('Jin, Z., Wu, S., Chen, J., Shi, J., & Wu, X. (2021). EmbedDTI: Enhancing the molecular representations via sequence embedding and graph neural network for the prediction of drug–target interaction. Biomolecules, 11(12). https://doi.org/10.3390/biom11121783', { noIndent: true }),
  p('Khojasteh, H., Pirgazi, J., & Sorkhi, A. G. (2023). Improving prediction of drug-target interactions based on fusing multiple features with data balancing and feature selection techniques. PLOS ONE, 18(8), 1–25. https://doi.org/10.1371/journal.pone.0288173', { noIndent: true }),
  p('Kipf, T. N., & Welling, M. (2017). Semi-supervised classification with graph convolutional networks. International Conference on Learning Representations (ICLR).', { noIndent: true }),
  p('Lee, J., Jun, D. W., Song, I., & Kim, Y. (2024). DLM-DTI: A dual language model for the prediction of drug-target interaction with hint-based learning. Journal of Cheminformatics, 16(1), 1–12. https://doi.org/10.1186/s13321-024-00808-1', { noIndent: true }),
  p('Li, M., Guo, Z., Wu, Y., Guo, P., Shi, Y., Hu, S., Wan, W., & Hu, S. (2024). ViDTA: Enhanced drug-target affinity prediction via virtual graph nodes and attention-based feature fusion. Proceedings—2024 IEEE International Conference on Bioinformatics and Biomedicine (BIBM 2024), 42–47. https://doi.org/10.1109/BIBM62325.2024.10822490', { noIndent: true }),
  p('Li, N., Yang, Z., Wang, J., & Lin, H. (2024). Drug–target interaction prediction using knowledge graph embedding. iScience, 27(6). https://doi.org/10.1016/j.isci.2024.109393', { noIndent: true }),
  p('Liao, J., Chen, H., Wei, L., & Wei, L. (2022). GSAML-DTA: An interpretable drug-target binding affinity prediction model based on graph neural networks with self-attention mechanism and mutual information. Computers in Biology and Medicine, 150, 106145. https://doi.org/10.1016/j.compbiomed.2022.106145', { noIndent: true }),
  p('Liao, Q., Zhang, Y., Chu, Y., Ding, Y., Liu, Z., Zhao, X., Wang, Y., Wan, J., Ding, Y., Tiwari, P., Zou, Q., & Han, K. (2025). Application of artificial intelligence in drug-target interactions prediction: A review. NPJ Biomedical Innovations, 2(1). https://doi.org/10.1038/s44385-024-00003-9', { noIndent: true }),
  p('Liu, B., Wu, S., Wang, J., Deng, X., & Zhou, A. (2024). HiGraphDTI: Hierarchical graph representation learning for drug-target interaction prediction. Lecture Notes in Computer Science, 14946 LNAI, 354–370. https://doi.org/10.1007/978-3-031-70365-2_21', { noIndent: true }),
  p('Lu, Z., Song, G., Zhu, H., Lei, C., Sun, X., Wang, K., Qin, L., Chen, Y., Tang, J., & Li, M. (2025). DTIAM: A unified framework for predicting drug-target interactions, binding affinities and drug mechanisms. Nature Communications, 16(1). https://doi.org/10.1038/s41467-025-57828-0', { noIndent: true }),
  p('Luo, Y., Duan, G., Zhao, Q., Bi, X., & Wang, J. (2024). DTKGIN: Predicting drug-target interactions based on knowledge graph and intent graph. Methods, 226, 21–27. https://doi.org/10.1016/j.ymeth.2024.04.010', { noIndent: true }),
  p('Mienye, I. D., Swart, T. G., & Obaido, G. (2024). Recurrent neural networks: A comprehensive review of architectures, variants, and applications. Information, 15(9), 1–34. https://doi.org/10.3390/info15090517', { noIndent: true }),
  p('Minh, N. T., Thin, N., & Truyen, T. (2022). Mitigating cold-start problems in drug-target affinity prediction. Briefings in Bioinformatics, 23(July), 1–13. https://doi.org/10.1093/bib/bbac269', { noIndent: true }),
  p('Nguyen, T., Le, H., Quinn, T. P., Nguyen, T., Le, T. D., & Venkatesh, S. (2021). GraphDTA: Predicting drug target binding affinity with graph neural networks. Bioinformatics, 37(8), 1140–1147. https://doi.org/10.1093/bioinformatics/btaa921', { noIndent: true }),
  p('Ouyang, X., Feng, Y., Cui, C., Li, Y., Zhang, L., & Wang, H. (2025). Improving generalizability of drug–target binding prediction by pre-trained multi-view molecular representations. Bioinformatics, 41(1), 1–9. https://doi.org/10.1093/bioinformatics/btaf002', { noIndent: true }),
  p('Öztürk, H., Özgür, A., & Ozkirimli, E. (2018). DeepDTA: Deep drug–target binding affinity prediction. Bioinformatics, 34(17), i821–i829. https://doi.org/10.1093/bioinformatics/bty593', { noIndent: true }),
  p('Panahandeh, F., & Mansouri, N. (2025). A comprehensive review of neural network-based approaches for drug–target interaction prediction. Molecular Diversity. https://doi.org/10.1007/s11030-025-11303-6', { noIndent: true }),
  p('Quan, N., Ma, S., Zhao, K., Bi, X., & Zhang, L. (2025). MFCADTI: Improving drug-target interaction prediction by integrating multiple features through cross attention mechanism. BMC Bioinformatics, 26(1). https://doi.org/10.1186/s12859-025-06075-7', { noIndent: true }),
  p('Shi, H., Liu, S., Chen, J., Li, X., Ma, Q., & Yu, B. (2019). Predicting drug-target interactions using lasso with random forest based on evolutionary information and chemical structure. Genomics, 111(6), 1839–1852. https://doi.org/10.1016/j.ygeno.2018.12.007', { noIndent: true }),
  p('Suruliandi, A., Idhaya, T., & Raja, S. P. (2024). Drug target interaction prediction using machine learning techniques—A review. International Journal of Interactive Multimedia and Artificial Intelligence, 8(6), 86–100. https://doi.org/10.9781/ijimai.2022.11.002', { noIndent: true }),
  p('Sun, Y., Li, Y. Y., Leung, C. K., & Hu, P. (2024). iNGNN-DTI: Prediction of drug-target interaction with interpretable nested graph neural network and pretrained molecule models. Bioinformatics, 40(3). https://doi.org/10.1093/bioinformatics/btae135', { noIndent: true }),
  p('Talo, M., & Bozdag, S. (2025). Top-DTI: Integrating topological deep learning and large language models for drug-target interaction prediction. Bioinformatics, 41, i133–i141. https://doi.org/10.1093/bioinformatics/btaf183', { noIndent: true }),
  p('Tanoli, Z., Schulman, A., & Aittokallio, T. (2025). Validation guidelines for drug-target prediction methods. Expert Opinion on Drug Discovery, 20(1), 31–46. https://doi.org/10.1080/17460441.2024.2430955', { noIndent: true }),
  p('Tran, H. N. T., Thomas, J. J., & Malim, N. H. A. H. (2022). DeepNC: A framework for drug-target interaction prediction with graph neural networks. PeerJ, 10, 1–24. https://doi.org/10.7717/peerj.13163', { noIndent: true }),
  p('Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. Advances in Neural Information Processing Systems, 30.', { noIndent: true }),
  p('Vefghi, A., Rahmati, Z., & Akbari, M. (2025). Drug-target interaction/affinity prediction: Deep learning models and advances review. Computers in Biology and Medicine, 196, 1–64. https://doi.org/10.1016/j.compbiomed.2025.110438', { noIndent: true }),
  p('Veličković, P., Cucurull, G., Casanova, A., Romero, A., Liò, P., & Bengio, Y. (2018). Graph attention networks. International Conference on Learning Representations (ICLR).', { noIndent: true }),
  p('Wu, Z., Li, W., Liu, G., & Tang, Y. (2018). Network-based methods for prediction of drug-target interactions. Frontiers in Pharmacology, 9, 1–14. https://doi.org/10.3389/fphar.2018.01134', { noIndent: true }),
  p('Xuan, P., Sun, C., Zhang, T., Ye, Y., Shen, T., & Dong, Y. (2019). Gradient boosting decision tree-based method for predicting interactions between target genes and drugs. Frontiers in Genetics, 10, 1–11. https://doi.org/10.3389/fgene.2019.00459', { noIndent: true }),
  p('Yang, H., Chen, Y., Zuo, Y., Deng, Z., Pan, X., Shen, H., Choi, K. S., & Yu, D. J. (2024). MINDG: A drug–target interaction prediction method based on an integrated learning algorithm. Bioinformatics, 40(4). https://doi.org/10.1093/bioinformatics/btae147', { noIndent: true }),
  p('Yang, Z., Zhong, W., Lv, Q., Dong, T., Chen, G., & Chen, C. Y.-C. (2024). Interaction-based inductive bias in graph neural networks: Enhancing protein-ligand binding affinity predictions from 3D structures. IEEE Transactions on Pattern Analysis and Machine Intelligence, 46(12), 8191–8208. https://doi.org/10.1109/TPAMI.2024.3400515', { noIndent: true }),
  p('Yuan, Y., Chen, S., Hu, R., & Wang, X. (2025). MutualDTA: An interpretable drug-target affinity prediction model leveraging pretrained models and mutual attention. Journal of Chemical Information and Modeling, 65(3), 1211–1227. https://doi.org/10.1021/acs.jcim.4c01893', { noIndent: true }),
  p('Zeng, X., Li, S., Lv, S., & Wen, M. (2024). A comprehensive review of the recent advances on predicting drug-target affinity based on deep learning. Frontiers in Pharmacology, 15, 1–15. https://doi.org/10.3389/fphar.2024.1375522', { noIndent: true }),
  p('Zhang, Q., Sun, Z., Zhong, Z., Yang, H., Wei, Y., & Xu, J. (2025). SaeGraphDTI: Drug–target interaction prediction based on sequence attribute extraction and graph neural network. BMC Bioinformatics, 26(1). https://doi.org/10.1186/s12859-025-06195-0', { noIndent: true }),
  p('Zhang, X. M., Liang, L., Liu, L., & Tang, M. J. (2021). Graph neural networks and their current applications in bioinformatics. Frontiers in Genetics, 12, 1–22. https://doi.org/10.3389/fgene.2021.690049', { noIndent: true }),
  p('Zhang, X., Wu, J., Xie, J., Chen, T., & Zhou, K. (2024). Benchmark on drug target interaction modeling from a structure perspective. ArXiv. https://arxiv.org/abs/2407.0', { noIndent: true }),
  p('Zhang, Y., Wang, Q., Baoming, Z., Junliang, F., & Li, S. (2025). IHDFN-DTI: Interpretable hybrid deep feature fusion network for drug–target interaction prediction. Interdisciplinary Sciences: Computational Life Sciences. https://doi.org/10.1007/s12539-025-00712-8', { noIndent: true }),
  p('Zhao, Q., Zhao, H., Zheng, K., & Wang, J. (2022). HyperAttentionDTI: Improving drug-protein interaction prediction by sequence-based deep learning with attention mechanism. Bioinformatics, 38(3), 655–662. https://doi.org/10.1093/bioinformatics/btab715', { noIndent: true }),
  p('Zhijian, L., Shaohua, J., Yigao, L., & Min, G. (2022). GDGRU-DTA: Predicting drug-target binding affinity based on GNN and double GRU. CSIT, 120703, 25–37. https://doi.org/10.5121/csit.2022.120703', { noIndent: true }),
  p('Zhu, Y., Ning, C., Zhang, N., Wang, M., & Zhang, Y. (2024). GSRF-DTI: A framework for drug-target interaction prediction based on a drug-target pair network and representation learning on a large graph. BMC Biology, 22(1). https://doi.org/10.1186/s12915-024-01949-3', { noIndent: true }),
  p('Zuo, Y., Wu, X., Ge, F., Yan, H., Fei, S., Liang, J., & Deng, Z. (2025). Research progress on drug-target interactions in the last five years. Analytical Biochemistry, 697, 115691. https://doi.org/10.1016/j.ab.2024.115691', { noIndent: true }),
];
