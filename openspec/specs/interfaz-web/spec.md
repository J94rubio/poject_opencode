# interfaz-web Specification

## Purpose
La capacidad `interfaz-web` define el comportamiento observable de la interfaz web del sistema: la pantalla de inicio de sesión, el ciclo de vida de la sesión, el tratamiento de los errores de autorización, la protección de las rutas y las pantallas de administración de usuarios. No fija detalles de diseño visual, que quedan fuera de la especificación.

## Requirements

### Requirement: Pantalla de inicio de sesión

La pantalla de inicio de sesión SHALL pedir el correo y la contraseña, SHALL invocar el inicio de sesión del backend y SHALL mostrar el mensaje del servidor asociado al código de error devuelto.

#### Scenario: Credenciales inválidas

- **WHEN** el usuario envía un correo y una contraseña que no corresponden a ninguna cuenta
- **THEN** la interfaz muestra el mensaje asociado al código `credenciales_invalidas`
- **AND** no se inicia sesión

#### Scenario: Cuenta desactivada

- **WHEN** el usuario envía las credenciales correctas de una cuenta desactivada
- **THEN** la interfaz muestra el mensaje asociado al código `usuario_desactivado`
- **AND** no se inicia sesión

#### Scenario: Datos de acceso inválidos

- **WHEN** el usuario envía el correo o la contraseña vacíos o ausentes, o un correo con formato inválido
- **THEN** la interfaz envía la petición al servidor sin validar el formato del correo y muestra el mensaje del código devuelto: `datos_invalidos` cuando el correo o la contraseña están vacíos o ausentes, y `credenciales_invalidas` cuando el servidor lo devuelve, incluido el caso de un correo con formato inválido
- **AND** no se inicia sesión

#### Scenario: Credenciales válidas

- **WHEN** el usuario envía las credenciales correctas de una cuenta activa
- **THEN** la interfaz inicia sesión con el token devuelto por el backend

### Requirement: Ciclo de vida de la sesión

La interfaz SHALL conservar el token de acceso de la sesión iniciada, SHALL restaurarla al volver a cargar la aplicación mientras el token siga siendo válido y SHALL permitir cerrarla de forma explícita.

#### Scenario: Restauración de la sesión

- **WHEN** la aplicación se vuelve a cargar y el token guardado sigue siendo válido
- **THEN** la interfaz restaura la sesión sin volver a pedir las credenciales

#### Scenario: Cierre de sesión

- **WHEN** el usuario cierra sesión
- **THEN** la interfaz descarta el token guardado
- **AND** vuelve a la pantalla de inicio de sesión

#### Scenario: Token expirado

- **WHEN** el backend responde `token_expirado` en una petición autenticada
- **THEN** la interfaz descarta el token guardado
- **AND** vuelve a la pantalla de inicio de sesión

### Requirement: Mensaje de error por permisos insuficientes

Cuando el backend responde 403 con el código `permiso_insuficiente`, la interfaz SHALL mostrar un mensaje de error al usuario y SHALL NOT cerrar la sesión.

#### Scenario: Error de permisos insuficientes

- **WHEN** el backend responde 403 con el código `permiso_insuficiente` a una operación solicitada
- **THEN** la interfaz muestra un mensaje de error
- **AND** la sesión permanece activa

### Requirement: Protección de las rutas de la aplicación

La interfaz SHALL exigir una sesión activa para las rutas protegidas y SHALL limitar el acceso a la sección de administración de usuarios a las cuentas con rol `admin`.

#### Scenario: Ruta protegida sin sesión

- **WHEN** el usuario navega a una ruta protegida sin una sesión activa
- **THEN** la interfaz lo redirige a la pantalla de inicio de sesión

#### Scenario: Acceso de un rol sin permiso

- **WHEN** un usuario con rol `solicitante` o `aprobador` navega a la sección de administración de usuarios
- **THEN** la interfaz no muestra la sección de administración de usuarios

#### Scenario: Acceso del administrador

- **WHEN** un usuario con rol `admin` navega a la sección de administración de usuarios
- **THEN** la interfaz muestra la sección de administración de usuarios

### Requirement: Pantallas de administración de usuarios

La sección de administración de usuarios SHALL mostrar el listado de cuentas con su estado, SHALL permitir dar de alta y editar cuentas, SHALL permitir desactivar y reactivar cuentas y SHALL permitir restablecer la contraseña, mostrando en cada caso el mensaje de error devuelto por el servidor.

#### Scenario: Listado de cuentas con su estado

- **WHEN** el administrador abre el listado de usuarios
- **THEN** la interfaz muestra cada cuenta con su estado activo o inactivo

#### Scenario: Alta y edición de una cuenta

- **WHEN** el administrador da de alta o edita una cuenta
- **THEN** la interfaz envía los datos al servidor
- **AND** muestra el mensaje de error devuelto por el servidor, como `correo_duplicado`, `rol_invalido`, `contrasena_invalida`, `datos_invalidos` u `operacion_no_permitida`

#### Scenario: Desactivación y reactivación de una cuenta

- **WHEN** el administrador desactiva o reactiva una cuenta
- **THEN** la interfaz llama al endpoint correspondiente
- **AND** el listado refleja el nuevo estado de la cuenta

#### Scenario: Restablecimiento de la contraseña

- **WHEN** el administrador restablece la contraseña de una cuenta
- **THEN** la interfaz envía la nueva contraseña al servidor
- **AND** muestra el mensaje de error devuelto por el servidor cuando la operación es rechazada

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
