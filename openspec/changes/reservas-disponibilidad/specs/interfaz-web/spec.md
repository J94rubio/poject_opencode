# Spec Delta

## Purpose

La capacidad `interfaz-web` define el comportamiento observable de la interfaz web del sistema. En este change cubre las pantallas del módulo de reservas: creación de solicitudes, consulta de disponibilidad y listado de solicitudes. No fija detalles de diseño visual.

## ADDED Requirements

### Requirement: Creación de solicitudes en la interfaz

La interfaz SHALL ofrecer a cualquier sesión autenticada un formulario para crear una solicitud de reserva con espacio, inicio y fin, SHALL enviar el inicio y el fin con zona horaria explícita y SHALL mostrar el mensaje asociado al código de error devuelto por el servidor.

#### Scenario: Acceso al formulario de creación

- **WHEN** un usuario autenticado abre la sección de reservas para crear una solicitud
- **THEN** la interfaz presenta los campos de espacio, inicio y fin

#### Scenario: Envío con zona horaria explícita

- **WHEN** el usuario envía el formulario con un espacio, un inicio y un fin
- **THEN** la interfaz envía el inicio y el fin con zona horaria explícita al servidor

#### Scenario: Creación correcta

- **WHEN** el servidor responde 201 con la solicitud creada
- **THEN** la interfaz muestra la solicitud creada con el estado `pendiente`

#### Scenario: Mensajes de error de la creación

- **WHEN** el servidor responde `datos_invalidos`, `espacio_no_encontrado`, `espacio_inactivo` o `reserva_solapada`
- **THEN** la interfaz muestra el mensaje asociado al código devuelto
- **AND** no muestra ninguna solicitud como creada

### Requirement: Consulta de disponibilidad en la interfaz

La interfaz SHALL permitir consultar la disponibilidad de un espacio por rango, SHALL mostrar los intervalos ocupados devueltos por el servidor y SHALL mostrar el mensaje asociado al código de error cuando la consulta falle.

#### Scenario: Intervalos ocupados visibles

- **WHEN** el usuario consulta un espacio y un rango, y el servidor devuelve intervalos ocupados
- **THEN** la interfaz muestra cada intervalo ocupado con su inicio y su fin

#### Scenario: Rango sin reservas aprobadas

- **WHEN** el servidor devuelve una lista vacía
- **THEN** la interfaz indica que no hay intervalos ocupados, sin mostrar un mensaje de error

#### Scenario: Error en la consulta

- **WHEN** el servidor responde `datos_invalidos` o `espacio_no_encontrado`
- **THEN** la interfaz muestra el mensaje asociado al código devuelto
- **AND** no muestra intervalos

### Requirement: Listado de solicitudes en la interfaz

La interfaz SHALL mostrar el listado de solicitudes tal como lo devuelve la API según el rol de la sesión, y SHALL mostrar el mensaje del servidor cuando la consulta falle.

#### Scenario: Listado de un solicitante

- **WHEN** un usuario con rol `solicitante` abre el listado de solicitudes
- **THEN** la interfaz muestra únicamente las solicitudes que devuelve la API para ese usuario

#### Scenario: Listado de un aprobador o administrador

- **WHEN** un usuario con rol `aprobador` o `admin` abre el listado de solicitudes
- **THEN** la interfaz muestra todas las solicitudes que devuelve la API

#### Scenario: Listado vacío

- **WHEN** la API devuelve una lista vacía
- **THEN** la interfaz muestra el listado vacío sin un mensaje de error
