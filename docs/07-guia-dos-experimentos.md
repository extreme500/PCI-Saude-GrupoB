# Guia: o que cada coisa faz

Documento de uso. Responde, nesta ordem: **quais são os dados e onde mexer
neles**, **o que cada comando faz de fato**, **quem está sendo comparado com
quem em cada experimento**, e **onde ler os resultados**.

---

## 1. Os dados

### 1.1 Não existe mapa

Isso costuma confundir, então vale dizer de saída: **o projeto não tem mapa**.
Cada paciente tem latitude e longitude, e dessas coordenadas sai uma **matriz
de tempos de deslocamento** entre todos os pontos. É só isso que as camadas
seguintes enxergam: uma tabela de "de A até B leva N minutos".

A matriz pode vir de dois lugares:

| Provedor | O que é | Quando usar |
|---|---|---|
| `haversine` (padrão) | distância em linha reta × 1,3 (fator de malha urbana), convertida a 4,5 km/h | sempre que os experimentos precisarem ser reproduzíveis sem rede |
| `osrm` | tempo real de percurso pelas ruas, serviço público da Open Source Routing Machine | quando quiser número realista; cai para haversine se a rede falhar |

> Experimentos rodados com provedores diferentes **não são comparáveis entre
> si**. Por isso o sistema sempre imprime qual provedor foi usado de fato.

### 1.2 Para ver os dados

```bash
python -m acsplan dados
python -m acsplan dados --matriz              # com a matriz completa
python -m acsplan dados --instancia-sintetica 8 3   # uma instância sorteada
```

Isso imprime os pacientes ordenados por urgência, o que cada um exige, os
recursos do turno e um **desenho aproximado** da distribuição espacial:

```
  +----------------------------------------------------------+
  |               p9               p3                        |
  |                      p2                              p7  |
  |                                        p1                |
  |p6                        UBS                             |
  |          p4                                              |
  |                                              p8          |
  |                                   p5                     |
  |                     p10                                  |
  +----------------------------------------------------------+
```

O desenho é uma projeção linear sem correção de escala, e **distorce**. Serve
para ver quem está perto de quem, nada além. As distâncias usadas no
planejamento vêm da matriz, não do desenho.

### 1.3 Onde inserir os seus dados

Dois formatos, e o CSV existe justamente para editar em planilha.

```
acsplan/dados/microarea_exemplo.csv    <- a tabela de pacientes
acsplan/dados/microarea_exemplo.json   <- unidade, recursos e agente
```

Um CSV procura um arquivo `.json` **de mesmo nome** ao lado dele, de onde tira
unidade de saúde, recursos do turno e dados do agente. Se não achar, usa
padrões documentados. Na prática: **edite a planilha e deixe o JSON quieto**.

```bash
python -m acsplan planejar --dados acsplan/dados/microarea_exemplo.csv
python -m acsplan dados --exportar-csv minha-microarea.csv   # gera o modelo
```

**Colunas do CSV.** Só `id`, `lat` e `lon` são obrigatórias; o resto tem
padrão, então uma planilha mínima com três colunas já roda.

| Coluna | O que é |
|---|---|
| `id` | identificador curto e único (p1, p2…) |
| `lat`, `lon` | coordenadas decimais |
| `nome`, `grupo` | rótulos (gestante, crianca, pessoa_idosa, adulto, lactante) |
| `condicoes` | várias, separadas por `;` |
| `prioridade` | 1 a 3, atribuída pela unidade de saúde |
| `dias_desde_ultima_visita` | usado para calcular atraso |
| `intervalo_maximo_dias` | prazo do perfil (30 em geral, 15 para gestante e lactante) |
| `requer_pa`, `requer_glicemia`, `requer_temperatura`, `requer_antropometria`, `requer_orientacao_medicacao` | os cinco incisos do art. 3º § 4º |
| `requer_vacinal` | atividade típica do § 3º |
| `exige_protecao_respiratoria` | **sintético**, só o domínio estendido lê |

Colunas booleanas aceitam `sim/nao`, `s/n`, `true/false`, `1/0`, `x` ou vazio.
Separador `,` ou `;` (detectado sozinho). Erros de formato apontam a linha e a
coluna.

### 1.4 Urgência e atraso: de onde saem

Não são colunas, são **calculados**:

```
atraso  = dias_desde_ultima_visita - intervalo_maximo_dias
escore  = prioridade + 0,6 × (atraso / intervalo) × 3
urgência = ALTA se escore >= 3,5 | média se >= 2,0 | baixa abaixo disso
```

Isso importa porque **urgência ALTA tem de ser atendida antes de urgência
baixa** (restrição de precedência), e porque a seleção do turno ordena por
esse escore.

### 1.5 Instâncias sintéticas

Os experimentos não usam a microárea de exemplo: usam microáreas **sorteadas**
por `gerador.gerar(n, semente)`. Mesma semente, mesma instância, sempre. Elas
variam a **estrutura combinatória** do problema (quantos procedimentos
supervisionados, quantas glicemias, onde ficam) e **não estimam prevalência
epidemiológica**.

---

## 2. O que "pipeline completo" quer dizer

Quatro camadas, nesta ordem. Cada uma recebe o resultado da anterior.

```
   dados (CSV ou JSON)
        |
  [1] SELEÇÃO        quem entra no turno de hoje
        |            ordena por urgência, corta pelo orçamento de tempo
        |            --orcamento 240  --max-pacientes 6  --sem-selecao
        v
  [2] ROTEAMENTO     em que ordem visitar
        |            vizinho mais próximo + 2-opt, ou algoritmo genético
        |            --metodo nn2opt|ag   --distancias haversine|osrm
        v            saída: rota fixa + matriz + custo de desvio até a UBS
        |
  [3] PLANEJAMENTO   o que fazer em cada parada
        |            domínio PDDL, busca A*/h_max, A*/h_add, GBFS, UCS ou DFS
        |            --dominio legal|estendido   --estrategia ...
        v            NÃO pode mudar a ordem recebida da camada 2
        |
  [4] SAÍDA          roteiro do turno, ou comparação com a linha de base
```

**A camada 3 nunca escolhe a rota.** Ela recebe a ordem congelada no predicado
`(proxima-parada ?a ?b)` e só pode andar pelas arestas que a camada 2
autorizou. O que ela decide é o que fazer dentro de cada casa, quando acionar
a supervisão e **em qual parada vale a pena sair da rota para repor insumo**.

### Os comandos

| Comando | O que faz |
|---|---|
| `python -m acsplan dados` | mostra a microárea, o mapa e os recursos. Não planeja nada |
| `python -m acsplan planejar` | roda as camadas 1 a 3 e **compara com o executor procedural** |
| `python -m acsplan roteiro` | roda o mesmo pipeline, mas imprime o roteiro para o agente |
| `python -m acsplan experimentos` | roda os experimentos E1 a E12 |
| `python -m acsplan.testes` | roda os testes do código |

`planejar` é diagnóstico, para vocês. `roteiro` é o produto, para o agente.

---

## 3. Quem compara com quem

Aqui estava a confusão. **Não existe um experimento só**; cada um compara uma
coisa diferente, e nem todos envolvem Planning.

### Os quatro competidores

1. **Planejamento** — domínio PDDL + busca. Variantes: `astar-hmax` (ótimo
   garantido), `astar-hadd` e `gbfs` (rápidos, sem garantia), `ucs` e `dfs`
   (buscas cegas, sem heurística).
2. **Executor procedural reativo** — percorre a mesma rota, cumpre os mesmos
   protocolos, mas só descobre que falta recurso no momento de usá-lo.
   É o "um laço `for` faria o mesmo" implementado de verdade.
3. **Executor procedural corrigido** — o mesmo, com uma correção manual que
   confere os recursos ao chegar na casa.
4. **Roteirizadores** — vizinho mais próximo + 2-opt contra algoritmo
   genético. Isto é camada 2 e **não tem Planning nenhum envolvido**.

### A tabela que faltava

| Exp. | Compara | Pergunta |
|---|---|---|
| **E1** | planejamento × planejamento | até que tamanho cada busca aguenta? |
| **E2** | planejamento × procedural reativo | o planejamento ganha de um laço simples? |
| **E3** | planejamento × procedural | ambos reconhecem turno impossível? a que custo? |
| **E4** | **2-opt × algoritmo genético** | qual roteiriza melhor? *(sem Planning)* |
| **E5** | política de seleção × corte arbitrário | escolher o turno por critério muda algo? *(sem Planning)* |
| **E6** | domínio legal × domínio estendido | quanto custa acrescentar regras? |
| **E7** | planejamento × procedural **corrigido** | e se consertarem o laço simples? |
| **E8** | 2-opt × AG, **com e sem precedência** | de onde vinha a vantagem do AG? |
| **E9** | planejamento satisfaciente × procedural corrigido | e na configuração que escala? |
| **E10** | os três, com **regras novas** | a correção manual generaliza? |
| **E11** | planejamento × **busca cega** | um algoritmo trivial faz o mesmo? |
| **E12** | nosso planejador × **pyperplan** | nosso planejador está certo? |

**E1 a E6 medem o sistema. E7 a E11 tentam derrubar as conclusões de E1 a E6,
e três conseguiram.** E12 é verificação de corretude, não de desempenho.

---

## 4. Onde ler os resultados

### 4.1 Falso negativo: o que é e quem gera

> **Falso negativo** = dizer "este turno é impossível" quando existe uma
> sequência de atendimentos válida.

Quem gera são os **executores procedurais**, nunca o planejamento. O
mecanismo, que é sempre o mesmo:

1. o agente chega na casa e aciona a supervisão para aferir a pressão;
2. só **depois** descobre que acabaram as fitas de glicemia;
3. desvia até a unidade para repor, e **o deslocamento encerra a supervisão**
   que ele já tinha acionado;
4. ao voltar, precisa acionar uma **segunda** vez para a mesma casa;
5. gastando duas por casa, fica sem acionamentos antes do fim do turno e
   conclui que o turno é inviável.

O planejamento deriva das pré-condições que o desvio deve vir **antes** do
acionamento, e fecha com uma supervisão por residência.

**Como o experimento sabe que era um falso negativo?** Porque o planejamento
encontrou um plano para a mesma instância. Plano encontrado é prova de que o
turno era executável.

### 4.2 Onde o número aparece

No **E7** e no **E10**:

```
                                       REATIVO     CORRIGIDO
  --------------------------------------------------------------
  falsos negativos                  9/40 (22%)     0/40 (0%)
```

Lê-se: em 40 microáreas em que **existia** plano válido, o executor reativo
declarou 9 como inviáveis. Corrigido, nenhuma.

E o E10, que é o resultado central do trabalho:

```
    N |  planeja |        REATIVO |  CORRECAO ANTIGA |  CORRECAO NOVA
  TOT |       40 |    27/40 (68%) |      27/40 (68%) |      0/40 (0%)
```

A coluna `planeja ok` é quantas instâncias tinham plano comprovado. A correção
**antiga** (escrita para as regras antigas) entrega **benefício zero** diante
de regras novas. Uma correção **nova** zera. O planejamento, que não aparece
na tabela porque não falha em nenhuma, vai de 0% a 0% sem receber ajuste.

### 4.3 Como ler as outras tabelas

**Custos em minutos.** Todo custo de plano é tempo de turno: deslocamento mais
a duração de cada ação, pela tabela do próprio `.pddl`. Os dois lados são
precificados pela **mesma** tabela, de propósito.

**`--` significa que não terminou** no limite de tempo ou de expansões.

**`(N)` ao lado de um custo** significa que só N sementes concluíram. Nesse
caso a mediana é sobre um **subconjunto** e **não é comparável entre colunas**.
Essa armadilha já quase foi lida como contradição entre duas buscas ótimas.

**"procedural melhor que o ótimo" tem de ser sempre 0.** Não é resultado, é
verificação: valor diferente de zero significaria que a heurística `h_max` não
é admissível e a garantia de otimalidade caiu.

### 4.4 Onde está a conclusão

| Documento | Conteúdo |
|---|---|
| [`05-analise-e-conclusoes.md`](05-analise-e-conclusoes.md) | o percurso: o que caiu e o que sobreviveu |
| [`06-veredito-sobre-planning.md`](06-veredito-sobre-planning.md) | a resposta: faz sentido usar Planning? |
| [`03-metodo-experimental.md`](03-metodo-experimental.md) | tabelas completas de E1 a E6 |
| [`saida-experimentos.txt`](saida-experimentos.txt) | saída bruta de uma execução |

---

## 5. Testes: fumaça e regressão

São duas coisas diferentes, e as duas vivem em `python -m acsplan.testes`.

**Teste de fumaça** (*smoke test*) vem de eletrônica: liga o aparelho e vê se
sai fumaça. É o teste mais grosso possível, que só pergunta "isto funciona
minimamente?". Aqui são os que checam se os dois domínios são PDDL válido, se
o arquivo de exemplo carrega e planeja, se a rota respeita a precedência. Não
verificam se o resultado está **certo**, só se o sistema não quebra.

**Teste de regressão** existe por causa de um bug que **já aconteceu**. Depois
de corrigir, escreve-se um teste que falharia se o bug voltasse. "Regressão" é
o nome de um defeito corrigido que reaparece. Os nossos:

| Teste | Bug que ele vigia |
|---|---|
| glicemia estendida tem instâncias válidas | o *grounding* descartava combinações de parâmetros repetidos, e a glicemia do domínio estendido ficava sem nenhuma instância. O planejador passou a "provar" inviabilidade onde havia plano |
| planejador e executor usam a mesma tabela de custos | `retornar-a-rota` era cobrada de formas diferentes nos dois lados, e a comparação estava medindo com réguas distintas |
| o plano ótimo nunca perde para o procedural | se falhar, `h_max` deixou de ser admissível |
| inciso III não impõe encaminhamento | fixa uma decisão **de base legal**: o texto condiciona o encaminhamento a "quando necessário". Uma uniformização bem-intencionada do domínio apagaria a distinção sem ninguém notar |

> Dois testes já passaram **por vacuidade**: usavam uma instância fixa e saíam
> calados quando ela era inviável, de modo que davam "ok" sem verificar nada.
> Hoje varrem doze sementes e **falham se não exercitarem um mínimo de casos**.
> Um teste que não testa é pior que nenhum, porque dá confiança.

---

## 6. Receitas

```bash
# ver os dados antes de qualquer coisa
python -m acsplan dados

# usar a minha planilha
python -m acsplan dados --exportar-csv minha.csv     # gera o modelo
#   ... edite minha.csv ...
python -m acsplan dados --dados minha.csv            # confira
python -m acsplan roteiro --dados minha.csv --orcamento 240

# ver o planejamento ganhando do laço simples
python -m acsplan experimentos --experimento e7

# ver o resultado central do trabalho
python -m acsplan experimentos --experimento e10

# ver que um algoritmo trivial não resolve
python -m acsplan experimentos --experimento e11

# conferir que o nosso planejador está certo
pip install pyperplan
python -m acsplan experimentos --experimento e12

# provar que o sistema detecta turno impossível
python -m acsplan planejar --sem-curso-tecnico
```


---

## Realimentação do passo 3 para o passo 2

Até aqui o pipeline era de mão única: a camada geométrica entregava uma rota
e a camada lógica dizia se ela servia. Com `--realimentar`, quando o
planejamento prova que a rota corrente é inexequível, o pipeline volta ao
passo 2, pede **outra** rota e tenta de novo.

```bash
python -m acsplan planejar --instancia-sintetica 12 7 --orcamento 240     --realimentar --roteador-cego
```

As rotas alternativas saem de duas fontes, conforme o método: outra execução
do algoritmo genético (semente diferente), ou uma construção gulosa
aleatorizada, no estilo GRASP, seguida de 2-opt. Rotas repetidas são
descartadas sem gastar busca.

`--roteador-cego` faz o roteirizador ignorar a precedência por urgência,
enquanto a camada normativa continua exigindo-a. É a situação real de quem
troca a camada geométrica por um serviço externo que não conhece a norma: o
roteirizador otimiza distância, a camada lógica reprova o que viola a regra,
e o laço converge para uma rota que satisfaz as duas coisas.

### Nem toda inviabilidade se resolve com outra rota

Antes de iterar, o módulo diagnostica. Duas causas são **estruturais**, e
nenhuma reordenação das paradas as resolve:

1. o ACS não cumpre as condições do art. 3º § 4º (sem curso técnico ou sem
   equipamento) e há paciente que exige procedimento condicionado;
2. as janelas de supervisão do turno são menos numerosas que os pacientes
   que exigem procedimento do § 4º. Como a supervisão se encerra ao deixar a
   residência e não se repõe na unidade, cada uma dessas visitas consome ao
   menos uma janela, em qualquer ordem.

Nesses dois casos o laço para de saída e diz por quê, em vez de reprovar N
rotas pelo mesmo motivo.

---

## Saída visual: mapa e demonstração

```bash
python -m acsplan mapa --instancia-sintetica 12 7 --orcamento 240     --realimentar --roteador-cego     --saida saida/mapa.html --demonstracao saida/demonstracao.html
```

Gera dois arquivos HTML autocontidos, com os dados embutidos como JSON:

- **mapa da rota**: a rota final sobre o mapa real de Porto Alegre, com as
  paradas numeradas na ordem de visita, coloridas por urgência, os desvios de
  reposição em tracejado e o roteiro parada a parada ao lado. As famílias
  adiadas pela política aparecem apagadas.
- **demonstração**: os mesmos dados em sete passos navegáveis, que é o
  caminho que o sistema percorre: microárea inteira, seleção do turno, rota
  candidata, veredito do protocolo, rota seguinte quando a primeira é
  reprovada, veredito de novo, e o roteiro final.

Os dois exigem rede para **abrir**, não para gerar, porque os ladrilhos do
mapa vêm do OpenStreetMap. As cópias usadas na apresentação estão em
[`apresentacao/3/`](../apresentacao/3/).

As coordenadas são reais. Os dados clínicos são fictícios.
