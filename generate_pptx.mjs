// generate_pptx.mjs — DTI Proposal Presentation (26 slides + talking points)
import PptxGenJS from 'pptxgenjs';
import fs from 'fs';

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Jamila Abdul-Hadi';
pptx.title = 'Enhanced DTI Prediction Through Hybrid Deep Learning';

const FIGS = 'C:\\Users\\Jamila\\Modeling-DTI\\paper\\figures';
const OUT  = 'C:\\Users\\Jamila\\Modeling-DTI\\paper\\DTI_Proposal_Presentation.pptx';

// ── Colors ─────────────────────────────────────────────────────────────────
const C = {
  navy:'1A3A6E', blue:'1565C0', dblue:'0D47A1', lblue:'DDEEFF',
  teal:'00695C', lteal:'E0F2F1',
  orange:'E65100', lorange:'FFF3E0',
  green:'1B5E20', lgreen:'C8E6C9',
  red:'B71C1C', lred:'FFCDD2',
  purple:'4A148C', lpurp:'F3E5F5',
  gold:'F57F17', lgold:'FFF9C4',
  text:'1C2833', gray:'546E7A', lgray:'ECEFF1',
  white:'FFFFFF', black:'000000',
};

const SW=13.33, SH=7.5;

// ── Helpers ─────────────────────────────────────────────────────────────────
function hdr(sl, title, sub='', col=C.navy) {
  sl.addShape(pptx.ShapeType.rect,{x:0,y:0,w:SW,h:1.05,fill:{color:col},line:{color:col}});
  sl.addText(title,{x:0.35,y:0.05,w:SW-0.7,h:0.62,fontSize:26,bold:true,color:C.white,fontFace:'Calibri',valign:'middle'});
  if(sub) sl.addText(sub,{x:0.35,y:0.67,w:SW-0.7,h:0.34,fontSize:13,color:'AED6F1',fontFace:'Calibri',italic:true});
  sl.addShape(pptx.ShapeType.rect,{x:0,y:SH-0.32,w:SW,h:0.32,fill:{color:C.navy},line:{color:C.navy}});
  sl.addText('School of Computer Sciences  |  Universiti Sains Malaysia  |  PhD Research Proposal 2025/2026',
    {x:0.3,y:SH-0.29,w:10.5,h:0.26,fontSize:8,color:'90CAF9',fontFace:'Calibri'});
}

function num(sl,n) {
  sl.addText(String(n),{x:SW-0.55,y:SH-0.29,w:0.45,h:0.24,fontSize:10,bold:true,color:C.white,align:'right',fontFace:'Calibri'});
}

function stripe(sl,col=C.blue) {
  sl.addShape(pptx.ShapeType.rect,{x:0,y:1.05,w:0.14,h:SH-1.37,fill:{color:col},line:{color:col}});
}

function box(sl,x,y,w,h,fill,brd,title,lines,tSz=12,bSz=10.5,tCol=C.white,lCol=C.text,rx=0.08) {
  sl.addShape(pptx.ShapeType.roundRect,{x,y,w,h,fill:{color:fill},line:{color:brd,pt:1},rectRadius:rx});
  if(title){
    sl.addShape(pptx.ShapeType.rect,{x,y,w,h:0.38,fill:{color:brd},line:{color:brd}});
    sl.addText(title,{x:x+0.1,y:y+0.04,w:w-0.2,h:0.33,fontSize:tSz,bold:true,color:tCol,fontFace:'Calibri'});
  }
  if(lines && lines.length){
    const arr = lines.map(l=>({text:typeof l==='string'?l:l.t,
      options:{fontSize:typeof l==='string'?bSz:l.sz||bSz, color:typeof l==='string'?lCol:l.c||lCol,
      bold:typeof l==='string'?false:!!l.b, bullet:typeof l==='string'?{type:'bullet'}:l.bul!==false?{type:'bullet'}:false,
      fontFace:'Calibri'}}));
    sl.addText(arr,{x:x+0.15,y:y+(title?0.42:0.1),w:w-0.28,h:h-(title?0.5:0.16),valign:'top',fontFace:'Calibri'});
  }
}

function txt(sl,t,x,y,w,h,sz=12,col=C.text,bold=false,align='left',wrap=true,italic=false) {
  sl.addText(t,{x,y,w,h,fontSize:sz,color:col,bold,align,wrap,italic,fontFace:'Calibri',valign:'middle'});
}

function img(sl,file,x,y,w,h) {
  const p=`${FIGS}\\${file}`;
  if(fs.existsSync(p)) sl.addImage({path:p,x,y,w,h});
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  sl.addShape(pptx.ShapeType.rect,{x:0,y:0,w:SW,h:SH,fill:{color:C.navy},line:{color:C.navy}});
  // Diagonal accent
  sl.addShape(pptx.ShapeType.rect,{x:0,y:0,w:SW,h:2.2,fill:{color:C.dblue},line:{color:C.dblue}});
  sl.addShape(pptx.ShapeType.rect,{x:0,y:SH-1.6,w:SW,h:1.6,fill:{color:C.dblue},line:{color:C.dblue}});
  // USM header
  sl.addText('SCHOOL OF COMPUTER SCIENCES',{x:0.4,y:0.18,w:SW-0.8,h:0.42,fontSize:16,bold:true,color:'90CAF9',fontFace:'Calibri',align:'center'});
  sl.addText('UNIVERSITI SAINS MALAYSIA',{x:0.4,y:0.52,w:SW-0.8,h:0.38,fontSize:14,color:'BDE3FA',fontFace:'Calibri',align:'center'});
  sl.addText('RESEARCH PROPOSAL  |  SEMESTER 2  2025/2026',{x:0.4,y:0.86,w:SW-0.8,h:0.3,fontSize:11,color:'90CAF9',fontFace:'Calibri',align:'center',italic:true});
  // Main title box
  sl.addShape(pptx.ShapeType.roundRect,{x:0.5,y:1.6,w:SW-1,h:2.4,fill:{color:C.blue},line:{color:C.gold,pt:2},rectRadius:0.12});
  sl.addText('Enhanced Drug-Target Interaction Prediction\nThrough Hybrid Deep Learning Approaches',
    {x:0.7,y:1.7,w:SW-1.4,h:2.2,fontSize:26,bold:true,color:C.white,fontFace:'Calibri',align:'center',valign:'middle'});
  // Info grid
  const cols=['PRESENTER','MATRIC NUMBER','SUPERVISOR','PROGRAM'];
  const vals=['Jamila Abdul-Hadi','24100625','Assoc. Prof. Dr. Nurul Hashimah\nAhamed Hassain Malim','Doctor of Philosophy (PhD)'];
  cols.forEach((c,i)=>{
    const x=0.4+i*3.1, y=4.3;
    sl.addShape(pptx.ShapeType.roundRect,{x,y,w:3.0,h:1.35,fill:{color:'0D2B5A'},line:{color:'4A90D9'},rectRadius:0.08});
    sl.addText(c,{x:x+0.08,y:y+0.06,w:2.84,h:0.3,fontSize:9,bold:true,color:'90CAF9',fontFace:'Calibri'});
    sl.addText(vals[i],{x:x+0.08,y:y+0.36,w:2.84,h:0.9,fontSize:11,color:C.white,fontFace:'Calibri',valign:'top',wrap:true});
  });
  sl.addText('School of Computer Sciences  |  2025',{x:0,y:SH-0.3,w:SW,h:0.3,fontSize:9,color:'7FA8D4',fontFace:'Calibri',align:'center'});
  sl.addNotes(`TALKING POINTS — TITLE SLIDE

Good [morning/afternoon], Professor [Supervisor's name]. Thank you for this opportunity to present my PhD research proposal.

My name is Jamila Abdul-Hadi, matric number 24100625, under your supervision in the School of Computer Sciences at USM.

The title of my proposed research is "Enhanced Drug-Target Interaction Prediction Through Hybrid Deep Learning Approaches." This work addresses one of the most computationally challenging problems in modern drug discovery — accurately and efficiently predicting how drug molecules interact with protein targets.

Over the next [estimated time] minutes, I will walk you through the complete proposal, covering the research background, problem statement, objectives, methodology, and expected contributions.

I welcome your questions and feedback throughout or at the end of the presentation.`);
  num(sl,1);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 2 — PRESENTATION OUTLINE
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Presentation Outline');
  stripe(sl);
  txt(sl,'The following sections structure this research proposal:',0.4,1.15,SW-0.5,0.3,11,C.gray,false,'left',true,true);

  const items=[
    ['1','Introduction & Background','💊 Drug discovery landscape & computational motivation',C.blue],
    ['2','Problem Statement','⚠️ Four critical gaps in existing DTI models',C.red],
    ['3','Research Objectives & Questions','🎯 Main aim, three objectives, three research questions',C.teal],
    ['4','Scope & Significance','📐 Research boundaries and expected impact',C.purple],
    ['5','Literature Review Overview','📚 DTI methodologies and critical analysis of baselines',C.navy],
    ['6','Methodology','🏗️ H-GNN-RNN-DTI architecture, training, evaluation',C.orange],
    ['7','Timeline & Milestones','📅 3-year Gantt chart and research phases','5D4037'],
    ['8','Expected Outcomes & References','✅ Contributions, publications, and key citations',C.green],
  ];

  items.forEach(([n,title,sub,col],i)=>{
    const r=Math.floor(i/2), c=i%2;
    const x=0.28+c*6.55, y=1.52+r*1.38;
    sl.addShape(pptx.ShapeType.roundRect,{x,y,w:6.35,h:1.28,fill:{color:C.lgray},line:{color:col,pt:2},rectRadius:0.1});
    sl.addShape(pptx.ShapeType.rect,{x,y,w:0.48,h:1.28,fill:{color:col},line:{color:col}});
    sl.addText(n,{x:x+0.02,y:y+0.4,w:0.44,h:0.48,fontSize:18,bold:true,color:C.white,align:'center',fontFace:'Calibri'});
    sl.addText(title,{x:x+0.58,y:y+0.1,w:5.65,h:0.4,fontSize:13,bold:true,color:col,fontFace:'Calibri'});
    sl.addText(sub,{x:x+0.58,y:y+0.5,w:5.65,h:0.65,fontSize:10.5,color:C.gray,fontFace:'Calibri',valign:'top',wrap:true});
  });

  sl.addNotes(`TALKING POINTS — PRESENTATION OUTLINE

This slide maps the eight thematic sections I will cover today.

Section 1 sets the stage — I'll explain why drug-target interaction prediction matters and how computational approaches have evolved.

Section 2 identifies the four specific technical gaps that motivate this research: weak feature fusion, cold-start failure, lack of interpretability, and data imbalance.

Section 3 presents the three research questions and three specific objectives that precisely define what this study will achieve.

Section 4 defines the research boundaries — what is and is not within scope — and articulates why this work matters scientifically and practically.

Section 5 reviews the relevant literature, focusing on three key baseline models that directly inform our design.

Section 6 is the core — I'll present the proposed H-GNN-RNN-DTI architecture in detail.

Section 7 presents the realistic 3-year timeline with measurable milestones.

Section 8 closes with expected contributions and selected references.`);
  num(sl,2);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 3 — INTRODUCTION: DRUG DISCOVERY CHALLENGE
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Introduction & Background','The Drug Discovery Challenge',C.blue);
  stripe(sl,C.blue);

  // Left column — problem
  box(sl,0.28,1.15,5.8,2.8,C.lred,C.red,'Why DTI Prediction Matters',[
    {t:'Traditional drug development costs ~$2.6 billion per approved drug',b:true,sz:11},
    {t:'Average development timeline: 10–15 years from discovery to market',sz:11},
    {t:'Only ~1 in 5,000 candidate compounds reaches clinical approval',sz:11},
    {t:'Wet-lab DTI assays are expensive, slow, and cannot scale to millions of compound-target pairs',sz:11},
  ],12,10.5,C.white,C.text);

  // Right column — solution motivation
  box(sl,6.28,1.15,6.75,2.8,C.lblue,C.blue,'Computational DTI Prediction: The Solution',[
    {t:'In silico prediction screens millions of pairs in hours vs. years',sz:11},
    {t:'Enables drug repurposing — identifying new uses for approved drugs',sz:11},
    {t:'Predicts off-target effects early, improving safety profiles',sz:11},
    {t:'Deep learning models automatically learn complex molecular features without hand-crafting',sz:11},
  ],12,10.5,C.blue,C.text);

  // Bottom evolution bar
  sl.addShape(pptx.ShapeType.rect,{x:0.28,y:4.1,w:12.75,h:0.3,fill:{color:C.lgray},line:{color:C.lgray}});
  const stages=['Molecular\nDocking','Ligand-Based\nQSAR','Classical\nML','Deep\nLearning','Hybrid\nMultimodal DL\n(This Study)'];
  const scols=[C.gray,C.teal,C.blue,C.orange,C.red];
  stages.forEach((s,i)=>{
    const x=0.28+i*2.55;
    sl.addShape(pptx.ShapeType.roundRect,{x,y:3.85,w:2.4,h:0.66,fill:{color:scols[i]},line:{color:scols[i]},rectRadius:0.08});
    sl.addText(s,{x:x+0.05,y:3.87,w:2.3,h:0.62,fontSize:10,bold:i===4,color:C.white,align:'center',fontFace:'Calibri',valign:'middle'});
    if(i<4) sl.addText('→',{x:x+2.4,y:3.95,w:0.15,h:0.4,fontSize:14,color:C.gray,align:'center',fontFace:'Calibri'});
  });
  sl.addText('Evolution of Computational DTI Methodology',{x:0.28,y:4.48,w:12.75,h:0.28,fontSize:10,color:C.gray,italic:true,align:'center',fontFace:'Calibri'});

  // Key stat boxes
  const stats=[['$2.6B','Per drug','Cost',C.red],['15 Years','To approval','Timeline','5D4037'],['~5,000+','Targets','Human proteins',C.blue],['Billions','Pairs','Chemical space',C.green]];
  stats.forEach(([v,l,sub,col],i)=>{
    const x=0.28+i*3.2, y=4.88;
    sl.addShape(pptx.ShapeType.roundRect,{x,y,w:3.1,h:1.06,fill:{color:C.lgray},line:{color:col,pt:2},rectRadius:0.08});
    sl.addText(v,{x:x+0.08,y:y+0.04,w:2.94,h:0.46,fontSize:22,bold:true,color:col,align:'center',fontFace:'Calibri'});
    sl.addText(l,{x:x+0.08,y:y+0.48,w:2.94,h:0.25,fontSize:10,bold:true,color:C.text,align:'center',fontFace:'Calibri'});
    sl.addText(sub,{x:x+0.08,y:y+0.72,w:2.94,h:0.24,fontSize:9,color:C.gray,align:'center',fontFace:'Calibri'});
  });

  sl.addNotes(`TALKING POINTS — INTRODUCTION: DRUG DISCOVERY CHALLENGE

The motivation for this research starts with a sobering reality: developing a single new drug costs approximately $2.6 billion and takes 10 to 15 years, with a very high attrition rate — only about 1 in 5,000 drug candidates ever reaches market approval.

A major bottleneck is the experimental identification of drug-target interactions. Traditional wet-lab assays — like binding affinity measurements, co-crystallization, or mutagenesis studies — are inherently slow, expensive, and cannot realistically scale to cover the billions of possible drug-protein pairs.

This is where computational DTI prediction becomes critical. By training machine learning models on known interactions, we can screen millions of compound-target pairs computationally in a fraction of the time and cost, identifying the most promising candidates to prioritize for experimental validation.

The bottom bar shows how the field has evolved: from physics-based molecular docking in the 1980s, through QSAR and classical machine learning, to the deep learning revolution of the past decade. My proposed work represents the frontier of this evolution — hybrid multimodal deep learning that combines the strengths of multiple architectures.

The four statistics at the bottom reinforce the scale of the problem: the enormous cost, the long timeline, the complexity of the human proteome, and the vast chemical space that computational methods must navigate.`);
  num(sl,3);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 4 — INTRODUCTION: DTI FUNDAMENTALS
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Introduction & Background','Drug–Target Interaction: Biological Foundations',C.blue);
  stripe(sl,C.blue);

  box(sl,0.28,1.15,4.1,5.6,C.lblue,C.blue,'Drug Representation',[
    {t:'SMILES String → Molecular Graph',b:true,sz:11.5},
    {t:'G = (V, E) where V = atoms, E = bonds',sz:11},
    {t:'Node features: atomic number, valence, aromaticity, hybridization',sz:10.5},
    {t:'Edge features: bond type, conjugation, ring membership',sz:10.5},
    {t:'Pre-trained: ChemBERTa embeddings for node initialization',sz:10.5},
  ],12,10.5,C.blue,C.text);

  box(sl,4.58,1.15,4.1,5.6,C.lgreen,C.green,'Protein Representation',[
    {t:'FASTA Amino Acid Sequence',b:true,sz:11.5},
    {t:'x = (x₁, x₂, ..., x_T) residue string',sz:11},
    {t:'Encoded via ESM-2 protein language model (650M params)',sz:10.5},
    {t:'Captures evolutionary and structural context',sz:10.5},
    {t:'Variable length: 20 to 35,000+ residues',sz:10.5},
  ],12,10.5,C.green,C.text);

  box(sl,8.88,1.15,4.15,5.6,C.lpurp,C.purple,'Prediction Tasks',[
    {t:'Binary Classification (DTI)',b:true,sz:11.5},
    {t:'Does drug d interact with target t? → {0,1}',sz:11},
    {t:'Evaluated with AUC-ROC, AUPR',sz:10.5},
    {t:'Regression (DTA)',b:true,sz:11.5},
    {t:'Binding affinity value: pKd, pKi, pIC₅₀ (continuous)',sz:11},
    {t:'Evaluated with RMSE, CI, PCC',sz:10.5},
    {t:'Target Protein Classes:',b:true,sz:11.5},
    {t:'Enzymes, Ion Channels, GPCRs, Nuclear Receptors',sz:10.5},
  ],12,10.5,C.purple,C.text);

  sl.addNotes(`TALKING POINTS — DTI FUNDAMENTALS

Before diving into the technical approach, let me ground the problem biologically.

A drug–target interaction occurs when a small-molecule drug non-covalently binds to a protein target — forming hydrogen bonds, hydrophobic contacts, and electrostatic interactions. The strength of this binding is quantified by the dissociation constant K_d, the inhibitory concentration IC₅₀, or the inhibition constant K_i. Our computational task is to predict either whether this interaction occurs (classification) or how strong it is (regression).

Drugs are computationally represented as molecular graphs — atoms are nodes with features describing their chemistry, and bonds are edges. We also have SMILES strings, which encode this graph as a linear sequence of characters. Importantly, we will initialize node features using ChemBERTa, a language model pre-trained on millions of drug structures.

Proteins are represented as ordered sequences of amino acid residues — their primary structure. We will encode these using ESM-2, a state-of-the-art protein language model that captures both local sequence patterns and long-range evolutionary dependencies.

The prediction can be framed in two ways: as binary classification — does this drug interact with this target — or as regression, predicting the exact binding affinity value. My proposed model supports both within a unified framework.

Supervisor may ask: Why use both graph AND sequence representations? The answer is that each captures different, complementary aspects of the molecules — graphs capture topology and structure, while sequences capture evolutionary context and functional motifs.`);
  num(sl,4);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 5 — PROBLEM STATEMENT
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Problem Statement','Four Critical Limitations in Existing DTI Models',C.red);
  stripe(sl,C.red);

  const gaps=[
    ['🧩','Weak Cross-Modal\nFeature Integration',
     'Existing models (GSRF-DTI, TTModel, DTKGIN) use static, shallow fusion — simple concatenation of drug and protein embeddings. This prevents meaningful cross-modal interaction and loses binding-site geometry information.',
     C.lred,C.red],
    ['❄️','Cold-Start\nGeneralization Failure',
     'Models fail to generalize to novel drugs or targets unseen during training (S2/S3 cold-start settings), due to data sparsity and biased training distributions. No foundation-model pretraining is employed.',
     C.lblue,C.blue],
    ['⬛','"Black Box" Model\nPredictions',
     'High-performing models lack atom-level and residue-level interpretability mechanisms. Predictions cannot guide rational drug design or structure-activity relationship (SAR) studies — a critical translational barrier.',
     C.lgold,C.gold],
    ['⚖️','Severe Data\nImbalance',
     'Known positive DTI pairs are vastly outnumbered by unknown/negative pairs. Standard training without imbalance-aware loss functions produces biased models with inflated accuracy but poor recall on positives.',
     C.lpurp,C.purple],
  ];

  gaps.forEach(([ico,title,desc,fill,brd],i)=>{
    const r=Math.floor(i/2), col=i%2;
    const x=0.28+col*6.54, y=1.18+r*2.65;
    sl.addShape(pptx.ShapeType.roundRect,{x,y,w:6.34,h:2.5,fill:{color:fill},line:{color:brd,pt:2},rectRadius:0.1});
    sl.addText(ico,{x:x+0.12,y:y+0.06,w:0.6,h:0.58,fontSize:22,color:brd,fontFace:'Segoe UI Emoji'});
    sl.addText(title,{x:x+0.72,y:y+0.08,w:5.5,h:0.58,fontSize:13.5,bold:true,color:brd,fontFace:'Calibri',valign:'middle'});
    sl.addText(desc,{x:x+0.15,y:y+0.72,w:6.05,h:1.68,fontSize:11,color:C.text,fontFace:'Calibri',valign:'top',wrap:true});
  });

  // Motivation banner
  sl.addShape(pptx.ShapeType.rect,{x:0.28,y:SH-0.85,w:12.75,h:0.52,fill:{color:C.navy},line:{color:C.navy}});
  sl.addText('✓  Research Motivation: H-GNN-RNN-DTI is designed to simultaneously address all four gaps through dynamic gated fusion, foundation-model pretraining, attention-based XAI, and imbalance-aware training.',
    {x:0.4,y:SH-0.84,w:12.5,h:0.5,fontSize:11,bold:true,color:C.white,fontFace:'Calibri',valign:'middle'});

  sl.addNotes(`TALKING POINTS — PROBLEM STATEMENT

These four gaps represent the core motivation for this research. Let me walk through each one.

GAP 1 — Weak Feature Integration: The most widespread limitation is that existing hybrid models simply concatenate drug and protein embeddings — they glue the two vectors together without any mechanism for them to interact. Models like GSRF-DTI use DeepWalk embeddings followed by Random Forest classification, while DTKGIN uses an inner product of KG entity embeddings. Neither allows drug atoms to selectively attend to relevant protein residues, which is exactly what happens during physical binding.

GAP 2 — Cold-Start Failure: Real drug discovery constantly encounters novel drugs and unexplored targets. When a model is tested on compounds or proteins it has never seen during training — what we call cold-start scenarios — performance drops dramatically. DTKGIN, for example, achieves AUC of 0.950 in warm-start settings but drops to 0.851 for cold-target prediction. Without pre-trained molecular and protein language model embeddings, models cannot transfer biochemical knowledge to novel entities.

GAP 3 — Interpretability: Medicinal chemists need to know WHY a model predicts an interaction — specifically which drug functional groups and protein residues drive the predicted binding. Without this, computational predictions cannot guide experimental design or lead optimization. Currently, none of the three baseline models provide atom-level or residue-level attribution.

GAP 4 — Data Imbalance: DTI datasets have very few confirmed positive interactions relative to the vast space of uncharacterized pairs, which are treated as negatives. Standard cross-entropy training on such imbalanced data produces models that achieve high accuracy by simply predicting "no interaction" for most pairs — but this is useless for drug discovery.

The motivation banner at the bottom summarizes my proposed solution: H-GNN-RNN-DTI addresses all four gaps simultaneously.`);
  num(sl,5);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 6 — RESEARCH QUESTIONS & OBJECTIVES
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Research Questions & Objectives','Three Questions Driving Three Specific Objectives',C.teal);
  stripe(sl,C.teal);

  // Main aim banner
  sl.addShape(pptx.ShapeType.roundRect,{x:0.28,y:1.18,w:12.75,h:0.68,fill:{color:C.navy},line:{color:C.gold,pt:2},rectRadius:0.1});
  sl.addText('Main Aim: Design an enhanced hybrid deep learning model integrating GNNs and RNNs through a novel dynamic cross-modal fusion mechanism to improve DTI prediction performance, generalization, and interpretability.',
    {x:0.45,y:1.2,w:12.4,h:0.62,fontSize:12,bold:true,color:C.white,fontFace:'Calibri',valign:'middle'});

  const rqs=[
    ['Q1','How can a Gated Cross-Attention fusion mechanism effectively integrate GNN-based drug encoders and RNN-based protein encoders, and how does this improve DTI prediction over static concatenation methods?',
     'O1','Design and evaluate H-GNN-RNN-DTI integrating structural graph and sequence encoders via an advanced cross-modal fusion mechanism, achieving statistically significant improvements over concatenation-based baselines.'],
    ['Q2','To what extent can pre-trained molecular and protein language embeddings, combined with imbalance-aware learning strategies, improve generalization to unseen drugs, targets, and cross-dataset scenarios?',
     'O2','Develop a robust representation learning and pretraining strategy integrating imbalance-aware learning and foundation-model embeddings to significantly enhance cold-start predictive performance.'],
    ['Q3','Can an attention-enhanced hybrid model provide interpretable, biologically meaningful insights by identifying key binding residues and pharmacophoric features?',
     'O3','Implement and benchmark an attention-based interpretability layer generating quantitative and visual explanations of DTI/DTA predictions to support structure–activity relationship (SAR) studies.'],
  ];

  rqs.forEach(([qn,qt,on,ot],i)=>{
    const y=1.98+i*1.65;
    // Question
    sl.addShape(pptx.ShapeType.roundRect,{x:0.28,y,w:6.3,h:1.5,fill:{color:C.lteal},line:{color:C.teal,pt:1.5},rectRadius:0.08});
    sl.addShape(pptx.ShapeType.rect,{x:0.28,y,w:0.52,h:1.5,fill:{color:C.teal},line:{color:C.teal}});
    sl.addText(qn,{x:0.3,y:y+0.52,w:0.48,h:0.46,fontSize:16,bold:true,color:C.white,align:'center',fontFace:'Calibri'});
    sl.addText(qt,{x:0.88,y:y+0.08,w:5.6,h:1.34,fontSize:10.5,color:C.text,fontFace:'Calibri',valign:'top',wrap:true});
    // Arrow
    sl.addText('→',{x:6.62,y:y+0.55,w:0.35,h:0.5,fontSize:22,color:C.teal,align:'center',fontFace:'Calibri'});
    // Objective
    sl.addShape(pptx.ShapeType.roundRect,{x:7.0,y,w:6.03,h:1.5,fill:{color:C.lgray},line:{color:C.navy,pt:1.5},rectRadius:0.08});
    sl.addShape(pptx.ShapeType.rect,{x:7.0,y,w:0.52,h:1.5,fill:{color:C.navy},line:{color:C.navy}});
    sl.addText(on,{x:7.02,y:y+0.52,w:0.48,h:0.46,fontSize:16,bold:true,color:C.white,align:'center',fontFace:'Calibri'});
    sl.addText(ot,{x:7.6,y:y+0.08,w:5.33,h:1.34,fontSize:10.5,color:C.text,fontFace:'Calibri',valign:'top',wrap:true});
  });

  sl.addNotes(`TALKING POINTS — RESEARCH QUESTIONS & OBJECTIVES

This slide shows the direct mapping between each research question and its corresponding specific objective.

The Main Aim at the top summarizes the overarching goal: build a hybrid model that is more accurate, more generalizable, and more interpretable than existing DTI predictors.

Question 1 and Objective 1 address the architectural innovation — specifically whether a gated cross-attention fusion mechanism can outperform the simpler concatenation strategy used by current models. This is the primary technical contribution of the work.

Question 2 and Objective 2 address the cold-start challenge — can pre-trained embeddings from large-scale molecular and protein language models (ChemBERTa and ESM-2) help the model generalize to novel drugs and targets? This is evaluated explicitly using cold-drug (S2) and cold-target (S3) test splits.

Question 3 and Objective 3 address interpretability — can the model identify which drug atoms and protein residues drive the predicted interaction? This makes the model useful for medicinal chemists designing and optimizing drug candidates.

Each objective is measurable: O1 requires statistically significant performance improvements, O2 requires demonstrated cold-start generalization, and O3 requires both quantitative metrics and biological validation of attention maps against known binding site data.`);
  num(sl,6);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 7 — SCOPE & SIGNIFICANCE
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Scope & Significance of the Research','Research Boundaries and Expected Impact',C.purple);
  stripe(sl,C.purple);

  // Scope
  box(sl,0.28,1.18,6.2,4.18,C.lpurp,C.purple,'Scope: What This Study Covers',[
    {t:'Prediction Tasks:',b:true,sz:11.5},{t:'Binary DTI classification AND continuous DTA regression (pKd, pKi, pIC₅₀)',sz:11},
    {t:'Drug Modality:',b:true,sz:11.5},{t:'SMILES → molecular graphs using RDKit; ChemBERTa node initialization',sz:11},
    {t:'Protein Modality:',b:true,sz:11.5},{t:'FASTA sequences; ESM-2 (650M params) contextual embeddings',sz:11},
    {t:'Benchmark Datasets:',b:true,sz:11.5},{t:'BindingDB, DAVIS, KIBA, DrugBank, ChEMBL, Yamanishi_08, Luo_17',sz:11},
    {t:'Architecture:',b:true,sz:11.5},{t:'H-GAT (3L/8 heads) + Bi-LSTM/Bi-GRU + Gated Cross-Attention Fusion',sz:11},
    {t:'Evaluation:',b:true,sz:11.5},{t:'AUC-ROC, AUPR, RMSE, MAE, CI, PCC; cold-start S1/S2/S3; ablation studies',sz:11},
  ],12,10.5,C.purple,C.text);

  // Out of scope
  box(sl,6.6,1.18,6.43,1.85,C.lred,C.red,'Explicitly Outside Scope',[
    {t:'Wet-lab experimental validation of predicted interactions',sz:11},
    {t:'Non-small-molecule ligands (peptides, antibodies, macromolecules)',sz:11},
    {t:'Large-scale industrial deployment or clinical applications',sz:11},
  ],12,10.5,C.red,C.text);

  // Significance
  const sigs=[
    [C.blue,'Methodological','Novel gated cross-attention fusion advances multimodal deep learning theory beyond static concatenation'],
    [C.green,'Practical','Scalable virtual screening tool reduces experimental costs; supports drug repurposing'],
    [C.orange,'Translational','Attention-based XAI provides chemists with actionable binding site insights for SAR studies'],
    [C.purple,'Scientific','Biologically grounded evaluation (cold-start, slice-aware) raises DTI benchmark standards'],
  ];
  sl.addText('Significance:',{x:6.6,y:3.1,w:6.43,h:0.3,fontSize:13,bold:true,color:C.navy,fontFace:'Calibri'});
  sigs.forEach(([col,area,desc],i)=>{
    const y=3.42+i*0.78;
    sl.addShape(pptx.ShapeType.roundRect,{x:6.6,y,w:6.43,h:0.72,fill:{color:C.lgray},line:{color:col,pt:2},rectRadius:0.07});
    sl.addShape(pptx.ShapeType.rect,{x:6.6,y,w:1.5,h:0.72,fill:{color:col},line:{color:col}});
    sl.addText(area,{x:6.62,y:y+0.18,w:1.46,h:0.36,fontSize:11,bold:true,color:C.white,align:'center',fontFace:'Calibri'});
    sl.addText(desc,{x:8.2,y:y+0.08,w:4.72,h:0.56,fontSize:10.5,color:C.text,fontFace:'Calibri',valign:'middle',wrap:true});
  });

  sl.addNotes(`TALKING POINTS — SCOPE & SIGNIFICANCE

The scope section clarifies exactly what this study will and will not do — an important boundary-setting exercise for a PhD proposal.

In-scope: The study predicts both binary DTIs (does interaction occur?) and continuous DTAs (how strong is the binding?) using computational methods only. Drugs are represented as molecular graphs from SMILES; proteins as amino acid sequences encoded with ESM-2. Seven benchmark datasets will be used for training, validation, and testing. The architecture — H-GAT with Bi-LSTM/GRU and Gated Cross-Attention — is specified. Evaluation includes both standard metrics and cold-start protocols.

Out-of-scope: We will not perform any wet-lab experiments, which keeps the work computationally focused and feasible within the PhD timeline. Non-small-molecule ligands like peptides or antibodies have different structural properties and are excluded to maintain a coherent scope. Industrial deployment is also excluded.

The four significance areas explain why this work matters beyond the thesis:

Methodologically, we advance the theory of multimodal learning in bioinformatics by introducing principled dynamic fusion.

Practically, the resulting tool can accelerate virtual screening pipelines for pharmaceutical companies, reducing the cost and time of early-stage drug discovery.

Translationally, the interpretability module makes predictions actionable for medicinal chemists — they can understand which parts of a drug molecule and protein to modify.

Scientifically, our rigorous cold-start evaluation protocol raises the bar for how DTI models should be benchmarked in the community.`);
  num(sl,7);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 8 — LITERATURE REVIEW: OVERVIEW
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Literature Review','Overview of DTI Prediction Methodology Taxonomy',C.navy);
  stripe(sl);
  img(sl,'fig2_mindmap.png',0.28,1.12,7.2,6.04);

  // Right panel
  box(sl,7.7,1.12,5.35,2.85,C.lblue,C.blue,'Five Methodological Generations',[
    {t:'Generation 1: Molecular Docking — 3D physics simulation, structure-dependent, slow',sz:10.5},
    {t:'Generation 2: Ligand-Based / QSAR — fingerprint similarity, fails for novel scaffolds',sz:10.5},
    {t:'Generation 3: Classical ML — SVM, RF; requires hand-crafted features; cold-start problem',sz:10.5},
    {t:'Generation 4: Deep Learning — CNN (DeepDTA), GNN (GraphDTA), RNN; automatic feature learning',sz:10.5},
    {t:'Generation 5: Hybrid Multimodal DL — integrates multiple modalities with attention fusion [THIS STUDY]',sz:10.5,b:true},
  ],12,10.5,C.blue,C.text);

  box(sl,7.7,4.12,5.35,3.04,C.lgray,C.navy,'36 Models Reviewed in This Study',[
    {t:'CNN-based: DeepDTA, DTI-RCNN',sz:10.5},
    {t:'GNN-based: GraphDTA, SaeGraphDTI, NHGNN-DTA',sz:10.5},
    {t:'Attention: MutualDTA, GSAML-DTA, GraphATT-DTA',sz:10.5},
    {t:'Transformer: TransformerCPI, MolTrans, EmbedDTI',sz:10.5},
    {t:'KG-based: TTModel, DTKGIN (baseline)',sz:10.5},
    {t:'Network: GSRF-DTI (baseline), MINDG',sz:10.5},
    {t:'Advanced Hybrid: iNGNN-DTI, Top-DTI, HMSA-DTI, MMDG-DTI',sz:10.5},
    {t:'Cold-Start: DrugBAN, ColdDTA, CoaDTI, BACPI',sz:10.5},
  ],12,10.5,C.navy,C.text);

  sl.addNotes(`TALKING POINTS — LITERATURE REVIEW OVERVIEW

This mind map shows the six broad methodological paradigms covered in the literature review component of my work.

Starting from the centre — DTI Prediction Methods — six branches radiate out, each representing a different approach.

Physics-based methods at the top were the earliest approach but face fundamental scalability limitations.

Classical Machine Learning in the upper right improved scalability through feature engineering but required domain expertise and could not generalize to novel molecules.

Deep Learning architectures — CNNs, GNNs, and RNNs — eliminated manual feature engineering but each architecture captures only part of the molecular picture.

Transformer and Foundation Models represent the most recent generation, leveraging large-scale pretraining for richer representations.

Hybrid Multimodal Deep Learning — the focus of this proposal — combines multiple architectures to overcome the limitations of single-architecture approaches.

Finally, Interpretable and Cold-Start Models represent specialized directions that address the practical deployment requirements.

On the right, I list the 36 models reviewed in my comprehensive literature review. The three highlighted baseline models — GSRF-DTI, TTModel, and DTKGIN — are the most recent comparable approaches against which my proposed model will be benchmarked.

I should mention that this review resulted in a companion review paper that I have been developing as a systematic academic output alongside the proposal.`);
  num(sl,8);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 9 — LITERATURE REVIEW: BASELINE ANALYSIS
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Literature Review','Critical Analysis of Three Key Baseline Models',C.navy);
  stripe(sl);

  const models=[
    ['GSRF-DTI','Zhu et al., 2024','AUROC 0.9818\n(Luo_17)',
     ['DeepWalk + GraphSAGE + Random Forest','Drug-Target Pair Network (DTP-NET)','Network-level topological features'],
     ['No GNN molecular graph or RNN sequence encoding','Static concatenation fusion — no cross-modal interaction','Random Forest lacks atom/residue-level XAI','Explicitly acknowledged: "need for data imbalance strategies"'],
     C.blue,C.lred],
    ['TTModel','N. Li et al., 2024','AUPR 0.95\n(GPCR class)',
     ['Knowledge Graph embedding','Relation triple encoder (structural + textual)','Type triple encoder (entity type info)'],
     ['No SMILES molecular graph encoding','No direct amino acid sequence processing','Performance depends on KG completeness','No dynamic cross-modal attention'],
     C.teal,'FFF3E0'],
    ['DTKGIN','Luo et al., 2024','AUC 0.894 (S2\ncold-drug)',
     ['KG + Intent Graph mechanism','Latent intent nodes for interaction granularity','Relation path-aware GNN aggregation'],
     ['No modality-specific encoders (GNN/RNN)','Inner product prediction — no attention fusion','Random initialization — no foundation model pretraining','Intent node count is dataset-specific hyperparameter'],
     C.purple,C.lgreen],
  ];

  models.forEach(([name,ref,perf,arch,gaps,col,bgcol],i)=>{
    const x=0.28+i*4.36, y=1.18;
    sl.addShape(pptx.ShapeType.roundRect,{x,y,w:4.2,h:5.6,fill:{color:bgcol},line:{color:col,pt:2},rectRadius:0.1});
    sl.addShape(pptx.ShapeType.rect,{x,y,w:4.2,h:0.52,fill:{color:col},line:{color:col}});
    sl.addText(name,{x:x+0.1,y:y+0.05,w:2.8,h:0.42,fontSize:16,bold:true,color:C.white,fontFace:'Calibri'});
    sl.addText(ref,{x:x+0.1,y:y+0.05,w:4.0,h:0.42,fontSize:9,color:'D0ECFF',fontFace:'Calibri',align:'right'});
    // Performance badge
    sl.addShape(pptx.ShapeType.roundRect,{x:x+0.12,y:y+0.6,w:3.96,h:0.62,fill:{color:col},line:{color:col},rectRadius:0.06});
    sl.addText(`Best Performance: ${perf}`,{x:x+0.15,y:y+0.62,w:3.9,h:0.58,fontSize:11,bold:true,color:C.white,align:'center',fontFace:'Calibri',valign:'middle'});
    // Architecture
    sl.addText('Architecture:',{x:x+0.12,y:y+1.3,w:3.96,h:0.26,fontSize:10.5,bold:true,color:col,fontFace:'Calibri'});
    arch.forEach((a,j)=>sl.addText(`• ${a}`,{x:x+0.18,y:y+1.56+j*0.32,w:3.82,h:0.3,fontSize:9.5,color:C.text,fontFace:'Calibri',wrap:true}));
    // Gaps
    sl.addText('Identified Gaps:',{x:x+0.12,y:y+2.66,w:3.96,h:0.26,fontSize:10.5,bold:true,color:C.red,fontFace:'Calibri'});
    gaps.forEach((g,j)=>sl.addText(`✗ ${g}`,{x:x+0.18,y:y+2.92+j*0.52,w:3.82,h:0.48,fontSize:9.5,color:C.red,fontFace:'Calibri',wrap:true}));
  });

  // Summary bar
  sl.addShape(pptx.ShapeType.rect,{x:0.28,y:SH-0.83,w:12.75,h:0.5,fill:{color:C.lgray},line:{color:C.navy}});
  sl.addText('Common Thread: All three models lack dynamic cross-modal attention, foundation-model pretraining, and comprehensive cold-start evaluation — directly motivating H-GNN-RNN-DTI.',
    {x:0.42,y:SH-0.82,w:12.48,h:0.48,fontSize:11,bold:true,color:C.navy,fontFace:'Calibri',valign:'middle'});

  sl.addNotes(`TALKING POINTS — BASELINE MODELS

These three models are the most relevant recent works against which my proposed model will be directly compared. They represent the current state of practice and their limitations directly motivate my design choices.

GSRF-DTI (Zhu et al., 2024): This model achieves impressive performance on the Luo_17 network dataset — AUROC of 0.9818. However, it uses DeepWalk for feature extraction followed by simple concatenation before a Random Forest classifier. The authors themselves acknowledge in the paper that future work must address data imbalance and richer embeddings. It has no molecular graph encoding and no interpretability.

TTModel (Li et al., 2024): A knowledge graph embedding approach that integrates textual descriptions and entity type information. It shows strong performance on sparse protein families like GPCRs and nuclear receptors. But it has no direct SMILES graph or amino acid sequence encoding — everything goes through the KG framework, which means it cannot capture fine-grained molecular topology.

DTKGIN (Luo et al., 2024): This is the most sophisticated of the three baselines. It introduces intent nodes in the knowledge graph to capture interaction purposes at varying granularities, and it explicitly evaluates cold-start performance. Cold-drug AUC drops from 0.950 (warm) to 0.894 (S2) and 0.851 (S3). This tells us that even with intent-graph innovations, cold-start generalization remains challenging without pre-trained molecular and protein embeddings.

The bottom banner summarizes the common thread: all three models lack the three things my proposed model will provide — dynamic cross-modal attention, pre-trained foundation model embeddings, and rigorous cold-start benchmarking.`);
  num(sl,9);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 10 — METHODOLOGY OVERVIEW / RESEARCH DESIGN
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Methodology','Research Design: Three-Pillar Framework',C.orange);
  stripe(sl,C.orange);

  // Three pillars
  const pillars=[
    ['Pillar 1','Dynamic Cross-Modal\nFeature Integration','H-GAT drug encoder\n+ BiGRU protein encoder\n+ Gated Cross-Attention Fusion\n→ Objective 1',C.blue],
    ['Pillar 2','Robust Representation\nLearning & Pretraining','ChemBERTa + ESM-2 init\n+ Focal loss + Weighted BCE\n+ Self-supervised pretraining\n→ Objective 2',C.green],
    ['Pillar 3','Attention-Based\nInterpretability','Cross-attention heatmaps\n+ Grad-CAM subgraphs\n+ Biological case studies\n→ Objective 3',C.purple],
  ];

  pillars.forEach(([num,title,body,col],i)=>{
    const x=0.28+i*4.36, y=1.2;
    sl.addShape(pptx.ShapeType.roundRect,{x,y,w:4.2,h:2.6,fill:{color:C.lgray},line:{color:col,pt:2.5},rectRadius:0.12});
    sl.addShape(pptx.ShapeType.rect,{x,y,w:4.2,h:0.46,fill:{color:col},line:{color:col}});
    sl.addText(num,{x:x+0.1,y:y+0.05,w:4.0,h:0.36,fontSize:12,bold:true,color:C.white,fontFace:'Calibri'});
    sl.addText(title,{x:x+0.12,y:y+0.52,w:3.96,h:0.62,fontSize:13,bold:true,color:col,fontFace:'Calibri',wrap:true});
    sl.addText(body,{x:x+0.12,y:y+1.16,w:3.96,h:1.36,fontSize:11,color:C.text,fontFace:'Calibri',valign:'top',wrap:true});
  });

  // Research design flow
  const steps=[
    ['Data\nCollection','7 public DTI/DTA\nbenchmark datasets',C.blue],
    ['Preprocessing','SMILES→Graph\nFASTA→ESM-2\nNeg. sampling',C.teal],
    ['Model Design','H-GNN-RNN-DTI\narchitecture\nimplementation','4A148C'],
    ['Training','Focal loss\nAdam optimizer\n10-fold CV',C.orange],
    ['Evaluation','AUC/AUPR/RMSE\nCold-start S1/S2/S3\nAblation studies',C.green],
    ['Interpretability','Attention maps\nGrad-CAM\nCase studies',C.purple],
  ];

  sl.addText('Research Pipeline:',{x:0.28,y:3.95,w:5,h:0.3,fontSize:12,bold:true,color:C.navy,fontFace:'Calibri'});
  steps.forEach(([t,sub,col],i)=>{
    const x=0.28+i*2.18, y=4.28;
    sl.addShape(pptx.ShapeType.roundRect,{x,y,w:2.05,h:1.62,fill:{color:C.lgray},line:{color:col,pt:1.5},rectRadius:0.08});
    sl.addShape(pptx.ShapeType.rect,{x,y,w:2.05,h:0.34,fill:{color:col},line:{color:col}});
    sl.addText(String(i+1),{x:x+0.04,y:y+0.02,w:0.28,h:0.3,fontSize:11,bold:true,color:C.white,fontFace:'Calibri'});
    sl.addText(t,{x:x+0.34,y:y+0.02,w:1.68,h:0.3,fontSize:11,bold:true,color:C.white,fontFace:'Calibri'});
    sl.addText(sub,{x:x+0.1,y:y+0.4,w:1.86,h:1.14,fontSize:10,color:C.text,fontFace:'Calibri',valign:'top',wrap:true});
    if(i<5) sl.addText('→',{x:x+2.06,y:y+0.6,w:0.11,h:0.42,fontSize:14,color:C.gray,fontFace:'Calibri',align:'center'});
  });

  sl.addText('Implementation: Python 3.10 | PyTorch 2.0+ | PyTorch Geometric | RDKit | HuggingFace Transformers (ESM-2) | Optuna | NVIDIA A100 GPU',
    {x:0.28,y:SH-0.81,w:12.75,h:0.47,fontSize:10,color:C.gray,italic:true,fontFace:'Calibri',valign:'middle'});

  sl.addNotes(`TALKING POINTS — METHODOLOGY OVERVIEW

The research design is organized around three interconnected pillars, each directly addressing one research objective.

Pillar 1 addresses the core architectural innovation: how to integrate drug graph representations and protein sequence representations through a principled dynamic fusion mechanism. This is answered by the Gated Cross-Attention module — which I will detail in a subsequent slide.

Pillar 2 addresses generalization: how to ensure the model performs well on novel drugs and targets it has never seen. The answer involves two strategies: initializing drug and protein encoders with pre-trained language model weights (ChemBERTa and ESM-2 respectively), and using imbalance-aware loss functions that give higher weight to the minority positive class.

Pillar 3 addresses interpretability: the model should not be a black box. The cross-attention weights naturally serve as attribution scores, highlighting which drug atoms attended to which protein residues during prediction. These are visualized as heatmaps and validated against known binding site data.

The bottom panel shows the six-stage research pipeline: from data collection and preprocessing, through model design and training, to evaluation and interpretability analysis. This is the workflow I will follow throughout the PhD.

Implementation details: everything is implemented in Python using PyTorch and PyTorch Geometric for the graph neural network components. RDKit handles molecular graph construction from SMILES. HuggingFace Transformers provides the ESM-2 protein language model. Optuna is used for Bayesian hyperparameter optimization. All computations will be run on NVIDIA A100 GPUs.`);
  num(sl,10);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 11 — DATASETS
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Methodology','Data Collection: Benchmark Datasets',C.orange);
  stripe(sl,C.orange);

  const ds=[
    ['BindingDB','Large-scale','DTI + DTA','Millions of K_d, K_i, IC₅₀ measurements; diverse targets; primary large-scale training source',C.blue],
    ['DAVIS','Medium-scale','DTA Regression','30,056 K_d values; 442 kinases × 68 inhibitors; standard affinity benchmark (CI, RMSE)',C.teal],
    ['KIBA','Medium-scale','DTA Regression','52,498 bioactivity values integrating Ki/Kd/IC₅₀; 467 targets × 229 drugs; CI benchmark',C.green],
    ['Yamanishi_08','Small-scale','DTI Classification','Gold-standard; 4 target classes (Enzyme, Ion Channel, GPCR, NR); cold-start S1/S2/S3 protocol',C.purple],
    ['Luo_17','Large-scale','DTI Classification','1,923 drugs × 3,770 targets; heterogeneous network dataset; used by GSRF-DTI baseline',C.orange],
    ['DrugBank','Supplementary','Feature + Pretrain','Approved/experimental drugs with annotated targets; used for pretraining and generalizability testing',C.red],
    ['ChEMBL','Large-scale','DTI + DTA','~2M compounds; comprehensive bioactivity; supports pretraining and large-scale benchmarking','4A148C'],
  ];

  const hdrs=['Dataset','Scale','Task','Description','Use in Study'];
  const cws=[1.6,1.3,1.4,5.5,2.55];

  // Table header
  let hx=0.28;
  hdrs.forEach((h,i)=>{
    sl.addShape(pptx.ShapeType.rect,{x:hx,y:1.18,w:cws[i],h:0.38,fill:{color:C.navy},line:{color:C.navy}});
    sl.addText(h,{x:hx+0.05,y:1.19,w:cws[i]-0.1,h:0.36,fontSize:11,bold:true,color:C.white,align:'center',fontFace:'Calibri',valign:'middle'});
    hx+=cws[i]+0.04;
  });

  ds.forEach(([name,scale,task,desc,col],i)=>{
    const y=1.6+i*0.68;
    const bg=i%2===0?C.lgray:C.white;
    let dx=0.28;
    [name,scale,task,desc].forEach((cell,ci)=>{
      sl.addShape(pptx.ShapeType.rect,{x:dx,y,w:cws[ci],h:0.64,fill:{color:bg},line:{color:'CFD8DC'}});
      sl.addText(cell,{x:dx+0.05,y:y+0.04,w:cws[ci]-0.1,h:0.56,fontSize:ci===3?9.5:10.5,bold:ci===0,color:ci===0?col:C.text,align:ci===3?'left':'center',fontFace:'Calibri',valign:'middle',wrap:true});
      dx+=cws[ci]+0.04;
    });
    // Use badge
    sl.addShape(pptx.ShapeType.roundRect,{x:dx,y:y+0.1,w:cws[4],h:0.44,fill:{color:col},line:{color:col},rectRadius:0.06});
    sl.addText(task,{x:dx+0.05,y:y+0.1,w:cws[4]-0.1,h:0.44,fontSize:10,bold:true,color:C.white,align:'center',fontFace:'Calibri',valign:'middle'});
  });

  sl.addNotes(`TALKING POINTS — DATASETS

Seven benchmark datasets will be used across different stages of the research.

BindingDB is the primary large-scale training source — it contains millions of experimentally measured binding affinities across a very diverse set of drug-target pairs, making it ideal for training a generalizable model.

DAVIS and KIBA are the standard benchmarks for drug-target affinity regression. DAVIS contains kinase-inhibitor binding affinities measured as K_d values, while KIBA integrates multiple bioactivity measurement types. Both are used extensively in the literature, enabling direct comparison with baseline models.

Yamanishi_08 is particularly important because it defines the standard cold-start evaluation protocol. Its four target classes — enzymes, ion channels, GPCRs, and nuclear receptors — allow us to test whether the model generalizes across biologically distinct protein families. The S1 (warm-start), S2 (cold-drug), and S3 (cold-target) split protocols are the standard way to evaluate cold-start generalization.

Luo_17 is used because it is the dataset on which GSRF-DTI (one of our key baselines) was evaluated — including it ensures our performance comparisons are direct and fair.

DrugBank and ChEMBL provide supplementary data for pretraining the molecular and protein encoders, and for testing cross-dataset transferability.

The combination of these datasets allows us to evaluate the model from multiple angles: large-scale regression, binary classification, cold-start generalization, and cross-dataset transfer.`);
  num(sl,11);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 12 — DATA PREPROCESSING
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Methodology','Data Preprocessing Pipeline',C.orange);
  stripe(sl,C.orange);

  // Drug pipeline
  box(sl,0.28,1.18,6.1,2.55,C.lblue,C.blue,'Drug Representation: SMILES → Molecular Graph',[
    {t:'1. SMILES string validated and standardized using RDKit',sz:10.5},
    {t:'2. Molecular graph G = (V, E) constructed: atoms=nodes, bonds=edges',sz:10.5},
    {t:'3. Node features (12D): atomic number, degree, hybridization, aromaticity, formal charge, ring, chirality',sz:10.5},
    {t:'4. Edge features: bond type (single/double/triple/aromatic), conjugation, ring membership',sz:10.5},
    {t:'5. ChemBERTa embeddings concatenated to node features for richer initialization',sz:10.5},
  ],12,10.5,C.blue,C.text);

  // Protein pipeline
  box(sl,6.5,1.18,6.53,2.55,C.lgreen,C.green,'Protein Representation: FASTA → Contextual Embeddings',[
    {t:'1. FASTA sequences cleaned; non-standard amino acids removed',sz:10.5},
    {t:'2. Tokenized at residue level (20 amino acids + special tokens)',sz:10.5},
    {t:'3. ESM-2 (650M parameters) generates residue-level contextual embeddings',sz:10.5},
    {t:'4. Sequences padded/truncated to max length 1,200 residues for batch processing',sz:10.5},
    {t:'5. Attention mask applied to ignore padding tokens in RNN/pooling layers',sz:10.5},
  ],12,10.5,C.green,C.text);

  // Label processing
  box(sl,0.28,3.86,6.1,2.36,C.lgold,C.gold,'Label Processing & Negative Sampling',[
    {t:'Binary: positive=1 (known DTI); negative=0 via unknown-negative sampling (1:1 and 1:10 ratios)',sz:10.5},
    {t:'Regression: raw affinity values log-transformed → pKd = -log₁₀(Kd); standardized for stability',sz:10.5},
    {t:'Focal loss γ=2.0 and weighted BCE applied to address class imbalance',sz:10.5},
    {t:'Stratified sampling preserves interaction ratio across train/val/test splits',sz:10.5},
  ],12,10.5,C.gold,C.text);

  // Data splits
  box(sl,6.5,3.86,6.53,2.36,C.lpurp,C.purple,'Data Splitting Protocols',[
    {t:'S1 Warm-Start: random 10-fold CV — both drugs and targets seen in training',sz:10.5},
    {t:'S2 Cold-Drug: drug-disjoint split — test compounds never seen during training',sz:10.5},
    {t:'S3 Cold-Target: target-disjoint split — test proteins never seen during training',sz:10.5},
    {t:'Cross-Dataset: train on BindingDB, test on DAVIS — evaluates transferability',sz:10.5},
    {t:'Ablation: each component removed in turn to measure its individual contribution',sz:10.5},
  ],12,10.5,C.purple,C.text);

  sl.addNotes(`TALKING POINTS — DATA PREPROCESSING

Let me walk through the preprocessing pipeline for both modalities and the label handling strategy.

For drug molecules: We start from SMILES strings, which are standardized using RDKit to handle tautomers, salts, and representation ambiguities. RDKit then constructs the molecular graph. Each atom becomes a node with a 12-dimensional feature vector capturing chemistry: atomic number, valence, hybridization state, aromaticity, formal charge, ring membership, and chirality. Bonds become edges with features encoding bond type and ring membership. Crucially, we also initialize node features with ChemBERTa embeddings — a BERT-style model pre-trained on 77 million SMILES strings — which gives the graph encoder a head start with rich chemical semantics.

For proteins: FASTA sequences are tokenized at the residue level and processed through ESM-2, a 650-million parameter protein language model pre-trained on 250 million protein sequences. This produces a contextualized embedding for each amino acid that captures both local sequence patterns and long-range evolutionary information. Sequences are padded or truncated to 1,200 residues to enable efficient batch processing.

For labels: In binary classification, positive labels are confirmed from DTI databases; negatives are generated by unknown-negative sampling — we treat drug-target pairs with no confirmed interaction as negatives, using 1:1 and 1:10 ratios. For regression, affinity values are log-transformed to pKd = -log₁₀(Kd) to stabilize the distribution.

The splitting protocols define four evaluation scenarios — warm-start, cold-drug, cold-target, and cross-dataset — which together comprehensively test generalization capability.`);
  num(sl,12);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 13 — H-GNN-RNN-DTI ARCHITECTURE
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Methodology','H-GNN-RNN-DTI: Proposed Architecture',C.orange);
  stripe(sl,C.orange);
  img(sl,'fig3_architecture.png',0.28,1.12,8.45,5.62);

  // Right annotation panel
  box(sl,8.85,1.12,4.18,1.68,C.lblue,C.blue,'Drug Branch (H-GAT)',[
    {t:'3-layer Hierarchical Graph Attention Network',sz:10.5},
    {t:'8 attention heads per layer',sz:10.5},
    {t:'ChemBERTa node feature initialization',sz:10.5},
    {t:'Attention-weighted global graph readout',sz:10.5},
  ],11,10,C.blue,C.text);

  box(sl,8.85,2.88,4.18,1.68,C.lgreen,C.green,'Protein Branch (BiGRU)',[
    {t:'2-layer Bidirectional LSTM or GRU',sz:10.5},
    {t:'ESM-2 residue embedding initialization',sz:10.5},
    {t:'Attention-based sequence pooling',sz:10.5},
    {t:'Captures both fwd/bwd sequence context',sz:10.5},
  ],11,10,C.green,C.text);

  box(sl,8.85,4.64,4.18,1.12,'FFF3E0',C.orange,'Gated Cross-Attention [NOVEL]',[
    {t:'Bidirectional drug↔protein attention',sz:10.5},
    {t:'Adaptive gates G_d, G_p ∈ (0,1)^d',sz:10.5},
    {t:'Prevents information loss from either modality',sz:10.5},
  ],11,10,C.orange,C.text);

  box(sl,8.85,5.84,4.18,0.9,C.lpurp,C.purple,'Prediction Head',[
    {t:'MLP + Dropout → Sigmoid (class.) or Linear (regression)',sz:10.5},
  ],11,10,C.purple,C.text);

  sl.addNotes(`TALKING POINTS — PROPOSED ARCHITECTURE

This diagram shows the full H-GNN-RNN-DTI architecture. Let me walk through it from top to bottom.

The DRUG BRANCH (left, blue) takes a molecular graph as input. After node feature initialization with ChemBERTa embeddings, three layers of the Hierarchical Graph Attention Network (H-GAT) perform message passing with 8 attention heads per layer. This allows each atom to selectively attend to its most chemically relevant neighbors, learning atom-level representations that capture molecular topology and functional groups. An attention-weighted readout then produces the global drug embedding z_d.

The PROTEIN BRANCH (right, green) takes the ESM-2-initialized amino acid sequence and processes it through 2 layers of Bidirectional LSTM or GRU. The bidirectionality is important — each residue's representation incorporates context from both the residues before it and after it in the sequence. Attention-based pooling then selects the most informative residues to form the protein embedding z_p.

The GATED CROSS-ATTENTION FUSION MODULE (centre, orange) is the key innovation. Rather than simply concatenating z_d and z_p, we compute bidirectional attention: drug atom embeddings attend to protein residue embeddings (A_{d→p}) and protein residue embeddings attend to drug atom embeddings (A_{p→d}). A learned gate G_d then adaptively mixes the cross-modal information with the original drug representation — preserving important modality-specific features while enabling deep cross-modal interaction.

The PREDICTION HEAD (purple, bottom) maps the fused representation through a multi-layer perceptron to the final output — a sigmoid for binary DTI classification or a linear activation for continuous affinity regression.

This unified design handles both classification and regression within a single architecture.`);
  num(sl,13);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 14 — GATED CROSS-ATTENTION (DETAIL)
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Methodology','Gated Cross-Attention Fusion: The Core Innovation',C.orange);
  stripe(sl,C.orange);
  img(sl,'fig8_crossattn.png',0.28,1.12,7.15,4.55);

  // Equations panel
  box(sl,7.55,1.12,5.5,4.56,'FFF3E0',C.orange,'Key Mathematical Formulations',[
    {t:'Cross-Attention (Drug → Protein):',b:true,sz:11},
    {t:'A_d→p = softmax(Q_d K_p^T / √d_k) · V_p',sz:10.5},
    {t:'Cross-Attention (Protein → Drug):',b:true,sz:11},
    {t:'A_p→d = softmax(Q_p K_d^T / √d_k) · V_d',sz:10.5},
    {t:'Drug Gate (prevents info loss):',b:true,sz:11},
    {t:'G_d = σ(W_g [h_d ∥ A_d→p] + b_g)',sz:10.5},
    {t:'Gated Drug Representation:',b:true,sz:11},
    {t:"h_d' = G_d ⊙ A_d→p + (1 - G_d) ⊙ h_d",sz:10.5},
    {t:'(Symmetric equations for protein branch)',sz:10,b:false},
    {t:'Fused Output:',b:true,sz:11},
    {t:'h_fused = σ(W_f [z_d ∥ z_p] + b_f)',sz:10.5},
  ],11,10.5,C.orange,C.text);

  // Why better than concatenation
  box(sl,0.28,5.78,12.77,0.94,C.lgray,C.navy,'Why Gated Cross-Attention Outperforms Simple Concatenation',[
    {t:'Concatenation [h_d; h_p]: treats drug and protein as independent — no direct drug-protein interaction modeled at the feature level',sz:10.5},
    {t:'Gated Cross-Attention: drug atoms dynamically attend to relevant protein residues and vice versa — models the physical binding relationship at the representation level',sz:10.5,b:true},
  ],12,10.5,C.navy,C.text);

  sl.addNotes(`TALKING POINTS — GATED CROSS-ATTENTION

This is the single most important technical contribution of the proposed work, so I want to explain it carefully.

The fundamental problem with concatenation-based fusion is that it treats the drug and protein representations as independent vectors and simply glues them together. The model then has to learn from scratch that certain drug features are related to certain protein features — but there is no direct pathway for this cross-modal interaction to happen at the feature level.

Cross-attention solves this by computing Query-Key-Value attention across modalities. The drug atom embeddings (h_d) act as queries, the protein residue embeddings (h_p) act as keys and values. Each drug atom can then attend to and aggregate information from the protein residues that are most relevant to it — and vice versa. This directly models the physical binding relationship: specific drug functional groups interact with specific protein residues at the binding site.

The gating mechanism is a refinement: the gate G_d is a learned sigmoid function that decides, for each dimension of the embedding, how much of the cross-modal information (A_{d→p}) to incorporate versus how much of the original drug representation (h_d) to preserve. This prevents the cross-attention from completely overwriting useful drug-specific features that don't have a direct protein counterpart.

The formula at the bottom shows the gated update: the new drug representation h_d' is a weighted interpolation between the cross-attended representation and the original, controlled by the gate G_d.

A key question the supervisor might ask: Is this similar to co-attention? Yes, it is related to co-attention mechanisms, but the gating component is the key difference — it explicitly controls information flow to prevent over-emphasis on cross-modal information at the expense of modality-specific features.`);
  num(sl,14);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 15 — TRAINING STRATEGY
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Methodology','Training Strategy: Imbalance-Aware Learning',C.orange);
  stripe(sl,C.orange);

  box(sl,0.28,1.18,4.15,3.0,C.lred,C.red,'Loss Functions for Class Imbalance',[
    {t:'Focal Loss (Classification):',b:true,sz:11.5},
    {t:'FL(p_t) = -α_t (1 - p_t)^γ log(p_t)',sz:11},
    {t:'γ=2.0 down-weights easy examples; focuses learning on hard misclassifications',sz:10.5},
    {t:'α_t balances positive/negative class frequency',sz:10.5},
    {t:'Weighted BCE (alternative):',b:true,sz:11.5},
    {t:'L = -(w₊·y·log(p) + w₋·(1-y)·log(1-p))',sz:11},
    {t:'MSE (Regression):',b:true,sz:11.5},
    {t:'L = (1/N) Σ (ŷᵢ - yᵢ)²',sz:11},
  ],12,10.5,C.red,C.text);

  box(sl,4.55,1.18,4.15,3.0,C.lgold,C.gold,'Optimization & Regularization',[
    {t:'Optimizer: Adam with decoupled weight decay (AdamW)',sz:11},
    {t:'Learning rate scheduling: cosine annealing with warmup',sz:11},
    {t:'Dropout: applied in MLP prediction head and between RNN layers',sz:11},
    {t:'Residual connections: in GNN layers to prevent over-smoothing',sz:11},
    {t:'Early stopping: based on validation AUPR (5-epoch patience)',sz:11},
    {t:'Gradient clipping: max norm 1.0 to prevent exploding gradients',sz:11},
  ],12,10.5,C.gold,C.text);

  box(sl,8.82,1.18,4.21,3.0,C.lgreen,C.green,'Self-Supervised Pretraining',[
    {t:'Phase 1 — Pretraining:',b:true,sz:11.5},
    {t:'Drug/protein encoders pretrained on large unlabeled corpora (DrugBank, UniProt) using contrastive learning and masked feature prediction',sz:10.5},
    {t:'Phase 2 — Fine-tuning:',b:true,sz:11.5},
    {t:'Pretrained encoders fine-tuned end-to-end on labeled DTI datasets with the full H-GNN-RNN-DTI architecture and task-specific loss',sz:10.5},
    {t:'Benefit: significantly reduces cold-start degradation by encoding transferable biochemical knowledge',sz:10.5},
  ],12,10.5,C.green,C.text);

  // Experimental protocol
  box(sl,0.28,4.32,12.75,1.88,C.lpurp,C.purple,'Experimental & Ablation Protocol',[
    {t:'10-fold cross-validation with stratified splits; hold-out test set for final reporting',sz:11},
    {t:'Ablation studies: GNN-only, RNN-only, concatenation fusion, gated fusion — to isolate contribution of each component',sz:11},
    {t:'Hyperparameter optimization: Bayesian search (Optuna) over LR, dropout, hidden dim, attention heads, GNN layers',sz:11},
    {t:'Statistical reporting: mean ± std over 5 random seeds; paired Wilcoxon significance test vs. baselines',sz:11},
  ],12,10.5,C.purple,C.text);

  sl.addNotes(`TALKING POINTS — TRAINING STRATEGY

The training strategy has three key elements that directly address the identified research gaps.

First, loss functions for imbalance. Standard binary cross-entropy assigns equal weight to every training example. In DTI datasets where positives are rare, this leads the model to achieve high accuracy simply by predicting "no interaction" almost always. Focal loss adds a modulating factor (1-p_t)^gamma that down-weights easy, correctly classified examples and concentrates the gradient signal on the hard misclassifications — the cases where the model is uncertain or wrong. With gamma=2.0, examples the model is confident about receive very little gradient signal, forcing it to focus on the difficult boundary cases.

Second, optimization. We use AdamW — Adam with decoupled weight decay — which is the current best-practice optimizer for deep learning. Learning rate scheduling with cosine annealing and warmup prevents the learning rate from being too large early in training when gradients are noisy. Dropout and gradient clipping prevent overfitting and training instability.

Third, self-supervised pretraining. Before training on labeled DTI data, the drug and protein encoders are pretrained on millions of unlabeled molecular and protein sequences using contrastive learning. This gives the encoders a rich initialization that captures general biochemical principles — similar to how BERT pretraining on Wikipedia gives downstream NLP models a head start. When we then fine-tune on DTI-specific tasks, the pretrained features enable much better generalization to novel drugs and targets.

The ablation study design is critical for the scientific contribution: by systematically removing each component (GNN-only, RNN-only, concatenation fusion, gated fusion), we can quantify exactly how much each architectural choice contributes to performance.`);
  num(sl,15);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 16 — EVALUATION PROTOCOL
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Methodology','Evaluation Protocol: Metrics & Cold-Start Testing',C.orange);
  stripe(sl,C.orange);

  // Metrics
  box(sl,0.28,1.18,5.95,2.55,C.lblue,C.blue,'Classification Metrics (DTI)',[
    {t:'AUC-ROC: Area under ROC curve — threshold-independent overall discrimination',sz:11},
    {t:'AUPR: Area under Precision-Recall curve — preferred for imbalanced data; sensitive to minority class performance',sz:11,b:false},
    {t:'F1 Score: harmonic mean of precision and recall at optimal threshold',sz:11},
    {t:'Formula: AUPR = ∫ Precision(Recall) d(Recall)',sz:11},
  ],12,10.5,C.blue,C.text);

  box(sl,6.35,1.18,6.68,2.55,'FFF3E0',C.orange,'Regression Metrics (DTA)',[
    {t:'RMSE = √[(1/N) Σ(ŷᵢ - yᵢ)²] — penalizes large errors more severely',sz:11},
    {t:'MAE = (1/N) Σ|ŷᵢ - yᵢ| — robust to outliers; interpretable in affinity units',sz:11},
    {t:'CI (Concordance Index): measures ranking accuracy of predicted affinities among all valid pairs',sz:11},
    {t:'PCC: Pearson Correlation Coefficient — linear correlation between predicted and experimental values',sz:11},
  ],12,10.5,C.orange,C.text);

  // Cold-start table
  sl.addText('Cold-Start Evaluation Settings:',{x:0.28,y:3.86,w:6,h:0.3,fontSize:13,bold:true,color:C.navy,fontFace:'Calibri'});
  const cs=[
    ['S1 — Warm-Start','Random split; drugs & targets in test set were seen in training','Baseline performance; enables comparison with literature',C.green],
    ['S2 — Cold-Drug','Drug-disjoint split; all test compounds are NOVEL','Tests generalization to new chemical scaffolds',C.blue],
    ['S3 — Cold-Target','Target-disjoint split; all test proteins are NOVEL','Tests generalization to unexplored protein targets',C.purple],
    ['Cross-Dataset','Train on BindingDB, test on DAVIS/KIBA','Tests domain transferability across experimental protocols',C.orange],
  ];
  cs.forEach(([setting,desc,purpose,col],i)=>{
    const y=4.2+i*0.68;
    sl.addShape(pptx.ShapeType.roundRect,{x:0.28,y,w:12.75,h:0.62,fill:{color:i%2===0?C.lgray:C.white},line:{color:col,pt:1.5},rectRadius:0.06});
    sl.addShape(pptx.ShapeType.rect,{x:0.28,y,w:2.45,h:0.62,fill:{color:col},line:{color:col}});
    sl.addText(setting,{x:0.34,y:y+0.12,w:2.33,h:0.38,fontSize:11,bold:true,color:C.white,fontFace:'Calibri',valign:'middle'});
    sl.addText(desc,{x:2.82,y:y+0.06,w:5.55,h:0.5,fontSize:10.5,color:C.text,fontFace:'Calibri',valign:'middle',wrap:true});
    sl.addText(purpose,{x:8.45,y:y+0.06,w:4.5,h:0.5,fontSize:10.5,color:col,bold:true,fontFace:'Calibri',valign:'middle',wrap:true});
  });

  sl.addNotes(`TALKING POINTS — EVALUATION PROTOCOL

The evaluation framework is designed to be comprehensive and avoid the over-optimistic results that simple random-split evaluation can produce.

For classification tasks, we use both AUC-ROC and AUPR. AUC-ROC is the standard metric, but for imbalanced DTI datasets where negatives vastly outnumber positives, AUPR is a better indicator of practical performance — it measures how precisely the model identifies true positives across different recall thresholds.

For regression tasks, RMSE penalizes large errors more than MAE, making it useful for detecting cases where the model is dramatically wrong. The Concordance Index is particularly important because, in practice, what matters is correctly ranking compounds by their binding affinity — even if the absolute values aren't perfect. PCC measures linear correlation between predicted and experimental values.

The cold-start evaluation settings are the heart of the generalization assessment. In S1 warm-start, the model has seen both the drugs and proteins during training — this is the easiest setting and corresponds to most published benchmarks. In S2 cold-drug, the test compounds are entirely novel — the model must generalize based on structural properties alone. In S3 cold-target, the test proteins are entirely novel — the model must generalize based on the protein sequence properties it has learned.

The cross-dataset experiment is the most stringent test: train on BindingDB and test directly on DAVIS without any fine-tuning. This evaluates whether the model has learned truly transferable representations or has merely overfit to the training distribution.

This four-scenario evaluation design gives us a complete picture of the model's real-world utility.`);
  num(sl,16);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 17 — INTERPRETABILITY
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Methodology','Interpretability & Explainability Framework',C.orange);
  stripe(sl,C.orange);

  box(sl,0.28,1.18,4.15,5.45,C.lpurp,C.purple,'Attention-Based Attribution',[
    {t:'The Gated Cross-Attention weight matrix A_{d→p} ∈ ℝ^(n×m) directly encodes the contribution of each drug atom to each protein residue',sz:10.5},
    {t:'Atom importance score: α_v = Σⱼ A_v,j (summed over protein positions)',sz:10.5},
    {t:'Residue importance score: α_r = Σᵢ A_i,r (summed over drug atoms)',sz:10.5},
    {t:'High-weight atom-residue pairs indicate predicted binding contacts',sz:10.5},
    {t:'Intrinsic XAI: interpretability is built into the architecture, not added post-hoc',sz:10.5},
  ],12,10.5,C.purple,C.text);

  box(sl,4.55,1.18,4.15,5.45,C.lgold,C.gold,'Grad-CAM Visualization',[
    {t:'Gradient-weighted Class Activation Mapping adapted for molecular graphs',sz:10.5},
    {t:'Identifies drug substructures (rings, functional groups) most responsible for interaction prediction',sz:10.5},
    {t:'Highlights protein sequence regions (binding motifs, active site residues) most responsible for binding',sz:10.5},
    {t:'Visualized as: (1) atom-colored molecular graphs, (2) sequence heatmaps overlaid on FASTA',sz:10.5},
    {t:'Provides chemical and biological rationale for each prediction',sz:10.5},
  ],12,10.5,C.gold,C.text);

  box(sl,8.82,1.18,4.21,5.45,C.lgreen,C.green,'Biological Validation',[
    {t:'Case studies on well-characterized drug-target complexes with known crystal structures',sz:10.5},
    {t:'Compare model-predicted binding hotspots against experimentally determined binding contacts from PDB crystal structures',sz:10.5},
    {t:'Quantitative metric: % overlap between top-ranked atoms/residues and known binding site residues within 4Å cutoff',sz:10.5},
    {t:'Target: >75% overlap on PDB validation set (IHDFN-DTI achieves >80%)',sz:10.5},
    {t:'Results directly support structure-activity relationship (SAR) analysis for drug optimization',sz:10.5},
  ],12,10.5,C.green,C.text);

  sl.addNotes(`TALKING POINTS — INTERPRETABILITY

Interpretability is one of the three core objectives of this research, and arguably the one with the most direct translational value for drug discovery.

The attention-based attribution is the primary interpretability mechanism. When the cross-attention module computes A_{d→p}, it produces a matrix where entry (i,j) represents how much drug atom i attended to protein residue j during the prediction. We aggregate these scores to get atom-level drug importance and residue-level protein importance. Crucially, this interpretability is intrinsic — it comes from the architecture itself, not from a separate post-hoc explanation method like LIME or SHAP. This means the explanations are directly connected to the model's actual decision-making process.

Grad-CAM is a complementary technique originally developed for convolutional neural networks but adapted here for molecular graphs. It computes gradients of the prediction with respect to intermediate node embeddings to identify which molecular substructures and protein regions most influence the output. This is particularly useful for highlighting ring systems, functional groups, and protein binding motifs.

The biological validation step is what distinguishes rigorous interpretability from superficial attention visualization. We take well-characterized drug-target complexes — where the 3D crystal structure is known from the Protein Data Bank — and check whether our model's predicted binding atoms/residues overlap with the actual atomic contacts observed in the crystal structure. This provides a quantitative ground truth for evaluating whether the model's explanations are biologically meaningful.

The practical implication for drug discovery: a medicinal chemist working on lead optimization can look at the attention heatmap and directly see which functional group on the drug molecule is predicted to be interacting with which specific residue on the protein. This guides rational structural modifications to improve potency or selectivity.`);
  num(sl,17);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 18 — TIMELINE & MILESTONES
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Timeline & Milestones','3-Year PhD Research Plan','5D4037');
  stripe(sl,'5D4037');

  // Year labels
  const years=['Year 1 (2025/2026)','Year 2 (2026/2027)','Year 3 (2027/2028)'];
  const ycols=[C.blue,C.green,C.purple];
  years.forEach((y,i)=>{
    const x=0.28+i*4.36;
    sl.addShape(pptx.ShapeType.rect,{x,y:1.18,w:4.2,h:0.38,fill:{color:ycols[i]},line:{color:ycols[i]}});
    sl.addText(y,{x:x+0.05,y:1.19,w:4.1,h:0.36,fontSize:12,bold:true,color:C.white,align:'center',fontFace:'Calibri',valign:'middle'});
  });

  // Gantt rows
  const tasks=[
    ['Literature Review & Proposal','1','2','','','','','',C.blue],
    ['Dataset Collection & Preprocessing','','2','3','','','','',C.teal],
    ['Model Design (Architecture)','','','3','4','','','','4A148C'],
    ['Baseline Implementation & Comparison','','','','4','5','','',C.orange],
    ['Core Model Training & Evaluation','','','','','5','6','',C.red],
    ['Cold-Start & Ablation Studies','','','','','','6','7',C.green],
    ['Interpretability Module Development','','','','','5','6','',C.purple],
    ['Journal Publication (Review Paper)','','2','3','','','','','778899'],
    ['Conference Paper (Arch. Contribution)','','','','4','5','','',C.gold],
    ['Journal Paper (Main Results)','','','','','','6','7',C.red],
    ['Thesis Writing & Submission','','','','','','6','7','5D4037'],
  ];

  const semLabels=['S1','S2','S1','S2','S1','S2'];
  semLabels.forEach((s,i)=>{
    const x=0.28+Math.floor(i/2)*4.36+(i%2)*2.1;
    sl.addText(s,{x:x+0.05,y:1.58,w:2.02,h:0.28,fontSize:9,bold:true,color:C.gray,align:'center',fontFace:'Calibri'});
    sl.addShape(pptx.ShapeType.rect,{x:x+0.04,y:1.84,w:2.02,h:0.02,fill:{color:'CFD8DC'},line:{color:'CFD8DC'}});
  });

  tasks.forEach(([task,...sems],i)=>{
    const col=sems.pop();
    const y=1.9+i*0.48;
    sl.addText(task,{x:0.28,y:y+0.04,w:12.75,h:0.42,fontSize:9,color:C.gray,fontFace:'Calibri'});
    sems.forEach((active,si)=>{
      if(active){
        const x=0.28+Math.floor(si/2)*4.36+(si%2)*2.1;
        sl.addShape(pptx.ShapeType.roundRect,{x:x+0.06,y:y+0.05,w:1.95,h:0.36,fill:{color:col},line:{color:col},rectRadius:0.06});
      }
    });
    // Task label on first active cell
    const firstActive=sems.findIndex(s=>s);
    if(firstActive>=0){
      const x=0.28+Math.floor(firstActive/2)*4.36+(firstActive%2)*2.1;
      sl.addText(task,{x:x+0.1,y:y+0.08,w:12.0,h:0.28,fontSize:8.5,bold:true,color:C.white,fontFace:'Calibri'});
    }
  });

  // Key milestones
  const ms=[['M1: Proposal Defence','Y1S1'],['M2: Review Paper Submitted','Y1S2'],['M3: Architecture Implemented','Y2S1'],['M4: Conference Paper','Y2S2'],['M5: Full Results','Y3S1'],['M6: Thesis Submitted','Y3S2']];
  ms.forEach(([m,t],i)=>{
    sl.addText(`◆ ${m} (${t})`,{x:0.38+i*2.18,y:SH-0.86,w:2.1,h:0.32,fontSize:8.5,color:C.navy,bold:true,fontFace:'Calibri',wrap:true});
  });

  sl.addNotes(`TALKING POINTS — TIMELINE & MILESTONES

The research is organized across three years with six semesters, each with specific deliverables.

Year 1 Semester 1 (current): Literature review completion, proposal writing, and this defence. The literature review has resulted in a comprehensive review paper covering 36 models, which will be submitted for publication.

Year 1 Semester 2: Dataset collection, preprocessing pipeline development, and baseline model implementation. This phase establishes the fair comparison benchmarks against GSRF-DTI, TTModel, and DTKGIN.

Year 2 Semester 1: Core H-GNN-RNN-DTI architecture design, implementation, and initial training. The drug encoder (H-GAT) and protein encoder (BiGRU) are developed and tested independently before integration.

Year 2 Semester 2: Full model integration with Gated Cross-Attention, baseline comparison, and ablation studies. A conference paper presenting the architectural contribution will be prepared for submission to a venue such as IJCAI, AAAI, or BIBM.

Year 3 Semester 1: Cold-start evaluation, interpretability module development and validation, and comprehensive experimental analysis.

Year 3 Semester 2: Final experiments, thesis writing, and submission of the main journal paper to Briefings in Bioinformatics or similar Q1 venue.

The six key milestones are: M1 proposal defence (now), M2 review paper submission, M3 architecture implementation, M4 conference paper, M5 full experimental results, and M6 thesis submission.

Supervisor may ask about contingency plans: if model performance is lower than expected in Year 2, I will extend the architecture exploration phase and potentially reduce the scope of cold-start experiments. The core contribution (gated cross-attention) is the primary risk point and will be addressed early.`);
  num(sl,18);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 19 — EXPECTED OUTCOMES
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'Expected Outcomes & Contributions','Four Key Deliverables from This Research',C.green);
  stripe(sl,C.green);

  const outcomes=[
    ['O1','Advanced Hybrid\nArchitecture',
     'A robust H-GNN-RNN-DTI model capable of capturing molecular graph structure (H-GAT) and protein sequential dependencies (BiGRU/BiLSTM) through a novel Gated Cross-Attention fusion mechanism, achieving statistically significant improvements over GSRF-DTI, TTModel, DTKGIN, and single-modality baselines.',
     C.blue,C.lblue],
    ['O2','Improved Predictive\nPerformance & Generalization',
     'Statistically significant improvements in AUC-ROC, AUPR (classification) and RMSE, CI (regression) validated through rigorous benchmarking across 7 datasets. Cold-start performance (S2/S3) improved over DTKGIN through foundation-model pretraining and imbalance-aware training.',
     C.green,C.lgreen],
    ['O3','Interpretable DTI\nFramework',
     'An intrinsically interpretable computational framework providing attention heatmaps and Grad-CAM subgraph visualizations that identify binding pharmacophores and key residues. Validated quantitatively against PDB crystal structures (target: >75% binding site overlap).',
     C.purple,C.lpurp],
    ['O4','Reproducible Research\nOutput',
     'Fully reproducible implementation with publicly available source code, trained model weights, preprocessing pipelines, and experimental configurations on GitHub. Enables transparency, replicability, and future extension by the DTI research community.',
     C.orange,'FFF3E0'],
  ];

  outcomes.forEach(([num,title,desc,col,light],i)=>{
    const r=Math.floor(i/2), c=i%2;
    const x=0.28+c*6.54, y=1.18+r*2.68;
    sl.addShape(pptx.ShapeType.roundRect,{x,y,w:6.34,h:2.54,fill:{color:light},line:{color:col,pt:2},rectRadius:0.1});
    sl.addShape(pptx.ShapeType.rect,{x,y,w:0.54,h:2.54,fill:{color:col},line:{color:col}});
    sl.addText(num,{x:x+0.02,y:y+1.0,w:0.5,h:0.54,fontSize:18,bold:true,color:C.white,align:'center',fontFace:'Calibri'});
    sl.addText(title,{x:x+0.65,y:y+0.1,w:5.58,h:0.6,fontSize:13.5,bold:true,color:col,fontFace:'Calibri',valign:'middle',wrap:true});
    sl.addText(desc,{x:x+0.65,y:y+0.74,w:5.58,h:1.72,fontSize:10.5,color:C.text,fontFace:'Calibri',valign:'top',wrap:true});
  });

  // Publication targets
  sl.addShape(pptx.ShapeType.rect,{x:0.28,y:SH-0.82,w:12.75,h:0.5,fill:{color:C.lgray},line:{color:C.navy}});
  sl.addText('Target Venues: Briefings in Bioinformatics (Q1) | Bioinformatics (Q1) | IEEE BIBM | AAAI/IJCAI | BMC Bioinformatics | Journal of Chemical Information and Modeling',
    {x:0.42,y:SH-0.8,w:12.48,h:0.46,fontSize:10,color:C.navy,fontFace:'Calibri',valign:'middle',bold:false,italic:true});

  sl.addNotes(`TALKING POINTS — EXPECTED OUTCOMES

This slide summarizes the four principal contributions this research will produce.

Outcome 1 — The Architecture: The H-GNN-RNN-DTI model itself is the primary technical contribution. The Gated Cross-Attention mechanism is novel in the DTI domain and represents an advancement over both the static concatenation approaches in GSRF-DTI and TTModel, and the intent-graph approach in DTKGIN. We expect statistically significant improvements in AUC and AUPR on all benchmark datasets.

Outcome 2 — Improved Performance with Generalization: Beyond raw performance numbers, the key claim is improved cold-start generalization. By combining pre-trained foundation model embeddings with the gated fusion architecture and imbalance-aware training, we expect to substantially reduce the performance gap between warm-start and cold-start settings — making the model more practically useful for real drug discovery applications.

Outcome 3 — Interpretability: The attention-based XAI framework transforms the model from a black-box predictor into a hypothesis-generating tool that chemists can actually use. The biological validation against PDB crystal structures will provide the rigorous evidence needed to claim interpretability is meaningful rather than superficial.

Outcome 4 — Reproducibility: All code, trained models, and experimental protocols will be released on GitHub under an open-source license. This follows the increasing emphasis on reproducibility in computational biology and allows other researchers to build on this work.

For publication, I am targeting Q1 journals in bioinformatics — specifically Briefings in Bioinformatics and Bioinformatics — for the main results paper, with conference papers at IEEE BIBM or AAAI for early architectural results.`);
  num(sl,19);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 20 — REFERENCES
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  hdr(sl,'References','Key Citations Supporting This Research Proposal',C.navy);
  stripe(sl);

  const refs=[
    'Zhu, Y. et al. (2024). GSRF-DTI: DTI prediction via drug-target pair network and representation learning. BMC Biology, 22(1). [Baseline 1]',
    'Li, N. et al. (2024). Drug–target interaction prediction using knowledge graph embedding. iScience, 27(6). [Baseline 2]',
    'Luo, Y. et al. (2024). DTKGIN: Predicting DTI based on knowledge graph and intent graph. Methods, 226, 21–27. [Baseline 3]',
    'Nguyen, T. et al. (2021). GraphDTA: Predicting drug target binding affinity with graph neural networks. Bioinformatics, 37(8).',
    'Sun, Y. et al. (2024). iNGNN-DTI: Prediction with interpretable nested GNN and pretrained molecule models. Bioinformatics, 40(3).',
    'Talo, M. & Bozdag, S. (2025). Top-DTI: Integrating topological deep learning and LLMs for DTI prediction. Bioinformatics, 41.',
    'Yuan, Y. et al. (2025). MutualDTA: Interpretable DTA prediction leveraging pretrained models and mutual attention. J. Chem. Inf. Model., 65(3).',
    'Vefghi, A. et al. (2025). Drug-target interaction/affinity prediction: Deep learning models review. Computers in Biology & Medicine, 196.',
    'Panahandeh, F. & Mansouri, N. (2025). A comprehensive review of neural network-based approaches for DTI prediction. Molecular Diversity.',
    'Ouyang, X. et al. (2025). Improving generalizability of drug–target binding prediction by pre-trained multi-view representations. Bioinformatics.',
    'Hua, Y. et al. (2025). MMDG-DTI: DTI prediction via multimodal feature fusion and domain generalization. Pattern Recognition, 157.',
    'Tanoli, Z. et al. (2025). Validation guidelines for drug-target prediction methods. Expert Opinion on Drug Discovery, 20(1).',
    'Tran, H.N.T., Thomas, J.J., & Malim, N.H.A.H. (2022). DeepNC: Drug-target interaction prediction with graph neural networks. PeerJ, 10.',
    'Khan, A.K. & Ahamed Hassain Malim, N.H. (2023). Comparative studies on resampling techniques in ML and DL for DTI. Molecules, 28(4).',
  ];

  refs.forEach((r,i)=>{
    const x=0.28+Math.floor(i/7)*6.54;
    const y=1.2+(i%7)*0.82;
    sl.addText(`${i+1}. ${r}`,{x,y,w:6.3,h:0.74,fontSize:9.5,color:C.text,fontFace:'Calibri',valign:'top',wrap:true});
  });

  sl.addNotes(`TALKING POINTS — REFERENCES

This slide lists the 14 most critical references for this proposal. Let me highlight a few that are particularly important.

References 1, 2, and 3 are the three baseline models — GSRF-DTI, TTModel, and DTKGIN — that directly motivate this research. They represent the current state of the art that we aim to improve upon.

Reference 4 (GraphDTA) established the use of graph neural networks for drug molecular encoding and is the foundation for our H-GAT drug encoder design.

Reference 5 (iNGNN-DTI) is the most architecturally similar work to ours — it uses nested GNNs with cross-attention and pretrained embeddings. Our work extends this by adding explicit gating and bidirectional cross-attention.

Reference 6 (Top-DTI) demonstrates that foundation model embeddings significantly improve cold-start performance — validating our strategy of using ChemBERTa and ESM-2.

Reference 13 (DeepNC by Tran, Thomas, and our supervisor Assoc. Prof. Nurul Hashimah) is directly relevant as it represents prior work from our research group on graph neural network approaches to DTI prediction.

Reference 14 (Khan and Assoc. Prof. Nurul Hashimah, 2023) is also from our group, investigating resampling strategies for class imbalance in DTI — directly informing our choice of focal loss and weighted BCE.

The full reference list for the comprehensive review paper contains 55 references, available in the accompanying review paper document.`);
  num(sl,20);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 21 — CLOSING / Q&A
// ════════════════════════════════════════════════════════════════════════════
{
  const sl=pptx.addSlide();
  sl.addShape(pptx.ShapeType.rect,{x:0,y:0,w:SW,h:SH,fill:{color:C.navy},line:{color:C.navy}});
  sl.addShape(pptx.ShapeType.rect,{x:0,y:0,w:SW,h:2.0,fill:{color:C.dblue},line:{color:C.dblue}});
  sl.addShape(pptx.ShapeType.rect,{x:0,y:SH-2.0,w:SW,h:2.0,fill:{color:C.dblue},line:{color:C.dblue}});

  sl.addText('Thank You',{x:0.4,y:0.3,w:SW-0.8,h:1.3,fontSize:48,bold:true,color:C.white,align:'center',fontFace:'Calibri',valign:'middle'});

  // Summary box
  sl.addShape(pptx.ShapeType.roundRect,{x:0.6,y:2.2,w:SW-1.2,h:3.0,fill:{color:'0D2B5A'},line:{color:C.gold,pt:2},rectRadius:0.15});
  sl.addText('Research Summary',{x:0.8,y:2.28,w:SW-1.6,h:0.4,fontSize:14,bold:true,color:C.gold,fontFace:'Calibri',align:'center'});

  const bullets=[
    'Problem: 4 critical gaps — weak fusion, cold-start failure, black-box predictions, data imbalance',
    'Proposed: H-GNN-RNN-DTI with H-GAT drug encoder + BiGRU protein encoder + novel Gated Cross-Attention',
    'Innovation: Dynamic bidirectional drug–protein attention with adaptive gating — beyond static concatenation',
    'Generalization: ChemBERTa + ESM-2 pretraining + focal loss → improved cold-start performance',
    'Interpretability: Intrinsic attention attribution + Grad-CAM validated against PDB binding sites',
    'Evaluation: 7 datasets, AUC/AUPR/RMSE/CI, cold-start S1/S2/S3, cross-dataset, ablation studies',
  ];
  bullets.forEach((b,i)=>{
    sl.addText(`  ◆ ${b}`,{x:0.85,y:2.74+i*0.38,w:SW-1.7,h:0.36,fontSize:11,color:i===2?C.gold:C.white,bold:i===2,fontFace:'Calibri'});
  });

  sl.addText('Questions & Discussion Welcome',{x:0.4,y:5.35,w:SW-0.8,h:0.58,fontSize:20,bold:true,color:'90CAF9',align:'center',fontFace:'Calibri',valign:'middle'});
  sl.addText('Jamila Abdul-Hadi  |  24100625  |  jamcy98@gmail.com  |  School of Computer Sciences, USM',
    {x:0.4,y:SH-1.72,w:SW-0.8,h:0.4,fontSize:11,color:'BDE3FA',align:'center',fontFace:'Calibri'});
  sl.addText('Supervisor: Assoc. Prof. Dr. Nurul Hashimah Ahamed Hassain Malim',
    {x:0.4,y:SH-1.3,w:SW-0.8,h:0.36,fontSize:11,color:'90CAF9',align:'center',fontFace:'Calibri',italic:true});

  sl.addNotes(`TALKING POINTS — CLOSING

In closing, let me summarize what I have presented today.

The research addresses four clearly identified gaps in the current DTI prediction literature: weak cross-modal feature integration, poor cold-start generalization, lack of interpretability, and inadequate handling of data imbalance.

My proposed solution — the H-GNN-RNN-DTI model — addresses all four simultaneously. The Hierarchical Graph Attention Network captures molecular topology; the Bidirectional GRU captures protein sequence context; the Gated Cross-Attention Fusion enables dynamic, adaptive drug–protein interaction modeling at the feature level; foundation model pretraining and focal loss address cold-start and imbalance; and the intrinsic attention mechanism provides biologically meaningful interpretability.

The evaluation framework is rigorous: seven datasets, four evaluation scenarios including cold-start, comprehensive ablation studies, and biological validation of interpretability.

The research timeline is realistic: three years with clearly defined milestones, targeting Q1 journal publications and competitive conference venues.

I am confident that this work represents a timely, well-motivated, and methodologically sound contribution to the field of computational drug discovery.

Thank you for your time and attention. I welcome any questions, concerns, or suggestions regarding the proposal.

ANTICIPATED SUPERVISOR QUESTIONS:

Q: How does your gated cross-attention compare to existing co-attention mechanisms?
A: The key difference is the gating function, which explicitly prevents the cross-modal update from completely overwriting the original modality representation — addressing information loss that can occur in standard co-attention.

Q: What if ESM-2 pretraining doesn't help cold-start performance significantly?
A: We include both ChemBERTa and ESM-2 as separate ablation conditions, so we can assess their individual contribution. If pretrained embeddings don't help, we will investigate alternative strategies like graph meta-learning or prototypical networks.

Q: How do you handle the computational cost of cross-attention for long protein sequences?
A: We pad/truncate proteins to 1,200 residues, and cross-attention is computed at the global embedding level (after pooling), not token-by-token, keeping the computational cost manageable.`);
  num(sl,21);
}

// ── Save ──────────────────────────────────────────────────────────────────
await pptx.writeFile({ fileName: OUT });
console.log(`Done: DTI_Proposal_Presentation.pptx  (saved to paper/)`);
