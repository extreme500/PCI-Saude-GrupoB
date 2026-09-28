# Planejamento Automatizado (PDDL) para o cumprimento de protocolos legais em visitas domiciliares de Agentes Comunitários de Saúde no SUS

### Uma análise crítica da pertinência do paradigma simbólico em uma arquitetura hierárquica

**Projeto em Ciência e Inovação — INF99003 — Ciclo 2**
Gabriel Pieruccini Knopp · Arthur Andrade da Silva · Izadora Candotti de Oliveira
Grupo B — Instituto de Informática, UFRGS

---

## 1. Resumo e Palavras-Chave

**Resumo.** A Atenção Primária à Saúde no Brasil apoia-se nas visitas domiciliares
realizadas por Agentes Comunitários de Saúde (ACS), cuja atuação é normatizada pela
Lei nº 11.350/2006, na redação dada pela Lei nº 13.595/2018. Procedimentos como a
aferição de pressão arterial e a medição de glicemia capilar estão condicionados, pelo
art. 3º § 4º, à conclusão de curso técnico, à disponibilidade de equipamentos e à
assistência de profissional de saúde de nível superior, e obrigam o encaminhamento do
paciente à unidade de referência. Embora a ordem das visitas possa ser resolvida por
roteirizadores geométricos, o cumprimento dessas condições sob recursos finitos —
insumos consumíveis e disponibilidade limitada do profissional supervisor — acopla as
paradas entre si e torna o atendimento um problema combinatório que um percurso
otimizado, isoladamente, não resolve. Este projeto propõe e avalia um artefato em
arquitetura hierárquica de duas camadas: uma camada geométrica (Vizinho Mais Próximo
com refinamento 2-opt), que fixa a sequência espacial, e uma camada lógica em
Planejamento Automatizado (STRIPS/PDDL), que decide as ações em cada parada e os
desvios de reabastecimento. A avaliação é deliberadamente cética: um executor
procedural guloso, cumprindo os mesmos protocolos sob a mesma tabela de custos, atua
como grupo de controle. Espera-se demonstrar empiricamente não que o planejamento
simbólico é superior em todas as dimensões, mas *em quais dimensões* ele agrega valor
mensurável — corretude sob escassez de recursos, prova de inviabilidade e
declaratividade da norma — e em quais não agrega.

*(236 palavras)*

**Palavras-Chave:** Planejamento Automatizado; PDDL; Atenção Primária à Saúde;
Conformidade Normativa; Busca Heurística; Otimização de Rotas.

---

## 2. Introdução e Contextualização

### 2.1 O contexto

O ecossistema afetado é a **Atenção Primária à Saúde (APS) do Sistema Único de Saúde**,
especificamente o processo de trabalho das equipes de Saúde da Família (eSF). Cada
equipe é responsável por um território adscrito, subdividido em microáreas, e cada
microárea fica sob responsabilidade de um Agente Comunitário de Saúde.

A visita domiciliar é a atividade basilar desse profissional. A Política Nacional de
Atenção Básica (BRASIL, 2017) estabelece a visita como ação central do ACS e orienta
que sua periodicidade siga critérios de risco e vulnerabilidade. O agente opera com
dados clínicos da população adscrita (gestantes, pessoas idosas, pessoas com diabetes
ou hipertensão, crianças em puericultura), dados de georreferenciamento das residências
e um histórico de visitas realizadas.

Sobre esse trabalho incide uma camada normativa específica. A Lei nº 11.350/2006, na
redação dada pela Lei nº 13.595/2018, distingue dois regimes de atividade do ACS. O
art. 3º § 3º lista as **atividades típicas**, exercidas sem condicionantes — entre elas
o registro dos dados da visita (inciso II) e a verificação do estado vacinal de
crianças, gestantes e pessoas idosas (incisos IV "c" e V "c"). Já o art. 3º § 4º lista
atividades **condicionadas**, que só são atribuição do agente mediante requisitos
cumulativos.

### 2.2 O problema

O planejamento da visita domiciliar é tratado, na prática e na literatura de Pesquisa
Operacional, predominantemente como um problema de percurso: minimizar deslocamento,
cobrir o território no prazo, respeitar a capacidade da equipe. Essa formulação captura
apenas metade do problema.

A outra metade é que **chegar à residência correta não autoriza o atendimento**. Para
os procedimentos do § 4º, a permissão legal é uma conjunção de condições, e nem todas
são estáticas. O curso técnico e o equipamento não variam ao longo do turno; a
assistência do profissional de nível superior e os insumos consumíveis, sim. O agente
que gastou a última fita reagente ou já mobilizou o supervisor não perdeu sua
habilitação — mas, naquele momento e naquela residência, não pode executar o
procedimento.

Disso decorre a dor operacional central: **a incapacidade de antecipar conflitos de
recursos no decorrer do turno**. Uma decisão tomada na terceira parada — usar um insumo,
mobilizar o supervisor — pode inviabilizar a sétima. Um planejamento que trate as
paradas isoladamente, ou que otimize apenas a geometria do percurso, não enxerga esse
acoplamento. Quando o conflito se materializa, o agente é forçado a desvios não
previstos até a Unidade Básica de Saúde, com retrabalho e, no limite, com a conclusão
equivocada de que o turno é inexequível.

A pergunta que os dados ocultam, portanto, não é "qual o menor percurso", mas
**"esta sequência de atendimentos é executável sem violar a norma, dados os recursos
disponíveis — e, se não for, isso é fato demonstrável ou apenas uma falha do método de
planejamento?"**.

### 2.3 Pergunta de pesquisa e hipóteses

> **Pergunta de pesquisa.** Num contexto em que a rota física já está fixada por um
> roteirizador geométrico, o Planejamento Automatizado fundamentado em PDDL agrega
> valor mensurável em comparação a um executor procedural simples que percorra a mesma
> rota cumprindo os mesmos protocolos?

A formulação é deliberadamente neutra e admite resposta negativa. A **hipótese nula**
é a objeção da redundância tecnológica: *um laço procedural simples produziria o mesmo
resultado*. O desenho experimental (seção 6) foi construído para poder refutá-la ou
confirmá-la, e não para confirmá-la por construção.

As hipóteses de trabalho derivadas são:

| # | Hipótese |
|---|---|
| **H1** | O plano ótimo tem custo menor que o do executor guloso quando há escassez de insumos. |
| **H2** | O executor guloso produz falsos negativos: declara inviável um turno que admite plano válido. |
| **H3** | O planejamento ótimo (heurística admissível) escala pior que o satisfaciente. |
| **H4** | A detecção de inviabilidade é barata quando ela é lógica e cara quando é de recurso. |

---

## 3. Justificativa

### 3.1 Impacto prático: inovação de processo

Sob a ótica do Manual de Oslo (OCDE/EUROSTAT, 2018), o projeto caracteriza-se como uma
**inovação de processo** no setor público de saúde. O valor prático gerado não está,
como se poderia supor, na redução do tempo de deslocamento — os resultados preliminares
(seção 7) indicam que, para rotas em que os insumos são suficientes, um executor
procedural simples já alcança o percurso ótimo, e o ganho mediano de custo é nulo.

O valor está em três capacidades que o método procedural não oferece:

1. **Corretude sob escassez.** O artefato identifica sequências de atendimento
   executáveis em cenários em que o método ingênuo conclui, equivocadamente, pela
   inexequibilidade do turno.
2. **Prova de inviabilidade.** Quando o turno é de fato inexequível, o artefato
   distingue "não encontrei solução" de "demonstra-se que não existe solução". A
   segunda resposta é informação gerencial: indica à equipe que há pacientes a
   remanejar ou recursos a suprir, em vez de sugerir nova tentativa.
3. **Declaratividade da norma.** A regra sanitária fica expressa como especificação, e
   não embutida no fluxo de controle do programa. Alterações normativas passam a ser
   editadas onde a norma está escrita.

### 3.2 Impactos sociais e éticos

Os impactos a seguir são **projeções de aplicação em escala**, não resultados medidos
neste protótipo, e são declarados como tais.

A garantia de que um turno planejado é executável tende a favorecer a **equidade de
acesso**: os grupos cujo acompanhamento é normativamente exigido — gestantes, crianças,
pessoas idosas, pessoas com condições crônicas — são justamente os que dependem de
procedimentos condicionados do § 4º e, portanto, os primeiros a serem preteridos quando
um recurso se esgota no meio do turno. Um planejamento que antecipe o esgotamento reduz
essa preterição seletiva.

Em sentido oposto, há um **risco ético a declarar**: um sistema que decide a ordem e o
conteúdo do atendimento pode deslocar julgamento clínico e territorial do profissional
para uma função de custo. O artefato aqui proposto é deliberadamente um apoio à decisão
— ele não seleciona pacientes nem substitui a avaliação da equipe.

### 3.3 Pertinência do Planejamento Automatizado

A escolha do paradigma apoia-se em um argumento factual extraído da própria legislação,
e não em conveniência metodológica. O art. 3º § 4º da Lei nº 11.350/2006 (redação da
Lei nº 13.595/2018) estabelece:

> "**desde que** o Agente Comunitário de Saúde **tenha concluído curso técnico** e
> **tenha disponíveis os equipamentos adequados**, são atividades do Agente, em sua área
> geográfica de atuação, **assistidas por profissional de saúde de nível superior,
> membro da equipe**: I – a aferição da pressão arterial, durante a visita domiciliar,
> em caráter excepcional, **encaminhando o paciente** para a unidade de saúde de
> referência; II – a medição de glicemia capilar […] **encaminhando o paciente** […]"

Em termos computacionais, a norma tem a forma exata de um esquema de ação declarativo:
*a ação X só é permitida se (A ∧ B ∧ C), e executar X obriga o efeito Y*. Essa é,
literalmente, a estrutura de uma ação no formalismo STRIPS (FIKES; NILSSON, 1971):
pré-condições conjuntivas, lista de adição e lista de remoção. Um domínio PDDL
constitui, nesse caso, uma **especificação declarativa e executável da norma**.

A pertinência da Computação clássica manifesta-se ainda na natureza combinatória do
problema. Com recursos finitos repostos apenas na UBS e supervisão vinculada ao
atendimento em curso, o número de sequências de ação candidatas cresce
exponencialmente, e a interação entre decisões distantes na rota não é tratável por
inspeção manual nem por planilha.

Por fim, a arquitetura hierárquica evita o erro conhecido de submeter o problema de
percurso ao planejador simbólico. A otimização espacial — que é geométrica, contínua e
NP-difícil — é atribuída a heurísticas de grafos consagradas (CROES, 1958;
ROSENKRANTZ; STEARNS; LEWIS, 1977), enquanto o planejador responde apenas pelo
raciocínio sobre estados lógicos e recursos discretos, que é o que ele faz bem.

---

## 4. Objetivos

### 4.1 Objetivo geral

Modelar, implementar e validar um protótipo de software (TRL 3 a 4) baseado em
Planejamento Automatizado (STRIPS/PDDL) e decomposição hierárquica, destinado a
determinar as ações de atendimento e os desvios de reabastecimento que garantam o
cumprimento dos protocolos legais durante visitas domiciliares de Agentes Comunitários
de Saúde, e **mensurar em que dimensões esse paradigma supera um executor procedural
equivalente**.

### 4.2 Objetivos específicos

1. **Mapear e formalizar a norma legal.** Traduzir os §§ 3º e 4º do art. 3º da Lei
   nº 11.350/2006 (redação da Lei nº 13.595/2018) e as diretrizes da PNAB (Portaria
   GM/MS nº 2.436/2017) em esquemas de ações, pré-condições e efeitos declarativos em
   PDDL, no fragmento STRIPS com custos de ação
   (`:strips :typing :negative-preconditions :action-costs`).

2. **Construir a camada geométrica de roteamento.** Implementar o módulo de otimização
   espacial baseado na heurística do Vizinho Mais Próximo com refinamento local 2-opt,
   sobre matrizes de custo estimadas por distância haversine corrigida por fator de
   malha urbana.

3. **Desenvolver o compilador e tradutor PDDL.** Construir o módulo de geração
   automática de arquivos de problema, aplicando as técnicas de compilação de
   **polaridade invertida** para as exigências clínicas e de **desdobramento da UBS**
   (`ubs` e `ubs-fim`) para garantir aciclicidade no grafo de rota.

4. **Implementar o ambiente experimental e a linha de base.** Desenvolver um planejador
   STRIPS nativo em Python, com as buscas A\*/h_max, A\*/h_add e GBFS, e construir um
   executor guloso reativo como adversário de controle, compartilhando rigorosamente a
   mesma tabela de custos.

5. **Validar empiricamente o artefato.** Executar os experimentos controlados E1
   (escalabilidade), E2 (qualidade de plano e falsos negativos) e E3 (provas de
   inviabilidade), mensurando eliminação de erros, tempo de execução e limites de
   escalabilidade.

6. **Verificar a independência de implementação.** Submeter os mesmos arquivos de
   domínio e problema a um planejador de referência da área (Fast Downward), de modo a
   demonstrar que os resultados não dependem da implementação desenvolvida para este
   trabalho.

---

## 5. Revisão de Literatura e Soluções de Mercado

### 5.1 Fundamentação teórica

**Otimização espacial.** O problema de origem é o *Home Health Care Routing and
Scheduling Problem* (HHCRSP), extensão do Problema de Roteamento de Veículos com
restrições laterais próprias do contexto de saúde domiciliar. Duas revisões o
consolidam: FIKAR e HIRSCH (2017) sistematizam cenários, modelos e métodos; CISSÉ
*et al.* (2017) caracterizam o HHCRSP como extensão do VRP e identificam, entre as
restrições laterais, a preferência do paciente e os **requisitos de qualificação**
(*skill requirements*). Ambos registram a complexidade NP-difícil da formulação
completa.

Na camada geométrica, o refinamento 2-opt remonta a CROES (1958), e a análise das
heurísticas construtivas, incluindo o Vizinho Mais Próximo, a ROSENKRANTZ, STEARNS e
LEWIS (1977).

**Planejamento automatizado.** O formalismo empregado origina-se em FIKES e NILSSON
(1971), que introduzem a representação por pré-condições, lista de adição e lista de
remoção. BONET e GEFFNER (2001) estabelecem o planejamento como busca heurística no
espaço de estados e definem as heurísticas derivadas da relaxação por deleção: **h_max**,
admissível, e **h_add**, mais informativa porém inadmissível. HOFFMANN e NEBEL (2001)
consolidam o paradigma satisfaciente com o planejador FF. HELMERT (2006) descreve o
Fast Downward, planejador de referência da área. HELMERT e DOMSHLAK (2009) comparam
formalmente as famílias de heurísticas admissíveis e introduzem a LM-cut.

Esta última referência sustenta uma correção importante a uma objeção frequente:
**o planejamento de custo ótimo é subárea consolidada**. A afirmação defensável não é
que planejadores não otimizam custo — eles otimizam, com garantia formal —, e sim que
não escalam como solucionadores de Pesquisa Operacional dedicados.

### 5.2 Estado da arte científico

A tradução de normas de saúde para domínios de planejamento tem precedente direto na
literatura. BRADBROOK *et al.* (2005) propõem o uso de tecnologia de planejamento como
componente de diretrizes clínicas computadorizadas. GONZÁLEZ-FERRER *et al.* (2013)
vão além e traduzem diretrizes clínicas interpretáveis por computador em um domínio de
planejamento hierárquico (HTN) temporal, gerando planos de cuidado personalizados por
paciente.

Esse trabalho é a fronteira em que o presente projeto se insere. A diferença está na
**fonte da regra** — norma jurídica em vez de diretriz clínica — e no **formalismo** —
STRIPS com custos de ação em vez de HTN temporal.

Como alternativa contemporânea, considerou-se o emprego de Modelos de Linguagem de
Grande Escala como geradores de plano. VALMEEKAM *et al.* (2023) avaliam
sistematicamente essa capacidade em domínios do tipo IPC e reportam que a geração
autônoma de planos executáveis é limitada, com taxa média de sucesso de
aproximadamente 12% no melhor modelo avaliado. Essa evidência fundamentou o descarte
da alternativa para o núcleo do artefato.

### 5.3 Soluções de mercado e o que a indústria absorveu

O contraste entre a fronteira científica e a prática instalada é nítido e favorece a
proposta.

**Roteirização é tecnologia madura e amplamente absorvida.** Solucionadores como o
Google OR-Tools, serviços de matriz de distância como a Google Distance Matrix API e
motores de código aberto como o OSRM resolvem o problema geométrico em escala
industrial. Nenhum deles, contudo, raciocina sobre pré-condições normativas
encadeadas: para essas ferramentas, a compatibilidade entre profissional e paciente é
um parâmetro de entrada, não um estado que evolui durante a execução.

**Planejamento simbólico tem ferramental maduro, porém pouca penetração aplicada.** O
Fast Downward (HELMERT, 2006) é padrão de fato em pesquisa e competição, mas seu uso em
sistemas de gestão em saúde permanece restrito ao ambiente acadêmico.

**No SUS, o sistema de informação registra a visita, mas não a planeja.** O e-SUS APS,
do Ministério da Saúde, inclui o aplicativo e-SUS Território, utilizado por ACS para
cadastro territorial e registro de visitas domiciliares. A documentação oficial do
aplicativo descreve funcionalidades de coleta e qualificação de informação; não consta,
nessa documentação, funcionalidade de roteirização ou de verificação automática de
conformidade normativa dos procedimentos.

### 5.4 A lacuna

Cruzando as três frentes: a literatura de HHCRSP **já reconhece** a qualificação
profissional como restrição, mas a modela como rótulo estático de compatibilidade — o
agente *i* pode ou não atender o paciente *j*. A norma brasileira, por sua vez, define
a permissão como conjunção de condições em que **parte dos conjuntos é consumível**. As
ferramentas de mercado otimizam a geometria e ignoram a norma; os sistemas do SUS
registram a norma e ignoram a geometria.

É nessa interseção — norma consumível, tratada declarativamente, sobre rota previamente
fixada — que o projeto se posiciona.

---

## 6. Metodologia

A pesquisa segue abordagem de **Design Science** com validação experimental: constrói-se
um artefato e mede-se seu comportamento contra um grupo de controle sob variáveis
controladas.

### 6.1 Fonte de dados

O protótipo opera sobre **dados sintéticos**, por decisão metodológica e ética: dados
reais de pacientes da APS são sigilosos e seu uso exigiria aprovação em comitê de ética,
incompatível com o prazo do ciclo.

| Elemento | Origem |
|---|---|
| Identificação, condições clínicas, datas de visita | Fictícios |
| Coordenadas geográficas | Reais (região Bom Fim / Rio Branco, Porto Alegre-RS), apenas para conferir ordem de grandeza plausível à matriz de distâncias |
| Regras clínicas (quais procedimentos cada perfil exige) | Derivadas do texto legal (art. 3º §§ 3º e 4º) |
| Parâmetros de recurso e custo | Arbitrados e declarados como configuráveis |

A carga ocorre a partir de arquivo JSON estruturado. Um gerador de instâncias sintéticas
(`gerador_instancias.py`) produz microáreas parametrizadas por número de pacientes e
semente aleatória, variando a **estrutura combinatória** do problema. Registre-se que
esse gerador **não estima prevalência epidemiológica**, e suas proporções não devem ser
lidas como dados do SUS.

### 6.2 Arquitetura e algoritmia

A técnica central é a **decomposição hierárquica em duas camadas desacopladas**.

```
              dados clínicos + coordenadas
                          │
                          ▼
      ┌───────────────────────────────────────┐
      │ [1] CAMADA GEOMÉTRICA                 │
      │     haversine → Vizinho Mais Próximo  │
      │     → refinamento 2-opt               │
      └───────────────────────────────────────┘
                          │ rota fixada + matriz de custos
                          │ + custo de desvio por parada
                          ▼
      ┌───────────────────────────────────────┐
      │ [2] TRADUTOR                          │
      │     gera o problema PDDL              │
      └───────────────────────────────────────┘
                          │
                          ▼
      ┌───────────────────────────────────────┐
      │ [3] CAMADA LÓGICA                     │
      │     planejador STRIPS                 │
      │     A*/h_max · A*/h_add · GBFS        │
      └───────────────────────────────────────┘
                          │
                          ▼
             roteiro do turno + relatório
```

O contrato entre as camadas é mínimo e deliberadamente estreito: a camada geométrica
entrega apenas a ordem das paradas — congelada no predicado estático
`(proxima-parada ?l1 ?l2)` —, a matriz de custos e o custo de desvio até a UBS a partir
de cada parada. O planejador **não pode alterar a ordem**: só percorre arestas
autorizadas pelo roteirizador. Substituir a camada geométrica por OSRM ou OR-Tools não
exige alteração do domínio.

**Duas decisões de modelagem merecem registro.**

*Polaridade invertida.* STRIPS não dispõe de implicação, o que impede escrever a
pré-condição "*se* o paciente exige glicemia, *então* a medição deve estar feita".
Inverte-se a polaridade: em vez de marcar quem necessita, marca-se no estado inicial
quem já está quitado. Para um paciente que não exige o procedimento, `(glicemia-ok ?p)`
já nasce verdadeiro; para quem exige, apenas a ação correspondente o produz.

*Desdobramento da UBS.* A rota é um tour fechado. Representada a UBS por objeto único,
as arestas inicial e final fechariam um ciclo, permitindo ao planejador percorrer a rota
indefinidamente. Desdobra-se a unidade em `ubs` (partida) e `ubs-fim` (chegada e
reposição) — fisicamente a mesma UBS —, tornando o grafo acíclico. Essa alteração foi
determinante: registrou-se, antes dela, exaustão de 105 mil nós em 60 s sem plano numa
instância de 8 pacientes; após o desdobramento, a mesma instância foi resolvida em
0,48 s com 1.446 nós.

**Delimitação entre norma e modelagem.** O art. 3º § 4º exige assistência de
profissional de nível superior, sem estipular sua forma, duração ou frequência. São
**decisões de modelagem deste trabalho**, e não determinações legais: (i) representar
essa assistência como recurso discreto e finito por turno; (ii) encerrá-la quando o
agente deixa a residência. Ambas são parametrizáveis e estão declaradas como tais.

### 6.3 Ambiente de desenvolvimento

| Item | Escolha |
|---|---|
| Linguagem | Python 3.10+ |
| Dependências externas | **Nenhuma** — apenas biblioteca padrão |
| Formalismo | PDDL, fragmento `:strips :typing :negative-preconditions :action-costs` |
| Planejador | Implementação própria: parser PDDL, *grounding* com poda por predicados estáticos, A\* e GBFS |
| Planejador de referência (verificação) | Fast Downward (execução pendente — ver 6.4) |
| Versionamento | Git |

A ausência de dependências é decisão de projeto: garante reprodutibilidade em qualquer
máquina com Python, sem compilação. Justifica-se, com isso, a implementação de
planejador próprio em lugar do uso direto do Fast Downward, que exige compilação C++ e
não executa nativamente em Windows.

### 6.4 Plano de validação

A validação combina **demonstração prática**, **experimentação controlada**,
**teste de casos extremos** e **verificação cruzada de implementação**.

**Grupo de controle.** O executor guloso (`executor_guloso.py`) percorre a mesma rota,
cumpre os mesmos protocolos, aciona supervisão quando necessário e reabastece quando
fica sem insumo. Não é um espantalho: é a materialização da hipótese nula. Para eliminar
divergência de medição entre os grupos comparados, **ele lê a tabela de custos do
próprio arquivo de domínio PDDL**. O que ele não faz — e é essa a variável isolada pelo
experimento — é antecipar: só detecta a falta de insumo no momento do uso.

**Variáveis.**

- *Independentes:* número de pacientes; semente da instância; estratégia de busca;
  capacidade de insumos; número de acionamentos de supervisão; habilitação legal do
  agente.
- *Dependentes:* custo do plano (minutos); número de ações; tempo de busca; nós
  expandidos e gerados; sucesso ou insucesso.
- *Controladas:* mesma rota, mesmo domínio, mesmos protocolos e mesma tabela de custos.

**Experimentos.**

| Exp. | Pergunta | Desenho |
|---|---|---|
| **E1** | Até que tamanho cada estratégia de busca permanece viável? | N = 4 a 20 pacientes, 3 sementes por tamanho, três estratégias, mediana das execuções |
| **E2** | O planejador supera o executor procedural? | 30 microáreas sorteadas de 8 pacientes; comparação de custo, de número de ações e de taxa de falha |
| **E3** | O artefato reconhece a inviabilidade? A que custo? | Dois cenários extremos: inviabilidade *lógica* (agente sem curso técnico) e de *recurso* (supervisões insuficientes) |

E3 constitui o teste de casos extremos exigido pelo plano de validação: são instâncias
construídas para não admitirem solução.

**Verificação de implementação (pendente).** Todos os números provêm de um planejador
escrito para este trabalho. Trata-se da principal ameaça à validade interna, e o plano
para fechá-la é submeter os mesmos arquivos `.pddl`, sem adaptação, ao Fast Downward
com configuração ótima (`--search "astar(lmcut())"`), comparando três resultados: se o
domínio é aceito, se os vereditos de viabilidade coincidem — inclusive os negativos de
E3 — e se **o custo ótimo é numericamente idêntico**. Esta última é decisiva: duas
implementações independentes que alegam otimalidade devem convergir no mesmo valor.
Complementarmente, prevê-se o uso do validador VAL para conferir, passo a passo, a
validade dos planos emitidos.

**Análise de complexidade.** O *grounding* é O(|A| · |O|^k), com |A| esquemas de ação,
|O| objetos e k a maior aridade de parâmetros; a poda por predicados estáticos —
`proxima-parada`, `residencia-de`, `prox`, `desvio-ubs` — reduz drasticamente o termo
dominante, o que é confirmado empiricamente pelo crescimento aproximadamente linear do
número de ações instanciadas em E1 (≈ 26 por paciente). O custo da busca, esse sim,
cresce de forma super-linear e é o objeto de E1.

---

## 7. Resultados Esperados

O projeto situa-se em TRL 3 a 4: protótipo funcional validado em laboratório, não
produto. A entrega compõe-se de artefato executável, corpo de evidência experimental e
documentação técnica.

### 7.1 Resultados já obtidos

Os experimentos foram executados e os valores abaixo são **medidos**, não projetados.
Reprodução: `python prototipo/experimentos/rodar_experimentos.py`.

**E1 — Escalabilidade.** Mediana de 3 sementes por tamanho; nenhuma execução atingiu o
limite de tempo.

| N pacientes | Ações instanciadas | A\*/h_max | A\*/h_add | GBFS |
|---|---|---|---|---|
| 8 | 163 | 0,95 s · custo 268 | 0,10 s · 298 | 0,22 s · 332 |
| 14 | 367 | 5,40 s · custo 411 | 0,26 s · 501 | 1,00 s · 507 |
| 20 | 643 | 22,62 s · custo 535 | 1,29 s · 593 | 2,25 s · 655 |

A busca ótima permanece viável em toda a faixa de interesse prático — um turno de ACS
tem ordem de 10 a 15 visitas. As buscas satisfacientes são de 5 a 15 vezes mais rápidas
e entregam planos de 10% a 25% piores. **H3 confirmada.**

**E2 — Planejador ótimo × executor guloso.** 30 microáreas de 8 pacientes.

| Resultado | Instâncias |
|---|---|
| Planejador obteve plano de custo menor | 11 |
| Empate (o guloso já era ótimo) | 14 |
| Guloso superou o ótimo | **0** *(teste de sanidade)* |
| Guloso declarou inviável **havendo** plano válido | **5** |

Folga do guloso sobre o ótimo: média 2,14%, **mediana 0,00%**, máxima 10,33%; maior
ganho absoluto de 300 para 269 minutos.

A mediana nula **refuta H1 em sua forma forte**: em rotas com insumo suficiente, o
método procedural já alcança o ótimo. O resultado relevante é o dos falsos negativos —
17% das instâncias —, cujo mecanismo foi verificado nos planos: o executor aciona a
supervisão, só então detecta a falta de insumo, desvia até a UBS, e o deslocamento
encerra a assistência já mobilizada, consumindo dois acionamentos na mesma residência.
O planejador deriva das pré-condições que o desvio deve preceder o acionamento.
**H2 confirmada.**

A linha "guloso superou o ótimo = 0" não é resultado, e sim verificação de corretude:
valor diferente de zero indicaria que h_max não é admissível.

**E3 — Prova de inviabilidade.**

| Cenário | Veredito | Nós expandidos | Tempo |
|---|---|---|---|
| Agente sem curso técnico (lógica) | SEM PLANO | **0** | 0,0002 s |
| Supervisões insuficientes (recurso) | SEM PLANO | 332 | 0,109 s |

A inviabilidade lógica é detectada sem expandir um único estado: nenhuma ação produz o
fato exigido sequer no problema relaxado, e como a relaxação apenas facilita o problema,
a impossibilidade é demonstrada. Já a inviabilidade por recurso é invisível à relaxação,
que ignora efeitos de remoção e não percebe o contador decrescer; sua demonstração
requer exaurir o espaço de estados. **H4 confirmada.**

### 7.2 Resultados ainda esperados

1. Concordância do Fast Downward com os vereditos e os custos ótimos, em amostra de
   instâncias (objetivo específico 6).
2. Validação dos planos emitidos pelo VAL.
3. Relatório técnico consolidando os ganhos qualitativos projetados para aplicação em
   escala.

### 7.3 Ameaças à validade

Declaram-se as seguintes limitações:

1. **Implementação própria não verificada externamente** — a mais relevante; plano de
   mitigação em 6.4.
2. **Agente único.** O dimensionamento de equipe, previsto no enunciado, não é tratado;
   sua inclusão reconduziria o problema ao HHCRSP completo.
3. **Prioridade clínica e intervalo máximo entre visitas** constam dos dados, mas não
   integram a função objetivo nem a seleção do turno. É a lacuna mais visível frente ao
   enunciado do ciclo.
4. **Custos estimados, não medidos em campo**; distâncias por haversine corrigido, não
   por malha viária real.
5. **Amostra de 30 sementes em E2** — suficiente para evidenciar o fenômeno, insuficiente
   para intervalo de confiança estreito.
6. **O executor guloso poderia ser corrigido** para o caso específico observado. O
   argumento não é sua incorrigibilidade, e sim que cada nova regra exigiria correção
   manual análoga, enquanto o domínio declarativo a absorve sem alteração de código.

### 7.4 Registro de correções metodológicas

Duas correções durante o desenvolvimento alteraram resultados e são registradas por
rigor.

A primeira foi o ciclo no grafo de rota, descrito em 6.2. A segunda foi uma
**divergência de precificação entre os grupos comparados**: a ação `retornar-a-rota`
não declarava incremento explícito de custo, recebendo o custo unitário padrão de
STRIPS, enquanto o executor guloso a contabilizava como nula. Os dois grupos estavam
sendo medidos com réguas distintas. A falha foi detectada porque a diferença de custo
observada não se conciliava com a diferença de contagem de ações — verificação que se
recomenda como rotina.

---

## 8. Cronograma

Atividades mapeadas nos meses do semestre 2026/2. **A adequar ao calendário efetivo da
disciplina.** Legenda: ● concluído · ◐ em andamento · ○ previsto.

| # | Atividade | Ago | Set | Out | Nov | Dez |
|---|---|:---:|:---:|:---:|:---:|:---:|
| 1 | Delimitação do problema e revisão bibliográfica | ● | ● | | | |
| 2 | Mapeamento da norma legal em esquemas de ação (OE 1) | | ● | | | |
| 3 | Camada geométrica de roteamento (OE 2) | | ● | | | |
| 4 | Compilador e tradutor PDDL (OE 3) | | ● | | | |
| 5 | Planejador STRIPS e executor de controle (OE 4) | | ● | | | |
| 6 | Experimentos E1, E2 e E3 (OE 5) | | ● | | | |
| 7 | Verificação cruzada no Fast Downward e VAL (OE 6) | | | ◐ | | |
| 8 | Seleção do turno por prioridade e intervalo | | | ○ | ○ | |
| 9 | Extensão a múltiplos agentes (se houver folga) | | | | ○ | |
| 10 | Redação do documento do projeto | | ◐ | ◐ | ○ | |
| 11 | Apresentação do Ciclo 2 | | | ● | | |
| 12 | Crítica, reflexão e consolidação final | | | | ○ | ○ |

---

## 9. Referências Bibliográficas

BONET, B.; GEFFNER, H. Planning as heuristic search. **Artificial Intelligence**,
v. 129, n. 1-2, p. 5-33, 2001. DOI: 10.1016/S0004-3702(01)00108-4.

BRADBROOK, K.; WINSTANLEY, G.; GLASSPOOL, D.; FOX, J.; GRIFFITHS, R. AI Planning
Technology as a Component of Computerised Clinical Practice Guidelines. In:
**Artificial Intelligence in Medicine (AIME 2005)**. Lecture Notes in Computer Science,
v. 3581. Berlin: Springer, 2005. DOI: 10.1007/11527770_26.

BRASIL. **Lei nº 11.350, de 5 de outubro de 2006.** Regulamenta o § 5º do art. 198 da
Constituição, dispõe sobre o aproveitamento de pessoal amparado pelo parágrafo único do
art. 2º da Emenda Constitucional nº 51, de 14 de fevereiro de 2006. Brasília, 2006.

BRASIL. **Lei nº 13.595, de 5 de janeiro de 2018.** Altera a Lei nº 11.350, de 5 de
outubro de 2006, para dispor sobre a reformulação das atribuições, a jornada e as
condições de trabalho dos Agentes Comunitários de Saúde e dos Agentes de Combate às
Endemias. Brasília, 2018. Disponível em:
https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13595.htm.
Acesso em: 22 set. 2026.

BRASIL. Ministério da Saúde. **Portaria GM/MS nº 2.436, de 21 de setembro de 2017.**
Aprova a Política Nacional de Atenção Básica. Brasília: Diário Oficial da União, 2017.
Disponível em: https://www.in.gov.br/materia/-/asset_publisher/Kujrw0TZC2Mb/content/id/19308123.
Acesso em: 22 set. 2026.

BRASIL. Ministério da Saúde. **e-SUS Atenção Primária à Saúde: manual de utilização do
aplicativo e-SUS APS Território.** Brasília, [s.d.]. Disponível em:
https://sisaps.saude.gov.br/esus/upload/docs/manual_utilizacao_aplicativo_esus_aps_territorio.pdf.
Acesso em: 28 set. 2026.

CISSÉ, M.; YALÇINDAĞ, S.; KERGOSIEN, Y.; ŞAHIN, E.; LENTÉ, C.; MATTA, A. OR problems
related to Home Health Care: A review of relevant routing and scheduling problems.
**Operations Research for Health Care**, 2017. DOI: 10.1016/j.orhc.2017.06.001.

CROES, G. A. A Method for Solving Traveling-Salesman Problems. **Operations Research**,
v. 6, n. 6, p. 791-812, 1958. DOI: 10.1287/opre.6.6.791.

FIKAR, C.; HIRSCH, P. Home health care routing and scheduling: A review.
**Computers & Operations Research**, v. 77, p. 86-95, 2017.
DOI: 10.1016/j.cor.2016.07.019.

FIKES, R. E.; NILSSON, N. J. STRIPS: A new approach to the application of theorem
proving to problem solving. **Artificial Intelligence**, v. 2, n. 3-4, p. 189-208, 1971.
DOI: 10.1016/0004-3702(71)90010-5.

GONZÁLEZ-FERRER, A.; TEN TEIJE, A.; FDEZ-OLIVARES, J.; MILIAN, K. Automated generation
of patient-tailored electronic care pathways by translating computer-interpretable
guidelines into hierarchical task networks. **Artificial Intelligence in Medicine**,
v. 57, n. 2, p. 91-109, 2013. DOI: 10.1016/j.artmed.2012.08.008.

HELMERT, M. The Fast Downward Planning System. **Journal of Artificial Intelligence
Research**, v. 26, p. 191-246, 2006. DOI: 10.1613/jair.1705.

HELMERT, M.; DOMSHLAK, C. Landmarks, Critical Paths and Abstractions: What's the
Difference Anyway? In: **Proceedings of the International Conference on Automated
Planning and Scheduling (ICAPS)**, v. 19, n. 1, p. 162-169, 2009.
DOI: 10.1609/icaps.v19i1.13370.

HOFFMANN, J.; NEBEL, B. The FF Planning System: Fast Plan Generation Through Heuristic
Search. **Journal of Artificial Intelligence Research**, v. 14, p. 253-302, 2001.
DOI: 10.1613/jair.855.

OCDE; EUROSTAT. **Manual de Oslo 2018: diretrizes para a coleta, o relato e o uso de
dados sobre inovação.** 4. ed. Paris: OECD Publishing, 2018.
DOI: 10.1787/9789264304604-en.

ROSENKRANTZ, D. J.; STEARNS, R. E.; LEWIS, P. M. An Analysis of Several Heuristics for
the Traveling Salesman Problem. **SIAM Journal on Computing**, v. 6, n. 3, p. 563-581,
1977. DOI: 10.1137/0206041.

VALMEEKAM, K.; MARQUEZ, M.; SREEDHARAN, S.; KAMBHAMPATI, S. On the Planning Abilities
of Large Language Models – A Critical Investigation. In: **Advances in Neural
Information Processing Systems (NeurIPS)**, v. 36, 2023. Disponível em:
https://proceedings.neurips.cc/paper_files/paper/2023/hash/efb2072a358cefb75886a315a6fcf880-Abstract-Conference.html.
Acesso em: 22 set. 2026.

**Ferramentas e bibliotecas**

GOOGLE. **OR-Tools: routing library.** Disponível em:
https://developers.google.com/optimization/routing. Acesso em: 28 set. 2026.

PROJECT OSRM. **Open Source Routing Machine.** Disponível em: https://project-osrm.org.
Acesso em: 28 set. 2026.

PYTHON SOFTWARE FOUNDATION. **Python Language Reference, version 3.10.** Disponível em:
https://docs.python.org/3/reference. Acesso em: 28 set. 2026.

---

## Apêndice — Repositório e reprodução

Código, domínio PDDL, dados e documentação técnica:
`https://github.com/extreme500/PCI-Saude-GrupoB`, branch `feat/prototipo-planning`.

```bash
python prototipo/orquestrador.py                       # pipeline completo
python prototipo/orquestrador.py --sem-curso-tecnico   # teste de declaratividade
python prototipo/experimentos/rodar_experimentos.py    # E1, E2 e E3
```

Documentação de apoio: `docs/01-analise-da-proposta.md` (análise crítica e limitações),
`docs/02-modelagem-pddl.md` (decisões de modelagem), `docs/03-metodo-experimental.md`
(método e resultados completos), `docs/04-fontes.md` (texto literal das normas, com a
separação entre norma, parâmetro e ficção).
