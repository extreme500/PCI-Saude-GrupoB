"""
E13: a realimentacao do passo 3 para o passo 2 funciona?

O que se mede
-------------
Quando o planejamento reprova uma rota, a camada geometrica e chamada de
novo. Tres perguntas:

  1. o laco converge, isto e, chega a uma rota valida?
  2. em quantas tentativas?
  3. quanto custa a conformidade, em minutos de caminhada, comparando a
     rota aceita com a primeira rota reprovada?

Como a falha e forcada
----------------------
Nao ha truque: liga-se `roteador_ciente=False`, e entao a camada geometrica
passa a ignorar a precedencia por urgencia, exatamente como faria um
roteirizador de prateleira que minimiza distancia e nao conhece a norma. A
camada normativa continua exigindo a precedencia, reprova o que a viola e
pede outra rota.

Isso NAO e um cenario artificial: e a situacao de quem troca a camada 2 por
OR-Tools, por um servico de rotas ou por uma planilha.

O grupo de controle
-------------------
A mesma varredura com o roteirizador CIENTE da precedencia. Se nele a
primeira rota quase nunca for reprovada, o resultado e duplamente
informativo: diz que a arquitetura "roteiriza e depois verifica" e robusta,
e que o laco e seguro, nao cavalo de batalha.
"""

from __future__ import annotations

import statistics

from ..dados import gerador
from ..logica import realimentacao
from ..selecao import politica


def _varrer(ciente: bool, tamanhos, sementes, limite):
    from . import rodar

    primeira_reprovada = 0
    convergiu = 0
    esgotou = 0
    estruturais = 0
    total = 0
    tentativas_ate_valida: list[int] = []
    delta_caminhada: list[int] = []

    for n in tamanhos:
        for semente in sementes:
            dados = gerador.gerar(n, semente)
            if n >= 12:
                dados = politica.selecionar(dados, orcamento_minutos=240)
            if realimentacao.diagnosticar(dados)[0]:
                estruturais += 1
                continue
            total += 1
            r = realimentacao.planejar_com_realimentacao(
                dados, rodar.DOMINIOS["legal"], max_tentativas=6,
                limite=limite, roteador_ciente=ciente)
            if not r.tentativas:
                continue
            if not r.tentativas[0].sucesso:
                primeira_reprovada += 1
            if r.sucesso:
                convergiu += 1
                if not r.tentativas[0].sucesso:
                    # so interessa contar tentativas de quem precisou de
                    # mais de uma: incluir quem acertou de primeira puxaria
                    # a mediana para 1 e esconderia o custo do laco.
                    tentativas_ate_valida.append(len(r.tentativas))
                    delta_caminhada.append(
                        r.tentativas[-1].custo_rota - r.tentativas[0].custo_rota)
            else:
                esgotou += 1

    return {
        "total": total, "estruturais": estruturais,
        "primeira_reprovada": primeira_reprovada,
        "convergiu": convergiu, "esgotou": esgotou,
        "tentativas": tentativas_ate_valida, "delta": delta_caminhada,
    }


def experimento_e13(tamanhos=(7, 8, 12), sementes=range(1, 16),
                    limite_segundos: float = 30.0) -> None:
    from . import rodar

    rodar.regua("E13 - REALIMENTACAO: O PASSO 3 REPROVA, O PASSO 2 TENTA DE NOVO")
    print("  A falha da primeira rota e forcada do jeito realista: o")
    print("  roteirizador ignora a precedencia clinica (como faria um")
    print("  roteirizador de prateleira) e a camada normativa cobra.")
    print()

    sementes = list(sementes)
    cego = _varrer(False, tamanhos, sementes, limite_segundos)
    ciente = _varrer(True, tamanhos, sementes, limite_segundos)

    def linha(rotulo: str, d: dict) -> None:
        total = d["total"] or 1
        pct = 100 * d["primeira_reprovada"] / total
        print(f"  {rotulo:<34}{d['primeira_reprovada']:>3}/{d['total']:<3} "
              f"({pct:>4.0f}%){d['convergiu']:>9}/{d['total']:<3}"
              f"{d['esgotou']:>10}")

    print(f"  {'':<34}{'1a rota reprovada':>16}{'converge':>12}{'esgotou':>10}")
    print("  " + "-" * 74)
    linha("roteirizador CEGO a norma", cego)
    linha("roteirizador CIENTE da norma", ciente)
    print()

    if cego["tentativas"]:
        n = len(cego["tentativas"])
        print(f"  Das {n} instancias em que a 1a rota foi reprovada, todas as que")
        print(f"  convergiram precisaram de mediana {statistics.median(cego['tentativas']):.0f} "
              f"tentativas, maxima {max(cego['tentativas'])}.")
    if cego["delta"]:
        media = statistics.mean(cego["delta"])
        print()
        print(f"  CUSTO DA CONFORMIDADE (rota aceita menos rota reprovada):")
        print(f"    media {media:+.1f} min de caminhada, "
              f"minimo {min(cego['delta']):+d}, maximo {max(cego['delta']):+d}")
        if max(cego["delta"]) == 0 and min(cego["delta"]) == 0:
            print("    ou seja, ZERO: a rota que cumpre a norma custa o mesmo")
            print("    numero de minutos. O que muda e a ORDEM, nao a distancia.")
    if cego["estruturais"] or ciente["estruturais"]:
        print(f"  instancias com inviabilidade estrutural, descartadas: "
              f"{cego['estruturais']}")
    print()
    print("  LEITURA: a linha do roteirizador ciente e o resultado que importa.")
    print("  Se nela a primeira rota quase nunca e reprovada, a arquitetura")
    print("  'roteiriza e depois verifica' se sustenta, e o laco e seguranca")
    print("  para quando a camada 2 for trocada por algo que nao conhece a lei.")
