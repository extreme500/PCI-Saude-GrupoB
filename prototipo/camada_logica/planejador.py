"""
Planejador STRIPS didatico (parser PDDL + grounding + busca heuristica).

Por que um planejador proprio em vez do Fast Downward?
-------------------------------------------------------
O objetivo do protótipo e ser executavel sem nenhuma instalacao externa (o
Fast Downward exige compilacao C++ e nao roda direto no Windows). Este modulo
implementa o suficiente de PDDL para o dominio do projeto:

    :strips  :typing  :negative-preconditions  :action-costs

e duas buscas classicas, para permitir a comparacao experimental entre busca
otima e busca satisfaciente:

    - A* com h_max   -> admissivel, devolve plano de custo MINIMO
    - GBFS com h_add -> inadmissivel, rapido, plano qualquer

O modulo tambem exporta metricas (nos expandidos/gerados, tempo, custo) que
sao a materia-prima do experimento de escalabilidade.

Para validacao cruzada com um planejador consagrado, ver
`executar_fast_downward()` no fim do arquivo e docs/03-metodo-experimental.md.
"""

from __future__ import annotations

import heapq
import itertools
import re
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

# ============================================================================
#  1. LEITURA DE S-EXPRESSOES
# ============================================================================


def _tokenizar(texto: str) -> list[str]:
    """Remove comentarios PDDL (`;` ate o fim da linha) e separa os tokens."""
    texto = re.sub(r";[^\n]*", " ", texto)
    texto = texto.replace("(", " ( ").replace(")", " ) ")
    return texto.split()


def _parsear(tokens: list[str]) -> Any:
    """Converte a lista de tokens em listas aninhadas (arvore s-expression)."""
    if not tokens:
        raise SyntaxError("fim inesperado da entrada PDDL")
    token = tokens.pop(0)
    if token == "(":
        no: list[Any] = []
        while tokens and tokens[0] != ")":
            no.append(_parsear(tokens))
        if not tokens:
            raise SyntaxError("parentese '(' sem fechamento")
        tokens.pop(0)  # descarta o ')'
        return no
    if token == ")":
        raise SyntaxError("parentese ')' sem abertura")
    return token.lower()


def ler_sexp(caminho: str) -> Any:
    with open(caminho, encoding="utf-8") as arquivo:
        return _parsear(_tokenizar(arquivo.read()))


# ============================================================================
#  2. ESTRUTURAS DO DOMINIO
# ============================================================================


@dataclass
class AcaoEsquema:
    """Um (:action ...) ainda com variaveis (?ag, ?p, ...)."""

    nome: str
    parametros: list[tuple[str, str]]          # [(?ag, agente), ...]
    pre_positivas: list[tuple]                 # [(em, ?ag, ?origem), ...]
    pre_negativas: list[tuple]
    adicoes: list[tuple]
    remocoes: list[tuple]
    custo: Any = 1                             # int, ou ('func', nome, args)


@dataclass
class Dominio:
    nome: str
    tipos: dict[str, str]                      # subtipo -> supertipo
    acoes: list[AcaoEsquema] = field(default_factory=list)


@dataclass
class Problema:
    nome: str
    objetos: dict[str, str]                    # objeto -> tipo
    init: set[tuple]
    funcoes: dict[tuple, int]                  # (custo-deslocamento, a, b) -> 12
    objetivo_pos: list[tuple]
    objetivo_neg: list[tuple]


def _achatar_lista_tipada(itens: list[Any]) -> list[tuple[str, str]]:
    """Le `a b - tipo c - outro` e devolve [(a,tipo),(b,tipo),(c,outro)]."""
    resultado: list[tuple[str, str]] = []
    pendentes: list[str] = []
    i = 0
    while i < len(itens):
        if itens[i] == "-":
            tipo = itens[i + 1]
            resultado.extend((nome, tipo) for nome in pendentes)
            pendentes = []
            i += 2
        else:
            pendentes.append(itens[i])
            i += 1
    resultado.extend((nome, "object") for nome in pendentes)
    return resultado


def _coletar_literais(no: Any) -> tuple[list[tuple], list[tuple], list[tuple]]:
    """Separa uma formula `and` em (positivos, negativos, aumentos-de-custo)."""
    positivos: list[tuple] = []
    negativos: list[tuple] = []
    custos: list[tuple] = []

    def visitar(elemento: Any) -> None:
        if not elemento:
            return
        cabeca = elemento[0]
        if cabeca == "and":
            for filho in elemento[1:]:
                visitar(filho)
        elif cabeca == "not":
            negativos.append(tuple(elemento[1]))
        elif cabeca == "increase":
            custos.append(tuple(elemento[2]) if isinstance(elemento[2], list)
                          else (elemento[2],))
        else:
            positivos.append(tuple(elemento))

    visitar(no)
    return positivos, negativos, custos


def carregar_dominio(caminho: str) -> Dominio:
    arvore = ler_sexp(caminho)
    nome = "desconhecido"
    tipos: dict[str, str] = {}
    acoes: list[AcaoEsquema] = []

    for secao in arvore[1:]:
        if secao[0] == "domain":
            nome = secao[1]
        elif secao[0] == ":types":
            tipos = dict(_achatar_lista_tipada(secao[1:]))
        elif secao[0] == ":action":
            acoes.append(_carregar_acao(secao))

    return Dominio(nome=nome, tipos=tipos, acoes=acoes)


def _carregar_acao(secao: list[Any]) -> AcaoEsquema:
    nome = secao[1]
    parametros: list[tuple[str, str]] = []
    pre_pos: list[tuple] = []
    pre_neg: list[tuple] = []
    adicoes: list[tuple] = []
    remocoes: list[tuple] = []
    custo: Any = 1

    i = 2
    while i < len(secao):
        chave = secao[i]
        valor = secao[i + 1]
        if chave == ":parameters":
            parametros = _achatar_lista_tipada(valor)
        elif chave == ":precondition":
            pre_pos, pre_neg, _ = _coletar_literais(valor)
        elif chave == ":effect":
            adicoes, remocoes, custos = _coletar_literais(valor)
            if custos:
                termo = custos[0]
                # (increase (total-cost) 5)  ->  custo constante
                # (increase (total-cost) (custo-deslocamento ?a ?b)) -> funcao
                if len(termo) == 1 and str(termo[0]).lstrip("-").isdigit():
                    custo = int(termo[0])
                else:
                    custo = ("func", termo[0], termo[1:])
        i += 2

    return AcaoEsquema(nome, parametros, pre_pos, pre_neg, adicoes, remocoes,
                       custo)


def carregar_problema(caminho: str) -> Problema:
    arvore = ler_sexp(caminho)
    nome = "desconhecido"
    objetos: dict[str, str] = {}
    init: set[tuple] = set()
    funcoes: dict[tuple, int] = {}
    obj_pos: list[tuple] = []
    obj_neg: list[tuple] = []

    for secao in arvore[1:]:
        if secao[0] == "problem":
            nome = secao[1]
        elif secao[0] == ":objects":
            objetos = dict(_achatar_lista_tipada(secao[1:]))
        elif secao[0] == ":init":
            for fato in secao[1:]:
                if fato[0] == "=":                      # (= (funcao a b) 12)
                    funcoes[tuple(fato[1])] = int(fato[2])
                else:
                    init.add(tuple(fato))
        elif secao[0] == ":goal":
            obj_pos, obj_neg, _ = _coletar_literais(secao[1])

    return Problema(nome, objetos, init, funcoes, obj_pos, obj_neg)


# ============================================================================
#  3. GROUNDING (instanciacao das acoes)
# ============================================================================


@dataclass
class AcaoInstanciada:
    """Acao ja sem variaveis, com fatos representados por inteiros."""

    assinatura: str          # "mover(acs1, ubs, casa3)" - so para o relatorio
    pre_pos: frozenset[int]
    pre_neg: frozenset[int]
    adicoes: frozenset[int]
    remocoes: frozenset[int]
    custo: int


class TarefaPlanejamento:
    """Domínio + problema ja compilados para busca."""

    def __init__(self, dominio: Dominio, problema: Problema) -> None:
        self.dominio = dominio
        self.problema = problema

        self._id_por_fato: dict[tuple, int] = {}
        self._fato_por_id: list[tuple] = []

        self._indexar_tipos()
        estaticos = self._predicados_estaticos()
        self.acoes = self._instanciar_acoes(estaticos)

        self.estado_inicial = frozenset(
            self._id(f) for f in problema.init if f[0] in self._usados
        )
        self.objetivo_pos = frozenset(self._id(f) for f in problema.objetivo_pos)
        self.objetivo_neg = frozenset(self._id(f) for f in problema.objetivo_neg)

    # -- tabela de fatos -----------------------------------------------------

    def _id(self, fato: tuple) -> int:
        indice = self._id_por_fato.get(fato)
        if indice is None:
            indice = len(self._fato_por_id)
            self._id_por_fato[fato] = indice
            self._fato_por_id.append(fato)
        return indice

    def nome_do_fato(self, indice: int) -> str:
        fato = self._fato_por_id[indice]
        return f"({' '.join(fato)})"

    # -- tipos ---------------------------------------------------------------

    def _indexar_tipos(self) -> None:
        """objetos_por_tipo[t] = todos os objetos de t ou de seus subtipos."""
        self.objetos_por_tipo: dict[str, list[str]] = {}
        for objeto, tipo in self.problema.objetos.items():
            atual: str | None = tipo
            visitados = set()
            while atual and atual not in visitados:
                visitados.add(atual)
                self.objetos_por_tipo.setdefault(atual, []).append(objeto)
                atual = self.dominio.tipos.get(atual)
            self.objetos_por_tipo.setdefault("object", [])
            if objeto not in self.objetos_por_tipo["object"]:
                self.objetos_por_tipo["object"].append(objeto)

    def _predicados_estaticos(self) -> set[str]:
        """Predicados que nenhuma acao altera: podem ser testados no grounding.

        Este e o filtro que torna o grounding viavel: (proxima-parada ...),
        (residencia-de ...), (prox ...) e (desvio-ubs ...) sao todos estaticos,
        entao tuplas de parametros incompativeis com a rota sao descartadas
        antes de gerar qualquer acao.
        """
        alterados = {
            literal[0]
            for acao in self.dominio.acoes
            for literal in list(acao.adicoes) + list(acao.remocoes)
        }
        mencionados = {
            literal[0]
            for acao in self.dominio.acoes
            for literal in (list(acao.pre_positivas) + list(acao.pre_negativas)
                            + list(acao.adicoes) + list(acao.remocoes))
        }
        self._usados = mencionados
        return mencionados - alterados

    # -- instanciacao --------------------------------------------------------

    def _instanciar_acoes(self, estaticos: set[str]) -> list[AcaoInstanciada]:
        instanciadas: list[AcaoInstanciada] = []
        init = self.problema.init

        for esquema in self.dominio.acoes:
            nomes = [p for p, _ in esquema.parametros]
            dominios = [self.objetos_por_tipo.get(t, [])
                        for _, t in esquema.parametros]

            for combinacao in itertools.product(*dominios):
                if len(set(combinacao)) != len(combinacao):
                    continue  # assume-se hipotese de nomes unicos
                ligacao = dict(zip(nomes, combinacao))

                pre_pos = [self._aplicar(lit, ligacao) for lit in esquema.pre_positivas]
                # poda: precondicao estatica que nao vale no init mata a acao
                if any(f[0] in estaticos and f not in init for f in pre_pos):
                    continue
                pre_neg = [self._aplicar(lit, ligacao) for lit in esquema.pre_negativas]
                if any(f[0] in estaticos and f in init for f in pre_neg):
                    continue

                adicoes = [self._aplicar(l, ligacao) for l in esquema.adicoes]
                remocoes = [self._aplicar(l, ligacao) for l in esquema.remocoes]

                custo = self._resolver_custo(esquema.custo, ligacao)
                if custo is None:
                    continue  # funcao de custo sem valor definido no problema

                # precondicoes estaticas ja verificadas saem do teste da busca
                pre_pos_din = frozenset(self._id(f) for f in pre_pos
                                        if f[0] not in estaticos)
                pre_neg_din = frozenset(self._id(f) for f in pre_neg
                                        if f[0] not in estaticos)

                assinatura = f"{esquema.nome}({', '.join(combinacao)})"
                instanciadas.append(AcaoInstanciada(
                    assinatura,
                    pre_pos_din,
                    pre_neg_din,
                    frozenset(self._id(f) for f in adicoes),
                    frozenset(self._id(f) for f in remocoes),
                    custo,
                ))

        return instanciadas

    @staticmethod
    def _aplicar(literal: tuple, ligacao: dict[str, str]) -> tuple:
        return tuple(ligacao.get(termo, termo) for termo in literal)

    def _resolver_custo(self, custo: Any, ligacao: dict[str, str]) -> int | None:
        if isinstance(custo, int):
            return custo
        _, nome_funcao, argumentos = custo
        chave = (nome_funcao,) + tuple(ligacao.get(a, a) for a in argumentos)
        return self.problema.funcoes.get(chave)

    # -- interface de busca --------------------------------------------------

    def aplicaveis(self, estado: frozenset[int]):
        for acao in self.acoes:
            if acao.pre_pos <= estado and not (acao.pre_neg & estado):
                yield acao

    def e_objetivo(self, estado: frozenset[int]) -> bool:
        return (self.objetivo_pos <= estado
                and not (self.objetivo_neg & estado))


# ============================================================================
#  4. HEURISTICAS (grafo de planejamento relaxado - ignora as remocoes)
# ============================================================================


def _custos_relaxados(tarefa: TarefaPlanejamento, estado: frozenset[int],
                      combinar) -> dict[int, float]:
    """Propaga custos no problema relaxado (sem efeitos de remocao).

    `combinar=max` produz h_max (admissivel); `combinar=sum` produz h_add.
    """
    custo: dict[int, float] = {f: 0.0 for f in estado}
    faltando = {id(a): len(a.pre_pos) for a in tarefa.acoes}
    fila: list[tuple[float, int]] = [(0.0, f) for f in estado]
    heapq.heapify(fila)

    # indice fato -> acoes que o exigem
    if not hasattr(tarefa, "_consumidores"):
        consumidores: dict[int, list] = {}
        for acao in tarefa.acoes:
            for fato in acao.pre_pos:
                consumidores.setdefault(fato, []).append(acao)
        tarefa._consumidores = consumidores  # cache entre chamadas
    consumidores = tarefa._consumidores

    sem_precondicao = [a for a in tarefa.acoes if not a.pre_pos]
    for acao in sem_precondicao:
        for fato in acao.adicoes:
            if acao.custo < custo.get(fato, float("inf")):
                custo[fato] = float(acao.custo)
                heapq.heappush(fila, (float(acao.custo), fato))

    while fila:
        valor, fato = heapq.heappop(fila)
        if valor > custo.get(fato, float("inf")):
            continue
        for acao in consumidores.get(fato, ()):
            faltando[id(acao)] -= 1
            if faltando[id(acao)] > 0:
                continue
            base = combinar((custo.get(p, float("inf")) for p in acao.pre_pos),
                            default=0.0)
            if base == float("inf"):
                continue
            novo = base + acao.custo
            for adicionado in acao.adicoes:
                if novo < custo.get(adicionado, float("inf")):
                    custo[adicionado] = novo
                    heapq.heappush(fila, (novo, adicionado))

    return custo


def _soma(iteravel, default=0.0):
    valores = list(iteravel)
    return sum(valores) if valores else default


def heuristica(tarefa: TarefaPlanejamento, estado: frozenset[int],
               modo: str) -> float:
    """h_max (admissivel) ou h_add (informativa, porem inadmissivel)."""
    combinar = max if modo == "hmax" else _soma
    custo = _custos_relaxados(tarefa, estado, combinar)
    alvos = [custo.get(f, float("inf")) for f in tarefa.objetivo_pos]
    if any(v == float("inf") for v in alvos):
        return float("inf")      # objetivo inalcancavel na relaxacao -> poda
    return max(alvos, default=0.0) if modo == "hmax" else sum(alvos)


# ============================================================================
#  5. BUSCA
# ============================================================================


@dataclass
class Resultado:
    sucesso: bool
    plano: list[str]
    custo: int
    expandidos: int
    gerados: int
    segundos: float
    motivo: str = ""

    @property
    def tamanho(self) -> int:
        return len(self.plano)


ESTRATEGIAS = {
    # nome          (modo heuristico, usa g no ranking, garante otimo)
    "astar-hmax":   ("hmax", True,  True),
    "astar-hadd":   ("hadd", True,  False),
    "gbfs":         ("hadd", False, False),
}


def resolver(tarefa: TarefaPlanejamento, estrategia: str = "astar-hadd",
             limite_expansoes: int = 400_000,
             limite_segundos: float = 60.0) -> Resultado:
    """Busca no espaco de estados.

    "astar-hmax" -> A* com h_max. h_max e admissivel, logo o plano devolvido
                    tem custo MINIMO. E a unica estrategia com garantia de
                    otimalidade, e a que menos escala.
    "astar-hadd" -> A* com h_add. h_add soma o custo relaxado dos subobjetivos
                    e e muito mais informativo, mas superestima: o plano e
                    tipicamente otimo ou quase, SEM garantia formal.
    "gbfs"       -> best-first guloso (ignora g). O mais rapido e o de pior
                    qualidade de plano.
    """
    inicio = time.perf_counter()
    if estrategia not in ESTRATEGIAS:
        raise ValueError(f"estrategia desconhecida: {estrategia}")
    modo_h, usa_g, _otimo = ESTRATEGIAS[estrategia]

    h_inicial = heuristica(tarefa, tarefa.estado_inicial, modo_h)
    if h_inicial == float("inf"):
        return Resultado(False, [], 0, 0, 0,
                         time.perf_counter() - inicio,
                         "objetivo inalcancavel (deteccao na relaxacao)")

    contador = itertools.count()
    fronteira = [(h_inicial, next(contador), tarefa.estado_inicial, 0, [])]
    melhor_g = {tarefa.estado_inicial: 0}
    expandidos = gerados = 0

    while fronteira:
        if expandidos >= limite_expansoes:
            return Resultado(False, [], 0, expandidos, gerados,
                             time.perf_counter() - inicio,
                             f"limite de {limite_expansoes} expansoes atingido")
        if time.perf_counter() - inicio > limite_segundos:
            return Resultado(False, [], 0, expandidos, gerados,
                             time.perf_counter() - inicio,
                             f"timeout de {limite_segundos:.0f}s")

        _, _, estado, g, plano = heapq.heappop(fronteira)
        if g > melhor_g.get(estado, float("inf")):
            continue
        if tarefa.e_objetivo(estado):
            return Resultado(True, plano, g, expandidos, gerados,
                             time.perf_counter() - inicio)

        expandidos += 1
        for acao in tarefa.aplicaveis(estado):
            sucessor = (estado - acao.remocoes) | acao.adicoes
            novo_g = g + acao.custo
            if novo_g >= melhor_g.get(sucessor, float("inf")):
                continue
            h = heuristica(tarefa, sucessor, modo_h)
            if h == float("inf"):
                continue
            melhor_g[sucessor] = novo_g
            gerados += 1
            f = (novo_g + h) if usa_g else h
            heapq.heappush(fronteira, (f, next(contador), sucessor, novo_g,
                                       plano + [acao.assinatura]))

    return Resultado(False, [], 0, expandidos, gerados,
                     time.perf_counter() - inicio,
                     "espaco de estados exaurido: problema sem solucao")


def planejar(caminho_dominio: str, caminho_problema: str,
             estrategia: str = "astar", **limites) -> tuple[Resultado, TarefaPlanejamento]:
    """Atalho: carrega, instancia e resolve."""
    tarefa = TarefaPlanejamento(carregar_dominio(caminho_dominio),
                                carregar_problema(caminho_problema))
    return resolver(tarefa, estrategia, **limites), tarefa


# ============================================================================
#  6. VALIDACAO CRUZADA COM PLANEJADOR EXTERNO (opcional)
# ============================================================================


def executar_fast_downward(binario: str, caminho_dominio: str,
                           caminho_problema: str,
                           busca: str = "astar(lmcut())") -> str:
    """Roda o Fast Downward, se disponivel, sobre os MESMOS arquivos .pddl.

    Serve para comprovar que o dominio nao depende do planejador caseiro.
    Uso:  python -c "from planejador import *;
                     print(executar_fast_downward('/caminho/fast-downward.py',
                           'dominio.pddl','problema.pddl'))"
    """
    saida = subprocess.run(
        [binario, caminho_dominio, caminho_problema, "--search", busca],
        capture_output=True, text=True, timeout=300,
    )
    return saida.stdout
