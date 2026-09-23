# Fontes e fidelidade factual

Este documento separa três coisas que não podem ser confundidas no relatório:
o que é **norma legal citada**, o que é **parâmetro de modelagem escolhido por
nós**, e o que é **ficção** criada para o protótipo.

---

## 1. Norma legal — base das pré-condições do domínio PDDL

### 1.1 Lei nº 11.350/2006, art. 3º, § 4º (redação da Lei nº 13.595/2018)

Fonte primária: <https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13595.htm>

Texto literal:

> § 4º No modelo de atenção em saúde fundamentado na assistência
> multiprofissional em saúde da família, **desde que o Agente Comunitário de
> Saúde tenha concluído curso técnico e tenha disponíveis os equipamentos
> adequados**, são atividades do Agente, em sua área geográfica de atuação,
> **assistidas por profissional de saúde de nível superior, membro da equipe**:
>
> I – a aferição da pressão arterial, durante a visita domiciliar, em caráter
> excepcional, **encaminhando o paciente para a unidade de saúde de referência**;
>
> II – a medição de glicemia capilar, durante a visita domiciliar, em caráter
> excepcional, **encaminhando o paciente para a unidade de saúde de referência**;
>
> III – a aferição de temperatura axilar, durante a visita domiciliar, em
> caráter excepcional, com o devido encaminhamento do paciente, quando
> necessário, para a unidade de saúde de referência;
>
> IV – a orientação e o apoio, em domicílio, para a correta administração de
> medicação de paciente em situação de vulnerabilidade;
>
> V – a verificação antropométrica.

**Como isso virou domínio:**

| Trecho da lei | Elemento PDDL |
|---|---|
| "tenha concluído curso técnico" | `(curso-tecnico-concluido ?ag)` — pré-condição |
| "tenha disponíveis os equipamentos adequados" | `(equipamento-disponivel ?ag)` — pré-condição |
| "assistidas por profissional de saúde de nível superior" | `(supervisao-ativa ?ag)` — pré-condição, recurso finito |
| inciso I | ação `aferir-pressao-arterial` |
| inciso II | ação `medir-glicemia-capilar` |
| "encaminhando o paciente para a unidade de referência" | efeito `(pendencia-encaminhamento ?p)`, quitado por `registrar-encaminhamento` |

Os incisos III, IV e V **não** foram modelados — decisão de escopo do
protótipo, não omissão da norma.

### 1.2 Lei nº 11.350/2006, art. 3º, § 3º (mesma redação)

> II – o detalhamento das visitas domiciliares, com coleta e registro de dados
> relativos a suas atribuições, para fim exclusivo de controle e planejamento
> das ações de saúde;
>
> IV – a realização de visitas domiciliares regulares e periódicas para
> acolhimento e acompanhamento: […] c) **da criança, verificando seu estado
> vacinal** e a evolução de seu peso e de sua altura; […] e) da pessoa idosa […]
>
> V – realização de visitas domiciliares regulares e periódicas para
> identificação e acompanhamento: […] c) **do estado vacinal da gestante, da
> pessoa idosa e da população de risco**, conforme sua vulnerabilidade e em
> consonância com o previsto no calendário nacional de vacinação;

**Como isso virou domínio:**

- § 3º II → ação `registrar-visita`, obrigatória para fechar o protocolo.
- § 3º IV "c" e V "c" → ação `verificar-caderneta-vacinal`, exigida dos
  pacientes dos grupos `crianca`, `gestante` e `pessoa_idosa`.

Note o **contraste proposital** no domínio: `verificar-caderneta-vacinal` é
atividade *típica* (§ 3º) e não exige curso técnico, equipamento nem
supervisão; `aferir-pressao-arterial` é atividade do § 4º e exige as três
coisas. Essa assimetria vem da lei, não de conveniência de modelagem.

### 1.3 PNAB — Portaria GM/MS nº 2.436/2017

Fonte: <https://www.in.gov.br/materia/-/asset_publisher/Kujrw0TZC2Mb/content/id/19308123/do1-2017-09-22-portaria-n-2-436-de-21-de-setembro-de-2017-19308031>

Usada como fundamento de que a visita domiciliar é atividade central do ACS e
de que a periodicidade deve seguir **critérios de risco e vulnerabilidade**.

**Cuidado ao citar:** a PNAB 2017 **não fixa** um critério numérico de
periodicidade. A referência de "uma visita por família por mês" é prática
historicamente consolidada na Estratégia Saúde da Família, e a literatura
aponta justamente a ausência de critérios normatizados para orientar a
periodicidade. No protótipo, `intervalo_maximo_padrao_dias: 30` é **parâmetro
configurável, não norma** — e deve ser apresentado assim no relatório.

---

## 2. Parâmetros escolhidos por nós (não são norma, não são dados reais)

| Parâmetro | Valor | Origem |
|---|---|---|
| `fitas_glicemia_por_carga` | 2 | escolhido baixo de propósito, para gerar escassez e tornar o problema de planejamento não trivial |
| `janelas_supervisao_no_turno` | 8 (1 por residência) | escolhido para que o recurso escasso do experimento seja a fita, não a supervisão |
| velocidade de caminhada | 4,5 km/h | valor usual para deslocamento a pé em área urbana |
| fator de malha urbana | 1,3 | correção usual de distância em linha reta para percurso em malha em grade |
| custos das ações (minutos) | 2 a 5 | estimativas nossas de ordem de grandeza; **não** foram medidas em campo |

Todos são configuráveis. Nenhum deve ser apresentado como dado do SUS.

---

## 3. Ficção

- **Todos os pacientes, condições clínicas, datas e prioridades são fictícios.**
  Nenhum dado pessoal real foi utilizado.
- A "UBS Santa Cecília" do arquivo de exemplo é fictícia.
- As **coordenadas** são reais (região Bom Fim / Rio Branco, Porto Alegre-RS) e
  servem apenas para que a matriz de distâncias tenha ordem de grandeza
  plausível. Não correspondem a residências reais de pacientes.
- As instâncias sintéticas de `gerador_instancias.py` sorteiam perfis com pesos
  arbitrários. Eles variam a **estrutura combinatória** do problema; **não**
  estimam prevalência epidemiológica brasileira e não devem ser lidos assim.

---

## 4. Sobre o material de apoio

A conversa com o Gemini que originou a ideia contém uma premissa clínica
incorreta (ACS aplicando insulina, fazendo curativo cirúrgico, manipulando
rede de frio). Esses procedimentos **não** são atribuição do ACS. A
modelagem deste repositório descarta essa premissa e usa apenas o rol legal
do art. 3º da Lei 11.350/2006. Ver [`01-analise-da-proposta.md`](01-analise-da-proposta.md),
seção 2.

---

## Lista de links

- Lei nº 13.595/2018 (altera a Lei nº 11.350/2006) — <https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13595.htm>
- Lei nº 13.595/2018 no DOU — <https://www.in.gov.br/materia/-/asset_publisher/Kujrw0TZC2Mb/content/id/10859112/do1-2018-04-18-lei-n-13-595-de-5-de-janeiro-de-2018-10859108>
- PNAB, Portaria GM/MS nº 2.436/2017 — <https://www.in.gov.br/materia/-/asset_publisher/Kujrw0TZC2Mb/content/id/19308123/do1-2017-09-22-portaria-n-2-436-de-21-de-setembro-de-2017-19308031>
- Visitas domiciliares no Brasil: características da atividade basilar dos ACS (SciELO) — <https://www.scielosp.org/article/sdeb/2018.v42nspe2/127-144/>
