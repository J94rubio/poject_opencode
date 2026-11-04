# Spec Delta

## Purpose

La capacidad `cancelaciones` define cómo un solicitante cancela sus propias reservas pendientes o aprobadas que aún no han comenzado, y qué ocurre con el espacio al cancelar. No cubre la cancelación de reservas ajenas ni el registro del cambio, que pertenece a `historial`.

## ADDED Requirements

### Requirement: Cancelación de reservas propias

El sistema SHALL permitir al usuario que creó una solicitud, con el permiso `reservas:cancelar_propia`, cancelarla mientras esté en estado `pendiente` o `aprobada` y su inicio sea posterior al momento actual, y SHALL cambiar su estado a `cancelada`.

#### Scenario: Cancelación de una solicitud pendiente

- **WHEN** un solicitante cancela su propia solicitud `pendiente` que aún no ha comenzado
- **THEN** el sistema responde 200 con la solicitud en estado `cancelada`

#### Scenario: Cancelación de una reserva aprobada

- **WHEN** un solicitante cancela su propia reserva `aprobada` que aún no ha comenzado
- **THEN** el sistema responde 200 con la reserva en estado `cancelada`

#### Scenario: Cancelación por un aprobador de su propia solicitud

- **WHEN** un usuario con rol `aprobador` o `admin` cancela una solicitud creada por él mismo que está `pendiente` o `aprobada` y aún no ha comenzado
- **THEN** el sistema responde 200 con la solicitud en estado `cancelada`

### Requirement: Liberación del espacio al cancelar

El sistema SHALL dejar de considerar ocupado el espacio por una reserva `aprobada` en cuanto se cancela, y una reserva cancelada SHALL NOT volver a ocuparlo.

#### Scenario: La disponibilidad refleja la cancelación

- **WHEN** se cancela una reserva `aprobada` y luego se consulta la disponibilidad del espacio en un rango que la contenía
- **THEN** la respuesta no incluye el intervalo de la reserva cancelada

#### Scenario: Aprobación de una solicitud antes en conflicto

- **WHEN** se cancela una reserva `aprobada` y luego se aprueba una solicitud `pendiente` que se solapaba con ella en el mismo espacio
- **THEN** el sistema responde 200 con la solicitud en estado `aprobada`

#### Scenario: Una reserva cancelada no se puede aprobar

- **WHEN** se intenta aprobar una reserva en estado `cancelada`
- **THEN** el sistema responde 409 con el código `transicion_invalida`

### Requirement: Condiciones de la cancelación

El sistema SHALL rechazar la cancelación de una solicitud cuyo estado no sea `pendiente` o `aprobada` con el código `transicion_invalida`, y la de una solicitud cuyo inicio ya ocurrió con el código `reserva_iniciada`, sin modificarla.

#### Scenario: Cancelación de una solicitud rechazada o ya cancelada

- **WHEN** un solicitante intenta cancelar su propia solicitud en estado `rechazada` o `cancelada`
- **THEN** el sistema responde 409 con el código `transicion_invalida`
- **AND** el estado de la solicitud no cambia

#### Scenario: Cancelación de una reserva que ya comenzó

- **WHEN** un solicitante intenta cancelar su propia solicitud `pendiente` o `aprobada` cuyo inicio es anterior al momento actual
- **THEN** el sistema responde 409 con el código `reserva_iniciada`
- **AND** el estado de la solicitud no cambia

#### Scenario: Cancelación en el instante de inicio

- **WHEN** un solicitante intenta cancelar su propia solicitud cuyo inicio es exactamente el momento actual
- **THEN** el sistema responde 409 con el código `reserva_iniciada`

### Requirement: Cancelación restringida al dueño

El sistema SHALL permitir cancelar únicamente al usuario que creó la solicitud, SHALL exigir autenticación y SHALL responder 404 cuando la solicitud no exista.

#### Scenario: Cancelación de una solicitud ajena por un solicitante

- **WHEN** un solicitante intenta cancelar una solicitud creada por otro usuario
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** el estado de la solicitud no cambia

#### Scenario: Cancelación de una solicitud ajena por un aprobador o administrador

- **WHEN** un usuario con rol `aprobador` o `admin` intenta cancelar una solicitud creada por otro usuario
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** el estado de la solicitud no cambia

#### Scenario: Cancelación sin sesión

- **WHEN** se intenta cancelar una solicitud sin enviar token
- **THEN** el sistema responde 401 con el código `token_ausente`

#### Scenario: Cancelación de una solicitud inexistente

- **WHEN** un usuario autenticado intenta cancelar un identificador que no existe
- **THEN** el sistema responde 404 con el código `solicitud_no_encontrada`

### Requirement: Cancelaciones simultáneas

El sistema SHALL garantizar que una cancelación concurrente con otra cancelación o con una decisión sobre la misma solicitud deje la solicitud en un estado coherente.

#### Scenario: Dos cancelaciones simultáneas de la misma solicitud

- **WHEN** el dueño cancela dos veces al mismo tiempo la misma solicitud
- **THEN** exactamente una cancelación responde 200 y la otra responde 409 con el código `transicion_invalida`

#### Scenario: Cancelación y aprobación simultáneas de la misma solicitud

- **WHEN** el dueño cancela una solicitud `pendiente` mientras un aprobador la aprueba al mismo tiempo
- **THEN** la cancelación responde 200 y el estado final de la solicitud es `cancelada`
- **AND** la aprobación responde 200 o responde 409 con el código `transicion_invalida`
