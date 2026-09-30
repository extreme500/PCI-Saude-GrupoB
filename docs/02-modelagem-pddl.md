# Modelagem PDDL: decisões e por quê

Referência dos arquivos
[`acsplan/logica/dominios/dominio-legal.pddl`](../acsplan/logica/dominios/dominio-legal.pddl)
e
[`acsplan/logica/dominios/dominio-estendido.pddl`](../acsplan/logica/dominios/dominio-estendido.pddl).

---

## 1. O contrato entre as duas camadas

A camada geométrica entrega três coisas, e só três:

| Saída do roteirizador | Vira, no PDDL |
|---|---|
| ordem das paradas | `(proxima-parada ?l1 ?l2)` — **estático** |
| matriz de custos | `(= (custo-deslocamento ?l1 ?l2) N)` |
| custo de desvio até a UBS | `(= (custo-desvio ?l) N)` |

Trocar VMP+2-opt por OSRM, OR-Tools ou Google Distance Matrix não exige
mudar uma linha do domínio. É o ponto da arquitetura desacoplada.

O planejador **nunca escolhe a ordem das casas**. Ele só pode andar pelas
arestas que o roteirizador autorizou. O que ele decide é: o que fazer em cada
parada, quando acionar a supervisão, e em qual parada sair da rota para
reabastecer.

---

## 2. As quatro decisões de modelagem que importam

### 2.1 Predicados complementares (`pa-ok` em vez de `requer-pa`)

STRIPS não tem implicação. Não dá para escrever a pré-condição:

> "*se* o paciente exige glicemia, *então* a glicemia precisa estar medida"

A solução padrão é **inverter a polaridade**. Em vez de marcar quem precisa,
marca-se no estado inicial quem já está quitado:

```lisp
;; p5 é criança, não exige glicemia → já nasce quitado
(glicemia-ok p5)
;; p2 é diabético, exige → o fato NÃO está no init;
;;                          só a ação medir-glicemia-capilar produz
```

A pré-condição de `registrar-visita` vira então uma conjunção simples:
`(and (pa-ok ?p) (glicemia-ok ?p) (vacinal-ok ?p))`.

**Leia com atenção, porque é contraintuitivo:** no arquivo gerado, a *ausência*
de `(glicemia-ok p2)` é o que codifica "p2 precisa de glicemia".

### 2.2 Contadores por níveis discretos, não por fluentes numéricos

O estoque de fitas poderia ser `(= (fitas ?ag) 2)` com `:fluents`. Optamos por
níveis encadeados:

```lisp
(prox n0 n1) (prox n1 n2)
(fitas n2)            ; bolsa cheia
(nivel-maximo n2)
```

"Consumir uma fita" vira: exigir `(fitas ?n)` e `(prox ?n-1 ?n)`, remover
`(fitas ?n)` e adicionar `(fitas ?n-1)`. Em `n0` não existe predecessor, então
a ação simplesmente não é aplicável — o estoque zerado bloqueia sozinho.

**Vantagem:** mantém o domínio em STRIPS puro, compatível com qualquer
planejador e com o planejador didático do protótipo.
**Custo:** o número de objetos cresce linearmente com a capacidade. Para uma
bolsa de 50 fitas isso ficaria ruim, e fluentes numéricos seriam melhores.
Declare esse trade-off no relatório.

### 2.3 A UBS desdobrada em dois objetos (`ubs` e `ubs-fim`)

A rota é um tour fechado: `ubs → p1 → … → p8 → ubs`. Se a UBS fosse um único
objeto, as arestas `(proxima-parada casa-p8 ubs)` e `(proxima-parada ubs
casa-p1)` fechariam um **ciclo**, e o planejador poderia dar voltas na rota
indefinidamente.

Isso não é teórico: na primeira versão do protótipo, com o ciclo presente,
A\*/h_max **expandiu 105 mil nós em 60 s sem achar plano** numa instância de 8
pacientes. Desdobrando a UBS em dois objetos (mesma unidade física, papéis
distintos de partida e de chegada/reposição), o grafo fica acíclico, a posição
do agente passa a ser monótona ao longo da rota, e a **mesma instância passou a
ser resolvida em 0,48 s com 1.446 nós**.

Desdobrar objetos para eliminar ciclos é técnica padrão de compilação em
planejamento. Vale como resultado a ser relatado: a diferença entre um modelo
inviável e um viável foi uma decisão de *modelagem*, não de algoritmo.

### 2.4 A supervisão é vinculada à residência

`mover` e `desviar-para-ubs` têm `(not (supervisao-ativa ?ag))` no efeito: sair
da residência encerra a assistência do profissional de nível superior.

Isso é o que cria o acoplamento entre a reposição de insumos e a supervisão — e
é a origem do resultado principal do experimento E2, em que o executor guloso
desperdiça janelas ao desviar depois de já ter acionado a supervisão.

### 2.5 Precedência por urgência sem sair de STRIPS

O nível de urgência, calculado a partir da prioridade clínica e do atraso, induz
uma restrição de ordem: urgência alta antes de urgência baixa. Expressar isso
exigiria quantificação universal ("todos os urgentes já visitados"), que STRIPS
não tem.

A solução usa o mesmo truque de contador dos insumos. `(altos-pendentes n)`
começa no número de pacientes de urgência alta, `iniciar-visita-urgente`
decrementa, e `iniciar-visita-adiavel` exige que o contador esteja em zero. São
três variantes de início de visita (urgente, comum e adiável) em vez de uma.

Quando a precedência está desativada, nenhum paciente recebe os fatos de
urgência e o contador nasce em zero, de modo que só a variante comum se aplica
e a restrição desaparece sozinha, sem `if` em lugar nenhum.

### 2.6 Dois domínios, e por quê

`dominio-legal.pddl` contém somente regras com base em norma vigente, e cada
ação traz no comentário o dispositivo que a fundamenta. Os cinco incisos do
art. 3º § 4º estão modelados. Vale notar a assimetria preservada do inciso III:
seu texto condiciona o encaminhamento a "quando necessário", e por isso a
aferição de temperatura **não** produz `pendencia-encaminhamento`, ao contrário
dos incisos I e II, cujo encaminhamento é incondicional.

`dominio-estendido.pddl` acrescenta três protocolos marcados `[SINTETICO]`:
higienização das mãos, proteção respiratória e descarte de perfurocortante.
Nenhum consta de norma. Existem para medir o comportamento do método sob
complexidade normativa crescente, e a separação em dois arquivos é o que
permite não confundir lei com suposição nossa.

A comparação entre eles é o experimento E6, e o resultado é forte: três
protocolos adicionais derrubam o limite da busca ótima de cerca de 14 pacientes
para menos de 6.

---

## 3. A armadilha do grounding

Vale registrar porque custou tempo e porque o sintoma era enganoso.

A instanciação de ações descartava combinações de parâmetros com objetos
repetidos, assumindo hipótese de nomes únicos. Isso é inofensivo enquanto
nenhuma ação tem dois contadores do mesmo tipo. O domínio estendido quebrou
essa premissa: `medir-glicemia-capilar` consome uma fita **e** ocupa espaço no
coletor, e a combinação legítima `(n2, n1, n3, n2)` era descartada por repetir
`n2`.

O efeito não foi um erro, foi um **resultado plausível**: o planejador passou a
responder "inviável" para turnos perfeitamente executáveis. Sem desconfiar e ir
atrás de qual fato do objetivo estava inalcançável, isso teria ido para o
relatório como se fosse uma propriedade do problema.

As combinações degeneradas que a remoção readmite são eliminadas pela poda
estática, porque predicados como `(prox ?n ?n)` nunca constam do estado inicial.

---

## 4. Mapa ação ↔ norma

| Ação | Base | Pré-condições relevantes |
|---|---|---|
| `aferir-pressao-arterial` | art. 3º § 4º I | curso técnico + equipamento + supervisão |
| `medir-glicemia-capilar` | art. 3º § 4º II | idem + uma fita em estoque |
| `aferir-temperatura-axilar` | art. 3º § 4º III | idem, **sem** obrigação de encaminhamento |
| `orientar-administracao-medicacao` | art. 3º § 4º IV | idem |
| `verificacao-antropometrica` | art. 3º § 4º V | idem |
| `registrar-encaminhamento` | art. 3º § 4º I e II (*"encaminhando o paciente"*) | pendência aberta |
| `verificar-caderneta-vacinal` | art. 3º § 3º IV "c" e V "c" | **nenhuma das três** — atividade típica |
| `registrar-visita` | art. 3º § 3º II | tudo quitado e sem pendência |
| `mover`, `desviar-para-ubs`, `retornar-a-rota`, `reabastecer-fitas`, `acionar-supervisao`, `iniciar-visita` | operacionais | — |

Texto literal das normas em [`04-fontes.md`](04-fontes.md).

**Custos.** `desviar-para-ubs` já cobra a ida **e** a volta (`custo-desvio` =
2× o trajeto de ida), por isso `retornar-a-rota` tem custo zero. Não é
esquecimento.

---

## 5. Teste de declaratividade

O argumento "mudou a regra, não mudou o código" é verificável em um comando:

```bash
python -m acsplan planejar --sem-curso-tecnico
```

Isso remove um único fato do estado inicial. Nenhuma linha de Python muda.
O planejador responde:

```
SEM PLANO — objetivo inalcançável (detecção na relaxação)
0 nós expandidos, 0.0002 s
```

Ou seja: ele **prova** que, sem o curso técnico, nenhuma sequência de ações
cumpre o protocolo desses pacientes — e prova instantaneamente, porque nenhuma
ação no domínio relaxado produz `(pa-ok ?p)`.

Para contrastar, o experimento E3(b) torna o turno inviável por **falta de
recurso** (poucas janelas de supervisão). Aí a detecção custa exaurir o espaço
de estados, porque a heurística de relaxação ignora efeitos de remoção e não
enxerga o contador baixando. Mesma resposta, custo muito diferente — bom
material de discussão.

---

## 6. Limitações do domínio

- Um único agente. Múltiplos ACS exigiriam repensar a alocação de pacientes,
  e o problema voltaria a ser HHCRSP completo.
- A precedência só liga os extremos de urgência. Encadear todos os níveis
  produziria uma ordem quase total e esvaziaria a otimização geométrica.
- Sem janelas de tempo por paciente e sem duração real das ações (custos são
  estimativas de ordem de grandeza, não medições).
- Prioridade clínica e intervalo máximo entram na seleção do turno e na
  precedência, mas não na função objetivo do planejador: ele minimiza tempo,
  não urgência atendida.
