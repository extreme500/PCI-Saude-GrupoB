# PCI-Saude-GrupoB

Projeto em Ciência e Inovação (INF99003) — **Ciclo 2**
Planejamento de visitas domiciliares de Agentes Comunitários de Saúde na APS/SUS.

> **Branch `feat/prototipo-planning`** — protótipo da abordagem híbrida
> *roteamento por grafos + Planejamento Automatizado (PDDL)*.

---

## A ideia em um parágrafo

O roteamento físico (em que ordem visitar as casas) é resolvido por uma
heurística de grafos, que é o que ela faz bem. O **Planejamento Automatizado**
cuida do que um roteirizador não sabe fazer: garantir que cada atendimento
cumpra as condições legais do art. 3º da Lei 11.350/2006 — curso técnico,
equipamento disponível, assistência de profissional de nível superior,
encaminhamento obrigatório — sob **recursos finitos** (fitas de glicemia que só
se repõem na UBS, número limitado de acionamentos da supervisão no turno).

A escolha do paradigma não é estética. A norma que rege o trabalho do ACS já
tem a forma *"a ação X só é permitida se A ∧ B ∧ C, e executar X obriga Y"* —
que é literalmente um esquema de ação STRIPS. Ver
[`docs/01-analise-da-proposta.md`](docs/01-analise-da-proposta.md), seção 2.

---

## Como rodar

Não há dependências. Python 3.10+ e mais nada — nem instalar planejador.

```bash
# pipeline completo sobre a microárea de exemplo
python prototipo/orquestrador.py

# buscas alternativas
python prototipo/orquestrador.py --estrategia astar-hadd   # rápida, subótima
python prototipo/orquestrador.py --estrategia gbfs         # mais rápida ainda

# teste de declaratividade: remove UM fato do estado inicial
python prototipo/orquestrador.py --sem-curso-tecnico

# os três experimentos
python prototipo/experimentos/rodar_experimentos.py
python prototipo/experimentos/rodar_experimentos.py --experimento e2
```

---

## Estrutura

```
apresentacao/
  slides.html                 deck para projetar (8 slides, paleta Creme)
  slides-orador.html          mesmos slides + roteiro de fala e cronometragem
  CHEATSHEET.md               bibliografia comentada, glossario e numeros

docs/
  01-analise-da-proposta.md   por que a abordagem é válida, e onde ela falha
  02-modelagem-pddl.md        decisões de modelagem e o mapa ação ↔ norma legal
  03-metodo-experimental.md   hipóteses, variáveis, resultados, ameaças à validade
  04-fontes.md                texto literal das leis; o que é norma, parâmetro e ficção

prototipo/
  orquestrador.py                  pipeline completo + relatório no terminal
  dados/
    microarea_exemplo.json         8 pacientes fictícios, coordenadas reais
    gerador_instancias.py          instâncias sintéticas para os experimentos
  camada_geo/
    roteirizador.py                haversine + vizinho mais próximo + 2-opt
  camada_logica/
    dominio.pddl                   o domínio de planejamento (comentado com a base legal)
    gerador_problema.py            traduz (dados + rota) → problema PDDL
    planejador.py                  parser PDDL + grounding + A*/GBFS (sem dependências)
    executor_guloso.py             linha de base: o "script simples" de Python
  experimentos/
    rodar_experimentos.py          E1 escalabilidade, E2 vs. guloso, E3 inviabilidade
```

O arquivo `camada_logica/problema_gerado.pddl` é **gerado** — não editar à mão.

---

## Resultados principais

Detalhes e tabelas completas em
[`docs/03-metodo-experimental.md`](docs/03-metodo-experimental.md).

**A pergunta cética que guiou o trabalho:** com a rota já fixa, o planejador faz
algo que um laço `for` não faria?

| | |
|---|---|
| Ganho de custo sobre o executor guloso | mediana **0%**, média 2,1%, máx. 10,3% |
| Turnos que o guloso declarou inviáveis **havendo** plano válido | **5 de 30 (17%)** |
| Prova de inviabilidade lógica (ACS sem curso técnico) | **0 nós expandidos**, 0,2 ms |
| Prova de inviabilidade de recurso (faltam janelas) | 332 nós, 109 ms |
| Planejamento ótimo (A\*/h_max) | 0,95 s com 8 casas; 5,4 s com 14; 22,6 s com 20 |

**A resposta honesta é matizada:** o planejador quase não economiza
deslocamento. O que ele entrega é corretude sob escassez, prova de
inviabilidade, garantia de otimalidade e declaratividade.

O mecanismo por trás dos 17% foi verificado nos planos: o guloso aciona a
supervisão, **depois** descobre que faltam fitas, desvia até a UBS — e o desvio
invalida a supervisão já acionada, gastando duas janelas na mesma casa. O
planejador deduz sozinho que basta desviar **antes** de acionar a supervisão.
Essa ordem não está escrita em lugar nenhum do domínio; ela sai das
pré-condições.

---

## Limitações conhecidas

Declaradas por extenso em
[`docs/01-analise-da-proposta.md`](docs/01-analise-da-proposta.md) (seção 6).
Em resumo: um único agente; prioridade clínica e intervalo máximo entre visitas
presentes nos dados mas fora da função objetivo; custos estimados por haversine
em vez de API de mapas; planejador didático em vez do Fast Downward; instâncias
sintéticas não calibradas epidemiologicamente.

---

## Fidelidade factual

Pacientes, condições e datas são **fictícios**. As coordenadas são reais apenas
para dar ordem de grandeza à matriz de distâncias. As regras clínicas modeladas
vêm do texto literal da Lei 11.350/2006 (redação da Lei 13.595/2018) e da PNAB
— transcrito com links em [`docs/04-fontes.md`](docs/04-fontes.md), que também
separa o que é norma, o que é parâmetro escolhido por nós e o que é ficção.
