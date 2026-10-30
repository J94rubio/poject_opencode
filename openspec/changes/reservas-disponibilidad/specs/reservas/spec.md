# Spec Delta

## Purpose

La capacidad `reservas` define la creación de solicitudes de reserva de espacios académicos, el catálogo cerrado de estados de una reserva, la regla de ocupación (solo las reservas aprobadas ocupan un espacio), la garantía contra solapamientos aprobados mediante validación en el servicio y una restricción de exclusión en la base de datos, la consulta de disponibilidad por rango y el listado y detalle de solicitudes con control por rol.

## ADDED Requirements

### Requirement: Creación de solicitudes de reserva

El sistema SHALL permitir que un usuario autenticado con permiso `reservas:crear` cree una solicitud de reserva con espacio, fecha/hora de inicio y fecha/hora de fin, SHALL asignar como solicitante al usuario autenticado y SHALL responder 201 con los datos de la solicitud (identificador, espacio, solicitante, inicio, fin y estado). Las solicitudes SHALL nacer en estado `pendiente`. Las fechas se envían en ISO 8601 con zona horaria explícita y se almacenan en UTC.

#### Scenario: Creación válida en estado pendiente

- **WHEN** un usuario autenticado envía una solicitud con un espacio existente y activo, inicio y fin con zona horaria explícita, fin posterior al inicio e inicio posterior al instante actual
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

#### Scenario: Inicio en el pasado

- **WHEN** la fecha/hora de inicio es anterior al instante actual
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna solicitud

#### Scenario: Inicio en el instante actual

- **WHEN** la fecha/hora de inicio es exactamente el instante actual
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna solicitud

#### Scenario: Espacio inexistente

- **WHEN** el espacio indicado no existe
- **THEN** el sistema responde 404 con el código `espacio_no_encontrado`
- **AND** no se crea ninguna solicitud

#### Scenario: Espacio inactivo rechaza la solicitud

- **WHEN** se intenta crear una solicitud para un espacio en estado `inactivo`
- **THEN** el sistema responde 400 con el código `espacio_inactivo`
- **AND** no se crea ninguna solicitud

#### Scenario: Espacio desactivado y luego reactivado admite solicitudes

- **WHEN** un espacio fue desactivado y luego reactivado, y se envía una solicitud válida sobre él sin solapamiento con reservas aprobadas
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente`

#### Scenario: Creación sin autenticación

- **WHEN** una petición sin token intenta crear una solicitud
- **THEN** el sistema responde 401 con el código `token_ausente`
- **AND** no se crea ninguna solicitud

### Requirement: Catálogo de estados de una reserva

El sistema SHALL restringir el estado de una reserva a un catálogo cerrado compuesto por `pendiente`, `aprobada`, `rechazada` y `cancelada`. En este change solo se crean solicitudes en estado `pendiente`; las transiciones entre estados se especifican en los changes `aprobacion-reservas` y `cancelacion-historial`.

#### Scenario: Toda solicitud creada por la API queda pendiente

- **WHEN** cualquier usuario autenticado crea una solicitud válida
- **THEN** la solicitud queda en estado `pendiente`
- **AND** la petición no puede fijar otro estado

#### Scenario: Estado fuera del catálogo rechazado al persistir

- **WHEN** se intenta persistir una reserva con un estado distinto de `pendiente`, `aprobada`, `rechazada` o `cancelada`
- **THEN** la persistencia la rechaza
- **AND** no se almacena ninguna reserva

### Requirement: Ocupación por reservas aprobadas

Solo las reservas en estado `aprobada` ocupan un espacio. El sistema SHALL rechazar de inmediato la creación de una solicitud cuyo rango, semiabierto `[inicio, fin)`, se solape con el de alguna reserva en estado `aprobada` del mismo espacio.

#### Scenario: Solapamiento parcial con una reserva aprobada

- **WHEN** existe una reserva aprobada del espacio en [10:00, 12:00) y se crea una solicitud para el mismo espacio en [11:00, 13:00)
- **THEN** el sistema responde 409 con el código `reserva_solapada`
- **AND** no se crea la solicitud

#### Scenario: Solicitud contenida en una reserva aprobada

- **WHEN** existe una reserva aprobada del espacio en [10:00, 14:00) y se crea una solicitud para el mismo espacio en [11:00, 12:00)
- **THEN** el sistema responde 409 con el código `reserva_solapada`
- **AND** no se crea la solicitud

#### Scenario: Solicitud que contiene a una reserva aprobada

- **WHEN** existe una reserva aprobada del espacio en [11:00, 12:00) y se crea una solicitud para el mismo espacio en [10:00, 14:00)
- **THEN** el sistema responde 409 con el código `reserva_solapada`
- **AND** no se crea la solicitud

#### Scenario: Reserva que termina exactamente cuando otra empieza es permitida

- **WHEN** existe una reserva aprobada del espacio en [10:00, 12:00) y se crea una solicitud para el mismo espacio en [12:00, 13:00)
- **THEN** no hay solapamiento porque los rangos son semiabiertos
- **AND** el sistema responde 201 y crea la solicitud en estado `pendiente`

#### Scenario: La misma franja en otro espacio no genera conflicto

- **WHEN** existe una reserva aprobada de un espacio en [10:00, 12:00) y se crea una solicitud para otro espacio en el mismo rango
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente`

#### Scenario: Una reserva rechazada o cancelada no ocupa el espacio

- **WHEN** existe una reserva en estado `rechazada` o `cancelada` del espacio en [10:00, 12:00) y se crea una solicitud para el mismo espacio en ese rango
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente`

#### Scenario: Varias solicitudes pendientes pueden solaparse entre sí

- **WHEN** existe una solicitud pendiente del espacio en [10:00, 12:00) y se crea otra solicitud para el mismo espacio en [11:00, 13:00)
- **THEN** el sistema responde 201 y crea la solicitud en estado `pendiente`

### Requirement: Garantía de integridad contra solapamientos aprobados

La garantía contra solapamientos aprobados SHALL existir tanto por validación en el servicio como por una restricción de exclusión en la base de datos sobre el rango `[inicio, fin)` por espacio, aplicable solo a las filas en estado `aprobada`. La base de datos SHALL rechazar además cualquier reserva cuyo fin sea igual o anterior a su inicio. Estos escenarios se verifican a nivel de repositorio, insertando directamente las reservas.

#### Scenario: Dos reservas aprobadas solapadas en el mismo espacio

- **WHEN** se insertan directamente dos reservas en estado `aprobada` del mismo espacio con rangos que se solapan
- **THEN** la restricción de exclusión rechaza la segunda inserción
- **AND** solo la primera reserva queda almacenada

#### Scenario: Dos reservas aprobadas que solo comparten el extremo

- **WHEN** se insertan directamente dos reservas en estado `aprobada` del mismo espacio, una en [10:00, 12:00) y otra en [12:00, 14:00)
- **THEN** ambas inserciones se aceptan

#### Scenario: Reservas aprobadas con el mismo rango en espacios distintos

- **WHEN** se insertan directamente dos reservas en estado `aprobada` de espacios distintos con el mismo rango
- **THEN** ambas inserciones se aceptan

#### Scenario: Dos reservas pendientes solapadas

- **WHEN** se insertan directamente dos reservas en estado `pendiente` del mismo espacio con rangos que se solapan
- **THEN** ambas inserciones se aceptan

#### Scenario: Una reserva aprobada y una pendiente solapadas

- **WHEN** se insertan directamente una reserva en estado `aprobada` y otra en estado `pendiente` del mismo espacio con rangos que se solapan
- **THEN** ambas inserciones se aceptan

#### Scenario: Rango con fin igual o anterior al inicio

- **WHEN** se intenta insertar directamente una reserva cuyo fin es igual o anterior a su inicio
- **THEN** la base de datos rechaza la inserción

### Requirement: Consulta de disponibilidad de un espacio por rango

El sistema SHALL permitir que cualquier usuario autenticado con permiso `espacios:ver` consulte la disponibilidad de un espacio por rango, y SHALL devolver los intervalos ocupados por reservas en estado `aprobada` como una lista de intervalos con `inicio` y `fin` en UTC, en orden ascendente, sin datos del solicitante. Los intervalos que solapan parcialmente el rango consultado se devuelven completos, sin recortar, y una reserva que solo toca el borde del rango, sin solaparse, no se incluye.

#### Scenario: Disponibilidad devuelve los intervalos de reservas aprobadas

- **WHEN** se consulta la disponibilidad de un espacio para el rango [08:00, 18:00) y existen reservas aprobadas en [10:00, 12:00) y [14:00, 15:00)
- **THEN** el sistema responde 200 con esos dos intervalos en orden ascendente
- **AND** cada intervalo contiene solo `inicio` y `fin` en UTC

#### Scenario: Disponibilidad ignora reservas que no están aprobadas

- **WHEN** en el rango consultado hay reservas en estado `pendiente`, `rechazada` o `cancelada`
- **THEN** los intervalos devueltos no las incluyen

#### Scenario: Intervalo que solapa parcialmente el rango se devuelve completo

- **WHEN** existe una reserva aprobada en [07:00, 09:00) y se consulta el rango [08:00, 18:00)
- **THEN** el sistema devuelve el intervalo [07:00, 09:00) completo, sin recortarlo

#### Scenario: Reserva que solo toca el borde del rango

- **WHEN** existe una reserva aprobada en [06:00, 08:00) y se consulta el rango [08:00, 18:00)
- **THEN** esa reserva no se incluye en la respuesta

#### Scenario: Espacio sin reservas aprobadas en el rango

- **WHEN** no existen reservas aprobadas del espacio en el rango consultado
- **THEN** el sistema responde 200 con una lista vacía

#### Scenario: Rango inválido

- **WHEN** falta el inicio o el fin del rango, alguno se envía sin zona horaria explícita, o el fin es igual o anterior al inicio
- **THEN** el sistema responde 400 con el código `datos_invalidos`

#### Scenario: Espacio inexistente en la consulta

- **WHEN** el espacio consultado no existe
- **THEN** el sistema responde 404 con el código `espacio_no_encontrado`

#### Scenario: Espacio inactivo en la consulta

- **WHEN** el espacio consultado está en estado `inactivo`
- **THEN** la consulta procede y devuelve los intervalos de sus reservas aprobadas

#### Scenario: Consulta sin autenticación

- **WHEN** una petición sin token consulta la disponibilidad
- **THEN** el sistema responde 401 con el código `token_ausente`

### Requirement: Listado y detalle de solicitudes

El sistema SHALL permitir consultar solicitudes según la matriz de permisos definida en el change `usuarios-roles-auth`: con el permiso `reservas:ver_propias` el solicitante ve solo las suyas, y con el permiso `reservas:ver_todas` el aprobador y el admin ven todas. El listado SHALL devolverse completo, sin paginación, ordenado por inicio ascendente y luego por identificador. El formato de errores es el definido en `usuarios-roles-auth`.

#### Scenario: Solicitante ve solo sus propias solicitudes

- **WHEN** un usuario con rol `solicitante` consulta el listado de solicitudes
- **THEN** el sistema devuelve únicamente las solicitudes cuyo solicitante es ese usuario

#### Scenario: Aprobador ve todas las solicitudes

- **WHEN** un usuario con rol `aprobador` consulta el listado de solicitudes
- **THEN** el sistema devuelve todas las solicitudes de todos los solicitantes

#### Scenario: Admin ve todas las solicitudes

- **WHEN** un usuario con rol `admin` consulta el listado de solicitudes
- **THEN** el sistema devuelve todas las solicitudes de todos los solicitantes

#### Scenario: Orden del listado

- **WHEN** existen solicitudes con distintos inicios y un usuario con permiso consulta el listado
- **THEN** las solicitudes se devuelven ordenadas por inicio ascendente y, a igual inicio, por identificador

#### Scenario: Listado sin solicitudes

- **WHEN** un usuario autorizado consulta el listado y no existe ninguna solicitud visible para él
- **THEN** el sistema responde 200 con una lista vacía

#### Scenario: Detalle de una solicitud propia

- **WHEN** un solicitante consulta el detalle de una solicitud propia
- **THEN** el sistema responde 200 con los datos de la solicitud

#### Scenario: Detalle de una solicitud ajena por un solicitante

- **WHEN** un solicitante consulta el detalle de una solicitud de otro usuario
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la respuesta no contiene los datos de la solicitud

#### Scenario: Detalle de una solicitud ajena por aprobador o admin

- **WHEN** un usuario con rol `aprobador` o `admin` consulta el detalle de una solicitud de otro usuario
- **THEN** el sistema responde 200 con los datos de la solicitud

#### Scenario: Detalle de una solicitud inexistente

- **WHEN** un usuario autorizado consulta el detalle de un identificador que no corresponde a ninguna solicitud
- **THEN** el sistema responde 404 con el código `solicitud_no_encontrada`

#### Scenario: Consulta sin autenticación

- **WHEN** una petición sin token consulta el listado o el detalle de solicitudes
- **THEN** el sistema responde 401 con el código `token_ausente`
