# Modelagem PDDL: decisões e por quê

Referência do arquivo [`prototipo/camada_logica/dominio.pddl`](../prototipo/camada_logica/dominio.pddl).

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

---

## 3. Mapa ação ↔ norma

| Ação | Base | Pré-condições relevantes |
|---|---|---|
| `aferir-pressao-arterial` | art. 3º § 4º I | curso técnico + equipamento + supervisão |
| `medir-glicemia-capilar` | art. 3º § 4º II | idem + uma fita em estoque |
| `registrar-encaminhamento` | art. 3º § 4º I e II (*"encaminhando o paciente"*) | pendência aberta |
| `verificar-caderneta-vacinal` | art. 3º § 3º IV "c" e V "c" | **nenhuma das três** — atividade típica |
| `registrar-visita` | art. 3º § 3º II | tudo quitado e sem pendência |
| `mover`, `desviar-para-ubs`, `retornar-a-rota`, `reabastecer-fitas`, `acionar-supervisao`, `iniciar-visita` | operacionais | — |

Texto literal das normas em [`04-fontes.md`](04-fontes.md).

**Custos.** `desviar-para-ubs` já cobra a ida **e** a volta (`custo-desvio` =
2× o trajeto de ida), por isso `retornar-a-rota` tem custo zero. Não é
esquecimento.

---

## 4. Teste de declaratividade

O argumento "mudou a regra, não mudou o código" é verificável em um comando:

```bash
python prototipo/orquestrador.py --sem-curso-tecnico
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

## 5. Limitações do domínio

- Um único agente. Múltiplos ACS exigiriam repensar a alocação de pacientes,
  e o problema voltaria a ser HHCRSP completo.
- Sem janelas de tempo por paciente e sem duração real das ações (custos são
  estimativas de ordem de grandeza, não medições).
- Incisos III, IV e V do § 4º não modelados.
- Prioridade clínica e intervalo máximo entre visitas estão nos dados, mas não
  entram no objetivo nem na seleção do turno. É a lacuna mais visível em
  relação ao enunciado do Ciclo 2.
