// Generates the PhD proposal defense PPTX deck from slide_content.mjs.
// Run: node build_pptx.mjs
import PptxGenJS from 'pptxgenjs';
import { META, SLIDES } from './slide_content.mjs';

const C = {
  navy: '0B2545', teal: '0E7C7B', gold: 'C9962C', slate: '20293A',
  panel: 'EEF2F6', gray: '667085', red: 'B3261E', white: 'FFFFFF',
  lteal: 'E3F2F1', lgold: 'FBF1DE', navySoft: '17335A',
};
const F = 'Calibri';
const MONO = 'Consolas';
const SW = 13.333, SH = 7.5;

const pptx = new PptxGenJS();
pptx.defineLayout({ name: 'DEFENSE_16x9', width: SW, height: SH });
pptx.layout = 'DEFENSE_16x9';
pptx.author = META.presenter;
pptx.title = META.title;

// content slides only (title/closing handled separately) -> used for numbering & section footer
const contentSlides = SLIDES.filter(s => s.layout !== 'title' && s.layout !== 'closing');
const totalPages = SLIDES.length;

function addHeader(sl, kicker, title) {
  sl.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.16, h: SH, fill: { color: C.teal } });
  if (kicker) sl.addText(kicker.toUpperCase(), {
    x: 0.5, y: 0.32, w: SW - 1.0, h: 0.32, fontSize: 12.5, bold: true, color: C.gold,
    fontFace: F, charSpacing: 1.2,
  });
  sl.addText(title, {
    x: 0.5, y: 0.62, w: SW - 1.0, h: 0.82, fontSize: 25, bold: true, color: C.navy,
    fontFace: F, valign: 'top', wrap: true,
  });
  sl.addShape(pptx.ShapeType.line, {
    x: 0.5, y: 1.5, w: SW - 1.0, h: 0, line: { color: C.gold, width: 1.5 },
  });
}

function addFooter(sl, pageNo, section) {
  sl.addShape(pptx.ShapeType.line, { x: 0.5, y: SH - 0.42, w: SW - 1.0, h: 0, line: { color: 'D5DCE3', width: 0.75 } });
  sl.addText(section || META.shortTitle, {
    x: 0.5, y: SH - 0.38, w: SW - 2.2, h: 0.3, fontSize: 9.5, italic: true, color: C.gray, fontFace: F,
  });
  sl.addText(`${pageNo} / ${totalPages}`, {
    x: SW - 1.5, y: SH - 0.38, w: 1.0, h: 0.3, fontSize: 9.5, bold: true, color: C.navy, fontFace: F, align: 'right',
  });
}

function bulletTextObjs(bullets, opts = {}) {
  return bullets.map((b, i) => {
    const [text, lvl] = Array.isArray(b) ? b : [b, 0];
    return {
      text,
      options: {
        bullet: { code: lvl > 0 ? '2013' : '25AA', indent: 14 },
        indentLevel: lvl,
        fontSize: opts.fontSize || (lvl > 0 ? 12 : 13.5),
        color: lvl > 0 ? C.gray : C.slate,
        breakLine: true,
        paraSpaceAfter: opts.spaceAfter || 10,
        fontFace: F,
      },
    };
  });
}

function addBullets(sl, bullets, { x, y, w, h, fontSize } = {}) {
  sl.addText(bulletTextObjs(bullets, { fontSize }), { x, y, w, h, valign: 'top' });
}

function addEquations(sl, eqs, { x, y, w, boxH } = {}) {
  const gap = 0.13;
  const eqH = Math.max(0.56, Math.min(1.05, (boxH - (eqs.length - 1) * gap) / eqs.length));
  let cy = y;
  eqs.forEach(eq => {
    sl.addShape(pptx.ShapeType.roundRect, {
      x, y: cy, w, h: eqH, rectRadius: 0.06, fill: { color: C.panel }, line: { color: 'D5DCE3', width: 0.75 },
    });
    sl.addShape(pptx.ShapeType.rect, { x, y: cy, w: 0.06, h: eqH, fill: { color: C.gold } });
    sl.addText(eq.p, {
      x: x + 0.22, y: cy, w: w - 0.4, h: eqH, fontSize: 13, color: C.slate, fontFace: MONO,
      valign: 'middle', wrap: true, shrinkText: true,
    });
    cy += eqH + gap;
  });
  return cy;
}

function addTable(sl, tbl, { x, y, w, h } = {}) {
  const nCols = tbl.head.length;
  const firstColW = w * (nCols === 3 ? 0.24 : 0.20);
  const lastColW = w * (nCols === 3 ? 0.42 : 0.30);
  const midW = (w - firstColW - lastColW) / Math.max(1, nCols - 2);
  const colW = nCols === 3 ? [firstColW, w - firstColW - lastColW, lastColW]
    : tbl.head.map((_, i) => (i === 0 ? firstColW : i === nCols - 1 ? lastColW : midW));

  const headerRow = tbl.head.map(hcell => ({
    text: hcell, options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 12, fontFace: F, valign: 'middle', align: 'left' },
  }));
  const rows = [headerRow];
  tbl.rows.forEach((r, ri) => {
    rows.push(r.map((cell, ci) => ({
      text: cell,
      options: {
        fill: { color: ri % 2 === 0 ? C.white : C.panel },
        color: ci === 0 ? C.teal : C.slate,
        bold: ci === 0,
        fontSize: 11, fontFace: F, valign: 'middle', align: 'left', margin: [4, 6, 4, 6],
      },
    })));
  });
  sl.addTable(rows, { x, y, w, h, colW, autoPage: false, border: { type: 'solid', color: 'D5DCE3', pt: 0.5 } });
}

function addTwoCol(sl, cols, { x, y, w, h } = {}) {
  const gap = 0.35;
  const colW = (w - gap) / 2;
  [['l', C.teal, C.lteal], ['r', C.red, 'FBEAEA']].forEach(([key, accent, bg], i) => {
    const cx = x + i * (colW + gap);
    const data = cols[key];
    sl.addShape(pptx.ShapeType.roundRect, { x: cx, y, w: colW, h, rectRadius: 0.07, fill: { color: bg }, line: { color: accent, width: 1 } });
    sl.addShape(pptx.ShapeType.rect, { x: cx, y, w: colW, h: 0.46, fill: { color: accent } });
    sl.addText(data.h, { x: cx + 0.15, y, w: colW - 0.3, h: 0.46, fontSize: 14, bold: true, color: C.white, fontFace: F, valign: 'middle' });
    sl.addText(bulletTextObjs(data.items, { fontSize: 11.5, spaceAfter: 8 }), {
      x: cx + 0.2, y: y + 0.58, w: colW - 0.4, h: h - 0.75, valign: 'top',
    });
  });
}

// ---------------------------------------------------------------- TITLE SLIDE
{
  const sl = pptx.addSlide();
  sl.background = { color: C.navy };
  sl.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: SW, h: 0.14, fill: { color: C.gold } });
  sl.addShape(pptx.ShapeType.rect, { x: 0, y: SH - 0.14, w: SW, h: 0.14, fill: { color: C.gold } });
  sl.addText('UNIVERSITI SAINS MALAYSIA', { x: 0.5, y: 0.75, w: SW - 1.0, h: 0.4, fontSize: 15, color: 'AFC8E8', fontFace: F, align: 'center', charSpacing: 2 });
  sl.addText(META.school.toUpperCase().replace('UNIVERSITI SAINS MALAYSIA', '').replace(/^, /, ''), {
    x: 0.5, y: 1.12, w: SW - 1.0, h: 0.36, fontSize: 13, color: '8FB0DA', fontFace: F, align: 'center',
  });
  sl.addShape(pptx.ShapeType.line, { x: SW / 2 - 1.0, y: 1.65, w: 2.0, h: 0, line: { color: C.gold, width: 1.5 } });
  sl.addText(META.program.toUpperCase(), { x: 0.5, y: 1.85, w: SW - 1.0, h: 0.4, fontSize: 13, bold: true, color: C.gold, fontFace: F, align: 'center', charSpacing: 1.5 });
  sl.addText(META.title, {
    x: 1.0, y: 2.55, w: SW - 2.0, h: 2.0, fontSize: 30, bold: true, color: C.white, fontFace: F, align: 'center', valign: 'middle', wrap: true,
  });
  sl.addShape(pptx.ShapeType.roundRect, { x: SW / 2 - 3.6, y: 4.85, w: 7.2, h: 1.55, rectRadius: 0.08, fill: { color: C.navySoft }, line: { color: C.gold, width: 1 } });
  sl.addText([
    { text: META.presenter, options: { bold: true, fontSize: 15, color: C.white, breakLine: true, align: 'center' } },
    { text: `Matric No. ${META.matric}`, options: { fontSize: 11.5, color: 'AFC8E8', breakLine: true, align: 'center' } },
    { text: `Supervisor: ${META.supervisor}`, options: { fontSize: 11.5, color: 'AFC8E8', breakLine: false, align: 'center' } },
  ], { x: SW / 2 - 3.4, y: 4.98, w: 6.8, h: 1.3, fontFace: F, valign: 'middle' });
  sl.addText(META.school, { x: 0.5, y: SH - 0.62, w: SW - 1.0, h: 0.35, fontSize: 10.5, color: '7FA0C9', fontFace: F, align: 'center', italic: true });
  sl.addNotes(SLIDES[0].notes);
}

// ---------------------------------------------------------------- CONTENT SLIDES
let pageNo = 1;
SLIDES.forEach((s) => {
  if (s.layout === 'title' || s.layout === 'closing') return;
  pageNo += 1;
  const sl = pptx.addSlide();
  sl.background = { color: C.white };
  addHeader(sl, s.sec, s.title);

  const cx = 0.5, cTop = 1.72, cBottom = SH - 0.55, cw = SW - 1.0;

  if (s.tbl) {
    addTable(sl, s.tbl, { x: cx, y: cTop + 0.05, w: cw, h: cBottom - cTop - 0.05 });
  } else if (s.cols) {
    addTwoCol(sl, s.cols, { x: cx, y: cTop + 0.05, w: cw, h: cBottom - cTop - 0.05 });
  } else if (s.bullets && s.eqs) {
    const bulletsH = Math.min(1.9, s.bullets.length * 0.44 + 0.15);
    addBullets(sl, s.bullets, { x: cx, y: cTop, w: cw, h: bulletsH, fontSize: 13 });
    const eqY = cTop + bulletsH + 0.12;
    addEquations(sl, s.eqs, { x: cx, y: eqY, w: cw, boxH: cBottom - eqY });
  } else if (s.eqs) {
    addEquations(sl, s.eqs, { x: cx, y: cTop + 0.1, w: cw, boxH: cBottom - cTop - 0.1 });
  } else if (s.bullets) {
    addBullets(sl, s.bullets, { x: cx, y: cTop + 0.15, w: cw, h: cBottom - cTop - 0.15, fontSize: 14.5 });
  }

  addFooter(sl, pageNo, s.sec);
  sl.addNotes(s.notes || '');
});

// ---------------------------------------------------------------- CLOSING SLIDE
{
  const sl = pptx.addSlide();
  sl.background = { color: C.navy };
  sl.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: SW, h: 0.14, fill: { color: C.gold } });
  sl.addShape(pptx.ShapeType.rect, { x: 0, y: SH - 0.14, w: SW, h: 0.14, fill: { color: C.gold } });
  sl.addText('Thank You', { x: 0.5, y: 2.3, w: SW - 1.0, h: 1.1, fontSize: 44, bold: true, color: C.white, fontFace: F, align: 'center' });
  sl.addText('Questions & Discussion', { x: 0.5, y: 3.35, w: SW - 1.0, h: 0.6, fontSize: 20, color: C.gold, fontFace: F, align: 'center' });
  sl.addShape(pptx.ShapeType.line, { x: SW / 2 - 1.0, y: 4.15, w: 2.0, h: 0, line: { color: C.gold, width: 1.5 } });
  sl.addText([
    { text: META.presenter, options: { bold: true, fontSize: 14, color: C.white, breakLine: true, align: 'center' } },
    { text: META.supervisor, options: { fontSize: 11.5, color: 'AFC8E8', breakLine: true, align: 'center' } },
    { text: META.school, options: { fontSize: 11, color: '7FA0C9', italic: true, align: 'center' } },
  ], { x: 1.0, y: 4.4, w: SW - 2.0, h: 1.0, fontFace: F, align: 'center' });
  sl.addNotes(SLIDES[SLIDES.length - 1].notes);
}

const outPath = new URL('./HGNN_RNN_DTI_Defense_Slides.pptx', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
await pptx.writeFile({ fileName: outPath });
console.log('Wrote', outPath, '-', SLIDES.length, 'slides');
