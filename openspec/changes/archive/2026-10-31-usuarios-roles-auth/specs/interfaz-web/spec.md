# Spec Delta

## Purpose

La capacidad `interfaz-web` define el comportamiento observable de la interfaz web del sistema: la pantalla de inicio de sesión, el ciclo de vida de la sesión, el tratamiento de los errores de autorización, la protección de las rutas y las pantallas de administración de usuarios. No fija detalles de diseño visual, que quedan fuera de la especificación.

## ADDED Requirements

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
