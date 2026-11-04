# Spec Delta

## Purpose

La capacidad `interfaz-web` define el comportamiento observable de la interfaz web del sistema. En este change cubre las acciones de decisión (aprobar y rechazar) sobre las solicitudes pendientes. No fija detalles de diseño visual.

## ADDED Requirements

### Requirement: Decisión de solicitudes en la interfaz

La interfaz SHALL ofrecer las acciones de aprobar y rechazar sobre las solicitudes pendientes solo a sesiones con rol `aprobador` o `admin`, SHALL exigir un motivo para rechazar y SHALL mostrar el resultado o el mensaje asociado al código de error devuelto por el servidor.

#### Scenario: Acciones visibles para aprobador y administrador

- **WHEN** un usuario con rol `aprobador` o `admin` abre el listado de solicitudes
- **THEN** cada solicitud `pendiente` ofrece las acciones de aprobar y rechazar

#### Scenario: Sin acciones para el solicitante

- **WHEN** un usuario con rol `solicitante` abre el listado de solicitudes
- **THEN** ninguna solicitud ofrece las acciones de aprobar o rechazar

#### Scenario: Sin acciones sobre solicitudes decididas

- **WHEN** un usuario con rol `aprobador` o `admin` abre el listado de solicitudes
- **THEN** las solicitudes en estado `aprobada`, `rechazada` o `cancelada` no ofrecen las acciones de aprobar o rechazar

#### Scenario: Aprobación correcta

- **WHEN** el usuario aprueba una solicitud y el servidor responde 200
- **THEN** la interfaz muestra la solicitud con el estado `aprobada`

#### Scenario: Rechazo con motivo

- **WHEN** el usuario rechaza una solicitud indicando un motivo y el servidor responde 200
- **THEN** la interfaz muestra la solicitud con el estado `rechazada` y su motivo

#### Scenario: Rechazo sin motivo

- **WHEN** el usuario intenta enviar un rechazo sin motivo
- **THEN** la interfaz no envía la petición y muestra que el motivo es obligatorio

#### Scenario: Mensajes de error de la decisión

- **WHEN** el servidor responde `reserva_solapada`, `transicion_invalida`, `solicitud_vencida`, `espacio_inactivo` o `permiso_insuficiente`
- **THEN** la interfaz muestra el mensaje asociado al código devuelto
- **AND** la solicitud conserva el estado que mostraba antes de la acción
