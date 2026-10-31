# Spec Delta

## Purpose

La capacidad `interfaz-web` define el comportamiento observable de la interfaz web del sistema: inicio de sesión, ciclo de vida de la sesión, tratamiento de errores de autorización, protección de rutas y pantallas de cada módulo. No fija detalles de diseño visual.

## ADDED Requirements

### Requirement: Consulta de espacios en la interfaz

La interfaz SHALL mostrar el catálogo de espacios con nombre, tipo, capacidad y estado, SHALL identificar los espacios inactivos y SHALL permitir consultar el detalle de un espacio, mostrando el mensaje del servidor cuando la consulta falle.

#### Scenario: Listado con espacios activos e inactivos

- **WHEN** el usuario abre la sección de espacios y existen espacios activos e inactivos
- **THEN** la interfaz muestra cada espacio con su nombre, tipo, capacidad y estado
- **AND** identifica los espacios inactivos como tales

#### Scenario: Catálogo sin espacios

- **WHEN** el usuario abre la sección de espacios y no hay ningún espacio registrado
- **THEN** la interfaz muestra el catálogo vacío sin un mensaje de error

#### Scenario: Detalle de un espacio

- **WHEN** el usuario consulta un espacio existente
- **THEN** la interfaz muestra su nombre, tipo, capacidad y estado

#### Scenario: Error al consultar un espacio inexistente

- **WHEN** el backend responde 404 con el código `espacio_no_encontrado`
- **THEN** la interfaz muestra el mensaje asociado a ese código
- **AND** no muestra datos de ningún espacio

### Requirement: Alta y edición de espacios en la interfaz

La interfaz SHALL ofrecer el alta y la edición de espacios a las sesiones cuyo rol las autoriza, SHALL enviar nombre, tipo y capacidad al servidor y SHALL mostrar el mensaje asociado al código de error devuelto por el servidor.

#### Scenario: Alta correcta de un espacio

- **WHEN** un usuario autorizado envía un nombre, un tipo del catálogo y una capacidad válida
- **THEN** la interfaz envía los datos al servidor
- **AND** el catálogo muestra el espacio creado en estado activo

#### Scenario: Edición correcta de un espacio

- **WHEN** un usuario autorizado modifica el nombre, el tipo o la capacidad de un espacio
- **THEN** la interfaz envía los datos al servidor
- **AND** el catálogo muestra los datos actualizados sin alterar el estado del espacio

#### Scenario: Mensajes de error del alta y de la edición

- **WHEN** el backend responde `datos_invalidos`, `tipo_espacio_invalido`, `capacidad_invalida` o `espacio_duplicado`
- **THEN** la interfaz muestra el mensaje asociado al código devuelto
- **AND** no refleja el espacio como creado o modificado

#### Scenario: Acciones de alta y edición no ofrecidas a un rol sin permiso

- **WHEN** un usuario con rol `solicitante` abre la sección de espacios
- **THEN** la interfaz no le ofrece las acciones de alta ni de edición

### Requirement: Activación y desactivación de espacios en la interfaz

La interfaz SHALL ofrecer la activación y la desactivación de espacios a las sesiones cuyo rol las autoriza, SHALL invocar la operación del servidor y SHALL reflejar el estado resultante en el catálogo, mostrando el mensaje del servidor cuando la operación falle.

#### Scenario: Desactivación correcta de un espacio

- **WHEN** un usuario autorizado desactiva un espacio activo
- **THEN** la interfaz invoca la desactivación en el servidor
- **AND** el catálogo muestra ese espacio como inactivo conservando su nombre, tipo y capacidad

#### Scenario: Reactivación correcta de un espacio

- **WHEN** un usuario autorizado reactiva un espacio inactivo
- **THEN** la interfaz invoca la activación en el servidor
- **AND** el catálogo muestra ese espacio como activo conservando su nombre, tipo y capacidad

#### Scenario: Error al desactivar un espacio ya inactivo

- **WHEN** el backend responde 409 con el código `espacio_ya_inactivo`
- **THEN** la interfaz muestra el mensaje asociado a ese código
- **AND** el catálogo mantiene el espacio como inactivo

#### Scenario: Error al desactivar un espacio inexistente

- **WHEN** el backend responde 404 con el código `espacio_no_encontrado`
- **THEN** la interfaz muestra el mensaje asociado a ese código

#### Scenario: Acción de desactivación no ofrecida a un rol sin permiso

- **WHEN** un usuario con rol `solicitante` abre la sección de espacios
- **THEN** la interfaz no le ofrece la acción de desactivación

#### Scenario: Acción de reactivación no ofrecida a un rol sin permiso

- **WHEN** un usuario con rol `solicitante` abre la sección de espacios
- **THEN** la interfaz no le ofrece la acción de reactivación
