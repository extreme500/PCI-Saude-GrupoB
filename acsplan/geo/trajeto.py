"""
Geometria do caminho pelas ruas, para desenho.

Para que serve, e sobretudo para que NAO serve
----------------------------------------------
Este modulo existe por um motivo so: fazer a rota aparecer no mapa
percorrendo ruas reais, em vez de cortar quadras por dentro com linhas
retas entre as coordenadas.

Ele **nao** entra no modelo. Os custos que o planejamento e o executor
procedural usam continuam vindo de `distancias.py`, que e onde a decisao
de medicao esta declarada (haversine vezes 1,3 a 4,5 km/h, ou o servico
Table do OSRM quando habilitado). Misturar as duas coisas tornaria a
comparacao entre os dois grupos dependente de uma chamada de rede, que e
exatamente o que o metodo experimental evita.

Em resumo: isto aqui muda o DESENHO, nunca o NUMERO.

Qual servidor
-------------
A instancia publica do projeto OSRM (`router.project-osrm.org`) aceita o
caminho `/foot/` mas responde com o perfil de carro: 34 km/h e respeito a
mao unica, o que para um agente a pe esta errado. Usamos entao a instancia
que o proprio site do OpenStreetMap usa para rotas a pe, cujo perfil devolve
4,4 km/h e caminhos de pedestre.

Sem rede, a funcao devolve None e quem chama desenha em linha reta,
dizendo-o na legenda.
"""

from __future__ import annotations

import hashlib
import json
import os

from . import _rede
from .distancias import modal_de

TIMEOUT_S = 30
DIRETORIO_CACHE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dados", "cache_trajeto")


def _chave(coordenadas: str, cfg: dict) -> str:
    # o servidor entra na chave: ha instancias que servem um perfil
    # diferente do que o caminho da URL promete
    assinatura = cfg["servidor"] + "|" + coordenadas
    digest = hashlib.sha256(assinatura.encode()).hexdigest()[:16]
    return f"{cfg['perfil']}-{digest}.json"


def _ler_cache(coordenadas: str, cfg: dict):
    caminho = os.path.join(DIRETORIO_CACHE, _chave(coordenadas, cfg))
    if os.path.exists(caminho):
        try:
            with open(caminho, encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except (OSError, ValueError):
            return None
    return None


def _gravar_cache(coordenadas: str, dados, cfg: dict) -> None:
    os.makedirs(DIRETORIO_CACHE, exist_ok=True)
    caminho = os.path.join(DIRETORIO_CACHE, _chave(coordenadas, cfg))
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo)


def _inverter(coordenadas: list) -> list[list[float]]:
    """GeoJSON vem em [lon, lat]; o Leaflet quer [lat, lon]."""
    return [[c[1], c[0]] for c in coordenadas]


def tracar(pontos: list[dict], *, modal: str | None = None,
           silencioso: bool = True) -> dict | None:
    """Caminho pelas ruas passando pelos pontos, na ordem dada.

    Devolve `{"linha": [[lat, lon], ...], "pernas": [...], "metros": float,
    "segundos": float}` ou None se o servico nao responder.

    `pernas[i]` e a geometria do trecho entre `pontos[i]` e `pontos[i+1]`,
    util para colorir trechos isoladamente.
    """
    if len(pontos) < 2:
        return None

    cfg = modal_de(modal)
    coordenadas = ";".join(f"{p['lon']:.6f},{p['lat']:.6f}" for p in pontos)
    cache = _ler_cache(coordenadas, cfg)
    if cache is not None:
        return cache

    url = (f"{cfg['servidor']}/route/v1/{cfg['perfil']}/{coordenadas}"
           f"?overview=full&geometries=geojson&steps=true&annotations=false")
    corpo = _rede.obter_json(url, timeout=TIMEOUT_S, silencioso=silencioso)
    if corpo is None:
        if not silencioso:
            print("  [aviso] servico de rotas indisponivel; "
                  "o mapa sai com linhas retas.")
        return None

    if corpo.get("code") != "Ok" or not corpo.get("routes"):
        return None

    rota = corpo["routes"][0]
    pernas = []
    for perna in rota.get("legs", []):
        pontos_perna: list[list[float]] = []
        for passo in perna.get("steps", []):
            geo = (passo.get("geometry") or {}).get("coordinates") or []
            trecho = _inverter(geo)
            # os passos compartilham o ponto de juncao: evita duplicar
            if pontos_perna and trecho and pontos_perna[-1] == trecho[0]:
                trecho = trecho[1:]
            pontos_perna.extend(trecho)
        pernas.append(pontos_perna)

    resultado = {
        "linha": _inverter(rota["geometry"]["coordinates"]),
        "pernas": pernas,
        "metros": rota.get("distance", 0.0),
        "segundos": rota.get("duration", 0.0),
    }
    _gravar_cache(coordenadas, resultado, cfg)
    return resultado


def tracar_ida_e_volta(a: dict, b: dict,
                       modal: str | None = None) -> list[list[float]] | None:
    """Caminho de `a` ate `b`, para desenhar um desvio de reposicao."""
    traco = tracar([a, b], modal=modal)
    return traco["linha"] if traco else None
