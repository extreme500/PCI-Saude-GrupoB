;; ============================================================================
;;  DOMINIO: visita-domiciliar-acs-estendido  (versao ESTENDIDA)
;;  Projeto em Ciencia e Inovacao - INF99003 - Grupo B
;; ----------------------------------------------------------------------------
;;  ATENCAO: ESTE ARQUIVO CONTEM REGRAS SINTETICAS.
;;
;;  Este dominio reproduz integralmente o dominio-legal.pddl e acrescenta
;;  tres protocolos operacionais HIPOTETICOS, marcados adiante com
;;  [SINTETICO]. Eles NAO constam da Lei 11.350/2006 nem da PNAB, e nao
;;  devem ser apresentados como norma em nenhuma circunstancia.
;;
;;  POR QUE ELE EXISTE
;;  A pergunta de pesquisa trata do valor do planejamento sob complexidade
;;  normativa. Com um unico dominio nao ha como observar como o metodo se
;;  comporta quando essa complexidade cresce. Manter dois dominios, um fiel
;;  a norma vigente e outro deliberadamente mais exigente, permite medir o
;;  efeito do acrescimo de regras isolando-o de tudo o mais.
;;
;;  AS TRES REGRAS SINTETICAS
;;  1. Higienizacao das maos antes de cada procedimento do par. 4o, com
;;     consumo de solucao alcoolica, reposta apenas na UBS.
;;  2. Protecao respiratoria para residencias sinalizadas, com estoque finito
;;     de mascaras e descarte obrigatorio ao sair.
;;  3. Descarte de material perfurocortante gerado pela glicemia capilar, em
;;     coletor de capacidade limitada, trocado apenas na UBS.
;;
;;  As tres compartilham a estrutura de acoplamento das regras reais: um
;;  recurso finito, reposto fora da rota, cujo esgotamento em uma parada
;;  afeta a viabilidade das seguintes.
;; ============================================================================

(define (domain visita-domiciliar-acs-estendido)

  (:requirements :strips :typing :negative-preconditions :action-costs)

  (:types
    agente paciente local nivel - object
  )

  (:predicates
    ;; ---- posicao e rota (rota FIXADA pela camada geometrica) ----
    (em ?ag - agente ?l - local)
    (proxima-parada ?l1 - local ?l2 - local)
    (residencia-de ?p - paciente ?l - local)
    (e-ubs ?l - local)
    (desvio-ubs ?l - local ?ubs - local)
    (fora-da-rota ?ag - agente ?l - local)

    ;; ---- habilitacao legal do agente (art. 3o par. 4o, caput) ----
    (curso-tecnico-concluido ?ag - agente)
    (equipamento-disponivel ?ag - agente)
    (supervisao-ativa ?ag - agente)

    ;; ---- precedencia por urgencia ----
    (urgencia-alta ?p - paciente)
    (urgencia-baixa ?p - paciente)
    (altos-pendentes ?n - nivel)

    ;; ---- estado do atendimento ----
    (visitado ?p - paciente)
    (pa-ok ?p - paciente)
    (glicemia-ok ?p - paciente)
    (temperatura-ok ?p - paciente)
    (antropometria-ok ?p - paciente)
    (orientacao-ok ?p - paciente)
    (vacinal-ok ?p - paciente)
    (pendencia-encaminhamento ?p - paciente)
    (protocolo-cumprido ?p - paciente)

    ;; ---- insumos ----
    (fitas ?n - nivel)
    (prox ?menor - nivel ?maior - nivel)
    (nivel-maximo ?n - nivel)
    (nivel-zero ?n - nivel)
    (janelas ?n - nivel)

    ;; ---- [SINTETICO] higienizacao das maos ----
    (maos-higienizadas ?ag - agente)
    (alcool ?n - nivel)

    ;; ---- [SINTETICO] protecao respiratoria ----
    (exige-protecao-respiratoria ?p - paciente)
    (mascara-vestida ?ag - agente)
    (mascaras ?n - nivel)
    (protecao-conferida ?ag - agente ?p - paciente)

    ;; ---- [SINTETICO] descarte de perfurocortante ----
    (coletor ?n - nivel)
    (nivel-maximo-coletor ?n - nivel)
    (nivel-maximo-alcool ?n - nivel)
    (nivel-maximo-mascaras ?n - nivel)
  )

  (:functions
    (total-cost)
    (custo-deslocamento ?l1 - local ?l2 - local)
    (custo-desvio ?l - local)
  )

  ;; ==========================================================================
  ;;  DESLOCAMENTO
  ;;  Alem de encerrar a supervisao, o deslocamento invalida a higienizacao e
  ;;  descarta a mascara [SINTETICO].
  ;; ==========================================================================

  (:action mover
    :parameters (?ag - agente ?origem - local ?destino - local)
    :precondition (and (em ?ag ?origem)
                       (proxima-parada ?origem ?destino))
    :effect (and (not (em ?ag ?origem))
                 (em ?ag ?destino)
                 (not (supervisao-ativa ?ag))
                 (not (maos-higienizadas ?ag))
                 (not (mascara-vestida ?ag))
                 (increase (total-cost) (custo-deslocamento ?origem ?destino)))
  )

  (:action desviar-para-ubs
    :parameters (?ag - agente ?l - local ?ubs - local)
    :precondition (and (em ?ag ?l)
                       (desvio-ubs ?l ?ubs))
    :effect (and (not (em ?ag ?l))
                 (em ?ag ?ubs)
                 (fora-da-rota ?ag ?l)
                 (not (supervisao-ativa ?ag))
                 (not (maos-higienizadas ?ag))
                 (not (mascara-vestida ?ag))
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
  ;;  [SINTETICO] HIGIENIZACAO DAS MAOS
  ;; ==========================================================================

  (:action higienizar-maos
    :parameters (?ag - agente ?n - nivel ?n-1 - nivel)
    :precondition (and (alcool ?n)
                       (prox ?n-1 ?n)
                       (not (maos-higienizadas ?ag)))
    :effect (and (maos-higienizadas ?ag)
                 (not (alcool ?n))
                 (alcool ?n-1)
                 (increase (total-cost) 2))
  )

  (:action repor-alcool
    :parameters (?ag - agente ?ubs - local ?atual - nivel ?cheio - nivel)
    :precondition (and (em ?ag ?ubs)
                       (e-ubs ?ubs)
                       (alcool ?atual)
                       (nivel-maximo-alcool ?cheio))
    :effect (and (not (alcool ?atual))
                 (alcool ?cheio)
                 (increase (total-cost) 3))
  )

  ;; ==========================================================================
  ;;  [SINTETICO] PROTECAO RESPIRATORIA
  ;;  A conferencia tem duas variantes: a residencia sinalizada exige mascara
  ;;  vestida, e as demais dispensam. Sem a conferencia, a visita nao inicia.
  ;; ==========================================================================

  (:action vestir-mascara
    :parameters (?ag - agente ?n - nivel ?n-1 - nivel)
    :precondition (and (mascaras ?n)
                       (prox ?n-1 ?n)
                       (not (mascara-vestida ?ag)))
    :effect (and (mascara-vestida ?ag)
                 (not (mascaras ?n))
                 (mascaras ?n-1)
                 (increase (total-cost) 2))
  )

  (:action repor-mascaras
    :parameters (?ag - agente ?ubs - local ?atual - nivel ?cheio - nivel)
    :precondition (and (em ?ag ?ubs)
                       (e-ubs ?ubs)
                       (mascaras ?atual)
                       (nivel-maximo-mascaras ?cheio))
    :effect (and (not (mascaras ?atual))
                 (mascaras ?cheio)
                 (increase (total-cost) 3))
  )

  (:action conferir-protecao-exigida
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (exige-protecao-respiratoria ?p)
                       (mascara-vestida ?ag)
                       (not (protecao-conferida ?ag ?p)))
    :effect (and (protecao-conferida ?ag ?p)
                 (increase (total-cost) 1))
  )

  (:action conferir-protecao-dispensada
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (not (exige-protecao-respiratoria ?p))
                       (not (protecao-conferida ?ag ?p)))
    :effect (and (protecao-conferida ?ag ?p)
                 (increase (total-cost) 0))
  )

  ;; ==========================================================================
  ;;  [SINTETICO] DESCARTE DE PERFUROCORTANTE
  ;; ==========================================================================

  (:action trocar-coletor
    :parameters (?ag - agente ?ubs - local ?atual - nivel ?cheio - nivel)
    :precondition (and (em ?ag ?ubs)
                       (e-ubs ?ubs)
                       (coletor ?atual)
                       (nivel-maximo-coletor ?cheio))
    :effect (and (not (coletor ?atual))
                 (coletor ?cheio)
                 (increase (total-cost) 3))
  )

  ;; ==========================================================================
  ;;  INICIO DO ATENDIMENTO
  ;;  Tres variantes implementam a precedencia por urgencia. Todas exigem a
  ;;  conferencia de protecao [SINTETICO].
  ;; ==========================================================================

  (:action iniciar-visita-urgente
    :parameters (?ag - agente ?p - paciente ?l - local ?n - nivel ?n-1 - nivel)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (not (visitado ?p))
                       (protecao-conferida ?ag ?p)
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
                       (protecao-conferida ?ag ?p)
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
                       (protecao-conferida ?ag ?p)
                       (urgencia-baixa ?p)
                       (altos-pendentes ?zero)
                       (nivel-zero ?zero))
    :effect (and (visitado ?p)
                 (increase (total-cost) 5))
  )

  ;; ==========================================================================
  ;;  PROCEDIMENTOS DO ART. 3o PAR. 4o
  ;;  Condicoes legais cumulativas do caput, acrescidas da higienizacao das
  ;;  maos [SINTETICO].
  ;; ==========================================================================

  ;; Inciso I. Encaminhamento incondicional no texto.
  (:action aferir-pressao-arterial
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (pa-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag)
                       (maos-higienizadas ?ag))
    :effect (and (pa-ok ?p)
                 (pendencia-encaminhamento ?p)
                 (increase (total-cost) 4))
  )

  ;; Inciso II. Consome fita reagente e ocupa espaco no coletor [SINTETICO].
  (:action medir-glicemia-capilar
    :parameters (?ag - agente ?p - paciente ?l - local ?n - nivel ?n-1 - nivel
                 ?c - nivel ?c-1 - nivel)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (glicemia-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag)
                       (maos-higienizadas ?ag)
                       (fitas ?n)
                       (prox ?n-1 ?n)
                       (coletor ?c)
                       (prox ?c-1 ?c))
    :effect (and (glicemia-ok ?p)
                 (pendencia-encaminhamento ?p)
                 (not (fitas ?n))
                 (fitas ?n-1)
                 (not (coletor ?c))
                 (coletor ?c-1)
                 (increase (total-cost) 5))
  )

  ;; Inciso III. Encaminhamento condicional no texto ("quando necessario"),
  ;; por isso nao e imposto como efeito.
  (:action aferir-temperatura-axilar
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (temperatura-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag)
                       (maos-higienizadas ?ag))
    :effect (and (temperatura-ok ?p)
                 (increase (total-cost) 3))
  )

  ;; Inciso IV.
  (:action orientar-administracao-medicacao
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (orientacao-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag)
                       (maos-higienizadas ?ag))
    :effect (and (orientacao-ok ?p)
                 (increase (total-cost) 6))
  )

  ;; Inciso V.
  (:action verificacao-antropometrica
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (antropometria-ok ?p))
                       (curso-tecnico-concluido ?ag)
                       (equipamento-disponivel ?ag)
                       (supervisao-ativa ?ag)
                       (maos-higienizadas ?ag))
    :effect (and (antropometria-ok ?p)
                 (increase (total-cost) 4))
  )

  ;; ==========================================================================
  ;;  ATIVIDADES TIPICAS DO ART. 3o PAR. 3o
  ;;  Nao exigem curso tecnico, equipamento nem supervisao. A assimetria vem
  ;;  da lei e e preservada tambem neste dominio.
  ;; ==========================================================================

  (:action verificar-caderneta-vacinal
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (visitado ?p)
                       (not (vacinal-ok ?p)))
    :effect (and (vacinal-ok ?p)
                 (increase (total-cost) 3))
  )

  (:action registrar-encaminhamento
    :parameters (?ag - agente ?p - paciente ?l - local)
    :precondition (and (em ?ag ?l)
                       (residencia-de ?p ?l)
                       (pendencia-encaminhamento ?p))
    :effect (and (not (pendencia-encaminhamento ?p))
                 (increase (total-cost) 2))
  )

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
