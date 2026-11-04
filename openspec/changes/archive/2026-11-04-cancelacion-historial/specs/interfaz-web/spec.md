# Spec Delta

## Purpose

La capacidad `interfaz-web` define el comportamiento observable de la interfaz web del sistema. En este change cubre la cancelación de reservas propias y la consulta del historial. No fija detalles de diseño visual.

## ADDED Requirements

### Requirement: Cancelación de reservas en la interfaz

La interfaz SHALL ofrecer la acción de cancelar solo sobre las solicitudes propias en estado `pendiente` o `aprobada` que aún no han comenzado, y SHALL mostrar el resultado o el mensaje asociado al código de error devuelto por el servidor.

#### Scenario: Acción visible sobre solicitudes propias cancelables

- **WHEN** un usuario autenticado abre el listado de solicitudes
- **THEN** cada solicitud suya en estado `pendiente` o `aprobada` cuyo inicio es futuro ofrece la acción de cancelar

#### Scenario: Sin acción sobre solicitudes no cancelables

- **WHEN** un usuario autenticado abre el listado de solicitudes
- **THEN** las solicitudes en estado `rechazada` o `cancelada`, las que ya comenzaron y las creadas por otros usuarios no ofrecen la acción de cancelar

#### Scenario: Cancelación correcta

- **WHEN** el usuario cancela una solicitud propia y el servidor responde 200
- **THEN** la interfaz muestra la solicitud con el estado `cancelada`

#### Scenario: Mensajes de error de la cancelación

- **WHEN** el servidor responde `transicion_invalida`, `reserva_iniciada` o `permiso_insuficiente`
- **THEN** la interfaz muestra el mensaje asociado al código devuelto
- **AND** la solicitud conserva el estado que mostraba antes de la acción

### Requirement: Consulta del historial en la interfaz

La interfaz SHALL mostrar el historial tal como lo devuelve la API según el rol de la sesión, SHALL permitir aplicar los filtros de espacio, estado y rango de fechas, y SHALL mostrar el mensaje asociado al código de error cuando la consulta falle.

#### Scenario: Entradas del historial visibles

- **WHEN** un usuario autenticado abre la pantalla de historial y el servidor devuelve entradas
- **THEN** la interfaz muestra, por cada entrada, la reserva, el estado anterior, el estado nuevo, el actor y la fecha del cambio

#### Scenario: Envío de los filtros

- **WHEN** el usuario aplica un espacio, un estado y un rango de fechas
- **THEN** la interfaz envía los filtros al servidor, con las fechas con zona horaria explícita, y muestra las entradas devueltas

#### Scenario: Historial vacío

- **WHEN** el servidor devuelve una lista vacía
- **THEN** la interfaz indica que no hay entradas, sin mostrar un mensaje de error

#### Scenario: Error en la consulta del historial

- **WHEN** el servidor responde `datos_invalidos` o `espacio_no_encontrado`
- **THEN** la interfaz muestra el mensaje asociado al código devuelto
- **AND** no muestra entradas
