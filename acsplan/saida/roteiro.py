"""
Roteiro do turno em linguagem de trabalho.

O plano que o planejador devolve e uma sequencia de acoes instanciadas, com
nomes de predicados e identificadores de objetos. Isso serve para depurar o
dominio e para os experimentos, e nao serve para nada no campo.

Este modulo traduz esse plano no unico artefato que interessa a quem vai
executa-lo: a lista de paradas, na ordem, com o que fazer em cada uma.

Principios adotados
-------------------
- Uma parada por bloco, numerada. Nada de identificadores internos.
- So o essencial. Acoes de bookkeeping do modelo (conferencias, registros
  internos) sao agrupadas ou omitidas; o que aparece e o que muda a conduta.
- Os desvios ate a unidade aparecem em destaque, porque sao a parte do
  roteiro que o agente nao esperaria.
- Tempos acumulados em minutos, para o agente se situar no turno.
"""

from __future__ import annotations

import re

# Como cada acao do plano deve aparecer no roteiro. None = nao exibir.
LEGENDA = {
    "iniciar-visita": None,
    "iniciar-visita-urgente": None,
    "iniciar-visita-adiavel": None,
    "conferir-protecao-dispensada": None,
    "retornar-a-rota": None,
    "registrar-visita": "Registrar a visita no sistema",
    "registrar-encaminhamento": "Encaminhar o paciente a unidade de referencia",
    "aferir-pressao-arterial": "Aferir pressao arterial",
    "medir-glicemia-capilar": "Medir glicemia capilar",
    "aferir-temperatura-axilar": "Aferir temperatura axilar",
    "verificacao-antropometrica": "Verificacao antropometrica (peso e altura)",
    "orientar-administracao-medicacao": "Orientar a administracao da medicacao",
    "verificar-caderneta-vacinal": "Conferir a caderneta de vacinacao",
    "acionar-supervisao": "Acionar o enfermeiro da equipe (acompanhamento obrigatorio)",
    "higienizar-maos": "Higienizar as maos",
    "vestir-mascara": "Colocar mascara de protecao respiratoria",
    "conferir-protecao-exigida": "Conferir a protecao antes de entrar",
}

# Acoes de reposicao: nao sao tarefas clinicas. Aparecem agrupadas na linha
# do desvio, para o agente saber o que buscar quando passar na unidade.
REPOSICOES = {
    "reabastecer-fitas": "fitas de glicemia",
    "repor-alcool": "solucao alcoolica",
    "repor-mascaras": "mascaras",
    "trocar-coletor": "coletor de perfurocortante",
}

# O planejador e livre para ordenar acoes equivalentes como quiser, e essa
# ordem varia de parada para parada. Para uma lista de conferencia isso e
# ruim: o agente espera sempre a mesma sequencia de trabalho. As tarefas sao
# entao reordenadas por etapa, e nao pela ordem interna do plano.
ORDEM_ETAPA = {
    "Acionar o enfermeiro da equipe (acompanhamento obrigatorio)": 0,
    "Colocar mascara de protecao respiratoria": 1,
    "Conferir a protecao antes de entrar": 2,
    "Higienizar as maos": 3,
    "Aferir pressao arterial": 4,
    "Medir glicemia capilar": 5,
    "Aferir temperatura axilar": 6,
    "Verificacao antropometrica (peso e altura)": 7,
    "Orientar a administracao da medicacao": 8,
    "Conferir a caderneta de vacinacao": 9,
    "Encaminhar o paciente a unidade de referencia": 10,
    "Registrar a visita no sistema": 11,
}

_ARGS = re.compile(r"^([a-z0-9-]+)\((.*)\)$")


def _partes(acao: str) -> tuple[str, list[str]]:
    m = _ARGS.match(acao.strip())
    if not m:
        return acao.strip(), []
    return m.group(1), [a.strip() for a in m.group(2).split(",")]


def montar(plano: list[str], dados: dict, custos_acao: dict[str, int],
           matriz: dict[tuple[str, str], int]) -> list[dict]:
    """Agrupa o plano em paradas. Cada parada vira um dicionario.

    A atribuicao de cada acao a uma parada e feita em duas passagens, e nao
    por acumulacao sequencial. O motivo e que o planejador intercala acoes
    livremente: a supervisao pode ser acionada antes de a visita comecar, e
    um desvio ate a unidade pode ocorrer no meio de um atendimento. Uma
    varredura unica com buffer atribui essas acoes a parada errada.

    Regra usada: toda acao que menciona um paciente pertence a ele. As
    demais (acionar supervisao, higienizar, vestir mascara, repor material)
    pertencem ao paciente da PROXIMA acao que mencione um, porque sao sempre
    preparacao para o atendimento seguinte.
    """
    por_id = {p["id"]: p for p in dados["pacientes"]}
    id_ubs = dados["ubs"]["id"]

    def custo(nome: str, args: list[str]) -> int:
        if nome == "mover" and len(args) >= 3:
            a = args[1].replace("casa-", "")
            b = args[2].replace("casa-", "")
            a = id_ubs if a in (id_ubs, "ubs-fim") else a
            b = id_ubs if b in (id_ubs, "ubs-fim") else b
            return matriz.get((a, b), 0)
        if nome == "desviar-para-ubs" and len(args) >= 2:
            alvo = args[1].replace("casa-", "")
            return 2 * matriz.get((alvo, id_ubs), 0)
        return custos_acao.get(nome, 0)

    # ---- passagem 1: eventos com tempo acumulado e dono, quando evidente --
    eventos: list[dict] = []
    minutos = 0
    for acao in plano:
        nome, args = _partes(acao)
        minutos += custo(nome, args)
        dono = next((a for a in args if a in por_id), None)
        eventos.append({"nome": nome, "args": args, "minutos": minutos,
                        "dono": dono})

    # ---- passagem 2: propaga o dono para tras ----------------------------
    dono_seguinte: str | None = None
    for evento in reversed(eventos):
        if evento["dono"] is not None:
            dono_seguinte = evento["dono"]
        elif evento["nome"] in ("acionar-supervisao", "higienizar-maos",
                                "vestir-mascara", "desviar-para-ubs",
                                "reabastecer-fitas", "repor-alcool",
                                "repor-mascaras", "trocar-coletor"):
            evento["dono"] = dono_seguinte

    # ---- monta as paradas na ordem em que as visitas comecam -------------
    paradas: list[dict] = []
    indice: dict[str, dict] = {}
    for evento in eventos:
        if not evento["nome"].startswith("iniciar-visita"):
            continue
        dono = evento["dono"]
        if dono is None or dono in indice:
            continue
        parada = {"ordem": len(paradas) + 1, "paciente": por_id.get(dono),
                  "tarefas": [], "desvio_ubs": False, "repor": [],
                  "minutos_chegada": evento["minutos"]}
        paradas.append(parada)
        indice[dono] = parada

    for evento in eventos:
        parada = indice.get(evento["dono"] or "")
        if parada is None:
            continue
        if evento["nome"] == "desviar-para-ubs":
            parada["desvio_ubs"] = True
            continue
        if evento["nome"] in REPOSICOES:
            item = REPOSICOES[evento["nome"]]
            if item not in parada["repor"]:
                parada["repor"].append(item)
            continue
        rotulo = LEGENDA.get(evento["nome"])
        if rotulo and rotulo not in parada["tarefas"]:
            parada["tarefas"].append(rotulo)

    for parada in paradas:
        parada["tarefas"].sort(key=lambda t: ORDEM_ETAPA.get(t, 99))
    return paradas


def imprimir(paradas: list[dict], dados: dict, *, custo_total: int,
             orcamento: int | None = None, largura: int = 66) -> str:
    """Devolve o roteiro pronto para impressao ou envio ao agente."""
    linhas: list[str] = []
    add = linhas.append
    ubs = dados["ubs"].get("nome", "Unidade Basica de Saude")

    add("=" * largura)
    add("  ROTEIRO DO TURNO")
    add(f"  Saida e retorno: {ubs}")
    add(f"  {len(paradas)} visitas  |  duracao estimada: {custo_total} min")
    if orcamento is not None and custo_total > orcamento:
        add(f"  ATENCAO: excede em {custo_total - orcamento} min o orcamento de "
            f"{orcamento} min")
    add("=" * largura)

    for parada in paradas:
        paciente = parada["paciente"] or {}
        nome = paciente.get("nome", paciente.get("id", "?"))
        grupo = (paciente.get("grupo") or "").replace("_", " ")
        add("")
        cabecalho = f"  {parada['ordem']}. {nome}"
        if grupo:
            cabecalho += f"  ({grupo})"
        add(cabecalho)
        add(f"     inicio aprox.: {parada['minutos_chegada']} min de turno")

        if parada["desvio_ubs"]:
            itens = ", ".join(parada.get("repor") or ["material"])
            add(f"     >> PASSAR NA UNIDADE ANTES desta visita: repor {itens}")

        if parada["tarefas"]:
            for tarefa in parada["tarefas"]:
                add(f"     [ ] {tarefa}")
        else:
            add("     [ ] Visita de acompanhamento, sem procedimento previsto")

    add("")
    add("-" * largura)
    add("  Marque cada item ao concluir. Em caso de impossibilidade de")
    add("  realizar algum procedimento, registre a ocorrencia e comunique")
    add("  a equipe antes de seguir para a proxima visita.")
    add("-" * largura)
    return "\n".join(linhas)


def salvar(texto: str, caminho: str) -> None:
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto + "\n")
