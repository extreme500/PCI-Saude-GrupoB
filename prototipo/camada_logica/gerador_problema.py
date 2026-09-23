"""
Traducao: (dados clinicos + rota da camada geometrica) -> arquivo .pddl

Este modulo e a fronteira entre as duas camadas da arquitetura. Ele congela a
saida do roteirizador no predicado estatico (proxima-parada ?l1 ?l2) e traduz
as necessidades clinicas de cada paciente em fatos do estado inicial.

TRUQUE DE MODELAGEM IMPORTANTE (predicados complementares)
----------------------------------------------------------
STRIPS nao tem implicacao, entao nao da para escrever a precondicao
"SE o paciente exige glicemia ENTAO a glicemia precisa estar medida".
A solucao padrao e inverter a polaridade: em vez de marcar quem PRECISA,
marca-se no estado inicial quem JA ESTA QUITADO. Para um paciente que nao
exige glicemia, (glicemia-ok p) ja nasce verdadeiro; para quem exige, so a
acao medir-glicemia-capilar produz esse fato. A precondicao de
registrar-visita vira entao uma conjuncao simples.
"""

from __future__ import annotations


def local_do_paciente(id_paciente: str) -> str:
    return f"casa-{id_paciente}"


def gerar_problema(dados: dict, roteamento: dict, caminho_saida: str) -> str:
    """Escreve o arquivo de problema PDDL e devolve seu conteudo."""
    ubs = dados["ubs"]
    pacientes = dados["pacientes"]
    agente = dados["agente"]
    recursos = dados["recursos"]

    capacidade_fitas = recursos["fitas_glicemia_por_carga"]
    janelas = recursos["janelas_supervisao_no_turno"]
    nivel_maximo = max(capacidade_fitas, janelas)

    id_agente = agente["id"]
    id_ubs = ubs["id"]
    # A UBS aparece em DOIS papeis: ponto de partida (`ubs`) e ponto de
    # chegada / reposicao (`ubs-fim`). Fisicamente e a mesma unidade; o
    # desdobramento serve para que o grafo da rota fique ACICLICO.
    # Sem ele, a aresta final (p_n -> ubs) fecharia um ciclo com a aresta
    # inicial (ubs -> p_1) e o planejador poderia dar voltas na rota
    # indefinidamente, explodindo o espaco de estados sem necessidade.
    # Desdobrar objetos para remover ciclos e uma tecnica padrao de
    # compilacao em planejamento.
    id_ubs_fim = "ubs-fim"
    rota = roteamento["rota"]
    matriz = roteamento["matriz"]

    # ---- objetos -----------------------------------------------------------
    locais = [id_ubs, id_ubs_fim] + [local_do_paciente(p["id"])
                                     for p in pacientes]
    niveis = [f"n{i}" for i in range(nivel_maximo + 1)]

    linhas: list[str] = []
    add = linhas.append

    add(";; ARQUIVO GERADO AUTOMATICAMENTE por gerador_problema.py")
    add(";; A ordem das paradas abaixo foi decidida pela camada geometrica.")
    add(";; Nao editar a mao: rode `python prototipo/orquestrador.py`.")
    add("")
    add("(define (problem microarea-turno)")
    add("  (:domain visita-domiciliar-acs)")
    add("")
    add("  (:objects")
    add(f"    {id_agente} - agente")
    add(f"    {' '.join(p['id'] for p in pacientes)} - paciente")
    add(f"    {' '.join(locais)} - local")
    add(f"    {' '.join(niveis)} - nivel")
    add("  )")
    add("")
    add("  (:init")

    # ---- posicao inicial e topologia --------------------------------------
    add("    ;; posicao inicial e identificacao da unidade")
    add(f"    (em {id_agente} {id_ubs})")
    add(f"    (e-ubs {id_ubs})")
    add(f"    (e-ubs {id_ubs_fim})   ; mesma UBS, papel de chegada/reposicao")
    add("")
    add("    ;; ROTA FIXADA PELA CAMADA GEOMETRICA (vizinho mais proximo + 2-opt)")
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

    # ---- habilitacao legal do agente --------------------------------------
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

    # ---- contadores discretos ---------------------------------------------
    add("    ;; contador discreto de niveis (substitui fluentes numericos)")
    for i in range(nivel_maximo):
        add(f"    (prox n{i} n{i + 1})")
    add(f"    (fitas n{capacidade_fitas})")
    add(f"    (nivel-maximo n{capacidade_fitas})")
    add(f"    (janelas n{janelas})")
    add("")

    # ---- necessidades clinicas (polaridade invertida) ---------------------
    add("    ;; necessidades clinicas: marca-se o que JA esta quitado.")
    add("    ;; a ausencia de (X-ok p) significa que o procedimento e exigido.")
    for p in pacientes:
        exigencias = []
        if not p.get("requer_pa"):
            add(f"    (pa-ok {p['id']})")
        else:
            exigencias.append("PA")
        if not p.get("requer_glicemia"):
            add(f"    (glicemia-ok {p['id']})")
        else:
            exigencias.append("glicemia")
        if not p.get("requer_vacinal"):
            add(f"    (vacinal-ok {p['id']})")
        else:
            exigencias.append("vacinal")
        add(f"    ;; {p['id']}: exige {', '.join(exigencias) or 'nada'} "
            f"({p.get('grupo', '?')})")
    add("")

    # ---- custos numericos vindos da matriz real ---------------------------
    add("    ;; custos em minutos, vindos da matriz de distancias (haversine)")
    add(f"    (= (total-cost) 0)")
    for a in [id_ubs] + [p["id"] for p in pacientes]:
        for b in [id_ubs] + [p["id"] for p in pacientes]:
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

    # ---- objetivo ----------------------------------------------------------
    add("  ;; Todo paciente da lista precisa ter o protocolo integralmente")
    add("  ;; cumprido, e o agente precisa terminar o turno de volta na UBS.")
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


def _local(identificador: str, id_ubs: str) -> str:
    """Converte um id da rota (paciente ou UBS) no nome do local PDDL."""
    return identificador if identificador == id_ubs \
        else local_do_paciente(identificador)
