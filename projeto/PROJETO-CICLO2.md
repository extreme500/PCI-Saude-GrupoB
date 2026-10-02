# Planejamento Automatizado aplicado ao cumprimento de protocolos legais em visitas domiciliares de Agentes Comunitários de Saúde

**Projeto em Ciência e Inovação (INF99003), Ciclo 2**
Gabriel Pieruccini Knopp · Arthur Andrade da Silva · Izadora Candotti de Oliveira
Grupo B, Instituto de Informática, UFRGS

---

## 1. Resumo e Palavras-Chave

**Resumo.** A Atenção Primária à Saúde no Brasil apoia-se nas visitas domiciliares
realizadas por Agentes Comunitários de Saúde, cuja atuação é normatizada pela Lei
nº 11.350/2006, na redação dada pela Lei nº 13.595/2018. Procedimentos como a aferição
de pressão arterial e a medição de glicemia capilar estão condicionados, pelo art. 3º
§ 4º, à conclusão de curso técnico, à disponibilidade de equipamentos e à assistência
de profissional de saúde de nível superior, e obrigam o encaminhamento do paciente à
unidade de referência. A ordem das visitas pode ser resolvida por roteirizadores
geométricos, mas o cumprimento dessas condições sob recursos finitos (insumos
consumíveis e disponibilidade limitada do profissional supervisor) faz com que uma
decisão tomada em uma residência afete a viabilidade das seguintes, configurando um
problema combinatório que a otimização de percurso, isoladamente, não resolve. Este
projeto propõe um sistema de apoio ao planejamento do turno organizado em duas camadas:
uma camada geométrica, responsável pela sequência espacial das visitas, e uma camada
lógica em Planejamento Automatizado (STRIPS/PDDL), responsável pelas ações em cada
parada e pelos desvios de reabastecimento. Espera-se que a representação declarativa da
norma permita identificar sequências de atendimento válidas que um método procedural
classificaria como inexequíveis, e que alterações normativas possam ser absorvidas sem
reescrita do código de busca. A validação prevista compara o sistema proposto com um
executor procedural equivalente, sob a mesma tabela de custos, e mede a ocorrência
desse tipo de erro, a qualidade dos planos e os limites de escalabilidade.

**Palavras-Chave:** Planejamento Automatizado; PDDL; Atenção Primária à Saúde;
Conformidade Normativa; Otimização de Rotas; Busca Heurística.

---

## 2. Introdução e Contextualização

O ecossistema afetado é a Atenção Primária à Saúde do Sistema Único de Saúde,
especificamente o processo de trabalho das equipes de Saúde da Família. Cada equipe
responde por um território adscrito, subdividido em microáreas, e cada microárea fica
sob responsabilidade de um Agente Comunitário de Saúde. A visita domiciliar é a
atividade basilar desse profissional: a Política Nacional de Atenção Básica (BRASIL,
2017) a estabelece como ação central e orienta que sua periodicidade siga critérios de
risco e vulnerabilidade. O agente opera com dados clínicos da população adscrita
(gestantes, pessoas idosas, pessoas com diabetes ou hipertensão, crianças em
puericultura), com o georreferenciamento das residências e com o histórico de visitas.

Sobre esse trabalho incide uma camada normativa específica. A Lei nº 11.350/2006, na
redação dada pela Lei nº 13.595/2018, distingue dois regimes de atividade. O art. 3º
§ 3º lista atividades típicas, exercidas sem condicionantes, entre elas o registro dos
dados da visita e a verificação do estado vacinal de crianças, gestantes e pessoas
idosas. Já o art. 3º § 4º lista atividades condicionadas, que só são atribuição do
agente mediante requisitos cumulativos.

O planejamento da visita domiciliar costuma ser tratado como um problema de percurso:
minimizar deslocamento, cobrir o território no prazo, respeitar a capacidade da equipe.
Essa formulação captura apenas parte do problema, porque chegar à residência correta não
autoriza o atendimento. Para os procedimentos do § 4º, a permissão legal é uma conjunção
de condições, e nem todas são estáticas. O curso técnico e o equipamento não variam ao
longo do turno; a assistência do profissional de nível superior e os insumos
consumíveis, sim. O agente que gastou a última fita reagente ou já mobilizou o
supervisor não perdeu sua habilitação, mas, naquele momento e naquela residência, não
pode executar o procedimento.

Disso decorre a dor operacional central: a incapacidade de antecipar conflitos de
recursos no decorrer do turno. Uma decisão tomada na terceira parada pode inviabilizar a
sétima. Um planejamento que trate as paradas isoladamente, ou que otimize apenas a
geometria do percurso, não enxerga esse acoplamento; quando o conflito se materializa,
o agente é forçado a desvios não previstos até a Unidade Básica de Saúde e, no limite,
à conclusão equivocada de que o turno é inexequível. A pergunta que os dados ocultam,
portanto, não é qual o menor percurso, mas se determinada sequência de atendimentos é
executável sem violar a norma, dados os recursos disponíveis.

A hipótese que orienta o projeto é que a representação declarativa das condições legais,
tratada por um planejador simbólico, reduzirá a ocorrência de falsos negativos, isto é,
de turnos classificados como inexequíveis quando existe uma sequência de atendimentos
válida, e que esse ganho justificará o custo de adotar o paradigma. A hipótese pode se
mostrar incorreta, e o desenho de validação precisa admitir essa possibilidade. Dois
desfechos alternativos são plausíveis: que um executor procedural simples alcance
desempenho equivalente, tornando o planejador redundante; ou que o custo computacional
da busca cresça a ponto de inviabilizar seu uso em microáreas de tamanho realista. A
metodologia descrita na seção 6 foi construída para permitir que qualquer um dos três
desfechos se manifeste.

---

## 3. Justificativa

Sob a ótica do Manual de Oslo (OCDE; EUROSTAT, 2025), o projeto caracteriza-se como uma
inovação de processo de negócio, aqui aplicada ao setor público de saúde. A quarta
edição do manual reduziu os tipos de inovação a dois, de produto e de processo de
negócio, e orienta a medição no setor empresarial, tratando o setor governamental à
parte; a transposição feita aqui é analógica, e fica declarada como tal.
O valor prático esperado não está na
redução do tempo de deslocamento, que as ferramentas de roteirização já endereçam, e sim
em três capacidades que o método procedural não oferece. A primeira é a corretude sob
escassez: identificar sequências de atendimento executáveis em cenários nos quais um
método ingênuo concluiria, equivocadamente, pela inexequibilidade do turno. A segunda é
a demonstração de inviabilidade: quando o turno é de fato inexequível, distinguir "não
encontrei solução" de "demonstra-se que não existe solução", resposta que constitui
informação gerencial, pois indica à equipe que há pacientes a remanejar ou recursos a
suprir. A terceira é a declaratividade: com a norma expressa como especificação, e não
embutida no fluxo de controle do programa, alterações normativas passam a ser editadas
onde a regra está escrita.

Os impactos sociais esperados decorrem da primeira capacidade. A garantia de que um
turno planejado é executável tende a favorecer a equidade de acesso, porque os grupos
cujo acompanhamento é normativamente exigido (gestantes, crianças, pessoas idosas,
pessoas com condições crônicas) são justamente os que dependem de procedimentos
condicionados e, portanto, os primeiros a serem preteridos quando um recurso se esgota
no meio do turno. Há também um risco ético a declarar: um sistema que decide a ordem e
o conteúdo do atendimento pode deslocar julgamento clínico e territorial do profissional
para uma função de custo. Por isso o sistema é concebido como apoio à decisão, sem
selecionar pacientes nem substituir a avaliação da equipe.

A pertinência do Planejamento Automatizado apoia-se em um argumento factual extraído da
própria legislação. O art. 3º § 4º da Lei nº 11.350/2006 estabelece que, "desde que o
Agente Comunitário de Saúde tenha concluído curso técnico e tenha disponíveis os
equipamentos adequados, são atividades do Agente, em sua área geográfica de atuação,
assistidas por profissional de saúde de nível superior, membro da equipe: I, a aferição
da pressão arterial, durante a visita domiciliar, em caráter excepcional, encaminhando
o paciente para a unidade de saúde de referência; II, a medição de glicemia capilar (...)
encaminhando o paciente (...)". Em termos computacionais, a norma tem a forma de um
esquema de ação declarativo: a ação só é permitida se um conjunto de condições vale, e
executá-la obriga um efeito. Essa é a estrutura de uma ação no formalismo STRIPS (FIKES;
NILSSON, 1971), com pré-condições, lista de adição e lista de remoção. Um domínio PDDL
constitui, nesse caso, uma especificação declarativa e executável da norma.

A Computação clássica é a ferramenta adequada porque o problema é combinatório. Com
recursos finitos repostos apenas na Unidade Básica de Saúde e supervisão vinculada ao
atendimento em curso, o número de sequências de ação candidatas cresce exponencialmente,
e a interação entre decisões distantes na rota não é tratável por inspeção manual nem
por planilha. A decomposição em duas camadas evita, por sua vez, o erro conhecido de
submeter o problema de percurso ao planejador simbólico: a otimização espacial, que é
geométrica e NP-difícil, permanece com heurísticas de grafos consagradas (CROES, 1958;
ROSENKRANTZ; STEARNS; LEWIS, 1977), enquanto o planejador responde apenas pelo
raciocínio sobre estados lógicos e recursos discretos.

---

## 4. Objetivos

**Objetivo geral.** Modelar, implementar e validar um sistema de apoio ao planejamento
de turnos de visitas domiciliares de Agentes Comunitários de Saúde, baseado em
decomposição hierárquica e em Planejamento Automatizado (STRIPS/PDDL), capaz de
determinar as ações de atendimento e os desvios de reabastecimento que garantam o
cumprimento dos protocolos legais, e mensurar em que dimensões esse paradigma supera um
executor procedural equivalente.

**Objetivos específicos.**

1. Mapear e formalizar em PDDL os §§ 3º e 4º do art. 3º da Lei nº 11.350/2006 (redação
   da Lei nº 13.595/2018) e as diretrizes da PNAB, traduzindo-os em esquemas de ações,
   pré-condições e efeitos.

2. Construir a camada geométrica de roteamento, partindo de heurísticas construtivas
   com refinamento local e avaliando a substituição por metaheurísticas, como algoritmos
   genéticos ou busca em vizinhança ampla adaptativa, conforme a escala exigida.

3. Implementar o módulo de tradução que converte os dados clínicos e a rota definida
   pela camada geométrica em arquivos de problema PDDL.

4. Implementar o ambiente experimental, incluindo o planejador simbólico e um executor
   procedural que sirva de referência de comparação, ambos sob a mesma tabela de custos.

5. Produzir uma saída operacional legível pelo agente de saúde, contendo o roteiro do
   turno passo a passo com apenas as informações essenciais ao atendimento.

6. Validar empiricamente o sistema por meio de experimentos controlados de
   escalabilidade, de qualidade de plano e de reconhecimento de inviabilidade.

7. Verificar a independência de implementação, submetendo os mesmos arquivos de domínio
   e problema a um planejador de referência da área.

---

## 5. Revisão de Literatura e Soluções de Mercado

No campo da otimização espacial, o problema de origem é o *Home Health Care Routing and
Scheduling Problem*, extensão do Problema de Roteamento de Veículos com restrições
próprias do contexto de saúde domiciliar. Duas revisões o consolidam: FIKAR e HIRSCH
(2017) sistematizam cenários, modelos e métodos; CISSÉ *et al.* (2017) o caracterizam
como extensão do VRP e identificam, entre as restrições laterais, a preferência do
paciente e os requisitos de qualificação profissional. Especificamente para agentes
comunitários, BRUNSKILL e LESH (2010) propõem formular a programação de visitas como
problema de roteamento e agendamento, sugerindo técnicas derivadas do caixeiro viajante
com janelas de tempo. Trata-se de um artigo de posição de duas páginas, que delineia
direções de pesquisa em vez de apresentar resultados. Dele interessa ainda uma
observação diretamente ligada à camada de seleção deste projeto: uma visita domiciliar
costuma gerar visitas de acompanhamento futuras, característica pouco tratada na
literatura combinatória de roteamento e escalonamento. Na camada
geométrica, o refinamento 2-opt remonta a CROES (1958), e a análise das heurísticas
construtivas a ROSENKRANTZ, STEARNS e LEWIS (1977).

No Planejamento Automatizado, o formalismo empregado origina-se em FIKES e NILSSON
(1971). BONET e GEFFNER (2001) estabelecem o planejamento como busca heurística no
espaço de estados e definem as heurísticas derivadas da relaxação por deleção, entre as
quais a h_max, admissível, e a h_add, mais informativa porém sem garantia de otimalidade.
HELMERT e DOMSHLAK (2009) comparam formalmente as famílias de heurísticas admissíveis e
introduzem a LM-cut. Essa literatura sustenta uma correção a uma objeção frequente: o
planejamento de custo ótimo é subárea consolidada, e a afirmação defensável não é que
planejadores não otimizam custo, mas que não escalam como solucionadores de Pesquisa
Operacional dedicados. HELMERT (2006) descreve o Fast Downward, planejador de referência
da área.

A tradução de normas de saúde para domínios de planejamento tem precedente. BRADBROOK
*et al.* (2005) propõem o uso de tecnologia de planejamento como componente de diretrizes
clínicas computadorizadas, e GONZÁLEZ-FERRER *et al.* (2013) traduzem diretrizes clínicas
interpretáveis por computador em um domínio de planejamento hierárquico temporal, gerando
planos de cuidado personalizados. Considerou-se ainda o emprego de Modelos de Linguagem
de Grande Escala como geradores de plano, alternativa descartada com base em VALMEEKAM
*et al.* (2023), que reportam limitação acentuada na geração autônoma de planos
executáveis.

Quanto ao que a indústria absorveu, a roteirização é tecnologia madura: solucionadores
como o Google OR-Tools e motores de código aberto como o OSRM resolvem o problema
geométrico em escala. Nenhum deles raciocina sobre pré-condições normativas encadeadas,
pois, para essas ferramentas, a compatibilidade entre profissional e paciente é parâmetro
de entrada, não estado que evolui durante a execução. O planejamento simbólico, por sua
vez, dispõe de ferramental maduro, mas com penetração aplicada restrita ao ambiente
acadêmico. No SUS, o e-SUS APS inclui o aplicativo e-SUS Território, utilizado por
agentes comunitários para cadastro territorial e registro de visitas. O manual de uso
oficial da versão 3.1 do aplicativo descreve funcionalidades de cadastro e de registro
de acompanhamento das visitas domiciliares, sem menção a rota, mapa, agenda ou
planejamento, e sem verificação automática de conformidade normativa. A afirmação vale
para essa versão do manual.

Cruzando essas frentes, delimita-se a lacuna que o projeto ocupa. A literatura de
roteamento em saúde domiciliar reconhece a qualificação profissional como restrição, mas
a modela como rótulo estático de compatibilidade dentro de formulações de programação
matemática; a literatura de planejamento aplicado à saúde trata diretrizes clínicas sem
componente de roteamento; e as ferramentas de mercado otimizam a geometria ignorando a
norma. Nas buscas realizadas, não foram localizados trabalhos que apliquem planejamento
automatizado simbólico à conformidade normativa de visitas domiciliares sobre rota
previamente fixada, tratando as condições legais como recursos consumíveis ao longo do
turno. É nessa interseção que o projeto se posiciona.

---

## 6. Metodologia

A pesquisa segue abordagem de Design Science com validação experimental: constrói-se um
artefato e mede-se seu comportamento contra um grupo de comparação sob variáveis
controladas.

Quanto à fonte de dados, o projeto usará dados sintéticos de pacientes, decisão
metodológica e ética, uma vez que dados reais da Atenção Primária são sigilosos e seu uso
exigiria aprovação em comitê de ética. Identificação, condições clínicas e datas de
visita serão fictícias; as coordenadas geográficas serão reais, extraídas de uma região
urbana de Porto Alegre, para conferir ordem de grandeza plausível à matriz de distâncias.
As regras clínicas que determinam quais procedimentos cada perfil exige serão derivadas
do texto legal. A carga ocorrerá a partir de arquivos estruturados, complementados por um
gerador de instâncias parametrizado por número de pacientes e semente aleatória, cuja
função é variar a estrutura combinatória do problema, e não estimar prevalência
epidemiológica.

A arquitetura central é a decomposição hierárquica em duas camadas desacopladas. A camada
geométrica calcula a matriz de custos e determina a ordem das paradas; a camada lógica
recebe essa ordem congelada e decide as ações em cada residência, incluindo quando sair
da rota para reabastecer. O contrato entre elas é deliberadamente estreito: a camada
geométrica entrega a sequência de paradas, a matriz de custos e o custo de desvio até a
unidade a partir de cada ponto, e o planejador não pode alterar a ordem recebida. Essa
separação permite substituir a camada geométrica, por exemplo por um serviço externo de
roteamento com distâncias reais de malha viária, ou por uma metaheurística, sem alterar o
domínio PDDL. Na camada lógica, prevê-se a construção de ao menos um domínio fiel ao
texto legal vigente, e admite-se a construção de um segundo domínio, mais extenso, com
protocolos sintéticos adicionais, para observar como o método se comporta quando a
complexidade normativa cresce.

Cabe registrar a fronteira entre norma e modelagem. O art. 3º § 4º exige assistência de
profissional de nível superior, sem estipular sua forma, duração ou frequência.
Representar essa assistência como recurso discreto e finito por turno, e encerrá-la
quando o agente deixa a residência, são decisões de modelagem deste trabalho, não
determinações legais, e permanecerão parametrizáveis.

O ambiente de desenvolvimento será Python, preferencialmente sem dependências externas
obrigatórias, de modo a garantir reprodutibilidade. O formalismo adotado é o PDDL, no
fragmento STRIPS com custos de ação. Além do planejador desenvolvido no projeto,
pretende-se utilizar o Fast Downward como planejador de referência para verificação. O
versionamento será feito em Git, com o código e a documentação técnica públicos.

O plano de validação combina demonstração prática, experimentação controlada, teste de
casos extremos e verificação cruzada de implementação. O grupo de comparação será um
executor procedural que percorre a mesma rota, cumpre os mesmos protocolos e reabastece
quando fica sem insumo, lendo a tabela de custos do próprio arquivo de domínio, de modo a
eliminar divergência de medição entre os grupos comparados. A variável isolada é a
capacidade de antecipação: o executor procedural só detecta a falta de recurso no momento
do uso. Serão variáveis independentes o número de pacientes, a semente da instância, a
estratégia de busca, a capacidade de insumos, o número de acionamentos de supervisão
disponíveis e a habilitação legal do agente; serão dependentes o custo do plano, o número
de ações, o tempo de busca, os nós expandidos e o desfecho de sucesso ou insucesso.

Três experimentos estão previstos. O primeiro medirá a escalabilidade, variando o número
de pacientes e comparando estratégias de busca ótimas e satisfacientes, para identificar
até que tamanho de microárea cada uma permanece viável. O segundo comparará o sistema
proposto com o executor procedural em um conjunto de instâncias sorteadas, medindo custo
dos planos e, principalmente, a frequência com que cada abordagem classifica
incorretamente um turno como inexequível. O terceiro submeterá o sistema a instâncias
construídas para não admitirem solução, de dois tipos distintos, uma em que falta uma
condição legal e outra em que falta recurso, para verificar se a inviabilidade é
reconhecida e a que custo computacional. Prevê-se ampliar o número de execuções conforme
os resultados iniciais indiquem variância relevante.

A verificação de independência de implementação é parte do plano e não uma etapa
opcional: os mesmos arquivos de domínio e problema serão submetidos ao Fast Downward, e a
comparação incidirá sobre a aceitação do domínio, a coincidência dos vereditos de
viabilidade e a igualdade numérica do custo ótimo, esta última decisiva, pois duas
implementações independentes que alegam otimalidade devem convergir no mesmo valor.

Uma implementação exploratória preliminar já foi conduzida, em escala reduzida, com a
finalidade única de verificar se a modelagem proposta é viável e se o fenômeno previsto
pela hipótese chega a se manifestar. Os indícios obtidos foram favoráveis e motivaram a
continuidade, mas não constituem resultado do projeto: são anteriores ao desenho
experimental aqui descrito, e é esse desenho que produzirá as medições.

Conforme o desenvolvimento avance, outras extensões poderão ser incorporadas. Estuda-se
incluir uma política de seleção dos pacientes que comporão cada turno, a partir da
prioridade clínica e do intervalo máximo entre visitas, hoje presentes nos dados, mas
ainda não utilizados nessa decisão. Investiga-se também se o nível de urgência pode
induzir restrições de precedência entre atendimentos, isto é, exigir que determinado
paciente seja visitado antes de outro, hipótese particularmente adequada ao paradigma
adotado, já que precedências são expressas nativamente como pré-condições.

---

## 7. Resultados Esperados

O projeto situa-se entre os níveis 3 e 4 de maturidade tecnológica: um sistema funcional
validado em laboratório, não um produto pronto para implantação em rede de saúde.

Espera-se entregar, ao final, o sistema executável com as duas camadas integradas; o
domínio PDDL correspondente à norma vigente, acompanhado do mapeamento entre cada ação
modelada e o dispositivo legal que a fundamenta; a saída operacional legível pelo agente
de saúde; o conjunto de experimentos reprodutíveis; e um relatório técnico consolidando
as medições e discutindo os ganhos projetados para uma eventual aplicação em escala.

Quanto ao comportamento do sistema, a expectativa é que o planejamento simbólico
reconheça como executáveis turnos que o executor procedural classificaria como
inviáveis, e que a diferença se concentre justamente nos cenários de escassez de
recursos, que são os de maior interesse operacional. Espera-se também que a busca ótima
permaneça computacionalmente viável na faixa de tamanho correspondente a um turno real
de trabalho, e que a substituição de regras no domínio produza alteração de comportamento
sem qualquer modificação no código de busca, evidenciando a declaratividade pretendida.

É igualmente possível que os experimentos apontem em outra direção, e o projeto
considera esse desfecho legítimo: pode-se verificar que a vantagem do planejamento se
restringe a instâncias pouco frequentes, ou que o custo da busca ótima cresça além do
aceitável. Nessa hipótese, o resultado do trabalho passa a ser a delimitação precisa das
condições sob as quais o paradigma compensa, o que também responde à pergunta de
pesquisa.

As principais ameaças à validade já identificadas são o uso de um planejador desenvolvido
pelo próprio grupo, mitigado pela verificação cruzada descrita na seção 6; a restrição a
um único agente, que deixa o dimensionamento de equipe fora do escopo; a estimativa de
custos de deslocamento sem medição em campo; e o caráter sintético das instâncias, que
variam a estrutura combinatória do problema sem representar prevalência epidemiológica
real.

---

## 8. Cronograma

| Período | Atividades |
|---|---|
| Até 25/09/2026 | Delimitação do problema, revisão bibliográfica, concepção da proposta e implementação exploratória preliminar para verificação da viabilidade da ideia. |
| Até 02/10/2026 | Ampliação das condições modeladas no domínio; execução de novo conjunto de testes; evolução do sistema rumo a uma versão funcional; avaliação de metaheurísticas na camada de roteamento; integração de serviço externo para cálculo de distâncias reais; construção da saída operacional legível pelo agente de saúde; estudo da política de seleção de pacientes do turno e do uso do nível de urgência como restrição de precedência; separação entre um domínio fiel à norma vigente e um domínio estendido com protocolos sintéticos. |
| Até 09/10/2026 | Consolidação dos resultados, análise crítica, redação do relatório final e preparação da apresentação. |

---

## 9. Referências Bibliográficas

BONET, B.; GEFFNER, H. Planning as heuristic search. **Artificial Intelligence**, v. 129,
n. 1-2, p. 5-33, 2001. DOI: 10.1016/S0004-3702(01)00108-4.

BRADBROOK, K.; WINSTANLEY, G.; GLASSPOOL, D.; FOX, J.; GRIFFITHS, R. AI Planning
Technology as a Component of Computerised Clinical Practice Guidelines. In:
**Artificial Intelligence in Medicine (AIME 2005)**. Lecture Notes in Computer Science,
v. 3581. Berlin: Springer, 2005. p. 171-180. DOI: 10.1007/11527770_26.

BRASIL. **Lei nº 11.350, de 5 de outubro de 2006.** Regulamenta o § 5º do art. 198 da
Constituição, dispõe sobre o aproveitamento de pessoal amparado pelo parágrafo único do
art. 2º da Emenda Constitucional nº 51, de 14 de fevereiro de 2006, e dá outras
providências. Brasília, 2006. Disponível em:
https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11350.htm.
Acesso em: 1 out. 2026. [O art. 3º § 4º está na redação dada pela Lei nº 13.595/2018; a
alteração posterior, da Lei nº 14.536/2023, incide apenas sobre o art. 2º-A.]

BRASIL. **Lei nº 13.595, de 5 de janeiro de 2018.** Altera a Lei nº 11.350, de 5 de
outubro de 2006, para dispor sobre a reformulação das atribuições, a jornada e as
condições de trabalho dos Agentes Comunitários de Saúde e dos Agentes de Combate às
Endemias. Brasília, 2018. Disponível em:
https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13595.htm.
Acesso em: 22 set. 2026.

BRASIL. Ministério da Saúde. **Portaria GM/MS nº 2.436, de 21 de setembro de 2017.**
Aprova a Política Nacional de Atenção Básica. Brasília: Diário Oficial da União, 2017.
Disponível em:
https://www.in.gov.br/materia/-/asset_publisher/Kujrw0TZC2Mb/content/id/19308123.
Acesso em: 22 set. 2026.

BRASIL. Ministério da Saúde. Secretaria de Atenção Primária à Saúde. Departamento de
Saúde da Família. **e-SUS Atenção Primária à Saúde: Manual de Uso do Aplicativo e-SUS
Território, Versão 3.1.** Brasília: Ministério da Saúde, 2020. Disponível em:
https://sisaps.saude.gov.br/esus/upload/docs/manual_utilizacao_aplicativo_esus_aps_territorio.pdf.
Acesso em: 28 set. 2026.

BRUNSKILL, E.; LESH, N. Routing for Rural Health: Optimizing Community Health Worker
Visit Schedules. In: **AAAI Spring Symposium on Artificial Intelligence for Development**.
Technical Report SS-10-01. Menlo Park: AAAI Press, 2010. Disponível em:
https://aaai.org/papers/01139-1139-routing-for-rural-health-optimizing-community-health-worker-visit-schedules/.
Acesso em: 1 out. 2026.

CISSÉ, M.; YALÇINDAĞ, S.; KERGOSIEN, Y.; ŞAHIN, E.; LENTÉ, C.; MATTA, A. OR problems
related to Home Health Care: A review of relevant routing and scheduling problems.
**Operations Research for Health Care**, v. 13-14, p. 1-22, 2017.
DOI: 10.1016/j.orhc.2017.06.001.

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

OCDE; EUROSTAT. **Manual de Oslo 2018: diretrizes para coleta, relatório e uso de dados
sobre inovação.** 4. ed. Tradução de Finep, Fiesp e Senai-SP. Rio de Janeiro: Finep,
2025. Disponível em:
http://www.finep.gov.br/images/a-finep/5CNCTI/04_07_2025_Manual_de_Oslo.pdf.
Acesso em: 1 out. 2026.

ROSENKRANTZ, D. J.; STEARNS, R. E.; LEWIS, P. M. An Analysis of Several Heuristics for
the Traveling Salesman Problem. **SIAM Journal on Computing**, v. 6, n. 3, p. 563-581,
1977. DOI: 10.1137/0206041.

VALMEEKAM, K.; MARQUEZ, M.; SREEDHARAN, S.; KAMBHAMPATI, S. On the Planning Abilities of
Large Language Models: A Critical Investigation. In: **Advances in Neural Information
Processing Systems (NeurIPS)**, v. 36, 2023. Disponível em:
https://proceedings.neurips.cc/paper_files/paper/2023/hash/efb2072a358cefb75886a315a6fcf880-Abstract-Conference.html.
Acesso em: 22 set. 2026.

GOOGLE. **OR-Tools: routing library.** Disponível em:
https://developers.google.com/optimization/routing. Acesso em: 28 set. 2026.

PROJECT OSRM. **Open Source Routing Machine.** Disponível em: https://project-osrm.org.
Acesso em: 28 set. 2026.

PYTHON SOFTWARE FOUNDATION. **Python Language Reference.** Disponível em:
https://docs.python.org/3/reference. Acesso em: 28 set. 2026.
