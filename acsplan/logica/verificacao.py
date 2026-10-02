"""
Verificacao cruzada contra um planejador de referencia externo.

POR QUE ISTO EXISTE
-------------------
Todos os resultados do projeto saem de um planejador escrito para ele. Se o
parser lesse o dominio errado, se o grounding descartasse acoes legitimas ou
se a heuristica nao fosse admissivel, os numeros estariam errados e nao
haveria como saber. Essa e a maior ameaca a validade do trabalho, e um bug
exatamente desse tipo ja ocorreu (ver docs/03, "hipotese de nomes unicos").

A conferencia interna entre A*/h_max e UCS (busca cega) reduziu o risco, mas
as duas compartilham o MESMO parser e o MESMO grounding. Um erro ali
afetaria ambas igualmente.

O PLANEJADOR DE REFERENCIA
--------------------------
Usa-se o pyperplan, desenvolvido no grupo de Malte Helmert (Universidade de
Basileia), o mesmo do Fast Downward. E uma implementacao independente, com
parser, grounding e busca proprios, e nao compartilha uma linha de codigo com
este projeto.

O Fast Downward em si exigiria compilacao C++ e nao executa nativamente em
Windows. O pyperplan resolve o mesmo papel de testemunha independente.

A TRANSFORMACAO PARA CUSTO UNITARIO
-----------------------------------
O pyperplan e STRIPS puro e nao aceita `:functions` nem `:action-costs`.
Para submeter os mesmos modelos a ele, gera-se uma variante sem custos:
remove-se o bloco `(:functions ...)`, cada `(increase (total-cost) ...)` dos
efeitos, o requisito `:action-costs`, as atribuicoes numericas do estado
inicial e a metrica.

A transformacao NAO altera quais planos existem: custo nenhum aparece em
precondicao, entao a viabilidade e preservada exatamente. O que muda e o
criterio de otimalidade, que passa a ser NUMERO DE ACOES em vez de minutos.
Por isso a comparacao se da em duas dimensoes bem definidas:

    1. VIABILIDADE   os dois concordam sobre existir ou nao plano?
    2. COMPRIMENTO   os dois concordam sobre o numero minimo de acoes?

Para a segunda, o nosso planejador tambem roda sobre a variante unitaria, de
modo que ambos resolvem exatamente o mesmo problema.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile


# ---------------------------------------------------------------------------
#  Transformacao: remove custos preservando a estrutura logica
# ---------------------------------------------------------------------------

def _remover_sexp(texto: str, abertura: str) -> str:
    """Remove toda s-expressao que comece com `abertura`, com parenteses
    balanceados. Necessario porque `(increase (total-cost) (f ?a ?b))` tem
    parenteses aninhados e um regex simples cortaria no lugar errado."""
    saida = []
    i = 0
    while True:
        j = texto.find(abertura, i)
        if j < 0:
            saida.append(texto[i:])
            return "".join(saida)
        saida.append(texto[i:j])
        profundidade = 0
        k = j
        while k < len(texto):
            if texto[k] == "(":
                profundidade += 1
            elif texto[k] == ")":
                profundidade -= 1
                if profundidade == 0:
                    k += 1
                    break
            k += 1
        i = k


def para_strips_unitario(caminho_dominio: str, caminho_problema: str,
                         destino: str) -> tuple[str, str]:
    """Escreve copias sem custos e devolve os caminhos (dominio, problema)."""
    os.makedirs(destino, exist_ok=True)

    dominio = open(caminho_dominio, encoding="utf-8").read()
    dominio = _remover_sexp(dominio, "(:functions")
    dominio = _remover_sexp(dominio, "(increase")
    dominio = dominio.replace(" :action-costs", "")
    # efeitos podem ter ficado com linhas em branco no meio do (and ...)
    dominio = re.sub(r"\n[ \t]*\n(?=[ \t]*\))", "\n", dominio)

    problema = open(caminho_problema, encoding="utf-8").read()
    problema = _remover_sexp(problema, "(= (total-cost)")
    problema = _remover_sexp(problema, "(= (custo-deslocamento")
    problema = _remover_sexp(problema, "(= (custo-desvio")
    problema = _remover_sexp(problema, "(:metric")

    saida_d = os.path.join(destino, "dominio-unitario.pddl")
    saida_p = os.path.join(destino, "problema-unitario.pddl")
    open(saida_d, "w", encoding="utf-8").write(dominio)
    open(saida_p, "w", encoding="utf-8").write(problema)
    return saida_d, saida_p


# ---------------------------------------------------------------------------
#  Execucao do planejador de referencia
# ---------------------------------------------------------------------------

def pyperplan_disponivel() -> bool:
    try:
        import pyperplan  # noqa: F401
        return True
    except ImportError:
        return False


def executar_pyperplan(caminho_dominio: str, caminho_problema: str,
                       heuristica: str = "hmax", busca: str = "astar",
                       timeout: int = 300) -> dict:
    """Roda o pyperplan e devolve {sucesso, comprimento, plano, erro}."""
    soln = caminho_problema + ".soln"
    if os.path.exists(soln):
        os.remove(soln)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pyperplan", "-H", heuristica, "-s", busca,
             caminho_dominio, caminho_problema],
            capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"sucesso": False, "comprimento": None, "plano": [],
                "erro": f"timeout de {timeout}s"}

    saida = (proc.stdout or "") + (proc.stderr or "")
    if os.path.exists(soln):
        linhas = [l.strip() for l in open(soln, encoding="utf-8") if l.strip()]
        return {"sucesso": True, "comprimento": len(linhas), "plano": linhas,
                "erro": ""}
    if "goal can not be reached" in saida.lower() or "no solution" in saida.lower():
        return {"sucesso": False, "comprimento": None, "plano": [],
                "erro": "sem plano (segundo o pyperplan)"}
    ultima = [l for l in saida.strip().split("\n") if l.strip()]
    return {"sucesso": False, "comprimento": None, "plano": [],
            "erro": ultima[-1][:160] if ultima else "falha desconhecida"}


# ---------------------------------------------------------------------------
#  Comparacao
# ---------------------------------------------------------------------------

def comparar(dados: dict, roteamento: dict, caminho_dominio: str,
             dominio_nome: str = "legal", timeout: int = 300) -> dict:
    """Resolve a MESMA instancia nos dois planejadores e confronta.

    Os dois rodam sobre a variante de custo unitario, para que estejam
    resolvendo exatamente o mesmo problema, e ambos em configuracao otima.
    """
    from .gerador_problema import gerar_problema
    from .planejador import (TarefaPlanejamento, carregar_dominio,
                             carregar_problema, resolver)

    from .compilacao import compilar_negativas

    destino = tempfile.mkdtemp(prefix="acsplan-verif-")
    original = os.path.join(destino, "problema.pddl")
    gerar_problema(dados, roteamento, original, dominio=dominio_nome)

    # duas transformacoes, ambas preservando o conjunto de planos validos:
    # custo unitario (o pyperplan nao tem :action-costs) e eliminacao das
    # precondicoes negativas (ele tambem nao tem :negative-preconditions)
    dom_u, prob_u = para_strips_unitario(caminho_dominio, original, destino)
    dom_c, prob_c = compilar_negativas(dom_u, prob_u, destino)

    # Controle da transformacao: o NOSSO planejador roda nas duas versoes.
    # Se o comprimento otimo mudar, a transformacao alterou o problema e a
    # comparacao com o pyperplan nao significaria nada.
    t_antes = TarefaPlanejamento(carregar_dominio(dom_u), carregar_problema(prob_u))
    antes = resolver(t_antes, "astar-hmax", limite_segundos=timeout,
                     limite_expansoes=3_000_000)
    tarefa = TarefaPlanejamento(carregar_dominio(dom_c), carregar_problema(prob_c))
    nosso = resolver(tarefa, "astar-hmax", limite_segundos=timeout,
                     limite_expansoes=3_000_000)
    transformacao_ok = (antes.sucesso == nosso.sucesso
                        and (not antes.sucesso or antes.tamanho == nosso.tamanho))

    deles = executar_pyperplan(dom_c, prob_c, timeout=timeout)

    viabilidade_bate = (nosso.sucesso == deles["sucesso"])
    comprimento_bate = None
    if nosso.sucesso and deles["sucesso"]:
        comprimento_bate = (nosso.tamanho == deles["comprimento"])

    return {
        "transformacao_preserva": transformacao_ok,
        "nosso_sucesso": nosso.sucesso,
        "nosso_comprimento": nosso.tamanho if nosso.sucesso else None,
        "nosso_acoes_instanciadas": len(tarefa.acoes),
        "deles_sucesso": deles["sucesso"],
        "deles_comprimento": deles["comprimento"],
        "deles_erro": deles["erro"],
        "viabilidade_bate": viabilidade_bate,
        "comprimento_bate": comprimento_bate,
        "arquivos": destino,
    }
