"""
Grandezas derivadas dos dados de entrada.

Este módulo não guarda estado: recebe o dicionário de um paciente (como vem
do JSON) e devolve os valores calculados a partir dele. Concentrar essas
contas aqui evita que a mesma regra apareça escrita de formas diferentes no
roteirizador, na política de seleção e no gerador de problema.

As duas grandezas centrais são o ATRASO e a URGÊNCIA.

O atraso compara há quantos dias o paciente não é visitado com o intervalo
máximo definido para o seu perfil. A referência de intervalo é parâmetro
configurável, não norma: a PNAB orienta priorizar por risco e
vulnerabilidade sem fixar critério numérico de periodicidade.
"""

from __future__ import annotations

# Pesos da combinação prioridade × atraso. Arbitrados, e ajustáveis:
# o objetivo é que um paciente muito atrasado suba na fila mesmo com
# prioridade clínica baixa, sem que o atraso sozinho domine a decisão.
PESO_PRIORIDADE = 1.0
PESO_ATRASO = 0.6

INTERVALO_MAXIMO_PADRAO_DIAS = 30


def intervalo_maximo(paciente: dict, padrao: int = INTERVALO_MAXIMO_PADRAO_DIAS) -> int:
    """Intervalo máximo entre visitas aceito para este paciente, em dias."""
    return int(paciente.get("intervalo_maximo_dias") or padrao)


def atraso_em_dias(paciente: dict, padrao: int = INTERVALO_MAXIMO_PADRAO_DIAS) -> int:
    """Dias além do intervalo máximo. Zero ou negativo significa em dia."""
    return int(paciente.get("dias_desde_ultima_visita", 0)) - intervalo_maximo(paciente, padrao)


def esta_atrasado(paciente: dict, padrao: int = INTERVALO_MAXIMO_PADRAO_DIAS) -> bool:
    return atraso_em_dias(paciente, padrao) > 0


def escore_urgencia(paciente: dict, padrao: int = INTERVALO_MAXIMO_PADRAO_DIAS) -> float:
    """Combina prioridade clínica e atraso num único número comparável.

    A prioridade vem da unidade de saúde (1 a 3). O atraso entra normalizado
    pelo próprio intervalo máximo, de modo que "15 dias de atraso" pese o
    mesmo para quem tem intervalo de 30 dias e para quem tem de 15 dias,
    proporcionalmente.
    """
    prioridade = float(paciente.get("prioridade", 1))
    atraso = atraso_em_dias(paciente, padrao)
    janela = max(1, intervalo_maximo(paciente, padrao))
    atraso_relativo = max(0.0, atraso / janela)
    return PESO_PRIORIDADE * prioridade + PESO_ATRASO * atraso_relativo * 3.0


def nivel_urgencia(paciente: dict, padrao: int = INTERVALO_MAXIMO_PADRAO_DIAS) -> int:
    """Discretiza o escore em três faixas: 3 alta, 2 média, 1 baixa.

    A faixa alta é a que gera restrição de precedência (ver
    `acsplan.geo.roteirizador.precedencias`): um paciente de urgência alta
    deve ser atendido antes dos de urgência baixa no mesmo turno.
    """
    escore = escore_urgencia(paciente, padrao)
    if escore >= 3.5:
        return 3
    if escore >= 2.0:
        return 2
    return 1


def rotulo_urgencia(nivel: int) -> str:
    return {3: "ALTA", 2: "média", 1: "baixa"}.get(nivel, "?")


def exigencias(paciente: dict) -> list[str]:
    """Procedimentos que o perfil do paciente exige, em nomes legíveis."""
    mapa = [
        ("requer_pa", "aferir pressão arterial"),
        ("requer_glicemia", "medir glicemia capilar"),
        ("requer_temperatura", "aferir temperatura axilar"),
        ("requer_antropometria", "verificação antropométrica"),
        ("requer_orientacao_medicacao", "orientar administração de medicação"),
        ("requer_vacinal", "verificar caderneta vacinal"),
    ]
    return [rotulo for campo, rotulo in mapa if paciente.get(campo)]


def exige_supervisao(paciente: dict) -> bool:
    """Se algum procedimento do art. 3º § 4º é exigido por este paciente.

    Os cinco incisos do § 4º compartilham as mesmas condições cumulativas
    (curso técnico, equipamento e assistência de profissional de nível
    superior), então basta um deles para que a supervisão seja necessária.
    """
    return any(paciente.get(c) for c in (
        "requer_pa", "requer_glicemia", "requer_temperatura",
        "requer_antropometria", "requer_orientacao_medicacao",
    ))
