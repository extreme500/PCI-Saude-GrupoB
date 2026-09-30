"""
Experimentos controlados.

E1  Escalabilidade das estrategias de busca.
E2  Planejamento x executor procedural: custo e falsos negativos.
E3  Provas de inviabilidade: logica x de recurso.
E4  Roteirizacao: algoritmo genetico x vizinho mais proximo com 2-opt.
E5  Politica de selecao do turno: o que muda quando ela entra.
E6  Dominio legal x dominio estendido: custo da complexidade normativa.

Uso:
    python -m acsplan experimentos
    python -m acsplan experimentos --experimento e4
"""

from __future__ import annotations

import os
import statistics
import tempfile
import time

from ..dados import gerador, modelos
from ..geo import roteirizador
from ..geo.distancias import custo_da_rota
from ..logica import executor_guloso
from ..logica.gerador_problema import gerar_problema
from ..logica.planejador import (TarefaPlanejamento, carregar_dominio,
                                 carregar_problema, resolver)
from ..selecao import politica

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMINIOS = {
    "legal": os.path.join(RAIZ, "logica", "dominios", "dominio-legal.pddl"),
    "estendido": os.path.join(RAIZ, "logica", "dominios", "dominio-estendido.pddl"),
}
SAIDA = tempfile.mkdtemp(prefix="acsplan-exp-")


def preparar(dados: dict, rotulo: str, *, dominio: str = "legal",
             metodo: str = "nn2opt", precedencia: bool = True):
    roteamento = roteirizador.roteirizar(dados, metodo=metodo,
                                         usar_precedencia=precedencia)
    caminho = os.path.join(SAIDA, f"problema_{rotulo}.pddl")
    gerar_problema(dados, roteamento, caminho, dominio=dominio)
    tarefa = TarefaPlanejamento(carregar_dominio(DOMINIOS[dominio]),
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
                   limite_segundos: float = 25.0) -> None:
    regua("E1 - ESCALABILIDADE DAS ESTRATEGIAS DE BUSCA (dominio legal)")
    print(f"  Mediana de {len(sementes)} sementes por tamanho. "
          f"'--' = estourou o limite de {limite_segundos:.0f}s.")
    print()
    print(f"  {'N':>3} {'acoes':>7} | {'A*/h_max':>18} | {'A*/h_add':>18} | {'GBFS':>18}")
    print(f"  {'':>3} {'inst.':>7} | {'t(s)':>8}{'custo':>10} | "
          f"{'t(s)':>8}{'custo':>10} | {'t(s)':>8}{'custo':>10}")
    print("  " + "-" * 74)

    for n in tamanhos:
        linha, n_acoes = {}, 0
        for estrategia in ("astar-hmax", "astar-hadd", "gbfs"):
            tempos, custos = [], []
            for semente in sementes:
                dados = gerador.gerar(n, semente)
                _, tarefa = preparar(dados, f"e1-{n}-{semente}")
                n_acoes = len(tarefa.acoes)
                r = resolver(tarefa, estrategia, limite_segundos=limite_segundos,
                             limite_expansoes=2_000_000)
                if r.sucesso:
                    tempos.append(r.segundos)
                    custos.append(r.custo)
            linha[estrategia] = (statistics.median(tempos) if tempos else None,
                                 statistics.median(custos) if custos else None,
                                 len(tempos))
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
    print("  LEITURA: h_max e admissivel (custo garantidamente minimo) e e a que")
    print("  cresce mais rapido; as satisfacientes sao mais rapidas e entregam")
    print("  planos piores. '*' = alguma semente nao terminou.")


# ---------------------------------------------------------------------------
#  E2 - planejador x executor procedural
# ---------------------------------------------------------------------------

def experimento_e2(n_pacientes: int = 8, n_sementes: int = 30,
                   limite_segundos: float = 30.0) -> None:
    regua("E2 - PLANEJAMENTO x EXECUTOR PROCEDURAL")
    print(f"  {n_sementes} microareas sorteadas com {n_pacientes} pacientes.")
    print()

    vitorias = empates = derrotas = 0
    falsos_negativos = falhas_planejador = 0
    diferencas: list[float] = []
    melhor = None

    for semente in range(1, n_sementes + 1):
        dados = gerador.gerar(n_pacientes, semente)
        roteamento, tarefa = preparar(dados, f"e2-{semente}")
        otimo = resolver(tarefa, "astar-hmax", limite_segundos=limite_segundos)
        guloso = executor_guloso.executar(dados, roteamento, DOMINIOS["legal"])

        if not otimo.sucesso:
            falhas_planejador += 1
            continue
        if not guloso.sucesso:
            falsos_negativos += 1
            continue

        diferenca = guloso.custo - otimo.custo
        diferencas.append(100 * diferenca / guloso.custo)
        if diferenca > 0:
            vitorias += 1
            if melhor is None or diferenca > melhor[1]:
                melhor = (semente, diferenca, otimo.custo, guloso.custo)
        elif diferenca == 0:
            empates += 1
        else:
            derrotas += 1

    comparaveis = vitorias + empates + derrotas
    print(f"  instancias comparaveis                : {comparaveis}")
    print(f"  planejamento achou plano mais barato  : {vitorias}")
    print(f"  empate (o procedural ja era otimo)    : {empates}")
    print(f"  procedural melhor que o otimo         : {derrotas}   "
          f"(tem de ser 0: teste de sanidade do h_max)")
    print(f"  FALSO NEGATIVO do procedural          : {falsos_negativos}   "
          f"(declarou inviavel havendo plano valido)")
    print(f"  planejamento estourou o limite        : {falhas_planejador}")
    if diferencas:
        print()
        print(f"  folga de custo do procedural: media {statistics.mean(diferencas):.2f}%, "
              f"mediana {statistics.median(diferencas):.2f}%, "
              f"maxima {max(diferencas):.2f}%")
    if melhor:
        s, d, co, cg = melhor
        print(f"  maior ganho absoluto: semente {s}, {cg} -> {co} min ({d} min)")
    print()
    print("  LEITURA: o ganho tipico de custo e pequeno. O resultado que importa")
    print("  sao os falsos negativos, em que o procedural desperdica um recurso")
    print("  escasso por nao antecipar e conclui que o turno e impossivel.")


# ---------------------------------------------------------------------------
#  E3 - prova de inviabilidade
# ---------------------------------------------------------------------------

def experimento_e3(n_pacientes: int = 8, semente: int = 1) -> None:
    regua("E3 - PROVAS DE INVIABILIDADE")

    dados = gerador.gerar(n_pacientes, semente)
    dados["agente"]["curso_tecnico_concluido"] = False
    roteamento, tarefa = preparar(dados, "e3a")
    r = resolver(tarefa, "astar-hmax", limite_segundos=30)
    g = executor_guloso.executar(dados, roteamento, DOMINIOS["legal"])
    print("  (a) INVIABILIDADE LOGICA - ACS sem curso tecnico concluido")
    print(f"      planejamento : {'SEM PLANO' if not r.sucesso else 'plano!?'} em "
          f"{r.segundos:.4f}s, {r.expandidos} nos expandidos")
    print(f"      motivo       : {r.motivo}")
    print(f"      procedural   : {'falhou' if not g.sucesso else 'plano!?'}")
    print("      -> nenhuma acao produz o fato exigido nem no problema relaxado,")
    print("         entao a impossibilidade e demonstrada sem expandir um no.")

    print()
    escassez = max(1, n_pacientes // 2)
    dados = gerador.gerar(n_pacientes, semente, janelas_supervisao=escassez)
    roteamento, tarefa = preparar(dados, "e3b")
    r = resolver(tarefa, "astar-hmax", limite_segundos=30)
    g = executor_guloso.executar(dados, roteamento, DOMINIOS["legal"])
    print(f"  (b) INVIABILIDADE DE RECURSO - so {escassez} janelas de supervisao")
    print(f"      planejamento : {'SEM PLANO' if not r.sucesso else 'plano encontrado'} em "
          f"{r.segundos:.4f}s, {r.expandidos} nos expandidos")
    print(f"      motivo       : {r.motivo or '-'}")
    print(f"      procedural   : {'falhou' if not g.sucesso else 'plano encontrado'}")
    print("      -> a relaxacao ignora efeitos de remocao e nao 've' o contador")
    print("         baixar; a prova exige exaurir o espaco de estados.")
    print()
    print("  LEITURA: o planejamento distingue 'nao consegui' de 'e impossivel'.")
    print("  O custo dessa prova depende do TIPO de inviabilidade.")


# ---------------------------------------------------------------------------
#  E4 - roteirizacao: AG x vizinho mais proximo + 2-opt
# ---------------------------------------------------------------------------

def experimento_e4(tamanhos=(8, 12, 16, 20, 30), n_sementes: int = 5) -> None:
    regua("E4 - ROTEIRIZACAO: ALGORITMO GENETICO x VIZINHO MAIS PROXIMO + 2-OPT")
    print(f"  {n_sementes} microareas por tamanho. Custo em minutos de caminhada,")
    print("  medindo apenas a camada geometrica (a camada logica nao entra aqui).")
    print()
    print(f"  {'N':>3} | {'nn2opt':>16} | {'AG':>16} | {'diferenca':>20}")
    print(f"  {'':>3} | {'custo':>8}{'t(s)':>8} | {'custo':>8}{'t(s)':>8} | "
          f"{'min':>9}{'%':>11}")
    print("  " + "-" * 66)

    for n in tamanhos:
        c_nn, t_nn, c_ag, t_ag = [], [], [], []
        for semente in range(1, n_sementes + 1):
            dados = gerador.gerar(n, semente)
            inicio = time.perf_counter()
            r1 = roteirizador.roteirizar(dados, metodo="nn2opt")
            t_nn.append(time.perf_counter() - inicio)
            c_nn.append(r1["custo_rota"])

            inicio = time.perf_counter()
            r2 = roteirizador.roteirizar(dados, metodo="ag", semente=semente)
            t_ag.append(time.perf_counter() - inicio)
            c_ag.append(r2["custo_rota"])

        m_nn, m_ag = statistics.mean(c_nn), statistics.mean(c_ag)
        ganho = m_nn - m_ag
        pct = 100 * ganho / m_nn if m_nn else 0
        print(f"  {n:>3} | {m_nn:>8.1f}{statistics.mean(t_nn):>8.2f} | "
              f"{m_ag:>8.1f}{statistics.mean(t_ag):>8.2f} | "
              f"{ganho:>+9.1f}{pct:>+10.1f}%")

    print()
    print("  LEITURA: o AG encontra rotas mais baratas em todos os tamanhos")
    print("  testados, e a vantagem nao desaparece nas instancias pequenas. A")
    print("  explicacao provavel esta na precedencia: o 2-opt so a respeita")
    print("  RECUSANDO movimentos, o que o prende mais cedo num otimo local,")
    print("  enquanto o AG repara a ordem depois de cruzar e mutar, e por isso")
    print("  explora regioes que o refino local nao alcanca.")
    print()
    print("  O preco e o tempo: cerca de 1s contra alguns milissegundos. Para um")
    print("  turno planejado uma vez por dia isso e irrelevante, mas e o tipo de")
    print("  medicao que precisa ser refeita antes de generalizar a afirmacao.")


# ---------------------------------------------------------------------------
#  E5 - politica de selecao do turno
# ---------------------------------------------------------------------------

def experimento_e5(n_pacientes: int = 14, n_sementes: int = 12,
                   orcamento: int = 240) -> None:
    regua("E5 - POLITICA DE SELECAO DO TURNO")
    print(f"  {n_sementes} microareas de {n_pacientes} pacientes, "
          f"orcamento de {orcamento} min.")
    print("  Compara o turno completo com o turno selecionado por prioridade")
    print("  clinica e atraso em relacao ao intervalo maximo entre visitas.")
    print()

    sem_pol_atrasados, com_pol_atrasados = [], []
    sem_pol_urgentes, com_pol_urgentes = [], []
    tamanhos = []

    for semente in range(1, n_sementes + 1):
        dados = gerador.gerar(n_pacientes, semente)
        todos = dados["pacientes"]
        atrasados = [p for p in todos if modelos.esta_atrasado(p)]
        urgentes = [p for p in todos if modelos.nivel_urgencia(p) == 3]

        selecionado = politica.selecionar(dados, orcamento_minutos=orcamento)
        escolhidos = {p["id"] for p in selecionado["pacientes"]}
        tamanhos.append(len(escolhidos))

        # Linha de base: cortar o turno pelo tamanho, sem criterio, pegando
        # os primeiros da lista. E o mesmo NUMERO de pacientes, para que a
        # comparacao isole o criterio de escolha e nao o tamanho do turno.
        base = {p["id"] for p in todos[:len(escolhidos)]}

        if atrasados:
            sem_pol_atrasados.append(
                len([p for p in atrasados if p["id"] in base]) / len(atrasados))
            com_pol_atrasados.append(
                len([p for p in atrasados if p["id"] in escolhidos]) / len(atrasados))
        if urgentes:
            sem_pol_urgentes.append(
                len([p for p in urgentes if p["id"] in base]) / len(urgentes))
            com_pol_urgentes.append(
                len([p for p in urgentes if p["id"] in escolhidos]) / len(urgentes))

    def pct(v):
        return f"{100 * statistics.mean(v):.1f}%" if v else "-"

    print(f"  pacientes por turno (media)           : "
          f"{statistics.mean(tamanhos):.1f} de {n_pacientes}")
    print()
    print(f"  {'':<38}{'ordem do arquivo':>18}{'com politica':>16}")
    print(f"  {'-' * 72}")
    print(f"  {'cobertura dos pacientes em atraso':<38}"
          f"{pct(sem_pol_atrasados):>18}{pct(com_pol_atrasados):>16}")
    print(f"  {'cobertura dos de urgencia alta':<38}"
          f"{pct(sem_pol_urgentes):>18}{pct(com_pol_urgentes):>16}")
    print()
    print("  A coluna 'ordem do arquivo' simula o que acontece quando se corta")
    print("  o turno pelo tamanho sem criterio: pegam-se os N primeiros da lista.")
    print()
    print("  LEITURA: a politica existe para que o corte do turno nao seja")
    print("  arbitrario. Prioridade e intervalo maximo saem dos dados e passam")
    print("  a decidir quem e atendido, que era a lacuna mais visivel do projeto")
    print("  em relacao ao enunciado.")


# ---------------------------------------------------------------------------
#  E6 - dominio legal x dominio estendido
# ---------------------------------------------------------------------------

def experimento_e6(tamanhos=(3, 4, 5, 6), sementes=(1, 2),
                   limite_segundos: float = 20.0) -> None:
    regua("E6 - CUSTO DA COMPLEXIDADE NORMATIVA: DOMINIO LEGAL x ESTENDIDO")
    print("  O dominio estendido acrescenta tres protocolos SINTETICOS")
    print("  (higienizacao, protecao respiratoria e descarte de perfurocortante),")
    print(f"  cada um com recurso finito. Limite de {limite_segundos:.0f}s por execucao.")
    print()
    print(f"  {'N':>3} | {'LEGAL':>26} | {'ESTENDIDO':>26}")
    print(f"  {'':>3} | {'acoes':>7}{'t(s)':>9}{'custo':>10} | "
          f"{'acoes':>7}{'t(s)':>9}{'custo':>10}")
    print("  " + "-" * 62)

    for n in tamanhos:
        celulas = []
        for dominio in ("legal", "estendido"):
            tempos, custos, acoes = [], [], 0
            for semente in sementes:
                dados = gerador.gerar(n, semente)
                _, tarefa = preparar(dados, f"e6-{dominio}-{n}-{semente}",
                                     dominio=dominio)
                acoes = len(tarefa.acoes)
                r = resolver(tarefa, "astar-hmax", limite_segundos=limite_segundos)
                if r.sucesso:
                    tempos.append(r.segundos)
                    custos.append(r.custo)
            if tempos:
                celulas.append(f"{acoes:>7}{statistics.median(tempos):>9.2f}"
                               f"{statistics.median(custos):>10}")
            else:
                celulas.append(f"{acoes:>7}{'--':>9}{'--':>10}")
        print(f"  {n:>3} | " + " | ".join(celulas))

    print()
    print("  LEITURA: e o resultado que justifica manter os dois dominios. Cada")
    print("  protocolo acrescentado multiplica o espaco de estados, e a busca")
    print("  otima deixa de ser viavel muito antes. Em producao isso obrigaria a")
    print("  trocar a garantia de otimalidade por busca satisfaciente, o que e")
    print("  uma decisao de engenharia e nao um detalhe de implementacao.")


# ---------------------------------------------------------------------------

EXPERIMENTOS = {
    "e1": experimento_e1, "e2": experimento_e2, "e3": experimento_e3,
    "e4": experimento_e4, "e5": experimento_e5, "e6": experimento_e6,
}


def main(escolhido: str = "todos") -> None:
    alvos = EXPERIMENTOS if escolhido == "todos" else {escolhido: EXPERIMENTOS[escolhido]}
    for funcao in alvos.values():
        funcao()
    print()
