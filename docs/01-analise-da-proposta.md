# Análise crítica da proposta antes de implementar

**Pergunta:** a ideia final da conversa com o Gemini — usar um roteirizador
externo para fixar a ordem das visitas e deixar o *Automated Planning* cuidando
dos protocolos entre e dentro das visitas — é válida para o Ciclo 2?

**Resposta curta: sim, com duas correções obrigatórias.** A arquitetura está
correta e é defensável academicamente, mas (a) a premissa clínica usada na
conversa está factualmente errada e precisa ser trocada, e (b) do jeito que foi
descrita, o problema de planejamento seria trivial — e a objeção da
"redundância tecnológica" voltaria com força total. As duas correções estão
descritas abaixo e já estão implementadas no protótipo.

---

## 1. O que a proposta acerta

O núcleo da ideia é uma **decomposição hierárquica** clássica: dar a cada
paradigma o subproblema para o qual ele foi feito.

| Camada | Subproblema | Ferramenta | Por quê |
|---|---|---|---|
| Geométrica | em que ordem visitar | heurística de grafos (VMP + 2-opt) | espaço contínuo, métrica, ótimo aproximado barato |
| Lógica | o que fazer em cada parada | planejador STRIPS/PDDL | pré-condições encadeadas, recursos discretos, regras declarativas |

Isso é legítimo e conhecido na literatura. Dois pontos a favor:

- **Evita o gargalo real.** Forçar um planejador clássico a resolver o TSP é
  um erro conhecido, e a conversa identificou isso corretamente.
- **Dá um papel que não é decorativo ao planejador** — desde que a correção
  nº 2 abaixo seja feita.

E há um argumento a favor que a conversa com o Gemini **não** usou e que é o
mais forte de todos — está na seção 2.

---

## 2. Correção nº 1: a premissa clínica da conversa está errada

A conversa modelou o ACS aplicando insulina, fazendo "curativo cirúrgico
especial" e manipulando geladeira de vacinas. **O Agente Comunitário de Saúde
não faz nada disso.** Esses são procedimentos de técnico de enfermagem ou
enfermeiro. Apresentar esse domínio numa banca é um erro factual visível.

Mas a norma real é **melhor** para o projeto do que a versão inventada.
A Lei 11.350/2006, art. 3º § 4º (redação da Lei 13.595/2018), diz:

> "**desde que** o Agente Comunitário de Saúde **tenha concluído curso técnico**
> e **tenha disponíveis os equipamentos adequados**, são atividades do Agente,
> em sua área geográfica de atuação, **assistidas por profissional de saúde de
> nível superior, membro da equipe**:
> I – a aferição da pressão arterial, durante a visita domiciliar, em caráter
> excepcional, **encaminhando o paciente** para a unidade de saúde de referência;
> II – a medição de glicemia capilar […] **encaminhando o paciente** […]"

Leia de novo com olhos de PDDL. A lei é literalmente um esquema de ação:

```
:precondition (and (curso-tecnico-concluido ?ag)      ; "desde que tenha concluído"
                   (equipamento-disponivel ?ag)        ; "equipamentos adequados"
                   (supervisao-ativa ?ag))             ; "assistidas por profissional
                                                       ;  de nível superior"
:effect       (and (pa-ok ?p)
                   (pendencia-encaminhamento ?p))      ; "encaminhando o paciente"
```

**Esta é a melhor justificativa possível para usar Planning neste problema, e é
um argumento factual, não retórico:** a norma que rege o trabalho do ACS já tem
a forma "a ação X só é permitida se A ∧ B ∧ C, e executar X obriga Y". Traduzir
isso para STRIPS não é forçar a ferramenta — é reconhecer que o objeto de estudo
já é declarativo. Um `if/else` em Python *codifica* a regra; um domínio PDDL
*é* a regra.

Use esse argumento na fundamentação do relatório. Ele responde à pergunta
"por que Planning e não OR-Tools?" de uma forma que a banca não tem como
descartar como conveniência.

> Todo o texto legal citado, com link para a fonte primária, está em
> [`04-fontes.md`](04-fontes.md).

---

## 3. Correção nº 2: sem acoplamento entre visitas, o planejamento é trivial

Esta é a falha que a conversa com o Gemini não viu, e é a que derruba o
projeto se passar despercebida.

Se a rota está fixa **e** os protocolos são independentes por paciente, então o
problema se decompõe: cada parada vira um subproblema isolado e sequencial. Um
`for` sobre a rota resolve, e o planejador não está descobrindo nada. A objeção
da "redundância tecnológica" estaria certa.

**O que faz o planejamento deixar de ser trivial é acoplamento entre paradas.**
No protótipo esse acoplamento vem de dois recursos finitos:

1. **Fitas de glicemia** — consumíveis, só repostas na UBS. O planejador tem de
   decidir *em qual parada* vale a pena sair da rota para reabastecer, usando os
   custos de desvio reais de cada ponto.
2. **Janelas de supervisão** — o § 4º exige assistência de profissional de nível
   superior. O número de acionamentos no turno é finito, e sair da residência
   encerra a assistência em curso.

Com isso, uma decisão tomada na parada 3 torna inviável a parada 7. Isso é
exatamente o tipo de raciocínio que o planejador faz nativamente e que um laço
`for` só faz se alguém já tiver descoberto a regra e codificado à mão.

E o efeito é mensurável — não é argumento de autoridade. Ver seção 4.

---

## 4. O que a medição mostrou (e o que ela não mostra)

Rodamos o planejador ótimo contra um executor guloso honesto — o "script
simples" de Python, implementado de verdade, cumprindo os mesmos protocolos e
usando a mesma tabela de custos lida do próprio arquivo `.pddl`.

Em 30 microáreas sorteadas de 8 pacientes:

| Resultado | Instâncias |
|---|---|
| Planejador achou plano de custo menor | 11 |
| Empate (o guloso já era ótimo) | 14 |
| Guloso melhor que o ótimo | 0 *(sanidade: h_max é admissível)* |
| **Guloso declarou o turno inviável, mas existia plano válido** | **5** |

**Seja honesto no relatório sobre a primeira linha:** a folga mediana de custo
do guloso é **0%** e a média é 2,1%. Em rotas onde os insumos bastam, o guloso
acerta o ótimo. Vender "o planejador economiza tempo de deslocamento" seria
exagerar o resultado.

**O resultado que importa é a última linha.** Em 5 de 30 instâncias (17%) o
executor guloso concluiu que o turno era impossível quando existia um plano
válido. A causa é sempre a mesma, e foi verificada nos planos:

> O guloso aciona a supervisão para aferir a PA, **depois** descobre que faltam
> fitas, desvia até a UBS — e o desvio invalida a supervisão já acionada. Ele
> gasta duas janelas na mesma casa e fica sem janelas antes do fim do turno.
> O planejador deduz sozinho que basta **desviar antes de acionar a supervisão**
> e fecha o turno com uma janela por residência.

Nenhuma linha do domínio PDDL menciona essa ordem. Ela sai das pré-condições.
Essa é a resposta empírica à pergunta "o que o Planning faz que 10 linhas de
Python não fazem" — e ela tem um número associado.

Um segundo resultado, do experimento E3: o planejador **prova** inviabilidade,
enquanto o guloso só sabe dizer "não consegui". Mas o custo dessa prova depende
do tipo de inviabilidade — inviabilidade lógica (falta uma pré-condição) é
detectada em 0 nós expandidos pela relaxação; inviabilidade de recurso (acabaram
as janelas) exige exaurir o espaço de estados, porque a relaxação ignora efeitos
de remoção e não "vê" o contador baixando. Esse contraste é bom material de
discussão.

---

## 5. Onde a conversa com o Gemini exagerou — corrija antes de escrever

Três afirmações que, se forem para o relatório como estão, são atacáveis:

1. **"Planejadores buscam viabilidade, não otimização de custos."** Falso como
   afirmação geral. *Cost-optimal planning* é uma subárea consolidada (A\* com
   heurísticas admissíveis, LM-cut, busca simbólica). O próprio protótipo
   devolve planos de custo **comprovadamente mínimo** com A\*/h_max. A
   afirmação defensável é outra: planejadores não são competitivos com
   solucionadores de PO/CP dedicados em roteamento métrico, e o planejamento
   ótimo escala pior que o satisfaciente. Isso o experimento E1 mostra.

2. **"Use uma LLM para gerar a rota e o planejador para validá-la."** Aqui o
   Gemini se corrigiu sozinho e estava certo: seria redundância pura. Um laço
   sobre a matriz de adjacência valida uma rota. Essa linha foi descartada.

3. **"Planning é indispensável aqui."** Não é. É *adequado*, e o quanto ele
   agrega é uma pergunta empírica — que é justamente o que o Ciclo 2 pede que
   vocês respondam com método. Um trabalho que mede e relata "mediana 0% de
   ganho de custo, mas 17% de falsos negativos evitados" vale muito mais do que
   um que afirma superioridade sem medir.

---

## 6. Limitações honestas (declare todas no relatório)

- **Um único agente.** O enunciado menciona tamanho de equipe; o protótipo não
  trata múltiplos ACS. É a extensão natural, e é onde o problema volta a ser
  HHCRSP de verdade.
- **Prioridade e intervalo máximo entre visitas estão nos dados mas não entram
  na função objetivo.** O uso correto deles é numa etapa *anterior* ao
  roteamento: selecionar quais pacientes entram no turno. Hoje o turno atende
  todos. É a lacuna mais visível em relação ao enunciado do Ciclo 2.
- **Custos de deslocamento são estimados por haversine × 1,3 a 4,5 km/h**, não
  por API de mapas. A troca por OSRM/Google não muda nenhuma outra camada — o
  contrato entre elas é só a matriz.
- **Estoque modelado por níveis discretos**, não por fluentes numéricos, para
  manter STRIPS puro. Com capacidade grande isso incharia o domínio.
- **Planejador próprio**, não Fast Downward. Ele implementa um subconjunto de
  PDDL e é lento comparado a planejadores de produção. Os arquivos `.pddl` são
  padrão e podem ser validados em um planejador consagrado
  (`executar_fast_downward()` em `planejador.py`) — **façam isso antes da
  entrega final**; é barato e blinda o trabalho contra a crítica de que os
  resultados dependem de uma implementação caseira.
- **As instâncias sintéticas não são epidemiologicamente calibradas.** Elas
  variam a estrutura combinatória, não estimam prevalência real. Não apresente
  as proporções sorteadas como dados do SUS.

---

## 7. Veredito

A proposta é **válida e vale a pena**, desde que o relatório:

1. use a base legal real (Lei 11.350/2006 art. 3º) em vez dos protocolos
   inventados na conversa — isso é o que sustenta a escolha do paradigma;
2. mantenha o acoplamento por recursos finitos entre as paradas, porque sem ele
   o planejador não faz nada que um laço não faça;
3. relate o resultado como ele é: ganho de custo pequeno, mas eliminação de
   falsos negativos e capacidade de provar inviabilidade;
4. declare as limitações da seção 6 em vez de esperar que a banca não note.

O ponto forte do trabalho não é "usamos Planning". É **"medimos onde Planning
ajuda neste problema e onde não ajuda"** — que é exatamente o que o Ciclo 2
pede ao exigir organização pelo método científico.
