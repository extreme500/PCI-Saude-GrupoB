"""
Experimentos E7, E8 e E9: os que tentam derrubar as proprias conclusoes.

Os seis primeiros experimentos medem o sistema. Estes tres atacam o que os
seis parecem demonstrar:

E7  E se o executor procedural for corrigido? E a objecao mais forte contra o
    trabalho inteiro, e precisa ser respondida com numero, nao com argumento.
E8  A vantagem do algoritmo genetico vem do operador ou da precedencia? O E4
    deixou os dois efeitos confundidos.
E9  Na pratica se usaria busca satisfaciente, porque a otima nao escala. O
    ganho sobrevive nessa configuracao?
"""

from __future__ import annotations

import statistics

from ..dados import gerador
from ..geo import roteirizador
from ..logica import executor_guloso
from ..logica.planejador import resolver


def _ctx():
    from . import rodar
    return rodar.preparar, rodar.DOMINIOS, rodar.regua


# ---------------------------------------------------------------------------
#  E7 - e se o executor procedural for corrigido?
# ---------------------------------------------------------------------------

def experimento_e7(n_pacientes: int = 8, n_sementes: int = 40,
                   limite_segundos: float = 30.0) -> None:
    preparar, DOMINIOS, regua = _ctx()
    regua("E7 - A OBJECAO MAIS FORTE: E SE O PROCEDURAL FOR CORRIGIDO?")
    print("  O executor REATIVO so descobre que falta recurso ao usa-lo. O")
    print("  CORRIGIDO recebe UMA correcao manual dirigida ao unico modo de")
    print("  falha observado: conferir os recursos ao chegar na residencia e")
    print("  desviar ANTES de acionar a supervisao.")
    print()
    print(f"  {n_sementes} microareas de {n_pacientes} pacientes.")
    print()

    falhas_reativo = falhas_corrigido = comparaveis = sem_plano = 0
    folga_reativo: list[float] = []
    folga_corrigido: list[float] = []
    corrigido_otimo = 0

    for semente in range(1, n_sementes + 1):
        dados = gerador.gerar(n_pacientes, semente)
        roteamento, tarefa = preparar(dados, f"e7-{semente}")
        otimo = resolver(tarefa, "astar-hmax", limite_segundos=limite_segundos)
        if not otimo.sucesso:
            sem_plano += 1
            continue
        reativo = executor_guloso.executar(dados, roteamento, DOMINIOS["legal"])
        corrigido = executor_guloso.executar(dados, roteamento, DOMINIOS["legal"],
                                             antecipar="legal")
        comparaveis += 1
        if not reativo.sucesso:
            falhas_reativo += 1
        else:
            folga_reativo.append(100 * (reativo.custo - otimo.custo) / reativo.custo)
        if not corrigido.sucesso:
            falhas_corrigido += 1
        else:
            folga_corrigido.append(
                100 * (corrigido.custo - otimo.custo) / corrigido.custo)
            if corrigido.custo == otimo.custo:
                corrigido_otimo += 1

    def taxa(n: int) -> str:
        return f"{n}/{comparaveis} ({100 * n / comparaveis:.0f}%)" if comparaveis else "-"

    def media(v: list[float]) -> str:
        return f"{statistics.mean(v):.2f}%" if v else "-"

    def maximo(v: list[float]) -> str:
        return f"{max(v):.2f}%" if v else "-"

    print(f"  instancias com plano valido existente  : {comparaveis}")
    print(f"  (planejamento sem plano, descartadas)   : {sem_plano}")
    print()
    print(f"  {'':<34}{'REATIVO':>14}{'CORRIGIDO':>14}")
    print(f"  {'-' * 62}")
    print(f"  {'falsos negativos':<34}{taxa(falhas_reativo):>14}"
          f"{taxa(falhas_corrigido):>14}")
    print(f"  {'folga media de custo':<34}{media(folga_reativo):>14}"
          f"{media(folga_corrigido):>14}")
    print(f"  {'folga maxima de custo':<34}{maximo(folga_reativo):>14}"
          f"{maximo(folga_corrigido):>14}")
    if folga_corrigido:
        print(f"  {'atingiu o otimo':<34}{'':>14}"
              f"{f'{corrigido_otimo}/{len(folga_corrigido)}':>14}")
    print()
    print("  LEITURA: este experimento decide o valor do trabalho, e a resposta")
    print("  honesta pode nao ser a que se gostaria. Dois numeros importam:")
    print("  quanto a correcao recupera, e quanto ainda sobra depois dela.")


# ---------------------------------------------------------------------------
#  E8 - ablacao da precedencia
# ---------------------------------------------------------------------------

def experimento_e8(tamanhos=(8, 16, 30), n_sementes: int = 8) -> None:
    _, _, regua = _ctx()
    regua("E8 - ABLACAO: DE ONDE VEM A VANTAGEM DO ALGORITMO GENETICO")
    print("  O E4 mostrou o AG ganhando em todos os tamanhos, inclusive nos")
    print("  pequenos, onde se esperaria empate. A hipotese levantada la foi")
    print("  que a vantagem viesse da precedencia, que o 2-opt so respeita")
    print("  recusando movimentos. Aqui a precedencia e ligada e desligada.")
    print()
    print(f"  {'N':>3} | {'SEM precedencia':>25} | {'COM precedencia':>25}")
    print(f"  {'':>3} | {'nn2opt':>8}{'AG':>8}{'ganho':>9} | "
          f"{'nn2opt':>8}{'AG':>8}{'ganho':>9}")
    print("  " + "-" * 62)

    for n in tamanhos:
        celulas = []
        for precedencia in (False, True):
            c_nn, c_ag = [], []
            for semente in range(1, n_sementes + 1):
                dados = gerador.gerar(n, semente)
                r1 = roteirizador.roteirizar(dados, metodo="nn2opt",
                                             usar_precedencia=precedencia)
                r2 = roteirizador.roteirizar(dados, metodo="ag", semente=semente,
                                             usar_precedencia=precedencia)
                c_nn.append(r1["custo_rota"])
                c_ag.append(r2["custo_rota"])
            m_nn, m_ag = statistics.mean(c_nn), statistics.mean(c_ag)
            pct = 100 * (m_nn - m_ag) / m_nn if m_nn else 0.0
            celulas.append(f"{m_nn:>8.1f}{m_ag:>8.1f}{pct:>8.1f}%")
        print(f"  {n:>3} | " + " | ".join(celulas))

    print()
    print("  LEITURA: se o ganho encolher na coluna da esquerda, a vantagem do")
    print("  AG vinha mesmo da precedencia. Se persistir nas duas colunas, a")
    print("  explicacao dada no E4 estava errada e o 2-opt simplesmente para")
    print("  cedo demais.")


# ---------------------------------------------------------------------------
#  E9 - busca satisfaciente contra o procedural corrigido
# ---------------------------------------------------------------------------

def experimento_e9(n_pacientes: int = 8, n_sementes: int = 25,
                   limite_segundos: float = 30.0) -> None:
    preparar, DOMINIOS, regua = _ctx()
    regua("E9 - NA PRATICA SE USA BUSCA SATISFACIENTE. O GANHO SOBREVIVE?")
    print("  O E6 mostrou que a busca otima deixa de caber quando a")
    print("  complexidade normativa cresce. Em uso real a escolha seria GBFS.")
    print("  A comparacao justa, entao, e GBFS contra o procedural CORRIGIDO,")
    print("  que e a alternativa realista do outro lado.")
    print()

    gbfs_falhas = proc_falhas = comparaveis = gbfs_pior = 0
    gbfs_vs_otimo: list[float] = []
    gbfs_vs_proc: list[float] = []

    for semente in range(1, n_sementes + 1):
        dados = gerador.gerar(n_pacientes, semente)
        roteamento, tarefa = preparar(dados, f"e9-{semente}")
        otimo = resolver(tarefa, "astar-hmax", limite_segundos=limite_segundos)
        if not otimo.sucesso:
            continue
        satisf = resolver(tarefa, "gbfs", limite_segundos=limite_segundos)
        proc = executor_guloso.executar(dados, roteamento, DOMINIOS["legal"],
                                        antecipar="legal")
        comparaveis += 1
        if not satisf.sucesso:
            gbfs_falhas += 1
            continue
        if not proc.sucesso:
            proc_falhas += 1
            continue
        gbfs_vs_otimo.append(100 * (satisf.custo - otimo.custo) / otimo.custo)
        gbfs_vs_proc.append(100 * (satisf.custo - proc.custo) / proc.custo)
        if satisf.custo > proc.custo:
            gbfs_pior += 1

    print(f"  instancias comparaveis                     : {comparaveis}")
    print(f"  GBFS nao achou plano havendo um            : {gbfs_falhas}")
    print(f"  procedural corrigido falhou                : {proc_falhas}")
    if gbfs_vs_otimo:
        print()
        print(f"  GBFS acima do otimo (media)                : "
              f"{statistics.mean(gbfs_vs_otimo):+.2f}%")
        print(f"  GBFS em relacao ao procedural corrigido    : "
              f"{statistics.mean(gbfs_vs_proc):+.2f}%")
        print(f"  instancias em que GBFS ficou PIOR que ele  : "
              f"{gbfs_pior}/{len(gbfs_vs_proc)}")
    print()
    print("  LEITURA: se o GBFS ficar pior que o procedural corrigido, entao na")
    print("  unica configuracao que de fato escalaria o planejamento perde")
    print("  tambem em custo, e o que resta a seu favor e a garantia de achar")
    print("  plano quando existe, mais a declaratividade.")


# ---------------------------------------------------------------------------
#  E10 - a correcao manual generaliza para regras novas?
# ---------------------------------------------------------------------------

def experimento_e10(tamanhos=(4, 5, 6), n_sementes: int = 15,
                    limite_segundos: float = 30.0,
                    doses_alcool: int = 3, capacidade_coletor: int = 1,
                    mascaras: int = 1) -> None:
    """O teste decisivo depois do E7.

    A correcao do executor procedural foi derivada observando UM modo de
    falha, no dominio legal. O dominio estendido acrescenta tres recursos
    finitos que nao existiam quando essa correcao foi escrita.

    Se a correcao continuar valendo, o argumento do trabalho cai: bastaria
    corrigir o procedural uma vez. Se voltarem a aparecer falsos negativos,
    entao o que o planejamento oferece e exatamente nao precisar descobrir
    a regra antes de respeita-la.
    """
    preparar, DOMINIOS, regua = _ctx()
    regua("E10 - A CORRECAO MANUAL GENERALIZA PARA REGRAS NOVAS?")
    print("  A correcao do E7 foi escrita olhando o dominio LEGAL. Aqui ela e")
    print("  submetida ao dominio ESTENDIDO, que tem tres recursos finitos a")
    print("  mais, SEM receber nenhum ajuste novo: a variante usada confere")
    print("  apenas as fitas, que era tudo o que ela conhecia.")
    print()
    print(f"  Os recursos novos sao ESCASSOS de proposito ({doses_alcool} doses de")
    print(f"  alcool, coletor para {capacidade_coletor}, {mascaras} mascara(s)). Com")
    print("  folga eles nunca restringiriam e o teste nao mediria nada.")
    print()
    print("  O planejamento usa GBFS, porque a busca otima nao cabe neste")
    print("  dominio (E6). Achar um plano prova que o turno era exequivel.")
    print()
    print(f"  {'N':>3} | {'planeja':>8} | {'REATIVO':>14} | "
          f"{'CORRECAO ANTIGA':>16} | {'CORRECAO NOVA':>14}")
    print(f"  {'':>3} | {'ok':>8} | {'falsos neg.':>14} | "
          f"{'falsos neg.':>16} | {'falsos neg.':>14}")
    print("  " + "-" * 74)

    totais = [0, 0, 0, 0]
    for n in tamanhos:
        viaveis = fn_reativo = fn_corrigido = fn_novo = 0
        for semente in range(1, n_sementes + 1):
            dados = gerador.gerar(n, semente, doses_alcool=doses_alcool,
                                  capacidade_coletor=capacidade_coletor,
                                  mascaras=mascaras)
            roteamento, tarefa = preparar(dados, f"e10-{n}-{semente}",
                                          dominio="estendido")
            plano = resolver(tarefa, "gbfs", limite_segundos=limite_segundos)
            if not plano.sucesso:
                continue
            viaveis += 1
            reativo = executor_guloso.executar(
                dados, roteamento, DOMINIOS["estendido"], estendido=True)
            corrigido = executor_guloso.executar(
                dados, roteamento, DOMINIOS["estendido"], estendido=True,
                antecipar="legal")
            novo = executor_guloso.executar(
                dados, roteamento, DOMINIOS["estendido"], estendido=True,
                antecipar="completo")
            if not reativo.sucesso:
                fn_reativo += 1
            if not corrigido.sucesso:
                fn_corrigido += 1
            if not novo.sucesso:
                fn_novo += 1
        totais[0] += viaveis
        totais[1] += fn_reativo
        totais[2] += fn_corrigido
        totais[3] += fn_novo

        def p(x):
            return f"{x}/{viaveis} ({100*x/viaveis:.0f}%)" if viaveis else "-"

        print(f"  {n:>3} | {viaveis:>8} | {p(fn_reativo):>14} | "
              f"{p(fn_corrigido):>16} | {p(fn_novo):>14}")

    viaveis, fn_r, fn_c, fn_n = totais
    print("  " + "-" * 74)
    if viaveis:
        def t(x):
            return f"{x}/{viaveis} ({100*x/viaveis:.0f}%)"
        print(f"  {'TOT':>3} | {viaveis:>8} | {t(fn_r):>14} | "
              f"{t(fn_c):>16} | {t(fn_n):>14}")
    print()
    print("  COLUNAS: 'correcao antiga' e a do E7, que so conhece as fitas.")
    print("  'correcao nova' e a mesma ideia reescrita sabendo dos tres")
    print("  recursos acrescentados. O planejamento nao recebeu ajuste algum")
    print("  nos dois casos: ele le as regras do dominio.")
    print()
    print("  LEITURA: se a correcao antiga falhar e a nova funcionar, entao o")
    print("  executor procedural nao e incapaz, e sim DEPENDENTE de alguem")
    print("  descobrir cada interacao antes de respeita-la. E isso que o")
    print("  planejamento dispensa, e e sobre isso que a conclusao do trabalho")
    print("  deve se apoiar, nao sobre a taxa de falsos negativos isolada.")


# ---------------------------------------------------------------------------
#  E11 - um algoritmo trivial sobre o mesmo modelo faz a mesma coisa?
# ---------------------------------------------------------------------------

def experimento_e11(tamanhos=(4, 5, 6, 7, 8, 10), sementes=(1, 2, 3),
                    dominio: str = "legal", limite_segundos: float = 25.0,
                    limite_expansoes: int = 600_000) -> None:
    """Separa o valor da MODELAGEM DECLARATIVA do valor do PLANEJADOR.

    Ate aqui o planejamento foi comparado com um procedimento escrito a mao.
    Mas existe uma terceira possibilidade, que e a mais incomoda para o
    trabalho: pegar o mesmo dominio declarativo e varre-lo com uma busca
    trivial, sem nenhuma heuristica.

    Se a busca cega resolver, o merito nao e do planejador: e de ter
    modelado o problema declarativamente, e qualquer busca completa serviria.
    Se ela nao resolver, a tecnologia de planejamento esta fazendo trabalho
    que nenhum algoritmo trivial faz.

    UCS (custo uniforme, h=0) e completa e otima, e e exatamente o A* sem a
    heuristica. DFS e o mais trivial que existe. As duas operam sobre as
    MESMAS acoes instanciadas que o planejador usa.
    """
    preparar, _, regua = _ctx()
    regua(f"E11 - BUSCA CEGA x PLANEJAMENTO (dominio {dominio})")
    print("  Todas as estrategias varrem o MESMO modelo declarativo e as")
    print("  mesmas acoes instanciadas. A unica diferenca e a orientacao da")
    print("  busca. 'ucs' e A* com h=0; 'dfs' e profundidade pura.")
    print()
    print(f"  Mediana de {len(sementes)} sementes. '--' = nao concluiu em "
          f"{limite_segundos:.0f}s ou {limite_expansoes} expansoes.")
    print("  (N) ao lado do custo = so N sementes concluiram. Nesses casos a")
    print("  mediana e sobre um SUBCONJUNTO e nao e comparavel entre colunas.")
    print()
    print(f"  {'N':>3} | {'A*/h_max':>18} | {'GBFS':>18} | "
          f"{'UCS (h=0)':>18} | {'DFS':>18}")
    print(f"  {'':>3} | {'nos':>10}{'custo':>8} | {'nos':>10}{'custo':>8} | "
          f"{'nos':>10}{'custo':>8} | {'nos':>10}{'custo':>8}")
    print("  " + "-" * 84)

    estrategias = ("astar-hmax", "gbfs", "ucs", "dfs")
    resumo: dict[str, list] = {e: [] for e in estrategias}

    for n in tamanhos:
        celulas = []
        for estrategia in estrategias:
            nos, custos, ok = [], [], 0
            for semente in sementes:
                dados = gerador.gerar(n, semente)
                _, tarefa = preparar(dados, f"e11-{dominio}-{n}-{semente}",
                                     dominio=dominio)
                r = resolver(tarefa, estrategia, limite_segundos=limite_segundos,
                             limite_expansoes=limite_expansoes)
                if r.sucesso:
                    ok += 1
                    nos.append(r.expandidos)
                    custos.append(r.custo)
            if ok:
                # Quantas sementes concluiram vai junto do numero, porque
                # medianas sobre subconjuntos diferentes NAO sao comparaveis
                # entre colunas, e isso induz a erro com facilidade.
                marca = "" if ok == len(sementes) else f"({ok})"
                celulas.append(f"{statistics.median(nos):>10.0f}"
                               f"{str(int(statistics.median(custos))) + marca:>8}")
                resumo[estrategia].append((n, statistics.median(nos), ok))
            else:
                celulas.append(f"{'--':>10}{'--':>8}")
                resumo[estrategia].append((n, None, 0))
        print(f"  {n:>3} | " + " | ".join(celulas))

    print()
    print("  Fator de expansao em relacao ao A*/h_max (mediana por tamanho):")
    base = {n: v for n, v in [(x[0], x[1]) for x in resumo["astar-hmax"]] if v}
    for estrategia in ("ucs", "dfs"):
        fatores = [v / base[n] for n, v, ok in resumo[estrategia]
                   if ok and v and n in base]
        if fatores:
            print(f"    {estrategia:<5}: {min(fatores):.0f}x a {max(fatores):.0f}x")
        else:
            print(f"    {estrategia:<5}: nao concluiu em nenhum tamanho")
    print()
    print("  LEITURA: se a busca cega resolve os mesmos tamanhos, o merito e da")
    print("  modelagem declarativa e nao do planejador, e o trabalho precisa")
    print("  dizer isso. Se ela para antes, a diferenca entre os limites e")
    print("  exatamente o que a tecnologia de planejamento esta comprando.")
