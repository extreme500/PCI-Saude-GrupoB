"""
E12: verificacao cruzada contra um planejador de referencia independente.

Era a maior ameaca a validade do trabalho e estava em aberto desde o inicio:
todos os resultados saem de um planejador escrito para este projeto, e um bug
exatamente desse tipo ja ocorreu (docs/03, "hipotese de nomes unicos").

O que torna esta verificacao significativa:

- O pyperplan e do grupo de Malte Helmert (Universidade de Basileia), o mesmo
  do Fast Downward. Tem parser, grounding e busca PROPRIOS, e nao compartilha
  uma linha de codigo com este projeto.
- As transformacoes aplicadas aos arquivos (custo unitario e eliminacao de
  precondicoes negativas) sao TEXTUAIS, e nao derivadas do modelo interno do
  nosso parser. Se o nosso parser lesse o dominio errado, o arquivo entregue
  ao pyperplan nao reproduziria esse erro.
- Cada instancia carrega um CONTROLE DA TRANSFORMACAO: o nosso planejador
  resolve a versao original e a transformada, e os comprimentos otimos tem de
  coincidir. Se nao coincidirem, a transformacao mudou o problema e a
  comparacao nao significa nada.

As instancias inviaveis sao tao importantes quanto as viaveis: concordar que
NAO existe plano exercita o grounding de forma diferente, e e exatamente onde
o bug dos nomes unicos se manifestava.
"""

from __future__ import annotations

import os

from ..dados import gerador
from ..geo import roteirizador
from ..logica import verificacao

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMINIOS = {
    "legal": os.path.join(RAIZ, "logica", "dominios", "dominio-legal.pddl"),
    "estendido": os.path.join(RAIZ, "logica", "dominios", "dominio-estendido.pddl"),
}


def _casos(tamanhos, sementes):
    """Instancias viaveis e inviaveis, para exercitar os dois vereditos."""
    for n in tamanhos:
        for s in sementes:
            yield (f"n={n} s={s}", gerador.gerar(n, s), "legal")
    # inviabilidade logica: sem curso tecnico, nenhuma acao produz (pa-ok ?p)
    d = gerador.gerar(4, 1)
    d["agente"]["curso_tecnico_concluido"] = False
    yield ("sem curso tec.", d, "legal")
    # inviabilidade de recurso: supervisoes insuficientes
    yield ("1 supervisao", gerador.gerar(4, 2, janelas_supervisao=1), "legal")
    # dominio estendido, onde o bug do grounding se manifestou
    for s in (1, 2):
        yield (f"estendido s={s}", gerador.gerar(3, s), "estendido")


def experimento_e12(tamanhos=(2, 3, 4), sementes=(1, 2, 3),
                    timeout: int = 240) -> None:
    print()
    print("=" * 78)
    print("  E12 - VERIFICACAO CRUZADA COM PLANEJADOR DE REFERENCIA (pyperplan)")
    print("=" * 78)

    if not verificacao.pyperplan_disponivel():
        print("  pyperplan nao instalado.  pip install pyperplan")
        return

    print("  Ambos resolvem a MESMA instancia, na variante de custo unitario e")
    print("  sem precondicoes negativas, e ambos em configuracao otima. A")
    print("  comparacao e sobre VIABILIDADE e COMPRIMENTO MINIMO do plano.")
    print()
    print(f"  {'instancia':<18}{'acoes':>7}{'nosso':>9}{'pyperplan':>11}"
          f"{'transf.':>9}  veredito")
    print("  " + "-" * 74)

    total = acordos = 0
    falhas_transformacao = 0
    inconclusivos = 0

    for rotulo, dados, dominio in _casos(tamanhos, sementes):
        roteamento = roteirizador.roteirizar(dados)
        r = verificacao.comparar(dados, roteamento, DOMINIOS[dominio],
                                 dominio_nome=dominio, timeout=timeout)

        nosso = str(r["nosso_comprimento"]) if r["nosso_sucesso"] else "sem plano"
        if r["deles_erro"] and not r["deles_sucesso"] and \
                "sem plano" not in r["deles_erro"]:
            deles, veredito = "ERRO", r["deles_erro"][:34]
            inconclusivos += 1
        else:
            deles = str(r["deles_comprimento"]) if r["deles_sucesso"] else "sem plano"
            total += 1
            if not r["transformacao_preserva"]:
                falhas_transformacao += 1
                veredito = "!! transformacao mudou o problema"
            elif r["viabilidade_bate"] and r["comprimento_bate"] is not False:
                acordos += 1
                veredito = "concordam"
            else:
                veredito = "!! DIVERGEM"

        transf = "ok" if r["transformacao_preserva"] else "FALHOU"
        print(f"  {rotulo:<18}{r['nosso_acoes_instanciadas']:>7}{nosso:>9}"
              f"{deles:>11}{transf:>9}  {veredito}")

    print("  " + "-" * 74)
    print(f"  comparacoes conclusivas : {total}")
    print(f"  concordancias           : {acordos}")
    print(f"  divergencias            : {total - acordos - falhas_transformacao}")
    print(f"  transformacao invalida  : {falhas_transformacao}")
    if inconclusivos:
        print(f"  inconclusivas (erro)    : {inconclusivos}")
    print()
    if total and acordos == total:
        print("  LEITURA: concordancia total. Duas implementacoes independentes,")
        print("  com parsers, groundings e buscas distintos, chegam ao mesmo")
        print("  veredito de viabilidade e ao mesmo comprimento minimo. A maior")
        print("  ameaca a validade do trabalho deixa de estar em aberto.")
    else:
        print("  LEITURA: ha divergencia. Investigar antes de usar qualquer")
        print("  numero deste projeto: o planejador proprio pode estar errado.")
