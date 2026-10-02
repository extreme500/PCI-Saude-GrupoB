"""
Testes de fumaca e de regressao.

    python -m acsplan.testes

Nao pretendem cobertura. Cada teste aqui existe porque a ausencia dele deixou
passar, ou deixaria passar, um erro concreto. Os tres ultimos correspondem
diretamente a bugs que ocorreram durante o desenvolvimento e que estao
registrados em docs/03-metodo-experimental.md.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import traceback

from .dados import gerador, modelos
from .geo import distancias, genetico, roteirizador
from .logica import executor_guloso
from .logica.gerador_problema import gerar_problema
from .logica.planejador import (TarefaPlanejamento, carregar_dominio,
                                carregar_problema, resolver)
from .selecao import politica

RAIZ = os.path.dirname(os.path.abspath(__file__))
DOMINIOS = {
    "legal": os.path.join(RAIZ, "logica", "dominios", "dominio-legal.pddl"),
    "estendido": os.path.join(RAIZ, "logica", "dominios", "dominio-estendido.pddl"),
}
TMP = tempfile.mkdtemp(prefix="acsplan-testes-")

_resultados: list[tuple[str, bool, str]] = []


def teste(nome):
    def decorador(funcao):
        try:
            funcao()
            _resultados.append((nome, True, ""))
        except Exception:
            _resultados.append((nome, False, traceback.format_exc(limit=2)))
        return funcao
    return decorador


def _tarefa(dados, dominio="legal", **kw):
    roteamento = roteirizador.roteirizar(dados, **kw)
    caminho = os.path.join(TMP, f"p-{dominio}-{len(dados['pacientes'])}.pddl")
    gerar_problema(dados, roteamento, caminho, dominio=dominio)
    tarefa = TarefaPlanejamento(carregar_dominio(DOMINIOS[dominio]),
                                carregar_problema(caminho))
    return roteamento, tarefa


# ---------------------------------------------------------------------------

@teste("os dois dominios sao PDDL valido e instanciam acoes")
def _():
    dados = gerador.gerar(3, 1)
    for dominio in ("legal", "estendido"):
        _, tarefa = _tarefa(dados, dominio)
        assert len(tarefa.acoes) > 0, dominio
    # o estendido tem de ser estritamente maior que o legal
    _, legal = _tarefa(dados, "legal")
    _, estendido = _tarefa(dados, "estendido")
    assert len(estendido.acoes) > len(legal.acoes)


@teste("os cinco incisos do art. 3o par. 4o estao no dominio legal")
def _():
    dominio = carregar_dominio(DOMINIOS["legal"])
    nomes = {a.nome for a in dominio.acoes}
    for acao in ("aferir-pressao-arterial", "medir-glicemia-capilar",
                 "aferir-temperatura-axilar", "orientar-administracao-medicacao",
                 "verificacao-antropometrica"):
        assert acao in nomes, acao


@teste("inciso III nao impoe encaminhamento; incisos I e II impoem")
def _():
    # A lei condiciona o encaminhamento do inciso III a "quando necessario".
    dominio = carregar_dominio(DOMINIOS["legal"])
    por_nome = {a.nome: a for a in dominio.acoes}

    def gera_pendencia(nome):
        return any(lit[0] == "pendencia-encaminhamento"
                   for lit in por_nome[nome].adicoes)

    assert gera_pendencia("aferir-pressao-arterial")
    assert gera_pendencia("medir-glicemia-capilar")
    assert not gera_pendencia("aferir-temperatura-axilar")


@teste("REGRESSAO: glicemia estendida tem instancias validas (nomes unicos)")
def _():
    # O grounding descartava combinacoes com objetos repetidos. Como a acao
    # consome uma fita E ocupa espaco no coletor, a combinacao legitima
    # (n2, n1, n3, n2) sumia e o planejador 'provava' inviabilidade.
    dados = gerador.gerar(3, 1)
    _, tarefa = _tarefa(dados, "estendido")
    instancias = [a for a in tarefa.acoes
                  if a.assinatura.startswith("medir-glicemia-capilar")]
    assert instancias, "medir-glicemia-capilar ficou sem instancia valida"


@teste("REGRESSAO: planejador e executor usam a mesma tabela de custos")
def _():
    # A diferenca de custo entre os dois planos tem de ser explicada pela
    # diferenca de contagem de acoes. Foi essa conferencia que revelou que
    # retornar-a-rota era cobrada de formas diferentes nos dois lados.
    #
    # ATENCAO: a primeira versao deste teste usava UMA instancia e saia calado
    # quando ela era inviavel. Com a semente que estava fixada, o executor
    # falhava e o teste passava sem verificar coisa alguma. Agora varre varias
    # sementes e EXIGE um minimo de casos efetivamente exercitados.
    from collections import Counter
    exercitados = 0
    for semente in range(1, 13):
        dados = gerador.gerar(6, semente)
        roteamento, tarefa = _tarefa(dados)
        otimo = resolver(tarefa, "astar-hmax", limite_segundos=30)
        guloso = executor_guloso.executar(dados, roteamento, DOMINIOS["legal"])
        if not (otimo.sucesso and guloso.sucesso):
            continue
        exercitados += 1
        custos = {a.assinatura.split("(")[0]: a.custo for a in tarefa.acoes}
        a = Counter(x.split("(")[0] for x in otimo.plano)
        b = Counter(x.split("(")[0] for x in guloso.plano)
        previsto = sum(custos.get(t, 0) * (b[t] - a[t]) for t in set(a) | set(b)
                       if t not in ("mover", "desviar-para-ubs"))
        observado = guloso.custo - otimo.custo
        assert abs(previsto - observado) <= 2, (semente, previsto, observado)
    assert exercitados >= 5, f"so {exercitados} instancias exercitaram a asercao"


@teste("o plano otimo nunca perde para o executor procedural")
def _():
    # Se isto falhar, h_max nao e admissivel e a garantia de otimalidade caiu.
    # Tambem exige minimo de casos exercitados, pelo mesmo motivo acima.
    exercitados = 0
    for semente in range(1, 13):
        dados = gerador.gerar(6, semente)
        roteamento, tarefa = _tarefa(dados)
        otimo = resolver(tarefa, "astar-hmax", limite_segundos=30)
        guloso = executor_guloso.executar(dados, roteamento, DOMINIOS["legal"])
        if otimo.sucesso and guloso.sucesso:
            exercitados += 1
            assert otimo.custo <= guloso.custo, (semente, otimo.custo, guloso.custo)
    assert exercitados >= 5, f"so {exercitados} instancias exercitaram a asercao"


@teste("inviabilidade logica e provada sem expandir nenhum no")
def _():
    dados = gerador.gerar(6, 1)
    dados["agente"]["curso_tecnico_concluido"] = False
    _, tarefa = _tarefa(dados)
    r = resolver(tarefa, "astar-hmax", limite_segundos=20)
    assert not r.sucesso and r.expandidos == 0, (r.sucesso, r.expandidos)


@teste("o reparo de precedencia produz ordem sempre valida")
def _():
    precede = {"c": {"a", "b"}, "d": {"a"}}
    for entrada in (["d", "c", "b", "a"], ["c", "a", "d", "b"], ["a", "b", "c", "d"]):
        saida = genetico.reparar_precedencia(entrada, precede)
        assert sorted(saida) == sorted(entrada)
        vistos = set()
        for item in saida:
            assert not (precede.get(item, set()) - vistos), (entrada, saida)
            vistos.add(item)


@teste("a rota respeita a precedencia nos dois metodos de roteamento")
def _():
    dados = gerador.gerar(10, 7)
    for metodo in ("nn2opt", "ag"):
        r = roteirizador.roteirizar(dados, metodo=metodo)
        precede = r["precedencias"]
        vistos = set()
        for parada in r["rota"][1:-1]:
            assert not (precede.get(parada, set()) - vistos), (metodo, parada)
            vistos.add(parada)


@teste("a politica de selecao respeita o orcamento e nunca adia um inadiavel")
def _():
    dados = gerador.gerar(14, 2)
    saida = politica.selecionar(dados, orcamento_minutos=200)
    sel = saida["_selecao"]
    inadiaveis = {p["id"] for p in dados["pacientes"]
                  if modelos.atraso_em_dias(p) >= politica.ATRASO_INADIAVEL_DIAS}
    assert inadiaveis <= set(sel["selecionados"])
    assert len(saida["pacientes"]) < len(dados["pacientes"])
    # sem orcamento nem limite, a microarea inteira entra
    completo = politica.selecionar(dados)
    assert len(completo["pacientes"]) == len(dados["pacientes"])


@teste("a matriz do OSRM e convertida e o fallback e reportado")
def _():
    pontos = [{"id": "ubs", "lat": -30.0397, "lon": -51.2189},
              {"id": "p1", "lat": -30.0362, "lon": -51.2141},
              {"id": "p2", "lat": -30.0341, "lon": -51.2203}]
    original = distancias.consultar_osrm
    try:
        distancias.consultar_osrm = lambda p: [[0, 540, 900], [560, 0, 700],
                                               [880, 690, 0]]
        m = distancias.matriz_osrm(pontos)
        assert m[("ubs", "p1")] == 9 and m[("ubs", "ubs")] == 0, m

        # um ponto inalcancavel invalida a matriz inteira
        distancias.consultar_osrm = lambda p: [[0, None, 900], [560, 0, 700],
                                               [880, 690, 0]]
        assert distancias.matriz_osrm(pontos) is None

        # e o provedor efetivamente usado precisa ser reportado
        _, provedor = distancias.construir_matriz(pontos, "osrm")
        assert provedor.startswith("haversine"), provedor
    finally:
        distancias.consultar_osrm = original
        shutil.rmtree(distancias.DIRETORIO_CACHE, ignore_errors=True)


@teste("planejador de referencia concorda (pyperplan), se instalado")
def _():
    from .logica import verificacao
    if not verificacao.pyperplan_disponivel():
        return   # ambiente sem a dependencia opcional
    for semente in (1, 2):
        dados = gerador.gerar(3, semente)
        roteamento = roteirizador.roteirizar(dados)
        r = verificacao.comparar(dados, roteamento, DOMINIOS["legal"],
                                 timeout=240)
        assert r["transformacao_preserva"], semente
        if r["deles_erro"] and not r["deles_sucesso"]:
            continue   # erro do lado deles: inconclusivo, nao e divergencia
        assert r["viabilidade_bate"], (semente, r)
        assert r["comprimento_bate"] is not False, (semente, r)


@teste("o arquivo de exemplo carrega e planeja")
def _():
    with open(os.path.join(RAIZ, "dados", "microarea_exemplo.json"),
              encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    dados = politica.selecionar(dados, maximo_pacientes=5)
    _, tarefa = _tarefa(dados)
    r = resolver(tarefa, "astar-hmax", limite_segundos=40)
    assert r.sucesso, r.motivo


# ---------------------------------------------------------------------------

def main() -> int:
    print()
    falhas = 0
    for nome, ok, detalhe in _resultados:
        print(f"  {'ok  ' if ok else 'FALHA'}  {nome}")
        if not ok:
            falhas += 1
            print("         " + detalhe.replace("\n", "\n         ").rstrip())
    print()
    print(f"  {len(_resultados) - falhas} de {len(_resultados)} testes passaram.")
    print()
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
