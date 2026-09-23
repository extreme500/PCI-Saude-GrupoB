"""
Orquestrador do prototipo: executa o pipeline completo das duas camadas.

    dados clinicos + coordenadas
              |
              v
    [1] CAMADA GEOMETRICA  -- vizinho mais proximo + 2-opt
              |  (rota fixada + matriz de custos + custos de desvio)
              v
    [2] TRADUTOR           -- gera o problema PDDL
              |
              v
    [3] CAMADA LOGICA      -- planejador STRIPS (A* / GBFS)
              |
              v
    [4] RELATORIO          -- roteiro do turno + comparacao com a linha de base

Uso:
    python prototipo/orquestrador.py
    python prototipo/orquestrador.py --dados prototipo/dados/microarea_exemplo.json
    python prototipo/orquestrador.py --estrategia gbfs
    python prototipo/orquestrador.py --sem-curso-tecnico   # experimento E3
"""

from __future__ import annotations

import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(RAIZ, "camada_geo"), os.path.join(RAIZ, "camada_logica")]

import executor_guloso                      # noqa: E402
from gerador_problema import gerar_problema  # noqa: E402
from planejador import (TarefaPlanejamento, carregar_dominio,  # noqa: E402
                        carregar_problema, resolver)
from roteirizador import roteirizar          # noqa: E402

CAMINHO_DOMINIO = os.path.join(RAIZ, "camada_logica", "dominio.pddl")
CAMINHO_PROBLEMA = os.path.join(RAIZ, "camada_logica", "problema_gerado.pddl")
CAMINHO_DADOS_PADRAO = os.path.join(RAIZ, "dados", "microarea_exemplo.json")


def titulo(texto: str) -> None:
    print()
    print("=" * 74)
    print(f"  {texto}")
    print("=" * 74)


def executar_pipeline(caminho_dados: str, estrategia: str,
                      sem_curso_tecnico: bool = False,
                      silencioso: bool = False) -> dict:
    with open(caminho_dados, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if sem_curso_tecnico:
        dados["agente"]["curso_tecnico_concluido"] = False

    # ---- [1] camada geometrica --------------------------------------------
    roteamento = roteirizar(dados)

    if not silencioso:
        titulo("[1] CAMADA GEOMETRICA - roteamento fisico")
        print(f"  Heuristica    : vizinho mais proximo + refino 2-opt")
        print(f"  Paradas       : {len(dados['pacientes'])} residencias + UBS")
        print(f"  Rota escolhida: {' -> '.join(roteamento['rota'])}")
        print(f"  Custo do trajeto: {roteamento['custo_rota']} min de caminhada")
        print()
        print("  Custo de um desvio ida-e-volta ate a UBS a partir de cada parada:")
        for parada, valor in sorted(roteamento["custo_desvio"].items(),
                                    key=lambda kv: kv[1]):
            print(f"    {parada:>4} : {valor:>3} min")
        print("  (o planejador usa esta tabela para escolher ONDE reabastecer)")

    # ---- [2] traducao ------------------------------------------------------
    gerar_problema(dados, roteamento, CAMINHO_PROBLEMA)
    if not silencioso:
        titulo("[2] TRADUTOR - problema PDDL gerado")
        print(f"  Arquivo: {os.path.relpath(CAMINHO_PROBLEMA, os.getcwd())}")
        print("  A rota da etapa [1] virou o predicado estatico (proxima-parada).")

    # ---- [3] camada logica -------------------------------------------------
    tarefa = TarefaPlanejamento(carregar_dominio(CAMINHO_DOMINIO),
                                carregar_problema(CAMINHO_PROBLEMA))
    resultado = resolver(tarefa, estrategia)

    if not silencioso:
        titulo("[3] CAMADA LOGICA - planejamento automatizado")
        rotulos = {
            "astar-hmax": "A* com h_max (otimo, com garantia)",
            "astar-hadd": "A* com h_add (informado, sem garantia formal)",
            "gbfs": "GBFS com h_add (satisfaciente, rapido)",
        }
        print(f"  Estrategia          : {rotulos[estrategia]}")
        print(f"  Acoes instanciadas  : {len(tarefa.acoes)}")
        print(f"  Nos expandidos      : {resultado.expandidos}")
        print(f"  Nos gerados         : {resultado.gerados}")
        print(f"  Tempo de busca      : {resultado.segundos:.3f}s")
        if resultado.sucesso:
            print(f"  Plano encontrado    : {resultado.tamanho} acoes, "
                  f"custo {resultado.custo} min")
        else:
            print(f"  SEM PLANO           : {resultado.motivo}")

    # ---- [4] linha de base -------------------------------------------------
    guloso = executor_guloso.executar(dados, roteamento, CAMINHO_DOMINIO)

    if not silencioso:
        titulo("[4] LINHA DE BASE - executor guloso (o 'script simples')")
        if guloso.sucesso:
            print(f"  Plano: {guloso.tamanho} acoes, custo {guloso.custo} min")
        else:
            print(f"  FALHOU: {guloso.motivo}")

        imprimir_roteiro(resultado, guloso, dados)
        imprimir_comparacao(resultado, guloso)

    return {
        "dados": dados,
        "roteamento": roteamento,
        "tarefa": tarefa,
        "planejador": resultado,
        "guloso": guloso,
    }


def imprimir_roteiro(resultado, guloso, dados: dict) -> None:
    """Imprime o roteiro do turno - a entrega que chegaria ao ACS."""
    titulo("ROTEIRO DO TURNO (saida do planejador)")
    if not resultado.sucesso:
        print("  Nenhum plano viavel foi encontrado.")
        print(f"  Motivo: {resultado.motivo}")
        print()
        print("  Este resultado NAO e uma falha do prototipo: e a resposta")
        print("  correta quando as condicoes legais do art. 3o par. 4o nao")
        print("  sao satisfeitas. O planejador PROVA que nenhuma sequencia de")
        print("  acoes cumpre o protocolo, o que e informacao gerencial util")
        print("  (a equipe precisa remanejar esses pacientes).")
        return

    for numero, acao in enumerate(resultado.plano, start=1):
        marcador = "  "
        if acao.startswith("desviar-para-ubs"):
            marcador = "->"
        elif acao.startswith("reabastecer"):
            marcador = "**"
        print(f"  {numero:>3}. {marcador} {acao}")


def _diferenca_por_acao(plano_otimo: list[str], plano_guloso: list[str]):
    """Tipos de acao cuja contagem difere entre os dois planos.

    Evita afirmar de onde veio a economia: mostra o dado e deixa a leitura
    para quem analisa. Em instancias diferentes o mecanismo e diferente.
    """
    from collections import Counter
    a = Counter(x.split("(")[0] for x in plano_otimo)
    b = Counter(x.split("(")[0] for x in plano_guloso)
    return [(tipo, a.get(tipo, 0), b.get(tipo, 0))
            for tipo in sorted(set(a) | set(b))
            if a.get(tipo, 0) != b.get(tipo, 0)]


def imprimir_comparacao(resultado, guloso) -> None:
    titulo("COMPARACAO: planejador x linha de base")
    print(f"  {'':<22}{'PLANEJADOR':>20}{'GULOSO':>16}")
    print(f"  {'-' * 58}")
    estado_p = "plano encontrado" if resultado.sucesso else "SEM PLANO"
    estado_g = "plano encontrado" if guloso.sucesso else "FALHOU"
    print(f"  {'resultado':<22}{estado_p:>20}{estado_g:>16}")
    if resultado.sucesso and guloso.sucesso:
        print(f"  {'custo total (min)':<22}{resultado.custo:>20}{guloso.custo:>16}")
        print(f"  {'numero de acoes':<22}{resultado.tamanho:>20}{guloso.tamanho:>16}")
        diferenca = guloso.custo - resultado.custo
        if diferenca > 0:
            percentual = 100 * diferenca / guloso.custo
            print()
            print(f"  O planejador economizou {diferenca} min "
                  f"({percentual:.1f}% do turno).")
            print("  Onde a diferenca aparece (contagem por tipo de acao):")
            for tipo, no_plano, no_guloso in _diferenca_por_acao(resultado.plano,
                                                                guloso.plano):
                print(f"    {tipo:<28} planejador {no_plano:>2}  "
                      f"guloso {no_guloso:>2}")
        elif diferenca == 0:
            print()
            print("  Empate nesta instancia: o guloso encontrou o otimo.")
            print("  Esperado quando os insumos bastam para todo o turno - ver H1.")
    print()
    print(f"  Custo de busca do planejador: {resultado.expandidos} nos "
          f"expandidos, {resultado.segundos:.3f}s")
    print("  Custo de busca do guloso    : 0 nos (uma unica passada pela rota)")


def main() -> None:
    analisador = argparse.ArgumentParser(
        description="Prototipo PCI Projeto 2 - roteamento + planejamento")
    analisador.add_argument("--dados", default=CAMINHO_DADOS_PADRAO)
    analisador.add_argument("--estrategia",
                            choices=["astar-hmax", "astar-hadd", "gbfs"],
                            default="astar-hmax")
    analisador.add_argument("--sem-curso-tecnico", action="store_true",
                            help="experimento E3: remove a habilitacao legal "
                                 "do ACS e observa o planejador provar a "
                                 "inviabilidade do protocolo")
    argumentos = analisador.parse_args()

    executar_pipeline(argumentos.dados, argumentos.estrategia,
                      argumentos.sem_curso_tecnico)


if __name__ == "__main__":
    main()
