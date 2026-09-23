;; ============================================================================
;;  DOMINIO: visita-domiciliar-acs
;;  PCI Projeto 2 - Grupo B - prototipo da camada de Planejamento Automatizado
;; ----------------------------------------------------------------------------
;;  PAPEL DESTE DOMINIO NA ARQUITETURA
;;  A camada geometrica (roteirizador) ja decidiu a ORDEM das paradas. Ela e
;;  entregue aqui como o predicado estatico (proxima-parada ?l1 ?l2). Este
;;  dominio NAO procura a menor rota: ele decide O QUE FAZER em cada parada e
;;  QUANDO desviar ate a UBS para repor insumos, respeitando as normas legais.
;;
;;  FUNDAMENTO LEGAL DE CADA REGRA (texto literal em docs/04-fontes.md)
;;  - Lei 11.350/2006, art. 3o par. 4o (red. Lei 13.595/2018): afericao de PA,
;;    medicao de glicemia capilar e afericao de temperatura so sao atividades
;;    do ACS "desde que [...] tenha concluido curso tecnico e tenha disponiveis
;;    os equipamentos adequados", "assistidas por profissional de saude de
;;    nivel superior, membro da equipe", e obrigam o encaminhamento do paciente
;;    a unidade de saude de referencia.
;;  - Lei 11.350/2006, art. 3o par. 3o, II: registro dos dados da visita.
;;  - Lei 11.350/2006, art. 3o par. 3o, IV "c" e V "c": verificacao do estado
;;    vacinal (crianca, gestante, pessoa idosa, populacao de risco).
;;
;;  OBSERVACAO DE MODELAGEM
;;  O estoque de fitas de glicemia e representado por niveis discretos
;;  encadeados por (prox ?menor ?maior) em vez de fluentes numericos, para
;;  manter o dominio em STRIPS puro e compativel com o planejador didatico
;;  incluido no prototipo. Ver docs/02-modelagem-pddl.md, secao "limitacoes".
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
    (desvio-ubs ?l - local ?ubs - local)       ; estatico: desvio disponivel
    (fora-da-rota ?ag - agente ?l - local)     ; agente saiu da rota em ?l

    ;; ---- habilitacao legal do agente (art. 3o par. 4o) ----
    (curso-tecnico-concluido ?ag - agente)
    (equipamento-disponivel ?ag - agente)
    (supervisao-ativa ?ag - agente)            ; profissional de nivel superior

    ;; ---- estado do atendimento ----
    (visitado ?p - paciente)
    (pa-ok ?p - paciente)         ; PA aferida OU nao exigida para este paciente
    (glicemia-ok ?p - paciente)   ; idem
    (vacinal-ok ?p - paciente)    ; idem
    (pendencia-encaminhamento ?p - paciente)
    (protocolo-cumprido ?p - paciente)

    ;; ---- insumos: contador discreto de fitas de glicemia ----
    (fitas ?n - nivel)
    (prox ?menor - nivel ?maior - nivel)       ; estatico
    (nivel-maximo ?n - nivel)                  ; estatico

    ;; ---- supervisao: janelas de teleorientacao disponiveis no turno ----
    (janelas ?n - nivel)
  )

  (:functions
    (total-cost)
    (custo-deslocamento ?l1 - local ?l2 - local)  ; minutos, da matriz real
    (custo-desvio ?l - local)                     ; ida e volta ate a UBS
  )

  ;; ==========================================================================
  ;;  DESLOCAMENTO
  ;; ==========================================================================

  ;; Avanca para a proxima parada da rota definida pelo roteirizador.
  ;; Sair da residencia encerra a teleorientacao em curso: a supervisao do
  ;; profissional de nivel superior e vinculada ao atendimento (art. 3o p.4o).
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
    :effect (and (not (em ?ag ?ubs))
                 (em ?ag ?l)
                 (not (fora-da-rota ?ag ?l))
                 ;; custo ZERO e proposital, nao esquecimento: a volta ja foi
                 ;; cobrada em (custo-desvio ?l), que e o trajeto de IDA E
                 ;; VOLTA. O incremento explicito evita que o parser aplique
                 ;; o custo unitario padrao de STRIPS.
                 (increase (total-cost) 0))
  )

  ;; ==========================================================================
  ;;  RECURSOS
  ;; ==========================================================================

  ;; Reposicao de fitas so existe na UBS: e o que acopla as visitas entre si.
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

  ;; Aciona o profissional de nivel superior da equipe (art. 3o p.4o, caput).
  ;; O numero de acionamentos no turno e finito: consome uma janela.
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
  ;;  ATENDIMENTO
  ;; ==========================================================================

  (:action iniciar-visita
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (not (visitado ?p)))
    :effect (and (visitado ?p)
                 (increase (total-cost) 5))
  )

  ;; Art. 3o par. 4o, I. Precondicoes = as tres condicoes legais cumulativas.
  ;; Efeito = a obrigacao legal de encaminhamento a unidade de referencia.
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

  ;; Art. 3o par. 4o, II. Alem das condicoes legais, consome uma fita reagente.
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

  ;; Art. 3o par. 3o, IV "c" e V "c". Atividade tipica: nao exige curso
  ;; tecnico, equipamento nem supervisao. O contraste e proposital.
  (:action verificar-caderneta-vacinal
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (vacinal-ok ?p)))
    :effect (and (vacinal-ok ?p)
                 (increase (total-cost) 3))
  )

  ;; Art. 3o par. 4o, I e II: "encaminhando o paciente para a unidade de saude
  ;; de referencia". Sem isto o protocolo do paciente nao fecha.
  (:action registrar-encaminhamento
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (pendencia-encaminhamento ?p))
    :effect (and (not (pendencia-encaminhamento ?p))
                 (increase (total-cost) 2))
  )

  ;; Art. 3o par. 3o, II: registro dos dados da visita. Fecha o protocolo.
  (:action registrar-visita
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (pa-ok ?p)
                       (glicemia-ok ?p)
                       (vacinal-ok ?p)
                       (not (pendencia-encaminhamento ?p))
                       (not (protocolo-cumprido ?p)))
    :effect (and (protocolo-cumprido ?p)
                 (increase (total-cost) 2))
  )
)
