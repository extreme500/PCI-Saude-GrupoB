// Deck do Ciclo 2, baseado no documento de planejamento.
// Paleta "Creme" pedida pelo grupo. Gradiente entra como imagem de fundo,
// porque pptxgenjs nao suporta preenchimento em gradiente.
const pptxgen = require("pptxgenjs");
const path = require("path");

const FUNDO = path.join(__dirname, "fundo-creme.png");
const SAIDA = process.argv[2];

const THEME = {
  name: "Creme",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "33291F", lt1: "FEFCF7", dk2: "5C4F41", lt2: "F2E7D2",
    accent1: "B35C38", accent2: "4A6B5B", accent3: "8A7A67",
    accent4: "E8D8BC", accent5: "F3DFD3", accent6: "DDE7E0",
    hlink: "B35C38", folHlink: "8A7A67",
  },
};

const TINTA = "33291F", TINTA70 = "5C4F41", TINTA45 = "8A7A67";
const TERRA = "B35C38", SAGE = "4A6B5B";
const CARTAO = "FFFDF8", TERRA_SUAVE = "F3DFD3", SAGE_SUAVE = "DDE7E0";

const M = 0.75;                 // margem lateral
const W = 13.333 - M * 2;       // largura util
const SOMBRA = () => ({ type: "outer", color: "33291F", blur: 10,
                        offset: 2, angle: 90, opacity: 0.1 });

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Grupo B";
pres.title = "Protocolos legais em visitas domiciliares de ACS";

pres.defineSlideMaster({
  title: "BASE",
  background: { path: FUNDO },
  objects: [
    { text: { text: "INF99003 · Ciclo 2 · Grupo B",
              options: { x: M, y: 6.92, w: 5, h: 0.3, fontSize: 10,
                         color: TINTA45, charSpacing: 1, isTextBox: true } } },
    { text: { text: " ", options: { x: 12.1, y: 6.92, w: 0.5, h: 0.3,
                                    fontSize: 10, color: TINTA45,
                                    align: "right", isTextBox: true } } },
  ],
  slideNumber: { x: 12.45, y: 6.92, w: 0.4, h: 0.3, fontSize: 10,
                 color: TINTA45, align: "right" },
});

pres.defineSlideMaster({ title: "CAPA", background: { path: FUNDO } });

// ---------------------------------------------------------------- utilidades
function etiqueta(s, texto) {
  s.addText(texto.toUpperCase(), {
    x: M, y: 0.46, w: W, h: 0.3, fontSize: 11, bold: true, color: TERRA,
    charSpacing: 2.2, isTextBox: true, margin: 0,
  });
}

function titulo(s, texto, opc = {}) {
  s.addText(texto, {
    x: M, y: 0.82, w: opc.w || W, h: opc.h || 0.95, fontSize: opc.fontSize || 34,
    bold: true, color: TINTA, fontFace: "Cambria", valign: "top",
    isTextBox: true, margin: 0, lineSpacing: opc.lineSpacing || 38,
  });
}

function cartao(s, o) {
  s.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.1,
    fill: { color: o.fundo || CARTAO }, line: { color: "E6DCCB", width: 0.75 },
    shadow: SOMBRA(), objectName: o.nome,
  });
  let cursor = o.y + 0.22;
  if (o.rotulo) {
    s.addText(o.rotulo, {
      x: o.x + 0.26, y: cursor, w: o.w - 0.52, h: 0.3, fontSize: 12.5,
      bold: true, color: o.corRotulo || TERRA, charSpacing: 1,
      isTextBox: true, margin: 0,
    });
    cursor += 0.36;
  }
  if (o.titulo) {
    s.addText(o.titulo, {
      x: o.x + 0.26, y: cursor, w: o.w - 0.52, h: o.alturaTitulo || 0.42,
      fontSize: o.tamTitulo || 17, bold: true, color: TINTA,
      fontFace: "Cambria", isTextBox: true, margin: 0, lineSpacing: 21,
    });
    cursor += (o.alturaTitulo || 0.42) + 0.08;
  }
  if (o.corpo) {
    s.addText(o.corpo, {
      x: o.x + 0.26, y: cursor, w: o.w - 0.52, h: o.y + o.h - cursor - 0.18,
      fontSize: o.tamCorpo || 13.5, color: TINTA70, isTextBox: true,
      margin: 0, lineSpacing: o.entrelinha || 17, valign: "top",
    });
  }
}

// O fecho de cada slide muda de forma de propósito, para que a conclusao nao
// vire um rodape repetido. Tres variantes: faixa, linha solta e destaque.
function fechoFaixa(s, y, texto, verde) {
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y, w: W, h: 0.78, rectRadius: 0.09,
    fill: { color: verde ? SAGE_SUAVE : TERRA_SUAVE }, line: { type: "none" },
    objectName: "fecho",
  });
  s.addText(texto, {
    x: M + 0.3, y: y + 0.08, w: W - 0.6, h: 0.62, fontSize: 15.5,
    color: TINTA, fontFace: "Cambria", italic: true, valign: "middle",
    isTextBox: true, margin: 0, lineSpacing: 19,
  });
}

function fechoLinha(s, y, texto) {
  s.addText(texto, {
    x: M, y, w: W, h: 0.6, fontSize: 17, color: TINTA, fontFace: "Cambria",
    bold: true, isTextBox: true, margin: 0, lineSpacing: 21,
  });
}

const sec = (t) => pres.addSection({ title: t });

// =============================================================== 1. CAPA
sec("Abertura");
{
  const s = pres.addSlide({ masterName: "CAPA", sectionTitle: "Abertura" });
  s.addText("PROJETO EM CIÊNCIA E INOVAÇÃO · INF99003 · CICLO 2", {
    x: 1.0, y: 1.35, w: 11.3, h: 0.3, fontSize: 11.5, bold: true,
    color: TERRA, charSpacing: 2.2, isTextBox: true, margin: 0,
  });
  s.addText("Planejamento Automatizado para o\ncumprimento de protocolos legais", {
    x: 1.0, y: 1.85, w: 11.3, h: 1.75, fontSize: 40, bold: true, color: TINTA,
    fontFace: "Cambria", isTextBox: true, margin: 0, lineSpacing: 46,
  });
  s.addText("Visitas domiciliares de Agentes Comunitários de Saúde na Atenção Primária do SUS", {
    x: 1.0, y: 3.72, w: 10.2, h: 0.5, fontSize: 16.5, color: TINTA70,
    isTextBox: true, margin: 0,
  });
  s.addShape(pres.ShapeType.rect, {
    x: 1.0, y: 4.65, w: 2.1, h: 0.025, fill: { color: "D9C4A1" },
    line: { type: "none" }, objectName: "divisor-capa",
  });
  s.addText("Gabriel Pieruccini Knopp   ·   Arthur Andrade da Silva   ·   Izadora Candotti de Oliveira", {
    x: 1.0, y: 4.95, w: 11.3, h: 0.4, fontSize: 15, bold: true, color: TINTA,
    fontFace: "Cambria", isTextBox: true, margin: 0,
  });
  s.addText("Grupo B   ·   Instituto de Informática, UFRGS", {
    x: 1.0, y: 5.38, w: 11.3, h: 0.35, fontSize: 12.5, color: TINTA45,
    isTextBox: true, margin: 0,
  });
  s.addNotes("Abertura. O enunciado do ciclo pede um artefato que facilite o "
    + "planejamento das visitas dos ACS. Quase todo mundo vai atacar isso como "
    + "problema de rota. Nos tambem, mas descobrimos que a rota e so metade do "
    + "problema. Nao mencione PDDL ainda.");
}

// ======================================================== 2. O PROBLEMA
sec("O problema");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "O problema" });
  etiqueta(s, "Contextualização");
  titulo(s, "Chegar na casa certa não autoriza o atendimento");

  cartao(s, { x: M, y: 2.0, w: 5.8, h: 2.35, nome: "trad",
    rotulo: "COMO O PROBLEMA COSTUMA SER TRATADO", corRotulo: TINTA45,
    titulo: "Um problema de percurso",
    corpo: "Minimizar deslocamento, cobrir o território no prazo e respeitar a "
         + "capacidade da equipe. É o que roteirizadores já resolvem bem." });

  cartao(s, { x: M + 6.03, y: 2.0, w: 5.8, h: 2.35, nome: "falta",
    rotulo: "O QUE ESSA FORMULAÇÃO DEIXA DE FORA", corRotulo: TERRA,
    titulo: "A norma que rege o atendimento",
    corpo: "A Lei 11.350/2006 condiciona o que o agente pode fazer em cada "
         + "residência. Nem toda condição é estática: insumo e supervisão se "
         + "esgotam ao longo do turno." });

  fechoFaixa(s, 4.72, "A pergunta não é qual o menor percurso, e sim se aquela "
    + "sequência de atendimentos é executável sem violar a norma.");
  s.addNotes("O ACS visita as familias da microarea. O enunciado cita percurso, "
    + "equipe, urgencia e intervalo. Nosso recorte: um agente, um turno, rota "
    + "ja definida. A dor que nos interessou e que chegar na casa nao autoriza "
    + "atender: a lei condiciona, e algumas condicoes acabam no meio do turno.");
}

// =================================================== 3. A LEI E UMA ACAO
sec("Justificativa");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Justificativa" });
  etiqueta(s, "Por que Planejamento Automatizado");
  titulo(s, "A lei já está escrita como uma ação STRIPS");

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.92, w: W, h: 1.62, rectRadius: 0.09,
    fill: { color: TERRA_SUAVE }, line: { type: "none" }, objectName: "lei" });
  s.addText([
    { text: "“desde que ", options: {} },
    { text: "tenha concluído curso técnico", options: { bold: true } },
    { text: " e ", options: {} },
    { text: "tenha disponíveis os equipamentos adequados", options: { bold: true } },
    { text: ", são atividades do Agente […] ", options: {} },
    { text: "assistidas por profissional de saúde de nível superior", options: { bold: true } },
    { text: " […] a aferição da pressão arterial […], ", options: {} },
    { text: "encaminhando o paciente", options: { bold: true } },
    { text: " para a unidade de referência”", options: {} },
  ], { x: M + 0.32, y: 2.1, w: W - 0.64, h: 0.95, fontSize: 15,
       color: TINTA, fontFace: "Cambria", italic: true, isTextBox: true,
       margin: 0, lineSpacing: 20 });
  s.addText("Lei nº 11.350/2006, art. 3º § 4º, na redação da Lei nº 13.595/2018",
    { x: M + 0.32, y: 3.1, w: W - 0.64, h: 0.3, fontSize: 11, bold: true,
      color: TINTA45, isTextBox: true, margin: 0 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 3.78, w: W, h: 1.82, rectRadius: 0.09, fill: { color: "FFFDF8" },
    line: { color: "E6DCCB", width: 0.75 }, shadow: SOMBRA(),
    objectName: "pddl" });
  s.addText([
    { text: ":precondition", options: { color: SAGE, bold: true } },
    { text: " (and (curso-tecnico-concluido ?ag)\n                   (equipamento-disponivel ?ag)\n                   (supervisao-ativa ?ag))\n", options: { color: TINTA } },
    { text: ":effect", options: { color: SAGE, bold: true } },
    { text: "       (and (pa-ok ?p)\n                   (pendencia-encaminhamento ?p))", options: { color: TINTA } },
  ], { x: M + 0.32, y: 3.96, w: W - 0.64, h: 1.5, fontSize: 13,
       fontFace: "Courier New", isTextBox: true, margin: 0, lineSpacing: 17 });

  fechoLinha(s, 5.82, "Um if/else codifica a regra. Um domínio PDDL é a regra.");
  s.addNotes("Leia o trecho em voz alta: e a unica leitura literal que vale a "
    + "pena no deck. Tres condicoes conjuntivas e um efeito obrigatorio: isso e "
    + "exatamente um esquema de acao STRIPS, formalismo de 1971. STRIPS = "
    + "pre-condicoes, o que passa a valer e o que deixa de valer. Se a norma "
    + "mudar, edita-se a norma no dominio, nao o codigo de busca.");
}

// ========================================================= 4. A LACUNA
sec("Literatura");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Literatura" });
  etiqueta(s, "Revisão de literatura e mercado");
  titulo(s, "Três frentes maduras, e o que nenhuma cobre");

  const larg = (W - 0.52) / 3;
  cartao(s, { x: M, y: 1.98, w: larg, h: 2.42, nome: "lit1",
    titulo: "Roteamento em saúde domiciliar", tamTitulo: 15.5, alturaTitulo: 0.72,
    corpo: "Reconhece qualificação profissional como restrição, mas a modela "
         + "como etiqueta fixa de compatibilidade.\n\nFikar & Hirsch (2017)\n"
         + "Cissé et al. (2017)", tamCorpo: 12.5, entrelinha: 15 });

  cartao(s, { x: M + larg + 0.26, y: 1.98, w: larg, h: 2.42, nome: "lit2",
    titulo: "Planejamento em protocolos clínicos", tamTitulo: 15.5, alturaTitulo: 0.72,
    corpo: "Traduz diretrizes clínicas para domínios de planejamento, mas sem "
         + "componente de roteamento.\n\nGonzález-Ferrer et al. (2013)\n"
         + "Bradbrook et al. (2005)", tamCorpo: 12.5, entrelinha: 15 });

  cartao(s, { x: M + (larg + 0.26) * 2, y: 1.98, w: larg, h: 2.42, nome: "lit3",
    titulo: "Ferramentas de mercado", tamTitulo: 15.5, alturaTitulo: 0.72,
    corpo: "OR-Tools e OSRM otimizam a geometria. O e-SUS Território registra a "
         + "visita, sem roteirizar nem verificar conformidade.", tamCorpo: 12.5,
    entrelinha: 15 });

  fechoFaixa(s, 4.76, "Na literatura, a qualificação é uma etiqueta fixa. Na lei "
    + "brasileira, ela é uma soma de condições que se gastam durante o turno. "
    + "É nessa interseção que o projeto se posiciona.", true);
  s.addNotes("Nao leia os tres cartoes. Gaste o tempo no primeiro e no segundo. "
    + "O ponto: a literatura JA sabe que qualificacao importa, mas trata como "
    + "rotulo estatico, agente i atende paciente j. Gonzalez-Ferrer e o "
    + "precedente que blinda a escolha: traduzir norma em dominio de "
    + "planejamento nao e invencao nossa. Nas buscas realizadas nao achamos "
    + "trabalho que junte as duas coisas.");
}

// ================================================ 5. O QUE ACOPLA AS PARADAS
sec("O problema computacional");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "O problema computacional" });
  etiqueta(s, "Por que não é trivial");
  titulo(s, "Dois recursos acoplam as paradas entre si");

  cartao(s, { x: M, y: 2.0, w: 5.52, h: 1.72, nome: "rec1",
    rotulo: "RECURSO 1", corRotulo: TERRA,
    titulo: "Insumo consumível",
    corpo: "A fita de glicemia só se repõe na unidade de saúde. Acabar no meio "
         + "da rota obriga um desvio não previsto." });

  cartao(s, { x: M + 5.78, y: 2.0, w: 5.52, h: 1.72, nome: "rec2",
    rotulo: "RECURSO 2", corRotulo: TERRA,
    titulo: "Supervisão da equipe",
    corpo: "O § 4º exige assistência de profissional de nível superior, e ela "
         + "se encerra quando o agente deixa a residência." });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.02, w: W, h: 1.42, rectRadius: 0.09, fill: { color: CARTAO },
    line: { color: "E6DCCB", width: 0.75 }, shadow: SOMBRA(),
    objectName: "consequencia" });
  s.addText("Uma decisão tomada na terceira parada pode inviabilizar a sétima.", {
    x: M + 0.32, y: 4.2, w: W - 0.64, h: 0.42, fontSize: 19, bold: true,
    color: TINTA, fontFace: "Cambria", isTextBox: true, margin: 0 });
  s.addText("O número de sequências candidatas cresce exponencialmente, e a "
    + "interação entre decisões distantes na rota não é tratável por inspeção "
    + "manual nem por planilha.", {
    x: M + 0.32, y: 4.68, w: W - 0.64, h: 0.6, fontSize: 13.5, color: TINTA70,
    isTextBox: true, margin: 0, lineSpacing: 17 });

  fechoLinha(s, 5.66, "É esse acoplamento que torna o problema combinatório, e "
    + "não a geometria da rota.");
  s.addNotes("Se a rota esta fixa e cada visita fosse independente, o problema "
    + "se decomporia e um laco for bastaria. O que impede isso sao os recursos "
    + "finitos. Observacao honesta: a lei exige assistencia e nao diz nada "
    + "sobre forma ou frequencia. Representa-la como recurso finito por turno, "
    + "e encerra-la ao sair da casa, sao decisoes de modelagem NOSSAS.");
}

// ======================================================= 6. A HIPOTESE
sec("Hipótese");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Hipótese" });
  etiqueta(s, "Hipótese de trabalho");
  titulo(s, "O que acreditamos, e os dois jeitos de estarmos errados");

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.95, w: W, h: 1.5, rectRadius: 0.09, fill: { color: TERRA_SUAVE },
    line: { type: "none" }, objectName: "hip" });
  s.addText("A representação declarativa das condições legais reduzirá a "
    + "ocorrência de falsos negativos: turnos classificados como inexequíveis "
    + "quando existe sequência válida.", {
    x: M + 0.34, y: 2.14, w: W - 0.68, h: 1.12, fontSize: 19, bold: true,
    color: TINTA, fontFace: "Cambria", isTextBox: true, margin: 0,
    lineSpacing: 25 });

  cartao(s, { x: M, y: 3.72, w: 5.52, h: 1.72, nome: "alt1", fundo: "FFFDF8",
    rotulo: "SE ESTIVERMOS ERRADOS, CAMINHO 1", corRotulo: TINTA45,
    titulo: "O planejador é redundante",
    corpo: "Um executor procedural simples alcança desempenho equivalente." });

  cartao(s, { x: M + 5.78, y: 3.72, w: 5.52, h: 1.72, nome: "alt2", fundo: "FFFDF8",
    rotulo: "SE ESTIVERMOS ERRADOS, CAMINHO 2", corRotulo: TINTA45,
    titulo: "O planejador não escala",
    corpo: "O custo da busca cresce a ponto de inviabilizar microáreas reais." });

  fechoLinha(s, 5.68, "A validação foi desenhada para que qualquer um dos três "
    + "desfechos possa aparecer.");
  s.addNotes("Esta e a parte metodologica que vale sublinhar: a hipotese pode "
    + "estar errada, e o desenho admite isso. Nao formulamos uma pergunta que "
    + "so podia dar certo. Guarde esta frase, porque o slide 10 vai cobrar: um "
    + "dos dois caminhos de erro realmente se materializou.");
}

// ====================================================== 6b. OBJETIVOS
sec("Objetivos");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Objetivos" });
  etiqueta(s, "Objetivos");
  titulo(s, "O que será modelado, construído e medido");

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.92, w: W, h: 1.18, rectRadius: 0.09, fill: { color: TERRA_SUAVE },
    line: { type: "none" }, objectName: "og" });
  s.addText("OBJETIVO GERAL", { x: M + 0.32, y: 2.04, w: 4, h: 0.26,
    fontSize: 11.5, bold: true, color: TERRA, charSpacing: 1.6,
    isTextBox: true, margin: 0 });
  s.addText("Modelar, implementar e validar um sistema de apoio ao planejamento "
    + "de turnos de visitas domiciliares, e mensurar em que dimensões o "
    + "paradigma supera um executor procedural equivalente.", {
    x: M + 0.32, y: 2.34, w: W - 0.64, h: 0.66, fontSize: 15.5, color: TINTA,
    fontFace: "Cambria", isTextBox: true, margin: 0, lineSpacing: 20 });

  const grupos = [
    ["Formalizar", "A norma em domínio PDDL",
     "Traduzir os §§ 3º e 4º do art. 3º da Lei 11.350/2006 e as diretrizes da "
     + "PNAB em ações, pré-condições e efeitos."],
    ["Construir", "O sistema e o ambiente de medição",
     "A camada geométrica, o tradutor para PDDL, o executor procedural de "
     + "referência e a saída legível pelo agente."],
    ["Validar", "Os experimentos e a independência",
     "Escalabilidade, qualidade de plano e reconhecimento de inviabilidade, "
     + "com conferência em planejador de referência."],
  ];
  const lg = (W - 0.52) / 3;
  grupos.forEach(([verbo, t, d], i) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: M + (lg + 0.26) * i, y: 3.38, w: lg, h: 2.1, rectRadius: 0.1,
      fill: { color: CARTAO }, line: { color: "E6DCCB", width: 0.75 },
      shadow: SOMBRA(), objectName: "obj" + i });
    s.addText(verbo, { x: M + (lg + 0.26) * i + 0.26, y: 3.58, w: lg - 0.52,
      h: 0.34, fontSize: 17, bold: true, color: i === 2 ? SAGE : TERRA,
      fontFace: "Cambria", isTextBox: true, margin: 0 });
    s.addText(t, { x: M + (lg + 0.26) * i + 0.26, y: 3.96, w: lg - 0.52,
      h: 0.52, fontSize: 14, bold: true, color: TINTA, isTextBox: true,
      margin: 0, lineSpacing: 17 });
    s.addText(d, { x: M + (lg + 0.26) * i + 0.26, y: 4.54, w: lg - 0.52,
      h: 0.78, fontSize: 12.5, color: TINTA70, isTextBox: true, margin: 0,
      lineSpacing: 15.5 });
  });

  fechoLinha(s, 5.7, "Os sete objetivos específicos cabem nesses três verbos, e "
    + "a ordem entre eles é a ordem do trabalho.");
  s.addNotes("Este slide responde a secao 4 do guia. Nao leia os tres cartoes: "
    + "diga que os sete objetivos especificos se agrupam em formalizar a norma, "
    + "construir o sistema e validar com medicao, e que a verificacao em "
    + "planejador de referencia e objetivo declarado, nao detalhe. Se "
    + "perguntarem quantos sao, sao sete, e estao listados no documento.");
}

// ===================================================== 7. A ARQUITETURA
sec("Proposta");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Proposta" });
  etiqueta(s, "Proposta de abordagem");
  titulo(s, "Três camadas, cada paradigma no seu lugar");

  const camadas = [
    ["1", "Seleção", "quem entra no turno", "Prioridade clínica e atraso em relação ao intervalo máximo, sob orçamento de tempo.", TERRA],
    ["2", "Roteamento", "em que ordem visitar", "Heurística de grafos sobre a matriz de distâncias. Entrega a rota e o custo de desviar até a unidade.", TERRA],
    ["3", "Planejamento", "o que fazer em cada parada", "Domínio PDDL com as condições legais e os recursos finitos. Decide as ações e os desvios de reposição.", SAGE],
  ];
  let y = 1.95;
  camadas.forEach(([n, nome, oque, desc, cor]) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: M, y, w: W, h: 1.08, rectRadius: 0.08, fill: { color: CARTAO },
      line: { color: "E6DCCB", width: 0.75 }, shadow: SOMBRA(),
      objectName: "camada" + n });
    s.addShape(pres.ShapeType.ellipse, {
      x: M + 0.28, y: y + 0.3, w: 0.48, h: 0.48, fill: { color: cor },
      line: { type: "none" }, objectName: "num" + n });
    s.addText(n, { x: M + 0.28, y: y + 0.3, w: 0.48, h: 0.48, fontSize: 15,
      bold: true, color: "FFFFFF", align: "center", valign: "middle",
      isTextBox: true, margin: 0 });
    s.addText([
      { text: nome, options: { bold: true, color: cor, fontSize: 17 } },
      { text: "   " + oque, options: { color: TINTA70, fontSize: 13.5 } },
    ], { x: M + 0.95, y: y + 0.17, w: 4.3, h: 0.38, fontFace: "Cambria",
         isTextBox: true, margin: 0 });
    s.addText(desc, { x: M + 0.95, y: y + 0.56, w: 10.3, h: 0.42,
      fontSize: 13, color: TINTA70, isTextBox: true, margin: 0,
      lineSpacing: 16 });
    y += 1.2;
  });

  fechoFaixa(s, 5.6, "A camada 3 nunca escolhe a rota: ela só anda pelas arestas "
    + "que a camada 2 autorizou. Por isso trocar o roteirizador não muda uma "
    + "linha do domínio.", true);
  s.addNotes("Explique POR QUE sobra decisao para o planejador, senao a plateia "
    + "conclui que ele e decorativo. A camada geometrica entrega a ordem "
    + "congelada e o custo de desvio. O que sobra para o planejador: o que "
    + "fazer em cada casa, quando acionar a supervisao, e em qual parada vale "
    + "a pena sair da rota para repor. Se perguntarem por que nao OR-Tools: "
    + "ele resolve a metade geometrica e nao a normativa.");
}

// ===================================================== 8. VALIDACAO
sec("Metodologia");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Metodologia" });
  etiqueta(s, "Plano de validação");
  titulo(s, "Construímos o adversário antes de medir");

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.9, w: W, h: 1.24, rectRadius: 0.09, fill: { color: SAGE_SUAVE },
    line: { type: "none" }, objectName: "controle" });
  s.addText("Grupo de comparação", { x: M + 0.32, y: 2.04, w: 4, h: 0.3,
    fontSize: 12.5, bold: true, color: SAGE, charSpacing: 1, isTextBox: true,
    margin: 0 });
  s.addText("Um executor procedural percorre a mesma rota, cumpre os mesmos "
    + "protocolos e lê a mesma tabela de custos do arquivo PDDL. O que ele não "
    + "faz é antecipar: só descobre que falta recurso no momento de usá-lo.", {
    x: M + 0.32, y: 2.38, w: W - 0.64, h: 0.68, fontSize: 14, color: TINTA,
    isTextBox: true, margin: 0, lineSpacing: 18 });

  const exps = [
    ["Escalabilidade", "Até que tamanho de microárea cada estratégia de busca ainda é viável."],
    ["Falsos negativos", "Com que frequência cada abordagem declara inexequível um turno que tem solução."],
    ["Prova de inviabilidade", "Instâncias sem solução, de dois tipos: falta condição legal, ou falta recurso."],
  ];
  const lc = (W - 0.52) / 3;
  exps.forEach(([t, d], i) => {
    cartao(s, { x: M + (lc + 0.26) * i, y: 3.32, w: lc, h: 2.16,
      nome: "exp" + i, rotulo: "EXPERIMENTO " + (i + 1), corRotulo: TINTA45,
      titulo: t, tamTitulo: 15, alturaTitulo: 0.4, corpo: d,
      tamCorpo: 12.5, entrelinha: 15.5 });
  });

  fechoLinha(s, 5.62, "A variável isolada é uma só: a capacidade de antecipar "
    + "conflitos de recursos.");
  s.addNotes("Detalhe metodologico que vale citar: o executor le os custos do "
    + "proprio .pddl, para eliminar divergencia de medicao entre os dois "
    + "grupos. Isso pegou um erro real durante o desenvolvimento, em que a "
    + "mesma acao era cobrada de formas diferentes nos dois lados.");
}

// =============================================== 9. ENTREGA E CRONOGRAMA
sec("Entrega");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Entrega" });
  etiqueta(s, "Resultados esperados e cronograma");
  titulo(s, "O que será entregue, e até quando");

  cartao(s, { x: M, y: 1.95, w: 5.2, h: 3.4, nome: "entrega",
    rotulo: "NÍVEL DE MATURIDADE TRL 3 A 4", corRotulo: SAGE,
    titulo: "Sistema validado em laboratório",
    corpo: "Não é produto pronto para implantação em rede de saúde.\n\n"
         + "·  o sistema com as camadas integradas\n"
         + "·  o domínio PDDL mapeado dispositivo a dispositivo\n"
         + "·  a saída legível pelo agente de saúde\n"
         + "·  os experimentos reprodutíveis\n"
         + "·  o relatório técnico das medições", tamCorpo: 13, entrelinha: 18 });

  const marcos = [
    ["25 / 09", "Concepção e verificação de viabilidade", "Delimitação do problema, revisão bibliográfica e implementação exploratória."],
    ["02 / 10", "Construção do sistema", "Domínio completo, camada geométrica, política de seleção, saída operacional e experimentos."],
    ["09 / 10", "Consolidação", "Análise crítica, relatório final e apresentação."],
  ];
  let y = 1.95;
  marcos.forEach(([data, t, d], i) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: M + 5.46, y, w: W - 5.46, h: 1.06, rectRadius: 0.08,
      fill: { color: i === 0 ? SAGE_SUAVE : CARTAO },
      line: { color: "E6DCCB", width: 0.75 }, shadow: SOMBRA(),
      objectName: "marco" + i });
    s.addText(data, { x: M + 5.72, y: y + 0.18, w: 1.25, h: 0.32,
      fontSize: 14.5, bold: true, color: i === 0 ? SAGE : TERRA,
      fontFace: "Cambria", isTextBox: true, margin: 0 });
    s.addText(t, { x: M + 7.05, y: y + 0.16, w: 5.0, h: 0.34, fontSize: 14.5,
      bold: true, color: TINTA, fontFace: "Cambria", isTextBox: true,
      margin: 0 });
    s.addText(d, { x: M + 7.05, y: y + 0.54, w: 5.0, h: 0.44, fontSize: 12,
      color: TINTA70, isTextBox: true, margin: 0, lineSpacing: 14.5 });
    y += 1.17;
  });

  fechoLinha(s, 5.62, "O desfecho contrário à hipótese também é resultado: "
    + "delimitaria as condições em que o paradigma compensa.");
  s.addNotes("Apresente as lacunas como lacunas conhecidas, nao como promessas. "
    + "A mais visivel frente ao enunciado e prioridade e intervalo na selecao "
    + "do turno. Se perguntarem sobre dados de pacientes: todos ficticios, so "
    + "as coordenadas sao reais, para dar ordem de grandeza a matriz.");
}

// ========================================== 10. O QUE A EXPLORACAO MOSTROU
sec("Achados");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Achados" });
  etiqueta(s, "Implementação exploratória");
  titulo(s, "Três coisas que já aprendemos, uma delas contra nós");

  const achados = [
    ["A busca trivial não escala", "Varrer o mesmo modelo declarativo sem heurística resolve até 5 ou 6 pacientes. Um turno real tem de 10 a 15.", SAGE, "favoravel"],
    ["O planejador está correto", "Um planejador de referência independente concordou sobre viabilidade e plano mínimo em todas as instâncias testadas.", SAGE, "favoravel"],
    ["A hipótese foi refutada", "Uma correção manual no executor procedural zera os falsos negativos. Ele não era incapaz: faltava-lhe a regra.", TERRA, "contra"],
  ];
  const lc = (W - 0.52) / 3;
  achados.forEach(([t, d, cor, tipo], i) => {
    cartao(s, { x: M + (lc + 0.26) * i, y: 1.98, w: lc, h: 2.5,
      nome: "achado" + i, fundo: tipo === "contra" ? TERRA_SUAVE : CARTAO,
      rotulo: tipo === "contra" ? "CONTRA A HIPÓTESE" : "A FAVOR",
      corRotulo: cor, titulo: t, tamTitulo: 16, alturaTitulo: 0.66,
      corpo: d, tamCorpo: 13, entrelinha: 16.5 });
  });

  fechoFaixa(s, 4.82, "O caminho 1 de erro, previsto no slide da hipótese, foi o "
    + "que se materializou. A pergunta de pesquisa precisa ser reformulada.");
  s.addNotes("Este slide fecha o circulo com o slide 6. Dissemos que a hipotese "
    + "podia estar errada de dois jeitos, e um deles aconteceu. Abrir isso e "
    + "mais forte do que esconder: mostra que o desenho experimental "
    + "funcionou. Nao entre em numero de instancia aqui; se perguntarem, foram "
    + "40 microareas sorteadas.");
}

// =========================================== 12. REFORMULACAO DA HIPOTESE
sec("Fecho");
{
  const s = pres.addSlide({ masterName: "BASE", sectionTitle: "Fecho" });
  etiqueta(s, "Reformulação da hipótese");
  titulo(s, "O que o trabalho passa a defender");

  // Caixa deliberadamente igual em forma a do slide da hipotese, e diferente
  // em cor: ali a hipotese estava em aberto, aqui e a que sobreviveu.
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.92, w: W, h: 1.62, rectRadius: 0.09, fill: { color: SAGE_SUAVE },
    line: { type: "none" }, objectName: "nova-hipotese" });
  s.addText("Manter a norma como especificação declarativa preserva a corretude "
    + "do sistema diante de regras novas, a um custo de busca que ainda cabe "
    + "num turno real.", {
    x: M + 0.34, y: 2.12, w: W - 0.68, h: 1.24, fontSize: 20, bold: true,
    color: TINTA, fontFace: "Cambria", isTextBox: true, margin: 0,
    lineSpacing: 26 });

  // Falsificavel nas duas direcoes: e o que a torna uma hipotese, e nao um lema
  const pernas = [
    ["Tire a declaratividade", "e sobra o programa procedural",
     "Ele resolve bem as regras que alguém já analisou, e falha quando elas mudam."],
    ["Tire a busca heurística", "e sobra a varredura cega",
     "Ela absorve regra nova sem esforço, e não chega ao tamanho de um turno."],
  ];
  pernas.forEach(([cond, meio, cons], i) => {
    const x = M + (5.78) * i;
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 3.78, w: 5.52, h: 1.72, rectRadius: 0.1, fill: { color: CARTAO },
      line: { color: "E6DCCB", width: 0.75 }, shadow: SOMBRA(),
      objectName: "perna" + i });
    s.addText([
      { text: cond, options: { bold: true, color: TERRA, fontSize: 16 } },
      { text: "  " + meio, options: { color: TINTA70, fontSize: 13 } },
    ], { x: x + 0.26, y: 3.98, w: 5.0, h: 0.6, fontFace: "Cambria",
         isTextBox: true, margin: 0, lineSpacing: 19 });
    s.addText(cons, { x: x + 0.26, y: 4.62, w: 5.0, h: 0.66, fontSize: 13.5,
      color: TINTA70, isTextBox: true, margin: 0, lineSpacing: 17 });
  });

  fechoLinha(s, 5.68, "Nenhuma das duas metades sozinha resolve. Planejamento "
    + "Automatizado é o nome da combinação.");
  s.addNotes("A caixa tem a MESMA forma da do slide 6, e cor diferente de "
    + "proposito: la a hipotese estava em aberto, aqui e a que sobreviveu. Se "
    + "quiser, aponte isso. Os dois cartoes sao o que torna a nova hipotese "
    + "uma hipotese e nao um lema: ela e falsificavel nas duas direcoes, e "
    + "cada direcao ja tem medicao. Se perguntarem o que caiu: economia de "
    + "deslocamento e a ideia de que o planejamento acha planos que um "
    + "programa corrigido nao acharia.");
}

(async () => {
  await pres.writeFile({ fileName: SAIDA });
  const { applyTheme } = require(process.argv[3]);
  await applyTheme(SAIDA, THEME);
  console.log("gerado:", SAIDA);
})();
