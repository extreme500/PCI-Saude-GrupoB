// Converte projeto/PROJETO-CICLO2.md em .docx com a formatacao do guia da
// disciplina: titulo e cabecalhos de secao em azul, corpo justificado,
// referencias com recuo deslocado (ABNT).
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  BorderStyle, Table, TableRow, TableCell, WidthType, ShadingType,
  LevelFormat, convertInchesToTwip,
} = require('docx');

const AZUL_TITULO = '1F4E79';
const AZUL_SECAO  = '2E74B5';
const FONTE = 'Calibri';

const md = fs.readFileSync(process.argv[2], 'utf8');
const saida = process.argv[3];

// ---------- inline: **negrito** e *italico* ----------
function runs(txt, base = {}) {
  const out = [];
  txt.split('**').forEach((parte, i) => {
    const negrito = i % 2 === 1;
    parte.split('*').forEach((sub, j) => {
      if (!sub) return;
      out.push(new TextRun({
        text: sub, bold: negrito || base.bold, italics: j % 2 === 1,
        font: FONTE, size: base.size || 22, color: base.color,
      }));
    });
  });
  return out.length ? out : [new TextRun({ text: '', font: FONTE, size: 22 })];
}

const corpo = (txt, extra = {}) => new Paragraph({
  children: runs(txt),
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 160, line: 276 },
  ...extra,
});

// ---------- blocos ----------
const linhas = md.split('\n');
const blocos = [];
let buf = [];
for (const l of linhas) {
  if (l.trim() === '') { if (buf.length) { blocos.push(buf); buf = []; } }
  else buf.push(l);
}
if (buf.length) blocos.push(buf);

const filhos = [];
let titulo = null, secaoAtual = '';

for (const bloco of blocos) {
  const primeira = bloco[0].trim();

  if (primeira === '---') continue;

  // titulo do documento
  if (primeira.startsWith('# ') && !titulo) {
    titulo = primeira.slice(2);
    filhos.push(new Paragraph({
      children: [new TextRun({ text: titulo, bold: true, font: FONTE, size: 40, color: AZUL_TITULO })],
      spacing: { after: 200 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: AZUL_SECAO, space: 8 } },
    }));
    continue;
  }

  // cabecalho de secao
  if (primeira.startsWith('## ')) {
    secaoAtual = primeira.slice(3);
    filhos.push(new Paragraph({
      children: [new TextRun({ text: secaoAtual, bold: true, font: FONTE, size: 28, color: AZUL_SECAO })],
      heading: HeadingLevel.HEADING_1,
      spacing: { before: 360, after: 180 },
    }));
    continue;
  }

  // tabela
  if (primeira.startsWith('|')) {
    const linhasTab = bloco.filter(l => !/^\|[\s:|-]+\|$/.test(l.trim()));
    const dados = linhasTab.map(l =>
      l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));
    const larguras = [2100, 6926];
    filhos.push(new Table({
      columnWidths: larguras,
      width: { size: 9026, type: WidthType.DXA },
      rows: dados.map((cels, i) => new TableRow({
        children: cels.map((c, j) => new TableCell({
          width: { size: larguras[j], type: WidthType.DXA },
          shading: i === 0 ? { type: ShadingType.CLEAR, fill: 'DEEAF6' } : undefined,
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: runs(c, { bold: i === 0, size: 20 }),
            alignment: AlignmentType.LEFT,
            spacing: { after: 0, line: 260 },
          })],
        })),
      })),
    }));
    filhos.push(new Paragraph({ text: '', spacing: { after: 120 } }));
    continue;
  }

  // lista numerada: cada item pode ocupar varias linhas
  if (/^\d+\.\s/.test(primeira)) {
    const itens = [];
    for (const l of bloco) {
      if (/^\d+\.\s/.test(l.trim())) itens.push(l.trim().replace(/^\d+\.\s/, ''));
      else if (itens.length) itens[itens.length - 1] += ' ' + l.trim();
    }
    itens.forEach(it => filhos.push(new Paragraph({
      children: runs(it),
      numbering: { reference: 'objetivos', level: 0 },
      alignment: AlignmentType.JUSTIFIED,
      spacing: { after: 120, line: 276 },
    })));
    continue;
  }

  // paragrafo comum (as linhas do .md sao quebradas por largura)
  const texto = bloco.map(l => l.trim()).join(' ');

  // cabecalho de autoria: linhas logo apos o titulo, sem justificar
  if (filhos.length <= 1) {
    bloco.forEach(l => filhos.push(new Paragraph({
      children: runs(l.trim(), { size: 22 }),
      spacing: { after: 60 },
    })));
    continue;
  }

  // referencias: recuo deslocado
  const ehReferencia = secaoAtual.startsWith('9.');
  filhos.push(new Paragraph({
    children: runs(texto),
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: ehReferencia ? 140 : 160, line: 276 },
    ...(ehReferencia ? { indent: { left: convertInchesToTwip(0.5), hanging: convertInchesToTwip(0.5) } } : {}),
  }));
}

const doc = new Document({
  creator: 'Grupo B - INF99003',
  title: titulo,
  numbering: {
    config: [{
      reference: 'objetivos',
      levels: [{
        level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.START,
        style: { paragraph: { indent: { left: 460, hanging: 320 } } },
      }],
    }],
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children: filhos,
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(saida, b);
  console.log('gerado:', saida, '(' + b.length + ' bytes)');
});
