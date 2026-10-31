# auth Specification

## Purpose
La capacidad `auth` define cómo el sistema verifica la identidad de quien actúa y qué puede hacer en cada módulo: emisión y validación de tokens JWT, control del estado de la cuenta y aplicación de la matriz jerárquica de permisos por rol sobre espacios, reservas, aprobaciones e historial.

## Requirements

### Requirement: Emisión de token de acceso tras validar credenciales

El sistema SHALL autenticar al usuario con correo y contraseña y, cuando las credenciales son válidas y la cuenta está activa, emitir un token JWT de acceso firmado que contenga únicamente el identificador del usuario, la fecha de emisión y la fecha de expiración.

#### Scenario: Credenciales válidas de una cuenta activa

- **WHEN** se envía el correo de una cuenta activa junto con su contraseña correcta
- **THEN** el sistema responde 200 con el token de acceso, su tipo, su vigencia en segundos y los datos públicos del usuario (identificador, nombre, correo, rol)
- **AND** la respuesta no incluye la contraseña ni su hash

#### Scenario: Contenido del token emitido

- **WHEN** se decodifica un token de acceso emitido por el sistema
- **THEN** sus claims son el identificador del usuario, la fecha de emisión y la fecha de expiración
- **AND** no incluye el rol ni ningún otro dato de la cuenta

#### Scenario: Contraseña incorrecta

- **WHEN** el correo corresponde a una cuenta existente pero la contraseña no es la correcta
- **THEN** el sistema responde 401 con el código `credenciales_invalidas`
- **AND** el mensaje es idéntico al que se devuelve cuando el correo no existe, sin revelar cuál de los dos datos falló
- **AND** no se emite ningún token

#### Scenario: Correo inexistente

- **WHEN** el correo enviado no corresponde a ninguna cuenta
- **THEN** el sistema responde 401 con el código `credenciales_invalidas` y el mismo mensaje genérico que para una contraseña incorrecta
- **AND** no se emite ningún token

#### Scenario: Cuenta desactivada

- **WHEN** las credenciales son correctas pero la cuenta está desactivada
- **THEN** el sistema responde 401 con el código `usuario_desactivado`, indicando que la cuenta está desactivada
- **AND** no se emite ningún token

#### Scenario: Datos de acceso incompletos

- **WHEN** falta el correo o falta la contraseña en la petición de autenticación
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se emite ningún token

### Requirement: Validación del token en peticiones protegidas

Toda petición a un recurso protegido SHALL validar la firma, la expiración y el estado activo de la cuenta asociada al token antes de ejecutar la lógica de negocio, y SHALL responder 401 con un código de error específico cuando la validación falle.

#### Scenario: Petición sin token

- **WHEN** una petición a un recurso protegido no incluye la cabecera de autorización
- **THEN** el sistema responde 401 con el código `token_ausente`
- **AND** no ejecuta ninguna lógica de negocio

#### Scenario: Token mal formado

- **WHEN** la cabecera de autorización no tiene el formato `Bearer <token>` o el valor no es un JWT con la estructura esperada
- **THEN** el sistema responde 401 con el código `token_invalido`

#### Scenario: Firma inválida o token manipulado

- **WHEN** el token está bien formado pero su firma no corresponde a la clave de verificación de la aplicación
- **THEN** el sistema responde 401 con el código `token_invalido`

#### Scenario: Token expirado

- **WHEN** el token es válido pero su fecha de expiración ya pasó
- **THEN** el sistema responde 401 con el código `token_expirado`
- **AND** la respuesta indica que el token expiró y no que las credenciales fueron incorrectas

#### Scenario: Token válido

- **WHEN** el token es válido, no ha expirado y la cuenta asociada está activa
- **THEN** el sistema ejecuta la petición con la identidad del usuario del token y responde el resultado normal del recurso invocado

### Requirement: Revocación inmediata del acceso de una cuenta desactivada

Cuando el administrador desactiva una cuenta, los tokens emitidos previamente a esa cuenta SHALL ser rechazados en la siguiente petición con el código `usuario_desactivado`, aunque el token todavía no haya expirado.

#### Scenario: Token vigente después de la desactivación

- **WHEN** un usuario con un token aún vigente es desactivado por el administrador y luego invoca un recurso protegido
- **THEN** el sistema responde 401 con el código `usuario_desactivado`
- **AND** no ejecuta ninguna lógica de negocio

#### Scenario: Reactivación antes de la expiración del token

- **WHEN** el administrador reactiva la cuenta antes de que expire el token emitido y el usuario invoca un recurso protegido
- **THEN** la petición se atiende con normalidad y el usuario recupera el acceso

### Requirement: Consulta del usuario autenticado

El sistema SHALL exponer un recurso para consultar los datos del usuario autenticado a partir del token presentado, devolviendo identificador, nombre, correo, rol y estado de la cuenta, sin exponer la contraseña ni su hash.

#### Scenario: Consulta con token válido

- **WHEN** se solicita el perfil con un token válido de una cuenta activa
- **THEN** el sistema responde 200 con el identificador, nombre, correo, rol y estado activo del usuario

#### Scenario: Consulta sin token

- **WHEN** se solicita el perfil sin token
- **THEN** el sistema responde 401 con el código `token_ausente`

#### Scenario: Consulta con token expirado

- **WHEN** se solicita el perfil con un token expirado
- **THEN** el sistema responde 401 con el código `token_expirado`

### Requirement: Jerarquía y matriz de permisos por rol

El sistema SHALL aplicar al usuario el conjunto de permisos de su rol. La jerarquía es `admin` ⊇ `aprobador` ⊇ `solicitante`: cada rol incluye la totalidad de los permisos del anterior. Aprobar y rechazar no se aplican a las solicitudes propias del usuario; esa regla se verifica en el change `aprobacion-reservas`.

```
| Permiso | solicitante | aprobador | admin |
|---|---|---|---|
| espacios:ver | sí | sí | sí |
| espacios:crear | no | sí | sí |
| espacios:editar | no | sí | sí |
| espacios:desactivar | no | sí | sí |
| espacios:activar | no | sí | sí |
| reservas:crear | sí | sí | sí |
| reservas:ver_propias | sí | sí | sí |
| reservas:cancelar_propia | sí | sí | sí |
| reservas:ver_todas | no | sí | sí |
| aprobaciones:aprobar | no | sí | sí |
| aprobaciones:rechazar | no | sí | sí |
| historial:ver_propio | sí | sí | sí |
| historial:ver_todos | no | sí | sí |
| usuarios:ver | no | no | sí |
| usuarios:crear | no | no | sí |
| usuarios:editar | no | no | sí |
| usuarios:desactivar | no | no | sí |
| usuarios:activar | no | no | sí |
| usuarios:resetear_password | no | no | sí |
| roles:ver | no | no | sí |
```

#### Scenario: La matriz respeta la jerarquía de roles

- **WHEN** se compara, para cada permiso de la matriz, el conjunto de roles que lo poseen
- **THEN** el conjunto de roles que lo poseen en `aprobador` incluye al de `solicitante`, y el de `admin` incluye al de `aprobador`

#### Scenario: Gestión de usuarios denegada al solicitante

- **WHEN** un usuario con rol `solicitante` intenta listar, crear, editar o desactivar usuarios
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** no se modifica ningún dato de cuentas

#### Scenario: Gestión de usuarios denegada al aprobador

- **WHEN** un usuario con rol `aprobador` intenta listar, crear, editar o desactivar usuarios
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** no se modifica ningún dato de cuentas

#### Scenario: Gestión de usuarios permitida al administrador

- **WHEN** un usuario con rol `admin` crea una cuenta con datos válidos
- **THEN** el sistema ejecuta la operación y responde con éxito

### Requirement: Denegación de acceso sin permiso

Cuando un usuario autenticado invoca una operación que su rol no permite, el sistema SHALL responder 403 con el código `permiso_insuficiente` y SHALL NOT modificar ningún dato como consecuencia de la petición denegada.

#### Scenario: Denegación sobre una operación de escritura

- **WHEN** un usuario autenticado intenta una operación de escritura no permitida por su rol
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** el estado de los datos afectados permanece sin cambios

#### Scenario: Denegación sobre una operación de lectura

- **WHEN** un usuario autenticado intenta una operación de lectura no permitida por su rol
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** la respuesta no contiene los datos protegidos ni un resumen de su contenido

### Requirement: Resolución del rol efectivo desde el registro del usuario

El token de acceso no transporta el rol. El sistema SHALL obtener el rol efectivo de cada petición a partir del registro del usuario en la base de datos, de modo que un cambio de rol surta efecto en la siguiente petición sin necesidad de emitir un token nuevo.

#### Scenario: Cambio de rol con token vigente

- **WHEN** el administrador cambia el rol de un usuario y este invoca un recurso protegido con su token aún vigente
- **THEN** la petición se evalúa con el rol nuevo y con los permisos correspondientes a ese rol

### Requirement: Vigencia del token de acceso

La vigencia del token de acceso SHALL ser configurable y SHALL tener un valor por defecto de 60 minutos, de modo que el valor efectivo en un momento dado pueda fijarse de forma determinista para las pruebas.

#### Scenario: Vigencia por defecto

- **WHEN** la aplicación se ejecuta con la configuración por defecto y un usuario se autentica
- **THEN** el token emitido declara una vigencia de 60 minutos y expira transcurrido ese intervalo desde su emisión

#### Scenario: Vigencia configurada

- **WHEN** la aplicación se configura con una vigencia concreta distinta de la por defecto y un usuario se autentica
- **THEN** el token emitido declara esa misma vigencia y expira transcurrido ese intervalo desde su emisión

### Requirement: Formato de las respuestas de error de la API

Todas las respuestas de error de la API SHALL tener forma JSON `{"error": {"codigo": <código>, "mensaje": <mensaje>}}` y SHALL usar el código HTTP que corresponde al error: 400 para datos inválidos, 401 para credenciales o token no válidos, 403 para permisos insuficientes, 404 para un recurso inexistente, 405 para método no permitido, 409 para un conflicto de unicidad o de estado y 500 para un error interno no controlado.

#### Scenario: Error de credenciales

- **WHEN** el inicio de sesión falla por credenciales incorrectas
- **THEN** el sistema responde 401 con el cuerpo `{"error": {"codigo": "credenciales_invalidas", "mensaje": <mensaje>}}`

#### Scenario: Error de datos inválidos

- **WHEN** una petición contiene datos que no cumplen el formato esperado
- **THEN** el sistema responde 400 con el cuerpo `{"error": {"codigo": "datos_invalidos", "mensaje": <mensaje>}}`

#### Scenario: Error de permiso

- **WHEN** un usuario autenticado ejecuta una operación no permitida por su rol
- **THEN** el sistema responde 403 con el cuerpo `{"error": {"codigo": "permiso_insuficiente", "mensaje": <mensaje>}}`

#### Scenario: Recurso inexistente

- **WHEN** se solicita un recurso que no existe
- **THEN** el sistema responde 404 con el cuerpo `{"error": {"codigo": "usuario_no_encontrado", "mensaje": <mensaje>}}`

#### Scenario: Conflicto de unicidad

- **WHEN** se crea un recurso con un valor que ya está registrado
- **THEN** el sistema responde 409 con el cuerpo `{"error": {"codigo": "correo_duplicado", "mensaje": <mensaje>}}`

#### Scenario: Ruta inexistente

- **WHEN** se solicita una ruta que no existe
- **THEN** el sistema responde 404 con el cuerpo `{"error": {"codigo": "ruta_no_encontrada", "mensaje": <mensaje>}}`

#### Scenario: Método no permitido

- **WHEN** se solicita una ruta con un método HTTP no permitido
- **THEN** el sistema responde 405 con el cuerpo `{"error": {"codigo": "metodo_no_permitido", "mensaje": <mensaje>}}`

#### Scenario: Cuerpo JSON mal formado

- **WHEN** se envía una petición con un cuerpo JSON mal formado
- **THEN** el sistema responde 400 con el cuerpo `{"error": {"codigo": "datos_invalidos", "mensaje": <mensaje>}}`

#### Scenario: Error interno no controlado

- **WHEN** se produce un error interno no controlado
- **THEN** el sistema responde 500 con el cuerpo `{"error": {"codigo": "error_interno", "mensaje": <mensaje>}}`
- **AND** el mensaje es un texto fijo sin detalle técnico ni traza

#### Scenario: Los mensajes de error son textos fijos

- **WHEN** el sistema responde con un error de la API
- **THEN** el mensaje es un texto fijo del catálogo de errores
- **AND** no incluye ningún dato de la petición, como el correo, la contraseña o el detalle técnico del fallo
