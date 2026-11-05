## MODIFIED Requirements

### Requirement: Creación de solicitudes de reserva

El sistema SHALL permitir que un usuario autenticado con permiso `reservas:crear` cree una solicitud de reserva con espacio, fecha/hora de inicio y fecha/hora de fin, SHALL asignar como solicitante al usuario autenticado y SHALL responder 201 con los datos de la solicitud (identificador, espacio, solicitante, inicio, fin y estado). Las solicitudes SHALL nacer en estado `pendiente`. Las fechas se envían en ISO 8601 con zona horaria explícita y se almacenan en UTC. La duración de una solicitud, calculada como fin menos inicio sobre sus instantes en UTC, SHALL ser como máximo de 4 horas exactas, inclusive: el sistema SHALL rechazar una duración mayor con 400 y el código `duracion_excedida`, sin crear la solicitud ni ninguna entrada de historial. Esta comprobación SHALL hacerse justo después de validar que el fin es posterior al inicio y antes de comprobar que el inicio no ha pasado, que el espacio existe, que está activo y que no hay solapamiento.

#### Scenario: Creación válida en estado pendiente

- **WHEN** un usuario autenticado envía una solicitud con un espacio existente y activo, inicio y fin con zona horaria explícita, fin posterior al inicio, una duración no mayor de 4 horas e inicio posterior al instante actual
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente` asociada al usuario autenticado como solicitante
- **AND** la respuesta incluye identificador, espacio, solicitante, inicio, fin y estado

#### Scenario: Creación por aprobador o administrador

- **WHEN** un usuario con rol `aprobador` o `admin` envía una solicitud válida
- **THEN** el sistema responde 201 y la solicitud nace en estado `pendiente` asociada a ese usuario como solicitante

#### Scenario: Solicitante enviado en el cuerpo de la petición

- **WHEN** la petición incluye un campo de solicitante, aunque coincida con el usuario autenticado
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna solicitud

#### Scenario: Campos obligatorios faltantes

- **WHEN** falta el espacio, el inicio o el fin en la petición
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna solicitud

#### Scenario: Fecha sin zona horaria es inválida

- **WHEN** el inicio o el fin se envía sin zona horaria explícita
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna solicitud

#### Scenario: Fin anterior o igual al inicio

- **WHEN** la fecha/hora de fin es anterior o igual a la de inicio
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna solicitud

#### Scenario: Duración de 1 hora aceptada

- **WHEN** un usuario autenticado envía una solicitud por lo demás válida en [10:00, 11:00)
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente`

#### Scenario: Duración de 4 horas exactas aceptada

- **WHEN** un usuario autenticado envía una solicitud por lo demás válida en [10:00:00, 14:00:00)
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente`

#### Scenario: Duración de 4 horas y 1 segundo rechazada

- **WHEN** un usuario autenticado envía una solicitud por lo demás válida en [10:00:00, 14:00:01)
- **THEN** el sistema responde 400 con el código `duracion_excedida` y el mensaje fijo «La duración máxima de una reserva es de 4 horas.»
- **AND** no se crea ninguna solicitud

#### Scenario: Duración de 4 horas exactas con zonas horarias distintas

- **WHEN** una solicitud por lo demás válida tiene inicio `2026-11-03T10:00:00-05:00` y fin `2026-11-03T19:00:00+00:00`, que distan 4 horas exactas en UTC
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente`

#### Scenario: Duración excedida con zonas horarias distintas

- **WHEN** una solicitud por lo demás válida tiene inicio `2026-11-03T10:00:00+00:00` y fin `2026-11-03T10:00:01-05:00`, que distan 5 horas y 1 segundo en UTC
- **THEN** el sistema responde 400 con el código `duracion_excedida`
- **AND** no se crea ninguna solicitud

#### Scenario: Duración excedida con un cuerpo no válido

- **WHEN** una petición con una duración mayor de 4 horas incluye un campo no admitido o un espacio que no es un identificador entero
- **THEN** el sistema responde 400 con el código `datos_invalidos`, porque la forma de la petición se valida antes que la duración
- **AND** no se crea ninguna solicitud

#### Scenario: Duración excedida con inicio pasado

- **WHEN** una solicitud tiene una duración mayor de 4 horas y su inicio es anterior o igual al instante actual
- **THEN** el sistema responde 400 con el código `duracion_excedida`
- **AND** no se crea ninguna solicitud

#### Scenario: Duración excedida con espacio inexistente

- **WHEN** una solicitud tiene una duración mayor de 4 horas y el espacio indicado no existe
- **THEN** el sistema responde 400 con el código `duracion_excedida`
- **AND** no se crea ninguna solicitud

#### Scenario: Duración excedida con espacio inactivo

- **WHEN** una solicitud tiene una duración mayor de 4 horas y el espacio indicado está en estado `inactivo`
- **THEN** el sistema responde 400 con el código `duracion_excedida`
- **AND** no se crea ninguna solicitud

#### Scenario: Duración excedida con solapamiento

- **WHEN** una solicitud tiene una duración mayor de 4 horas y su rango se solapa con una reserva aprobada del mismo espacio
- **THEN** el sistema responde 400 con el código `duracion_excedida`
- **AND** no se crea ninguna solicitud

#### Scenario: La solicitud rechazada por duración no deja rastro

- **WHEN** una solicitud se rechaza con el código `duracion_excedida`
- **THEN** no existe ninguna reserva nueva
- **AND** el historial no contiene ninguna entrada nueva

#### Scenario: Inicio en el pasado

- **WHEN** la fecha/hora de inicio es anterior al instante actual y la duración no es mayor de 4 horas
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna solicitud

#### Scenario: Inicio en el instante actual

- **WHEN** la fecha/hora de inicio es exactamente el instante actual y la duración no es mayor de 4 horas
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna solicitud

#### Scenario: Espacio inexistente

- **WHEN** el espacio indicado no existe y la duración no es mayor de 4 horas
- **THEN** el sistema responde 404 con el código `espacio_no_encontrado`
- **AND** no se crea ninguna solicitud

#### Scenario: Espacio inactivo rechaza la solicitud

- **WHEN** se intenta crear una solicitud con una duración no mayor de 4 horas para un espacio en estado `inactivo`
- **THEN** el sistema responde 400 con el código `espacio_inactivo`
- **AND** no se crea ninguna solicitud

#### Scenario: Espacio desactivado y luego reactivado admite solicitudes

- **WHEN** un espacio fue desactivado y luego reactivado, y se envía una solicitud válida sobre él sin solapamiento con reservas aprobadas
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente`

#### Scenario: Creación sin autenticación

- **WHEN** una petición sin token intenta crear una solicitud
- **THEN** el sistema responde 401 con el código `token_ausente`
- **AND** no se crea ninguna solicitud

## ADDED Requirements

### Requirement: Alcance de la duración máxima

El sistema SHALL aplicar la duración máxima de 4 horas únicamente al crear una solicitud. El sistema SHALL NOT aplicarla al aprobar, rechazar o cancelar una reserva, ni a la consulta de disponibilidad ni al rango de fechas del historial, y SHALL conservar sin cambios las reservas que ya existan con una duración mayor.

#### Scenario: Aprobación de una solicitud existente de más de 4 horas

- **WHEN** un usuario con rol `aprobador` aprueba una solicitud `pendiente` de otro usuario con una duración mayor de 4 horas, creada antes de la regla, que cumple las condiciones de aprobación
- **THEN** el sistema responde 200 con la solicitud en estado `aprobada`

#### Scenario: Rechazo de una solicitud existente de más de 4 horas

- **WHEN** un usuario con rol `aprobador` rechaza con motivo una solicitud `pendiente` de otro usuario con una duración mayor de 4 horas, creada antes de la regla
- **THEN** el sistema responde 200 con la solicitud en estado `rechazada`

#### Scenario: Cancelación de una reserva existente de más de 4 horas

- **WHEN** un solicitante cancela su propia reserva `pendiente` o `aprobada` con una duración mayor de 4 horas, creada antes de la regla, que aún no ha comenzado
- **THEN** el sistema responde 200 con la reserva en estado `cancelada`

#### Scenario: Consulta de una reserva existente de más de 4 horas

- **WHEN** un usuario autorizado consulta el listado o el detalle de una reserva existente con una duración mayor de 4 horas
- **THEN** el sistema responde 200 con la reserva y con su inicio y su fin sin cambios

#### Scenario: Consulta de disponibilidad con un rango mayor de 4 horas

- **WHEN** se consulta la disponibilidad de un espacio para un rango válido de más de 4 horas
- **THEN** el sistema responde 200 con los intervalos ocupados del rango

#### Scenario: Consulta del historial con un rango mayor de 4 horas

- **WHEN** se consulta el historial con `desde` y `hasta` válidos que distan más de 4 horas
- **THEN** el sistema responde 200 con las entradas del rango
