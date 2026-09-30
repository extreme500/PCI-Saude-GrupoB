"""
Algoritmo genético para a ordenação das visitas.

Por que substituir vizinho mais próximo + 2-opt
------------------------------------------------
A heurística construtiva com refinamento local é barata e boa, mas tem duas
limitações no nosso caso. A primeira é que 2-opt fica preso no primeiro
ótimo local que encontra. A segunda, e a que motivou a troca, é que ela não
sabe lidar com **restrições de precedência**: quando o nível de urgência
exige que um paciente seja atendido antes de outro, uma inversão 2-opt pode
quebrar a exigência, e não há como reparar isso sem reescrever o operador.

O algoritmo genético acomoda as duas coisas naturalmente. A população
mantém diversidade e escapa de ótimos locais, e a precedência entra como
uma etapa de reparo aplicada a todo indivíduo gerado, o que garante que
nenhuma solução inviável chegue à avaliação.

Operadores
----------
- seleção por torneio;
- cruzamento OX (*order crossover*), que preserva subsequências relativas e
  é o padrão para representações por permutação;
- mutação por inversão de segmento, que é exatamente um movimento 2-opt;
- elitismo, para não perder o melhor indivíduo entre gerações;
- reparo de precedência após cruzamento e mutação.

Para instâncias pequenas o resultado tende a empatar com vizinho mais
próximo + 2-opt, já que ambos alcançam o ótimo. A diferença aparece quando
a instância cresce ou quando há precedências a respeitar.
"""

from __future__ import annotations

import random

from .distancias import custo_da_rota


def _ordem_valida(sequencia: list[str], precede: dict[str, set[str]]) -> bool:
    vistos: set[str] = set()
    for item in sequencia:
        if any(p not in vistos for p in precede.get(item, ())):
            return False
        vistos.add(item)
    return True


def reparar_precedencia(sequencia: list[str],
                        precede: dict[str, set[str]]) -> list[str]:
    """Reordena a sequência até que toda precedência seja respeitada.

    Usa ordenação topológica estável: varre a sequência repetidamente e
    emite o primeiro elemento cujos predecessores já foram emitidos. Isso
    preserva ao máximo a ordem proposta pelo indivíduo, alterando só o que
    viola a restrição.

    Se as precedências forem contraditórias (ciclo), o que restar é emitido
    na ordem original, e a inviabilidade será detectada pela camada lógica.
    """
    if not precede:
        return sequencia
    pendentes = list(sequencia)
    emitidos: set[str] = set()
    saida: list[str] = []
    while pendentes:
        for i, item in enumerate(pendentes):
            if all(p in emitidos for p in precede.get(item, ())):
                saida.append(item)
                emitidos.add(item)
                pendentes.pop(i)
                break
        else:
            saida.extend(pendentes)  # ciclo: entrega o resto como está
            break
    return saida


def cruzamento_ox(pai: list[str], mae: list[str], sorteio: random.Random) -> list[str]:
    """Order crossover: herda um trecho do pai e completa na ordem da mãe."""
    n = len(pai)
    if n < 3:
        return pai[:]
    i, j = sorted(sorteio.sample(range(n), 2))
    filho: list[str | None] = [None] * n
    filho[i:j + 1] = pai[i:j + 1]
    herdados = set(pai[i:j + 1])
    posicao = (j + 1) % n
    for gene in mae[j + 1:] + mae[:j + 1]:
        if gene in herdados:
            continue
        filho[posicao] = gene
        posicao = (posicao + 1) % n
    return [g for g in filho if g is not None]


def mutacao_inversao(sequencia: list[str], sorteio: random.Random) -> list[str]:
    """Inverte um segmento. Equivale a um movimento 2-opt aleatório."""
    if len(sequencia) < 3:
        return sequencia
    i, j = sorted(sorteio.sample(range(len(sequencia)), 2))
    return sequencia[:i] + sequencia[i:j + 1][::-1] + sequencia[j + 1:]


def otimizar(ids_pacientes: list[str], origem: str,
             matriz: dict[tuple[str, str], int],
             precede: dict[str, set[str]] | None = None,
             *,
             tamanho_populacao: int = 60,
             geracoes: int = 300,
             taxa_mutacao: float = 0.25,
             elite: int = 4,
             torneio: int = 3,
             semente: int = 0,
             sequencia_inicial: list[str] | None = None) -> tuple[list[str], dict]:
    """Devolve (rota fechada começando e terminando em `origem`, métricas)."""
    precede = precede or {}
    sorteio = random.Random(semente)

    def rota_completa(seq: list[str]) -> list[str]:
        return [origem] + seq + [origem]

    def aptidao(seq: list[str]) -> int:
        return custo_da_rota(rota_completa(seq), matriz)

    if len(ids_pacientes) <= 2:
        seq = reparar_precedencia(list(ids_pacientes), precede)
        return rota_completa(seq), {"geracoes": 0, "avaliacoes": 0,
                                    "melhor_geracao": 0}

    # População inicial: uma semente boa (se fornecida, tipicamente a rota do
    # vizinho mais próximo) e o resto aleatório, para manter diversidade.
    populacao: list[list[str]] = []
    if sequencia_inicial:
        populacao.append(reparar_precedencia(list(sequencia_inicial), precede))
    while len(populacao) < tamanho_populacao:
        candidato = list(ids_pacientes)
        sorteio.shuffle(candidato)
        populacao.append(reparar_precedencia(candidato, precede))

    avaliacoes = 0
    melhor = min(populacao, key=aptidao)
    melhor_custo = aptidao(melhor)
    avaliacoes += len(populacao)
    melhor_geracao = 0

    for geracao in range(1, geracoes + 1):
        pontuados = sorted(populacao, key=aptidao)
        avaliacoes += len(populacao)
        nova = pontuados[:elite]

        while len(nova) < tamanho_populacao:
            def escolher() -> list[str]:
                competidores = sorteio.sample(populacao, min(torneio, len(populacao)))
                return min(competidores, key=aptidao)

            filho = cruzamento_ox(escolher(), escolher(), sorteio)
            if sorteio.random() < taxa_mutacao:
                filho = mutacao_inversao(filho, sorteio)
            nova.append(reparar_precedencia(filho, precede))

        populacao = nova
        candidato = min(populacao, key=aptidao)
        custo = aptidao(candidato)
        if custo < melhor_custo:
            melhor, melhor_custo, melhor_geracao = candidato, custo, geracao

    assert _ordem_valida(melhor, precede), "reparo de precedência falhou"
    return rota_completa(melhor), {
        "geracoes": geracoes,
        "avaliacoes": avaliacoes,
        "melhor_geracao": melhor_geracao,
        "custo": melhor_custo,
    }
