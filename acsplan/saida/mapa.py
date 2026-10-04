"""
Saida visual: mapa da rota e demonstracao passo a passo do pipeline.

Os dois arquivos gerados aqui sao HTML autocontido, com os dados embutidos
como JSON. Nao ha servidor, nao ha build: abre no navegador e funciona. A
unica dependencia externa e a biblioteca de mapas e o mosaico de ladrilhos
do OpenStreetMap, ambos carregados por CDN, o que exige rede no momento de
ABRIR o arquivo, nao de gera-lo.

As coordenadas sao reais (Porto Alegre). Os dados clinicos sao ficticios.
"""

from __future__ import annotations

import json
import os

from ..dados import modelos

PALETA = {
    "escuro": "#33291F", "medio": "#5C4F41", "bege": "#8A7A67",
    "terracota": "#B35C38", "salvia": "#4A6B5B", "dourado": "#BF9000",
    "cartao": "#FFFDF8", "borda": "#E6DCCB",
    "faixa_quente": "#F3DFD3", "faixa_salvia": "#DDE7E0",
}

COR_URGENCIA = {3: PALETA["terracota"], 2: PALETA["dourado"], 1: PALETA["salvia"]}
ROTULO_URGENCIA = {3: "alta", 2: "media", 1: "baixa"}


def _pacientes_para_json(dados: dict, intervalo: int) -> list[dict]:
    """Usa a microarea INTEIRA, nao so quem a politica selecionou.

    A primeira etapa da demonstracao precisa mostrar o problema antes do
    corte, e as etapas seguintes precisam dos adiados para desenha-los
    apagados.
    """
    saida = []
    for p in dados.get("_todos_pacientes") or dados["pacientes"]:
        nivel = modelos.nivel_urgencia(p, intervalo)
        exige = [rotulo for campo, rotulo in (
            ("requer_pa", "pressao arterial"),
            ("requer_glicemia", "glicemia capilar"),
            ("requer_temperatura", "temperatura axilar"),
            ("requer_antropometria", "antropometria"),
            ("requer_orientacao_medicacao", "orientacao de medicacao"),
            ("requer_vacinal", "caderneta vacinal")) if p.get(campo)]
        saida.append({
            "id": p["id"], "nome": p.get("nome", p["id"]),
            "lat": p["lat"], "lon": p["lon"],
            "grupo": p.get("grupo", ""),
            "condicoes": p.get("condicoes", ""),
            "urgencia": nivel, "urgencia_rotulo": ROTULO_URGENCIA[nivel],
            "cor": COR_URGENCIA[nivel],
            "atraso": modelos.atraso_em_dias(p, intervalo),
            "exige": exige,
        })
    return saida


def _pontos_da_rota(dados: dict, rota: list[str]) -> list[dict]:
    por_id = {p["id"]: p
              for p in (dados.get("_todos_pacientes") or dados["pacientes"])}
    por_id[dados["ubs"]["id"]] = dados["ubs"]
    return [por_id[i] for i in rota if i in por_id]


def _arredondar(linha) -> list[list[float]]:
    """5 casas decimais e cerca de 1 metro: o suficiente para desenhar."""
    return [[round(p[0], 5), round(p[1], 5)] for p in (linha or [])]


def montar_contexto(estado: dict) -> dict:
    """Reune num unico dicionario tudo o que as duas paginas precisam."""
    from ..logica import executor_guloso
    from . import roteiro as saida_roteiro

    dados = estado["dados"]
    roteamento = estado["roteamento"]
    plano = estado["planejador"]
    laco = estado.get("laco")
    intervalo = estado["intervalo"]

    ubs = dados["ubs"]
    pacientes = _pacientes_para_json(dados, intervalo)
    coord = {p["id"]: [p["lat"], p["lon"]] for p in pacientes}
    coord[ubs["id"]] = [ubs["lat"], ubs["lon"]]

    paradas = []
    if plano is not None and plano.sucesso:
        custos = executor_guloso.custos_do_dominio(estado["caminho_dominio"])
        for parada in saida_roteiro.montar(plano.plano, dados, custos,
                                           roteamento["matriz"]):
            paciente = parada["paciente"] or {}
            paradas.append({
                "ordem": parada["ordem"],
                "id": paciente.get("id", ""),
                "nome": paciente.get("nome", ""),
                "tarefas": parada["tarefas"],
                "repor": parada["repor"],
                "desvio": parada["desvio_ubs"],
                "minuto": parada["minutos_chegada"],
            })

    # Caminho pelas ruas, so para desenho. Os custos continuam vindo da
    # camada de distancias; ver o cabecalho de geo/trajeto.py.
    from ..geo import trajeto as tracador
    traco = tracador.tracar(_pontos_da_rota(dados, roteamento["rota"]))
    desvios = {}
    for parada in paradas:
        if parada["desvio"] and parada["id"]:
            alvo = next((p for p in dados["pacientes"]
                         if p["id"] == parada["id"]), None)
            if alvo is not None:
                linha = tracador.tracar_ida_e_volta(alvo, ubs)
                if linha:
                    desvios[parada["id"]] = _arredondar(linha)

    selecao = dados.get("_selecao", {})
    tentativas = []
    if laco is not None:
        from ..logica import realimentacao
        base = dict(roteamento)
        for i, t in enumerate(laco.tentativas, 1):
            # a causa concreta da reprovacao, e nao "espaco exaurido", que e
            # o motivo da BUSCA e nao explica nada a quem le.
            explicacao, culpados = "", []
            if not t.sucesso:
                base["rota"] = t.rota
                causa = realimentacao.explicar_reprovacao(dados, base)
                explicacao = causa["texto"]
                culpados = [c for c in (causa.get("baixo"), causa.get("alto")) if c]
            invertida = (i > 1 and realimentacao.mesma_volta_invertida(
                t.rota, laco.tentativas[i - 2].rota))
            traco_t = tracador.tracar(_pontos_da_rota(dados, t.rota))
            tentativas.append({
                "numero": i, "rota": t.rota, "custo_rota": t.custo_rota,
                "linha": _arredondar(traco_t["linha"]) if traco_t else [],
                "sucesso": t.sucesso, "motivo": t.motivo,
                "explicacao": explicacao, "invertida": bool(invertida),
                "culpados": culpados,
                "custo_plano": t.custo_plano, "acoes": t.acoes,
                "expandidos": t.expandidos, "segundos": round(t.segundos, 3),
            })

    return {
        "ubs": {"id": ubs["id"], "nome": ubs.get("nome", "Unidade de saude"),
                "lat": ubs["lat"], "lon": ubs["lon"]},
        "pacientes": pacientes,
        "coord": coord,
        "rota": roteamento["rota"],
        "custo_rota": roteamento["custo_rota"],
        "trajeto": {
            "linha": _arredondar(traco["linha"]) if traco else [],
            "metros": round(traco["metros"]) if traco else 0,
            "minutos": round(traco["segundos"] / 60) if traco else 0,
            "provedor": "ruas" if traco else "reta",
        },
        "desvios": desvios,
        "metodo": roteamento["metodo"],
        "provedor": roteamento["provedor_distancia"],
        "precedencias": {k: sorted(v) for k, v in
                         (roteamento.get("precedencias") or {}).items()},
        "plano": {
            "sucesso": bool(plano is not None and plano.sucesso),
            "custo": plano.custo if plano is not None and plano.sucesso else 0,
            "acoes": plano.tamanho if plano is not None and plano.sucesso else 0,
            "expandidos": plano.expandidos if plano is not None else 0,
            "segundos": round(plano.segundos, 3) if plano is not None else 0,
            "motivo": "" if plano is None or plano.sucesso else plano.motivo,
        },
        "paradas": paradas,
        "selecao": {
            "ativa": bool(selecao.get("ativa")),
            "selecionados": selecao.get("selecionados", []),
            "adiados": selecao.get("adiados", []),
            "inadiaveis": selecao.get("inadiaveis", []),
            "orcamento": selecao.get("orcamento_minutos"),
        },
        "tentativas": tentativas,
        "paleta": PALETA,
    }


# ---------------------------------------------------------------------------
#  pagina 1: mapa da rota final
# ---------------------------------------------------------------------------

MAPA_HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rota do turno</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
  :root {
    --escuro:#33291F; --medio:#5C4F41; --bege:#8A7A67; --terracota:#B35C38;
    --salvia:#4A6B5B; --cartao:#FFFDF8; --borda:#E6DCCB; --quente:#F3DFD3;
  }
  * { box-sizing:border-box; }
  body { margin:0; font-family:Calibri,Carlito,"Segoe UI",sans-serif;
         color:var(--medio);
         background:linear-gradient(135deg,#FEFCF7 0%,#F9F2E4 45%,#F2E7D2 100%); }
  header { padding:18px 24px 10px; }
  h1 { font-family:Cambria,Georgia,serif; color:var(--escuro);
       margin:0 0 4px; font-size:26px; }
  .sub { font-size:15px; color:var(--bege); }
  .corpo { display:grid; grid-template-columns:1fr 380px; gap:16px;
           padding:0 24px 24px; align-items:start; }
  .corpo > div:first-child { min-height:0; }
  #mapa { height:72vh; min-height:460px; border-radius:12px;
          border:1px solid var(--borda); }
  .painel { background:var(--cartao); border:1px solid var(--borda);
            border-radius:12px; padding:16px; max-height:72vh; overflow:auto; }
  .painel h2 { font-family:Cambria,Georgia,serif; color:var(--escuro);
               font-size:17px; margin:0 0 10px; }
  .num { display:flex; gap:14px; margin-bottom:14px; flex-wrap:wrap; }
  .num div { flex:1; min-width:96px; }
  .num b { display:block; font-family:Cambria,Georgia,serif;
           font-size:26px; color:var(--escuro); line-height:1.1; }
  .num span { font-size:12px; color:var(--bege); text-transform:uppercase;
              letter-spacing:.04em; }
  .parada { border-top:1px solid var(--borda); padding:9px 0; }
  .parada .cab { display:flex; align-items:center; gap:8px; }
  .bolha { width:22px; height:22px; border-radius:50%; color:#fff;
           font-size:12px; font-weight:bold; display:flex;
           align-items:center; justify-content:center; flex:none; }
  .parada .nome { font-weight:bold; color:var(--escuro); }
  .parada ul { margin:5px 0 0 30px; padding:0; font-size:14px; }
  .aviso { color:var(--terracota); font-weight:bold; font-size:13px;
           margin-left:30px; }
  .legenda { font-size:13px; color:var(--bege); margin-top:12px;
             border-top:1px solid var(--borda); padding-top:10px; }
  .pino { border-radius:50%; border:2px solid #fff; color:#fff;
          font-weight:bold; font-size:12px; text-align:center;
          box-shadow:0 1px 4px rgba(0,0,0,.4); }
  #semfundo { display:none; position:absolute; z-index:500; left:50%;
              top:14px; transform:translateX(-50%); background:var(--cartao);
              border:1px solid var(--borda); border-radius:8px;
              padding:7px 14px; font-size:13px; color:var(--bege); }
  @media (max-width:900px){ .corpo{grid-template-columns:1fr;} #mapa{height:52vh;} }
</style>
</head>
<body>
<header>
  <h1>Rota do turno, com o protocolo ja formalizado</h1>
  <div class="sub" id="sub"></div>
</header>
<div class="corpo">
  <div style="position:relative">
    <div id="semfundo">Sem o fundo cartografico: a rota e as paradas continuam corretas.</div>
    <div id="mapa"></div>
  </div>
  <div class="painel">
    <div class="num" id="numeros"></div>
    <h2>Roteiro parada a parada</h2>
    <div id="paradas"></div>
    <div class="legenda" id="legenda"></div>
  </div>
</div>
<script id="dados" type="application/json">__DADOS__</script>
<script>
const D = JSON.parse(document.getElementById("dados").textContent);
const mapa = L.map("mapa", {scrollWheelZoom:true});
// Ladrilhos. Os servidores voluntarios do OpenStreetMap devolvem HTTP 403
// para paginas abertas de file://, porque a politica de uso deles exige que
// a requisicao venha de um site identificado. O provedor principal passa a
// ser o Esri World Street Map, que nao exige chave; se ele falhar, cai para
// o OSM; se os dois falharem, a pagina fica com fundo neutro e a rota
// continua perfeitamente legivel.
var PROVEDORES = [
  {url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
   att: 'Ladrilhos &copy; Esri. Fontes: Esri, HERE, Garmin, OpenStreetMap e colaboradores'},
  {url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
   att: '&copy; colaboradores do <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}
];
var iProvedor = 0, falhasLadrilho = 0, base = null;
function montarBase() {
  if (base) { mapa.removeLayer(base); base = null; }
  var p = PROVEDORES[iProvedor];
  if (!p) {
    var aviso = document.getElementById("semfundo");
    if (aviso) { aviso.style.display = "block"; }
    return;
  }
  falhasLadrilho = 0;
  base = L.tileLayer(p.url, {maxZoom: 19, attribution: p.att});
  base.on("tileerror", function () {
    falhasLadrilho += 1;
    if (falhasLadrilho === 3) { iProvedor += 1; montarBase(); }
  });
  base.addTo(mapa);
}
montarBase();

function pino(texto, cor, tamanho) {
  const t = tamanho || 26;
  return L.divIcon({
    className: "",
    html: `<div class="pino" style="background:${cor};width:${t}px;height:${t}px;line-height:${t-4}px">${texto}</div>`,
    iconSize: [t, t], iconAnchor: [t/2, t/2]
  });
}

const ordemPorId = {};
D.paradas.forEach(p => ordemPorId[p.id] = p);

const pontos = [];
D.rota.forEach(id => { if (D.coord[id]) pontos.push(D.coord[id]); });
// o traçado segue as ruas quando o serviço de rotas respondeu; senão, reta
const linhaRota = (D.trajeto && D.trajeto.linha.length) ? D.trajeto.linha : pontos;
L.polyline(linhaRota, {color:"#5C4F41", weight:4, opacity:.8}).addTo(mapa);

L.marker([D.ubs.lat, D.ubs.lon], {icon: pino("U", "#33291F", 30)})
 .addTo(mapa).bindPopup(`<b>${D.ubs.nome}</b><br>ponto de partida, de retorno e de reposicao`);

D.pacientes.forEach(p => {
  const parada = ordemPorId[p.id];
  const rotulo = parada ? String(parada.ordem) : "";
  // quem nao entrou no turno aparece apagado e menor: continua no mapa,
  // porque faz parte da microarea, mas nao disputa a leitura da rota.
  const m = L.marker([p.lat, p.lon], {
    icon: pino(rotulo, parada ? p.cor : "#C9BFAF", parada ? 26 : 17,
               parada ? 1 : 0.7)}).addTo(mapa);
  let html = `<b>${p.nome}</b><br>${p.grupo}`;
  if (!parada) html += `<br><i>adiado para o proximo turno</i>`;
  if (p.condicoes) html += `<br><i>${p.condicoes}</i>`;
  html += `<br>urgencia ${p.urgencia_rotulo}, ${p.atraso} dia(s) de atraso`;
  if (parada) {
    html += `<br><br><b>No plano (chegada aos ${parada.minuto} min):</b><ul style="margin:4px 0 0 16px;padding:0">`;
    parada.tarefas.forEach(t => html += `<li>${t}</li>`);
    html += "</ul>";
    if (parada.desvio) html += `<span style="color:#B35C38"><b>desvio ate a unidade antes desta visita</b></span>`;
  }
  m.bindPopup(html);
});

// desvios de reposicao, tracejados ate a unidade
D.paradas.filter(p => p.desvio).forEach(p => {
  if (!D.coord[p.id]) return;
  const caminho = (D.desvios && D.desvios[p.id] && D.desvios[p.id].length)
    ? D.desvios[p.id] : [D.coord[p.id], [D.ubs.lat, D.ubs.lon]];
  L.polyline(caminho, {color:"#B35C38", weight:3, dashArray:"7 6",
                       opacity:.85}).addTo(mapa);
});

mapa.fitBounds(L.polyline(pontos.concat([[D.ubs.lat, D.ubs.lon]])).getBounds(),
               {padding:[40,40]});

const traj = D.trajeto || {provedor:"reta"};
document.getElementById("sub").textContent =
  `${D.paradas.length} visitas  ·  ${D.custo_rota} min de caminhada  ·  ` +
  `roteirizador: ${D.metodo}  ·  distancias: ${D.provedor}` +
  (traj.provedor === "ruas"
     ? `  ·  tracado pelas ruas: ${(traj.metros/1000).toFixed(1)} km, ${traj.minutos} min a pe`
     : "") +
  `  ·  dados clinicos ficticios, coordenadas reais`;

document.getElementById("numeros").innerHTML = `
  <div><b>${D.plano.custo}</b><span>min de turno</span></div>
  <div><b>${D.paradas.length}</b><span>visitas</span></div>
  <div><b>${D.plano.acoes}</b><span>acoes no plano</span></div>`;

document.getElementById("paradas").innerHTML = D.paradas.map(p => {
  const cor = (D.pacientes.find(x => x.id === p.id) || {}).cor || "#5C4F41";
  return `<div class="parada">
    <div class="cab"><div class="bolha" style="background:${cor}">${p.ordem}</div>
      <span class="nome">${p.nome}</span></div>
    ${p.desvio ? '<div class="aviso">desvio ate a unidade antes de comecar</div>' : ""}
    <ul>${p.tarefas.map(t => `<li>${t}</li>`).join("")}</ul>
  </div>`;
}).join("");

document.getElementById("legenda").innerHTML =
  `Cor do pino: <b style="color:#B35C38">urgencia alta</b>, ` +
  `<b style="color:#BF9000">media</b>, <b style="color:#4A6B5B">baixa</b>. ` +
  `Linha cheia: a rota. Linha tracejada: desvio de reposicao decidido pelo planejamento. ` +
  `Pinos apagados e sem numero: familias adiadas para o proximo turno.` +
  (traj.provedor === "ruas"
    ? ` O tracado segue o caminho de pedestre pelas ruas (OSRM, perfil a pe). Os
        minutos do plano continuam vindo do modelo de distancias do projeto, e nao
        deste tracado.`.replace(/\s+/g, " ")
    : ` O servico de rotas nao respondeu, entao o tracado liga as coordenadas em
        linha reta.`.replace(/\s+/g, " "));
</script>
</body>
</html>
"""


def gerar_mapa(estado: dict, caminho: str) -> str:
    contexto = montar_contexto(estado)
    html = MAPA_HTML.replace("__DADOS__", json.dumps(contexto, ensure_ascii=True))
    os.makedirs(os.path.dirname(os.path.abspath(caminho)) or ".", exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write(html)
    return caminho


# ---------------------------------------------------------------------------
#  pagina 2: demonstracao passo a passo do pipeline
# ---------------------------------------------------------------------------

def _nota_rota_nova(ctx: dict, tentativa: dict) -> str:
    """Compara a rota nova com a anterior, para a nota do slide."""
    anterior = ctx["tentativas"][tentativa["numero"] - 2]
    delta = tentativa["custo_rota"] - anterior["custo_rota"]
    if delta == 0:
        igual = ("E a mesma volta no sentido contrario: "
                 if tentativa.get("invertida") else "Mesma distancia da anterior: ")
        return (igual + "o custo de caminhada e identico ao da rota reprovada. "
                "O que separa uma rota valida de uma invalida aqui nao e o "
                "comprimento, e a ordem em que as condicoes legais conseguem "
                "ser satisfeitas.")
    if delta > 0:
        return (f"Custa {delta} min a mais de caminhada que a rota reprovada. "
                "O preco da conformidade aparece aqui, e e mensuravel.")
    return (f"Custa {-delta} min a menos que a rota reprovada: a ordem que "
            "cumpre a norma nem sempre e a mais cara.")


def montar_passos(ctx: dict) -> list[dict]:
    """Narra o pipeline com os numeros que de fato sairam desta execucao."""
    sel = ctx["selecao"]
    passos: list[dict] = []
    total = len(ctx["pacientes"])
    altas = sum(1 for p in ctx["pacientes"] if p["urgencia"] == 3)

    frase_altas = ("Nenhuma esta em urgencia alta." if altas == 0 else
                   "Uma esta em urgencia alta." if altas == 1 else
                   f"{altas} estao em urgencia alta.")
    passos.append({
        "etapa": "PONTO DE PARTIDA",
        "titulo": "A microarea inteira",
        "texto": (f"Sao {total} familias cadastradas na microarea, com a unidade "
                  f"de saude como ponto de partida e de retorno. {frase_altas} "
                  "Nenhum turno cabe todas elas."),
        "nota": "Coordenadas reais de Porto Alegre. Dados clinicos ficticios.",
        "mapa": {"modo": "todos"},
        "metricas": [{"valor": total, "rotulo": "familias"},
                     {"valor": altas, "rotulo": "urgencia alta"}],
    })

    if sel["ativa"]:
        passos.append({
            "etapa": "PASSO 1",
            "titulo": "Selecao: quem entra no turno",
            "texto": (f"A politica ordena por prioridade clinica e por atraso em "
                      f"relacao ao intervalo maximo, e corta no orcamento de "
                      f"{sel['orcamento'] or '-'} minutos. Entram "
                      f"{len(sel['selecionados'])}; {len(sel['adiados'])} ficam "
                      "para o proximo turno, em cinza no mapa."),
            "nota": "Esta camada ainda nao sabe nada sobre a lei. Ela so escolhe.",
            "mapa": {"modo": "selecao"},
            "metricas": [{"valor": len(sel["selecionados"]), "rotulo": "no turno"},
                         {"valor": len(sel["adiados"]), "rotulo": "adiados"}],
        })

    for t in ctx["tentativas"]:
        passos.append({
            "etapa": f"PASSO 2{'' if t['numero'] == 1 else ' (de novo)'}",
            "titulo": (f"Rota candidata {t['numero']}"
                       if t["numero"] > 1 else "Roteamento: em que ordem visitar"),
            "texto": (
                f"A camada geometrica devolve uma sequencia de paradas com "
                f"{t['custo_rota']} minutos de caminhada. Ela otimiza distancia, "
                "e so: nao sabe o que a lei exige dentro de cada casa, nem que "
                "urgencia alta tem de ser atendida antes de urgencia baixa."
                + (" Esta rota e a anterior percorrida ao contrario, e por isso "
                   "custa exatamente o mesmo." if t.get("invertida") else "")),
            "nota": (_nota_rota_nova(ctx, t) if t["numero"] > 1 else
                     "A rota entra congelada no passo seguinte."),
            "mapa": {"modo": "rota", "rota": t["rota"], "estado": "neutro",
                     "linha": t.get("linha") or []},
            "metricas": [{"valor": t["custo_rota"], "rotulo": "min de caminhada"}],
        })
        if t["sucesso"]:
            passos.append({
                "etapa": "PASSO 3",
                "titulo": "O protocolo cabe nesta rota",
                "texto": (
                    f"O planejamento encontrou uma sequencia de {t['acoes']} "
                    f"acoes, de custo {t['custo_plano']} minutos, que cumpre as "
                    "condicoes do art. 3o par. 4o em todas as paradas: curso "
                    "tecnico, equipamento, supervisao ativa, insumo disponivel e "
                    "encaminhamento quando o procedimento o exige."
                    + (" Nesta ordem a urgencia alta vem antes da baixa, que era "
                       "exatamente o que faltava na rota anterior."
                       if t["numero"] > 1 else "")),
                "nota": (f"{t['expandidos']} estados expandidos em "
                         f"{t['segundos']}s, com garantia de otimalidade."),
                "mapa": {"modo": "rota", "rota": t["rota"],
                         "estado": "aprovada", "linha": t.get("linha") or []},
                "metricas": [{"valor": t["acoes"], "rotulo": "acoes"},
                             {"valor": t["custo_plano"], "rotulo": "min de turno"}],
            })
        else:
            passos.append({
                "etapa": "PASSO 3",
                "titulo": "O protocolo NAO cabe nesta rota",
                "texto": ("Por que esta rota nao serve: "
                          + (t.get("explicacao") or
                             "nesta ordem de paradas nenhuma sequencia de acoes "
                             "satisfaz as condicoes legais de todas as visitas.")),
                "nota": ("O planejamento nao disse que nao encontrou: ele exauriu "
                         "o espaco de estados e DEMONSTROU que nao existe. E a "
                         "inviabilidade e sensivel a ordem, isto e, vale para esta "
                         "rota e nao para o turno. Por isso vale voltar ao passo 2."),
                "mapa": {"modo": "rota", "rota": t["rota"],
                         "estado": "reprovada", "linha": t.get("linha") or [],
                         "destaques": t.get("culpados") or []},
                "metricas": [{"valor": t["expandidos"], "rotulo": "estados exauridos"},
                             {"valor": f"{t['segundos']}s", "rotulo": "para provar"}],
            })

    if ctx["plano"]["sucesso"]:
        com_desvio = sum(1 for p in ctx["paradas"] if p["desvio"])
        passos.append({
            "etapa": "RESULTADO",
            "titulo": "O protocolo formalizado sobre a rota",
            "texto": ("A saida nao e uma linha no mapa, e um roteiro: em cada "
                      "parada, o que fazer, em que ordem, e quando sair da rota "
                      "para repor material na unidade. "
                      + (f"Neste turno o plano decidiu {com_desvio} desvio(s) de "
                         "reposicao, em tracejado." if com_desvio else
                         "Neste turno nenhum desvio foi necessario.")),
            "nota": ("Trocar o roteirizador nao muda uma linha do dominio. "
                     "Mudar a lei nao muda uma linha do codigo de busca."),
            "mapa": {"modo": "final", "rota": ctx["rota"], "estado": "aprovada",
                     "linha": ctx["trajeto"]["linha"]},
            "metricas": [{"valor": len(ctx["paradas"]), "rotulo": "visitas"},
                         {"valor": ctx["plano"]["custo"], "rotulo": "min de turno"},
                         {"valor": ctx["plano"]["acoes"], "rotulo": "acoes"}],
        })
    return passos


DEMO_HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Como o sistema monta um turno</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
  :root {
    --escuro:#33291F; --medio:#5C4F41; --bege:#8A7A67; --terracota:#B35C38;
    --salvia:#4A6B5B; --cartao:#FFFDF8; --borda:#E6DCCB;
    --quente:#F3DFD3; --verde:#DDE7E0;
  }
  * { box-sizing:border-box; }
  html, body { height:100%; margin:0; }
  body { font-family:Calibri,Carlito,"Segoe UI",sans-serif; color:var(--medio);
         background:linear-gradient(135deg,#FEFCF7 0%,#F9F2E4 45%,#F2E7D2 100%);
         display:flex; flex-direction:column; overflow:hidden; }
  header { padding:14px 30px 8px; display:flex; align-items:baseline; gap:14px;
           flex-wrap:wrap; }
  header h1 { font-family:Cambria,Georgia,serif; font-size:21px; margin:0;
              color:var(--escuro); }
  header .ctx { font-size:13px; color:var(--bege); }
  main { flex:1; display:grid; grid-template-columns:1fr 440px; gap:18px;
         padding:0 30px 10px; min-height:0; }
  main > div:first-child { position:relative; min-height:0; }
  #mapa { border-radius:14px; border:1px solid var(--borda);
          height:100%; min-height:0; }
  .lado { display:flex; flex-direction:column; min-height:0; }
  .cartao { background:var(--cartao); border:1px solid var(--borda);
            border-radius:14px; padding:20px 22px; flex:1; overflow:auto; }
  .etapa { font-size:13px; font-weight:bold; letter-spacing:.08em;
           color:var(--terracota); text-transform:uppercase; }
  .cartao h2 { font-family:Cambria,Georgia,serif; color:var(--escuro);
               font-size:27px; margin:6px 0 12px; line-height:1.2; }
  .cartao p { font-size:17px; line-height:1.5; margin:0 0 14px; }
  .nota { font-size:14px; color:var(--bege); border-left:3px solid var(--borda);
          padding-left:12px; font-style:italic; }
  .metricas { display:flex; gap:18px; margin:16px 0 4px; flex-wrap:wrap; }
  .metricas div b { display:block; font-family:Cambria,Georgia,serif;
                    font-size:30px; color:var(--escuro); line-height:1; }
  .metricas div span { font-size:12px; color:var(--bege); text-transform:uppercase;
                       letter-spacing:.04em; }
  .selo { display:inline-block; padding:5px 12px; border-radius:20px;
          font-size:13px; font-weight:bold; margin-bottom:10px; }
  .selo.reprovada { background:var(--quente); color:var(--terracota); }
  .selo.aprovada { background:var(--verde); color:var(--salvia); }
  nav { display:flex; align-items:center; gap:14px; padding:6px 30px 16px; }
  button { font-family:inherit; font-size:15px; padding:8px 18px; cursor:pointer;
           border-radius:8px; border:1px solid var(--borda);
           background:var(--cartao); color:var(--escuro); }
  button:hover { background:var(--quente); }
  button:disabled { opacity:.4; cursor:default; }
  .pontos { display:flex; gap:7px; flex:1; }
  .ponto { width:9px; height:9px; border-radius:50%; background:var(--borda); }
  .ponto.on { background:var(--terracota); }
  .contador { font-size:13px; color:var(--bege); }
  .pino { border-radius:50%; border:2px solid #fff; color:#fff; font-weight:bold;
          font-size:12px; text-align:center; box-shadow:0 1px 4px rgba(0,0,0,.4); }
  #semfundo { display:none; position:absolute; z-index:500; left:50%;
              top:14px; transform:translateX(-50%); background:var(--cartao);
              border:1px solid var(--borda); border-radius:8px;
              padding:7px 14px; font-size:13px; color:var(--bege); }
  @media (max-width:980px){ main{grid-template-columns:1fr; grid-template-rows:46% 1fr;} }
</style>
</head>
<body>
<header>
  <h1>Como o sistema monta um turno de visitas</h1>
  <span class="ctx" id="ctx"></span>
</header>
<main>
  <div style="position:relative">
    <div id="semfundo">Sem o fundo cartografico: a rota e as paradas continuam corretas.</div>
    <div id="mapa"></div>
  </div>
  <div class="lado">
    <div class="cartao">
      <div class="etapa" id="etapa"></div>
      <h2 id="titulo"></h2>
      <div id="selo"></div>
      <p id="texto"></p>
      <div class="metricas" id="metricas"></div>
      <div class="nota" id="nota"></div>
    </div>
  </div>
</main>
<nav>
  <button id="voltar">&larr; Anterior</button>
  <button id="avancar">Proximo &rarr;</button>
  <div class="pontos" id="pontos"></div>
  <span class="contador" id="contador"></span>
</nav>
<script id="dados" type="application/json">__DADOS__</script>
<script>
const D = JSON.parse(document.getElementById("dados").textContent);
const P = D.passos;
let atual = 0;

const mapa = L.map("mapa", {scrollWheelZoom:false, zoomControl:true});
// Ladrilhos. Os servidores voluntarios do OpenStreetMap devolvem HTTP 403
// para paginas abertas de file://, porque a politica de uso deles exige que
// a requisicao venha de um site identificado. O provedor principal passa a
// ser o Esri World Street Map, que nao exige chave; se ele falhar, cai para
// o OSM; se os dois falharem, a pagina fica com fundo neutro e a rota
// continua perfeitamente legivel.
var PROVEDORES = [
  {url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
   att: 'Ladrilhos &copy; Esri. Fontes: Esri, HERE, Garmin, OpenStreetMap e colaboradores'},
  {url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
   att: '&copy; colaboradores do <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}
];
var iProvedor = 0, falhasLadrilho = 0, base = null;
function montarBase() {
  if (base) { mapa.removeLayer(base); base = null; }
  var p = PROVEDORES[iProvedor];
  if (!p) {
    var aviso = document.getElementById("semfundo");
    if (aviso) { aviso.style.display = "block"; }
    return;
  }
  falhasLadrilho = 0;
  base = L.tileLayer(p.url, {maxZoom: 19, attribution: p.att});
  base.on("tileerror", function () {
    falhasLadrilho += 1;
    if (falhasLadrilho === 3) { iProvedor += 1; montarBase(); }
  });
  base.addTo(mapa);
}
montarBase();
const camada = L.layerGroup().addTo(mapa);

function pino(texto, cor, tamanho, opacidade) {
  const t = tamanho || 26;
  const html = '<div class="pino" style="background:' + cor + ';width:' + t +
               'px;height:' + t + 'px;line-height:' + (t - 4) + 'px;opacity:' +
               (opacidade || 1) + '">' + texto + '</div>';
  return L.divIcon({className:"", html: html, iconSize:[t,t], iconAnchor:[t/2,t/2]});
}

const todos = [[D.ubs.lat, D.ubs.lon]].concat(D.pacientes.map(function(p){ return [p.lat, p.lon]; }));
mapa.fitBounds(L.polyline(todos).getBounds(), {padding:[45,45]});

const CORES = {neutro:"#5C4F41", reprovada:"#B35C38", aprovada:"#4A6B5B"};
const ordemFinal = {};
D.paradas.forEach(function(p){ ordemFinal[p.id] = p; });

function desenhar(passo) {
  camada.clearLayers();
  const m = passo.mapa;
  const selecionados = {};
  D.selecao.selecionados.forEach(function(id){ selecionados[id] = true; });

  L.marker([D.ubs.lat, D.ubs.lon], {icon: pino("U", "#33291F", 30)})
   .addTo(camada).bindPopup("<b>" + D.ubs.nome + "</b>");

  const ordemNaRota = {};
  if (m.rota) {
    let i = 0;
    m.rota.forEach(function(id){ if (id !== D.ubs.id) { ordemNaRota[id] = ++i; } });
    const retas = m.rota.map(function(id){ return D.coord[id]; }).filter(Boolean);
    // segue as ruas quando o servico de rotas respondeu; senao, liga em reta
    const pontos = (m.linha && m.linha.length) ? m.linha : retas;
    L.polyline(pontos, {color: CORES[m.estado] || CORES.neutro,
                        weight: m.estado === "neutro" ? 3 : 4,
                        opacity: m.estado === "reprovada" ? 0.55 : 0.85,
                        dashArray: m.estado === "reprovada" ? "9 7" : null
                       }).addTo(camada);
  }

  var destaques = {};
  (m.destaques || []).forEach(function(id){ destaques[id] = true; });

  D.pacientes.forEach(function(p){
    const dentro = !D.selecao.ativa || m.modo === "todos" || selecionados[p.id];
    if (destaques[p.id]) {
      // aro em volta de quem causou a reprovacao, para a explicacao do
      // painel ter onde pousar no mapa
      L.circleMarker([p.lat, p.lon], {radius: 22, color: "#B35C38",
        weight: 3, opacity: 0.95, fill: false, dashArray: "4 4"}).addTo(camada);
    }
    const rotulo = ordemNaRota[p.id] ? String(ordemNaRota[p.id]) : "";
    const cor = dentro ? p.cor : "#C9BFAF";
    const marcador = L.marker([p.lat, p.lon],
        {icon: pino(rotulo, cor, dentro ? 26 : 18, dentro ? 1 : 0.75)}).addTo(camada);
    let html = "<b>" + p.nome + "</b><br>" + p.grupo +
               "<br>urgencia " + p.urgencia_rotulo + ", " + p.atraso + " dia(s) de atraso";
    if (p.exige.length) { html += "<br><br>exige: " + p.exige.join(", "); }
    if (m.modo === "final" && ordemFinal[p.id]) {
      html += "<br><br><b>no plano:</b><ul style='margin:4px 0 0 16px;padding:0'>" +
              ordemFinal[p.id].tarefas.map(function(t){ return "<li>" + t + "</li>"; }).join("") +
              "</ul>";
    }
    marcador.bindPopup(html);
  });

  if (m.modo === "final") {
    D.paradas.filter(function(p){ return p.desvio && D.coord[p.id]; }).forEach(function(p){
      var caminho = (D.desvios && D.desvios[p.id] && D.desvios[p.id].length)
        ? D.desvios[p.id] : [D.coord[p.id], [D.ubs.lat, D.ubs.lon]];
      L.polyline(caminho, {color:"#B35C38", weight:3, dashArray:"7 6",
                           opacity:0.85}).addTo(camada);
    });
  }
}

function mostrar(i) {
  atual = Math.max(0, Math.min(P.length - 1, i));
  const passo = P[atual];
  document.getElementById("etapa").textContent = passo.etapa;
  document.getElementById("titulo").textContent = passo.titulo;
  document.getElementById("texto").textContent = passo.texto;
  document.getElementById("nota").textContent = passo.nota || "";
  const estado = passo.mapa.estado;
  document.getElementById("selo").innerHTML =
    estado === "reprovada" ? '<span class="selo reprovada">rota reprovada pelo protocolo</span>' :
    estado === "aprovada"  ? '<span class="selo aprovada">rota valida sob o protocolo</span>' : "";
  document.getElementById("metricas").innerHTML =
    (passo.metricas || []).map(function(x){
      return "<div><b>" + x.valor + "</b><span>" + x.rotulo + "</span></div>";
    }).join("");
  document.getElementById("contador").textContent = (atual + 1) + " / " + P.length;
  document.getElementById("pontos").innerHTML =
    P.map(function(_, k){ return '<div class="ponto ' + (k === atual ? "on" : "") + '"></div>'; }).join("");
  document.getElementById("voltar").disabled = atual === 0;
  document.getElementById("avancar").disabled = atual === P.length - 1;
  desenhar(passo);
}

document.getElementById("voltar").onclick = function(){ mostrar(atual - 1); };
document.getElementById("avancar").onclick = function(){ mostrar(atual + 1); };
document.addEventListener("keydown", function(e){
  if (e.key === "ArrowRight" || e.key === " ") { mostrar(atual + 1); }
  if (e.key === "ArrowLeft") { mostrar(atual - 1); }
});
document.getElementById("ctx").textContent =
  D.pacientes.length + " familias  ·  roteirizador: " + D.metodo +
  "  ·  distancias: " + D.provedor +
  ((D.trajeto && D.trajeto.provedor === "ruas")
     ? "  ·  tracado pelas ruas (OSRM, perfil a pe)" : "") +
  "  ·  dados clinicos ficticios, coordenadas reais de Porto Alegre";
mostrar(0);
</script>
</body>
</html>
"""


def gerar_demonstracao(estado: dict, caminho: str) -> str:
    contexto = montar_contexto(estado)
    contexto["passos"] = montar_passos(contexto)
    html = DEMO_HTML.replace("__DADOS__", json.dumps(contexto, ensure_ascii=True))
    os.makedirs(os.path.dirname(os.path.abspath(caminho)) or ".", exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write(html)
    return caminho
