# Método experimental

Documento interno de trabalho. Registra as perguntas, as variáveis, o desenho
dos experimentos e as medições obtidas até agora.

> **Atenção ao usar estes números.** Eles vêm de execuções de desenvolvimento,
> com o planejador escrito pelo grupo e ainda sem verificação cruzada contra um
> planejador de referência. O documento do projeto
> ([`projeto/PROJETO-CICLO2.md`](../projeto/PROJETO-CICLO2.md)) descreve o que
> **será** medido; este arquivo registra o que já saiu do que está construído.

Reprodução: `python -m acsplan experimentos`
Saída bruta da última execução completa:
[`saida-experimentos.txt`](saida-experimentos.txt)

Os **custos** são determinísticos (mesma semente, mesmo resultado); os **tempos**
variam entre execuções conforme a carga da máquina, tipicamente na casa dos 5%.
As tabelas abaixo são de uma execução específica.

---

## Pergunta de pesquisa

> Numa arquitetura em que a rota física já está fixada por um roteirizador, o
> Planejamento Automatizado agrega algo mensurável em relação a um executor
> procedural que percorra a mesma rota cumprindo os mesmos protocolos?

A formulação admite resposta negativa, e o desenho foi feito para permitir que
ela apareça.

---

## Variáveis

- **Independentes:** número de pacientes; semente da instância; estratégia de
  busca; domínio (legal ou estendido); método de roteamento; provedor de
  distâncias; capacidade de insumos; janelas de supervisão; orçamento do turno;
  habilitação legal do agente; precedência ativa ou não.
- **Dependentes:** custo do plano (minutos); número de ações; tempo de busca;
  nós expandidos; custo da rota; cobertura de urgência e de atraso; sucesso ou
  insucesso.
- **Controladas:** mesma rota, mesmo domínio, mesmos protocolos e **mesma tabela
  de custos** para os dois grupos comparados. O executor procedural lê os custos
  do próprio `.pddl` (`custos_do_dominio()`), para eliminar divergência de
  medição.

---

## Grupo de controle

`acsplan/logica/executor_guloso.py` percorre a rota, cumpre os mesmos protocolos
legais e sintéticos, aciona supervisão, higieniza, veste máscara e reabastece
quando precisa. Não é um espantalho.

O que ele **não** faz, e é a variável isolada, é antecipar: só descobre que falta
um recurso no momento de usá-lo, e então desvia a partir da parada em que
estiver.

---

## E1 — Escalabilidade (domínio legal)

Mediana de 3 sementes por tamanho, limite de 25 s.

```
  N   ações |           A*/h_max |           A*/h_add |               GBFS
      inst. |     t(s)     custo |     t(s)     custo |     t(s)     custo
--------------------------------------------------------------------------
  4      83 |     0.05       133 |     0.01       133 |     0.02       133
  6     133 |     0.20       222 |     0.04       222 |     0.05       222
  8     191 |     0.57       279 |     0.10       299 |     0.08       290
 10     257 |     1.41       325 |     0.17       384 |     0.33       372
 12     331 |     3.22       390 |     0.25       446 |     0.27       437
 14     426 |     5.80       449 |     0.34       501 |     0.88       510
```

A busca ótima permanece viável na faixa de um turno real (10 a 15 visitas). As
satisfacientes são de 5 a 17 vezes mais rápidas e entregam planos de 10 a 20%
piores; até N=7 as três empatam, porque todas alcançam o ótimo.

Isso corrige a afirmação de que planejadores não otimizam custo: eles otimizam,
com garantia formal. O que não fazem é escalar como um solucionador de Pesquisa
Operacional dedicado.

## E2 — Planejamento × executor procedural

30 microáreas de 8 pacientes.

| Resultado | Instâncias |
|---|---|
| Planejamento achou plano mais barato | 6 |
| Empate (o procedural já era ótimo) | 17 |
| Procedural melhor que o ótimo | **0** *(teste de sanidade do h_max)* |
| **Falso negativo do procedural** | **7 de 30** |

Folga de custo do procedural: média 1,27%, **mediana 0,00%**, máxima 7,62%.

A linha "procedural melhor que o ótimo = 0" não é resultado, é verificação de
corretude: valor diferente de zero indicaria que h_max não é admissível.

**O resultado relevante são os falsos negativos.** O mecanismo é sempre o mesmo:
o procedural aciona a supervisão, só então detecta a falta de insumo, desvia até
a unidade, e o deslocamento encerra a assistência já mobilizada, consumindo dois
acionamentos na mesma residência. O planejamento deriva das pré-condições que o
desvio deve preceder o acionamento.

A proporção subiu em relação às primeiras execuções, quando o domínio modelava
apenas dois dos cinco incisos do § 4º. Com os cinco, mais pacientes exigem
supervisão e a pressão sobre esse recurso aumenta.

**Ameaça a declarar:** o executor procedural poderia ser corrigido para esse caso
específico. O argumento não é que ele seja incorrigível, e sim que cada regra
nova exigiria uma correção manual análoga, enquanto o domínio declarativo a
absorve sem alteração de código.

## E3 — Provas de inviabilidade

| Cenário | Veredito | Nós expandidos | Tempo |
|---|---|---|---|
| Agente sem curso técnico (lógica) | SEM PLANO | **0** | 0,0003 s |
| Supervisões insuficientes (recurso) | SEM PLANO | 286 | 0,117 s |

A inviabilidade lógica é detectada sem expandir um único estado: nenhuma ação
produz o fato exigido nem no problema relaxado, e como a relaxação só facilita o
problema, a impossibilidade está demonstrada. A inviabilidade por recurso é
invisível à relaxação, que ignora efeitos de remoção e não percebe o contador
decrescer; sua demonstração requer exaurir o espaço de estados.

> **Os experimentos E7 a E10, que refutam boa parte do que está abaixo, estão
> em [`05-analise-e-conclusoes.md`](05-analise-e-conclusoes.md).** Leia os dois
> documentos juntos: o E2 acima não sobreviveu ao E7, e o E4 abaixo não
> sobreviveu ao E8.

## E4 — Roteirização: algoritmo genético × vizinho mais próximo + 2-opt

Média de 5 microáreas por tamanho, camada geométrica isolada.

```
  N |           nn2opt |               AG |            diferença
    |    custo    t(s) |    custo    t(s) |       min          %
------------------------------------------------------------------
  8 |    106.0    0.00 |    101.0    0.41 |      +5.0      +4.7%
 12 |    127.8    0.00 |    124.4    0.52 |      +3.4      +2.7%
 16 |    162.6    0.00 |    139.4    0.66 |     +23.2     +14.3%
 20 |    183.8    0.00 |    168.8    0.81 |     +15.0      +8.2%
 30 |    223.6    0.01 |    213.8    1.12 |      +9.8      +4.4%
```

O AG encontra rotas mais baratas em **todos** os tamanhos testados, e a vantagem
não desaparece nas instâncias pequenas, como se esperaria se ambos alcançassem o
ótimo. A explicação provável está na precedência: o 2-opt só a respeita
*recusando* movimentos, o que o prende mais cedo num ótimo local, enquanto o AG
repara a ordem depois de cruzar e mutar.

**Isto precisa ser reexaminado** antes de virar afirmação: falta rodar com a
precedência desativada, para separar o efeito do operador do efeito da restrição.

## E5 — Política de seleção do turno

12 microáreas de 14 pacientes, orçamento de 240 min, turno médio de 6 pacientes.
A linha de base corta o turno pelo tamanho sem critério, com o **mesmo número**
de pacientes, para isolar o critério de escolha.

| Cobertura | Ordem do arquivo | Com política |
|---|---|---|
| Pacientes em atraso | 37,4% | **72,6%** |
| Urgência alta | 50,0% | **100,0%** |

## E6 — Custo da complexidade normativa

Mesma busca ótima nos dois domínios, limite de 20 s.

| N | Legal: ações / t(s) / custo | Estendido: ações / t(s) / custo |
|---|---|---|
| 3 | 61 / 0,02 / 104 | 226 / 3,79 / 110 |
| 4 | 83 / 0,05 / 132 | 275 / 10,25 / 142 |
| 5 | 107 / 0,09 / 171 | 324 / 17,47 / 183 |
| 6 | 133 / 0,17 / 202 | 373 / **estourou o limite** |

Três protocolos sintéticos derrubam o limite da busca ótima de cerca de 14
pacientes para menos de 6, um fator de aproximadamente 100 no tempo. Em uso real
isso obrigaria a trocar a garantia de otimalidade por busca satisfaciente, o que
é decisão de engenharia e não detalhe de implementação.

---

## Ameaças à validade

1. **Planejador próprio, ainda sem verificação cruzada.** A mais relevante. O
   plano é submeter os mesmos `.pddl` ao Fast Downward e comparar vereditos e
   custo ótimo.
2. **Um único agente.** Dimensionamento de equipe fora do escopo.
3. **Custos de ação estimados**, não medidos em campo.
4. **Instâncias sintéticas** variam estrutura combinatória, não representam
   prevalência epidemiológica.
5. **Amostras pequenas** (30 sementes em E2, 5 em E4, 12 em E5).
6. **E4 confunde dois efeitos** (operador e precedência), como anotado acima.
7. **O executor procedural é implementação nossa**, discutido em E2.

---

## Registro de correções

Quatro correções durante o desenvolvimento mudaram resultados e ficam
registradas, porque todas são material de discussão.

**1. Ciclo no grafo da rota.** Com a UBS como objeto único, as arestas inicial e
final fechavam um ciclo, e A\*/h_max exauria 105 mil nós sem achar plano numa
instância de 8 pacientes. Desdobrando em `ubs` e `ubs-fim`, a mesma instância
passou a ser resolvida em menos de meio segundo.

**2. Divergência de precificação entre os grupos comparados.** A ação
`retornar-a-rota` não tinha incremento explícito de custo, então o parser lhe
aplicava o custo unitário padrão de STRIPS, enquanto o executor procedural a
cobrava como zero. Foi detectada porque a diferença de custo não fechava com a
diferença de contagem de ações. A conferência "a diferença de custo bate com a
diferença de ações?" é barata e pegou um erro real.

**3. Hipótese de nomes únicos no grounding.** A instanciação descartava
combinações de parâmetros com objetos repetidos. Inofensivo até o domínio
estendido ter dois contadores do mesmo tipo na mesma ação: a glicemia consome
uma fita e ocupa espaço no coletor, e a combinação legítima `(n2, n1, n3, n2)`
era descartada por repetir `n2`, deixando a ação sem nenhuma instância válida.
O planejador passou a "provar" inviabilidade onde havia plano. **É o mais
perigoso dos quatro**, porque se manifesta como um resultado plausível em vez
de um erro visível.

**4. Linha de base inválida no E5.** A primeira versão comparava a política
contra uma fatia da própria lista de atrasados, o que não media nada.
