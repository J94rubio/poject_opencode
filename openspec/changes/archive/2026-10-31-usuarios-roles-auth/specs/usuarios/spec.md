# Spec Delta

## Purpose

La capacidad `usuarios` define el ciclo de vida de las cuentas de usuario del sistema: alta, edición, estado activo o inactivo, cambio de rol, restablecimiento de contraseña y catálogo de roles, con una administración exclusiva del rol `admin`.

## ADDED Requirements

### Requirement: Alta de usuarios por el administrador

El sistema SHALL permitir que un usuario con rol `admin` cree una cuenta con nombre, correo, contraseña y rol, y SHALL registrar la contraseña únicamente como hash con sal.

#### Scenario: Alta válida

- **WHEN** un `admin` crea un usuario con nombre, correo, contraseña y rol válidos
- **THEN** el sistema responde 201 con los datos del usuario y la cuenta queda activa
- **AND** la respuesta no incluye la contraseña ni su hash

#### Scenario: Alta con correo ya registrado

- **WHEN** el correo enviado ya pertenece a otra cuenta
- **THEN** el sistema responde 409 con el código `correo_duplicado`
- **AND** no se crea ninguna cuenta

#### Scenario: Alta con rol fuera del catálogo

- **WHEN** el rol enviado no pertenece al catálogo de roles del sistema
- **THEN** el sistema responde 400 con el código `rol_invalido`
- **AND** no se crea ninguna cuenta

#### Scenario: Alta con contraseña que no cumple la política

- **WHEN** la contraseña tiene menos de 8 caracteres
- **THEN** el sistema responde 400 con el código `contrasena_invalida`
- **AND** no se crea ninguna cuenta

#### Scenario: Alta con contraseña que solo cumple el mínimo

- **WHEN** la contraseña tiene al menos 8 caracteres pero no contiene mayúsculas, dígitos ni símbolos
- **THEN** el sistema responde 201 y la cuenta queda creada
- **AND** no se exige ninguna regla de composición adicional

#### Scenario: Alta con correo de formato inválido

- **WHEN** el correo enviado no tiene un formato de correo válido
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna cuenta

#### Scenario: Alta con campos obligatorios faltantes

- **WHEN** falta el nombre, el correo o la contraseña en la petición de alta
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ninguna cuenta

#### Scenario: Alta solicitada por un rol sin permiso

- **WHEN** un usuario con rol `solicitante` o `aprobador` intenta crear un usuario
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** no se crea ninguna cuenta

#### Scenario: Alta sin autenticación

- **WHEN** una petición sin token intenta crear una cuenta de usuario
- **THEN** el sistema responde 401 con el código `token_ausente`
- **AND** no se crea ninguna cuenta

### Requirement: Almacenamiento seguro de las contraseñas

La contraseña de cada cuenta SHALL almacenarse únicamente como hash con sal, nunca en texto plano, y SHALL ser irreversible.

#### Scenario: Verificación de la contraseña con el valor almacenado

- **WHEN** se crea una cuenta con una contraseña conocida
- **THEN** el valor almacenado difiere de la contraseña en texto plano
- **AND** la verificación con esa contraseña correcta resulta exitosa
- **AND** dos cuentas con la misma contraseña almacenan valores distintos por la sal

#### Scenario: El detalle de usuario no expone credenciales

- **WHEN** se consulta el detalle de una cuenta por su identificador
- **THEN** la respuesta no incluye la contraseña ni su hash

### Requirement: Normalización y unicidad del correo

El correo SHALL almacenarse normalizado en minúsculas y SHALL compararse sin distinguir mayúsculas de minúsculas para la detección de duplicados.

#### Scenario: Inicio de sesión con correo en mayúsculas

- **WHEN** un usuario se autentica con un correo escrito en mayúsculas y la cuenta está almacenada en minúsculas
- **THEN** el inicio de sesión es exitoso

#### Scenario: Duplicado que solo difiere en mayúsculas

- **WHEN** se crea un usuario con un correo que solo difiere en mayúsculas de otro ya registrado
- **THEN** el sistema responde 409 con el código `correo_duplicado`
- **AND** no se crea ninguna cuenta

### Requirement: Listado de cuentas de usuario

El sistema SHALL permitir que un `admin` consulte el listado de cuentas con su identificador, nombre, correo, rol y estado, incluyendo las cuentas desactivadas.

#### Scenario: Listado solicitado por el administrador

- **WHEN** un `admin` solicita el listado de cuentas
- **THEN** el sistema responde 200 con la lista de usuarios, cada uno con identificador, nombre, correo, rol y estado activo

#### Scenario: El listado incluye cuentas desactivadas

- **WHEN** existe alguna cuenta desactivada
- **THEN** aparece en el listado con su estado inactivo
- **AND** sus datos se conservan íntegros

#### Scenario: Listado solicitado por un rol sin permiso

- **WHEN** un `solicitante` o un `aprobador` solicita el listado de cuentas
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la respuesta no contiene datos de cuentas

### Requirement: Consulta del detalle de una cuenta

El sistema SHALL permitir que un `admin` consulte el detalle de una cuenta por su identificador, devolviendo nombre, correo, rol y estado, sin exponer credenciales.

#### Scenario: Detalle de una cuenta existente

- **WHEN** un `admin` solicita el detalle de una cuenta existente
- **THEN** el sistema responde 200 con su nombre, correo, rol y estado

#### Scenario: Detalle de una cuenta inexistente

- **WHEN** el identificador solicitado no corresponde a ninguna cuenta
- **THEN** el sistema responde 404 con el código `usuario_no_encontrado`

#### Scenario: Detalle solicitado por un rol sin permiso

- **WHEN** un `solicitante` o un `aprobador` solicita el detalle de una cuenta
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`

### Requirement: Edición de los datos de una cuenta

El sistema SHALL permitir que un `admin` actualice el nombre, el correo y el rol de una cuenta, sin alterar su estado activo ni su contraseña.

#### Scenario: Cambio de nombre

- **WHEN** un `admin` actualiza el nombre de una cuenta
- **THEN** el sistema responde 200 con los datos actualizados

#### Scenario: Cambio de rol

- **WHEN** un `admin` cambia el rol de una cuenta a otro rol del catálogo
- **THEN** el sistema responde 200 y el rol nuevo se aplica a las siguientes peticiones del usuario

#### Scenario: Cambio de correo a uno ya registrado

- **WHEN** un `admin` actualiza el correo de una cuenta con un correo que ya pertenece a otra cuenta
- **THEN** el sistema responde 409 con el código `correo_duplicado`
- **AND** el correo de la cuenta no cambia

#### Scenario: Cambio de rol fuera del catálogo

- **WHEN** un `admin` intenta asignar un rol que no pertenece al catálogo
- **THEN** el sistema responde 400 con el código `rol_invalido`
- **AND** el rol de la cuenta no cambia

#### Scenario: Cambio del propio rol

- **WHEN** un `admin` intenta cambiar el rol de su propia cuenta
- **THEN** el sistema responde 409 con el código `operacion_no_permitida`
- **AND** el rol de la cuenta no cambia

#### Scenario: Edición solicitada por un rol sin permiso

- **WHEN** un `solicitante` o un `aprobador` intenta editar una cuenta
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la cuenta no se modifica

### Requirement: Restablecimiento de contraseña por el administrador

El sistema SHALL permitir que un `admin` asigne una nueva contraseña a una cuenta, y SHALL NOT permitir leer la contraseña vigente.

#### Scenario: Restablecimiento válido

- **WHEN** un `admin` asigna una contraseña nueva con al menos 8 caracteres
- **THEN** el sistema responde 200 y el usuario puede autenticarse con la contraseña nueva

#### Scenario: Contraseña que no cumple la política

- **WHEN** un `admin` asigna una contraseña con menos de 8 caracteres
- **THEN** el sistema responde 400 con el código `contrasena_invalida`
- **AND** la contraseña vigente se conserva

#### Scenario: Restablecimiento solicitado por un rol sin permiso

- **WHEN** un `solicitante` o un `aprobador` intenta restablecer una contraseña
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la contraseña no cambia

### Requirement: Desactivación y activación de cuentas

El sistema SHALL permitir que un `admin` desactive y reactive cuentas. Una cuenta desactivada SHALL conservar sus datos, pero SHALL perder el acceso al sistema.

#### Scenario: Desactivación de una cuenta activa

- **WHEN** un `admin` desactiva una cuenta activa
- **THEN** la cuenta queda con estado inactivo y el usuario ya no puede autenticarse

#### Scenario: Reactivación de una cuenta desactivada

- **WHEN** un `admin` reactiva una cuenta desactivada
- **THEN** la cuenta vuelve a estar activa y el usuario puede autenticarse de nuevo

#### Scenario: Conservación de los datos tras desactivar

- **WHEN** una cuenta con datos registrados es desactivada
- **THEN** sus datos se conservan sin cambios

#### Scenario: Desactivación solicitada por un rol sin permiso

- **WHEN** un `solicitante` o un `aprobador` intenta desactivar una cuenta
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la cuenta sigue activa

#### Scenario: Desactivación de la propia cuenta

- **WHEN** un `admin` intenta desactivar su propia cuenta
- **THEN** el sistema responde 409 con el código `operacion_no_permitida`
- **AND** la cuenta sigue activa

#### Scenario: Desactivación de la cuenta de otro administrador

- **WHEN** un `admin` desactiva la cuenta de otro administrador
- **THEN** el sistema responde 200 y esa cuenta queda desactivada

### Requirement: Catálogo de roles del sistema

El sistema SHALL exponer un catálogo cerrado de roles compuesto por `solicitante`, `aprobador` y `admin`, y SHALL rechazar cualquier otro valor de rol en el alta o en el cambio de rol de una cuenta.

#### Scenario: Consulta del catálogo por el administrador

- **WHEN** un `admin` solicita el catálogo de roles
- **THEN** el sistema responde 200 con los tres roles `solicitante`, `aprobador` y `admin` y sus identificadores

#### Scenario: Consulta del catálogo por un rol sin permiso

- **WHEN** un `solicitante` o un `aprobador` solicita el catálogo de roles
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`

### Requirement: Creación del primer administrador por línea de comandos

El sistema SHALL ofrecer un comando de línea de comandos que cree una cuenta con rol `admin` en estado activo cuando no exista ningún administrador activo, y SHALL fallar con un error explícito, sin crear ninguna cuenta, cuando esa condición no se cumpla.

#### Scenario: Creación del primer administrador

- **WHEN** se ejecuta el comando con un correo válido y una contraseña de 8 caracteres o más y no existe ninguna cuenta con rol `admin` activa
- **THEN** el comando crea la cuenta con rol `admin` en estado activo

#### Scenario: Ya existe un administrador activo

- **WHEN** se ejecuta el comando y ya existe una cuenta con rol `admin` activa
- **THEN** el comando falla con un error explícito
- **AND** no se crea ninguna cuenta

#### Scenario: Contraseña que no cumple la política

- **WHEN** se ejecuta el comando con una contraseña de menos de 8 caracteres
- **THEN** el comando falla con un error explícito
- **AND** no se crea ninguna cuenta

#### Scenario: Correo inválido o duplicado

- **WHEN** se ejecuta el comando con un correo de formato inválido o con un correo ya registrado
- **THEN** el comando falla con un error explícito
- **AND** no se crea ninguna cuenta
