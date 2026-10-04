# Veredito: faz sentido usar Planning neste problema?

Documento interno. Responde diretamente à pergunta que o projeto precisa
responder, e que estava respondida pela metade até aqui.

> **Pergunta.** Planejamento Automatizado agrega alguma coisa à camada de
> protocolos, ou um algoritmo mais simples (ou até trivial) faz o mesmo, com
> desempenho igual ou melhor?

> **Números refeitos com o algoritmo genético** como método de roteamento, que
> passou a ser o padrão do projeto. Nenhuma conclusão mudou de sinal.

**Resposta curta: sim, agrega, mas não pelo motivo que o projeto vinha
alegando.** O valor está na combinação de duas coisas, e nenhuma delas
sozinha resolve o problema.

---

## 1. Por que a resposta não estava completa

Até o E10, o planejamento tinha sido comparado contra **um procedimento
escrito à mão**. Essa comparação deixa um buraco: existe uma terceira
possibilidade, que é pegar o mesmo modelo declarativo e varrê-lo com uma
**busca trivial**, sem nenhuma tecnologia de planejamento.

Se a busca cega resolvesse, o mérito do trabalho seria da modelagem
declarativa, e não do planejador. Qualquer busca completa serviria, e falar em
"Planejamento Automatizado" seria inflar o que de fato foi usado.

O E11 fecha esse buraco.

---

## 2. As três alternativas, medidas

### (A) Procedimento escrito à mão

| | |
|---|---|
| Custo dos planos | igual ou melhor que o planejador satisfaciente (E7, E9) |
| Velocidade | instantâneo, nenhuma busca |
| Falsos negativos nas regras que conhece | **0%** (E7) |
| Falsos negativos quando as regras mudam | **65%** (E10) |

Corrigido, ele é excelente **para as regras que alguém já analisou**. O
problema não é capacidade, é dependência: cada regra nova exige que uma pessoa
descubra a interação antes de codificá-la. O E10 mede o que acontece quando
isso não é feito.

### (B) Modelo declarativo + busca trivial

Busca cega sobre as **mesmas** ações instanciadas que o planejador usa. UCS é
A\* com h=0 (completa e ótima); DFS é o mais trivial que existe.

```
  N |           A*/h_max |               GBFS |          UCS (h=0) |                DFS
    |        nós   custo |        nós   custo |        nós   custo |        nós   custo
------------------------------------------------------------------------------------
  4 |        227     133 |         59     133 |      25510     133 |      16829     159
  5 |        341     182 |         80     182 |     318629  171(2) |     141341  185(2)
  6 |        662     222 |        105     222 |         --      -- |         --      --
  7 |       1275     234 |        121     234 |         --      -- |         --      --
  8 |       2563     267 |        424     278 |         --      -- |         --      --
 10 |       4798     344 |       3572     391 |         --      -- |         --      --
```

Fator de expansão sobre A\*/h_max: **UCS de 112× a 934×**, DFS de 74× a 414×.

**A busca cega morre em 5 ou 6 pacientes.** O planejador chega a 14 (E1) e,
numa execução anterior com limite maior, a 20. **Um turno real de ACS tem
ordem de 10 a 15 visitas**, ou seja, a faixa inteira de interesse prático está
fora do alcance da busca trivial e dentro do alcance do planejador.

No domínio **estendido**, onde as regras são mais ricas, a busca cega colapsa
ainda antes:

```
  N |           A*/h_max |               GBFS |          UCS (h=0) |                DFS
    |        nós   custo |        nós   custo |        nós   custo |        nós   custo
------------------------------------------------------------------------------------
  3 |       7320  110(2) |        686     187 |     341556  110(2) |     234099  214(1)
  4 |      15868  141(2) |        641     235 |         --      -- |         --      --
  5 |      23499  183(2) |        769  315(2) |         --      -- |         --      --
  6 |         --      -- |       1165  377(2) |         --      -- |         --      --
```

A busca cega resolve **apenas N=3**, e mesmo assim só em duas das três
sementes (o DFS, em uma). O GBFS chega a 6. Quanto mais regras, mais cedo o
algoritmo trivial para.

> `(N)` marca tamanhos em que só N sementes concluíram. Nesses casos as
> medianas são sobre subconjuntos diferentes e **não são comparáveis entre
> colunas**. É por isso que o DFS aparece com custo 194 em N=6: ele só resolveu
> as instâncias fáceis. No domínio estendido, o UCS aparece com custo 110
> contra 113 do A\*, o que pareceria uma contradição entre duas buscas ótimas;
> é o mesmo artefato, e foi conferido instância a instância (seção 4).

Vale registrar que a busca trivial foi implementada numa versão **favorável**:
ela herda a detecção de estados repetidos e a poda por custo do planejador. Um
DFS ingênuo de verdade iria pior.

### (C) Modelo declarativo + busca heurística (o que o projeto usa)

| | |
|---|---|
| Tamanho viável | 14 a 20 pacientes com garantia de otimalidade (E1) |
| Falsos negativos | 0%, tanto nas regras conhecidas quanto nas novas (E10) |
| Custo dos planos | ótimo com A\*/h_max; 3,49% pior que (A) com GBFS (E9) |
| Esforço quando a regra muda | zero linhas de código de busca |

---

## 3. O valor do Planning, definido

O valor **não é** nenhuma das coisas que o projeto vinha sugerindo:

- não é achar planos que um procedimento não acharia (E7 refuta);
- não é economizar deslocamento (folga mediana de 0%);
- não é ser mais rápido (o procedimento é instantâneo).

O valor é a **conjunção de duas propriedades que nenhuma alternativa tem ao
mesmo tempo**:

| | Absorve regra nova sem código? | Resolve turno de 10 a 15 visitas? |
|---|---|---|
| Procedimento à mão | **não** (65% de falsos negativos) | sim |
| Declarativo + busca trivial | sim | **não** (morre em 5 a 6) |
| **Declarativo + busca heurística** | **sim** | **sim** |

Essa é a afirmação que o trabalho pode defender, e ela é verificável nas duas
direções: tire a heurística e o método para de escalar (E11); tire a
declaratividade e o método para de absorver regras novas (E10).

### O que a contagem de linhas diz, e por que ela não serve

Medindo o custo de expressar os três protocolos sintéticos:

| | Linhas |
|---|---|
| No domínio PDDL | 113 |
| No executor procedural | ~11 |
| Código de busca alterado (lado declarativo) | **0** |

**A contagem de linhas favorece o procedimento, e por larga margem.** Reportar
só o número que convém seria desonesto.

Mas a métrica é enganosa, e o E10 mostra por quê: as 113 linhas declarativas
são **transcrição de regras**, e não exigem raciocinar sobre interação entre
elas. As ~11 linhas procedurais exigem saber *quando* conferir *o quê*, e é
exatamente esse raciocínio que falha quando as regras mudam. Escrever menos
linhas não ajuda se as linhas erradas custam 65% de falsos negativos.

---

## 4. Um ganho colateral de validade

A busca cega serviu para uma coisa que não estava prevista. **A\*/h_max e UCS
são dois algoritmos independentes**, um guiado por heurística e outro sem
nenhuma, e ambos alegam otimalidade. Submetidos às mesmas instâncias:

```
  instância    A*/h_max    UCS    DFS    veredito
  n=3 s=1           107    107    122    ótimos batem
  n=3 s=2           101    101    127    ótimos batem
  n=4 s=1           130    130    143    ótimos batem
  n=4 s=2           133    133    159    ótimos batem
  n=4 s=3           170    170    215    ótimos batem
  n=5 s=1           182    182    199    ótimos batem
```

E no domínio estendido, que é onde o bug do *grounding* havia sido corrigido e
portanto onde um erro residual seria mais provável:

```
  instância    A*/h_max    UCS    veredito
  n=3 s=1           113    113    ótimos batem
  n=3 s=2           108    108    ótimos batem
  n=3 s=3           143    143    ótimos batem
```

Concordância exata em todas, e o DFS sempre acima do ótimo, como tem de ser.

Isso é **evidência interna de que h_max é de fato admissível e de que o
grounding está correto**. Não substitui a verificação com o Fast Downward,
porque as duas buscas compartilham o mesmo parser e o mesmo grounding, mas
elimina uma classe inteira de erro: se a heurística estivesse quebrada, ou o
espaço de estados mal construído, os dois números divergiriam.

---

## 5. Consequências para o documento do projeto

**A pergunta de pesquisa deve ser reescrita.** Hoje ela pergunta se o
planejamento "agrega valor mensurável", o que admite um *sim* vazio. A
pergunta que os dados respondem é:

> Numa camada de conformidade normativa sobre rota fixa, o que é necessário
> para que o sistema continue correto quando as regras mudam, sem deixar de
> ser executável na escala de um turno real?

E a resposta medida é: modelo declarativo (senão falha com regra nova, E10) e
busca heurística (senão não escala, E11). O Planejamento Automatizado é
exatamente o nome dessa combinação.

**A justificativa ganha um argumento que ela não tinha.** Antes, a defesa do
paradigma era a forma da lei (pré-condições conjuntivas e efeito obrigatório).
Isso continua valendo, mas agora há a medição de que nem a alternativa
procedural nem a busca trivial cobrem o problema.

**Três afirmações continuam tendo de sair:** economia de deslocamento,
capacidade de encontrar planos inacessíveis a um procedimento, e superioridade
do algoritmo genético como otimizador.

---

## 6. Ameaças que permanecem

1. ~~**Fast Downward.**~~ **Fechada.** A verificação cruzada foi feita com o
   **pyperplan**, do mesmo grupo do Fast Downward (Helmert, Universidade de
   Basileia), que tem parser, grounding e busca próprios. Concordância em
   **13 de 13** instâncias, incluindo as inviáveis e o domínio estendido.
   Detalhes no experimento E12 e em `acsplan/logica/verificacao.py`.
2. **Amostras pequenas:** 3 sementes por tamanho no E11, 40 instâncias no E7 e
   no E10.
3. **A busca trivial recebeu vantagem** (dedup de estados e poda por custo), o
   que torna o resultado conservador a favor dela, não contra.
4. **Os parâmetros de escassez do E10 foram escolhidos** para que os recursos
   restringissem. Necessário para o teste ter poder, mas significa que 65% não
   é taxa esperada em operação.
5. **Um único agente**, custos de ação estimados, instâncias sintéticas.
