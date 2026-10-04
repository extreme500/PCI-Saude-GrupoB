"""
Matriz de custos de deslocamento.

Dois provedores, com a mesma interface:

- `haversine`: distância em linha reta corrigida por um fator de malha
  urbana e convertida em minutos por uma velocidade de caminhada fixa.
  Não depende de rede e é o padrão.

- `osrm`: consulta o serviço Table da Open Source Routing Machine, que
  devolve o tempo de percurso real pelo traçado das ruas, no perfil a pé.
  Depende de rede; em caso de falha, cai automaticamente para haversine.

A troca de provedor não afeta nenhuma outra camada: o contrato é sempre o
mesmo dicionário {(origem, destino): minutos}. É esse desacoplamento que
permite alimentar tanto o roteirizador clássico quanto o algoritmo genético
com custos reais sem tocar no domínio PDDL.

As respostas do OSRM são gravadas em cache no disco, indexadas pelo conjunto
de coordenadas consultado, para que experimentos repetidos não refaçam a
mesma chamada de rede.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.error
import urllib.request

from . import _rede

# ---------------------------------------------------------------------------
#  Parâmetros do provedor haversine
# ---------------------------------------------------------------------------

# Velocidade média de deslocamento a pé do ACS em área urbana.
VELOCIDADE_CAMINHADA_KM_H = 4.5

# A distância em linha reta subestima o percurso real pelas ruas. 1,3 é a
# aproximação usual para malha urbana em grade.
FATOR_MALHA_URBANA = 1.3

# ---------------------------------------------------------------------------
#  Parâmetros do provedor OSRM
# ---------------------------------------------------------------------------

# A instancia do projeto OSRM (router.project-osrm.org) ACEITA o caminho
# /foot/ mas responde com o perfil de carro: 34 km/h e respeito a mao unica.
# Usar aquele servidor aqui alimentaria o modelo com tempos de automovel para
# um agente que vai a pe. Esta e a instancia que o proprio site do
# OpenStreetMap usa para rotas de pedestre, e devolve 4,4 km/h.
OSRM_SERVIDOR = os.environ.get("ACSPLAN_OSRM",
                               "https://routing.openstreetmap.de/routed-foot")
OSRM_PERFIL = "foot"
OSRM_TIMEOUT_S = 25

DIRETORIO_CACHE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "dados", "cache_osrm")


# ---------------------------------------------------------------------------
#  Provedor 1: haversine
# ---------------------------------------------------------------------------

def haversine_km(a: dict, b: dict) -> float:
    """Distância sobre a superfície da Terra entre dois pontos, em km."""
    raio = 6371.0
    lat1, lon1 = math.radians(a["lat"]), math.radians(a["lon"])
    lat2, lon2 = math.radians(b["lat"]), math.radians(b["lon"])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * raio * math.asin(math.sqrt(h))


def _minutos_haversine(a: dict, b: dict) -> int:
    km = haversine_km(a, b) * FATOR_MALHA_URBANA
    return max(1, round(km / VELOCIDADE_CAMINHADA_KM_H * 60))


def matriz_haversine(pontos: list[dict]) -> dict[tuple[str, str], int]:
    return {
        (a["id"], b["id"]): (0 if a["id"] == b["id"] else _minutos_haversine(a, b))
        for a in pontos for b in pontos
    }


# ---------------------------------------------------------------------------
#  Provedor 2: OSRM
# ---------------------------------------------------------------------------

def _chave_cache(pontos: list[dict]) -> str:
    # O SERVIDOR entra na chave de proposito: dois servidores respondem ao
    # mesmo caminho /foot/ com perfis diferentes (um deles com velocidade de
    # carro), e sem isso uma resposta antiga continuaria valendo depois de
    # trocar de servidor, que foi exatamente o que aconteceu aqui.
    assinatura = OSRM_SERVIDOR + "|" + ";".join(
        f"{p['lon']:.6f},{p['lat']:.6f}" for p in pontos)
    digest = hashlib.sha256(assinatura.encode()).hexdigest()[:16]
    return f"{OSRM_PERFIL}-{len(pontos)}-{digest}.json"


def _ler_cache(pontos: list[dict]):
    caminho = os.path.join(DIRETORIO_CACHE, _chave_cache(pontos))
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return None


def _gravar_cache(pontos: list[dict], dados) -> None:
    os.makedirs(DIRETORIO_CACHE, exist_ok=True)
    caminho = os.path.join(DIRETORIO_CACHE, _chave_cache(pontos))
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo)


def consultar_osrm(pontos: list[dict]) -> list[list[float]] | None:
    """Devolve a matriz de durações em segundos, ou None se não for possível.

    Uma única requisição resolve a matriz inteira (serviço Table), então o
    custo de rede é constante no número de pontos, não quadrático.
    """
    cache = _ler_cache(pontos)
    if cache is not None:
        return cache

    coordenadas = ";".join(f"{p['lon']:.6f},{p['lat']:.6f}" for p in pontos)
    url = (f"{OSRM_SERVIDOR}/table/v1/{OSRM_PERFIL}/{coordenadas}"
           f"?annotations=duration")
    corpo = _rede.obter_json(url, timeout=OSRM_TIMEOUT_S)
    if corpo is None or corpo.get("code") != "Ok" or "durations" not in corpo:
        return None

    _gravar_cache(pontos, corpo["durations"])
    return corpo["durations"]


def matriz_osrm(pontos: list[dict]) -> dict[tuple[str, str], int] | None:
    duracoes = consultar_osrm(pontos)
    if duracoes is None:
        return None
    matriz: dict[tuple[str, str], int] = {}
    for i, a in enumerate(pontos):
        for j, b in enumerate(pontos):
            if i == j:
                matriz[(a["id"], b["id"])] = 0
                continue
            segundos = duracoes[i][j]
            if segundos is None:
                return None  # ponto inalcançável: descarta a matriz inteira
            matriz[(a["id"], b["id"])] = max(1, round(segundos / 60))
    return matriz


# ---------------------------------------------------------------------------
#  Interface pública
# ---------------------------------------------------------------------------

def construir_matriz(pontos: list[dict], provedor: str = "haversine",
                     silencioso: bool = True) -> tuple[dict[tuple[str, str], int], str]:
    """Matriz completa de custos em minutos.

    Devolve também qual provedor foi efetivamente usado, que pode diferir do
    pedido quando o OSRM está indisponível. Quem chama deve registrar esse
    valor no relatório: um experimento rodado com haversine e outro com OSRM
    não são comparáveis entre si.
    """
    if provedor == "osrm":
        matriz = matriz_osrm(pontos)
        if matriz is not None:
            return matriz, "osrm"
        if not silencioso:
            print("  [aviso] OSRM indisponível; usando haversine.")
        return matriz_haversine(pontos), "haversine (OSRM indisponível)"
    return matriz_haversine(pontos), "haversine"


def custo_da_rota(rota: list[str], matriz: dict[tuple[str, str], int]) -> int:
    return sum(matriz[(rota[i], rota[i + 1])] for i in range(len(rota) - 1))
