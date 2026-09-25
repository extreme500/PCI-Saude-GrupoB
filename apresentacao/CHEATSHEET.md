# CheatSheet — bibliografia e mapa do projeto

Documento de consulta rápida para os integrantes do grupo. Serve para você se
situar antes de uma reunião, de uma apresentação ou de uma sessão de escrita.

**Como usar:** a seção 1 é o resumo do projeto em meia página. A seção 2 é a
bibliografia comentada — cada entrada diz *o que o trabalho faz*, *por que ele
está aqui* e *como citá-lo no nosso texto*. A seção 3 são as fontes normativas.
A seção 4 é o glossário. A seção 5 são os números que já medimos.

> ⚠️ **Todas as referências desta lista foram conferidas em fonte primária
> (editora, DOI ou repositório oficial).** Se você acrescentar alguma, confira
> antes — bibliografia incorreta é o erro mais fácil de a banca detectar.

---

## 1. O projeto em meia página

**Contexto.** Agentes Comunitários de Saúde (ACS) fazem visitas domiciliares no
território da sua Unidade Básica de Saúde. Planejar essas visitas envolve
georreferenciamento, prioridade clínica e intervalo máximo entre visitas.

**Nosso recorte.** Um ACS, um turno, e a **rota física já definida** por um
roteirizador. A pergunta passa a ser o que fazer *dentro* e *entre* as visitas.

**A tese.** O trabalho do ACS é regido por normas que já têm forma lógica: a
Lei 11.350/2006 (art. 3º § 4º) diz que aferir pressão arterial e medir glicemia
capilar só são atividades do ACS *"desde que tenha concluído curso técnico e
tenha disponíveis os equipamentos adequados"*, *"assistidas por profissional de
saúde de nível superior"*, e obrigam o encaminhamento do paciente. Isso é,
literalmente, um esquema de ação STRIPS: pré-condições conjuntivas + efeito
obrigatório.

**A arquitetura.** Duas camadas desacopladas:

| Camada | Decide | Ferramenta |
|---|---|---|
| Geométrica | a ordem das casas | heurística de grafos (VMP + 2-opt) |
| Lógica | o que fazer em cada casa, e onde repor insumos | planejador STRIPS/PDDL |

**A pergunta cética que guia o experimento.** Com a rota já fixa, o planejador
faz algo que um laço `for` não faria? (Ver seção 5 para a resposta medida.)

---

## 2. Bibliografia comentada

### 2.1 Roteamento e escalonamento em saúde domiciliar (HHCRSP)

> Grupo que define **o problema de origem** e de onde partimos ao fazer o
> recorte. Cite estes dois ao justificar por que *não* atacamos o HHCRSP
> completo.

---

**[1] Fikar, C.; Hirsch, P. (2017).** *Home health care routing and scheduling:
A review.* Computers & Operations Research, 77, 86–95.
<https://doi.org/10.1016/j.cor.2016.07.019>

- **O que faz:** revisão de referência do HHCRSP. Mapeia os cenários tratados
  na literatura — enfermeiros roteirizados e escalonados para prestar serviços
  nas casas dos pacientes — e sistematiza modelos, restrições e métodos.
- **Por que está aqui:** é a fonte que estabelece que o problema do enunciado é
  reconhecido na literatura como combinação de *roteamento de veículos* +
  *escalonamento*, e que ele é computacionalmente pesado.
- **Como citar no nosso texto:** ao apresentar o problema geral e ao justificar
  a redução de escopo para um único agente.

---

**[2] Cissé, M.; Yalçındağ, S.; Kergosien, Y.; Şahin, E.; Lenté, C.; Matta, A.
(2017).** *OR problems related to Home Health Care: A review of relevant routing
and scheduling problems.* Operations Research for Health Care.
<https://doi.org/10.1016/j.orhc.2017.06.001>

- **O que faz:** revisa os problemas de Pesquisa Operacional ligados à saúde
  domiciliar. Caracteriza o HHCRSP como uma **extensão do VRP** com restrições
  laterais próprias do contexto — preferência do paciente e **requisitos de
  qualificação** (*skill requirements*).
- **Por que está aqui:** é a referência mais próxima da nossa tese. A literatura
  **já reconhece** que qualificação profissional é uma restrição do problema —
  mas a trata como um rótulo estático de compatibilidade (agente *i* pode
  atender paciente *j*).
- **Como citar no nosso texto:** é aqui que abrimos a lacuna. Nós tratamos a
  habilitação não como rótulo, mas como **pré-condição dinâmica encadeada**
  (curso técnico ∧ equipamento ∧ supervisão ativa), em que a supervisão é um
  **recurso finito que o deslocamento consome**. Essa é a diferença que
  justifica trazer Planejamento para o problema.

---

### 2.2 Planejamento automatizado clássico

> Grupo que fundamenta **a ferramenta**. Cite ao descrever o domínio PDDL e as
> estratégias de busca.

---

**[3] Fikes, R. E.; Nilsson, N. J. (1971).** *STRIPS: A new approach to the
application of theorem proving to problem solving.* Artificial Intelligence,
2(3–4), 189–208. <https://doi.org/10.1016/0004-3702(71)90010-5>

- **O que faz:** artigo fundador do planejamento clássico. Introduz a
  representação por **pré-condições, lista de adição e lista de remoção** — o
  formalismo que até hoje se chama "STRIPS".
- **Por que está aqui:** é a citação obrigatória ao dizer "nosso domínio é
  STRIPS puro". Também sustenta a observação de que STRIPS **não tem
  implicação**, o que nos obrigou ao truque dos predicados complementares
  (`pa-ok` em vez de `requer-pa`).
- **Como citar:** na fundamentação da modelagem.

---

**[4] Bonet, B.; Geffner, H. (2001).** *Planning as heuristic search.*
Artificial Intelligence, 129(1–2), 5–33.
<https://doi.org/10.1016/S0004-3702(01)00108-4>
PDF aberto: <https://www.cs.toronto.edu/~sheila/2542/s14/A1/bonetgeffner-heusearch-aij01.pdf>

- **O que faz:** estabelece o planejamento como **busca heurística no espaço de
  estados** e define as heurísticas derivadas da *relaxação por deleção*:
  **h_max** (admissível) e **h_add** (informativa, porém inadmissível, porque
  tende a superestimar o custo real).
- **Por que está aqui:** é a base direta das três estratégias do nosso
  planejador (A\*/h_max, A\*/h_add, GBFS). Também explica, teoricamente, por que
  o experimento E3 se comporta como se comporta: a relaxação **ignora os efeitos
  de remoção**, então nenhuma heurística dessa família "enxerga" um contador de
  recursos baixando.
- **Como citar:** ao apresentar as heurísticas, e ao discutir E1 e E3.

---

**[5] Hoffmann, J.; Nebel, B. (2001).** *The FF Planning System: Fast Plan
Generation Through Heuristic Search.* Journal of Artificial Intelligence
Research, 14, 253–302. <https://doi.org/10.1613/jair.855>

- **O que faz:** apresenta o planejador FF e a heurística **h_FF**, que estima o
  custo extraindo um *plano relaxado* (ignorando efeitos de remoção). Marco do
  planejamento satisfaciente.
- **Por que está aqui:** referência do paradigma "satisfaciente rápido × ótimo
  caro", que é exatamente o eixo do experimento E1.
- **Como citar:** ao explicar por que buscas satisfacientes são muito mais
  rápidas e entregam planos piores. *(Não implementamos h_FF; citamos como
  contexto do paradigma.)*

---

**[6] Helmert, M. (2006).** *The Fast Downward Planning System.* Journal of
Artificial Intelligence Research, 26, 191–246. <https://doi.org/10.1613/jair.1705>

- **O que faz:** descreve o Fast Downward, planejador de referência da área,
  incluindo a tradução de PDDL para representações multivaloradas.
- **Por que está aqui:** é o planejador de produção contra o qual nosso
  planejador didático deve ser validado. **Item em aberto do projeto:** rodar
  uma amostra dos nossos `.pddl` no Fast Downward para mostrar que os resultados
  não dependem da nossa implementação.
- **Como citar:** na seção de ameaças à validade.

---

**[7] Helmert, M.; Domshlak, C. (2009).** *Landmarks, Critical Paths and
Abstractions: What's the Difference Anyway?* Proceedings of ICAPS, 19(1),
162–169. <https://doi.org/10.1609/icaps.v19i1.13370>
PDF aberto: <https://ai.dmi.unibas.ch/papers/helmert-domshlak-icaps2009.pdf>

- **O que faz:** compara formalmente as famílias de heurísticas **admissíveis**
  (relaxação por deleção, caminhos críticos, abstrações, landmarks) e introduz a
  heurística **LM-cut**. Recebeu o prêmio de artigo influente do ICAPS 2020.
- **Por que está aqui:** é a prova documental contra a afirmação de que
  "planejadores não otimizam custo". **Planejamento ótimo é uma subárea
  consolidada** — nosso A\*/h_max devolve custo comprovadamente mínimo.
- **Como citar:** exatamente no ponto em que corrigimos essa afirmação.

---

### 2.3 Planejamento aplicado a protocolos de saúde

> Grupo que mostra que **nossa abordagem tem precedente na literatura** — não é
> uma ideia solta. É o grupo mais importante para a justificativa.

---

**[8] González-Ferrer, A.; ten Teije, A.; Fdez-Olivares, J.; Milian, K. (2013).**
*Automated generation of patient-tailored electronic care pathways by
translating computer-interpretable guidelines into hierarchical task networks.*
Artificial Intelligence in Medicine, 57(2), 91–109.
<https://doi.org/10.1016/j.artmed.2012.08.008>

- **O que faz:** traduz diretrizes clínicas interpretáveis por computador
  (*computer-interpretable guidelines*) para um domínio de planejamento **HTN**
  temporal, e a partir dele gera planos de cuidado personalizados por paciente.
- **Por que está aqui:** **é o precedente direto da nossa tese.** Se diretrizes
  clínicas podem virar domínio de planejamento, atribuições legais do ACS também
  podem. A diferença do nosso trabalho é a fonte da regra (norma jurídica em vez
  de diretriz clínica) e o formalismo (STRIPS em vez de HTN).
- **Como citar:** na justificativa da abordagem — é a referência que sustenta
  "isto não é forçar a ferramenta".

---

**[9] Bradbrook, K.; Winstanley, G.; Glasspool, D.; Fox, J.; Griffiths, R.
(2005).** *AI Planning Technology as a Component of Computerised Clinical
Practice Guidelines.* In: AIME 2005, LNCS 3581, Springer.
<https://doi.org/10.1007/11527770_26>

- **O que faz:** propõe o uso de tecnologia de planejamento como componente de
  diretrizes clínicas computadorizadas — geração, avaliação e manipulação de
  planos de cuidado.
- **Por que está aqui:** mostra que a ideia tem duas décadas de literatura, e
  ajuda a posicionar o trabalho historicamente.
- **Como citar:** junto com [8], ao fundamentar a escolha do paradigma.

---

### 2.4 LLM como planejador

> Grupo que fecha a porta para o caminho que consideramos e descartamos.

---

**[10] Valmeekam, K.; Marquez, M.; Sreedharan, S.; Kambhampati, S. (2023).**
*On the Planning Abilities of Large Language Models — A Critical Investigation.*
Advances in Neural Information Processing Systems (NeurIPS) 36.
<https://proceedings.neurips.cc/paper_files/paper/2023/hash/efb2072a358cefb75886a315a6fcf880-Abstract-Conference.html>

- **O que faz:** avalia sistematicamente LLMs gerando planos em domínios do tipo
  IPC. Resultado central: a capacidade de gerar planos executáveis de forma
  autônoma é **limitada** — o melhor modelo avaliado (GPT-4) teve taxa média de
  sucesso de **≈ 12%**. Também avalia LLMs como fonte de orientação heurística
  para planejadores.
- **Por que está aqui:** cogitamos usar uma LLM para gerar a rota/plano e um
  planejador para validá-la. Esta referência é a base empírica para **descartar
  a LLM como geradora de planos** e para justificar o planejador simbólico.
- **Como citar:** na discussão de alternativas consideradas.

---

### 2.5 Heurísticas de roteamento (camada geométrica)

> Citação mínima necessária. A camada geométrica **não é** o objeto de estudo.

---

**[11] Croes, G. A. (1958).** *A Method for Solving Traveling-Salesman Problems.*
Operations Research, 6(6), 791–812. <https://doi.org/10.1287/opre.6.6.791>
— origem do refino **2-opt** que usamos.

**[12] Rosenkrantz, D. J.; Stearns, R. E.; Lewis, P. M. (1977).** *An Analysis of
Several Heuristics for the Traveling Salesman Problem.* SIAM Journal on
Computing, 6(3), 563–581. <https://doi.org/10.1137/0206041>
— análise do **Vizinho Mais Próximo** e de outras heurísticas construtivas, com
garantias de aproximação.

- **Como citar:** uma linha só, ao descrever a camada geométrica. Se alguém
  perguntar "por que não OR-Tools?", a resposta é que a qualidade do roteirizador
  não é a variável do experimento — e trocá-lo não muda nenhuma outra camada.

---

## 3. Fontes normativas (não são artigos — são a base factual do domínio)

**[N1] Lei nº 11.350/2006, art. 3º**, na redação dada pela **Lei nº 13.595/2018**.
<https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13595.htm>

O dispositivo central do projeto. O **§ 4º** condiciona aferição de PA, medição
de glicemia capilar e aferição de temperatura a: curso técnico concluído,
equipamentos adequados, assistência de profissional de nível superior — e obriga
o encaminhamento à unidade de referência. O **§ 3º, II** exige o registro dos
dados da visita; o **§ 3º, IV "c" e V "c"** tratam da verificação do estado
vacinal de criança, gestante e pessoa idosa.

**[N2] PNAB — Portaria GM/MS nº 2.436/2017.**
<https://www.in.gov.br/materia/-/asset_publisher/Kujrw0TZC2Mb/content/id/19308123/do1-2017-09-22-portaria-n-2-436-de-21-de-setembro-de-2017-19308031>

Fundamenta a visita domiciliar como atividade central do ACS e a priorização por
**risco e vulnerabilidade**. ⚠️ **Cuidado:** a PNAB **não fixa** critério
numérico de periodicidade. A referência de "uma visita por família por mês" é
prática consolidada, não norma — no nosso protótipo é parâmetro configurável.

> O texto literal de tudo isso, com o mapa ação ↔ dispositivo legal, está em
> [`docs/04-fontes.md`](../docs/04-fontes.md).

---

## 4. Glossário de sobrevivência

| Termo | O que significa aqui |
|---|---|
| **ACS** | Agente Comunitário de Saúde |
| **APS / UBS / eSF** | Atenção Primária à Saúde / Unidade Básica de Saúde / equipe de Saúde da Família |
| **HHCRSP** | *Home Health Care Routing and Scheduling Problem* — o problema completo, do qual fizemos um recorte |
| **VRP / TSP** | *Vehicle Routing Problem* / *Traveling Salesman Problem* |
| **STRIPS** | *Stanford Research Institute Problem Solver* (Fikes & Nilsson, 1971). O formalismo que leva esse nome: uma ação é **pré-condições** + **lista de adição** + **lista de remoção**, e nada mais. Sem laço, sem condicional, sem aritmética. É o fragmento básico do PDDL (`:requirements :strips`) |
| **PDDL** | *Planning Domain Definition Language* — a linguagem em que escrevemos o domínio |
| **Domínio × Problema** | Domínio = as regras (ações). Problema = a instância (objetos, estado inicial, objetivo) |
| **Grounding** | Instanciar as ações com variáveis em ações concretas sem variáveis |
| **Relaxação por deleção** | Fingir que ações nunca desfazem fatos; base de h_max, h_add e h_FF |
| **Admissível** | Heurística que nunca superestima → garante plano ótimo com A\* |
| **h_max / h_add** | Admissível (ótima, lenta) / inadmissível (rápida, subótima) |
| **GBFS** | *Greedy Best-First Search* — ignora o custo já gasto; rápido e subótimo |
| **Satisfaciente** | Busca que acha *um* plano válido, sem garantir que seja o melhor |
| **Falso negativo** | Dizer "impossível" quando existe solução — o erro que medimos no executor guloso |
| **Janela de supervisão** | **Termo nosso, não da lei.** Um episódio de assistência do profissional de nível superior exigido pelo art. 3º § 4º. O agente abre com `acionar-supervisao` e ela vale só enquanto ele está naquela residência — sair da casa fecha. O número por turno é parâmetro configurável |
| **Ganho mediano de custo** | Mediana de `(custo_guloso − custo_ótimo) / custo_guloso` sobre as instâncias comparáveis. Mediana 0% = em pelo menos metade delas o guloso já achava o ótimo |

---

## 5. Os números que já temos

Medidos com o protótipo (`python prototipo/experimentos/rodar_experimentos.py`).
Detalhamento em [`docs/03-metodo-experimental.md`](../docs/03-metodo-experimental.md).

| Medida | Valor |
|---|---|
| Ganho de custo sobre o executor guloso | mediana **0%**, média 2,1%, máx. 10,3% |
| Turnos que o guloso declarou inviáveis **havendo** plano válido | **5 de 30 (17%)** |
| Guloso melhor que o ótimo | **0** *(teste de sanidade: h_max é admissível)* |
| Inviabilidade **lógica** (ACS sem curso técnico) | provada em **0 nós**, 0,2 ms |
| Inviabilidade **de recurso** (faltam janelas) | 332 nós, 109 ms |
| A\*/h_max | 0,95 s (8 casas) · 5,4 s (14) · 22,6 s (20) |

**A frase que resume o resultado:** o planejador quase não economiza
deslocamento — o que ele entrega é **corretude sob escassez**, **prova de
inviabilidade**, **garantia de otimalidade** e **declaratividade**.

**O mecanismo dos 17%** (verificado nos planos, sabê-lo de cor ajuda muito):
o guloso aciona a supervisão para aferir a PA, *depois* descobre que faltam
fitas, desvia até a UBS — e o desvio invalida a supervisão já acionada. Gasta
duas janelas na mesma casa e fica sem janelas antes do fim do turno. O
planejador deduz sozinho que basta **desviar antes de acionar a supervisão**.
Essa ordem não está escrita em nenhuma linha do domínio.

---

## 6. Perguntas que a banca provavelmente vai fazer

**"Por que não usar só OR-Tools / um solver de VRP?"**
Porque ele resolve a metade geométrica, que nós também resolvemos — e não
resolve a metade normativa. Usamos os dois, cada um no seu lugar.

**"Isso não é um `if/else` disfarçado?"**
Foi exatamente a nossa hipótese nula. Implementamos o `if/else` (o executor
guloso), medimos, e ele produziu 17% de falsos negativos. Ver seção 5.

**"Planejador não otimiza custo, só viabilidade."**
Incorreto como afirmação geral — ver [7]. Nosso A\*/h_max devolve custo mínimo
com garantia. O que planejadores não fazem é escalar como um solver dedicado.

**"Vocês usaram dados reais de pacientes?"**
Não. Pacientes, condições e datas são fictícios. Só as coordenadas são reais,
para dar ordem de grandeza à matriz de distâncias.

**"Qual é a limitação principal?"**
Um único agente, e prioridade clínica / intervalo máximo entre visitas ainda
fora da função objetivo. Ambas declaradas em
[`docs/01-analise-da-proposta.md`](../docs/01-analise-da-proposta.md), seção 6.
