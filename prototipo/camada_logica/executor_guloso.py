"""
Linha de base: o "script simples de Python" que o planejador precisa vencer.

Por que este modulo existe
--------------------------
A objecao mais forte contra usar Planejamento Automatizado aqui e a da
REDUNDANCIA TECNOLOGICA: "um laco `for` sobre a rota faria o mesmo". Sem uma
implementacao concreta dessa objecao nao ha experimento - so retorica.

Este executor e, portanto, um adversario honesto, nao um espantalho:
  - percorre a rota na ordem dada;
  - cumpre exatamente os mesmos protocolos legais;
  - aciona a supervisao quando precisa e reabastece quando fica sem fitas;
  - usa EXATAMENTE a mesma tabela de custos do dominio PDDL (lida do
    proprio arquivo .pddl, para que nao haja divergencia entre as duas
    implementacoes).

O que ele nao faz - e e justamente essa a hipotese H1 do experimento - e
ANTECIPAR. Ele so descobre que precisa de fitas quando ja esta sem fitas, e
entao desvia a partir da parada em que estiver, por mais cara que ela seja.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gerador_problema import local_do_paciente
from planejador import carregar_dominio


# ---------------------------------------------------------------------------
#  Tabela de custos lida do dominio PDDL, para garantir paridade de medicao
# ---------------------------------------------------------------------------

def custos_do_dominio(caminho_dominio: str) -> dict[str, int]:
    """Extrai o custo constante de cada acao do proprio arquivo de dominio."""
    dominio = carregar_dominio(caminho_dominio)
    return {a.nome: a.custo for a in dominio.acoes if isinstance(a.custo, int)}


@dataclass
class ResultadoGuloso:
    sucesso: bool
    plano: list[str] = field(default_factory=list)
    custo: int = 0
    motivo: str = ""

    @property
    def tamanho(self) -> int:
        return len(self.plano)


def executar(dados: dict, roteamento: dict, caminho_dominio: str) -> ResultadoGuloso:
    """Simula o ACS seguindo a rota e cumprindo os protocolos de forma reativa."""
    custos = custos_do_dominio(caminho_dominio)
    agente = dados["agente"]
    id_agente = agente["id"]
    id_ubs = dados["ubs"]["id"]
    por_id = {p["id"]: p for p in dados["pacientes"]}

    capacidade = dados["recursos"]["fitas_glicemia_por_carga"]
    fitas = capacidade
    janelas = dados["recursos"]["janelas_supervisao_no_turno"]
    supervisao_ativa = False

    plano: list[str] = []
    custo = 0
    matriz = roteamento["matriz"]
    rota = roteamento["rota"]

    def registrar(acao: str, valor: int) -> None:
        nonlocal custo
        plano.append(acao)
        custo += valor

    def garantir_supervisao(local: str) -> bool:
        """Art. 3o par. 4o: aciona o profissional de nivel superior."""
        nonlocal supervisao_ativa, janelas
        if supervisao_ativa:
            return True
        if janelas <= 0:
            return False
        janelas -= 1
        supervisao_ativa = True
        registrar(f"acionar-supervisao({id_agente}, ...)",
                  custos["acionar-supervisao"])
        return True

    # ---- verificacao previa das condicoes do caput -------------------------
    habilitado = (agente.get("curso_tecnico_concluido")
                  and agente.get("equipamento_disponivel"))

    for indice, parada in enumerate(rota):
        if indice > 0:
            anterior = rota[indice - 1]
            registrar(
                f"mover({id_agente}, {_nome(anterior, id_ubs)}, "
                f"{_nome(parada, id_ubs)})",
                matriz[(anterior, parada)],
            )
            supervisao_ativa = False  # sair da residencia encerra a assistencia

        if parada == id_ubs:
            continue

        paciente = por_id[parada]
        local = local_do_paciente(parada)
        registrar(f"iniciar-visita({id_agente}, {parada}, {local})",
                  custos["iniciar-visita"])

        precisa_encaminhar = False

        if paciente.get("requer_vacinal"):
            registrar(f"verificar-caderneta-vacinal({id_agente}, {parada}, "
                      f"{local})", custos["verificar-caderneta-vacinal"])

        if paciente.get("requer_pa"):
            if not habilitado:
                return ResultadoGuloso(
                    False, plano, custo,
                    f"{parada} exige afericao de PA, mas o ACS nao cumpre as "
                    "condicoes do art. 3o par. 4o (curso tecnico / equipamento)")
            if not garantir_supervisao(local):
                return ResultadoGuloso(
                    False, plano, custo,
                    f"acabaram as janelas de supervisao antes de {parada}")
            registrar(f"aferir-pressao-arterial({id_agente}, {parada}, {local})",
                      custos["aferir-pressao-arterial"])
            precisa_encaminhar = True

        if paciente.get("requer_glicemia"):
            if not habilitado:
                return ResultadoGuloso(
                    False, plano, custo,
                    f"{parada} exige glicemia capilar, mas o ACS nao cumpre as "
                    "condicoes do art. 3o par. 4o (curso tecnico / equipamento)")

            # ---- AQUI ESTA A MIOPIA DO GULOSO --------------------------------
            # So percebe a falta de insumo no momento do uso, e resolve o
            # problema desviando a partir da parada ATUAL, seja ela qual for.
            if fitas == 0:
                custo_desvio = roteamento["custo_desvio"][parada]
                registrar(f"desviar-para-ubs({id_agente}, {local}, {id_ubs})",
                          custo_desvio)
                registrar(f"reabastecer-fitas({id_agente}, {id_ubs}, ...)",
                          custos["reabastecer-fitas"])
                registrar(f"retornar-a-rota({id_agente}, {id_ubs}, {local})", 0)
                fitas = capacidade
                supervisao_ativa = False
            # ------------------------------------------------------------------

            if not garantir_supervisao(local):
                return ResultadoGuloso(
                    False, plano, custo,
                    f"acabaram as janelas de supervisao antes de {parada}")
            registrar(f"medir-glicemia-capilar({id_agente}, {parada}, {local}, "
                      f"...)", custos["medir-glicemia-capilar"])
            fitas -= 1
            precisa_encaminhar = True

        if precisa_encaminhar:
            registrar(f"registrar-encaminhamento({id_agente}, {parada}, {local})",
                      custos["registrar-encaminhamento"])

        registrar(f"registrar-visita({id_agente}, {parada}, {local})",
                  custos["registrar-visita"])

    return ResultadoGuloso(True, plano, custo)


def _nome(identificador: str, id_ubs: str) -> str:
    return identificador if identificador == id_ubs \
        else local_do_paciente(identificador)
