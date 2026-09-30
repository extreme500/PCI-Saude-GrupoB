"""
Linha de base: o executor procedural que o planejamento precisa superar.

Por que este modulo existe
--------------------------
A objecao mais forte contra usar Planejamento Automatizado aqui e a da
redundancia tecnologica: "um laco `for` sobre a rota faria o mesmo". Sem uma
implementacao concreta dessa objecao nao ha experimento, apenas retorica.

Este executor e, portanto, um adversario honesto, nao um espantalho:

  - percorre a rota na ordem dada pela camada geometrica;
  - cumpre exatamente os mesmos protocolos, legais e sinteticos;
  - aciona supervisao, higieniza, veste mascara e reabastece quando precisa;
  - usa EXATAMENTE a mesma tabela de custos do dominio PDDL, lida do proprio
    arquivo, para que nao haja divergencia de medicao entre os dois grupos
    comparados.

O que ele nao faz, e e justamente a variavel que o experimento isola, e
ANTECIPAR. Ele so descobre que falta um recurso no momento de usa-lo, e
entao resolve o problema a partir da parada em que estiver, por mais cara
que seja.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..dados import modelos
from .gerador_problema import local_do_paciente
from .planejador import carregar_dominio


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


def executar(dados: dict, roteamento: dict, caminho_dominio: str,
             *, estendido: bool = False) -> ResultadoGuloso:
    """Simula o ACS seguindo a rota e cumprindo os protocolos de forma reativa."""
    custos = custos_do_dominio(caminho_dominio)
    agente = dados["agente"]
    id_agente = agente["id"]
    id_ubs = dados["ubs"]["id"]
    recursos = dados["recursos"]
    por_id = {p["id"]: p for p in dados["pacientes"]}
    intervalo = dados.get("_meta", {}).get(
        "intervalo_maximo_padrao_dias", modelos.INTERVALO_MAXIMO_PADRAO_DIAS)

    cap_fitas = recursos["fitas_glicemia_por_carga"]
    cap_alcool = recursos.get("doses_alcool_por_carga", 8)
    cap_mascaras = recursos.get("mascaras_por_carga", 3)
    cap_coletor = recursos.get("capacidade_coletor", 3)

    fitas = cap_fitas
    alcool = cap_alcool
    mascaras = cap_mascaras
    coletor = cap_coletor
    janelas = recursos["janelas_supervisao_no_turno"]
    supervisao = False
    maos = False
    mascara_vestida = False

    precede = roteamento.get("precedencias") or {}
    atendidos: set[str] = set()

    plano: list[str] = []
    custo = 0
    matriz = roteamento["matriz"]
    rota = roteamento["rota"]

    def registrar(acao: str, valor: int) -> None:
        nonlocal custo
        plano.append(acao)
        custo += valor

    def falhar(motivo: str) -> ResultadoGuloso:
        return ResultadoGuloso(False, plano, custo, motivo)

    def desviar(parada: str, local: str) -> None:
        """Desvio reativo ate a UBS, a partir de onde o agente estiver."""
        nonlocal fitas, alcool, mascaras, coletor, supervisao, maos, mascara_vestida
        registrar(f"desviar-para-ubs({id_agente}, {local}, {id_ubs})",
                  roteamento["custo_desvio"][parada])
        registrar(f"reabastecer-fitas({id_agente}, {id_ubs}, ...)",
                  custos["reabastecer-fitas"])
        fitas = cap_fitas
        if estendido:
            registrar(f"repor-alcool({id_agente}, {id_ubs}, ...)", custos["repor-alcool"])
            alcool = cap_alcool
            registrar(f"repor-mascaras({id_agente}, {id_ubs}, ...)", custos["repor-mascaras"])
            mascaras = cap_mascaras
            registrar(f"trocar-coletor({id_agente}, {id_ubs}, ...)", custos["trocar-coletor"])
            coletor = cap_coletor
        registrar(f"retornar-a-rota({id_agente}, {id_ubs}, {local})", 0)
        supervisao = False
        maos = False
        mascara_vestida = False

    def garantir_supervisao() -> bool:
        nonlocal supervisao, janelas
        if supervisao:
            return True
        if janelas <= 0:
            return False
        janelas -= 1
        supervisao = True
        registrar(f"acionar-supervisao({id_agente}, ...)", custos["acionar-supervisao"])
        return True

    def garantir_maos(parada: str, local: str) -> bool:
        """Higienizacao [SINTETICO]: so existe no dominio estendido."""
        nonlocal maos, alcool, supervisao
        if not estendido or maos:
            return True
        if alcool <= 0:
            desviar(parada, local)
        if alcool <= 0:
            return False
        alcool -= 1
        maos = True
        registrar(f"higienizar-maos({id_agente}, ...)", custos["higienizar-maos"])
        return True

    habilitado = (agente.get("curso_tecnico_concluido")
                  and agente.get("equipamento_disponivel"))

    for indice, parada in enumerate(rota):
        if indice > 0:
            anterior = rota[indice - 1]
            registrar(f"mover({id_agente}, {_nome(anterior, id_ubs)}, "
                      f"{_nome(parada, id_ubs)})", matriz[(anterior, parada)])
            supervisao = False
            maos = False
            mascara_vestida = False

        if parada == id_ubs:
            continue

        paciente = por_id[parada]
        local = local_do_paciente(parada)

        # precedencia por urgencia: a rota pode viola-la, e o executor so
        # percebe quando chega na parada errada.
        faltando = [a for a in precede.get(parada, ()) if a not in atendidos]
        if faltando:
            return falhar(f"{parada} tem urgencia baixa e foi alcancado antes de "
                          f"{', '.join(sorted(faltando))}, de urgencia alta")

        # protecao respiratoria [SINTETICO]
        if estendido:
            if paciente.get("exige_protecao_respiratoria"):
                if not mascara_vestida:
                    if mascaras <= 0:
                        desviar(parada, local)
                    if mascaras <= 0:
                        return falhar(f"sem mascaras para atender {parada}")
                    mascaras -= 1
                    mascara_vestida = True
                    registrar(f"vestir-mascara({id_agente}, ...)", custos["vestir-mascara"])
                registrar(f"conferir-protecao-exigida({id_agente}, {parada}, {local})",
                          custos["conferir-protecao-exigida"])
            else:
                registrar(f"conferir-protecao-dispensada({id_agente}, {parada}, {local})",
                          custos["conferir-protecao-dispensada"])

        nivel = modelos.nivel_urgencia(paciente, intervalo)
        if precede and nivel == 3:
            acao_inicio = "iniciar-visita-urgente"
        elif precede and nivel == 1:
            acao_inicio = "iniciar-visita-adiavel"
        else:
            acao_inicio = "iniciar-visita"
        registrar(f"{acao_inicio}({id_agente}, {parada}, {local})",
                  custos.get(acao_inicio, custos["iniciar-visita"]))
        atendidos.add(parada)

        precisa_encaminhar = False

        # atividade tipica do par. 3o: sem condicionantes
        if paciente.get("requer_vacinal"):
            registrar(f"verificar-caderneta-vacinal({id_agente}, {parada}, {local})",
                      custos["verificar-caderneta-vacinal"])

        # procedimentos do par. 4o
        procedimentos = [
            ("requer_pa", "aferir-pressao-arterial", True),
            ("requer_temperatura", "aferir-temperatura-axilar", False),
            ("requer_antropometria", "verificacao-antropometrica", False),
            ("requer_orientacao_medicacao", "orientar-administracao-medicacao", False),
        ]
        for campo, acao, encaminha in procedimentos:
            if not paciente.get(campo):
                continue
            if not habilitado:
                return falhar(f"{parada} exige {acao}, mas o ACS nao cumpre as "
                              "condicoes do art. 3o par. 4o")
            if not garantir_supervisao():
                return falhar(f"acabaram as janelas de supervisao antes de {parada}")
            if not garantir_maos(parada, local):
                return falhar(f"sem solucao alcoolica para atender {parada}")
            if not garantir_supervisao():
                return falhar(f"acabaram as janelas de supervisao antes de {parada}")
            registrar(f"{acao}({id_agente}, {parada}, {local})", custos[acao])
            precisa_encaminhar = precisa_encaminhar or encaminha

        if paciente.get("requer_glicemia"):
            if not habilitado:
                return falhar(f"{parada} exige glicemia capilar, mas o ACS nao "
                              "cumpre as condicoes do art. 3o par. 4o")
            # AQUI ESTA A MIOPIA DO GULOSO: so percebe a falta de insumo no
            # momento do uso, e desvia a partir da parada atual, seja ela qual for.
            if fitas == 0 or (estendido and coletor == 0):
                desviar(parada, local)
            if not garantir_supervisao():
                return falhar(f"acabaram as janelas de supervisao antes de {parada}")
            if not garantir_maos(parada, local):
                return falhar(f"sem solucao alcoolica para atender {parada}")
            if not garantir_supervisao():
                return falhar(f"acabaram as janelas de supervisao antes de {parada}")
            registrar(f"medir-glicemia-capilar({id_agente}, {parada}, {local}, ...)",
                      custos["medir-glicemia-capilar"])
            fitas -= 1
            if estendido:
                coletor -= 1
            precisa_encaminhar = True

        if precisa_encaminhar:
            registrar(f"registrar-encaminhamento({id_agente}, {parada}, {local})",
                      custos["registrar-encaminhamento"])

        registrar(f"registrar-visita({id_agente}, {parada}, {local})",
                  custos["registrar-visita"])

    return ResultadoGuloso(True, plano, custo)


def _nome(identificador: str, id_ubs: str) -> str:
    return identificador if identificador == id_ubs else local_do_paciente(identificador)
