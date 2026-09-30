"""
Política de seleção: quem entra no turno de hoje.

Até aqui, prioridade clínica e intervalo máximo entre visitas existiam nos
dados sem influenciar nenhuma decisão: o turno atendia a microárea inteira.
Este módulo fecha essa lacuna, que era a mais visível em relação ao
enunciado do ciclo.

A decisão é tomada ANTES do roteamento, e por isso é uma terceira camada,
acima das outras duas:

    seleção (quem)  ->  roteamento (em que ordem)  ->  planejamento (o que fazer)

Como a escolha é feita
----------------------
Cada paciente recebe um escore que combina prioridade clínica e atraso em
relação ao seu intervalo máximo (ver `acsplan.dados.modelos`). A seleção
então percorre os pacientes em ordem decrescente de escore e vai incluindo
enquanto couber no orçamento do turno.

O orçamento é estimado, não exato: o custo real só é conhecido depois de
roteirizar e planejar. Usa-se aqui uma estimativa deliberadamente
conservadora (tempo de atendimento por paciente mais uma parcela de
deslocamento), e o ajuste fino fica por conta da camada seguinte. Superestimar
o que cabe no turno seria pior do que subestimar: geraria planos que o
agente não consegue executar.

Regra de proteção
-----------------
Pacientes em atraso acima de um limiar entram no turno independentemente do
orçamento, porque adiá-los de novo é justamente o que a política deveria
evitar. Essa regra pode tornar o turno mais longo que o orçamento nominal,
e o relatório sinaliza quando isso acontece.
"""

from __future__ import annotations

from ..dados import modelos

# Estimativa de tempo por paciente, em minutos: atendimento mais uma parcela
# média de deslocamento até a próxima casa. Arbitrada, e configurável.
#
# O valor é deliberadamente alto: subestimar produziria turnos que o agente
# não consegue executar, o que é pior do que selecionar menos gente. Mesmo
# assim é só uma estimativa, e a camada de planejamento pode devolver um
# custo maior; quando isso acontece, o roteiro avisa.
MINUTOS_ESTIMADOS_POR_PACIENTE = 38

# Atraso a partir do qual o paciente entra no turno mesmo estourando o
# orçamento. Em dias além do intervalo máximo do seu perfil.
ATRASO_INADIAVEL_DIAS = 7


def _estimar_minutos(quantidade: int) -> int:
    return quantidade * MINUTOS_ESTIMADOS_POR_PACIENTE


def selecionar(dados: dict, *, orcamento_minutos: int | None = None,
               maximo_pacientes: int | None = None,
               ativar: bool = True) -> dict:
    """Devolve uma cópia de `dados` contendo apenas os pacientes do turno.

    Com `ativar=False` a microárea inteira é mantida, que é o comportamento
    anterior a esta política e serve de base de comparação nos experimentos.
    """
    pacientes = dados["pacientes"]
    intervalo = dados.get("_meta", {}).get(
        "intervalo_maximo_padrao_dias", modelos.INTERVALO_MAXIMO_PADRAO_DIAS)

    if not ativar or (orcamento_minutos is None and maximo_pacientes is None):
        return {**dados, "_selecao": {
            "ativa": False,
            "selecionados": [p["id"] for p in pacientes],
            "adiados": [],
            "inadiaveis": [],
            "minutos_estimados": _estimar_minutos(len(pacientes)),
        }}

    ordenados = sorted(
        pacientes,
        key=lambda p: (-modelos.escore_urgencia(p, intervalo), p["id"]))

    inadiaveis = [p for p in ordenados
                  if modelos.atraso_em_dias(p, intervalo) >= ATRASO_INADIAVEL_DIAS]
    ids_inadiaveis = {p["id"] for p in inadiaveis}

    escolhidos = list(inadiaveis)
    for paciente in ordenados:
        if paciente["id"] in ids_inadiaveis:
            continue
        if maximo_pacientes is not None and len(escolhidos) >= maximo_pacientes:
            break
        if orcamento_minutos is not None and \
                _estimar_minutos(len(escolhidos) + 1) > orcamento_minutos:
            break
        escolhidos.append(paciente)

    # devolve na ordem original do arquivo, para a saída ficar estável
    ids_escolhidos = {p["id"] for p in escolhidos}
    selecionados = [p for p in pacientes if p["id"] in ids_escolhidos]
    adiados = [p for p in pacientes if p["id"] not in ids_escolhidos]

    estimado = _estimar_minutos(len(selecionados))
    return {
        **dados,
        "pacientes": selecionados,
        "_selecao": {
            "ativa": True,
            "orcamento_minutos": orcamento_minutos,
            "maximo_pacientes": maximo_pacientes,
            "selecionados": [p["id"] for p in selecionados],
            "adiados": [p["id"] for p in adiados],
            "inadiaveis": sorted(ids_inadiaveis),
            "minutos_estimados": estimado,
            "estourou_orcamento": (orcamento_minutos is not None
                                   and estimado > orcamento_minutos),
            "detalhe_adiados": [
                {"id": p["id"],
                 "urgencia": modelos.nivel_urgencia(p, intervalo),
                 "atraso_dias": modelos.atraso_em_dias(p, intervalo)}
                for p in adiados
            ],
        },
    }
