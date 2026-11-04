# Spec Delta

## Purpose

La capacidad `aprobaciones` define cómo un aprobador o un administrador decide sobre las solicitudes de reserva pendientes: aprobarlas o rechazarlas con un motivo. Define también las transiciones de estado permitidas, la regla de que nadie decide sus propias solicitudes y el comportamiento ante decisiones simultáneas. No cubre la cancelación ni el historial de cambios de estado.

## ADDED Requirements

### Requirement: Aprobación de solicitudes pendientes

El sistema SHALL permitir a un usuario con el permiso `aprobaciones:aprobar` aprobar una solicitud en estado `pendiente`, SHALL cambiar su estado a `aprobada` y SHALL rechazar la aprobación cuando el rango se solape con una reserva aprobada del mismo espacio, cuando el espacio esté inactivo o cuando la solicitud ya haya comenzado, es decir, cuando su inicio sea anterior o igual al momento actual.

#### Scenario: Aprobación por un aprobador

- **WHEN** un usuario con rol `aprobador` aprueba una solicitud `pendiente` de otro usuario
- **THEN** el sistema responde 200 con la solicitud en estado `aprobada`

#### Scenario: Aprobación por un administrador

- **WHEN** un usuario con rol `admin` aprueba una solicitud `pendiente` de otro usuario
- **THEN** el sistema responde 200 con la solicitud en estado `aprobada`

#### Scenario: La reserva aprobada ocupa el espacio

- **WHEN** una solicitud se aprueba y luego se consulta la disponibilidad del espacio en un rango que la contiene
- **THEN** la respuesta incluye el intervalo de la reserva aprobada

#### Scenario: Aprobación con solapamiento

- **WHEN** se aprueba una solicitud cuyo rango se solapa con una reserva `aprobada` del mismo espacio
- **THEN** el sistema responde 409 con el código `reserva_solapada`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Aprobación con borde exacto

- **WHEN** se aprueba una solicitud que empieza exactamente cuando termina una reserva `aprobada` del mismo espacio
- **THEN** el sistema responde 200 con la solicitud en estado `aprobada`

#### Scenario: Aprobación en otro espacio

- **WHEN** se aprueba una solicitud con el mismo rango que una reserva `aprobada` de otro espacio
- **THEN** el sistema responde 200 con la solicitud en estado `aprobada`

#### Scenario: Las pendientes solapadas no cambian al aprobar

- **WHEN** se aprueba una solicitud que se solapa con otra solicitud `pendiente` del mismo espacio
- **THEN** la otra solicitud sigue en estado `pendiente`

#### Scenario: Aprobación de una pendiente que quedó en conflicto

- **WHEN** se intenta aprobar una solicitud `pendiente` que se solapa con una reserva aprobada después de su creación
- **THEN** el sistema responde 409 con el código `reserva_solapada`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Aprobación sobre un espacio desactivado

- **WHEN** se aprueba una solicitud `pendiente` cuyo espacio fue desactivado después de crearla
- **THEN** el sistema responde 400 con el código `espacio_inactivo`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Aprobación de una solicitud vencida

- **WHEN** se aprueba una solicitud `pendiente` cuyo inicio es anterior al momento actual
- **THEN** el sistema responde 409 con el código `solicitud_vencida`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Aprobación en el instante de inicio

- **WHEN** se aprueba una solicitud `pendiente` cuyo inicio es exactamente el momento actual
- **THEN** el sistema responde 409 con el código `solicitud_vencida`
- **AND** la solicitud sigue en estado `pendiente`

### Requirement: Rechazo de solicitudes pendientes con motivo

El sistema SHALL permitir a un usuario con el permiso `aprobaciones:rechazar` rechazar una solicitud en estado `pendiente`, SHALL exigir un motivo de texto no vacío de hasta 500 caracteres, SHALL cambiar su estado a `rechazada` y SHALL conservar el motivo en la solicitud.

#### Scenario: Rechazo con motivo

- **WHEN** un usuario con rol `aprobador` rechaza una solicitud `pendiente` de otro usuario indicando un motivo
- **THEN** el sistema responde 200 con la solicitud en estado `rechazada` y con el motivo indicado

#### Scenario: Rechazo sin motivo

- **WHEN** se rechaza una solicitud `pendiente` sin enviar el campo `motivo`
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Rechazo con motivo vacío

- **WHEN** se rechaza una solicitud `pendiente` con un motivo vacío o formado solo por espacios
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Rechazo con motivo demasiado largo

- **WHEN** se rechaza una solicitud `pendiente` con un motivo de más de 500 caracteres
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Rechazo de una pendiente solapada con una aprobada

- **WHEN** se rechaza con motivo una solicitud `pendiente` que se solapa con una reserva `aprobada`
- **THEN** el sistema responde 200 con la solicitud en estado `rechazada`

#### Scenario: Rechazo sobre un espacio desactivado o con la solicitud ya comenzada

- **WHEN** se rechaza con motivo una solicitud `pendiente` cuyo espacio está inactivo o cuyo inicio es anterior o igual al momento actual
- **THEN** el sistema responde 200 con la solicitud en estado `rechazada`

#### Scenario: El motivo aparece en el detalle

- **WHEN** el solicitante consulta el detalle de su propia solicitud rechazada
- **THEN** la respuesta incluye el motivo del rechazo

#### Scenario: La reserva rechazada no ocupa el espacio

- **WHEN** una solicitud se rechaza y luego se consulta la disponibilidad del espacio en un rango que la contiene
- **THEN** la respuesta no incluye el intervalo de la solicitud rechazada

### Requirement: Transiciones permitidas desde el estado pendiente

El sistema SHALL permitir aprobar o rechazar únicamente solicitudes en estado `pendiente` y SHALL responder con el código `transicion_invalida` cuando la solicitud esté en cualquier otro estado, sin modificarla.

#### Scenario: Aprobar una solicitud que no está pendiente

- **WHEN** se intenta aprobar una solicitud en estado `aprobada`, `rechazada` o `cancelada`
- **THEN** el sistema responde 409 con el código `transicion_invalida`
- **AND** el estado de la solicitud no cambia

#### Scenario: Rechazar una solicitud que no está pendiente

- **WHEN** se intenta rechazar con motivo una solicitud en estado `aprobada`, `rechazada` o `cancelada`
- **THEN** el sistema responde 409 con el código `transicion_invalida`
- **AND** el estado y el motivo de la solicitud no cambian

### Requirement: Prohibición de decidir las propias solicitudes

El sistema SHALL impedir que un usuario apruebe o rechace una solicitud que él mismo creó, cualquiera que sea su rol.

#### Scenario: Aprobador aprueba su propia solicitud

- **WHEN** un usuario con rol `aprobador` intenta aprobar una solicitud `pendiente` creada por él mismo
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Administrador rechaza su propia solicitud

- **WHEN** un usuario con rol `admin` intenta rechazar con motivo una solicitud `pendiente` creada por él mismo
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la solicitud sigue en estado `pendiente`

### Requirement: Control de acceso a las decisiones

El sistema SHALL exigir autenticación y el permiso correspondiente para aprobar o rechazar, y SHALL responder 404 cuando la solicitud no exista.

#### Scenario: Decisión de un solicitante

- **WHEN** un usuario con rol `solicitante` intenta aprobar o rechazar una solicitud `pendiente`
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la solicitud sigue en estado `pendiente`

#### Scenario: Decisión sin sesión

- **WHEN** se intenta aprobar o rechazar una solicitud sin enviar token
- **THEN** el sistema responde 401 con el código `token_ausente`

#### Scenario: Decisión sobre una solicitud inexistente

- **WHEN** un usuario con rol `aprobador` intenta aprobar o rechazar un identificador que no existe
- **THEN** el sistema responde 404 con el código `solicitud_no_encontrada`

### Requirement: Decisiones simultáneas

El sistema SHALL garantizar que decisiones concurrentes sobre solicitudes del mismo espacio no produzcan dos reservas aprobadas solapadas ni dos decisiones sobre la misma solicitud.

#### Scenario: Dos aprobaciones simultáneas de solicitudes solapadas

- **WHEN** dos solicitudes `pendiente` del mismo espacio con rangos solapados se aprueban al mismo tiempo
- **THEN** exactamente una responde 200 y la otra responde 409 con el código `reserva_solapada`
- **AND** solo una de las dos queda en estado `aprobada`

#### Scenario: Dos aprobaciones simultáneas de la misma solicitud

- **WHEN** la misma solicitud `pendiente` se aprueba dos veces al mismo tiempo
- **THEN** exactamente una responde 200 y la otra responde 409 con el código `transicion_invalida`

#### Scenario: Aprobación y rechazo simultáneos de la misma solicitud

- **WHEN** la misma solicitud `pendiente` se aprueba y se rechaza al mismo tiempo
- **THEN** exactamente una decisión responde 200 y la otra responde 409 con el código `transicion_invalida`
- **AND** el estado final de la solicitud corresponde a la decisión que tuvo éxito
