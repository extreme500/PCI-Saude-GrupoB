"""
Carregamento das microareas, em JSON ou CSV.

Por que existem dois formatos
-----------------------------
O JSON guarda a microarea inteira num arquivo so: unidade de saude, recursos
do turno, dados do agente e pacientes. E o formato interno e o que os
experimentos usam.

O CSV existe porque a tabela de pacientes e a unica parte que alguem edita na
pratica, e editar isso numa planilha e muito mais comodo do que mexer em
JSON. Um CSV de pacientes pode vir acompanhado de um arquivo de mesmo nome
com extensao `.json`, que traz unidade, recursos e agente; se nao vier, os
padroes documentados abaixo sao usados.

    microarea.csv          <- a planilha de pacientes (so isto e obrigatorio)
    microarea.json         <- opcional: unidade, recursos e agente

Colunas do CSV
--------------
Obrigatorias: id, lat, lon
Opcionais   : nome, grupo, condicoes, prioridade, dias_desde_ultima_visita,
              intervalo_maximo_dias e as colunas requer_* / exige_*

As colunas booleanas aceitam sim/nao, s/n, true/false, 1/0, x ou vazio.
A coluna `condicoes` aceita varios valores separados por ponto e virgula.
Qualquer coluna ausente recebe o padrao, de modo que uma planilha minima com
id, lat e lon ja funciona.
"""

from __future__ import annotations

import csv
import json
import os

BOOLEANOS_VERDADEIROS = {"sim", "s", "true", "t", "1", "x", "yes", "y", "v"}

COLUNAS_BOOLEANAS = [
    "requer_pa", "requer_glicemia", "requer_temperatura",
    "requer_antropometria", "requer_orientacao_medicacao",
    "requer_vacinal", "exige_protecao_respiratoria",
]

# Usados quando o CSV vem sem o .json companheiro.
UBS_PADRAO = {"id": "ubs", "nome": "Unidade Basica de Saude",
              "lat": -30.0397, "lon": -51.2189}
RECURSOS_PADRAO = {
    "fitas_glicemia_por_carga": 2,
    "janelas_supervisao_no_turno": None,   # None = uma por paciente
    "doses_alcool_por_carga": 6,
    "mascaras_por_carga": 2,
    "capacidade_coletor": 3,
}
AGENTE_PADRAO = {"id": "acs1", "nome": "ACS da microarea",
                 "curso_tecnico_concluido": True,
                 "equipamento_disponivel": True}


class ErroDeDados(Exception):
    """Erro de formato nos dados de entrada, com linha e coluna quando dá."""


def _booleano(valor: str | None) -> bool:
    return (valor or "").strip().lower() in BOOLEANOS_VERDADEIROS


def _inteiro(valor: str | None, padrao: int, linha: int, coluna: str) -> int:
    texto = (valor or "").strip()
    if not texto:
        return padrao
    try:
        return int(float(texto.replace(",", ".")))
    except ValueError:
        raise ErroDeDados(
            f"linha {linha}, coluna '{coluna}': '{texto}' nao e um numero")


def _decimal(valor: str | None, linha: int, coluna: str) -> float:
    texto = (valor or "").strip().replace(",", ".")
    if not texto:
        raise ErroDeDados(f"linha {linha}: a coluna '{coluna}' e obrigatoria")
    try:
        return float(texto)
    except ValueError:
        raise ErroDeDados(
            f"linha {linha}, coluna '{coluna}': '{texto}' nao e uma coordenada")


def ler_csv(caminho: str) -> dict:
    """Le a planilha de pacientes e monta a microarea completa."""
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        amostra = arquivo.read(4096)
        arquivo.seek(0)
        try:
            dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t")
        except csv.Error:
            dialeto = csv.excel
        leitor = csv.DictReader(arquivo, dialect=dialeto)
        if not leitor.fieldnames:
            raise ErroDeDados(f"{caminho}: planilha vazia ou sem cabecalho")
        cabecalho = [c.strip().lower() for c in leitor.fieldnames]
        for obrigatoria in ("id", "lat", "lon"):
            if obrigatoria not in cabecalho:
                raise ErroDeDados(
                    f"{caminho}: falta a coluna obrigatoria '{obrigatoria}'. "
                    f"Colunas encontradas: {', '.join(cabecalho)}")

        pacientes = []
        for numero, bruto in enumerate(leitor, start=2):   # 1 e o cabecalho
            linha = {(k or "").strip().lower(): v for k, v in bruto.items()}
            if not (linha.get("id") or "").strip():
                continue                                    # linha em branco
            paciente = {
                "id": linha["id"].strip(),
                "nome": (linha.get("nome") or "").strip() or linha["id"].strip(),
                "lat": _decimal(linha.get("lat"), numero, "lat"),
                "lon": _decimal(linha.get("lon"), numero, "lon"),
                "grupo": (linha.get("grupo") or "adulto").strip(),
                "condicoes": [c.strip() for c in
                              (linha.get("condicoes") or "").split(";") if c.strip()],
                "prioridade": _inteiro(linha.get("prioridade"), 1, numero, "prioridade"),
                "dias_desde_ultima_visita": _inteiro(
                    linha.get("dias_desde_ultima_visita"), 0, numero,
                    "dias_desde_ultima_visita"),
                "intervalo_maximo_dias": _inteiro(
                    linha.get("intervalo_maximo_dias"), 30, numero,
                    "intervalo_maximo_dias"),
            }
            for coluna in COLUNAS_BOOLEANAS:
                paciente[coluna] = _booleano(linha.get(coluna))
            pacientes.append(paciente)

    if not pacientes:
        raise ErroDeDados(f"{caminho}: nenhum paciente com 'id' preenchido")

    ids = [p["id"] for p in pacientes]
    repetidos = {i for i in ids if ids.count(i) > 1}
    if repetidos:
        raise ErroDeDados(f"{caminho}: ids repetidos: {', '.join(sorted(repetidos))}")

    # arquivo companheiro com unidade, recursos e agente
    companheiro = os.path.splitext(caminho)[0] + ".json"
    extra = {}
    if os.path.exists(companheiro):
        with open(companheiro, encoding="utf-8") as arquivo:
            extra = json.load(arquivo)

    recursos = {**RECURSOS_PADRAO, **extra.get("recursos", {})}
    if recursos.get("janelas_supervisao_no_turno") is None:
        recursos["janelas_supervisao_no_turno"] = len(pacientes)

    return {
        "_meta": {
            "descricao": f"microarea carregada de {os.path.basename(caminho)}",
            "intervalo_maximo_padrao_dias": 30,
            **extra.get("_meta", {}),
        },
        "ubs": {**UBS_PADRAO, **extra.get("ubs", {})},
        "recursos": recursos,
        "agente": {**AGENTE_PADRAO, **extra.get("agente", {})},
        "pacientes": pacientes,
    }


def ler_json(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def carregar(caminho: str) -> dict:
    """Le a microarea, escolhendo o leitor pela extensao do arquivo."""
    if caminho.lower().endswith(".csv"):
        return ler_csv(caminho)
    return ler_json(caminho)


def exportar_csv(dados: dict, caminho: str) -> None:
    """Grava a tabela de pacientes como CSV, para editar em planilha."""
    colunas = (["id", "nome", "lat", "lon", "grupo", "condicoes", "prioridade",
                "dias_desde_ultima_visita", "intervalo_maximo_dias"]
               + COLUNAS_BOOLEANAS)
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        for p in dados["pacientes"]:
            linha = {c: p.get(c, "") for c in colunas}
            linha["condicoes"] = ";".join(p.get("condicoes", []))
            for c in COLUNAS_BOOLEANAS:
                linha[c] = "sim" if p.get(c) else "nao"
            linha["lat"] = f"{p['lat']:.6f}"
            linha["lon"] = f"{p['lon']:.6f}"
            escritor.writerow(linha)
