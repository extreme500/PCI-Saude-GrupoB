"""
Gerador de microareas sinteticas para os experimentos.

As instancias sao sorteadas, mas nao arbitrarias: as prevalencias das
condicoes que disparam cada procedimento foram escolhidas para produzir
microareas com composicao parecida com a do exemplo real do protótipo
(mistura de hipertensos, diabeticos, gestantes, criancas e idosos).

O objetivo NAO e estimar prevalencia epidemiologica brasileira - seria
irresponsavel apresentar numeros sorteados como se fossem dados do SUS.
O objetivo e variar a estrutura combinatoria da instancia (quantos
procedimentos supervisionados, quantas medicoes de glicemia, onde ficam
geograficamente) para testar as hipoteses do experimento.
"""

from __future__ import annotations

import random

# Caixa geografica aproximada da regiao usada no exemplo (Porto Alegre-RS).
LAT_MIN, LAT_MAX = -30.0490, -30.0300
LON_MIN, LON_MAX = -51.2300, -51.2080

# Perfis e o que cada um exige. requer_pa / requer_glicemia derivam da
# condicao clinica; requer_vacinal deriva do grupo etario, conforme o
# art. 3o par. 3o IV "c" e V "c" da Lei 11.350/2006.
PERFIS = [
    # (grupo,          condicoes,                       pa,    glicemia, vacinal, peso)
    ("pessoa_idosa",   ["hipertensao"],                 True,  False,    True,    3),
    ("pessoa_idosa",   ["diabetes_mellitus_2"],         False, True,     True,    2),
    ("pessoa_idosa",   ["diabetes_mellitus_2",
                        "hipertensao"],                 True,  True,     True,    2),
    ("adulto",         ["hipertensao"],                 True,  False,    False,   3),
    ("adulto",         ["diabetes_mellitus_2"],         True,  True,     False,   2),
    ("gestante",       ["pre_natal"],                   True,  False,    True,    2),
    ("crianca",        ["puericultura"],                False, False,    True,    2),
    ("adulto",         ["sem_condicao_cronica"],        False, False,    False,   2),
]


def gerar(n_pacientes: int, semente: int,
          fitas_por_carga: int = 2,
          janelas_supervisao: int | None = None) -> dict:
    """Devolve um dicionario no mesmo formato de microarea_exemplo.json."""
    sorteio = random.Random(semente)

    pacientes = []
    pesos = [p[-1] for p in PERFIS]
    for i in range(1, n_pacientes + 1):
        grupo, condicoes, pa, glicemia, vacinal, _ = sorteio.choices(
            PERFIS, weights=pesos, k=1)[0]
        pacientes.append({
            "id": f"p{i}",
            "nome": f"Paciente {i:02d}",
            "lat": sorteio.uniform(LAT_MIN, LAT_MAX),
            "lon": sorteio.uniform(LON_MIN, LON_MAX),
            "grupo": grupo,
            "condicoes": condicoes,
            "requer_pa": pa,
            "requer_glicemia": glicemia,
            "requer_vacinal": vacinal,
            "dias_desde_ultima_visita": sorteio.randint(10, 40),
            "prioridade": sorteio.randint(1, 3),
        })

    # Por padrao, uma janela de supervisao por residencia: o recurso escasso
    # do experimento e a fita de glicemia, nao a supervisao. Reduzir este
    # valor e o que produz as instancias inviaveis do experimento E3b.
    if janelas_supervisao is None:
        janelas_supervisao = n_pacientes

    return {
        "_meta": {"descricao": f"instancia sintetica n={n_pacientes} "
                               f"semente={semente}"},
        "ubs": {"id": "ubs", "nome": "UBS sintetica",
                "lat": -30.0397, "lon": -51.2189},
        "recursos": {
            "fitas_glicemia_por_carga": fitas_por_carga,
            "janelas_supervisao_no_turno": janelas_supervisao,
        },
        "agente": {
            "id": "acs1",
            "nome": "ACS sintetico",
            "curso_tecnico_concluido": True,
            "equipamento_disponivel": True,
        },
        "pacientes": pacientes,
    }
