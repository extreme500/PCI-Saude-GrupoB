"""
Traducao: (dados clinicos + rota da camada geometrica) -> arquivo .pddl

Este modulo e a fronteira entre as camadas. Ele congela a saida do
roteirizador no predicado estatico (proxima-parada ?l1 ?l2) e traduz as
necessidades clinicas de cada paciente em fatos do estado inicial.

TRUQUE DE MODELAGEM: PREDICADOS COMPLEMENTARES
-----------------------------------------------
STRIPS nao tem implicacao, entao nao da para escrever a precondicao "SE o
paciente exige glicemia ENTAO a glicemia precisa estar medida". A solucao
padrao e inverter a polaridade: em vez de marcar quem PRECISA, marca-se no
estado inicial quem JA ESTA QUITADO. Para um paciente que nao exige
glicemia, (glicemia-ok p) ja nasce verdadeiro; para quem exige, so a acao
medir-glicemia-capilar produz esse fato.

DESDOBRAMENTO DA UBS
--------------------
A rota e um tour fechado. Com a UBS representada por um objeto unico, as
arestas inicial e final fechariam um ciclo e o planejador poderia percorrer
a rota indefinidamente. Desdobra-se em `ubs` (partida) e `ubs-fim` (chegada
e reposicao), fisicamente a mesma unidade, tornando o grafo aciclico.

PRECEDENCIA POR URGENCIA
------------------------
A restricao "urgencia alta antes de urgencia baixa" e expressa por um
contador regressivo: (altos-pendentes n) comeca no numero de pacientes de
urgencia alta e so quando chega a zero os de urgencia baixa podem ser
iniciados. Com a precedencia desativada, nenhum paciente recebe os fatos de
urgencia e o contador nasce em zero, de modo que a restricao desaparece.
"""

from __future__ import annotations

from ..dados import modelos

# Procedimentos modelados: campo no JSON -> predicado de quitacao no PDDL.
PROCEDIMENTOS = [
    ("requer_pa", "pa-ok"),
    ("requer_glicemia", "glicemia-ok"),
    ("requer_temperatura", "temperatura-ok"),
    ("requer_antropometria", "antropometria-ok"),
    ("requer_orientacao_medicacao", "orientacao-ok"),
    ("requer_vacinal", "vacinal-ok"),
]

NOME_DOMINIO = {
    "legal": "visita-domiciliar-acs",
    "estendido": "visita-domiciliar-acs-estendido",
}


def local_do_paciente(id_paciente: str) -> str:
    return f"casa-{id_paciente}"


def _local(identificador: str, id_ubs: str) -> str:
    return identificador if identificador == id_ubs else local_do_paciente(identificador)


def gerar_problema(dados: dict, roteamento: dict, caminho_saida: str,
                   *, dominio: str = "legal") -> str:
    """Escreve o arquivo de problema PDDL e devolve seu conteudo."""
    ubs = dados["ubs"]
    pacientes = dados["pacientes"]
    agente = dados["agente"]
    recursos = dados["recursos"]
    intervalo = dados.get("_meta", {}).get(
        "intervalo_maximo_padrao_dias", modelos.INTERVALO_MAXIMO_PADRAO_DIAS)

    estendido = dominio == "estendido"
    capacidade_fitas = recursos["fitas_glicemia_por_carga"]
    janelas = recursos["janelas_supervisao_no_turno"]
    capacidade_alcool = recursos.get("doses_alcool_por_carga", 8)
    capacidade_mascaras = recursos.get("mascaras_por_carga", 3)
    capacidade_coletor = recursos.get("capacidade_coletor", 3)

    id_agente = agente["id"]
    id_ubs = ubs["id"]
    id_ubs_fim = "ubs-fim"
    rota = roteamento["rota"]
    matriz = roteamento["matriz"]
    usa_precedencia = bool(roteamento.get("precedencias"))

    niveis_por_urgencia = {p["id"]: modelos.nivel_urgencia(p, intervalo)
                           for p in pacientes}
    altos = [i for i, n in niveis_por_urgencia.items() if n == 3] if usa_precedencia else []
    baixos = [i for i, n in niveis_por_urgencia.items() if n == 1] if usa_precedencia else []
    if not altos or not baixos:          # sem os dois extremos nao ha restricao
        altos, baixos = [], []

    nivel_maximo = max(capacidade_fitas, janelas, len(altos),
                       capacidade_alcool if estendido else 0,
                       capacidade_mascaras if estendido else 0,
                       capacidade_coletor if estendido else 0)

    locais = [id_ubs, id_ubs_fim] + [local_do_paciente(p["id"]) for p in pacientes]
    niveis = [f"n{i}" for i in range(nivel_maximo + 1)]

    linhas: list[str] = []
    add = linhas.append

    add(";; ARQUIVO GERADO AUTOMATICAMENTE por acsplan/logica/gerador_problema.py")
    add(";; A ordem das paradas abaixo foi decidida pela camada geometrica.")
    add(f";; Dominio alvo: {dominio}")
    add(";; Nao editar a mao.")
    add("")
    add("(define (problem microarea-turno)")
    add(f"  (:domain {NOME_DOMINIO[dominio]})")
    add("")
    add("  (:objects")
    add(f"    {id_agente} - agente")
    add(f"    {' '.join(p['id'] for p in pacientes)} - paciente")
    add(f"    {' '.join(locais)} - local")
    add(f"    {' '.join(niveis)} - nivel")
    add("  )")
    add("")
    add("  (:init")

    add("    ;; posicao inicial e identificacao da unidade")
    add(f"    (em {id_agente} {id_ubs})")
    add(f"    (e-ubs {id_ubs})")
    add(f"    (e-ubs {id_ubs_fim})   ; mesma UBS, papel de chegada/reposicao")
    add("")
    add(f"    ;; ROTA FIXADA PELA CAMADA GEOMETRICA ({roteamento.get('metodo', '?')})")
    add(f"    ;; {' -> '.join(rota)}")
    for indice, (origem, destino) in enumerate(zip(rota, rota[1:])):
        final = (indice == len(rota) - 2)
        alvo = id_ubs_fim if final else _local(destino, id_ubs)
        add(f"    (proxima-parada {_local(origem, id_ubs)} {alvo})")
    add("")
    add("    ;; vinculo residencia <-> paciente e desvios possiveis ate a UBS")
    for p in pacientes:
        local = local_do_paciente(p["id"])
        add(f"    (residencia-de {p['id']} {local})")
        add(f"    (desvio-ubs {local} {id_ubs_fim})")
    add("")

    add("    ;; condicoes do caput do art. 3o par. 4o da Lei 11.350/2006")
    if agente.get("curso_tecnico_concluido"):
        add(f"    (curso-tecnico-concluido {id_agente})")
    else:
        add(f"    ;; (curso-tecnico-concluido {id_agente})  <- AUSENTE de proposito")
    if agente.get("equipamento_disponivel"):
        add(f"    (equipamento-disponivel {id_agente})")
    else:
        add(f"    ;; (equipamento-disponivel {id_agente})  <- AUSENTE de proposito")
    add("")

    add("    ;; contadores discretos (substituem fluentes numericos)")
    for i in range(nivel_maximo):
        add(f"    (prox n{i} n{i + 1})")
    add(f"    (nivel-zero n0)")
    add(f"    (fitas n{capacidade_fitas})")
    add(f"    (nivel-maximo n{capacidade_fitas})")
    add(f"    (janelas n{janelas})")
    add("")

    add("    ;; precedencia por urgencia")
    if altos:
        for i in altos:
            add(f"    (urgencia-alta {i})")
        for i in baixos:
            add(f"    (urgencia-baixa {i})")
        add(f"    (altos-pendentes n{len(altos)})")
        add(f"    ;; {len(altos)} urgencia(s) alta(s) antes de {len(baixos)} baixa(s)")
    else:
        add("    (altos-pendentes n0)   ; sem restricao de precedencia neste turno")
    add("")

    if estendido:
        add("    ;; [SINTETICO] recursos dos protocolos operacionais hipoteticos")
        add(f"    (alcool n{capacidade_alcool})")
        add(f"    (mascaras n{capacidade_mascaras})")
        add(f"    (coletor n{capacidade_coletor})")
        add(f"    (nivel-maximo-coletor n{capacidade_coletor})")
        add(f"    (nivel-maximo-alcool n{capacidade_alcool})")
        add(f"    (nivel-maximo-mascaras n{capacidade_mascaras})")
        for p in pacientes:
            if p.get("exige_protecao_respiratoria"):
                add(f"    (exige-protecao-respiratoria {p['id']})")
        add("")

    add("    ;; necessidades clinicas: marca-se o que JA esta quitado.")
    add("    ;; a ausencia de (X-ok p) significa que o procedimento e exigido.")
    for p in pacientes:
        exigidos = []
        for campo, predicado in PROCEDIMENTOS:
            if p.get(campo):
                exigidos.append(predicado)
            else:
                add(f"    ({predicado} {p['id']})")
        rotulo = modelos.rotulo_urgencia(niveis_por_urgencia[p["id"]])
        add(f"    ;; {p['id']}: exige {', '.join(exigidos) or 'nada'} "
            f"| urgencia {rotulo} | {p.get('grupo', '?')}")
    add("")

    add("    ;; custos em minutos, vindos da matriz da camada geometrica")
    add("    (= (total-cost) 0)")
    ids = [id_ubs] + [p["id"] for p in pacientes]
    for a in ids:
        for b in ids:
            if a == b:
                continue
            add(f"    (= (custo-deslocamento {_local(a, id_ubs)} "
                f"{_local(b, id_ubs)}) {matriz[(a, b)]})")
            if b == id_ubs:
                add(f"    (= (custo-deslocamento {_local(a, id_ubs)} "
                    f"{id_ubs_fim}) {matriz[(a, b)]})")
    for p in pacientes:
        add(f"    (= (custo-desvio {local_do_paciente(p['id'])}) "
            f"{roteamento['custo_desvio'][p['id']]})")

    add("  )")
    add("")
    add("  ;; Todo paciente do turno precisa ter o protocolo integralmente")
    add("  ;; cumprido, e o agente precisa terminar de volta na UBS.")
    add("  (:goal (and")
    for p in pacientes:
        add(f"    (protocolo-cumprido {p['id']})")
    add(f"    (em {id_agente} {id_ubs_fim})")
    add("  ))")
    add("")
    add("  (:metric minimize (total-cost))")
    add(")")

    conteudo = "\n".join(linhas) + "\n"
    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
    return conteudo
