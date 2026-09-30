;; ============================================================================
;;  DOMINIO: visita-domiciliar-acs  (versao LEGAL)
;;  Projeto em Ciencia e Inovacao - INF99003 - Grupo B
;; ----------------------------------------------------------------------------
;;  ESCOPO DESTE ARQUIVO
;;  Este dominio contem SOMENTE regras com base em norma vigente. Cada acao
;;  tem, no comentario que a precede, o dispositivo legal que a fundamenta.
;;  Regras adicionais, hipoteticas, vivem em dominio-estendido.pddl e estao
;;  marcadas la como sinteticas. A separacao e proposital: permite medir o
;;  comportamento do planejador sob complexidade normativa crescente sem
;;  misturar o que e lei com o que e suposicao nossa.
;;
;;  PAPEL NA ARQUITETURA
;;  A camada geometrica ja decidiu a ORDEM das paradas, entregue aqui no
;;  predicado estatico (proxima-parada ?l1 ?l2). Este dominio NAO procura a
;;  menor rota: decide O QUE FAZER em cada parada e QUANDO desviar ate a UBS
;;  para repor insumos.
;;
;;  FUNDAMENTO LEGAL (texto literal em docs/04-fontes.md)
;;  Lei 11.350/2006, art. 3o, na redacao dada pela Lei 13.595/2018.
;;
;;  DELIMITACAO ENTRE NORMA E MODELAGEM
;;  A lei exige assistencia de profissional de nivel superior, sem estipular
;;  forma, duracao ou frequencia. Representa-la como recurso discreto e finito
;;  por turno, e encerra-la quando o agente deixa a residencia, sao decisoes
;;  de modelagem deste trabalho, nao determinacoes legais.
;; ============================================================================

(define (domain visita-domiciliar-acs)

  (:requirements :strips :typing :negative-preconditions :action-costs)

  (:types
    agente paciente local nivel - object
  )

  (:predicates
    ;; ---- posicao e rota (rota FIXADA pela camada geometrica) ----
    (em ?ag - agente ?l - local)
    (proxima-parada ?l1 - local ?l2 - local)   ; estatico: vem do roteirizador
    (residencia-de ?p - paciente ?l - local)   ; estatico
    (e-ubs ?l - local)                         ; estatico
    (desvio-ubs ?l - local ?ubs - local)       ; estatico
    (fora-da-rota ?ag - agente ?l - local)

    ;; ---- habilitacao legal do agente (art. 3o par. 4o, caput) ----
    (curso-tecnico-concluido ?ag - agente)
    (equipamento-disponivel ?ag - agente)
    (supervisao-ativa ?ag - agente)

    ;; ---- precedencia por urgencia ----
    ;; Classificacao produzida pela camada de selecao a partir da prioridade
    ;; clinica e do atraso. Quando a precedencia esta desativada, nenhum
    ;; paciente recebe estes fatos e a restricao desaparece sozinha.
    (urgencia-alta ?p - paciente)              ; estatico
    (urgencia-baixa ?p - paciente)             ; estatico
    (altos-pendentes ?n - nivel)               ; contador regressivo

    ;; ---- estado do atendimento ----
    ;; Polaridade invertida: marca-se quem JA esta quitado. A ausencia de
    ;; (X-ok ?p) no estado inicial e o que codifica "o paciente exige X".
    (visitado ?p - paciente)
    (pa-ok ?p - paciente)
    (glicemia-ok ?p - paciente)
    (temperatura-ok ?p - paciente)
    (antropometria-ok ?p - paciente)
    (orientacao-ok ?p - paciente)
    (vacinal-ok ?p - paciente)
    (pendencia-encaminhamento ?p - paciente)
    (protocolo-cumprido ?p - paciente)

    ;; ---- insumos: contador discreto de fitas de glicemia ----
    (fitas ?n - nivel)
    (prox ?menor - nivel ?maior - nivel)       ; estatico
    (nivel-maximo ?n - nivel)                  ; estatico
    (nivel-zero ?n - nivel)                    ; estatico

    ;; ---- supervisao: acionamentos disponiveis no turno ----
    (janelas ?n - nivel)
  )

  (:functions
    (total-cost)
    (custo-deslocamento ?l1 - local ?l2 - local)
    (custo-desvio ?l - local)
  )

  ;; ==========================================================================
  ;;  DESLOCAMENTO
  ;; ==========================================================================

  ;; Sair da residencia encerra a teleorientacao em curso: a assistencia do
  ;; profissional de nivel superior e vinculada ao atendimento (MODELAGEM).
  (:action mover
    :parameters (?ag - agente ?origem - local ?destino - local)
    :precondition (and (em ?ag ?origem)
                       (proxima-parada ?origem ?destino))
    :effect (and (not (em ?ag ?origem))
                 (em ?ag ?destino)
                 (not (supervisao-ativa ?ag))
                 (increase (total-cost) (custo-deslocamento ?origem ?destino)))
  )

  ;; Desvio nao previsto na rota, para reposicao de insumos na UBS.
  ;; E a decisao combinatoria central deste dominio: o planejador escolhe
  ;; EM QUAL parada vale a pena sair da rota.
  (:action desviar-para-ubs
    :parameters (?ag - agente ?l - local ?ubs - local)
    :precondition (and (em ?ag ?l)
                       (desvio-ubs ?l ?ubs))
    :effect (and (not (em ?ag ?l))
                 (em ?ag ?ubs)
                 (fora-da-rota ?ag ?l)
                 (not (supervisao-ativa ?ag))
                 (increase (total-cost) (custo-desvio ?l)))
  )

  (:action retornar-a-rota
    :parameters (?ag - agente ?ubs - local ?l - local)
    :precondition (and (em ?ag ?ubs)
                       (e-ubs ?ubs)
                       (fora-da-rota ?ag ?l))
    ;; custo ZERO e proposital: a volta ja foi cobrada em (custo-desvio ?l),
    ;; que e o trajeto de ida E volta. O incremento explicito evita que o
    ;; parser aplique o custo unitario padrao de STRIPS.
    :effect (and (not (em ?ag ?ubs))
                 (em ?ag ?l)
                 (not (fora-da-rota ?ag ?l))
                 (increase (total-cost) 0))
  )

  ;; ==========================================================================
  ;;  RECURSOS
  ;; ==========================================================================

  (:action reabastecer-fitas
    :parameters (?ag - agente ?ubs - local ?atual - nivel ?cheio - nivel)
    :precondition (and (em ?ag ?ubs)
                       (e-ubs ?ubs)
                       (fitas ?atual)
                       (nivel-maximo ?cheio))
    :effect (and (not (fitas ?atual))
                 (fitas ?cheio)
                 (increase (total-cost) 4))
  )

  ;; Aciona o profissional de nivel superior da equipe (art. 3o par. 4o, caput).
  (:action acionar-supervisao
    :parameters (?ag - agente ?n - nivel ?n-1 - nivel)
    :precondition (and (janelas ?n)
                       (prox ?n-1 ?n)
                       (not (supervisao-ativa ?ag)))
    :effect (and (supervisao-ativa ?ag)
                 (not (janelas ?n))
                 (janelas ?n-1)
                 (increase (total-cost) 3))
  )

  ;; ==========================================================================
  ;;  INICIO DO ATENDIMENTO
  ;;  Tres variantes que implementam a precedencia por urgencia em STRIPS
  ;;  puro. Um paciente de urgencia baixa so pode ser iniciado quando o
  ;;  contador de urgencias altas pendentes chegou a zero.
  ;; ==========================================================================

  (:action iniciar-visita-urgente
    :parameters (?ag - agente ?p - paciente ?l - local ?n - nivel ?n-1 - nivel)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (not (visitado ?p))
                       (urgencia-alta ?p)
                       (altos-pendentes ?n)
                       (prox ?n-1 ?n))
    :effect (and (visitado ?p)
                 (not (altos-pendentes ?n))
                 (altos-pendentes ?n-1)
                 (increase (total-cost) 5))
  )

  (:action iniciar-visita
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (not (visitado ?p))
                       (not (urgencia-alta ?p))
                       (not (urgencia-baixa ?p)))
    :effect (and (visitado ?p)
                 (increase (total-cost) 5))
  )

  (:action iniciar-visita-adiavel
    :parameters (?ag - agente ?p - paciente ?l - local ?zero - nivel)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (not (visitado ?p))
                       (urgencia-baixa ?p)
                       (altos-pendentes ?zero)
                       (nivel-zero ?zero))
    :effect (and (visitado ?p)
                 (increase (total-cost) 5))
  )

  ;; ==========================================================================
  ;;  PROCEDIMENTOS DO ART. 3o PAR. 4o
  ;;  Os cinco incisos compartilham as mesmas condicoes cumulativas do caput:
  ;;  curso tecnico concluido, equipamentos disponiveis e assistencia de
  ;;  profissional de saude de nivel superior.
  ;; ==========================================================================

  ;; Inciso I. O encaminhamento a unidade de referencia e incondicional no
  ;; texto: "encaminhando o paciente para a unidade de saude de referencia".
  (:action aferir-pressao-arterial
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (pa-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag))
    :effect (and (pa-ok ?p)
                 (pendencia-encaminhamento ?p)
                 (increase (total-cost) 4))
  )

  ;; Inciso II. Consome uma fita reagente, alem das condicoes do caput.
  ;; Encaminhamento tambem incondicional no texto.
  (:action medir-glicemia-capilar
    :parameters (?ag - agente ?p - paciente ?l - local ?n - nivel ?n-1 - nivel)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (glicemia-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag)
                       (fitas ?n)
                       (prox ?n-1 ?n))
    :effect (and (glicemia-ok ?p)
                 (pendencia-encaminhamento ?p)
                 (not (fitas ?n))
                 (fitas ?n-1)
                 (increase (total-cost) 5))
  )

  ;; Inciso III. Diferenca proposital em relacao aos incisos I e II: aqui o
  ;; texto diz "com o devido encaminhamento do paciente, QUANDO NECESSARIO".
  ;; Sendo condicional, o encaminhamento nao e imposto como efeito.
  (:action aferir-temperatura-axilar
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (temperatura-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag))
    :effect (and (temperatura-ok ?p)
                 (increase (total-cost) 3))
  )

  ;; Inciso IV: "a orientacao e o apoio, em domicilio, para a correta
  ;; administracao de medicacao de paciente em situacao de vulnerabilidade".
  (:action orientar-administracao-medicacao
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (orientacao-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag))
    :effect (and (orientacao-ok ?p)
                 (increase (total-cost) 6))
  )

  ;; Inciso V: "a verificacao antropometrica".
  (:action verificacao-antropometrica
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (antropometria-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag))
    :effect (and (antropometria-ok ?p)
                 (increase (total-cost) 4))
  )

  ;; ==========================================================================
  ;;  ATIVIDADES TIPICAS DO ART. 3o PAR. 3o
  ;;  Contraste proposital com o bloco acima: nao exigem curso tecnico,
  ;;  equipamento nem supervisao. A assimetria vem da lei.
  ;; ==========================================================================

  ;; Par. 3o, IV "c" e V "c": verificacao do estado vacinal de crianca,
  ;; gestante, pessoa idosa e populacao de risco.
  (:action verificar-caderneta-vacinal
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (vacinal-ok ?p)))
    :effect (and (vacinal-ok ?p)
                 (increase (total-cost) 3))
  )

  ;; Quitacao da obrigacao de encaminhamento gerada pelos incisos I e II.
  (:action registrar-encaminhamento
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (pendencia-encaminhamento ?p))
    :effect (and (not (pendencia-encaminhamento ?p))
                 (increase (total-cost) 2))
  )

  ;; Par. 3o, II: "o detalhamento das visitas domiciliares, com coleta e
  ;; registro de dados relativos a suas atribuicoes". Fecha o protocolo.
  (:action registrar-visita
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (pa-ok ?p)
                       (glicemia-ok ?p)
                       (temperatura-ok ?p)
                       (antropometria-ok ?p)
                       (orientacao-ok ?p)
                       (vacinal-ok ?p)
                       (not (pendencia-encaminhamento ?p))
                       (not (protocolo-cumprido ?p)))
    :effect (and (protocolo-cumprido ?p)
                 (increase (total-cost) 2))
  )
)
