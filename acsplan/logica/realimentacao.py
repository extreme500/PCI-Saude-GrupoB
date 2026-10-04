"""
Realimentacao do passo 3 para o passo 2.

Por que este modulo existe
--------------------------
Ate aqui o pipeline era de mao unica: a camada geometrica entregava UMA rota
e a camada logica dizia se ela era exequivel. Quando a resposta era "nao
existe plano", o turno simplesmente nao saia, embora muitas vezes OUTRA
ordem das mesmas paradas fosse perfeitamente exequivel.

Agora, quando o planejamento prova que a rota corrente e inexequivel, o
pipeline volta ao passo 2, pede uma rota diferente e tenta de novo.

O ponto delicado: nem toda inviabilidade se resolve trocando a rota
----------------------------------------------------------------------
Insistir em rotas novas diante de uma inviabilidade estrutural seria gastar
busca para reprovar o mesmo turno N vezes. Ha duas causas que nenhuma ordem
de visitas resolve:

  1. o ACS nao cumpre as condicoes do art. 3o par. 4o (sem curso tecnico ou
     sem equipamento) e ha paciente que exige procedimento condicionado;
  2. as janelas de supervisao do turno sao menos numerosas que os pacientes
     que exigem procedimento do par. 4o. Como a supervisao se encerra ao
     deixar a residencia e nao se repoe na unidade, cada uma dessas visitas
     consome ao menos uma janela, qualquer que seja a ordem.

Fora dessas duas, a inviabilidade E sensivel a ordem. O caso tipico e o que
o experimento E2 mediu: quando o insumo acaba no meio de uma visita, o
desvio ate a unidade encerra a assistencia ja mobilizada e consome uma
janela de supervisao a mais. Uma ordem que agrupe os pacientes de glicemia
de modo que a reposicao caia ENTRE visitas, e nao no meio de uma, pode ser
exequivel onde a anterior nao era.

Por isso o modulo diagnostica antes de reiterar.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from ..dados import modelos
from ..geo import roteirizador
from ..geo.distancias import construir_matriz
from .gerador_problema import gerar_problema
from .planejador import (TarefaPlanejamento, carregar_dominio,
                         carregar_problema, resolver)

PROCEDIMENTOS_PARAGRAFO_4 = ("requer_pa", "requer_glicemia", "requer_temperatura",
                             "requer_antropometria", "requer_orientacao_medicacao")

CAMINHO_PROBLEMA_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "problema_gerado.pddl")


@dataclass
class Tentativa:
    variante: int
    rota: list[str]
    custo_rota: int
    sucesso: bool
    motivo: str = ""
    custo_plano: int = 0
    acoes: int = 0
    expandidos: int = 0
    segundos: float = 0.0


@dataclass
class ResultadoRealimentacao:
    sucesso: bool
    tentativas: list[Tentativa] = field(default_factory=list)
    roteamento: dict | None = None
    tarefa: object | None = None
    plano: object | None = None
    diagnostico: str = ""
    estrutural: bool = False


def exige_paragrafo_4(paciente: dict) -> bool:
    return any(paciente.get(c) for c in PROCEDIMENTOS_PARAGRAFO_4)


def diagnosticar(dados: dict) -> tuple[bool, str]:
    """Devolve (estrutural, motivo).

    `estrutural = True` significa que nenhuma reordenacao das paradas torna
    o turno exequivel, e que insistir seria desperdicio de busca.
    """
    agente = dados["agente"]
    pacientes = dados["pacientes"]
    condicionados = [p for p in pacientes if exige_paragrafo_4(p)]

    habilitado = (agente.get("curso_tecnico_concluido")
                  and agente.get("equipamento_disponivel"))
    if condicionados and not habilitado:
        falta = ("curso tecnico" if not agente.get("curso_tecnico_concluido")
                 else "equipamento adequado")
        return True, (f"o ACS nao tem {falta}, e {len(condicionados)} paciente(s) "
                      "exigem procedimento do art. 3o par. 4o")

    janelas = dados["recursos"]["janelas_supervisao_no_turno"]
    if len(condicionados) > janelas:
        return True, (f"{len(condicionados)} visitas exigem supervisao e o turno "
                      f"tem {janelas} janela(s): a supervisao se encerra ao sair "
                      "da residencia e nao se repoe na unidade")

    return False, ""


def explicar_reprovacao(dados: dict, roteamento: dict) -> dict:
    """Traduz "espaco de estados exaurido" na causa concreta, legivel.

    O planejador prova que nao existe plano, mas o motivo que ele devolve e
    o da BUSCA ("exauri o espaco"), nao o do PROBLEMA. Para quem le, isso
    nao explica nada. Esta funcao reconstitui a causa a partir dos dados e
    da ordem das paradas.

    A causa que interessa aqui e a precedencia por urgencia. Com a rota
    congelada, se um paciente de urgencia baixa aparece antes de um de
    urgencia alta, a acao `iniciar-visita-adiavel` nunca fica aplicavel:
    sua pre-condicao exige o contador (altos-pendentes n0), e o contador so
    baixa quando a visita de urgencia alta comeca. Como o agente nao pode
    pular nem reordenar, nao ha plano, e A*/h_max demonstra isso exaurindo
    o espaco.
    """
    precede = roteamento.get("precedencias") or {}
    id_ubs = dados["ubs"]["id"]
    rota = [p for p in roteamento["rota"] if p != id_ubs]
    posicao = {p: i + 1 for i, p in enumerate(rota)}

    vistos: set[str] = set()
    for parada in rota:
        pendentes = [a for a in precede.get(parada, ()) if a not in vistos]
        if pendentes:
            alto = min(pendentes, key=lambda a: posicao.get(a, 999))
            return {
                "tipo": "precedencia",
                "baixo": parada, "alto": alto,
                "pos_baixo": posicao[parada], "pos_alto": posicao.get(alto, 0),
                "texto": (
                    f"a {posicao[parada]}a parada e {parada}, de urgencia baixa, "
                    f"e {alto}, de urgencia alta, so viria na "
                    f"{posicao.get(alto, 0)}a. Com a rota congelada, a acao de "
                    f"iniciar uma visita adiavel exige que nenhuma urgencia alta "
                    f"esteja pendente, e esse contador so baixa quando {alto} e "
                    f"atendido. Nenhuma sequencia de acoes satisfaz isso."),
            }
        vistos.add(parada)

    return {"tipo": "recurso", "texto": (
        "a ordem das paradas nao viola precedencia, entao a causa esta no "
        "consumo de recursos ao longo do turno: nesta sequencia, as janelas "
        "de supervisao ou o insumo nao bastam para cobrir todas as visitas.")}


def mesma_volta_invertida(rota_a: list[str], rota_b: list[str]) -> bool:
    """Diz se duas rotas sao o mesmo ciclo percorrido em sentidos opostos.

    Importa para a explicacao: num ciclo simetrico as duas direcoes custam
    exatamente o mesmo, e ainda assim uma pode cumprir a norma e a outra
    nao. E a demonstracao mais limpa de que o problema nao e geometrico.
    """
    if len(rota_a) != len(rota_b):
        return False
    return rota_a == list(reversed(rota_b))


def planejar_com_realimentacao(
        dados: dict, caminho_dominio: str, *,
        dominio: str = "legal",
        metodo: str = roteirizador.METODO_PADRAO,
        provedor_distancia: str = "haversine",
        modal: str | None = None,
        usar_precedencia: bool = True,
        roteador_ciente: bool = True,
        semente: int = 0,
        estrategia: str = "astar-hmax",
        limite: float = 60.0,
        max_tentativas: int = 6,
        caminho_problema: str = CAMINHO_PROBLEMA_PADRAO,
        silencioso: bool = True) -> ResultadoRealimentacao:
    """Passo 2 e passo 3 em laco, ate achar uma rota exequivel ou desistir.

    `roteador_ciente = False` simula o caso que motiva a realimentacao: um
    roteirizador de prateleira, que minimiza deslocamento e NAO conhece a
    precedencia clinica. A camada normativa continua exigindo-a, reprova as
    rotas que a violam e pede outra. E a situacao real de quem troca a
    camada geometrica por OR-Tools ou por um servico externo.
    """
    estrutural, motivo = diagnosticar(dados)
    if estrutural:
        return ResultadoRealimentacao(False, [], None, None, None, motivo, True)

    # a matriz nao muda entre tentativas: calcula uma vez e reaproveita,
    # senao cada tentativa refaria as chamadas de rede do provedor externo.
    pontos = [dados["ubs"]] + dados["pacientes"]
    matriz, provedor = construir_matriz(pontos, provedor_distancia, silencioso,
                                        modal=modal)
    pronta = {"matriz": matriz, "provedor": provedor}

    tentativas: list[Tentativa] = []
    vistas: set[tuple[str, ...]] = set()

    for variante in range(max_tentativas):
        roteamento = roteirizador.roteirizar(
            dados, metodo=metodo, provedor_distancia=provedor_distancia,
            modal=modal,
            usar_precedencia=usar_precedencia and roteador_ciente,
            semente=semente, variante=variante, matriz_pronta=pronta,
            silencioso=True)

        if usar_precedencia and not roteador_ciente:
            # a norma vale mesmo que o roteirizador a ignore: a restricao
            # volta para o problema PDDL, e e a camada logica que cobra.
            intervalo = dados.get("_meta", {}).get(
                "intervalo_maximo_padrao_dias",
                modelos.INTERVALO_MAXIMO_PADRAO_DIAS)
            roteamento["precedencias"] = roteirizador.precedencias(
                dados["pacientes"], True, intervalo)

        assinatura = tuple(roteamento["rota"])
        if assinatura in vistas:
            continue                       # a variante repetiu uma rota ja reprovada
        vistas.add(assinatura)

        gerar_problema(dados, roteamento, caminho_problema, dominio=dominio)
        tarefa = TarefaPlanejamento(carregar_dominio(caminho_dominio),
                                    carregar_problema(caminho_problema))
        plano = resolver(tarefa, estrategia, limite_segundos=limite)

        tentativas.append(Tentativa(
            variante=variante,
            rota=list(roteamento["rota"]),
            custo_rota=roteamento["custo_rota"],
            sucesso=plano.sucesso,
            motivo="" if plano.sucesso else plano.motivo,
            custo_plano=plano.custo if plano.sucesso else 0,
            acoes=plano.tamanho if plano.sucesso else 0,
            expandidos=plano.expandidos,
            segundos=plano.segundos))

        if plano.sucesso:
            return ResultadoRealimentacao(True, tentativas, roteamento, tarefa,
                                          plano, "", False)

    # nenhuma rota passou: devolve a ultima tentada, para que o relatorio e a
    # comparacao com o executor procedural ainda tenham sobre o que falar.
    return ResultadoRealimentacao(
        False, tentativas, roteamento, tarefa, plano,
        f"{len(tentativas)} rotas distintas foram reprovadas pelo planejamento",
        False)
