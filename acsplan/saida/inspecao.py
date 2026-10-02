"""
Inspecao da microarea: o que ha nos dados, antes de planejar nada.

Serve para responder, olhando e nao lendo codigo, tres perguntas:
quais sao os pacientes e o que cada um exige, onde eles ficam uns em relacao
aos outros, e quais recursos o turno tem.

O "mapa" do projeto nao e um mapa de verdade: sao coordenadas que viram uma
matriz de tempos de deslocamento. O desenho abaixo e uma projecao grosseira,
so para dar nocao de vizinhanca; as distancias usadas no planejamento vem da
matriz, nao do desenho.
"""

from __future__ import annotations

from ..dados import modelos
from ..geo.distancias import construir_matriz

SIGLAS = {
    "requer_pa": "PA",
    "requer_glicemia": "GLI",
    "requer_temperatura": "TMP",
    "requer_antropometria": "ANT",
    "requer_orientacao_medicacao": "MED",
    "requer_vacinal": "VAC",
}


def desenhar_mapa(dados: dict, largura: int = 58, altura: int = 17) -> list[str]:
    """Projeta as coordenadas numa grade de caracteres.

    A projecao e linear em latitude e longitude, sem correcao de escala, e
    portanto distorce. Serve para ver quem esta perto de quem, nada alem.
    """
    pontos = [dados["ubs"]] + dados["pacientes"]
    lats = [p["lat"] for p in pontos]
    lons = [p["lon"] for p in pontos]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    span_lat = (lat_max - lat_min) or 1e-9
    span_lon = (lon_max - lon_min) or 1e-9

    grade = [[" "] * largura for _ in range(altura)]
    ocupacao: dict[tuple[int, int], str] = {}

    for ponto in pontos:
        # latitude cresce para o norte, entao a linha e invertida
        linha = int((lat_max - ponto["lat"]) / span_lat * (altura - 1))
        coluna = int((ponto["lon"] - lon_min) / span_lon * (largura - 4))
        rotulo = "UBS" if ponto is dados["ubs"] else ponto["id"]
        while (linha, coluna) in ocupacao and coluna < largura - len(rotulo) - 1:
            coluna += 1                      # desvia sobreposicao
        ocupacao[(linha, coluna)] = rotulo
        for i, caractere in enumerate(rotulo):
            if coluna + i < largura:
                grade[linha][coluna + i] = caractere

    moldura = ["  +" + "-" * largura + "+"]
    moldura += ["  |" + "".join(l) + "|" for l in grade]
    moldura += ["  +" + "-" * largura + "+"]
    return moldura


def imprimir(dados: dict, *, mostrar_matriz: bool = False) -> None:
    pacientes = dados["pacientes"]
    recursos = dados["recursos"]
    agente = dados["agente"]
    intervalo = dados.get("_meta", {}).get(
        "intervalo_maximo_padrao_dias", modelos.INTERVALO_MAXIMO_PADRAO_DIAS)

    print()
    print("=" * 74)
    print("  MICROAREA")
    print("=" * 74)
    print(f"  {dados.get('_meta', {}).get('descricao', '')[:68]}")
    print()
    print(f"  Unidade  : {dados['ubs'].get('nome', dados['ubs']['id'])}")
    print(f"  Agente   : {agente.get('nome', agente['id'])}")
    print(f"             curso tecnico concluido: "
          f"{'sim' if agente.get('curso_tecnico_concluido') else 'NAO'}"
          f"   |   equipamento: "
          f"{'sim' if agente.get('equipamento_disponivel') else 'NAO'}")
    print(f"  Pacientes: {len(pacientes)}")

    print()
    print("  RECURSOS DO TURNO (parametros nossos, nao normas)")
    print(f"    fitas de glicemia por carga   : {recursos['fitas_glicemia_por_carga']}")
    print(f"    acionamentos de supervisao    : {recursos['janelas_supervisao_no_turno']}")
    print(f"    doses de alcool [sintetico]   : {recursos.get('doses_alcool_por_carga', '-')}")
    print(f"    mascaras [sintetico]          : {recursos.get('mascaras_por_carga', '-')}")
    print(f"    capacidade do coletor [sint.] : {recursos.get('capacidade_coletor', '-')}")

    print()
    print("  PACIENTES")
    print(f"    {'id':<5}{'grupo':<14}{'urg':<5}{'atraso':>7}  {'procedimentos exigidos':<30}")
    print("    " + "-" * 64)
    for p in sorted(pacientes, key=lambda x: -modelos.escore_urgencia(x, intervalo)):
        nivel = modelos.nivel_urgencia(p, intervalo)
        atraso = modelos.atraso_em_dias(p, intervalo)
        siglas = [s for campo, s in SIGLAS.items() if p.get(campo)]
        if p.get("exige_protecao_respiratoria"):
            siglas.append("[masc]")
        marca = {3: "ALTA", 2: "med", 1: "baixa"}[nivel]
        print(f"    {p['id']:<5}{(p.get('grupo') or '')[:13]:<14}{marca:<5}"
              f"{(f'+{atraso}d' if atraso > 0 else f'{atraso}d'):>7}  "
              f"{' '.join(siglas) or '(so acompanhamento)':<30}")
    print()
    print("    PA afericao de pressao | GLI glicemia capilar | TMP temperatura")
    print("    ANT antropometria | MED orientacao de medicacao | VAC caderneta")
    print("    urg = urgencia, de prioridade clinica + atraso sobre o intervalo")

    print()
    print("  MAPA (projecao aproximada, so para ver vizinhanca)")
    for linha in desenhar_mapa(dados):
        print(linha)

    pontos = [dados["ubs"]] + pacientes
    matriz, provedor = construir_matriz(pontos, "haversine")
    print(f"  Distancias por {provedor}, em minutos de caminhada.")
    print(f"  Da unidade ate cada paciente (ida):")
    distancias = sorted(((p['id'], matriz[(dados['ubs']['id'], p['id'])])
                         for p in pacientes), key=lambda x: x[1])
    linha = "    "
    for pid, minutos in distancias:
        trecho = f"{pid}={minutos}min  "
        if len(linha) + len(trecho) > 72:
            print(linha)
            linha = "    "
        linha += trecho
    if linha.strip():
        print(linha)

    if mostrar_matriz:
        print()
        print("  MATRIZ COMPLETA (minutos)")
        ids = [dados["ubs"]["id"]] + [p["id"] for p in pacientes]
        print("    " + "".join(f"{i:>6}" for i in [""] + ids))
        for a in ids:
            print(f"    {a:>6}" + "".join(f"{matriz[(a, b)]:>6}" for b in ids))
    print()
