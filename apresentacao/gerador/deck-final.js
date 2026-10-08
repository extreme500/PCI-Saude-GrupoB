// Copia em .pptx da apresentacao final em HTML.
// Mesmos 14 slides, mesma paleta creme, mesma tipografia.
// A demonstracao do pipeline, que no HTML roda viva dentro do slide, aqui
// vira um storyboard dos sete passos mais o link para abrir a versao viva.

const path = require("path");
const PptxGenJS = require("pptxgenjs");

const RAIZ = process.argv[2];                 // pasta do repositorio
const IMG = process.argv[3];                  // pasta com os recortes dos passos
const SAIDA = process.argv[4];

const C = {
  escuro: "33291F", medio: "5C4F41", bege: "8A7A67",
  terracota: "B35C38", salvia: "4A6B5B", dourado: "BF9000",
  cartao: "FFFDF8", borda: "E6DCCB",
  quente: "F3DFD3", verde: "DDE7E0", branco: "FFFFFF",
};
const SERIF = "Cambria";
const SANS = "Calibri";
const FUNDO = path.join(RAIZ, "apresentacao", "gerador", "fundo-creme.png");

const L = 0.62;              // margem esquerda
const W = 13.33 - 2 * L;     // largura util

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";
pres.author = "Grupo B";
pres.title = "Planejamento Automatizado para o cumprimento de protocolos legais";

function novo(notas) {
  const s = pres.addSlide();
  s.background = { path: FUNDO };
  if (notas) s.addNotes(notas);
  return s;
}

function etapa(s, texto) {
  s.addText(texto.toUpperCase(), {
    x: L, y: 0.38, w: W, h: 0.32, isTextBox: true,
    fontFace: SANS, fontSize: 13, bold: true, color: C.terracota,
    charSpacing: 1.6,
  });
}

function titulo(s, texto, opcoes) {
  const o = opcoes || {};
  s.addText(texto, {
    x: L, y: o.y || 0.74, w: W, h: o.h || 1.0, isTextBox: true,
    fontFace: SERIF, fontSize: o.tamanho || 40, bold: true, color: C.escuro,
    valign: "top", lineSpacingMultiple: 1.0,
  });
}

function faixa(s, o) {
  s.addShape(pres.ShapeType.roundRect, {
    x: o.x === undefined ? L : o.x, y: o.y,
    w: o.w === undefined ? W : o.w, h: o.h,
    fill: { color: o.cor || C.quente }, line: { color: o.cor || C.quente },
    rectRadius: 0.14,
  });
}

function cartao(s, o) {
  s.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h,
    fill: { color: o.cor || C.cartao },
    line: { color: o.borda || C.borda, width: 1 },
    rectRadius: 0.13,
  });
}

function rotulo(s, texto, o) {
  s.addText(texto.toUpperCase(), {
    x: o.x, y: o.y, w: o.w, h: 0.28, isTextBox: true,
    fontFace: SANS, fontSize: o.tamanho || 12, bold: true,
    color: o.cor || C.bege, charSpacing: 1.2,
  });
}

function sub(s, texto, o) {
  s.addText(texto, {
    x: o.x, y: o.y, w: o.w, h: o.h || 0.6, isTextBox: true,
    fontFace: SERIF, fontSize: o.tamanho || 21, bold: true,
    color: o.cor || C.escuro, valign: "top", lineSpacingMultiple: 1.05,
  });
}

function corpo(s, texto, o) {
  s.addText(texto, {
    x: o.x, y: o.y, w: o.w, h: o.h || 1.2, isTextBox: true,
    fontFace: SANS, fontSize: o.tamanho || 17, color: o.cor || C.medio,
    valign: "top", lineSpacingMultiple: 1.12,
  });
}

function fecho(s, partes, o) {
  const op = o || {};
  s.addText(partes, {
    x: L, y: op.y || 6.25, w: W, h: op.h || 0.95, isTextBox: true,
    fontFace: SERIF, fontSize: op.tamanho || 21, color: C.escuro,
    valign: "top", lineSpacingMultiple: 1.1,
  });
}

function numerao(s, texto, o) {
  s.addText(texto, {
    x: o.x, y: o.y, w: o.w, h: o.h || 1.3, isTextBox: true,
    fontFace: SERIF, fontSize: o.tamanho || 62, bold: true,
    color: o.cor || C.escuro, valign: "top", align: o.align || "left",
  });
}

// ===========================================================  1  capa
{
  const s = novo("Abertura. Apresente os tres e diga em uma frase o recorte: um agente, um turno, uma microarea. Nao mencione PDDL ainda, isso vem no slide 3. A frase que prepara tudo: quase todo mundo ataca isso como problema de rota, e a rota e so metade do problema.");
  s.addText("PROJETO EM CIÊNCIA E INOVAÇÃO  ·  INF99003  ·  CICLO 2  ·  APRESENTAÇÃO FINAL", {
    x: L, y: 0.42, w: W, h: 0.32, isTextBox: true,
    fontFace: SANS, fontSize: 13, bold: true, color: C.terracota, charSpacing: 1.6,
  });
  s.addText("Planejamento Automatizado para\no cumprimento de protocolos legais", {
    x: L, y: 1.45, w: W, h: 2.3, isTextBox: true,
    fontFace: SERIF, fontSize: 44, bold: true, color: C.escuro,
    lineSpacingMultiple: 1.05,
  });
  s.addText("Visitas domiciliares de Agentes Comunitários de Saúde na Atenção Primária do SUS.", {
    x: L, y: 3.85, w: W, h: 0.6, isTextBox: true,
    fontFace: SANS, fontSize: 22, color: C.medio,
  });
  s.addShape(pres.ShapeType.rect, {
    x: L, y: 4.95, w: 2.1, h: 0.05,
    fill: { color: C.terracota }, line: { color: C.terracota },
  });
  s.addText("Gabriel Pieruccini Knopp  ·  Arthur Andrade da Silva  ·  Izadora Candotti de Oliveira", {
    x: L, y: 5.45, w: W, h: 0.5, isTextBox: true,
    fontFace: SERIF, fontSize: 20, bold: true, color: C.escuro,
  });
  s.addText("Grupo B  ·  Instituto de Informática, UFRGS", {
    x: L, y: 5.98, w: W, h: 0.4, isTextBox: true,
    fontFace: SANS, fontSize: 16, color: C.bege,
  });
}

// ===========================================================  2  problema
{
  const s = novo("O enunciado do ciclo cita percurso, equipe, urgencia e intervalo. Quase todo grupo le isso como roteirizacao. A dor que nos interessou e outra: chegar na casa NAO autoriza atender. A lei condiciona, e algumas condicoes acabam no meio do turno.");
  etapa(s, "O problema");
  titulo(s, "Chegar na casa não autoriza atender");
  const lc = (W - 0.4) / 2;
  cartao(s, { x: L, y: 2.0, w: lc, h: 3.6 });
  rotulo(s, "Como o problema costuma ser lido", { x: L + 0.28, y: 2.25, w: lc - 0.56 });
  sub(s, "Um problema de percurso", { x: L + 0.28, y: 2.62, w: lc - 0.56, h: 0.6, tamanho: 24 });
  corpo(s, "Minimizar deslocamento, cobrir o território no prazo e respeitar a capacidade da equipe. Roteirizadores já resolvem isso bem.",
    { x: L + 0.28, y: 3.32, w: lc - 0.56, h: 2.0, tamanho: 19 });

  cartao(s, { x: L + lc + 0.4, y: 2.0, w: lc, h: 3.6, cor: C.quente, borda: "E9CFC2" });
  rotulo(s, "O que essa leitura deixa de fora", { x: L + lc + 0.68, y: 2.25, w: lc - 0.56, cor: C.terracota });
  sub(s, "Uma norma que condiciona cada atendimento", { x: L + lc + 0.68, y: 2.62, w: lc - 0.56, h: 0.95, tamanho: 24 });
  corpo(s, "A Lei 11.350/2006 diz o que o agente pode fazer em cada residência. E nem toda condição é estática: insumo e supervisão se esgotam ao longo do turno.",
    { x: L + lc + 0.68, y: 3.62, w: lc - 0.56, h: 1.8, tamanho: 19 });

  fecho(s, "A pergunta não é qual o menor percurso, e sim se aquela sequência de atendimentos é executável sem violar a norma.", { y: 6.0 });
}

// ===========================================================  3  a lei
{
  const s = novo("Leia o trecho da lei em voz alta: e a unica leitura literal que vale a pena no deck. Tres condicoes conjuntivas e um efeito obrigatorio. Isso e exatamente um esquema de acao STRIPS, formalismo de 1971: pre-condicoes, o que passa a valer e o que deixa de valer. Planejamento Automatizado e a area que, dado um estado inicial, um objetivo e acoes descritas assim, procura a sequencia que leva de um ao outro. Se a norma mudar, edita-se a norma, nao o codigo de busca.");
  etapa(s, "Justificativa · por que Planejamento Automatizado");
  titulo(s, "A lei já está escrita no formato de uma ação");
  const le = 6.55, ld = W - le - 0.4;
  faixa(s, { x: L, y: 1.92, w: le, h: 3.6 });
  s.addText([
    { text: "“desde que o Agente Comunitário de Saúde tenha concluído " },
    { text: "curso técnico", options: { bold: true } },
    { text: " e tenha disponíveis os " },
    { text: "equipamentos adequados", options: { bold: true } },
    { text: ", são atividades do Agente [...] " },
    { text: "assistidas por profissional de saúde de nível superior", options: { bold: true } },
    { text: " [...] a aferição da pressão arterial [...], " },
    { text: "encaminhando o paciente", options: { bold: true } },
    { text: " para a unidade de saúde de referência”" },
  ], {
    x: L + 0.3, y: 2.14, w: le - 0.6, h: 2.8, isTextBox: true,
    fontFace: SERIF, fontSize: 17, italic: true, color: C.escuro,
    lineSpacingMultiple: 1.12, valign: "top",
  });
  s.addText("Lei nº 11.350/2006, art. 3º § 4º, na redação da Lei nº 13.595/2018", {
    x: L + 0.3, y: 5.02, w: le - 0.6, h: 0.32, isTextBox: true,
    fontFace: SANS, fontSize: 12, color: C.bege,
  });

  rotulo(s, "A mesma regra, no domínio PDDL", { x: L + le + 0.4, y: 1.92, w: ld, cor: C.salvia });
  cartao(s, { x: L + le + 0.4, y: 2.32, w: ld, h: 3.2 });
  s.addText([
    { text: ":precondition\n", options: { bold: true, color: C.salvia } },
    { text: "  (and (curso-tecnico-concluido ?ag)\n       (equipamento-disponivel ?ag)\n       (supervisao-ativa ?ag))\n\n" },
    { text: ":effect\n", options: { bold: true, color: C.salvia } },
    { text: "  (and (pa-ok ?p)\n       (pendencia-encaminhamento ?p))" },
  ], {
    x: L + le + 0.62, y: 2.56, w: ld - 0.44, h: 2.8, isTextBox: true,
    fontFace: "Courier New", fontSize: 13, color: C.escuro,
    lineSpacingMultiple: 1.15, valign: "top",
  });

  fecho(s, "Três condições conjuntivas e um efeito obrigatório: é a forma de um esquema de ação STRIPS, o formalismo de 1971 em que o Planejamento Automatizado se apoia.", { y: 5.75 });
}

// ===========================================================  4  acoplamento
{
  const s = novo("Se a rota esta fixa e cada visita fosse independente, o problema se decomporia e um laco for bastaria. O que impede isso sao os recursos finitos. Observacao honesta, e vale dizer na hora: a lei exige assistencia e nao diz nada sobre forma ou frequencia. Representa-la como recurso finito por turno, e encerra-la ao sair da casa, sao decisoes de modelagem NOSSAS.");
  etapa(s, "Justificativa · por que não basta um laço");
  titulo(s, "Duas coisas acabam no meio do turno");
  const lc = (W - 0.4) / 2;
  cartao(s, { x: L, y: 1.95, w: lc, h: 2.45 });
  rotulo(s, "Recurso 1", { x: L + 0.28, y: 2.18, w: lc - 0.56, cor: C.terracota });
  sub(s, "Insumo consumível", { x: L + 0.28, y: 2.55, w: lc - 0.56, h: 0.5, tamanho: 24 });
  corpo(s, "A fita de glicemia só se repõe na unidade. Acabar no meio da rota obriga um desvio não previsto.",
    { x: L + 0.28, y: 3.12, w: lc - 0.56, h: 1.1, tamanho: 19 });

  cartao(s, { x: L + lc + 0.4, y: 1.95, w: lc, h: 2.45 });
  rotulo(s, "Recurso 2", { x: L + lc + 0.68, y: 2.18, w: lc - 0.56, cor: C.terracota });
  sub(s, "Supervisão da equipe", { x: L + lc + 0.68, y: 2.55, w: lc - 0.56, h: 0.5, tamanho: 24 });
  corpo(s, "O § 4º exige assistência de profissional de nível superior, e ela se encerra quando o agente deixa a residência.",
    { x: L + lc + 0.68, y: 3.12, w: lc - 0.56, h: 1.1, tamanho: 19 });

  faixa(s, { y: 4.72, h: 2.1 });
  s.addText("Uma decisão tomada na terceira parada pode inviabilizar a sétima.", {
    x: L + 0.34, y: 4.98, w: W - 0.68, h: 0.6, isTextBox: true,
    fontFace: SERIF, fontSize: 26, bold: true, color: C.escuro,
  });
  corpo(s, "É isso que impede decompor o turno visita a visita, e é por isso que um laço for sobre a rota não resolve.",
    { x: L + 0.34, y: 5.72, w: W - 0.68, h: 0.9, tamanho: 20 });
}

// ===========================================================  5  literatura 1
{
  const s = novo("Este slide e o mais importante da primeira metade. Nao leia os tres cartoes inteiros: gaste o tempo no terceiro. Os dois primeiros dizem que a literatura ja sabe das partes. O terceiro e o que quase ninguem espera: embutir regra legal em algoritmo de roteamento NAO e novidade, tem survey proprio, e a arquitetura rota pronta mais verificacao da norma tem nome, Truck Driver Scheduling Problem, resolvido desde 2009.");
  etapa(s, "Revisão de literatura · o que já existe");
  titulo(s, "Três frentes, e nenhuma delas é novidade");
  const lc = (W - 0.8) / 3;
  const dados = [
    ["Frente 1", "Roteamento em saúde domiciliar",
      "Reconhece qualificação profissional como restrição, mas a trata como etiqueta fixa de compatibilidade.",
      "Fikar & Hirsch (2017)\nCissé et al. (2017)", C.cartao, C.bege],
    ["Frente 2", "Protocolo de saúde virando domínio de planejamento",
      "Diretrizes clínicas já são traduzidas para planejamento automatizado, mas sem componente de roteamento.",
      "González-Ferrer et al. (2013)\nBradbrook et al. (2005)", C.cartao, C.bege],
    ["Frente 3, a que nos surpreendeu", "Regra legal dentro de roteamento",
      "A jornada de motoristas na União Europeia é lei embutida em roteirização, e tem revisão sistemática própria.",
      "Archetti & Savelsbergh (2009)\nGoel (2010) · Goel & Kok (2011)", C.quente, C.terracota],
  ];
  dados.forEach(function (d, i) {
    const x = L + i * (lc + 0.4);
    cartao(s, { x: x, y: 1.9, w: lc, h: 3.85, cor: d[4], borda: d[4] === C.quente ? "E9CFC2" : C.borda });
    rotulo(s, d[0], { x: x + 0.26, y: 2.12, w: lc - 0.52, cor: d[5], tamanho: 11 });
    sub(s, d[1], { x: x + 0.26, y: 2.5, w: lc - 0.52, h: 1.15, tamanho: 21 });
    corpo(s, d[2], { x: x + 0.26, y: 3.72, w: lc - 0.52, h: 1.3, tamanho: 17 });
    s.addText(d[3], {
      x: x + 0.26, y: 5.02, w: lc - 0.52, h: 0.62, isTextBox: true,
      fontFace: SANS, fontSize: 13, color: C.bege, lineSpacingMultiple: 1.1,
    });
  });
  fecho(s, [
    { text: "A arquitetura que usamos, rota já fixada e depois uma camada que verifica a norma, tem nome na literatura: " },
    { text: "Truck Driver Scheduling Problem", options: { bold: true } },
    { text: "." },
  ], { y: 6.0 });
}

// ===========================================================  6  literatura 2
{
  const s = novo("Aqui esta a honestidade que fortalece. Dissemos aos professores que eramos os primeiros, fomos checar, e nao somos. Mas a lista de artigos do TDSP e o nosso melhor argumento: um artigo e um algoritmo novo por jurisdicao, Uniao Europeia, Estados Unidos, Canada, Australia. Isso e o custo de manutencao do jeito procedural, acontecendo de verdade, por vinte anos. Nos medimos esse custo em laboratorio.");
  etapa(s, "Revisão de literatura · onde nos encaixamos");
  titulo(s, "Não somos os primeiros a fazer. Somos os primeiros a medir.", { tamanho: 34, h: 1.5 });
  faixa(s, { y: 2.28, h: 1.8, cor: C.verde });
  s.addText([
    { text: "O que não encontramos na literatura é esta combinação: a " },
    { text: "sequência de ações obrigatórias dentro da visita", options: { bold: true } },
    { text: ", derivada de norma jurídica, como domínio declarativo acoplado a roteamento, com a qualificação tratada como " },
    { text: "soma de condições que se gastam", options: { bold: true } },
    { text: " e não como etiqueta fixa." },
  ], {
    x: L + 0.34, y: 2.48, w: W - 0.68, h: 1.45, isTextBox: true,
    fontFace: SANS, fontSize: 20, color: C.escuro, lineSpacingMultiple: 1.12, valign: "top",
  });
  const lc = (W - 0.4) / 2;
  cartao(s, { x: L, y: 4.35, w: lc, h: 2.55 });
  rotulo(s, "O que a literatura do TDSP mostra", { x: L + 0.28, y: 4.56, w: lc - 0.56, cor: C.terracota });
  s.addText([
    { text: "Um artigo e um algoritmo " },
    { text: "novo por jurisdição", options: { bold: true } },
    { text: ": União Europeia, Estados Unidos, Canadá, Austrália. O mesmo problema resolvido quatro vezes." },
  ], {
    x: L + 0.28, y: 4.96, w: lc - 0.56, h: 1.8, isTextBox: true,
    fontFace: SANS, fontSize: 19, color: C.medio, lineSpacingMultiple: 1.12, valign: "top",
  });
  cartao(s, { x: L + lc + 0.4, y: 4.35, w: lc, h: 2.55, cor: C.verde, borda: "CBDCD1" });
  rotulo(s, "O que isso abre para nós", { x: L + lc + 0.68, y: 4.56, w: lc - 0.56, cor: C.salvia });
  corpo(s, "Esse é o custo de manutenção do caminho procedural, acontecendo por vinte anos. Ninguém o quantificou. Nós quantificamos.",
    { x: L + lc + 0.68, y: 4.96, w: lc - 0.56, h: 1.8, tamanho: 19 });
}

// ===========================================================  7  pipeline
{
  const s = novo("Explique POR QUE sobra decisao para o planejador, senao a plateia conclui que ele e decorativo. A camada 2 entrega a ordem congelada e o custo de desvio. O que sobra para a camada 3: o que fazer em cada casa, quando acionar a supervisao, e em qual parada vale a pena sair da rota para repor. Se perguntarem por que nao OR-Tools: ele resolve a metade geometrica, nao a normativa.");
  etapa(s, "O sistema");
  titulo(s, "Três camadas, e só a terceira conhece a lei");
  const passos = [
    ["1", "Seleção: quem entra no turno", "Prioridade clínica e atraso em relação ao intervalo máximo, sob orçamento de tempo.", C.terracota],
    ["2", "Roteamento: em que ordem visitar", "Algoritmo genético sobre a matriz de distâncias. Entrega a rota e o custo de desviar até a unidade.", C.terracota],
    ["3", "Planejamento: o que fazer em cada parada", "Domínio PDDL com as condições legais e os recursos finitos. Decide as ações e os desvios de reposição.", C.salvia],
  ];
  passos.forEach(function (p, i) {
    const y = 1.95 + i * 1.42;
    cartao(s, { x: L, y: y, w: W, h: 1.22 });
    s.addShape(pres.ShapeType.ellipse, {
      x: L + 0.3, y: y + 0.3, w: 0.6, h: 0.6,
      fill: { color: p[3] }, line: { color: p[3] },
    });
    s.addText(p[0], {
      x: L + 0.3, y: y + 0.3, w: 0.6, h: 0.6, isTextBox: true,
      fontFace: SERIF, fontSize: 20, bold: true, color: C.branco,
      align: "center", valign: "middle",
    });
    sub(s, p[1], { x: L + 1.1, y: y + 0.17, w: W - 1.5, h: 0.45, tamanho: 23, cor: p[3] });
    corpo(s, p[2], { x: L + 1.1, y: y + 0.66, w: W - 1.5, h: 0.5, tamanho: 18 });
  });
  fecho(s, "A camada 3 nunca escolhe a rota: ela só anda pelas arestas que a camada 2 autorizou. Por isso trocar o roteirizador não muda uma linha do domínio.", { y: 6.3 });
}

// ===========================================================  8  hipotese
{
  const s = novo("Esta e a parte metodologica que vale sublinhar: a hipotese podia estar errada, e o desenho admitia isso. Nao formulamos uma pergunta que so podia dar certo. Guarde esta frase, porque dois slides adiante vamos cobrar: um dos dois caminhos de erro realmente se materializou.");
  etapa(s, "Metodologia");
  titulo(s, "Formulamos a hipótese de modo que ela pudesse cair", { tamanho: 34 });
  faixa(s, { y: 1.95, h: 1.95 });
  s.addText("“A representação declarativa das condições legais reduzirá a ocorrência de falsos negativos: turnos classificados como inexequíveis quando existe sequência válida.”", {
    x: L + 0.34, y: 2.2, w: W - 0.68, h: 1.5, isTextBox: true,
    fontFace: SERIF, fontSize: 25, italic: true, color: C.escuro,
    lineSpacingMultiple: 1.12, valign: "top",
  });
  const lc = (W - 0.4) / 2;
  const erros = [
    ["Se estivermos errados, caminho 1", "O planejador é redundante", "Um executor procedural simples alcança desempenho equivalente."],
    ["Se estivermos errados, caminho 2", "O planejador não escala", "O custo da busca cresce a ponto de inviabilizar microáreas reais."],
  ];
  erros.forEach(function (e, i) {
    const x = L + i * (lc + 0.4);
    cartao(s, { x: x, y: 4.2, w: lc, h: 2.55 });
    rotulo(s, e[0], { x: x + 0.28, y: 4.44, w: lc - 0.56 });
    sub(s, e[1], { x: x + 0.28, y: 4.82, w: lc - 0.56, h: 0.5, tamanho: 25 });
    corpo(s, e[2], { x: x + 0.28, y: 5.42, w: lc - 0.56, h: 1.1, tamanho: 20 });
  });
}

// ===========================================================  9  refutacoes
{
  const s = novo("Abrir isso e mais forte do que esconder: mostra que o desenho experimental funcionou. O caminho 1 de erro, previsto no slide anterior, foi o que se materializou. Se perguntarem quantas instancias: 40 no E7, 25 no E9, 8 por tamanho no E8.");
  etapa(s, "Resultados · o que nós mesmos derrubamos");
  titulo(s, "Construímos três experimentos para nos refutar.\nOs três funcionaram.", { tamanho: 31, h: 1.5 });
  const lc = (W - 0.8) / 3;
  const quedas = [
    ["“Achamos planos que um programa não acharia”",
      [{ text: "Uma correção manual de poucas linhas leva o executor procedural de " },
       { text: "22%", options: { bold: true, color: C.terracota } },
       { text: " de falsos negativos a " },
       { text: "0%", options: { bold: true, color: C.salvia } },
       { text: "." }]],
    ["“O algoritmo genético é melhor otimizador”",
      [{ text: "Sem precedência, o ganho dele vira " },
       { text: "+1,4%, 0,0% e −0,3%", options: { bold: true, color: C.terracota } },
       { text: ". A vantagem vinha da restrição, não do operador." }]],
    ["“Na prática o planejamento sai na frente”",
      [{ text: "Na busca satisfaciente, que é a que escala, ele entrega planos " },
       { text: "3,5% mais caros", options: { bold: true, color: C.terracota } },
       { text: ", piores em 16 de 25." }]],
  ];
  quedas.forEach(function (q, i) {
    const x = L + i * (lc + 0.4);
    cartao(s, { x: x, y: 2.34, w: lc, h: 3.6, cor: C.quente, borda: "E9CFC2" });
    rotulo(s, "Caiu", { x: x + 0.26, y: 2.55, w: lc - 0.52, cor: C.terracota });
    sub(s, q[0], { x: x + 0.26, y: 2.92, w: lc - 0.52, h: 1.5, tamanho: 20 });
    s.addText(q[1], {
      x: x + 0.26, y: 4.45, w: lc - 0.52, h: 1.4, isTextBox: true,
      fontFace: SANS, fontSize: 17, color: C.medio,
      lineSpacingMultiple: 1.12, valign: "top",
    });
  });
  fecho(s, "O caminho 1 de erro, previsto no slide da hipótese, foi exatamente o que se materializou.", { y: 6.1 });
}

// ===========================================================  10  o que sobrou
{
  const s = novo("Este e o resultado central do trabalho. A correcao do E7 foi escrita observando UM modo de falha. Aplicada ao dominio estendido, com tres recursos novos e escassos, ela entrega beneficio ZERO. Uma correcao nova zera, mas alguem precisou escreve-la, e para escreve-la precisou descobrir a interacao antes. Ressalva honesta: os parametros de escassez foram escolhidos para que os recursos restringissem, entao 65% nao e taxa esperada em operacao.");
  etapa(s, "Resultados · o que sobreviveu");
  titulo(s, "Diante de regras novas, a correção antiga valeu nada", { tamanho: 34 });
  const lc = (W - 0.8) / 3;
  const col = [
    ["Executor procedural, sem correção", "65%", "falsos negativos", C.cartao, C.bege, C.terracota, C.borda],
    ["Com a correção escrita antes das regras novas", "65%", "idêntico, benefício zero", C.quente, C.terracota, C.terracota, "E9CFC2"],
    ["Planejamento, sem receber ajuste algum", "0%", "em 37 instâncias", C.verde, C.salvia, C.salvia, "CBDCD1"],
  ];
  col.forEach(function (c, i) {
    const x = L + i * (lc + 0.4);
    cartao(s, { x: x, y: 1.95, w: lc, h: 2.72, cor: c[3], borda: c[6] });
    rotulo(s, c[0], { x: x + 0.26, y: 2.16, w: lc - 0.52, cor: c[4], tamanho: 11 });
    numerao(s, c[1], { x: x + 0.26, y: 2.72, w: lc - 0.52, h: 1.2, tamanho: 64, cor: c[5] });
    s.addText(c[2].toUpperCase(), {
      x: x + 0.26, y: 4.02, w: lc - 0.52, h: 0.45, isTextBox: true,
      fontFace: SANS, fontSize: 13, color: C.bege, charSpacing: 0.8,
    });
  });
  faixa(s, { y: 5.0, h: 1.85, cor: C.verde });
  s.addText([
    { text: "O executor procedural depende de " },
    { text: "alguém descobrir cada interação entre regras antes de respeitá-la", options: { bold: true } },
    { text: ". O planejamento lê as regras do domínio e deriva a ordem correta sozinho." },
  ], {
    x: L + 0.34, y: 5.26, w: W - 0.68, h: 1.4, isTextBox: true,
    fontFace: SERIF, fontSize: 23, color: C.escuro, lineSpacingMultiple: 1.1, valign: "top",
  });
}

// ===========================================================  11  busca cega
{
  const s = novo("Este slide fecha o buraco que todos os outros deixavam. Ate aqui o planejamento so tinha sido comparado contra um programa escrito a mao. Faltava a terceira possibilidade: pegar o MESMO modelo declarativo e varrer com busca cega. Se funcionasse, o merito seria da modelagem e nao do planejador, e falar em Planejamento Automatizado seria inflar o que usamos. Nao funciona.");
  etapa(s, "Resultados · e se a busca fosse trivial?");
  titulo(s, "O mérito é da modelagem ou do planejador?");
  s.addText([
    { text: "Pegamos o " },
    { text: "mesmo", options: { bold: true } },
    { text: " modelo declarativo e o varremos com busca cega, sem heurística nenhuma. Se ela resolvesse, chamar o nosso trabalho de Planejamento Automatizado seria inflar o que de fato usamos." },
  ], {
    x: L, y: 1.85, w: W, h: 1.2, isTextBox: true,
    fontFace: SANS, fontSize: 21, color: C.medio, lineSpacingMultiple: 1.12, valign: "top",
  });
  const lc = (W - 0.4) / 2;
  const lados = [
    ["Busca cega sobre o mesmo modelo", "5 a 6", "pacientes, e para", "Expande de 112 a 934 vezes mais estados.", C.quente, C.terracota, "E9CFC2"],
    ["Busca heurística, o que o projeto usa", "14 a 20", "pacientes, com garantia de ótimo", "Um turno real de ACS tem de 10 a 15 visitas.", C.verde, C.salvia, "CBDCD1"],
  ];
  lados.forEach(function (d, i) {
    const x = L + i * (lc + 0.4);
    cartao(s, { x: x, y: 3.2, w: lc, h: 2.68, cor: d[4], borda: d[6] });
    rotulo(s, d[0], { x: x + 0.28, y: 3.42, w: lc - 0.56, cor: d[5] });
    numerao(s, d[1], { x: x + 0.28, y: 3.86, w: lc - 0.56, h: 1.1, tamanho: 58, cor: d[5] });
    s.addText(d[2].toUpperCase(), {
      x: x + 0.28, y: 4.98, w: lc - 0.56, h: 0.4, isTextBox: true,
      fontFace: SANS, fontSize: 13, color: C.bege, charSpacing: 0.8,
    });
    corpo(s, d[3], { x: x + 0.28, y: 5.36, w: lc - 0.56, h: 0.5, tamanho: 18 });
  });
  fecho(s, [
    { text: "Declaratividade sozinha não escala. Busca sozinha não absorve regra nova. " },
    { text: "Planejamento Automatizado é o nome da combinação das duas.", options: { bold: true } },
  ], { y: 6.15 });
}

// ===========================================================  12  verificacao
{
  const s = novo("A maior ameaca a validade do trabalho estava aqui: todos os numeros saem de um planejador que nos mesmos escrevemos, e um bug exatamente desse tipo ja tinha acontecido, o da hipotese de nomes unicos no grounding, que fez o planejador provar inviabilidade onde havia plano. Os casos inviaveis importam tanto quanto os viaveis: concordar que NAO existe plano exercita o grounding de outro jeito.");
  etapa(s, "Validade");
  titulo(s, "Como sabemos que isso não é um bug nosso");
  const le = 4.5;
  cartao(s, { x: L, y: 2.3, w: le, h: 2.5, cor: C.verde, borda: "CBDCD1" });
  numerao(s, "13 de 13", { x: L + 0.2, y: 2.75, w: le - 0.4, h: 1.2, tamanho: 50, cor: C.salvia, align: "center" });
  s.addText("INSTÂNCIAS EM CONCORDÂNCIA", {
    x: L + 0.2, y: 4.05, w: le - 0.4, h: 0.45, isTextBox: true,
    fontFace: SANS, fontSize: 13, color: C.bege, align: "center", charSpacing: 0.8,
  });
  s.addText([
    { text: "Submetemos os mesmos arquivos ao " },
    { text: "pyperplan", options: { bold: true } },
    { text: ", do grupo de Malte Helmert, em Basileia, o mesmo grupo do Fast Downward. Ele tem parser, grounding e busca próprios, e não compartilha uma linha com o nosso código.\n\nConcordância total sobre viabilidade e sobre o comprimento mínimo do plano, incluindo os dois casos " },
    { text: "inviáveis", options: { bold: true } },
    { text: " e o domínio estendido." },
  ], {
    x: L + le + 0.5, y: 2.1, w: W - le - 0.5, h: 3.1, isTextBox: true,
    fontFace: SANS, fontSize: 20, color: C.medio, lineSpacingMultiple: 1.14, valign: "top",
  });
  fecho(s, "A maior ameaça à validade do trabalho deixou de estar em aberto.", { y: 6.1 });
}

// ===========================================================  13  demonstracao
{
  const s = novo("No HTML esta demonstracao roda VIVA dentro do slide. Aqui ela esta como storyboard, e o link abre a versao viva. Navegue pelos sete passos. O ponto alto e o quarto e o quinto: as duas rotas candidatas custam os MESMOS 94 minutos de caminhada, porque sao a mesma volta percorrida em sentidos opostos, e ainda assim uma cumpre a norma e a outra nao. Em p4, de urgencia baixa, na primeira parada, enquanto p7, de urgencia alta, so viria na sexta.");
  etapa(s, "Demonstração · o sistema rodando");
  titulo(s, "Da microárea inteira até o roteiro do agente", { y: 0.72, h: 0.72, tamanho: 34 });

  const legendas = [
    "1. a microárea inteira", "2. seleção do turno", "3. rota candidata",
    "4. REPROVADA pelo protocolo", "5. outra rota, mesma distância",
    "6. aprovada", "7. o roteiro final",
  ];
  const lw = 2.42, lh = 1.76, g = 0.24;
  for (let i = 0; i < 7; i++) {
    const linha = i < 4 ? 0 : 1;
    const naLinha = linha === 0 ? i : i - 4;
    const n = linha === 0 ? 4 : 3;
    const x0 = (13.33 - (n * lw + (n - 1) * g)) / 2;
    const x = x0 + naLinha * (lw + g);
    const y = 1.66 + linha * (lh + 0.53);
    s.addImage({
      path: path.join(IMG, "passo" + i + ".jpg"),
      x: x, y: y, w: lw, h: lh,
    });
    s.addText(legendas[i], {
      x: x, y: y + lh + 0.04, w: lw, h: 0.4, isTextBox: true,
      fontFace: SANS, fontSize: 13,
      bold: i === 3, color: i === 3 ? C.terracota : C.bege,
      align: "center",
    });
  }
  s.addText([
    { text: "As duas rotas candidatas custam os mesmos 94 minutos de caminhada: são a mesma volta percorrida em sentidos opostos. ", options: {} },
    { text: "Uma cumpre a norma e a outra não.", options: { bold: true } },
  ], {
    x: L, y: 6.14, w: W, h: 0.62, isTextBox: true,
    fontFace: SERIF, fontSize: 19, color: C.escuro, valign: "top",
  });
  s.addText("Versão viva, navegável: apresentacao/3/demonstracao-do-pipeline.html", {
    x: L, y: 6.82, w: W, h: 0.38, isTextBox: true,
    fontFace: SANS, fontSize: 13, color: C.terracota, bold: true,
    hyperlink: { url: "demonstracao-do-pipeline.html",
                 tooltip: "abre a demonstracao viva no navegador" },
  });
}

// ===========================================================  14  fecho
{
  const s = novo("Fecho. O trunfo do trabalho nao e ter usado Planning. E termos medido COMO ele ajuda neste problema, inclusive descobrindo que a resposta nao era a que esperavamos. Se a banca perguntar o que sobrou: declaratividade com efeito medido, e prova de inviabilidade. Se perguntar o que caiu: economia de tempo e exclusividade de capacidade. E a frase final: nenhuma das duas metades sozinha resolve.");
  etapa(s, "Conclusão");
  titulo(s, "A hipótese que sobreviveu aos experimentos");
  faixa(s, { y: 1.95, h: 2.0, cor: C.verde });
  s.addText("“Manter a norma como especificação declarativa preserva a corretude do sistema diante de regras novas, a um custo de busca que ainda cabe num turno real.”", {
    x: L + 0.34, y: 2.2, w: W - 0.68, h: 1.55, isTextBox: true,
    fontFace: SERIF, fontSize: 25, italic: true, color: C.escuro,
    lineSpacingMultiple: 1.12, valign: "top",
  });
  const lc = (W - 0.4) / 2;
  const metades = [
    ["Tire a camada declarativa", "O programa procedural volta a falhar assim que entra uma regra que ninguém previu ao escrevê-lo."],
    ["Tire a busca heurística", "Varrer o mesmo modelo sem heurística para em 5 ou 6 pacientes, e um turno real tem de 10 a 15."],
  ];
  metades.forEach(function (m, i) {
    const x = L + i * (lc + 0.4);
    cartao(s, { x: x, y: 4.25, w: lc, h: 1.85 });
    rotulo(s, m[0], { x: x + 0.28, y: 4.46, w: lc - 0.56, cor: C.terracota });
    corpo(s, m[1], { x: x + 0.28, y: 4.86, w: lc - 0.56, h: 1.1, tamanho: 20 });
  });
  fecho(s, [
    { text: "O trunfo do trabalho não é ter usado Planning. É termos medido " },
    { text: "como", options: { bold: true } },
    { text: " ele ajuda, inclusive descobrindo que a resposta não era a que esperávamos." },
  ], { y: 6.35 });
}

pres.writeFile({ fileName: SAIDA }).then(function () {
  console.log("gerado:", SAIDA);
});
