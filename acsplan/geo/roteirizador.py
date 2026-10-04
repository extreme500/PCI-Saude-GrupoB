"""
Camada geométrica: decide a ordem das paradas.

Esta camada resolve o que a camada lógica não deve resolver. Ela entrega
três coisas, e só três, para o planejador:

    - a sequência de paradas, congelada;
    - a matriz de custos entre todos os pontos;
    - o custo de sair da rota e voltar, a partir de cada parada.

Dois métodos estão disponíveis, com a mesma assinatura: a heurística
construtiva clássica (vizinho mais próximo com refinamento 2-opt) e o
algoritmo genético. A escolha é do chamador.

Precedência por urgência
------------------------
Quando habilitada, pacientes de urgência alta passam a ter de ser atendidos
antes dos de urgência baixa. A restrição é respeitada aqui, na ordenação, e
verificada de novo na camada lógica: se uma rota chegar ao planejador
violando a precedência, ele prova que o turno é inexequível. Essa
redundância é proposital, e é o que permite tratar o roteirizador como
componente substituível sem abrir mão da garantia.
"""

from __future__ import annotations

import random

from ..dados import modelos
from . import genetico
from .distancias import construir_matriz, custo_da_rota

# Metodo de roteamento do projeto. A escolha esta num lugar so, de proposito,
# porque ela e consequencia de experimento e nao de gosto.
#
# O E8 mostrou que a vantagem do algoritmo genetico sobre vizinho mais
# proximo + 2-opt vem INTEIRA de lidar com precedencia: sem precedencia o
# ganho e de +1,4%, 0,0% e -0,3%. Como a precedencia por urgencia esta ativa
# por padrao neste projeto, o AG e o metodo certo: na configuracao de fato
# usada ele entrega rotas de 3% a 13% mais baratas, por menos de um segundo,
# o que e irrelevante para um turno planejado uma vez por dia.
#
# Ha um segundo motivo, operacional: a realimentacao do passo 3 precisa de
# rotas ALTERNATIVAS, e o AG as produz naturalmente, mudando a semente.
METODO_PADRAO = "ag"


def precedencias(pacientes: list[dict], ativar: bool = True,
                 intervalo_padrao: int = modelos.INTERVALO_MAXIMO_PADRAO_DIAS
                 ) -> dict[str, set[str]]:
    """Mapa {paciente: conjunto de pacientes que devem vir antes dele}.

    A regra adotada é deliberadamente conservadora: só se exige precedência
    entre os extremos, isto é, urgência alta antes de urgência baixa.
    Encadear todos os níveis produziria uma ordem quase total e esvaziaria
    a otimização geométrica.
    """
    if not ativar:
        return {}
    niveis = {p["id"]: modelos.nivel_urgencia(p, intervalo_padrao) for p in pacientes}
    altos = [i for i, n in niveis.items() if n == 3]
    baixos = [i for i, n in niveis.items() if n == 1]
    if not altos or not baixos:
        return {}
    return {baixo: set(altos) for baixo in baixos}


def vizinho_mais_proximo(ids: list[str], origem: str,
                         matriz: dict[tuple[str, str], int],
                         precede: dict[str, set[str]] | None = None) -> list[str]:
    """Heurística gulosa: sempre siga para a parada elegível mais barata.

    Com precedências ativas, "elegível" exclui quem ainda tem predecessor
    pendente, o que mantém a construção viável desde o início.
    """
    precede = precede or {}
    pendentes = [i for i in ids if i != origem]
    visitados: set[str] = set()
    sequencia: list[str] = []
    atual = origem
    while pendentes:
        elegiveis = [p for p in pendentes
                     if all(a in visitados for a in precede.get(p, ()))]
        if not elegiveis:           # precedências em ciclo
            elegiveis = pendentes
        proximo = min(elegiveis, key=lambda x: matriz[(atual, x)])
        sequencia.append(proximo)
        visitados.add(proximo)
        pendentes.remove(proximo)
        atual = proximo
    return sequencia


def vizinho_mais_proximo_aleatorizado(
        ids: list[str], origem: str, matriz: dict[tuple[str, str], int],
        precede: dict[str, set[str]] | None = None,
        *, semente: int = 1, candidatos: int = 3) -> list[str]:
    """Variante GRASP da construção gulosa, para gerar rotas alternativas.

    A cada passo, em vez de tomar sempre a parada elegível mais barata,
    sorteia entre as `candidatos` mais baratas. Serve à realimentação do
    passo 3 para o passo 2: quando o planejamento prova que a rota corrente
    é inexequível, é preciso oferecer outra rota, e não a mesma.
    """
    precede = precede or {}
    sorteio = random.Random(semente)
    pendentes = [i for i in ids if i != origem]
    visitados: set[str] = set()
    sequencia: list[str] = []
    atual = origem
    while pendentes:
        elegiveis = [p for p in pendentes
                     if all(a in visitados for a in precede.get(p, ()))]
        if not elegiveis:
            elegiveis = pendentes
        elegiveis.sort(key=lambda x: matriz[(atual, x)])
        proximo = sorteio.choice(elegiveis[:max(1, candidatos)])
        sequencia.append(proximo)
        visitados.add(proximo)
        pendentes.remove(proximo)
        atual = proximo
    return sequencia


def dois_opt(sequencia: list[str], origem: str,
             matriz: dict[tuple[str, str], int],
             precede: dict[str, set[str]] | None = None) -> list[str]:
    """Refino 2-opt, recusando inversões que quebrem precedência."""
    precede = precede or {}

    def viavel(seq: list[str]) -> bool:
        if not precede:
            return True
        vistos: set[str] = set()
        for item in seq:
            if any(a not in vistos for a in precede.get(item, ())):
                return False
            vistos.add(item)
        return True

    def custo(seq: list[str]) -> int:
        return custo_da_rota([origem] + seq + [origem], matriz)

    melhor = sequencia[:]
    melhor_custo = custo(melhor)
    houve_melhoria = True
    while houve_melhoria:
        houve_melhoria = False
        for i in range(len(melhor) - 1):
            for j in range(i + 1, len(melhor)):
                candidata = melhor[:i] + melhor[i:j + 1][::-1] + melhor[j + 1:]
                if not viavel(candidata):
                    continue
                c = custo(candidata)
                if c < melhor_custo:
                    melhor, melhor_custo = candidata, c
                    houve_melhoria = True
    return melhor


def roteirizar(dados: dict, *, metodo: str = METODO_PADRAO,
               provedor_distancia: str = "haversine",
               usar_precedencia: bool = True,
               semente: int = 0,
               variante: int = 0,
               matriz_pronta: dict | None = None,
               silencioso: bool = True) -> dict:
    """Ponto de entrada da camada geométrica.

    metodo = "nn2opt" -> vizinho mais próximo + 2-opt
    metodo = "ag"     -> algoritmo genético, semeado com a rota do nn2opt

    `variante` serve à realimentação do passo 3. Com `variante = 0` sai a
    rota canônica, determinística. Com `variante > 0` sai uma rota
    alternativa: outra execução do algoritmo genético, ou uma construção
    gulosa aleatorizada seguida de 2-opt. A matriz de distâncias pode ser
    passada pronta, para não refazer chamadas de rede a cada tentativa.
    """
    ubs = dados["ubs"]
    pacientes = dados["pacientes"]
    pontos = [ubs] + pacientes
    intervalo = dados.get("_meta", {}).get(
        "intervalo_maximo_padrao_dias", modelos.INTERVALO_MAXIMO_PADRAO_DIAS)

    if matriz_pronta is not None:
        matriz, provedor_usado = matriz_pronta["matriz"], matriz_pronta["provedor"]
    else:
        matriz, provedor_usado = construir_matriz(pontos, provedor_distancia,
                                                  silencioso)
    precede = precedencias(pacientes, usar_precedencia, intervalo)

    ids = [p["id"] for p in pacientes]
    if variante == 0:
        base = vizinho_mais_proximo([ubs["id"]] + ids, ubs["id"], matriz, precede)
    else:
        base = vizinho_mais_proximo_aleatorizado(
            [ubs["id"]] + ids, ubs["id"], matriz, precede,
            semente=semente * 1000 + variante)

    metricas: dict = {}
    if metodo == "ag":
        rota, metricas = genetico.otimizar(
            ids, ubs["id"], matriz, precede,
            semente=semente + variante, sequencia_inicial=base)
    else:
        rota = [ubs["id"]] + dois_opt(base, ubs["id"], matriz, precede) + [ubs["id"]]

    return {
        "rota": rota,
        "matriz": matriz,
        "custo_desvio": {p["id"]: 2 * matriz[(p["id"], ubs["id"])] for p in pacientes},
        "custo_rota": custo_da_rota(rota, matriz),
        "precedencias": precede,
        "metodo": metodo,
        "variante": variante,
        "provedor_distancia": provedor_usado,
        "metricas_ag": metricas,
    }
