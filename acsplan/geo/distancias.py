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
#  Modal de deslocamento
# ---------------------------------------------------------------------------
#
# O projeto NAO restringe o ACS a andar a pe. A velocidade de caminhada
# estava embutida numa constante, o que fazia parecer decisao de escopo o
# que era so um valor padrao. Agora o modal e parametro declarado, e cada um
# traz as quatro coisas que mudam com ele: a velocidade suposta pelo
# provedor haversine, o fator de correcao da malha urbana, e o servidor e o
# perfil do provedor OSRM.
#
# A troca de modal muda os CUSTOS, entao dois experimentos rodados em modais
# diferentes nao se comparam. Por isso o modal efetivo volta junto da
# matriz, para ir ao relatorio.

MODAIS = {
    "pe": {
        "velocidade_km_h": 4.5,
        "fator_malha": 1.3,
        "servidor": "https://routing.openstreetmap.de/routed-foot",
        "perfil": "foot",
        "rotulo": "a pe",
        "rotulo_custo": "min de caminhada",
    },
    "carro": {
        # media urbana COM paradas, semaforos e estacionamento, bem abaixo
        # da velocidade de fluxo livre que o OSRM devolve (cerca de 34 km/h)
        "velocidade_km_h": 25.0,
        # mao unica e conversoes proibidas alongam mais o percurso de carro
        # do que o de pedestre
        "fator_malha": 1.4,
        "servidor": "https://routing.openstreetmap.de/routed-car",
        "perfil": "driving",
        "rotulo": "de carro",
        "rotulo_custo": "min de deslocamento",
    },
}
MODAL_PADRAO = "pe"


def modal_de(nome):
    """Configuracao do modal, com o padrao para nome vazio ou desconhecido."""
    return MODAIS.get(nome or MODAL_PADRAO, MODAIS[MODAL_PADRAO])


# Mantidos por compatibilidade com quem importava as constantes antigas.
VELOCIDADE_CAMINHADA_KM_H = MODAIS["pe"]["velocidade_km_h"]
FATOR_MALHA_URBANA = MODAIS["pe"]["fator_malha"]

# ---------------------------------------------------------------------------
#  Parâmetros do provedor OSRM
# ---------------------------------------------------------------------------
#
# Atencao ao servidor: a instancia do projeto OSRM (router.project-osrm.org)
# ACEITA o caminho /foot/ mas responde com o perfil de CARRO, a 34 km/h e
# respeitando mao unica. Usar aquele servidor para o modal a pe alimentaria
# o modelo com tempos de automovel. As instancias usadas aqui sao as que o
# proprio site do OpenStreetMap usa, e cada uma serve o perfil que promete.
OSRM_SERVIDOR = os.environ.get("ACSPLAN_OSRM", MODAIS["pe"]["servidor"])
OSRM_PERFIL = MODAIS["pe"]["perfil"]
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


def _minutos_haversine(a: dict, b: dict, modal: dict) -> int:
    km = haversine_km(a, b) * modal["fator_malha"]
    return max(1, round(km / modal["velocidade_km_h"] * 60))


def matriz_haversine(pontos: list[dict],
                     modal: str | None = None) -> dict[tuple[str, str], int]:
    cfg = modal_de(modal)
    return {
        (a["id"], b["id"]): (0 if a["id"] == b["id"]
                             else _minutos_haversine(a, b, cfg))
        for a in pontos for b in pontos
    }


# ---------------------------------------------------------------------------
#  Provedor 2: OSRM
# ---------------------------------------------------------------------------

def _chave_cache(pontos: list[dict], cfg: dict | None = None) -> str:
    # O SERVIDOR entra na chave de proposito: dois servidores respondem ao
    # mesmo caminho /foot/ com perfis diferentes (um deles com velocidade de
    # carro), e sem isso uma resposta antiga continuaria valendo depois de
    # trocar de servidor, que foi exatamente o que aconteceu aqui.
    cfg = cfg or modal_de(None)
    assinatura = cfg["servidor"] + "|" + ";".join(
        f"{p['lon']:.6f},{p['lat']:.6f}" for p in pontos)
    digest = hashlib.sha256(assinatura.encode()).hexdigest()[:16]
    return f"{cfg['perfil']}-{len(pontos)}-{digest}.json"


def _ler_cache(pontos: list[dict], cfg: dict | None = None):
    caminho = os.path.join(DIRETORIO_CACHE, _chave_cache(pontos, cfg))
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return None


def _gravar_cache(pontos: list[dict], dados, cfg: dict | None = None) -> None:
    os.makedirs(DIRETORIO_CACHE, exist_ok=True)
    caminho = os.path.join(DIRETORIO_CACHE, _chave_cache(pontos, cfg))
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo)


def consultar_osrm(pontos: list[dict],
                   modal: str | None = None) -> list[list[float]] | None:
    """Devolve a matriz de durações em segundos, ou None se não for possível.

    Uma única requisição resolve a matriz inteira (serviço Table), então o
    custo de rede é constante no número de pontos, não quadrático.
    """
    cfg = modal_de(modal)
    cache = _ler_cache(pontos, cfg)
    if cache is not None:
        return cache

    coordenadas = ";".join(f"{p['lon']:.6f},{p['lat']:.6f}" for p in pontos)
    url = (f"{cfg['servidor']}/table/v1/{cfg['perfil']}/{coordenadas}"
           f"?annotations=duration")
    corpo = _rede.obter_json(url, timeout=OSRM_TIMEOUT_S)
    if corpo is None or corpo.get("code") != "Ok" or "durations" not in corpo:
        return None

    _gravar_cache(pontos, corpo["durations"], cfg)
    return corpo["durations"]


def matriz_osrm(pontos: list[dict],
                modal: str | None = None) -> dict[tuple[str, str], int] | None:
    duracoes = consultar_osrm(pontos, modal)
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
                     silencioso: bool = True, modal: str | None = None
                     ) -> tuple[dict[tuple[str, str], int], str]:
    """Matriz completa de custos em minutos.

    Devolve também qual provedor foi efetivamente usado, que pode diferir do
    pedido quando o OSRM está indisponível. Quem chama deve registrar esse
    valor no relatório: um experimento rodado com haversine e outro com OSRM
    não são comparáveis entre si.
    """
    cfg = modal_de(modal)
    if provedor == "osrm":
        matriz = matriz_osrm(pontos, modal)
        if matriz is not None:
            return matriz, f"osrm ({cfg['rotulo']})"
        if not silencioso:
            print("  [aviso] OSRM indisponível; usando haversine.")
        return (matriz_haversine(pontos, modal),
                f"haversine ({cfg['rotulo']}, OSRM indisponível)")
    return matriz_haversine(pontos, modal), f"haversine ({cfg['rotulo']})"


def custo_da_rota(rota: list[str], matriz: dict[tuple[str, str], int]) -> int:
    return sum(matriz[(rota[i], rota[i + 1])] for i in range(len(rota) - 1))
