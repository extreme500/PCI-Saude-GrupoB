"""
Compilacao de precondicoes negativas para STRIPS estrito.

O planejador de referencia usado na verificacao cruzada (pyperplan) nao
aceita `:negative-preconditions`. A saida e a transformacao classica por
PREDICADOS COMPLEMENTARES: para cada predicado P usado negativamente,
cria-se `nao-P`, inicializado em todas as instancias ground que NAO constam
do estado inicial, e mantido em paridade com P por todas as acoes que o
alteram.

A transformacao preserva o problema exatamente: o conjunto de planos validos
e o mesmo, porque `(not (P x))` e `(nao-P x)` sao verdadeiros nos mesmos
estados por construcao.

POR QUE ELA E FEITA TEXTUALMENTE
--------------------------------
Seria mais simples gerar os arquivos a partir do modelo interno do nosso
parser. Seria tambem inutil: se o parser lesse o dominio errado, o arquivo
transformado reproduziria o mesmo erro, o pyperplan concordaria com ele, e a
verificacao nao estaria verificando nada.

Trabalhando sobre o texto, o unico que o pyperplan recebe sao os arquivos
`.pddl`, e ele os interpreta com parser e grounding proprios.
"""

from __future__ import annotations

import itertools
import os
import re


def extrair_bloco(texto: str, marcador: str, inicio: int = 0) -> tuple[int, int]:
    """Posicao (abre, fecha) da s-expressao que segue `marcador`."""
    i = texto.find(marcador, inicio)
    if i < 0:
        return -1, -1
    # Se o proprio marcador abre a s-expressao (caso de "(:predicates"), o
    # parentese a varrer e o DELE. Procurar o proximo "(" devolveria apenas
    # a primeira declaracao interna, e nao o bloco inteiro.
    j = i if marcador.startswith("(") else texto.find("(", i + len(marcador))
    if j < 0:
        return -1, -1
    profundidade, k = 0, j
    while k < len(texto):
        if texto[k] == "(":
            profundidade += 1
        elif texto[k] == ")":
            profundidade -= 1
            if profundidade == 0:
                return j, k + 1
        k += 1
    return -1, -1


def _expandir_tipos(tokens: list[str]) -> list[str]:
    """Le `?a ?b - t ?c - u` e devolve [t, t, u]."""
    tipos: list[str] = []
    pendentes = 0
    i = 0
    while i < len(tokens):
        if tokens[i] == "-":
            tipos.extend([tokens[i + 1]] * pendentes)
            pendentes = 0
            i += 2
        else:
            if tokens[i].startswith("?"):
                pendentes += 1
            i += 1
    tipos.extend(["object"] * pendentes)
    return tipos


def declaracoes_de_predicados(dominio: str) -> dict[str, list[str]]:
    """{nome: [tipos dos parametros]}, lido do bloco (:predicates ...)."""
    a, b = extrair_bloco(dominio, "(:predicates")
    if a < 0:
        return {}
    bloco = re.sub(r";[^\n]*", "", dominio[a:b])
    decls: dict[str, list[str]] = {}
    for corpo in re.findall(r"\(([^()]+)\)", bloco):
        partes = corpo.split()
        if partes:
            decls[partes[0]] = _expandir_tipos(partes[1:])
    return decls


def objetos_por_tipo(problema: str) -> dict[str, list[str]]:
    a, b = extrair_bloco(problema, "(:objects")
    if a < 0:
        return {}
    tokens = re.sub(r";[^\n]*", "", problema[a + 1:b - 1]).split()
    # extrair_bloco devolve o bloco INCLUINDO o marcador, entao o primeiro
    # token e ":objects" e precisa sair, sob pena de virar nome de objeto.
    if tokens and tokens[0].startswith(":"):
        tokens = tokens[1:]
    mapa: dict[str, list[str]] = {}
    pendentes: list[str] = []
    i = 0
    while i < len(tokens):
        if tokens[i] == "-":
            mapa.setdefault(tokens[i + 1], []).extend(pendentes)
            pendentes = []
            i += 2
        else:
            pendentes.append(tokens[i])
            i += 1
    return mapa


def _predicados_negados(dominio: str, conhecidos: set[str]) -> set[str]:
    negados: set[str] = set()
    pos = 0
    while True:
        a, b = extrair_bloco(dominio, ":precondition", pos)
        if a < 0:
            return negados
        for nome in re.findall(r"\(not\s+\(([^\s()]+)", dominio[a:b]):
            if nome in conhecidos:
                negados.add(nome)
        pos = b


def _trocar_precondicoes(texto: str, negados: set[str]) -> str:
    saida: list[str] = []
    pos = 0
    while True:
        a, b = extrair_bloco(texto, ":precondition", pos)
        if a < 0:
            saida.append(texto[pos:])
            return "".join(saida)
        saida.append(texto[pos:a])
        bloco = texto[a:b]
        for nome in negados:
            padrao = r"\(not\s+\(" + re.escape(nome) + r"((?:\s+[^()]*?)?)\)\s*\)"
            bloco = re.sub(padrao, lambda m: "(nao-" + nome + m.group(1) + ")", bloco)
        saida.append(bloco)
        pos = b


def _ajustar_efeitos(texto: str, negados: set[str]) -> str:
    saida: list[str] = []
    pos = 0
    while True:
        a, b = extrair_bloco(texto, ":effect", pos)
        if a < 0:
            saida.append(texto[pos:])
            return "".join(saida)
        saida.append(texto[pos:a])
        bloco = texto[a:b]
        adicionais: list[str] = []
        for nome in negados:
            esc = re.escape(nome)
            # P deixa de valer  ->  nao-P passa a valer
            for args in re.findall(r"\(not\s+\(" + esc + r"((?:\s+[^()]*?)?)\)\s*\)", bloco):
                adicionais.append("(nao-" + nome + args + ")")
            # P passa a valer  ->  nao-P deixa de valer
            for m in re.finditer(r"\(" + esc + r"((?:\s+[^()]*?)?)\)", bloco):
                anterior = bloco[max(0, m.start() - 6):m.start()]
                if "not" in anterior:
                    continue
                adicionais.append("(not (nao-" + nome + m.group(1) + "))")
        if adicionais:
            unicos = list(dict.fromkeys(adicionais))
            bloco = bloco.rstrip()
            bloco = bloco[:-1].rstrip() + "\n                 " + \
                "\n                 ".join(unicos) + ")"
        saida.append(bloco)
        pos = b


def compilar_negativas(caminho_dominio: str, caminho_problema: str,
                       destino: str) -> tuple[str, str]:
    """Gera dominio e problema equivalentes, sem precondicoes negativas."""
    dominio = open(caminho_dominio, encoding="utf-8").read()
    problema = open(caminho_problema, encoding="utf-8").read()

    decls = declaracoes_de_predicados(dominio)
    negados = _predicados_negados(dominio, set(decls))
    if not negados:
        return caminho_dominio, caminho_problema

    # declarar os complementares
    _, pb = extrair_bloco(dominio, "(:predicates")
    extras = []
    for nome in sorted(negados):
        params = " ".join(f"?x{i} - {t}" for i, t in enumerate(decls[nome]))
        extras.append(f"    (nao-{nome} {params})".rstrip())
    dominio = (dominio[:pb - 1]
               + "\n    ;; complementares gerados para o planejador de\n"
                 "    ;; referencia, que nao aceita :negative-preconditions\n"
               + "\n".join(extras) + "\n  " + dominio[pb - 1:])

    dominio = _trocar_precondicoes(dominio, negados)
    dominio = _ajustar_efeitos(dominio, negados)
    dominio = dominio.replace(" :negative-preconditions", "")

    # estado inicial: nao-P para toda instancia ground ausente
    objetos = objetos_por_tipo(problema)
    ia, ib = extrair_bloco(problema, "(:init")
    init_txt = re.sub(r";[^\n]*", "", problema[ia:ib])
    presentes = set()
    for nome in negados:
        esc = re.escape(nome)
        for args in re.findall(r"\(" + esc + r"((?:\s+[^()]*?)?)\)", init_txt):
            presentes.add((nome, tuple(args.split())))

    novos: list[str] = []
    for nome in sorted(negados):
        dominios = [objetos.get(t, []) for t in decls[nome]]
        if any(not d for d in dominios):
            continue
        for combo in itertools.product(*dominios):
            if (nome, combo) not in presentes:
                novos.append(f"    (nao-{nome} {' '.join(combo)})")

    problema = (problema[:ib - 1] + "\n    ;; complementares gerados\n"
                + "\n".join(novos) + "\n  " + problema[ib - 1:])

    os.makedirs(destino, exist_ok=True)
    saida_d = os.path.join(destino, "dominio-compilado.pddl")
    saida_p = os.path.join(destino, "problema-compilado.pddl")
    open(saida_d, "w", encoding="utf-8").write(dominio)
    open(saida_p, "w", encoding="utf-8").write(problema)
    return saida_d, saida_p
