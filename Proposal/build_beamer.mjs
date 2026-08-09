// Generates the PhD proposal defense LaTeX Beamer deck from slide_content.mjs.
// Run: node build_beamer.mjs  ->  writes HGNN_RNN_DTI_Defense_Slides.tex
import fs from 'fs';
import { META, SLIDES } from './slide_content.mjs';

// ---- text -> LaTeX escaper (single pass, character-by-character, self-balanced) ----
const MAP = {
  '\\': '\\textbackslash{}',
  '$': '\\$', '&': '\\&', '%': '\\%', '#': '\\#', '_': '\\_', '{': '\\{', '}': '\\}', '^': '\\textasciicircum{}',
  '~': '\\(\\sim\\)',
  '—': '---', '–': '--', '…': '\\ldots{}',
  '→': '\\(\\rightarrow\\)', '↔': '\\(\\leftrightarrow\\)', '±': '\\(\\pm\\)',
  '√': '\\(\\surd\\)', '⊙': '\\(\\odot\\)', '∈': '\\(\\in\\)', 'ℝ': '\\(\\mathbb{R}\\)',
  '×': '\\(\\times\\)', '‖': '\\(\\Vert\\)', '²': '\\(^2\\)', '⁺': '\\(^{+}\\)',
  '·': '\\(\\cdot\\)', '’': "'", '‘': "'", '“': '"', '”': '"',
  '−': '-', '∫': '\\(\\int\\)', '∂': '\\(\\partial\\)', '∪': '\\(\\cup\\)',
  '₀': '\\(_0\\)', '¹': '\\(^1\\)', '½': '\\(\\tfrac{1}{2}\\)',
  'ŷ': '\\(\\hat{y}\\)', 'ĥ': '\\(\\hat{h}\\)', 'ȳ': '\\(\\bar{y}\\)', '←': '\\(\\leftarrow\\)',
  'Σ': '\\(\\Sigma\\)', 'α': '\\(\\alpha\\)', 'β': '\\(\\beta\\)', 'γ': '\\(\\gamma\\)',
  'σ': '\\(\\sigma\\)', 'τ': '\\(\\tau\\)', 'θ': '\\(\\theta\\)', 'η': '\\(\\eta\\)',
  'λ': '\\(\\lambda\\)', 'π': '\\(\\pi\\)',
};
const tex = (str) => [...String(str)].map(ch => (MAP[ch] !== undefined ? MAP[ch] : ch)).join('');

function itemize(items, opts = {}) {
  const size = opts.size || '\\normalsize';
  let out = `{${size}\n\\begin{itemize}\n`;
  let openSub = false;
  items.forEach((b) => {
    const [text, lvl] = Array.isArray(b) ? b : [b, 0];
    if (lvl > 0 && !openSub) { out += '\\begin{itemize}\n'; openSub = true; }
    if (lvl === 0 && openSub) { out += '\\end{itemize}\n'; openSub = false; }
    out += `\\item ${tex(text)}\n`;
  });
  if (openSub) out += '\\end{itemize}\n';
  out += '\\end{itemize}\n}\n';
  return out;
}

function eqBox(eqs) {
  const lines = eqs.map(e => e.t).join(' \\\\\n');
  return `\\begin{tcolorbox}[colback=DTIpanel, colframe=DTIgold, boxrule=0.6pt, arc=2pt, left=8pt, right=8pt, top=5pt, bottom=5pt]\n\\begin{gather*}\n${lines}\n\\end{gather*}\n\\end{tcolorbox}\n`;
}

function tableBlock(tbl) {
  const nCols = tbl.head.length;
  const spec = nCols === 3 ? 'p{2.6cm} p{4.0cm} p{4.9cm}' : 'p{2.2cm} p{2.6cm} p{2.6cm} p{2.6cm}';
  let out = `{\\footnotesize\n\\renewcommand{\\arraystretch}{1.35}\n\\begin{center}\n\\begin{tabular}{${spec}}\n\\rowcolor{DTInavy}\n`;
  out += tbl.head.map(h => `\\textcolor{white}{\\textbf{${tex(h)}}}`).join(' & ') + ' \\\\\n';
  tbl.rows.forEach((r, ri) => {
    out += `\\rowcolor{${ri % 2 === 0 ? 'white' : 'DTIpanel'}}\n`;
    out += r.map((c, ci) => (ci === 0 ? `\\textcolor{DTIteal}{\\textbf{${tex(c)}}}` : tex(c))).join(' & ') + ' \\\\\n';
  });
  out += '\\end{tabular}\n\\end{center}\n}\n';
  return out;
}

function colsBlock(cols) {
  const box = (data, accent, bg) => {
    let s = `\\begin{tcolorbox}[colback=${bg}, colframe=${accent}, coltitle=white, colbacktitle=${accent}, title=${tex(data.h)}, fonttitle=\\bfseries, arc=2pt, boxrule=0.6pt]\n`;
    s += `{\\footnotesize\n\\begin{itemize}\n`;
    data.items.forEach(it => { s += `\\item ${tex(it)}\n`; });
    s += `\\end{itemize}\n}\n\\end{tcolorbox}\n`;
    return s;
  };
  return `\\begin{columns}[t]\n\\begin{column}{0.49\\linewidth}\n${box(cols.l, 'DTIteal', 'DTIlteal')}\\end{column}\n\\begin{column}{0.49\\linewidth}\n${box(cols.r, 'DTIred', 'DTIlred')}\\end{column}\n\\end{columns}\n`;
}

function contentFrame(s) {
  let body = '';
  if (s.tbl) body = tableBlock(s.tbl);
  else if (s.cols) body = colsBlock(s.cols);
  else if (s.bullets && s.eqs) body = itemize(s.bullets, { size: '\\small' }) + '\\vspace{2mm}\n' + eqBox(s.eqs);
  else if (s.eqs) body = eqBox(s.eqs);
  else if (s.bullets) body = itemize(s.bullets);

  const kicker = s.sec ? `\\framesubtitle{\\textcolor{DTIgold}{\\MakeUppercase{${tex(s.sec)}}}}\n` : '';
  return `\\begin{frame}{${tex(s.title)}}\n${kicker}${body}\\note{${tex(s.notes || '')}}\n\\end{frame}\n\n`;
}

// ------------------------------------------------------------------ document
let doc = `% H-GNN-RNN-DTI PhD Proposal Defense — LaTeX Beamer deck
% Auto-generated from slide_content.mjs — do not hand-edit generated equations/bullets there; edit the source and rebuild.
%
% SPEAKER NOTES: every frame carries \\note{...} talking points (hidden by default).
% To compile a presenter-view PDF with notes shown beside each slide, uncomment the two
% lines below and recompile:
% \\usepackage{pgfpages}
% \\setbeameroption{show notes on second screen=right}

\\documentclass[aspectratio=169,10pt]{beamer}
\\usepackage[T1]{fontenc}
\\usepackage[utf8]{inputenc}
\\usepackage{lmodern}
\\usepackage{amsmath,amssymb}
\\usepackage[table]{xcolor}
\\usepackage{tcolorbox}
\\usepackage{booktabs}
\\usepackage{array}
\\usepackage{hyperref}

\\definecolor{DTInavy}{HTML}{0B2545}
\\definecolor{DTIteal}{HTML}{0E7C7B}
\\definecolor{DTIgold}{HTML}{C9962C}
\\definecolor{DTIslate}{HTML}{20293A}
\\definecolor{DTIgray}{HTML}{667085}
\\definecolor{DTIpanel}{HTML}{EEF2F6}
\\definecolor{DTIred}{HTML}{B3261E}
\\definecolor{DTIlteal}{HTML}{E3F2F1}
\\definecolor{DTIlred}{HTML}{FBEAEA}

\\usetheme{default}
\\setbeamertemplate{navigation symbols}{}
\\setbeamercolor{frametitle}{bg=DTInavy, fg=white}
\\setbeamerfont{frametitle}{size=\\large\\bfseries}
\\setbeamercolor{framesubtitle}{fg=DTIgold}
\\setbeamercolor{structure}{fg=DTIteal}
\\setbeamercolor{itemize item}{fg=DTIgold}
\\setbeamercolor{itemize subitem}{fg=DTIteal}
\\setbeamertemplate{itemize item}{\\textcolor{DTIgold}{\\scriptsize\\ensuremath{\\blacksquare}}}
\\setbeamertemplate{itemize subitem}{\\textcolor{DTIteal}{--}}
\\setbeamercolor{normal text}{fg=DTIslate}
\\setbeamertemplate{footline}{%
  \\leavevmode
  \\hbox{\\begin{beamercolorbox}[wd=\\paperwidth,ht=2.6ex,dp=1ex,leftskip=.4cm,rightskip=.4cm]{normal text}
    {\\footnotesize\\color{DTIgray}\\textit{${tex(META.shortTitle)} --- PhD Proposal Defense}\\hfill{\\footnotesize\\color{DTInavy}\\bfseries\\insertframenumber\\,/\\,\\inserttotalframenumber}}
  \\end{beamercolorbox}}
}

\\title{${tex(META.title)}}
\\author{${tex(META.presenter)}}
\\institute{${tex(META.school)}}
\\date{}

\\begin{document}

`;

// ---- Title frame
{
  const s = SLIDES[0];
  doc += `{\\setbeamercolor{background canvas}{bg=DTInavy}
\\begin{frame}[plain,c]
\\begin{center}
{\\color{DTIgold}\\rule{0.9\\linewidth}{1.2pt}}\\\\[10pt]
{\\small\\color{white}\\MakeUppercase{Universiti Sains Malaysia}}\\\\[2pt]
{\\footnotesize\\color{DTIgold!70!white}${tex(META.school)}}\\\\[14pt]
{\\bfseries\\small\\color{DTIgold}\\MakeUppercase{${tex(META.program)}}}\\\\[16pt]
{\\Large\\bfseries\\color{white}${tex(META.title)}}\\\\[22pt]
\\begin{tcolorbox}[colback=DTInavy, colframe=DTIgold, coltext=white, width=0.72\\linewidth, arc=3pt, boxrule=0.8pt]
\\centering
\\textbf{${tex(META.presenter)}}\\\\[2pt]
{\\footnotesize Matric No. ${tex(META.matric)}}\\\\[2pt]
{\\footnotesize Supervisor: ${tex(META.supervisor)}}
\\end{tcolorbox}
\\vspace{10pt}
{\\color{DTIgold}\\rule{0.9\\linewidth}{1.2pt}}
\\end{center}
\\note{${tex(s.notes)}}
\\end{frame}
}

`;
}

// ---- Content frames
SLIDES.forEach((s) => {
  if (s.layout === 'title' || s.layout === 'closing') return;
  doc += contentFrame(s);
});

// ---- Closing frame
{
  const s = SLIDES[SLIDES.length - 1];
  doc += `{\\setbeamercolor{background canvas}{bg=DTInavy}
\\begin{frame}[plain,c]
\\begin{center}
{\\Huge\\bfseries\\color{white}Thank You}\\\\[10pt]
{\\Large\\color{DTIgold}Questions \\& Discussion}\\\\[18pt]
{\\color{DTIgold}\\rule{0.5\\linewidth}{1pt}}\\\\[14pt]
{\\bfseries\\color{white}${tex(META.presenter)}}\\\\[2pt]
{\\footnotesize\\color{DTIgold!70!white}${tex(META.supervisor)}}\\\\[2pt]
{\\footnotesize\\color{white!70!DTInavy}${tex(META.school)}}
\\end{center}
\\note{${tex(s.notes)}}
\\end{frame}
}

\\end{document}
`;
}

const outPath = new URL('./HGNN_RNN_DTI_Defense_Slides.tex', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
fs.writeFileSync(outPath, doc, 'utf8');
console.log('Wrote', outPath, '-', SLIDES.length, 'slides');
