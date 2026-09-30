# PCI-Saude-GrupoB

Projeto em Ciência e Inovação (INF99003), Ciclo 2
Planejamento de visitas domiciliares de Agentes Comunitários de Saúde na APS/SUS.

Gabriel Pieruccini Knopp · Arthur Andrade da Silva · Izadora Candotti de Oliveira

---

## A ideia

O roteamento físico (em que ordem visitar as casas) é resolvido por algoritmos
de grafos, que é o que eles fazem bem. O **Planejamento Automatizado** cuida do
que um roteirizador não sabe fazer: garantir que cada atendimento cumpra as
condições legais do art. 3º da Lei 11.350/2006 (curso técnico, equipamento
disponível, assistência de profissional de nível superior, encaminhamento
obrigatório) sob **recursos finitos**, que só se repõem na unidade de saúde.

A escolha do paradigma não é estética. A norma que rege o trabalho do ACS já tem
a forma *"a ação X só é permitida se A ∧ B ∧ C, e executar X obriga Y"*, que é
literalmente um esquema de ação STRIPS.

Documento do projeto: [`projeto/PROJETO-CICLO2.md`](projeto/PROJETO-CICLO2.md)
(e a versão `.docx` ao lado).

---

## Como rodar

Python 3.10+, sem dependências obrigatórias.

```bash
# pipeline completo: seleção, roteamento, planejamento, comparação
python -m acsplan planejar

# o roteiro do turno no formato que o agente usa
python -m acsplan roteiro --orcamento 240 --salvar roteiro.txt

# algoritmo genético e distâncias reais de rua (OSRM, cai para haversine offline)
python -m acsplan planejar --metodo ag --distancias osrm

# domínio com protocolos sintéticos (mais pesado: prefira busca satisfaciente)
python -m acsplan planejar --dominio estendido --max-pacientes 4 --estrategia gbfs

# teste de declaratividade: remove UM fato do estado inicial
python -m acsplan planejar --sem-curso-tecnico

# experimentos
python -m acsplan experimentos                      # todos
python -m acsplan experimentos --experimento e4     # um só
```

---

## Estrutura

```
acsplan/                      o sistema
  cli.py                      interface de linha de comando
  selecao/politica.py         [1] quem entra no turno (prioridade + atraso)
  geo/
    distancias.py             matriz de custos: haversine ou OSRM, com cache
    roteirizador.py           [2] ordem das paradas + precedência por urgência
    genetico.py               algoritmo genético com reparo de precedência
  logica/
    dominios/
      dominio-legal.pddl      só regras com base em norma vigente
      dominio-estendido.pddl  o legal + 3 protocolos SINTÉTICOS
    gerador_problema.py       traduz (dados + rota) em problema PDDL
    planejador.py             [3] parser PDDL, grounding, A*/GBFS
    executor_guloso.py        linha de base procedural para comparação
  saida/roteiro.py            [4] roteiro do turno para o agente
  dados/                      microárea de exemplo e gerador de instâncias
  experimentos/rodar.py       E1 a E6

projeto/                      documento do projeto (md + docx + gerador)
docs/                         análise, modelagem, método e fontes
apresentacao/                 slides, versão do orador e cheatsheet
```

---

## As quatro camadas

| | Decide | Como |
|---|---|---|
| **1. Seleção** | quem entra no turno | escore de prioridade clínica e atraso, sob orçamento de tempo |
| **2. Roteamento** | em que ordem visitar | vizinho mais próximo + 2-opt, ou algoritmo genético; distâncias por haversine ou OSRM |
| **3. Planejamento** | o que fazer em cada parada | domínio PDDL (STRIPS com custos), busca A\*/h_max, A\*/h_add ou GBFS |
| **4. Saída** | o que o agente recebe | roteiro passo a passo, só com o essencial |

O contrato entre 2 e 3 é estreito de propósito: a camada geométrica entrega a
ordem das paradas, a matriz de custos e o custo de desvio até a unidade, e o
planejador não pode alterar a ordem recebida. Trocar o roteirizador não exige
mudar uma linha do domínio.

---

## Os dois domínios

`dominio-legal.pddl` contém **somente** regras com base em norma vigente, e cada
ação traz no comentário o dispositivo que a fundamenta. Os cinco incisos do
art. 3º § 4º estão modelados, inclusive a assimetria do inciso III, cujo
encaminhamento é condicional ("quando necessário") e por isso não é imposto como
efeito.

`dominio-estendido.pddl` é o mesmo domínio acrescido de **três protocolos
hipotéticos**, marcados `[SINTETICO]`: higienização das mãos, proteção
respiratória e descarte de perfurocortante. Eles não constam de norma alguma e
existem para medir como o método se comporta quando a complexidade normativa
cresce. O resultado dessa comparação é o experimento E6.

---

## Fidelidade factual

Pacientes, condições e datas são **fictícios**. As coordenadas são reais apenas
para dar ordem de grandeza à matriz de distâncias. As regras clínicas vêm do
texto literal da Lei 11.350/2006 (redação da Lei 13.595/2018) e da PNAB,
transcrito com links em [`docs/04-fontes.md`](docs/04-fontes.md), que separa o
que é norma, o que é parâmetro escolhido por nós e o que é ficção.

O número de janelas de supervisão por turno, a capacidade de insumos e os custos
das ações em minutos são **parâmetros nossos**, não normas.
