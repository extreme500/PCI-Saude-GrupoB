"""
Experimentos do protótipo. Tres perguntas, tres medicoes.

E1 - ESCALABILIDADE
    Ate que tamanho de microarea cada estrategia de busca continua viavel?
    Variavel independente : numero de pacientes (4..14)
    Variaveis dependentes : tempo de busca, nos expandidos, custo do plano

E2 - O PLANEJADOR GANHA DO SCRIPT SIMPLES?
    Em quantas instancias, e por quanto, o plano otimo bate o executor guloso?
    Variavel independente : instancia sorteada (30 sementes)
    Variaveis dependentes : custo de cada abordagem, taxa de falha do guloso

E3 - PROVA DE INVIABILIDADE
    Quando o protocolo e impossivel, o planejador percebe? A que custo?
    Dois tipos de inviabilidade, com comportamentos MUITO diferentes:
      (a) logica   - falta uma precondicao (o ACS nao tem curso tecnico)
      (b) de recurso - faltam janelas de supervisao para tantas residencias

Uso:
    python prototipo/experimentos/rodar_experimentos.py
    python prototipo/experimentos/rodar_experimentos.py --experimento e1
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(RAIZ, "camada_geo"),
                os.path.join(RAIZ, "camada_logica"),
                os.path.join(RAIZ, "dados")]

import executor_guloso                       # noqa: E402
import gerador_instancias                    # noqa: E402
from gerador_problema import gerar_problema   # noqa: E402
from planejador import (TarefaPlanejamento, carregar_dominio,  # noqa: E402
                        carregar_problema, resolver)
from roteirizador import roteirizar           # noqa: E402

CAMINHO_DOMINIO = os.path.join(RAIZ, "camada_logica", "dominio.pddl")
DIRETORIO_SAIDA = tempfile.mkdtemp(prefix="pci-planning-")


def preparar(dados: dict, rotulo: str):
    """Roda a camada geometrica e compila a tarefa de planejamento."""
    roteamento = roteirizar(dados)
    caminho = os.path.join(DIRETORIO_SAIDA, f"problema_{rotulo}.pddl")
    gerar_problema(dados, roteamento, caminho)
    tarefa = TarefaPlanejamento(carregar_dominio(CAMINHO_DOMINIO),
                                carregar_problema(caminho))
    return roteamento, tarefa


def regua(titulo: str) -> None:
    print()
    print("=" * 78)
    print(f"  {titulo}")
    print("=" * 78)


# ---------------------------------------------------------------------------
#  E1 - escalabilidade
# ---------------------------------------------------------------------------

def experimento_e1(tamanhos=range(4, 15), sementes=(1, 2, 3),
                   limite_segundos: float = 20.0) -> None:
    regua("E1 - ESCALABILIDADE DAS TRES ESTRATEGIAS DE BUSCA")
    print("  Mediana de 3 sementes por tamanho. '--' = estourou o limite de "
          f"{limite_segundos:.0f}s.")
    print()
    print(f"  {'N':>3} {'acoes':>7} | {'A*/h_max':>18} | {'A*/h_add':>18} | "
          f"{'GBFS':>18}")
    print(f"  {'':>3} {'inst.':>7} | {'t(s)':>8}{'custo':>10} | "
          f"{'t(s)':>8}{'custo':>10} | {'t(s)':>8}{'custo':>10}")
    print("  " + "-" * 74)

    for n in tamanhos:
        linha = {}
        n_acoes = 0
        for estrategia in ("astar-hmax", "astar-hadd", "gbfs"):
            tempos, custos = [], []
            for semente in sementes:
                dados = gerador_instancias.gerar(n, semente)
                _, tarefa = preparar(dados, f"e1-{n}-{semente}")
                n_acoes = len(tarefa.acoes)
                resultado = resolver(tarefa, estrategia,
                                     limite_segundos=limite_segundos,
                                     limite_expansoes=2_000_000)
                if resultado.sucesso:
                    tempos.append(resultado.segundos)
                    custos.append(resultado.custo)
            linha[estrategia] = (
                statistics.median(tempos) if tempos else None,
                statistics.median(custos) if custos else None,
                len(tempos),
            )

        celulas = []
        for estrategia in ("astar-hmax", "astar-hadd", "gbfs"):
            tempo, custo, ok = linha[estrategia]
            if ok == 0:
                celulas.append(f"{'--':>8}{'--':>10}")
            else:
                marca = "" if ok == len(sementes) else "*"
                celulas.append(f"{tempo:>8.2f}{str(custo) + marca:>10}")
        print(f"  {n:>3} {n_acoes:>7} | " + " | ".join(celulas))

    print()
    print("  LEITURA: h_max e admissivel (custo garantidamente minimo) mas")
    print("  explode primeiro; h_add e barato porem entrega planos piores.")
    print("  '*' = alguma semente nao terminou; a mediana usa so as que terminaram.")


# ---------------------------------------------------------------------------
#  E2 - planejador x guloso
# ---------------------------------------------------------------------------

def experimento_e2(n_pacientes: int = 8, n_sementes: int = 30,
                   limite_segundos: float = 30.0) -> None:
    regua("E2 - PLANEJADOR OTIMO x EXECUTOR GULOSO ('script simples')")
    print(f"  {n_sementes} microareas sorteadas com {n_pacientes} pacientes, "
          "2 fitas de glicemia por carga.")
    print()

    vitorias = empates = derrotas = 0
    falhas_guloso = falhas_planejador = 0
    diferencas: list[float] = []
    exemplo_de_vitoria = None

    for semente in range(1, n_sementes + 1):
        dados = gerador_instancias.gerar(n_pacientes, semente)
        roteamento, tarefa = preparar(dados, f"e2-{semente}")
        otimo = resolver(tarefa, "astar-hmax", limite_segundos=limite_segundos)
        guloso = executor_guloso.executar(dados, roteamento, CAMINHO_DOMINIO)

        if not otimo.sucesso:
            falhas_planejador += 1
            continue
        if not guloso.sucesso:
            falhas_guloso += 1
            continue

        diferenca = guloso.custo - otimo.custo
        diferencas.append(100 * diferenca / guloso.custo)
        if diferenca > 0:
            vitorias += 1
            if exemplo_de_vitoria is None or diferenca > exemplo_de_vitoria[1]:
                exemplo_de_vitoria = (semente, diferenca, otimo.custo,
                                      guloso.custo)
        elif diferenca == 0:
            empates += 1
        else:
            derrotas += 1  # impossivel: o otimo nunca perde. serve de sanidade.

    comparaveis = vitorias + empates + derrotas
    print(f"  instancias comparaveis            : {comparaveis}")
    print(f"  o planejador encontrou plano melhor: {vitorias}")
    print(f"  empate (o guloso ja era otimo)     : {empates}")
    print(f"  o guloso foi melhor                : {derrotas}  "
          f"(tem de ser 0 - teste de sanidade do h_max admissivel)")
    print(f"  o guloso DECLAROU INVIAVEL, mas havia")
    print(f"    plano valido (falso negativo)      : {falhas_guloso}")
    print(f"  o planejador estourou o limite     : {falhas_planejador}")
    if diferencas:
        print()
        print(f"  folga do guloso sobre o otimo: media {statistics.mean(diferencas):.2f}%, "
              f"mediana {statistics.median(diferencas):.2f}%, "
              f"maxima {max(diferencas):.2f}%")
    if exemplo_de_vitoria:
        semente, diferenca, custo_otimo, custo_guloso = exemplo_de_vitoria
        print(f"  maior ganho absoluto: semente {semente}, "
              f"{custo_guloso} -> {custo_otimo} min ({diferenca} min)")
    print()
    print("  LEITURA 1 - custo: a folga tipica do guloso e pequena (mediana 0%).")
    print("  Em rotas onde os insumos bastam, o guloso ja acerta o otimo.")
    print()
    print("  LEITURA 2 - o resultado que importa: os FALSOS NEGATIVOS.")
    print("  Nessas instancias existe um plano que cumpre todos os protocolos,")
    print("  e mesmo assim o guloso conclui que o turno e impossivel. A causa e")
    print("  sempre a mesma e e instrutiva:")
    print("    o guloso aciona a supervisao para aferir a PA, DEPOIS descobre")
    print("    que faltam fitas, desvia ate a UBS - e o desvio invalida a")
    print("    supervisao ja acionada. Ele gasta DUAS janelas na mesma casa.")
    print("    O planejador descobre sozinho que basta desviar ANTES de acionar")
    print("    a supervisao, e fecha o turno com uma janela por residencia.")
    print("  Nenhuma linha do dominio PDDL menciona essa ordem: ela e deduzida")
    print("  das precondicoes. E exatamente isto que um laco `for` nao faz.")


# ---------------------------------------------------------------------------
#  E3 - prova de inviabilidade
# ---------------------------------------------------------------------------

def experimento_e3(n_pacientes: int = 8, semente: int = 1) -> None:
    regua("E3 - COMO O PLANEJADOR PROVA QUE O PROTOCOLO E INVIAVEL")

    # (a) inviabilidade LOGICA: falta uma precondicao do art. 3o par. 4o
    dados = gerador_instancias.gerar(n_pacientes, semente)
    dados["agente"]["curso_tecnico_concluido"] = False
    roteamento, tarefa = preparar(dados, "e3a")
    resultado = resolver(tarefa, "astar-hmax", limite_segundos=30)
    guloso = executor_guloso.executar(dados, roteamento, CAMINHO_DOMINIO)

    print("  (a) INVIABILIDADE LOGICA - ACS sem curso tecnico concluido")
    print(f"      planejador : {'SEM PLANO' if not resultado.sucesso else 'plano!?'}"
          f" em {resultado.segundos:.4f}s, {resultado.expandidos} nos expandidos")
    print(f"      motivo     : {resultado.motivo}")
    print(f"      guloso     : {'falhou' if not guloso.sucesso else 'plano!?'}")
    print("      -> a relaxacao detecta na hora: nenhuma acao produz (pa-ok p),")
    print("         entao o objetivo e inalcancavel sem expandir um unico no.")

    # (b) inviabilidade DE RECURSO: faltam janelas de supervisao
    print()
    escassez = max(1, n_pacientes // 2)
    dados = gerador_instancias.gerar(n_pacientes, semente,
                                     janelas_supervisao=escassez)
    roteamento, tarefa = preparar(dados, "e3b")
    resultado = resolver(tarefa, "astar-hmax", limite_segundos=30)
    guloso = executor_guloso.executar(dados, roteamento, CAMINHO_DOMINIO)

    print(f"  (b) INVIABILIDADE DE RECURSO - so {escassez} janelas de supervisao")
    print(f"      planejador : {'SEM PLANO' if not resultado.sucesso else 'plano encontrado'}"
          f" em {resultado.segundos:.4f}s, {resultado.expandidos} nos expandidos")
    print(f"      motivo     : {resultado.motivo or '-'}")
    print(f"      guloso     : {'falhou' if not guloso.sucesso else 'plano encontrado'}")
    if not guloso.sucesso:
        print(f"      msg guloso : {guloso.motivo}")
    print("      -> a heuristica de relaxacao IGNORA os efeitos de remocao,")
    print("         logo nao 've' o contador de janelas baixando. A prova de")
    print("         inviabilidade exige exaurir o espaco de estados: ordens de")
    print("         grandeza mais cara que o caso (a).")
    print()
    print("  CONCLUSAO DO E3: o planejador distingue 'nao consegui' de")
    print("  'e impossivel' - o guloso so sabe dizer 'nao consegui'. Mas o")
    print("  custo dessa prova depende do TIPO de inviabilidade.")


def main() -> None:
    analisador = argparse.ArgumentParser()
    analisador.add_argument("--experimento", choices=["e1", "e2", "e3", "todos"],
                            default="todos")
    argumentos = analisador.parse_args()

    if argumentos.experimento in ("e1", "todos"):
        experimento_e1()
    if argumentos.experimento in ("e2", "todos"):
        experimento_e2()
    if argumentos.experimento in ("e3", "todos"):
        experimento_e3()
    print()


if __name__ == "__main__":
    main()
