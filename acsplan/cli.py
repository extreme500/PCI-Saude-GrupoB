"""
Interface de linha de comando do acsplan.

O sistema tem tres camadas, executadas nesta ordem:

    [1] SELECAO      quem entra no turno de hoje
                     prioridade clinica + atraso + orcamento de tempo
                          |
    [2] ROTEAMENTO   em que ordem visitar
                     vizinho mais proximo + 2-opt, ou algoritmo genetico
                     distancias por haversine ou por servico OSRM
                          |
    [3] PLANEJAMENTO o que fazer em cada parada
                     dominio PDDL (legal ou estendido), busca A*/GBFS
                          |
    [4] SAIDA        roteiro do turno, no formato que o agente usa

Uso:
    python -m acsplan planejar
    python -m acsplan planejar --metodo ag --distancias osrm
    python -m acsplan planejar --dominio estendido --orcamento 240
    python -m acsplan planejar --sem-curso-tecnico
    python -m acsplan roteiro --orcamento 240 --salvar roteiro.txt
    python -m acsplan experimentos --experimento e2
"""

from __future__ import annotations

import argparse
import json
import os

from .dados import gerador, modelos
from .geo import roteirizador
from .logica import executor_guloso
from .logica.gerador_problema import gerar_problema
from .logica.planejador import (TarefaPlanejamento, carregar_dominio,
                                carregar_problema, resolver)
from .saida import roteiro as saida_roteiro
from .selecao import politica

RAIZ = os.path.dirname(os.path.abspath(__file__))
DOMINIOS = {
    "legal": os.path.join(RAIZ, "logica", "dominios", "dominio-legal.pddl"),
    "estendido": os.path.join(RAIZ, "logica", "dominios", "dominio-estendido.pddl"),
}
CAMINHO_PROBLEMA = os.path.join(RAIZ, "logica", "problema_gerado.pddl")
DADOS_PADRAO = os.path.join(RAIZ, "dados", "microarea_exemplo.json")


def titulo(texto: str) -> None:
    print()
    print("=" * 74)
    print(f"  {texto}")
    print("=" * 74)


def executar_pipeline(args, *, silencioso: bool = False) -> dict:
    """Roda as tres camadas e devolve tudo o que elas produziram."""
    if args.instancia_sintetica:
        n, semente = args.instancia_sintetica
        dados = gerador.gerar(n, semente)
    else:
        with open(args.dados, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

    if args.sem_curso_tecnico:
        dados["agente"]["curso_tecnico_concluido"] = False

    caminho_dominio = DOMINIOS[args.dominio]
    intervalo = dados.get("_meta", {}).get(
        "intervalo_maximo_padrao_dias", modelos.INTERVALO_MAXIMO_PADRAO_DIAS)

    # ---- [1] selecao ------------------------------------------------------
    dados = politica.selecionar(
        dados,
        orcamento_minutos=args.orcamento,
        maximo_pacientes=args.max_pacientes,
        ativar=not args.sem_selecao)
    selecao = dados["_selecao"]

    if not silencioso:
        titulo("[1] SELECAO DO TURNO")
        if not selecao["ativa"]:
            print(f"  Politica desativada: os {len(dados['pacientes'])} pacientes "
                  "da microarea entram no turno.")
        else:
            print(f"  Orcamento          : {selecao['orcamento_minutos'] or '-'} min"
                  f"  |  maximo: {selecao['maximo_pacientes'] or '-'} pacientes")
            print(f"  Selecionados ({len(selecao['selecionados']):>2}) : "
                  f"{', '.join(selecao['selecionados'])}")
            if selecao["adiados"]:
                print(f"  Adiados      ({len(selecao['adiados']):>2}) : "
                      f"{', '.join(selecao['adiados'])}")
            if selecao["inadiaveis"]:
                print(f"  Inadiaveis (atraso >= {politica.ATRASO_INADIAVEL_DIAS}d): "
                      f"{', '.join(selecao['inadiaveis'])}")
            if selecao.get("estourou_orcamento"):
                print("  [aviso] os inadiaveis estouram o orcamento nominal do turno.")

    # ---- [2] roteamento ---------------------------------------------------
    roteamento = roteirizador.roteirizar(
        dados,
        metodo=args.metodo,
        provedor_distancia=args.distancias,
        usar_precedencia=not args.sem_precedencia,
        semente=args.semente,
        silencioso=silencioso)

    if not silencioso:
        titulo("[2] ROTEAMENTO")
        metodo = {"nn2opt": "vizinho mais proximo + 2-opt",
                  "ag": "algoritmo genetico"}[args.metodo]
        print(f"  Metodo             : {metodo}")
        print(f"  Distancias         : {roteamento['provedor_distancia']}")
        print(f"  Rota               : {' -> '.join(roteamento['rota'])}")
        print(f"  Custo do trajeto   : {roteamento['custo_rota']} min de caminhada")
        if roteamento["precedencias"]:
            pares = sum(len(v) for v in roteamento["precedencias"].values())
            print(f"  Precedencias       : {pares} restricoes de urgencia ativas")
        if roteamento["metricas_ag"]:
            m = roteamento["metricas_ag"]
            print(f"  AG                 : {m['geracoes']} geracoes, "
                  f"melhor na geracao {m['melhor_geracao']}")

    # ---- [3] planejamento -------------------------------------------------
    gerar_problema(dados, roteamento, CAMINHO_PROBLEMA, dominio=args.dominio)
    tarefa = TarefaPlanejamento(carregar_dominio(caminho_dominio),
                                carregar_problema(CAMINHO_PROBLEMA))
    resultado = resolver(tarefa, args.estrategia, limite_segundos=args.limite)

    if not silencioso:
        titulo("[3] PLANEJAMENTO")
        rotulos = {"astar-hmax": "A* com h_max (otimo, com garantia)",
                   "astar-hadd": "A* com h_add (informado, sem garantia formal)",
                   "gbfs": "GBFS com h_add (satisfaciente, rapido)"}
        print(f"  Dominio            : {args.dominio}")
        print(f"  Estrategia         : {rotulos[args.estrategia]}")
        print(f"  Acoes instanciadas : {len(tarefa.acoes)}")
        print(f"  Nos expandidos     : {resultado.expandidos}")
        print(f"  Tempo de busca     : {resultado.segundos:.3f}s")
        if resultado.sucesso:
            print(f"  Plano              : {resultado.tamanho} acoes, "
                  f"custo {resultado.custo} min")
        else:
            print(f"  SEM PLANO          : {resultado.motivo}")

    guloso = executor_guloso.executar(dados, roteamento, caminho_dominio,
                                      estendido=args.dominio == "estendido")

    return {"dados": dados, "roteamento": roteamento, "tarefa": tarefa,
            "planejador": resultado, "guloso": guloso,
            "caminho_dominio": caminho_dominio, "intervalo": intervalo}


def comando_planejar(args) -> None:
    estado = executar_pipeline(args)
    resultado, guloso = estado["planejador"], estado["guloso"]

    titulo("[4] COMPARACAO COM O EXECUTOR PROCEDURAL")
    print(f"  {'':<24}{'PLANEJADOR':>18}{'PROCEDURAL':>16}")
    print(f"  {'-' * 58}")
    print(f"  {'resultado':<24}"
          f"{('plano' if resultado.sucesso else 'SEM PLANO'):>18}"
          f"{('plano' if guloso.sucesso else 'FALHOU'):>16}")
    if resultado.sucesso and guloso.sucesso:
        print(f"  {'custo total (min)':<24}{resultado.custo:>18}{guloso.custo:>16}")
        print(f"  {'numero de acoes':<24}{resultado.tamanho:>18}{guloso.tamanho:>16}")
        diferenca = guloso.custo - resultado.custo
        if diferenca:
            print()
            print(f"  Diferenca de {diferenca} min. Onde ela aparece:")
            from collections import Counter
            a = Counter(x.split("(")[0] for x in resultado.plano)
            b = Counter(x.split("(")[0] for x in guloso.plano)
            for tipo in sorted(set(a) | set(b)):
                if a.get(tipo, 0) != b.get(tipo, 0):
                    print(f"    {tipo:<34} planejador {a.get(tipo,0):>2}"
                          f"   procedural {b.get(tipo,0):>2}")
    elif not guloso.sucesso:
        print()
        print(f"  O executor procedural falhou: {guloso.motivo}")
        if resultado.sucesso:
            print("  O planejador encontrou plano valido para o mesmo turno.")

    if not resultado.sucesso:
        print()
        print("  Nenhum plano viavel foi encontrado. Isto nao e uma falha do")
        print("  sistema: quando as condicoes legais nao sao satisfeitas, a")
        print("  resposta correta e demonstrar que nenhuma sequencia de acoes")
        print("  cumpre o protocolo, o que e informacao gerencial util.")
        return

    if args.mostrar_plano:
        titulo("PLANO COMPLETO (representacao interna)")
        for numero, acao in enumerate(resultado.plano, start=1):
            print(f"  {numero:>3}. {acao}")


def comando_roteiro(args) -> None:
    estado = executar_pipeline(args, silencioso=True)
    resultado = estado["planejador"]
    if not resultado.sucesso:
        print("Nao foi possivel montar o roteiro: o turno solicitado e inexequivel.")
        print(f"Motivo: {resultado.motivo}")
        print("Reveja a selecao de pacientes ou os recursos disponiveis.")
        raise SystemExit(1)

    custos = executor_guloso.custos_do_dominio(estado["caminho_dominio"])
    paradas = saida_roteiro.montar(resultado.plano, estado["dados"], custos,
                                   estado["roteamento"]["matriz"])
    texto = saida_roteiro.imprimir(paradas, estado["dados"],
                                   custo_total=resultado.custo,
                                   orcamento=args.orcamento)
    print(texto)
    if args.salvar:
        saida_roteiro.salvar(texto, args.salvar)
        print(f"\n[salvo em {args.salvar}]")


def comando_experimentos(args) -> None:
    from .experimentos import rodar
    rodar.main(args.experimento)


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="acsplan",
        description="Planejamento de visitas domiciliares de Agentes "
                    "Comunitarios de Saude.")
    sub = p.add_subparsers(dest="comando", required=True)

    def comuns(sp):
        sp.add_argument("--dados", default=DADOS_PADRAO)
        sp.add_argument("--instancia-sintetica", nargs=2, type=int,
                        metavar=("N", "SEMENTE"),
                        help="usa uma microarea sorteada em vez do arquivo")
        sp.add_argument("--dominio", choices=["legal", "estendido"], default="legal")
        sp.add_argument("--metodo", choices=["nn2opt", "ag"], default="nn2opt")
        sp.add_argument("--distancias", choices=["haversine", "osrm"],
                        default="haversine")
        sp.add_argument("--estrategia", choices=["astar-hmax", "astar-hadd", "gbfs"],
                        default="astar-hmax")
        sp.add_argument("--orcamento", type=int, default=None,
                        metavar="MIN", help="orcamento do turno em minutos")
        sp.add_argument("--max-pacientes", type=int, default=None)
        sp.add_argument("--sem-selecao", action="store_true")
        sp.add_argument("--sem-precedencia", action="store_true")
        sp.add_argument("--sem-curso-tecnico", action="store_true",
                        help="remove a habilitacao legal do ACS")
        sp.add_argument("--semente", type=int, default=0)
        sp.add_argument("--limite", type=float, default=60.0,
                        metavar="S", help="limite de tempo da busca")

    sp = sub.add_parser("planejar", help="executa o pipeline completo")
    comuns(sp)
    sp.add_argument("--mostrar-plano", action="store_true")
    sp.set_defaults(func=comando_planejar)

    sp = sub.add_parser("roteiro", help="imprime o roteiro do turno para o ACS")
    comuns(sp)
    sp.add_argument("--salvar", metavar="ARQUIVO")
    sp.set_defaults(func=comando_roteiro)

    sp = sub.add_parser("experimentos", help="executa os experimentos")
    sp.add_argument("--experimento",
                    choices=["e1","e2","e3","e4","e5","e6","e7","e8","e9","e10","todos"],
                    default="todos")
    sp.set_defaults(func=comando_experimentos)

    return p


def main(argv: list[str] | None = None) -> None:
    args = construir_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
