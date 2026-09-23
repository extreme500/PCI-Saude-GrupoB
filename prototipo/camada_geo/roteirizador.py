"""
Camada geometrica: matriz de custos + heuristica de roteamento.

Esta camada resolve o que o planejador NAO deve resolver (a ordem fisica das
paradas). Ela e deliberadamente simples - Vizinho Mais Proximo seguido de
2-opt - porque o objeto de estudo do projeto nao e a qualidade do roteador,
e sim o acoplamento entre a rota e a camada de protocolos.

Substituir esta camada por OSRM, OR-Tools ou pela Distance Matrix API nao
exige nenhuma mudanca na camada logica: o contrato entre as duas e apenas a
lista ordenada de paradas e a matriz de custos.
"""

from __future__ import annotations

import math

# Velocidade media de deslocamento a pe do ACS em area urbana, usada para
# converter distancia em minutos. Parametro do modelo, nao norma.
VELOCIDADE_CAMINHADA_KM_H = 4.5

# Fator de correcao de rota: a distancia em linha reta subestima o percurso
# real pelas ruas. 1.3 e a aproximacao usual para malha urbana em grade.
FATOR_MALHA_URBANA = 1.3


def haversine_km(a: dict, b: dict) -> float:
    """Distancia em km sobre a superficie da Terra entre dois pontos."""
    raio = 6371.0
    lat1, lon1 = math.radians(a["lat"]), math.radians(a["lon"])
    lat2, lon2 = math.radians(b["lat"]), math.radians(b["lon"])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * raio * math.asin(math.sqrt(h))


def minutos_entre(a: dict, b: dict) -> int:
    """Custo de deslocamento em minutos inteiros (o PDDL usa custos inteiros)."""
    km = haversine_km(a, b) * FATOR_MALHA_URBANA
    return max(1, round(km / VELOCIDADE_CAMINHADA_KM_H * 60))


def construir_matriz(pontos: list[dict]) -> dict[tuple[str, str], int]:
    """Matriz completa de custos entre todos os pontos (inclui a UBS)."""
    return {
        (a["id"], b["id"]): (0 if a["id"] == b["id"] else minutos_entre(a, b))
        for a in pontos for b in pontos
    }


def vizinho_mais_proximo(ids: list[str], origem: str,
                         matriz: dict[tuple[str, str], int]) -> list[str]:
    """Heuristica gulosa classica: sempre siga para a parada nao visitada
    mais barata a partir da atual."""
    pendentes = [i for i in ids if i != origem]
    rota = [origem]
    atual = origem
    while pendentes:
        proximo = min(pendentes, key=lambda x: matriz[(atual, x)])
        rota.append(proximo)
        pendentes.remove(proximo)
        atual = proximo
    rota.append(origem)  # tour fechado: o ACS retorna a UBS
    return rota


def custo_da_rota(rota: list[str], matriz: dict[tuple[str, str], int]) -> int:
    return sum(matriz[(rota[i], rota[i + 1])] for i in range(len(rota) - 1))


def dois_opt(rota: list[str], matriz: dict[tuple[str, str], int]) -> list[str]:
    """Refino 2-opt: desfaz cruzamentos ate nao haver mais melhoria.

    Mantem fixos o primeiro e o ultimo elemento (a UBS).
    """
    melhor = rota[:]
    melhor_custo = custo_da_rota(melhor, matriz)
    houve_melhoria = True
    while houve_melhoria:
        houve_melhoria = False
        for i in range(1, len(melhor) - 2):
            for j in range(i + 1, len(melhor) - 1):
                candidata = melhor[:i] + melhor[i:j + 1][::-1] + melhor[j + 1:]
                custo = custo_da_rota(candidata, matriz)
                if custo < melhor_custo:
                    melhor, melhor_custo = candidata, custo
                    houve_melhoria = True
    return melhor


def roteirizar(dados: dict) -> dict:
    """Ponto de entrada da camada geometrica.

    Devolve a rota, a matriz e o custo de desvio ate a UBS a partir de cada
    parada (ida e volta), que e a informacao que o planejador precisa para
    decidir onde inserir uma reposicao de insumos.
    """
    ubs = dados["ubs"]
    pontos = [ubs] + dados["pacientes"]
    matriz = construir_matriz(pontos)

    ids = [p["id"] for p in pontos]
    rota = dois_opt(vizinho_mais_proximo(ids, ubs["id"], matriz), matriz)

    # Custo de sair da rota em L, ir a UBS e voltar a L.
    custo_desvio = {
        p["id"]: 2 * matriz[(p["id"], ubs["id"])] for p in dados["pacientes"]
    }

    return {
        "rota": rota,
        "matriz": matriz,
        "custo_desvio": custo_desvio,
        "custo_rota": custo_da_rota(rota, matriz),
    }
