# Spec Delta

## Purpose

La capacidad `historial` define el registro inmutable de cada cambio de estado de una reserva (creación, aprobación, rechazo y cancelación) con su actor y su fecha, y la consulta de ese registro según el rol, con filtros por espacio, estado y rango de fechas.

## ADDED Requirements

### Requirement: Registro de cada cambio de estado

El sistema SHALL registrar una entrada de historial por cada creación, aprobación, rechazo y cancelación de una reserva, con la reserva, el espacio, el estado anterior, el estado nuevo, el usuario que realizó la acción y la fecha del cambio en UTC, y SHALL escribirla de forma atómica con el cambio de estado.

#### Scenario: Registro de la creación

- **WHEN** un solicitante crea una solicitud
- **THEN** el historial contiene una entrada con estado anterior vacío, estado nuevo `pendiente`, el solicitante como actor y la fecha de la creación

#### Scenario: Registro de la aprobación

- **WHEN** un aprobador aprueba una solicitud `pendiente`
- **THEN** el historial contiene una entrada con estado anterior `pendiente`, estado nuevo `aprobada`, el aprobador como actor y la fecha de la decisión

#### Scenario: Registro del rechazo

- **WHEN** un aprobador rechaza una solicitud `pendiente`
- **THEN** el historial contiene una entrada con estado anterior `pendiente`, estado nuevo `rechazada`, el aprobador como actor y la fecha de la decisión

#### Scenario: Registro de la cancelación

- **WHEN** un solicitante cancela su solicitud `aprobada`
- **THEN** el historial contiene una entrada con estado anterior `aprobada`, estado nuevo `cancelada`, el solicitante como actor y la fecha de la cancelación

#### Scenario: Las operaciones fallidas no se registran

- **WHEN** una aprobación, un rechazo o una cancelación responde con un error
- **THEN** el historial no contiene ninguna entrada nueva

#### Scenario: Atomicidad del registro

- **WHEN** no se puede escribir la entrada del historial durante un cambio de estado
- **THEN** el estado de la solicitud no cambia
- **AND** el historial no contiene ninguna entrada nueva

### Requirement: Inmutabilidad del historial

El sistema SHALL impedir editar o borrar entradas del historial, tanto desde la API como directamente en la base de datos.

#### Scenario: Modificación directa de una entrada

- **WHEN** se intenta actualizar una entrada del historial directamente en la base de datos
- **THEN** la base de datos rechaza la operación
- **AND** la entrada conserva sus valores

#### Scenario: Borrado directo de una entrada

- **WHEN** se intenta borrar una entrada del historial directamente en la base de datos
- **THEN** la base de datos rechaza la operación
- **AND** la entrada sigue existiendo

#### Scenario: Escritura por la API

- **WHEN** se envía una petición `POST`, `PUT`, `PATCH` o `DELETE` a la ruta del historial
- **THEN** el sistema responde 405 con el código `metodo_no_permitido`

### Requirement: Consulta del historial según el rol

El sistema SHALL permitir a un usuario con el permiso `historial:ver_todos` consultar todas las entradas y a un usuario con el permiso `historial:ver_propio` consultar solo las entradas de las reservas que él creó, ordenadas por fecha del cambio ascendente y luego por identificador.

#### Scenario: Historial de un solicitante

- **WHEN** un usuario con rol `solicitante` consulta el historial
- **THEN** la respuesta contiene únicamente las entradas de las reservas que él creó, incluidas las decisiones tomadas por otros usuarios sobre ellas

#### Scenario: Historial de un aprobador o administrador

- **WHEN** un usuario con rol `aprobador` o `admin` consulta el historial
- **THEN** la respuesta contiene las entradas de todas las reservas

#### Scenario: Contenido de cada entrada

- **WHEN** se consulta el historial
- **THEN** cada entrada incluye la reserva, el espacio, el estado anterior, el estado nuevo, el actor y la fecha del cambio en UTC

#### Scenario: Orden de las entradas

- **WHEN** se consulta un historial con entradas de fechas distintas
- **THEN** las entradas se devuelven por fecha del cambio ascendente y, ante fechas iguales, por identificador ascendente

#### Scenario: Historial vacío

- **WHEN** un usuario sin entradas visibles consulta el historial
- **THEN** el sistema responde 200 con una lista vacía

#### Scenario: Consulta sin sesión

- **WHEN** se consulta el historial sin enviar token
- **THEN** el sistema responde 401 con el código `token_ausente`

### Requirement: Filtros del historial

El sistema SHALL permitir filtrar el historial por espacio (`espacio_id`), por estado nuevo (`estado`) y por rango de fechas del cambio (`desde` y `hasta`, con rango semiabierto `[desde, hasta)` y zona horaria explícita), SHALL combinar los filtros presentes con Y lógico y SHALL respetar siempre la visibilidad del rol.

#### Scenario: Filtro por espacio

- **WHEN** se consulta el historial con un `espacio_id`
- **THEN** la respuesta contiene únicamente entradas de reservas de ese espacio

#### Scenario: Filtro por estado

- **WHEN** se consulta el historial con un `estado`
- **THEN** la respuesta contiene únicamente entradas cuyo estado nuevo es ese estado

#### Scenario: Filtro por rango de fechas

- **WHEN** se consulta el historial con `desde` y `hasta`
- **THEN** la respuesta contiene únicamente entradas cuya fecha de cambio es mayor o igual que `desde` y menor que `hasta`

#### Scenario: Filtros combinados

- **WHEN** se consulta el historial con un espacio, un estado y un rango de fechas
- **THEN** la respuesta contiene únicamente entradas que cumplen los tres filtros

#### Scenario: Filtros y visibilidad del solicitante

- **WHEN** un solicitante consulta el historial filtrando por un espacio donde existen reservas de otros usuarios
- **THEN** la respuesta no contiene entradas de las reservas de otros usuarios

#### Scenario: Estado fuera del catálogo

- **WHEN** se consulta el historial con un `estado` que no pertenece al catálogo de estados
- **THEN** el sistema responde 400 con el código `datos_invalidos`

#### Scenario: Rango de fechas inválido

- **WHEN** se consulta el historial con un `desde` o `hasta` sin zona horaria, con `hasta` igual o anterior a `desde`, o con solo uno de los dos
- **THEN** el sistema responde 400 con el código `datos_invalidos`

#### Scenario: Espacio inexistente

- **WHEN** se consulta el historial con un `espacio_id` que no existe
- **THEN** el sistema responde 404 con el código `espacio_no_encontrado`
