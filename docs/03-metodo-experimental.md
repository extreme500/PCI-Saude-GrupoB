# Método experimental

Este documento registra as perguntas, as hipóteses, as variáveis e os
resultados obtidos, na organização que o Ciclo 2 pede (método científico).

Reprodução: `python prototipo/experimentos/rodar_experimentos.py`

---

## Pergunta de pesquisa

> Numa arquitetura em que a rota física já está fixada por um roteirizador,
> o Planejamento Automatizado agrega algo mensurável em relação a um executor
> procedural simples que percorra a mesma rota cumprindo os mesmos protocolos?

Essa formulação é deliberadamente cética. A hipótese nula é a objeção da
"redundância tecnológica": *um laço `for` faria o mesmo*.

---

## Hipóteses

| # | Hipótese | Status |
|---|---|---|
| **H1** | O plano ótimo tem custo menor que o do executor guloso quando há escassez de insumos. | **Parcialmente confirmada** — ganho existe mas é pequeno (mediana 0%). |
| **H2** | O executor guloso produz **falsos negativos**: declara inviável um turno que tem plano válido. | **Confirmada** — 5 em 30 instâncias (17%). |
| **H3** | O planejamento ótimo (heurística admissível) escala pior que o satisfaciente. | **Confirmada** — ver E1. |
| **H4** | A detecção de inviabilidade é barata quando ela é lógica e cara quando é de recurso. | **Confirmada** — 0 nós vs. 332 nós. |

---

## Variáveis

- **Independentes:** número de pacientes na microárea; semente da instância;
  estratégia de busca; capacidade de insumos; número de janelas de supervisão;
  habilitação legal do ACS.
- **Dependentes:** custo do plano (minutos); número de ações; tempo de busca;
  nós expandidos e gerados; sucesso/insucesso.
- **Controladas:** mesma rota, mesmo domínio PDDL, mesmos protocolos e
  **mesma tabela de custos** para as duas abordagens — o executor guloso lê os
  custos do próprio `dominio.pddl` (`custos_do_dominio()`), justamente para
  eliminar divergência de medição entre os grupos comparados.

---

## Grupo de controle: o executor guloso

`prototipo/camada_logica/executor_guloso.py` é o adversário honesto, não um
espantalho. Ele percorre a rota, cumpre os mesmos protocolos legais, aciona a
supervisão quando precisa e reabastece quando fica sem fitas.

O que ele **não** faz é antecipar: só descobre que precisa de insumo no momento
do uso, e resolve desviando a partir da parada em que estiver.

Essa é a diferença que o experimento isola.

---

## E1 — Escalabilidade

Mediana de 3 sementes por tamanho. Limite de 20 s para N=4..14 e de
90 s para N=15..20; nenhuma execucao atingiu o limite.

```
  N   ações |           A*/h_max |           A*/h_add |               GBFS
      inst. |     t(s)     custo |     t(s)     custo |     t(s)     custo
--------------------------------------------------------------------------
  4      67 |     0.06       153 |     0.01       153 |     0.02       153
  5      88 |     0.12       178 |     0.02       178 |     0.03       178
  6     111 |     0.27       202 |     0.05       233 |     0.04       226
  7     136 |     0.57       231 |     0.08       271 |     0.07       261
  8     163 |     0.95       268 |     0.10       298 |     0.22       332
  9     192 |     1.11       313 |     0.11       367 |     0.54       395
 10     223 |     1.70       330 |     0.13       384 |     0.32       412
 11     256 |     2.97       371 |     0.21       446 |     0.32       464
 12     291 |     2.61       377 |     0.18       465 |     0.46       430
 13     328 |     4.22       400 |     0.22       487 |     1.15       490
 14     367 |     5.40       411 |     0.26       501 |     1.00       507
 15     408 |     6.07       412 |     0.28       479 |     0.46       497
 16     451 |     8.55       422 |     0.28       492 |     0.52       510
 17     496 |     9.78       441 |     0.42       511 |     0.76       539
 18     543 |    13.27       450 |     0.47       527 |     0.96       555
 19     592 |    17.24       467 |     0.84       510 |     0.93       572
 20     643 |    22.62       535 |     1.29       593 |     2.25       655
```

**Leitura:**

- O número de ações instanciadas cresce de forma suave (≈ 26 por paciente): o
  grounding não é o gargalo. A poda por predicados estáticos (`proxima-parada`,
  `residencia-de`, `prox`) faz a maior parte do trabalho.
- **A\*/h_max** dá custo comprovadamente mínimo e **não estourou o limite em
  nenhum tamanho testado**: 0,95 s em 8 pacientes, 5,4 s em 14 e 22,6 s em 20.
  O crescimento é claramente super-linear (≈ 24× entre N=8 e N=20 para 2,5×
  mais pacientes), mas a faixa de interesse prático — um turno de ACS tem
  ordem de 10 a 15 visitas — está confortavelmente dentro do viável.
- **As buscas satisfacientes são 5 a 15× mais rápidas e entregam planos 10 a
  25% piores.** A partir de N=6 elas já não acham o ótimo.
- Isso corrige a afirmação de que "planejadores não otimizam custo": eles
  otimizam, com garantia formal — o que não fazem é escalar como um
  solucionador de PO dedicado.

## E2 — Planejador ótimo × executor guloso

30 microáreas sorteadas, 8 pacientes, 2 fitas por carga.

| Resultado | Instâncias |
|---|---|
| Planejador achou plano de custo menor | 11 |
| Empate (o guloso já era ótimo) | 14 |
| Guloso melhor que o ótimo | **0** |
| Guloso declarou inviável **havendo** plano válido | **5** |

Folga do guloso sobre o ótimo: média **2,14%**, mediana **0,00%**, máxima
**10,33%**. Maior ganho absoluto: 300 → 269 min (31 min).

**A linha "guloso melhor que o ótimo = 0" é um teste de sanidade**, não um
resultado: se fosse diferente de zero, h_max não seria admissível e o
planejador estaria errado. Vale manter no relatório como evidência de corretude.

**O resultado principal é o dos falsos negativos.** Nas 5 instâncias, o
mecanismo foi verificado nos planos e é sempre o mesmo:

> O guloso aciona a supervisão para aferir a PA, **depois** descobre que faltam
> fitas, desvia até a UBS — e o desvio invalida a supervisão já acionada.
> Gasta duas janelas na mesma residência e fica sem janelas antes do fim do
> turno. O planejador deduz que basta **desviar antes de acionar a supervisão**
> e fecha o turno com uma janela por residência.

Nenhuma linha do domínio PDDL diz em que ordem fazer isso. A ordem é deduzida
das pré-condições. É a resposta empírica — com número — à pergunta "o que o
Planning faz que 10 linhas de Python não fazem".

**Ameaça à validade a declarar:** o executor guloso poderia ser corrigido para
esse caso específico (bastaria checar o estoque antes de acionar a supervisão).
O argumento não é que o guloso seja incorrigível — é que **cada regra nova exige
uma correção manual dessas**, enquanto o domínio declarativo absorve a regra
sem mudança de código. A honestidade aqui fortalece o trabalho.

## E3 — Prova de inviabilidade

| Cenário | Planejador | Nós expandidos | Tempo | Guloso |
|---|---|---|---|---|
| (a) ACS sem curso técnico (**lógica**) | SEM PLANO | **0** | 0,0002 s | falhou |
| (b) 4 janelas para 8 residências (**recurso**) | SEM PLANO | **332** | 0,109 s | falhou |

Nos dois casos o guloso só sabe dizer "não consegui"; o planejador diz
"**é impossível**" — e essa distinção é informação gerencial (a equipe precisa
remanejar pacientes, não tentar de novo).

Mas o custo da prova depende do tipo de inviabilidade:

- **(a) lógica:** nenhuma ação do domínio relaxado produz `(pa-ok ?p)`, então
  a relaxação detecta a inalcançabilidade sem expandir um único nó.
- **(b) de recurso:** a relaxação **ignora efeitos de remoção**, logo não
  "vê" o contador de janelas baixando. A inviabilidade só aparece exaurindo o
  espaço de estados.

Esse contraste é uma propriedade conhecida das heurísticas de relaxação por
deleção, e o experimento a reproduz de forma limpa.

---

## Ameaças à validade (declarar todas)

1. **Planejador próprio.** Os números vêm de uma implementação didática, não do
   Fast Downward. Os arquivos `.pddl` são padrão; rodar uma amostra em um
   planejador consagrado (`executar_fast_downward()` em `planejador.py`) antes
   da entrega final blinda o trabalho contra essa crítica. **Pendente.**
2. **Instâncias sintéticas não calibradas.** Variam estrutura combinatória, não
   estimam prevalência real. Não apresentar as proporções como dados do SUS.
3. **Custos de ação estimados**, não medidos em campo.
4. **N pequeno** (30 sementes em E2). Suficiente para evidenciar o fenômeno,
   insuficiente para intervalo de confiança estreito.
5. **A rota é entrada, não variável.** Este experimento não avalia a qualidade
   do roteirizador; uma rota diferente muda os custos de desvio e portanto a
   magnitude dos ganhos.
6. **O guloso é uma implementação nossa.** Ver a ameaça discutida em E2.

---

## Conclusão

A hipótese nula ("um laço `for` faria o mesmo") **não se sustenta**, mas
tampouco o planejamento se justifica pelo motivo que parecia óbvio no início.
O ganho de custo é marginal (mediana 0%). O que o planejador entrega e o
executor procedural não entrega é:

1. **corretude sob escassez** — 17% de falsos negativos eliminados;
2. **prova de inviabilidade**, distinguindo "não consegui" de "é impossível";
3. **garantia de otimalidade**, quando h_max cabe no orçamento de tempo;
4. **declaratividade** — mudar a regra é editar o domínio, não o código.

É um resultado mais modesto e mais defensável do que "Planning resolve o
HHCRSP", e é o tipo de resultado que o Ciclo 2 pede.


---

## Registro de correções durante o desenvolvimento

Duas correções feitas durante a construção do protótipo merecem registro,
porque as duas mudaram resultados e as duas são material de discussão:

1. **Ciclo no grafo da rota.** Na primeira versão a UBS era um único objeto, o
   que fechava um ciclo entre a última e a primeira aresta da rota. A\*/h_max
   expandiu 105 mil nós em 60 s **sem achar plano** numa instância de 8
   pacientes. Desdobrando a UBS em `ubs` e `ubs-fim`, a mesma instância passou
   a ser resolvida em **0,46 s com 1.438 nós**. A diferença entre um modelo
   inviável e um viável foi uma decisão de modelagem, não de algoritmo.

2. **Divergência de precificação entre os grupos comparados.** A ação
   `retornar-a-rota` não tinha `(increase (total-cost) …)` explícito, então o
   parser lhe aplicava o custo unitário padrão de STRIPS (1), enquanto o
   executor guloso a cobrava como 0. Os dois grupos estavam sendo medidos com
   réguas diferentes — exatamente o tipo de erro que invalidaria a comparação.
   Foi detectado porque a diferença de custo (2 min) não fechava com a
   diferença de contagem de ações (1 acionamento de supervisão × 3 min). Após
   corrigir o domínio, os números fecham: 289 − 286 = 3 = 1 × 3.

   **Lição metodológica:** a conferência "a diferença de custo bate com a
   diferença de ações?" é barata e pegou um erro real. Vale manter como
   verificação de rotina.
