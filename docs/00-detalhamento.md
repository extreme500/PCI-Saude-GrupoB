# Análise Crítica e Aplicação do Planejamento Automatizado (PDDL) no Agendamento e Cumprimento de Protocolos Clínicos por Agentes Comunitários de Saúde no SUS

**Resumo:** A Atenção Primária à Saúde no Brasil fundamenta-se nas visitas domiciliares realizadas pelos Agentes Comunitários de Saúde (ACS). A Lei nº 11.350/2006 estabelece pré-condições legais para procedimentos como aferição de pressão arterial e glicemia capilar, exigindo curso técnico, equipamentos e assistência ou supervisão de profissional de nível superior. Embora a ordem das visitas possa ser definida por roteirizadores geométricos, as restrições de recursos finitos e de supervisão tornam o atendimento um problema combinatório. Este projeto propõe um protótipo baseado em decomposição hierárquica em duas camadas: uma geométrica (Vizinho Mais Próximo + 2-opt), responsável pela sequência espacial, e outra lógica, em Planejamento Automatizado (STRIPS/PDDL), responsável pelas decisões de atendimento e desvios operacionais.

## 1. O Problema de Pesquisa e a Hipótese Fundamental

O problema identificado no processo de trabalho do ACS está na ineficiência operacional e nas falhas de agendamento causadas pela **incapacidade de antecipar conflitos de recursos no decorrer do turno**. Em cenários onde o ACS dispõe de recursos consumíveis limitados (como bolsas com quantidade restrita de fitas de glicemia capilar) e depende de recursos organizacionais escassos (como janelas de supervisão ou teleorientação por profissional de saúde de nível superior), as decisões tomadas em uma residência impactam diretamente a viabilidade dos atendimentos subsequentes.

A prática atual ou a automação baseada em scripts procedurais simples (laços gulosos reativos) trata as paradas de forma isolada. Consequentemente, quando o agente consome seus insumos ou aciona uma supervisão sem a devida antecipação, é forçado a realizar desvios não planejados à UBS para reabastecimento. Em virtude das regras legais, que encerram a supervisão ativa no momento em que o ACS sai da residência, desvios reativos invalidam assistências já iniciadas, levando o script reativo a declarar erroneamente que o turno é inviável (falso negativo).

A Pergunta de Pesquisa orientadora deste trabalho é: **Num contexto em que a rota física já está fixada por um roteirizador geométrico, o Planejamento Automatizado fundamentado em PDDL agrega valor mensurável em comparação a um executor procedural simples, eliminando falsos negativos e garantindo a corretude na execução dos protocolos legais?**

## 2. Justificativa

### 2.1 Impacto Prático

Sob a ótica do Manual de Oslo, este projeto caracteriza-se como uma inovação de processo no setor público de saúde. Ao introduzir um modelo computacional capaz de organizar e otimizar o fluxo de trabalho do ACS, o sistema reduz o desperdício de tempo em deslocamentos desnecessários e assegura o cumprimento integral das metas de acompanhamento em saúde da população vulnerável.

A solução gera relevantes impactos sociais e éticos: garante o tratamento equitativo dos cidadãos ao assegurar que crianças, gestantes, idosos e diabéticos recebam os procedimentos legais exigidos sem interrupções operacionais. Além disso, previne o descarte de materiais e mitiga o estresse profissional das equipes da ESF decorrente de retrabalho e falhas na supervisão clínica.

### 2.2 Pertinência do Planejamento Automatizado

A escolha do Planejamento Automatizado (PDDL/STRIPS) como ferramenta central apoia-se em um argumento factual extraído da legislação sanitária brasileira, que possui a estrutura exata de um esquema de ação de lógica declarativa:

> **Texto Literal da Norma Legal (Lei nº 11.350/2006, art. 3º, § 4º):**
>
> *"...desde que o Agente Comunitário de Saúde tenha concluído curso técnico e tenha disponíveis os equipamentos adequados, são atividades do Agente, em sua área geográfica de atuação, assistidas por profissional de saúde de nível superior, membro da equipe: I - a aferição da pressão arterial... encaminhando o paciente...; II - a medição de glicemia capilar... encaminhando o paciente..."*

Em termos computacionais, a lei estabelece formalmente: a ação X só é permitida se `(A ∧ B ∧ C)` e sua execução implica o efeito Y. Nesse contexto, um domínio PDDL constitui uma especificação declarativa e executável da lei. A abordagem de decomposição hierárquica, por sua vez, evita o elevado custo combinatório de resolver o Problema do Caixeiro Viajante (TSP) diretamente no planejador simbólico. Para isso, a otimização contínua da rota é atribuída a uma heurística de grafos (VMP + 2-opt), enquanto o planejador PDDL é responsável pelo raciocínio combinatório relacionado às restrições de insumos e às permissões legais.

## 3. Objetivos

### 3.1 Objetivo Geral

Modelar, implementar e validar um protótipo de software (nível TRL 3 a 4) baseado em Planejamento Automatizado (PDDL/STRIPS) e decomposição hierárquica, destinado a otimizar o agendamento, os desvios operacionais e o cumprimento de protocolos clínicos normativos durante visitas domiciliares de Agentes Comunitários de Saúde no âmbito do SUS.

### 3.2 Objetivos Específicos

- **Mapear e Formalizar a Norma Legal:** Mapear os artigos 3º (§ 3º e § 4º) da Lei nº 11.350/2006 e as diretrizes da PNAB (Portaria GM/MS nº 2.436/2017) em esquemas de ações, pré-condições e efeitos declarativos na linguagem PDDL 2.1.
- **Construir a Camada Geométrica de Roteamento:** Implementar o módulo de otimização de rotas espaciais baseado na heurística do Vizinho Mais Próximo com refinamento local 2-opt, utilizando matrizes de distâncias urbanas reais (haversine corrigido por fator de malha de 1,3).
- **Desenvolver o Compilador e Tradutor PDDL:** Construir um módulo automatizado de geração de arquivos de problema PDDL aplicando técnicas de compilação como a de polaridade invertida para restrições clínicas e o desdobramento da UBS (`ubs` e `ubs-fim`) para garantir aciclicidade no grafo de busca.
- **Implementar o Ambiente Experimental e Linha de Base:** Desenvolver um planejador STRIPS nativo em Python (com suporte às buscas A* com h_max, A* com h_add e GBFS) e construir um executor guloso reativo como adversário honesto de controle, compartilhando rigorosamente a mesma tabela de custos.
- **Validar Empiricamente o Artefato:** Executar experimentos científicos controlados (E1 - Escalabilidade, E2 - Qualidade de Plano vs. Falsos Negativos e E3 - Provas de Inviabilidade) para mensurar quantitativamente a eliminação de erros, o tempo de execução e os limites de escalabilidade.

## 4. Fundamentação Teórica em Ciência da Computação

A fundamentação teórica deste trabalho apoia-se em duas grandes áreas da Ciência da Computação: a Teoria dos Grafos/Pesquisa Operacional e o Planejamento Automatizado em Inteligência Artificial.

No campo da otimização espacial, o Problema do Caixeiro Viajante (TSP) e o Home Health Care Routing and Scheduling Problem (HHCRSP) são conhecidos por sua complexidade NP-dura. A literatura consagrada recomenda a decomposição de problemas híbridos: a camada de espaço contínuo é tratada eficientemente por algoritmos heurísticos de grafos (como a combinação do Vizinho Mais Próximo com refinamento 2-opt), enquanto a camada de decisão simbólica é endereçada por sistemas de planejamento baseados no modelo STRIPS e na linguagem PDDL.

No Planejamento Clássico, a busca no espaço de estados é guiada por heurísticas extraídas do Grafo de Planejamento Relaxado (que ignora os efeitos de remoção das ações). A heurística h_max é formalmente admissível e garante a otimalidade de custo do plano quando associada ao algoritmo A*, enquanto a heurística h_add (inadmissível) e o algoritmo Greedy Best-First Search (GBFS) priorizam a velocidade de busca em detrimento da otimalidade estrita.

O estado da arte científico defendido neste trabalho demonstra que a representação declarativa da norma **permite ajustar regras de saúde pública sem a necessidade de reescrever o código-fonte da aplicação.**