// generate_figures.mjs — Creates all professional SVG diagrams → PNGs
import { Resvg } from '@resvg/resvg-js';
import fs from 'fs';

const OUT = 'C:\\Users\\Jamila\\Modeling-DTI\\paper\\figures';
fs.mkdirSync(OUT, { recursive: true });

function render(svgStr, name) {
  const r = new Resvg(svgStr, { fitTo: { mode: 'original' }, font: { loadSystemFonts: true } });
  const buf = r.render().asPng();
  fs.writeFileSync(`${OUT}\\${name}`, buf);
  console.log(`  ✓ ${name}  (${(buf.length/1024).toFixed(1)} KB)`);
  return buf;
}

const DEFS = `<defs>
  <marker id="arr" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0,10 3.5,0 7" fill="#455A64"/>
  </marker>
  <marker id="arrW" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0,10 3.5,0 7" fill="#FFFFFF"/>
  </marker>
  <marker id="arrB" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0,10 3.5,0 7" fill="#1565C0"/>
  </marker>
  <marker id="arrG" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0,10 3.5,0 7" fill="#2E7D32"/>
  </marker>
  <filter id="sh" x="-5%" y="-5%" width="110%" height="110%">
    <feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="#00000025"/>
  </filter>
</defs>`;

// ── Helpers ─────────────────────────────────────────────────────────────────

function rect(x,y,w,h,fill,stroke='#90A4AE',rx=8,extra='') {
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="1.5" ${extra}/>`;
}

function esc(t) {
  return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function label(x,y,text,size=13,fill='#212121',weight='bold',anchor='middle') {
  const lines = Array.isArray(text) ? text : String(text).split('\n');
  const lh = size*1.45;
  const oy = y - (lines.length-1)*lh/2;
  return lines.map((l,i)=>
    `<text x="${x}" y="${oy+i*lh}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}" fill="${fill}" font-weight="${weight}">${esc(l)}</text>`
  ).join('');
}

function box(x,y,w,h,fill,text,tsize=13,tcol='#212121',stroke='#90A4AE',rx=8) {
  const cy = y+h/2;
  return rect(x,y,w,h,fill,stroke,rx,'filter="url(#sh)"') + label(x+w/2, cy, text, tsize, tcol);
}

function hArr(x1,y,x2,col='#455A64',marker='arr') {
  return `<line x1="${x1}" y1="${y}" x2="${x2-9}" y2="${y}" stroke="${col}" stroke-width="2" marker-end="url(#${marker})"/>`;
}

function vArr(x,y1,y2,col='#455A64',marker='arr') {
  return `<line x1="${x}" y1="${y1}" x2="${x}" y2="${y2-9}" stroke="${col}" stroke-width="2" marker-end="url(#${marker})"/>`;
}

function lineP(x1,y1,x2,y2,col='#455A64',dashed=false) {
  const d = dashed ? 'stroke-dasharray="5,3"' : '';
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col}" stroke-width="1.8" ${d}/>`;
}

// ─── FIGURE 1: Survey Framework Overview ───────────────────────────────────
export function fig1_framework() {
  const W=1380, H=520;
  const cols=['#D6EAF8','#D5F5E3','#FAD7A0','#E8DAEF','#FDEBD0'];
  const dark=['#1A5276','#1E8449','#9E5B00','#6C3483','#935116'];
  const heads=['Introduction','Related Databases','Encoding Methods','Research Methods','Model Evaluation'];
  const subs=[
    ['DTI/DTA Background','Drug Discovery','Motivation & Cost'],
    ['DAVIS, KIBA, BindingDB','Yamanishi_08, Luo_17','ChEMBL, DrugBank'],
    ['SMILES → Mol. Graph','Protein (FASTA) Seq.','GNN / RNN / LM Init'],
    ['CNN, GNN, RNN','Transformer, KG-based','Hybrid Multimodal'],
    ['AUC-ROC, AUPR','RMSE, CI, MAE','Cold-Start S1/S2/S3'],
  ];
  const cw=240, cx=30, cy=40, ch=300, gap=16;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  // Title bar
  s += rect(0,0,W,38,'#1A237E','none',0);
  s += label(W/2,19,'Fig. 1 — Framework Overview: Comprehensive Review of DTI Prediction Methods',15,'#FFFFFF','bold');

  // 5 column boxes
  for(let i=0;i<5;i++){
    const x = cx + i*(cw+gap);
    s += rect(x,cy,cw,ch,cols[i],'#B0BEC5',10,'filter="url(#sh)"');
    // header
    s += rect(x,cy,cw,48,dark[i],'none',10);
    s += rect(x,cy+38,cw,10,dark[i],'none',0); // square bottom
    s += label(x+cw/2, cy+24, heads[i], 13, '#FFFFFF','bold');
    // icon circle
    s += `<circle cx="${x+cw/2}" cy="${cy+85}" r="28" fill="${cols[i]}" stroke="${dark[i]}" stroke-width="2"/>`;
    s += label(x+cw/2, cy+90, String(i+1), 22, dark[i], 'bold');
    // sub-items
    subs[i].forEach((t,j)=>{
      s += rect(x+12, cy+130+j*50, cw-24, 38, '#FFFFFF','#CFD8DC',6,'filter="url(#sh)"');
      s += label(x+cw/2, cy+149+j*50, t, 11, '#37474F','normal');
    });
  }

  // Arrows between columns
  for(let i=0;i<4;i++){
    const x = cx + (i+1)*(cw+gap) - gap/2 - 4;
    s += hArr(cx+(i+1)*(cw+gap)-gap, cy+ch/2, cx+(i+1)*(cw+gap),'#1A237E','arrB');
  }

  // Bottom band
  const bw=380, bh=80, by=370, bx=[30,520,1010];
  const bcols=['#FFCCBC','#C8E6C9','#BBDEFB'];
  const bdark=['#BF360C','#1B5E20','#0D47A1'];
  const btxt=['5 Research Gaps\nIdentified','7 Future Research\nDirections','Conclusions +\nNext Steps'];
  bx.forEach((x,i)=>{
    s += rect(x,by,bw,bh,bcols[i],'#90A4AE',10,'filter="url(#sh)"');
    s += label(x+bw/2, by+bh/2, btxt[i], 13, bdark[i],'bold');
  });
  // dashed arrows
  s += `<line x1="${bx[2]+bw/2}" y1="${cy+ch}" x2="${bx[2]+bw/2}" y2="${by}" stroke="#1A237E" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arrB)"/>`;
  s += `<line x1="${bx[1]+bw}" y1="${by+bh/2}" x2="${bx[2]}" y2="${by+bh/2}" stroke="#455A64" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arr)"/>`;
  s += `<line x1="${bx[0]+bw}" y1="${by+bh/2}" x2="${bx[1]}" y2="${by+bh/2}" stroke="#455A64" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arr)"/>`;

  // Caption
  s += label(W/2, H-12, 'Fig. 1. Framework overview of this comprehensive review on hybrid deep learning approaches for DTI prediction.',12,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig1_framework.png');
}

// ─── FIGURE 2: Mind Map – DTI Method Taxonomy ──────────────────────────────
export function fig2_mindmap() {
  const W=980, H=880;
  const cx=490, cy=420;

  // Branch data: [angle_deg, color, dark, title, subs]
  const branches = [
    [270,'#B3E5FC','#01579B','Physics-Based\nMethods',['Molecular Docking','Ligand-Based/QSAR','Force-Field Scoring']],
    [330,'#C8E6C9','#1B5E20','Classical Machine\nLearning',['SVM / Random Forest','Gradient Boosting','Network-Based (RWR)']],
    [30,'#FFF9C4','#F57F17','Deep Learning\nArchitectures',['CNN (DeepDTA)','GNN (GraphDTA)','RNN / LSTM / GRU']],
    [90,'#F8BBD0','#880E4F','Transformer &\nFoundation Models',['TransformerCPI, MolTrans','ChemBERTa, ESM-2','ProtT5, MolFormer']],
    [150,'#E1BEE7','#4A148C','Hybrid Multimodal\nDeep Learning',['GNN + RNN','GNN + Transformer','Gated Cross-Attention']],
    [210,'#FFE0B2','#BF360C','Interpretable &\nCold-Start Models',['Attention Attribution','Multi-View Pretraining','Domain Adaptation']],
  ];

  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);

  // Draw branch lines and sub-nodes
  branches.forEach(([angleDeg, col, dark, title, subs])=>{
    const rad = angleDeg * Math.PI / 180;
    const r1=130, r2=260, r3=410;
    const mx = cx + Math.cos(rad)*r2;
    const my = cy + Math.sin(rad)*r2;

    // Main spoke line
    s += `<line x1="${cx + Math.cos(rad)*105}" y1="${cy + Math.sin(rad)*105}" x2="${cx + Math.cos(rad)*215}" y2="${cy + Math.sin(rad)*215}" stroke="${dark}" stroke-width="2.5"/>`;

    // Branch box
    const bw=150, bh=54;
    s += rect(mx-bw/2, my-bh/2, bw, bh, col, dark, 10,'filter="url(#sh)"');
    s += label(mx, my, title, 12, dark, 'bold');

    // Sub-nodes
    const subAngles = [-28, 0, 28];
    subs.forEach((sub, si)=>{
      const srad = (angleDeg + subAngles[si]) * Math.PI / 180;
      const sx = cx + Math.cos(srad)*r3;
      const sy = cy + Math.sin(srad)*r3;
      const sw=145, sh=38;
      s += `<line x1="${mx + Math.cos(srad)*80}" y1="${my + Math.sin(srad)*28}" x2="${sx - Math.cos(srad)*74}" y2="${sy - Math.sin(srad)*20}" stroke="${dark}" stroke-width="1.5" stroke-dasharray="4,2"/>`;
      s += rect(sx-sw/2, sy-sh/2, sw, sh, '#FFFFFF', dark, 6,'filter="url(#sh)"');
      s += label(sx, sy, sub, 11, dark,'normal');
    });
  });

  // Central node
  s += `<ellipse cx="${cx}" cy="${cy}" rx="100" ry="72" fill="#1A237E" filter="url(#sh)" stroke="#0D1B6E" stroke-width="2"/>`;
  s += label(cx, cy-8, 'DTI', 20, '#FFFFFF','bold');
  s += label(cx, cy+14, 'Prediction', 15, '#90CAF9','bold');
  s += label(cx, cy+32, 'Methods', 15, '#90CAF9','bold');

  // Title
  s += rect(0,0,W,36,'#1A237E','none',0);
  s += label(W/2,18,'Fig. 2 — Mind Map: Taxonomy of DTI/DTA Prediction Methods',14,'#FFFFFF','bold');
  s += label(W/2,H-12,'Fig. 2. Mind map illustrating the six major paradigms for drug–target interaction prediction.',12,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig2_mindmap.png');
}

// ─── FIGURE 3: H-GNN-RNN-DTI Architecture ──────────────────────────────────
export function fig3_architecture() {
  const W=1400, H=780;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#F8FAFB','none',0);
  // Title bar
  s += rect(0,0,W,40,'#1A237E','none',0);
  s += label(W/2,20,'Fig. 3 — H-GNN-RNN-DTI: Proposed Hybrid Architecture Overview',15,'#FFFFFF','bold');

  // ── Drug Branch (left) ──────────────────────────────────────────
  const drugX=40, drugW=340, drugCol='#DDEEFF', drugDark='#1565C0';
  s += rect(drugX,54,drugW,580,'#E8F4FD',drugDark,12,'filter="url(#sh)"');
  s += rect(drugX,54,drugW,38,'#1565C0','none',12);
  s += rect(drugX,78,drugW,14,'#1565C0','none',0);
  s += label(drugX+drugW/2,73,'DRUG BRANCH',14,'#FFFFFF','bold');

  const db = [
    ['SMILES String\nInput','#FFFFFF',drugDark,105],
    ['RDKit Mol. Graph\nG = (V, E)','#B3D9F7',drugDark,180],
    ['ChemBERTa Node\nFeature Init.','#B3D9F7',drugDark,255],
    ['H-GAT Encoder\n3 Layers · 8 Heads','#1565C0','#FFFFFF',330],
    ['Attention-Weighted\nGraph READOUT','#B3D9F7',drugDark,405],
    ['Drug Embedding\nz_d  ∈  ℝᵈ','#1565C0','#FFFFFF',480],
  ];
  db.forEach(([t,f,c,y])=>{
    s += rect(drugX+20,y,drugW-40,56,f,drugDark,8,'filter="url(#sh)"');
    s += label(drugX+drugW/2,y+28,t,12,c,'bold');
  });
  for(let i=0;i<db.length-1;i++) {
    const y1=db[i][3]+56, y2=db[i+1][3];
    s += vArr(drugX+drugW/2, y1, y2, drugDark,'arrB');
  }

  // ── Protein Branch (right) ──────────────────────────────────────
  const protX=1020, protW=340, protCol='#E8F5E9', protDark='#2E7D32';
  s += rect(protX,54,protW,580,protCol,protDark,12,'filter="url(#sh)"');
  s += rect(protX,54,protW,38,'#2E7D32','none',12);
  s += rect(protX,78,protW,14,'#2E7D32','none',0);
  s += label(protX+protW/2,73,'PROTEIN BRANCH',14,'#FFFFFF','bold');

  const pb = [
    ['FASTA Amino Acid\nSequence Input','#FFFFFF',protDark,105],
    ['ESM-2 Residue\nEmbeddings (650M)','#A5D6A7',protDark,180],
    ['Residue-Level\nTokenization','#A5D6A7',protDark,255],
    ['BiLSTM / BiGRU\n2 Layers (bidirectional)','#2E7D32','#FFFFFF',330],
    ['Attention-Based\nSequence Pooling','#A5D6A7',protDark,405],
    ['Protein Embedding\nz_p  ∈  ℝᵈ','#2E7D32','#FFFFFF',480],
  ];
  pb.forEach(([t,f,c,y])=>{
    s += rect(protX+20,y,protW-40,56,f,protDark,8,'filter="url(#sh)"');
    s += label(protX+protW/2,y+28,t,12,c,'bold');
  });
  for(let i=0;i<pb.length-1;i++) {
    const y1=pb[i][3]+56, y2=pb[i+1][3];
    s += vArr(protX+protW/2, y1, y2, protDark,'arrG');
  }

  // ── Gated Cross-Attention Fusion (centre) ──────────────────────
  const fusX=440, fusW=520, fusY=90, fusH=380;
  s += rect(fusX,fusY,fusW,fusH,'#FFF8E1','#E65100',12,'filter="url(#sh)"');
  s += rect(fusX,fusY,fusW,42,'#E65100','none',12);
  s += rect(fusX,fusY+32,fusW,10,'#E65100','none',0);
  s += label(fusX+fusW/2,fusY+21,'GATED CROSS-ATTENTION FUSION MODULE',13,'#FFFFFF','bold');

  const eqs=[
    ['Cross-Attention (Drug → Protein):','A_{d→p} = softmax( Q_d K_p^T / √d_k ) · V_p',fusY+80],
    ['Cross-Attention (Protein → Drug):','A_{p→d} = softmax( Q_p K_d^T / √d_k ) · V_d',fusY+140],
    ['Drug Gate:','G_d = σ( W_g [h_d ∥ A_{d→p}] + b_g )',fusY+200],
    ['Gated Drug Repr.:','h_d\' = G_d ⊙ A_{d→p} + (1 - G_d) ⊙ h_d',fusY+240],
    ['Protein Gate (symmetric):','G_p = σ( W_g\' [h_p ∥ A_{p→d}] + b_g\' )',fusY+280],
    ['Fused Representation:','h_fused = σ( W_f [z_d ∥ z_p] + b_f )',fusY+330],
  ];
  eqs.forEach(([lbl,eq,y])=>{
    s += label(fusX+20, y, lbl, 11,'#BF360C','bold','start');
    s += label(fusX+20, y+16, eq, 11,'#212121','normal','start');
  });

  // Arrows from drug/protein to fusion box
  s += hArr(drugX+drugW, 480+28, fusX,'#E65100');
  s += hArr(protX, 480+28, fusX+fusW,'#E65100');

  // ── Prediction Head ────────────────────────────────────────────
  const phX=540, phY=510, phW=320, phH=200;
  s += rect(phX,phY,phW,phH,'#F3E5F5','#6A1B9A',12,'filter="url(#sh)"');
  s += rect(phX,phY,phW,40,'#6A1B9A','none',12);
  s += rect(phX,phY+30,phW,10,'#6A1B9A','none',0);
  s += label(phX+phW/2,phY+20,'PREDICTION HEAD',13,'#FFFFFF','bold');

  s += rect(phX+20,phY+58,phW-40,40,'#E1BEE7','#6A1B9A',8,'filter="url(#sh)"');
  s += label(phX+phW/2,phY+78,'MLP (FC Layers + Dropout)',12,'#4A148C','bold');

  // Two outputs
  s += rect(phX+20,phY+118,130,56,'#C5CAE9','#283593',8,'filter="url(#sh)"');
  s += label(phX+85,phY+146,['Classification','Sigmoid → p(DTI)'],11,'#1A237E','bold');
  s += rect(phX+170,phY+118,130,56,'#B2DFDB','#004D40',8,'filter="url(#sh)"');
  s += label(phX+235,phY+146,['Regression','Linear → Affinity'],11,'#004D40','bold');

  // Arrow from fusion to prediction
  s += vArr(fusX+fusW/2, fusY+fusH, phY,'#6A1B9A');

  // Loss annotations
  s += rect(800,phY+60,180,90,'#FFECB3','#F57F17',8);
  s += label(890,phY+88,['Loss Functions:','Focal Loss (class.)','MSE (regression)'],11,'#E65100','bold');
  s += `<line x1="${phX+phW}" y1="${phY+80}" x2="800" y2="${phY+88}" stroke="#F57F17" stroke-width="1.5" stroke-dasharray="4,3"/>`;

  // Legend
  const legY=H-58, legX=40;
  [[drugDark,'Drug Branch (GNN)'],[protDark,'Protein Branch (RNN)'],['#E65100','Gated Cross-Attn Fusion'],['#6A1B9A','Prediction Head']].forEach(([c,t],i)=>{
    s += rect(legX+i*280, legY, 18,18,c,c,3);
    s += label(legX+i*280+24, legY+13, t, 11,'#37474F','normal','start');
  });

  s += label(W/2,H-12,'Fig. 3. Conceptual architecture of the proposed H-GNN-RNN-DTI model. The Gated Cross-Attention Fusion Module enables adaptive bidirectional drug–protein interaction.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig3_architecture.png');
}

// ─── FIGURE 4: CNN-Based Architecture ──────────────────────────────────────
export function fig4_cnn() {
  const W=1200, H=370;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  s += rect(0,0,W,36,'#37474F','none',0);
  s += label(W/2,18,'Fig. 4 — CNN-Based DTI Architecture (DeepDTA Paradigm)',14,'#FFFFFF','bold');

  const bw=140, bh=54, gap=18;
  const row1=[56,'#E3F2FD','#1565C0'];
  const row2=[170,'#E8F5E9','#2E7D32'];

  const steps1=['SMILES String','Char. Embedding','Conv1D Filters\n(k=4,6,8)','Max Pooling','Drug Embed.\nd_D'];
  const steps2=['FASTA Sequence','Char. Embedding','Conv1D Filters\n(k=4,6,8)','Max Pooling','Protein Embed.\nd_P'];

  [[steps1,row1],[steps2,row2]].forEach(([steps,[y,col,dark]])=>{
    steps.forEach((t,i)=>{
      const x = 40+i*(bw+gap);
      s += box(x,y,bw,bh,col,t,12,dark,dark,8);
      if(i<steps.length-1) s += hArr(x+bw, y+bh/2, x+bw+gap+1,dark,'arrB');
    });
  });

  // Concat block
  const cx=870, cy=56, cw=110, ch=168;
  s += rect(cx,cy,cw,ch,'#FFF3E0','#E65100',8,'filter="url(#sh)"');
  s += label(cx+cw/2,cy+ch/2,'Concat\n[d_D ; d_P]',13,'#BF360C','bold');

  // FC + Output
  s += box(1010,90,110,80,'#F3E5F5','FC Layers\n+ ReLU',12,'#4A148C','#6A1B9A',8);
  s += box(1145,90,100,80,'#EDE7F6','DTI Score\n(Sigmoid\n/Linear)',11,'#311B92','#7E57C2',8);

  s += hArr(40+5*(bw+gap), row1[0]+bh/2, cx,'#E65100');
  s += hArr(40+5*(bw+gap), row2[0]+bh/2, cx,'#E65100');
  s += hArr(cx+cw, cy+ch/2, 1010,'#455A64');
  s += hArr(1120, 90+40, 1145,'#455A64');

  // Key limitation note
  s += rect(30,270,500,68,'#FFEBEE','#C62828',8);
  s += label(280,300,['Key Limitations: No molecular graph topology; local protein context only;','static concatenation fusion; no pre-trained embeddings.'],11,'#B71C1C','normal');
  s += label(W/2,H-10,'Fig. 4. CNN-based DTI/DTA architecture (DeepDTA paradigm). Character-level sequence encoding with convolutional filters.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig4_cnn.png');
}

// ─── FIGURE 5: GNN-Based Architecture ──────────────────────────────────────
export function fig5_gnn() {
  const W=1200, H=420;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  s += rect(0,0,W,36,'#1A237E','none',0);
  s += label(W/2,18,'Fig. 5 — GNN-Based DTI Architecture (GraphDTA Paradigm)',14,'#FFFFFF','bold');

  // Drug pipeline (top)
  const dr=[
    ['SMILES','#E3F2FD','#1565C0',55,120],
    ['RDKit\nMol. Graph','#B3D9F7','#0D47A1',205,120],
    ['Atom/Bond\nFeatures','#B3D9F7','#0D47A1',355,120],
    ['GNN Layers\n(GCN/GAT/GIN)','#1565C0','#FFFFFF',505,120],
    ['Graph\nREADOUT','#B3D9F7','#0D47A1',665,120],
    ['Drug\nEmbedding','#0D47A1','#FFFFFF',815,120],
  ];
  dr.forEach(([t,f,c,x,y])=>{
    s += box(x,y,130,60,f,t,11,c,'#1565C0',8);
    if(x<815) s += hArr(x+130,y+30,x+145,'#1565C0','arrB');
  });

  // GNN message passing equation
  s += rect(505,50,280,60,'#E8EAF6','#3949AB',8);
  s += label(505+140,68,'h_v^(l+1) = σ(W·AGG{h_u^l: u∈N(v)})',11,'#1A237E','normal');
  s += label(505+140,85,'(GAT: weighted by attention α_vj)',10,'#5C6BC0','normal');

  // Protein pipeline (middle)
  const pr=[
    ['Protein\nFASTA','#E8F5E9','#2E7D32',55,250],
    ['Amino Acid\nEmbedding','#A5D6A7','#1B5E20',205,250],
    ['CNN / RNN\nEncoder','#2E7D32','#FFFFFF',355,250],
    ['Protein\nEmbedding','#1B5E20','#FFFFFF',505,250],
  ];
  pr.forEach(([t,f,c,x,y])=>{
    s += box(x,y,130,60,f,t,11,c,'#2E7D32',8);
    if(x<505) s += hArr(x+130,y+30,x+145,'#2E7D32','arrG');
  });

  // Concat + Prediction
  s += box(715,210,120,100,'#FFF8E1','Concat\n[d_Drug\n;d_Prot]',12,'#BF360C','#E65100',8);
  s += hArr(815+130, 120+30, 715+10,'#455A64');
  s += hArr(505+130, 250+30, 715+10,'#455A64');
  s += box(880,210,120,100,'#EDE7F6','FC Layers\n→ Affinity\n/ Interaction',11,'#4A148C','#6A1B9A',8);
  s += hArr(835,210+50,880,'#455A64');

  s += rect(30,340,660,48,'#FFEBEE','#C62828',8);
  s += label(360,366,['Limitation: Protein encoded as flat sequence (no 3D structure);','static concatenation fusion; no cross-modal attention.'],11,'#B71C1C','normal');
  s += label(W/2,H-10,'Fig. 5. GNN-based DTI architecture (GraphDTA paradigm). Molecular graph encoding via GNN combined with sequence-based protein encoding.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig5_gnn.png');
}

// ─── FIGURE 6: Transformer Architecture ────────────────────────────────────
export function fig6_transformer() {
  const W=1200, H=440;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  s += rect(0,0,W,36,'#004D40','none',0);
  s += label(W/2,18,'Fig. 6 — Transformer-Based DTI Architecture (TransformerCPI / MolTrans Paradigm)',14,'#FFFFFF','bold');

  // Drug path
  [['SMILES / Substructure\nTokens','#E0F7FA','#006064',50,70],
   ['Token + Segment +\nPosition Embedding','#B2EBF2','#006064',220,70],
   ['Transformer Encoder\nMulti-Head Self-Attn (L layers)','#006064','#FFFFFF',420,70],
   ['Drug\nRepresentation','#00695C','#FFFFFF',650,70],
  ].forEach(([t,f,c,x,y])=>{
    s += box(x,y,150,70,f,t,11,c,'#006064',8);
    if(x<650) s += hArr(x+150,y+35,x+165,'#006064');
  });

  // Protein path
  [['FASTA / AA\nTokens','#E8F5E9','#1B5E20',50,210],
   ['Token + Segment +\nPosition Embedding','#A5D6A7','#1B5E20',220,210],
   ['Transformer Encoder\nMulti-Head Self-Attn (L layers)','#2E7D32','#FFFFFF',420,210],
   ['Protein\nRepresentation','#1B5E20','#FFFFFF',650,210],
  ].forEach(([t,f,c,x,y])=>{
    s += box(x,y,150,70,f,t,11,c,'#2E7D32',8);
    if(x<650) s += hArr(x+150,y+35,x+165,'#2E7D32','arrG');
  });

  // Cross-attention / bilinear fusion
  s += rect(830,80,160,210,'#FFF9C4','#F9A825',10,'filter="url(#sh)"');
  s += rect(830,80,160,40,'#F9A825','none',10);
  s += rect(830,110,160,10,'#F9A825','none',0);
  s += label(830+80,100,'Cross-Attn\nFusion',13,'#212121','bold');
  s += label(830+80,160,'A = softmax(\n Q_d K_p^T /√d) V_p',11,'#37474F','normal');
  s += label(830+80,210,'Bilinear:\nI = h_d^T W_B h_p',11,'#37474F','normal');
  s += hArr(800, 70+35, 830,'#F9A825');
  s += hArr(800, 210+35, 830,'#F9A825');

  // Prediction
  s += box(1020,120,130,130,'#EDE7F6','MLP\n→\nDTI Score\n(sigmoid/\nlinear)',11,'#4A148C','#6A1B9A',8);
  s += hArr(990,80+105,1020,'#6A1B9A');

  // BERT embedding diagram (inset) — inspired by Sample Fig. 12
  s += rect(50,315,560,90,'#F3E5F5','#6A1B9A',8);
  s += label(330,330,'Pre-Trained Embedding Input (BERT-style):  [CLS] token₁ token₂ ... tokenₙ',12,'#4A148C','bold');
  s += label(330,352,'Token Embeddings  +  Segment Embeddings  +  Position Embeddings',11,'#37474F','normal');
  s += label(330,372,'(ChemBERTa for drug;  ESM-2 / ProtT5 for protein)',11,'#37474F','normal');

  s += label(W/2,H-10,'Fig. 6. Transformer-based DTI architecture. Self-attention models all-pair token dependencies; cross-attention enables inter-modal drug–protein alignment.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig6_transformer.png');
}

// ─── FIGURE 7: Knowledge Graph Architecture ─────────────────────────────────
export function fig7_kg() {
  const W=1200, H=400;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  s += rect(0,0,W,36,'#4A148C','none',0);
  s += label(W/2,18,'Fig. 7 — Knowledge Graph-Based DTI Architecture (TTModel / DTKGIN Paradigm)',14,'#FFFFFF','bold');

  // KG node types
  const nodes=[['Drug','#B3D9F7','#1565C0',80,155],['Protein','#A5D6A7','#2E7D32',80,260],
               ['Disease','#FFCCBC','#BF360C',240,155],['Pathway','#FFF9C4','#F57F17',240,260],
               ['Side Effect','#E1BEE7','#4A148C',160,205]];
  nodes.forEach(([t,f,c,x,y])=>{
    s += `<ellipse cx="${x}" cy="${y}" rx="65" ry="32" fill="${f}" stroke="${c}" stroke-width="2" filter="url(#sh)"/>`;
    s += label(x,y+4,t,12,c,'bold');
  });
  // KG edges (dashed)
  s += `<line x1="145" y1="155" x2="175" y2="210" stroke="#90A4AE" stroke-width="1.5" stroke-dasharray="4,2"/>`;
  s += `<line x1="145" y1="260" x2="175" y2="210" stroke="#90A4AE" stroke-width="1.5" stroke-dasharray="4,2"/>`;
  s += `<line x1="240" y1="155" x2="225" y2="210" stroke="#90A4AE" stroke-width="1.5" stroke-dasharray="4,2"/>`;
  s += `<line x1="240" y1="260" x2="225" y2="210" stroke="#90A4AE" stroke-width="1.5" stroke-dasharray="4,2"/>`;
  s += rect(30,50,300,310,'none','#90A4AE',12);
  s += label(180,72,'Biomedical Knowledge Graph',12,'#37474F','bold');

  // GNN processing
  s += box(380,120,150,80,'#1565C0',['KG Embedding','GNN / TransE','(Entity + Relation)'],11,'#FFFFFF','#0D47A1',8);
  s += box(380,240,150,80,'#4A148C',['Intent Graph\n(DTKGIN latent','intent nodes)'],11,'#FFFFFF','#38006B',8);
  s += hArr(330,205,380,'#455A64');
  s += hArr(330,280,380,'#455A64');

  // Embedding box
  s += box(600,120,160,80,'#0D47A1',['Drug Entity\nEmbedding  E_d'],12,'#FFFFFF','#1A237E',8);
  s += box(600,240,160,80,'#1B5E20',['Target Entity\nEmbedding  E_t'],12,'#FFFFFF','#004D40',8);
  s += hArr(530,160,600,'#1565C0','arrB');
  s += hArr(530,280,600,'#2E7D32','arrG');

  // Prediction
  s += box(830,170,150,100,'#FFF8E1',['Prediction\n\nScore(d,t) =\nE_d · E_t'],12,'#BF360C','#E65100',8);
  s += hArr(760,160,830,'#E65100');
  s += hArr(760,280,830,'#E65100');
  s += box(1040,185,130,70,'#EDE7F6',['Sigmoid\n→ DTI\nScore'],12,'#4A148C','#6A1B9A',8);
  s += hArr(980,220,1040,'#6A1B9A');

  s += rect(30,370,620,20,'none','none',0);
  s += label(W/2,H-10,'Fig. 7. Knowledge graph-based DTI architecture. Entities embedded via GNN/TransE; drug-target score from inner product of entity embeddings.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig7_kg.png');
}

// ─── FIGURE 8: Cross-Attention Mechanism (like Sample Fig. 17) ─────────────
export function fig8_crossattn() {
  const W=1050, H=540;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  s += rect(0,0,W,36,'#37474F','none',0);
  s += label(W/2,18,'Fig. 8 — Gated Cross-Attention Mechanism: Drug ↔ Protein Interaction',14,'#FFFFFF','bold');

  // Drug input
  s += box(30,100,160,70,'#E3F2FD','Drug Input\n(SMILES /\nMol. Graph)',12,'#1565C0','#1565C0',8);
  s += box(30,250,160,70,'#E8F5E9','Target Input\n(Protein\nFASTA Seq.)',12,'#2E7D32','#2E7D32',8);

  // Attention mechanisms (left)
  s += box(240,90,140,90,'#B3D9F7','Drug Attn.\nMechanism\n(H-GAT)',11,'#0D47A1','#1565C0',8);
  s += box(240,250,140,90,'#A5D6A7','Target Attn.\nMechanism\n(BiGRU)',11,'#1B5E20','#2E7D32',8);
  s += hArr(190,135,240,'#1565C0','arrB');
  s += hArr(190,285,240,'#2E7D32','arrG');

  // Self-attention bubbles
  s += `<ellipse cx="380" cy="72" rx="68" ry="30" fill="#90CAF9" stroke="#1565C0" stroke-width="1.5" filter="url(#sh)"/>`;
  s += label(380,76,'Self-Attention',11,'#0D47A1','bold');
  s += `<ellipse cx="380" cy="390" rx="68" ry="30" fill="#A5D6A7" stroke="#2E7D32" stroke-width="1.5" filter="url(#sh)"/>`;
  s += label(380,394,'Self-Attention',11,'#1B5E20','bold');
  s += vArr(380,102,135,'#1565C0','arrB');
  s += vArr(380,360,321,'#2E7D32','arrG');

  // Drug & Target embeddings
  s += box(345,135,120,85,'#1565C0',['Drug','Embedding','h_d'],13,'#FFFFFF','#0D47A1',8);
  s += box(345,250,120,85,'#2E7D32',['Target','Embedding','h_p'],13,'#FFFFFF','#1B5E20',8);
  s += hArr(380,135,345+60,'#1565C0','arrB');
  s += hArr(380,335,345+60,'#2E7D32','arrG');

  // Cross-attention (centre)
  s += rect(500,195,130,80,'#FFF3E0','#E65100',10,'filter="url(#sh)"');
  s += label(565,225,'Cross-Attention','#E65100' === '#E65100' ? 12 : 12,'#BF360C','bold');
  s += label(565,243,'Mechanism',12,'#BF360C','bold');
  s += label(565,262,'A_{d→p} & A_{p→d}',10,'#37474F','normal');
  s += hArr(465,177,500,'#E65100');
  s += hArr(465,318,500,'#E65100');

  // Gated outputs
  s += box(680,130,140,90,'#1565C0',['Gated\nDrug Repr.\nh_d\''],12,'#FFFFFF','#0D47A1',8);
  s += box(680,250,140,90,'#2E7D32',['Gated\nProtein Repr.\nh_p\''],12,'#FFFFFF','#1B5E20',8);
  s += hArr(630,230,680,'#E65100');
  s += hArr(630,295,680,'#E65100');

  // Multiple attention / output
  s += rect(870,135,140,210,'#E8EAF6','#3949AB',10,'filter="url(#sh)"');
  s += label(940,155,'Multiple','bold' === 'bold' ? 13 : 13,'#1A237E','bold');
  s += label(940,173,'Attention','13','#1A237E','bold');
  s += label(940,191,'Mechanisms','13','#1A237E','bold');
  s += `<rect x="880" y="205" width="120" height="28" rx="5" fill="#C5CAE9" stroke="#3949AB" stroke-width="1"/>`;
  s += label(940,219,'Self-Attn Drug',10,'#1A237E','normal');
  s += `<rect x="880" y="240" width="120" height="28" rx="5" fill="#C5CAE9" stroke="#3949AB" stroke-width="1"/>`;
  s += label(940,254,'Cross-Attn Joint',10,'#1A237E','normal');
  s += `<rect x="880" y="275" width="120" height="28" rx="5" fill="#C5CAE9" stroke="#3949AB" stroke-width="1"/>`;
  s += label(940,289,'Self-Attn Target',10,'#1A237E','normal');
  s += hArr(820,175,870,'#3949AB');
  s += hArr(820,295,870,'#3949AB');

  // Output arrow
  s += `<line x1="1010" y1="240" x2="1040" y2="240" stroke="#455A64" stroke-width="2" marker-end="url(#arr)"/>`;
  s += label(1048,244,'Output',11,'#37474F','bold','start');

  // Gate equations (bottom)
  s += rect(30,450,980,60,'#FFF8E1','#E65100',8);
  s += label(520,468,'Gate Equations:  G_d = σ(W_g[h_d ∥ A_{d→p}]+b_g)  ·  h_d\' = G_d⊙A_{d→p} + (1−G_d)⊙h_d',12,'#BF360C','normal');
  s += label(520,492,'Symmetric for protein:  G_p = σ(W_g\'[h_p ∥ A_{p→d}]+b_g\')  ·  h_p\' = G_p⊙A_{p→d} + (1−G_p)⊙h_p',12,'#BF360C','normal');

  s += label(W/2,H-10,'Fig. 8. Gated Cross-Attention mechanism: bidirectional drug–protein attention with adaptive gates that balance cross-modal information with original representations.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig8_crossattn.png');
}

// ─── FIGURE 9: Network-Based DTI (like Sample Figs. 8–9) ───────────────────
export function fig9_network() {
  const W=1100, H=400;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  s += rect(0,0,W,36,'#1B5E20','none',0);
  s += label(W/2,18,'Fig. 9 — Network-Based DTI: Drug–Target Similarity Matrices → Interaction Prediction',14,'#FFFFFF','bold');

  // Drug similarity network
  s += rect(30,55,200,290,'#E3F2FD','#1565C0',10,'filter="url(#sh)"');
  s += label(130,72,'Drug Similarity\nNetwork',12,'#0D47A1','bold');
  const dn=[[80,130],[160,120],[120,170],[80,210],[160,200]];
  dn.forEach(([x,y],i)=>{
    s += `<circle cx="${x}" cy="${y}" r="18" fill="#1565C0" stroke="#0D47A1" stroke-width="1.5"/>`;
    s += label(x,y+4,`D${i+1}`,10,'#FFFFFF','bold');
  });
  [[0,1],[0,2],[1,3],[2,3],[3,4],[2,4]].forEach(([a,b])=>{
    s += lineP(dn[a][0],dn[a][1],dn[b][0],dn[b][1],'#90CAF9',true);
  });

  // Target similarity network
  s += rect(30,230,200,115,'#E8F5E9','#2E7D32',10,'filter="url(#sh)"');
  s += label(130,248,'Target Similarity\nNetwork',12,'#1B5E20','bold');
  const tn=[[80,285],[130,275],[180,290],[110,310],[160,305]];
  tn.forEach(([x,y],i)=>{
    s += `<circle cx="${x}" cy="${y}" r="16" fill="#2E7D32" stroke="#1B5E20" stroke-width="1.5"/>`;
    s += label(x,y+4,`T${i+1}`,10,'#FFFFFF','bold');
  });
  [[0,1],[1,2],[2,4],[3,4],[0,3]].forEach(([a,b])=>{
    s += lineP(tn[a][0],tn[a][1],tn[b][0],tn[b][1],'#A5D6A7',true);
  });

  // DTI matrix
  const mx=270, my=60, mw=220, mh=200;
  s += rect(mx,my,mw,mh,'#FFF3E0','#E65100',8,'filter="url(#sh)"');
  s += label(mx+mw/2,my+20,'Drug–Target Matrix  R(D,T)',12,'#BF360C','bold');
  // Mini matrix grid
  for(let r=0;r<5;r++) for(let c=0;c<5;c++){
    const gf=Math.random()>0.65?'#1565C0':'#E3F2FD';
    s += `<rect x="${mx+20+c*34}" y="${my+35+r*30}" width="30" height="26" rx="3" fill="${gf}" stroke="#90A4AE" stroke-width="0.5"/>`;
    if(gf==='#1565C0') s += label(mx+35+c*34,my+48+r*30,'1',9,'#FFFFFF','bold');
  }
  s += hArr(230,155,mx,'#E65100');
  s += hArr(230,280,mx,'#E65100');

  // GNN / DeepWalk
  s += box(540,100,160,90,'#1A237E',['GNN Encoding\n(GraphSAGE /\nDeepWalk)'],12,'#FFFFFF','#0D47A1',8);
  s += hArr(490,160,540,'#1A237E');

  // Known DTI + Prediction
  s += box(750,80,160,80,'#E65100',['Known DTI\nR(Di,Tj)'],12,'#FFFFFF','#BF360C',8);
  s += hArr(700,145,750,'#455A64');

  // Candidate targets
  s += rect(960,60,120,300,'#F3E5F5','#6A1B9A',10,'filter="url(#sh)"');
  s += label(1020,80,'Candidate\nTargets',12,'#4A148C','bold');
  ['T1','T2','T3','...','Tn'].forEach((t,i)=>{
    s += `<rect x="975" y="${102+i*46}" width="90" height="36" rx="6" fill="#6A1B9A" stroke="#4A148C" stroke-width="1"/>`;
    s += label(1020,120+i*46,t,13,'#FFFFFF','bold');
  });
  s += hArr(910,120,960,'#6A1B9A');

  // P(D,T) cloud
  s += `<ellipse cx="${mx+mw/2}" cy="320" rx="90" ry="35" fill="#B2DFDB" stroke="#00695C" stroke-width="2" filter="url(#sh)"/>`;
  s += label(mx+mw/2,325,'P(D,T)\nPredicted DTI',11,'#004D40','bold');
  s += vArr(mx+mw/2,my+mh,282,'#00695C');

  s += label(W/2,H-10,'Fig. 9. Network-based DTI prediction: Drug and target similarity networks feed into a drug–target matrix; GNN-based encoding predicts candidate interactions.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig9_network.png');
}

// ─── FIGURE 10: GAN-Based Data Augmentation (like Sample Fig. 15) ──────────
export function fig10_gan() {
  const W=1100, H=440;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  s += rect(0,0,W,36,'#880E4F','none',0);
  s += label(W/2,18,'Fig. 10 — GAN-Based Data Augmentation for DTI Cold-Start Mitigation',14,'#FFFFFF','bold');

  // Protein branch (top)
  [['Protein\n(Real Data)','#E8F5E9','#2E7D32',40,80],
   ['Real Protein\nSequence','#A5D6A7','#2E7D32',230,80],
  ].forEach(([t,f,c,x,y])=>{
    s += `<ellipse cx="${x+70}" cy="${y+35}" rx="70" ry="35" fill="${f}" stroke="${c}" stroke-width="2" filter="url(#sh)"/>`;
    s += label(x+70,y+39,t,11,c,'bold');
  });
  s += hArr(180,115,230,'#2E7D32','arrG');

  s += box(40,165,140,60,'#ECEFF1','Noise /\nLatent z',11,'#455A64','#90A4AE',8);
  s += box(230,165,140,60,'#1565C0','Generator\n(Drug/Prot)',12,'#FFFFFF','#0D47A1',8);
  s += box(430,165,140,60,'#B3D9F7','Generated\nProtein Seq.',11,'#0D47A1','#1565C0',8);
  s += hArr(180,195,230,'#455A64');
  s += hArr(370,195,430,'#1565C0','arrB');

  // Discriminator (protein)
  s += `<polygon points="600,60 760,60 760,230 600,230 640,145" fill="#F3E5F5" stroke="#6A1B9A" stroke-width="2" filter="url(#sh)"/>`;
  s += label(700,135,'Discriminator',12,'#4A148C','bold');
  s += label(700,155,'(Protein)',11,'#4A148C','bold');
  s += hArr(370,115,600,'#2E7D32','arrG');
  s += hArr(570,195,600,'#6A1B9A');
  // Real/Fake output
  s += box(800,80,150,50,'#C8E6C9','Real: ✓',13,'#1B5E20','#2E7D32',8);
  s += box(800,150,150,50,'#FFCDD2','Fake: ✗',13,'#B71C1C','#C62828',8);
  s += hArr(760,110,800,'#2E7D32','arrG');
  s += hArr(760,175,800,'#C62828');

  // Co-processing
  s += box(960,180,100,80,'#FF8A65','Co-\nProcessing\n(Fusion)',12,'#FFFFFF','#E64A19',8);
  s += hArr(950,200,960,'#455A64');

  // Drug branch (bottom)
  [['Drug\n(Real Data)','#E3F2FD','#1565C0',40,290],
   ['Real Drug\nSequence','#B3D9F7','#1565C0',230,290],
  ].forEach(([t,f,c,x,y])=>{
    s += `<ellipse cx="${x+70}" cy="${y+35}" rx="70" ry="35" fill="${f}" stroke="${c}" stroke-width="2" filter="url(#sh)"/>`;
    s += label(x+70,y+39,t,11,c,'bold');
  });
  s += hArr(180,325,230,'#1565C0','arrB');

  s += box(40,355,140,60,'#ECEFF1','Noise /\nLatent z',11,'#455A64','#90A4AE',8);
  s += box(230,355,140,60,'#1565C0','Generator\n(Drug/Prot)',12,'#FFFFFF','#0D47A1',8);
  s += box(430,355,140,60,'#B3D9F7','Generated\nDrug Seq.',11,'#0D47A1','#1565C0',8);
  s += hArr(180,385,230,'#455A64');
  s += hArr(370,385,430,'#1565C0','arrB');

  // Discriminator drug
  s += `<polygon points="600,290 760,290 760,420 600,420 640,355" fill="#BBDEFB" stroke="#1565C0" stroke-width="2" filter="url(#sh)"/>`;
  s += label(700,345,'Discriminator',12,'#0D47A1','bold');
  s += label(700,365,'(Drug)',11,'#0D47A1','bold');
  s += hArr(370,325,600,'#1565C0','arrB');
  s += hArr(570,385,600,'#1565C0','arrB');
  s += box(800,290,150,50,'#C8E6C9','Real: ✓',13,'#1B5E20','#2E7D32',8);
  s += box(800,360,150,50,'#FFCDD2','Fake: ✗',13,'#B71C1C','#C62828',8);
  s += hArr(760,315,800,'#2E7D32','arrG');
  s += hArr(760,385,800,'#C62828');
  s += hArr(950,350,960,'#455A64');

  // Output
  s += box(1010,215,80,130,'#E65100','Output\n\nDTI\nPred.',12,'#FFFFFF','#BF360C',8);
  s += hArr(1060,215,1060+0,'#E65100');

  s += label(W/2,H-8,'Fig. 10. GAN-based data augmentation for DTI cold-start mitigation. Generators produce realistic drug/protein sequences; discriminators enforce authenticity.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig10_gan.png');
}

// ─── FIGURE 11: Research Gaps Summary ──────────────────────────────────────
export function fig11_gaps() {
  const W=1200, H=420;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}`;
  s += rect(0,0,W,H,'#FAFAFA','none',0);
  s += rect(0,0,W,38,'#B71C1C','none',0);
  s += label(W/2,19,'Fig. 11 — Research Gaps and Open Challenges in DTI Prediction',15,'#FFFFFF','bold');

  const gaps=[
    ['Gap 1','Static Cross-Modal\nFusion','Most models use concatenation;\nno dynamic drug–protein\ninteraction modeling','#FFCDD2','#B71C1C'],
    ['Gap 2','Cold-Start\nGeneralization','Performance drops 10–15%\nfor unseen drugs (S2) and\ntargets (S3)','#FFCCBC','#BF360C'],
    ['Gap 3','Data Imbalance &\nNegative Sampling','Known positives vastly\noutnumbered; false negatives\nlead to model bias','#FFF9C4','#F57F17'],
    ['Gap 4','Interpretability &\nBiological Validation','Attention weights lack\nexperimental binding-site\nvalidation (<20% of models)','#C8E6C9','#1B5E20'],
    ['Gap 5','Benchmark\nInconsistency','Incomparable protocols\nacross papers; N/R values\ndominate (see Table 2)','#BBDEFB','#0D47A1'],
  ];

  const gw=210, gh=290, gy=58, gx=20;
  gaps.forEach(([num,title,desc,col,dark],i)=>{
    const x = gx+i*(gw+8);
    s += rect(x,gy,gw,gh,col,dark,10,'filter="url(#sh)"');
    // severity bar
    const bars = 5-i;
    for(let b=0;b<5;b++){
      s += `<rect x="${x+10+b*38}" y="${gy+10}" width="32" height="18" rx="4" fill="${b<bars?dark:'#ECEFF1'}" stroke="${dark}" stroke-width="1"/>`;
    }
    s += label(x+gw/2, gy+20, '', 9,'#FFFFFF','bold');
    s += `<circle cx="${x+gw/2}" cy="${gy+68}" r="28" fill="${dark}" stroke="none"/>`;
    s += label(x+gw/2, gy+73, num, 12,'#FFFFFF','bold');
    s += label(x+gw/2, gy+120, title, 13, dark,'bold');
    s += rect(x+10,gy+145,gw-20,105,'#FFFFFF',dark,6);
    desc.split('\n').forEach((line,li)=>{
      s += label(x+gw/2, gy+168+li*20, line, 11,'#37474F','normal');
    });
  });

  // Proposed solution arrow
  s += rect(30,370,1140,35,'#E8EAF6','#3949AB',8);
  s += label(600,388,'Proposed Solution (H-GNN-RNN-DTI): Gated Cross-Attn Fusion  ·  ESM-2+ChemBERTa Pretraining  ·  Focal Loss  ·  Attention-Based XAI  ·  Standardized Benchmarking',12,'#1A237E','bold');

  s += label(W/2,H-8,'Fig. 11. Five key research gaps identified across 36 reviewed DTI/DTA models, with the proposed H-GNN-RNN-DTI solution framework.',11,'#546E7A','normal');
  s += '</svg>';
  return render(s,'fig11_gaps.png');
}

// ─── Run all ─────────────────────────────────────────────────────────────────
console.log('Generating figures...');
fig1_framework();
fig2_mindmap();
fig3_architecture();
fig4_cnn();
fig5_gnn();
fig6_transformer();
fig7_kg();
fig8_crossattn();
fig9_network();
fig10_gan();
fig11_gaps();
console.log('All figures generated.');
