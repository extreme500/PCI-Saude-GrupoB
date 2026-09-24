# Apresentação — Ciclo 2

Três arquivos, três usos diferentes.

| Arquivo | Para quê |
|---|---|
| [`slides.html`](slides.html) | **O deck que vai na tela.** 8 slides, texto enxuto. Abra no navegador e use ← → (ou espaço) para navegar. |
| [`slides-orador.html`](slides-orador.html) | **O que o apresentador lê.** Os mesmos 8 slides, cada um ao lado do roteiro de fala, cronometragem e respostas prováveis da banca. Não projetar. |
| [`CHEATSHEET.md`](CHEATSHEET.md) | **Para se situar no projeto.** Bibliografia comentada, glossário, números medidos e as perguntas que a banca provavelmente vai fazer. |

## Como apresentar

1. Todo mundo lê o `CHEATSHEET.md` antes — principalmente o glossário e a seção 6.
2. Quem apresenta abre o `slides-orador.html` num segundo monitor, tablet ou celular.
3. Projete o `slides.html` em tela cheia (`F11`).

Duração alvo: **~9 minutos** + perguntas. A cronometragem por slide está na
versão do orador.

## Estrutura dos 8 slides

1. Capa
2. **Problema & foco** — o recorte e por que ele é defensável
3. **Artigos** — quatro frentes da literatura e a lacuna que abrimos
4. **Questão inicial** — a pergunta cética e a hipótese nula
5. **Proposta** — a arquitetura em duas camadas
6. **Justificativa ‹1›** — a lei já está escrita como uma ação STRIPS
7. **Justificativa ‹2›** — a evidência preliminar medida
8. Fechamento — o que entrega e o que ainda falta

## Notas técnicas

- Arquivos HTML autocontidos. Única dependência externa são as fontes do Google
  Fonts; sem internet, caem para fontes do sistema sem quebrar o layout.
- Paleta **Creme**, com tema claro fixo (`color-scheme: light`) de propósito:
  uma apresentação precisa ficar idêntica em qualquer máquina, independentemente
  do tema do sistema do apresentador.
- Os dois decks imprimem em PDF pelo navegador (`Ctrl+P`) — o principal sai
  um slide por página.
