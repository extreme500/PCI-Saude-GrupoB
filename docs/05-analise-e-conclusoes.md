# Análise consolidada e conclusões

Documento interno. Reúne os dez experimentos e tenta chegar a uma conclusão
defensável sobre o que o projeto demonstrou.

> **Como ler.** Os experimentos E1 a E6 medem o sistema. Os experimentos E7 a
> E10 foram construídos para **derrubar** o que os seis primeiros pareciam
> demonstrar. Três deles conseguiram. A conclusão final é a que sobreviveu.

Reprodução: `python -m acsplan experimentos`

> **Números refeitos com o algoritmo genético** como método de roteamento, que
> passou a ser o padrão do projeto. Nenhuma conclusão mudou de sinal.

---

## 1. O percurso

A tese inicial do projeto era a de que o Planejamento Automatizado reduziria a
ocorrência de **falsos negativos**: turnos classificados como inexequíveis
quando existe uma sequência de atendimentos válida. O E2 pareceu confirmá-la,
com 7 falsos negativos em 30 microáreas.

A ameaça à validade estava declarada desde o início: *o executor procedural
poderia ser corrigido*. Em vez de deixar a objeção como ressalva textual, ela
foi transformada em experimento.

---

## 2. As três refutações

### E7 — a correção dirigida elimina o ganho

Uma única correção manual no executor procedural (conferir os recursos ao
chegar na residência e desviar **antes** de acionar a supervisão) produziu:

| | Reativo | Corrigido |
|---|---|---|
| Falsos negativos | 9/40 (22%) | **0/40 (0%)** |
| Folga média de custo | 0,77% | 0,89% |
| Atingiu o ótimo | | 29/40 |

**O resultado principal do E2 não sobreviveu.** Uma correção de poucas linhas
zera os falsos negativos e mantém a folga de custo praticamente inalterada.

### E8 — a vantagem do algoritmo genético vinha da precedência

O E4 mostrou o AG vencendo o 2-opt em todos os tamanhos, inclusive nos
pequenos. A ablação separou os efeitos:

| N | Ganho do AG **sem** precedência | Ganho do AG **com** precedência |
|---|---|---|
| 8 | +1,4% | +7,8% |
| 16 | 0,0% | +13,5% |
| 30 | **−0,3%** | +3,1% |

Sem precedência o AG **não tem vantagem alguma**, e em N=30 chega a perder.
A hipótese levantada no E4 estava certa: o 2-opt só respeita precedência
recusando movimentos, o que o prende cedo num ótimo local.

**Consequência prática:** se o projeto abandonasse a precedência por urgência,
o algoritmo genético deveria ser abandonado junto. Vizinho mais próximo com
2-opt é cerca de cem vezes mais rápido e entrega a mesma qualidade.

### E9 — na configuração que escala, o planejamento perde em custo

O E6 mostrou que a busca ótima não cabe quando a complexidade normativa cresce:
três protocolos adicionais derrubam o limite de ~14 pacientes para menos de 6.
Em uso real a escolha seria GBFS. Comparando GBFS com o procedural **corrigido**:

| | |
|---|---|
| GBFS acima do ótimo | +4,61% |
| GBFS em relação ao procedural corrigido | **+3,49%** (pior) |
| Instâncias em que GBFS ficou pior | 16/25 |

Na única configuração que de fato escalaria, o planejamento entrega planos
**mais caros** que o executor procedural corrigido.

---

## 3. O que sobreviveu: E10

As três refutações têm um pressuposto comum: que a correção do executor
procedural, uma vez escrita, continue valendo. O E10 testa exatamente isso,
aplicando a correção do E7 ao domínio estendido, que acrescenta três recursos
finitos que não existiam quando ela foi escrita.

Com os recursos novos **escassos** (3 doses de solução alcoólica, coletor para
1, 1 máscara), em 37 instâncias com plano comprovadamente existente:

| | Falsos negativos |
|---|---|
| Executor reativo | 24/37 (65%) |
| Executor com a **correção antiga** | **24/37 (65%)** |
| Executor com uma **correção nova**, escrita sabendo das regras novas | 0/37 (0%) |
| **Planejamento, sem ajuste algum** | **0/37 (0%)** |

A correção antiga entregou **benefício zero**. Ela funcionava porque o recurso
que ela conhecia era o que restringia; quando o gargalo mudou, voltou a ser
inútil. Uma correção nova resolve, mas alguém precisou escrevê-la.

### Um defeito do nosso próprio experimento, e como foi corrigido

A primeira versão do E10 deu 0% de falsos negativos para a correção antiga, e
parecia refutar o argumento. O motivo era metodológico: ao escrever a correção,
já tínhamos incluído as checagens dos recursos do domínio estendido. **O
experimento recebia a resposta de antemão.**

A correção foi separada em duas variantes (`"legal"`, que só conhece as fitas,
e `"completo"`), e o E10 passou a usar a primeira. Vale registrar porque é o
tipo de erro que passa despercebido justamente quando o resultado agrada.

Houve ainda um segundo ajuste: com os recursos novos em folga, eles nunca
restringiam e o teste não media nada. Foi preciso torná-los escassos para que
o experimento tivesse poder de detecção.

---

## 4. Conclusão

**A tese inicial estava mal formulada.** O planejamento não vence porque o
executor procedural seja incapaz de encontrar os planos: corrigido, ele os
encontra, e ainda por cima mais barato que a busca satisfaciente (E7, E9).

A formulação que os dados sustentam é outra:

> O executor procedural depende de **alguém descobrir cada interação entre
> regras antes de respeitá-la**. O planejamento não. Ele lê as regras do
> domínio e deriva a ordem correta das pré-condições, sem que a interação
> precise ter sido antecipada por um programador.

O E10 é a medida disso: diante de regras novas, o procedural passa de 65% de
falsos negativos para 0% **apenas depois** de receber uma correção escrita
especificamente para elas. O planejador vai de 0% a 0% sem tocar em código.

### O que o trabalho pode afirmar

1. **Declaratividade com efeito mensurado.** Acrescentar regras ao domínio
   muda o comportamento sem alterar o código de busca. O custo de manter o
   equivalente procedural é uma correção nova a cada regra nova, e o E10
   quantifica o que acontece quando ela não é escrita.
2. **Prova de inviabilidade.** O planejamento distingue "não encontrei" de
   "demonstra-se que não existe", e o custo dessa prova depende do tipo de
   impossibilidade: 0 nós quando é lógica, exaustão do espaço quando é de
   recurso (E3).
3. **Otimalidade com garantia formal**, enquanto a busca ótima couber (E1).

### O que o trabalho NÃO pode afirmar

1. Que economiza tempo de deslocamento. A folga mediana é 0% (E2, E7).
2. Que encontra planos que um programa procedural não encontraria. Encontra os
   mesmos, desde que o procedural tenha sido corrigido para aquelas regras (E7).
3. Que a configuração ótima é utilizável em escala realista de complexidade
   normativa (E6).
4. Que o algoritmo genético é superior como otimizador. Ele só compensa sob
   restrições de precedência (E8).

---

## 5. Consequências para o projeto

**Reformular a pergunta de pesquisa.** Ela pergunta se o planejamento "agrega
valor mensurável". Os dados respondem: agrega, mas não na dimensão esperada.
A pergunta útil é sobre **custo de manutenção sob mudança normativa**, e é essa
que o E10 responde.

**O domínio estendido deixou de ser um acessório.** Ele é o que torna o
argumento verificável, porque fornece as "regras novas" contra as quais a
correção manual é testada. Sem ele, o E10 não existiria.

**A precedência por urgência precisa de decisão explícita.** Ela é o que
justifica o algoritmo genético (E8) e o que mais restringe o espaço de busca.
Mantê-la ou não é escolha de escopo, e as duas opções são defensáveis, mas
precisam ser declaradas.

**A verificação cruzada foi feita.** O E12 submeteu os mesmos modelos ao
pyperplan, implementação independente do grupo do Fast Downward, com
concordância total sobre viabilidade e comprimento mínimo, inclusive nos casos
inviáveis e no domínio estendido. O E10 continua sendo o resultado mais
importante do trabalho, e agora se apoia num planejador cujo comportamento foi
confirmado por uma segunda implementação.

---

## 6. Qualidade dos próprios testes

A suíte foi auditada, e dois testes **passavam por vacuidade**: usavam uma
instância fixa e saíam calados quando ela era inviável. Com a semente que estava
fixada, o executor falhava e o teste passava sem verificar coisa alguma.

Ambos passaram a varrer doze sementes e a **exigir um mínimo de casos
efetivamente exercitados**, falhando se não houver. A suíte tem hoje 19 testes,
dos quais três cobrem bugs que de fato ocorreram e um fixa uma decisão de
modelagem com base legal (o encaminhamento condicional do inciso III).

---

## 7. Ameaças à validade que permanecem

1. ~~**Planejador próprio, sem verificação cruzada.**~~ **Fechada** pelo E12:
   o pyperplan, implementação independente do grupo do Fast Downward,
   concorda em 13 de 13 instâncias sobre viabilidade e comprimento mínimo.
2. **Amostras pequenas:** 40 instâncias no E7, 37 no E10, 25 no E9, 8 por
   tamanho no E8.
3. **A "correção nova" do E10 foi escrita por nós**, que já sabíamos o modo de
   falha. Em um cenário real a descoberta seria mais cara, não mais barata,
   o que favorece o argumento, mas não foi medido.
4. **Os parâmetros de escassez do E10 foram escolhidos para que os recursos
   restringissem.** É metodologicamente necessário para o teste ter poder, e
   está declarado, mas significa que o 65% não é uma taxa esperada em operação.
5. **Um único agente**, custos de ação estimados, instâncias sintéticas.
