"""
Gerador de microareas sinteticas para os experimentos.

As instancias sao sorteadas, mas nao arbitrarias: os perfis e suas
exigencias foram montados a partir do rol do art. 3o da Lei 11.350/2006, de
modo que a composicao de procedimentos de uma microarea sorteada tenha a
mesma natureza da microarea de exemplo.

O objetivo NAO e estimar prevalencia epidemiologica brasileira: seria
irresponsavel apresentar numeros sorteados como se fossem dados do SUS. O
objetivo e variar a estrutura combinatoria da instancia (quantos
procedimentos supervisionados, quantas medicoes de glicemia, qual a
distribuicao de urgencias, onde ficam geograficamente) para testar as
hipoteses do experimento.
"""

from __future__ import annotations

import random

# Caixa geografica aproximada da regiao usada no exemplo (Porto Alegre-RS).
LAT_MIN, LAT_MAX = -30.0490, -30.0300
LON_MIN, LON_MAX = -51.2300, -51.2080

# Perfis. As exigencias derivam da condicao clinica e do grupo etario:
# par. 4o I a V para os procedimentos condicionados, e par. 3o IV "c" / V "c"
# para a verificacao vacinal de crianca, gestante e pessoa idosa.
#
# campos: grupo, condicoes, pa, glicemia, temperatura, antropometria,
#         orientacao de medicacao, vacinal, protecao respiratoria, peso
PERFIS = [
    ("pessoa_idosa", ["hipertensao"],
     True, False, False, False, True, True, False, 3),
    ("pessoa_idosa", ["diabetes_mellitus_2"],
     False, True, False, False, True, True, False, 2),
    ("pessoa_idosa", ["diabetes_mellitus_2", "hipertensao"],
     True, True, False, False, True, True, False, 2),
    ("adulto", ["hipertensao"],
     True, False, False, False, False, False, False, 3),
    ("adulto", ["diabetes_mellitus_2"],
     True, True, False, False, False, False, False, 2),
    ("adulto", ["sintomatico_respiratorio_em_investigacao"],
     True, False, True, False, False, False, True, 1),
    ("gestante", ["pre_natal"],
     True, False, False, True, False, True, False, 2),
    ("lactante", ["puerperio"],
     True, False, False, True, False, True, False, 1),
    ("crianca", ["puericultura"],
     False, False, False, True, False, True, False, 2),
    ("adulto", ["sem_condicao_cronica"],
     False, False, False, False, False, False, False, 2),
]

INTERVALOS_POR_GRUPO = {
    "gestante": 15,
    "lactante": 15,
    "crianca": 30,
    "pessoa_idosa": 30,
    "adulto": 30,
}


def gerar(n_pacientes: int, semente: int,
          fitas_por_carga: int = 2,
          janelas_supervisao: int | None = None,
          doses_alcool: int = 6,
          mascaras: int = 2,
          capacidade_coletor: int = 3) -> dict:
    """Devolve um dicionario no mesmo formato de microarea_exemplo.json."""
    sorteio = random.Random(semente)

    pacientes = []
    pesos = [p[-1] for p in PERFIS]
    for i in range(1, n_pacientes + 1):
        (grupo, condicoes, pa, glicemia, temperatura, antropometria,
         orientacao, vacinal, protecao, _) = sorteio.choices(PERFIS, weights=pesos, k=1)[0]
        intervalo = INTERVALOS_POR_GRUPO.get(grupo, 30)
        pacientes.append({
            "id": f"p{i}",
            "nome": f"Paciente {i:02d}",
            "lat": sorteio.uniform(LAT_MIN, LAT_MAX),
            "lon": sorteio.uniform(LON_MIN, LON_MAX),
            "grupo": grupo,
            "condicoes": condicoes,
            "requer_pa": pa,
            "requer_glicemia": glicemia,
            "requer_temperatura": temperatura,
            "requer_antropometria": antropometria,
            "requer_orientacao_medicacao": orientacao,
            "requer_vacinal": vacinal,
            "exige_protecao_respiratoria": protecao,
            "dias_desde_ultima_visita": sorteio.randint(8, int(intervalo * 1.5)),
            "intervalo_maximo_dias": intervalo,
            "prioridade": sorteio.randint(1, 3),
        })

    # Por padrao, uma janela de supervisao por residencia: o recurso escasso
    # do experimento e a fita de glicemia, nao a supervisao. Reduzir este
    # valor e o que produz as instancias inviaveis por falta de recurso.
    if janelas_supervisao is None:
        janelas_supervisao = n_pacientes

    return {
        "_meta": {
            "descricao": f"instancia sintetica n={n_pacientes} semente={semente}",
            "intervalo_maximo_padrao_dias": 30,
        },
        "ubs": {"id": "ubs", "nome": "UBS sintetica",
                "lat": -30.0397, "lon": -51.2189},
        "recursos": {
            "fitas_glicemia_por_carga": fitas_por_carga,
            "janelas_supervisao_no_turno": janelas_supervisao,
            "doses_alcool_por_carga": doses_alcool,
            "mascaras_por_carga": mascaras,
            "capacidade_coletor": capacidade_coletor,
        },
        "agente": {
            "id": "acs1",
            "nome": "ACS sintetico",
            "curso_tecnico_concluido": True,
            "equipamento_disponivel": True,
        },
        "pacientes": pacientes,
    }
