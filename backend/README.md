# Backend: sistema de reservas de espacios académicos

API REST en Flask. Este documento describe los endpoints de los módulos `usuarios` (design.md, D7 y D8, del change `usuarios-roles-auth`) y `espacios` (design.md, D5 y D6, del change `espacios`) y el catálogo de códigos de error de la API.

Todas las rutas de los módulos `usuarios` y `espacios` son protegidas: exigen la cabecera `Authorization: Bearer <token>` con un token obtenido en `POST /api/auth/login`, y el permiso indicado en la tabla de cada módulo. Los permisos de gestión de usuarios y de consulta de roles los tiene únicamente el rol `admin`.

## Puesta en marcha

Todos los comandos se ejecutan desde la raíz del repositorio, en PowerShell clásico (Windows PowerShell 5.1). Se necesita Python y un servidor PostgreSQL 17 con la base de datos ya creada.

### 1. Instalar las dependencias en el entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

Si PowerShell bloquea `Activate.ps1` por la política de ejecución, permítala solo para la sesión actual con `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` y vuelva a activar el entorno.

### 2. Definir las variables de entorno solo en la terminal

La configuración se lee únicamente de variables de entorno. No se usa ningún archivo `.env`: las variables se definen en la terminal y valen solo para esa sesión. Nunca escriba sus valores en archivos del repositorio, en scripts ni en la documentación, y no los imprima en pantalla.

**`DATABASE_URL`**, sin que la contraseña quede en el historial. `Read-Host -AsSecureString` pide la contraseña sin mostrarla; el historial de PowerShell guarda solo la línea del comando, nunca lo que se teclea en el prompt. La contraseña se codifica para URL por si contiene caracteres como `@`, `:` o `/`:

```powershell
$clave = Read-Host -AsSecureString "Contraseña de PostgreSQL"
$texto = [System.Net.NetworkCredential]::new("", $clave).Password
$env:DATABASE_URL = "postgresql+psycopg://<usuario>:" + [uri]::EscapeDataString($texto) + "@localhost:5432/<base>"
Remove-Variable clave, texto
```

Sustituya `<usuario>` y `<base>` por el usuario y la base de datos de su instalación (y el host o el puerto, si no son los habituales).

**`JWT_SECRET_KEY`**, generada aleatoriamente y asignada directamente a la variable, sin escribirla en ningún archivo ni mostrarla en pantalla:

```powershell
$env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Como la clave se genera de nuevo en cada sesión, los tokens emitidos en una sesión anterior dejan de ser válidos al reiniciar el servidor con otra clave.

**`CORS_ORIGINS`**: lista de orígenes permitidos, separados por comas. Para el servidor de desarrollo del frontend:

```powershell
$env:CORS_ORIGINS = "http://localhost:5173"
```

Sin esta variable no se permite ningún origen cruzado.

### 3. Aplicar las migraciones

```powershell
alembic -c backend/alembic.ini upgrade head
```

### 4. Crear el primer administrador

```powershell
flask --app backend.app create-admin --correo <correo-del-administrador>
```

El comando pide la contraseña dos veces sin mostrarla. Las opciones y los casos de error se describen en [Primer administrador: `flask create-admin`](#primer-administrador-flask-create-admin).

### 5. Arrancar el servidor

```powershell
flask --app backend.app run --port 5000
```

La API queda disponible en `http://localhost:5000`. Para conectar el frontend, consulte `frontend/README.md`.

## Endpoints del módulo `usuarios`

| Método | Ruta | Permiso | Respuesta correcta |
|---|---|---|---|
| `GET` | `/api/usuarios` | `usuarios:ver` | 200 con la lista de cuentas, incluidas las inactivas |
| `POST` | `/api/usuarios` | `usuarios:crear` | 201 con los datos de la cuenta creada |
| `GET` | `/api/usuarios/{id}` | `usuarios:ver` | 200 con los datos de la cuenta |
| `PATCH` | `/api/usuarios/{id}` | `usuarios:editar` | 200 con los datos actualizados |
| `POST` | `/api/usuarios/{id}/password` | `usuarios:resetear_password` | 200 sin cuerpo |
| `POST` | `/api/usuarios/{id}/desactivar` | `usuarios:desactivar` | 200 con el estado actualizado |
| `POST` | `/api/usuarios/{id}/activar` | `usuarios:activar` | 200 con el estado actualizado |
| `GET` | `/api/roles` | `roles:ver` | 200 con el catálogo de roles |

Los datos de una cuenta nunca incluyen la contraseña ni su hash:

```json
{"id": 7, "nombre": "Luis Gómez", "correo": "luis.gomez@example.com", "rol": "solicitante", "activo": true}
```

### Listar cuentas

```http
GET /api/usuarios
Authorization: Bearer <token>
```

Respuesta 200: lista de cuentas con el formato anterior, ordenada por identificador.

### Crear una cuenta

```http
POST /api/usuarios
Authorization: Bearer <token>
Content-Type: application/json

{"nombre": "Luis Gómez", "correo": "Luis.Gomez@example.com", "contrasena": "contrasena-nueva", "rol": "solicitante"}
```

Respuesta 201: la cuenta creada, activa y con el correo en minúsculas. Los cuatro campos son obligatorios. La contraseña debe tener al menos 8 caracteres, sin reglas de composición. Errores: `datos_invalidos` (campo faltante o correo con formato inválido), `contrasena_invalida`, `rol_invalido` y `correo_duplicado` (también si el correo solo difiere en mayúsculas).

### Consultar una cuenta

```http
GET /api/usuarios/7
Authorization: Bearer <token>
```

Respuesta 200: la cuenta. Error: `usuario_no_encontrado`.

### Editar una cuenta

```http
PATCH /api/usuarios/7
Authorization: Bearer <token>
Content-Type: application/json

{"nombre": "Luis Gómez Ruiz", "correo": "luis.ruiz@example.com", "rol": "aprobador"}
```

Respuesta 200: la cuenta actualizada. Todos los campos son opcionales y solo se editan `nombre`, `correo` y `rol`; un cuerpo vacío `{}` responde 200 sin cambios. Cualquier otro campo, incluidos `activo` y `contrasena`, responde `datos_invalidos` sin modificar nada: el estado se cambia con `desactivar`/`activar` y la contraseña con `password`. Errores: `datos_invalidos`, `rol_invalido`, `correo_duplicado`, `usuario_no_encontrado` y `operacion_no_permitida` (un `admin` no puede cambiar su propio rol).

### Restablecer la contraseña

```http
POST /api/usuarios/7/password
Authorization: Bearer <token>
Content-Type: application/json

{"contrasena": "nueva-clave"}
```

Respuesta 200 sin cuerpo. La contraseña vigente no se puede leer. Errores: `datos_invalidos` (falta la contraseña), `contrasena_invalida` y `usuario_no_encontrado`.

### Desactivar y reactivar una cuenta

```http
POST /api/usuarios/7/desactivar
Authorization: Bearer <token>
```

```http
POST /api/usuarios/7/activar
Authorization: Bearer <token>
```

Respuesta 200: la cuenta con `"activo": false` o `"activo": true`. La cuenta desactivada conserva sus datos y pierde el acceso de inmediato, aunque su token no haya expirado. Errores: `usuario_no_encontrado` y `operacion_no_permitida` (un `admin` no puede desactivar su propia cuenta).

### Consultar el catálogo de roles

```http
GET /api/roles
Authorization: Bearer <token>
```

Respuesta 200:

```json
[{"id": 1, "nombre": "solicitante"}, {"id": 2, "nombre": "aprobador"}, {"id": 3, "nombre": "admin"}]
```

## Endpoints de espacios

La consulta (`espacios:ver`) está permitida a los roles `solicitante`, `aprobador` y `admin`. El alta, la edición, la desactivación y la reactivación (`espacios:crear`, `espacios:editar`, `espacios:desactivar` y `espacios:activar`) solo a `aprobador` y `admin`; un `solicitante` recibe 403 con `permiso_insuficiente` y no se modifica ningún dato.

| Método | Ruta | Permiso | Respuesta correcta |
|---|---|---|---|
| `GET` | `/api/espacios` | `espacios:ver` | 200 con la lista completa, incluidos los inactivos |
| `GET` | `/api/espacios/{id}` | `espacios:ver` | 200 con el espacio |
| `POST` | `/api/espacios` | `espacios:crear` | 201 con el espacio creado en estado `activo` |
| `PATCH` | `/api/espacios/{id}` | `espacios:editar` | 200 con el espacio actualizado |
| `POST` | `/api/espacios/{id}/desactivar` | `espacios:desactivar` | 200 con el espacio en estado `inactivo` |
| `POST` | `/api/espacios/{id}/activar` | `espacios:activar` | 200 con el espacio en estado `activo` |

Cada espacio se representa con exactamente estos campos, sin marcas de tiempo ni datos internos. El `tipo` es `laboratorio`, `auditorio` o `sala_de_computo`, y el `estado`, `activo` o `inactivo`:

```json
{"id": 3, "nombre": "Laboratorio de Redes", "tipo": "laboratorio", "capacidad": 30, "estado": "activo"}
```

### Listar espacios

```http
GET /api/espacios
Authorization: Bearer <token>
```

Respuesta 200: lista de espacios con el formato anterior, ordenada por identificador e incluidos los inactivos, identificados por su `estado`. Sin espacios registrados, una lista vacía `[]`. No hay paginación ni filtros.

### Consultar un espacio

```http
GET /api/espacios/3
Authorization: Bearer <token>
```

Respuesta 200: el espacio, también si está inactivo. Error: `espacio_no_encontrado`.

### Crear un espacio

```http
POST /api/espacios
Authorization: Bearer <token>
Content-Type: application/json

{"nombre": "Laboratorio de Redes", "tipo": "laboratorio", "capacidad": 30}
```

Respuesta 201: el espacio creado en estado `activo`. Los tres campos son obligatorios y no se admite ningún otro, incluido `estado`. El nombre se guarda sin espacios exteriores y es único sin distinguir mayúsculas, también frente a los espacios inactivos. Errores: `datos_invalidos` (campo ausente, campo no admitido, nombre vacío o solo con espacios, o cuerpo que no es un objeto JSON), `tipo_espacio_invalido`, `capacidad_invalida` (cero, negativa, decimal, texto, `null` o cadena vacía) y `espacio_duplicado`.

### Editar un espacio

```http
PATCH /api/espacios/3
Authorization: Bearer <token>
Content-Type: application/json

{"capacidad": 35}
```

Respuesta 200: el espacio actualizado. Todos los campos son opcionales y solo se editan `nombre`, `tipo` y `capacidad`; los omitidos conservan su valor, el estado no cambia y un cuerpo vacío `{}` responde 200 sin cambios. Mantener el propio nombre, aunque cambien solo mayúsculas o espacios exteriores, no es un duplicado. Cualquier otro campo, incluido `estado`, responde `datos_invalidos` sin modificar nada: el estado se cambia con `desactivar`/`activar`. Errores: `datos_invalidos`, `tipo_espacio_invalido`, `capacidad_invalida`, `espacio_duplicado` y `espacio_no_encontrado`.

### Desactivar y reactivar un espacio

```http
POST /api/espacios/3/desactivar
Authorization: Bearer <token>
```

```http
POST /api/espacios/3/activar
Authorization: Bearer <token>
```

Respuesta 200: el espacio con `"estado": "inactivo"` o `"estado": "activo"`. El espacio conserva su nombre, tipo y capacidad, y el inactivo sigue apareciendo en las consultas; no existe eliminación física. Errores: `espacio_ya_inactivo` (desactivar un espacio inactivo), `espacio_ya_activo` (reactivar un espacio activo) y `espacio_no_encontrado`.

## Catálogo de códigos de error

Todas las respuestas de error tienen la forma:

```json
{"error": {"codigo": "permiso_insuficiente", "mensaje": "No tiene permiso para realizar esta operación."}}
```

El mensaje es un texto fijo del catálogo y nunca incluye datos de la petición ni detalle técnico.

| Código | HTTP | Se produce cuando |
|---|---|---|
| `credenciales_invalidas` | 401 | Login con correo inexistente o contraseña incorrecta |
| `usuario_desactivado` | 401 | Login o petición protegida de una cuenta desactivada |
| `token_ausente` | 401 | Petición protegida sin cabecera `Authorization` |
| `token_invalido` | 401 | Token malformado o firma inválida |
| `token_expirado` | 401 | Token con la fecha de expiración ya pasada |
| `permiso_insuficiente` | 403 | Operación no permitida al rol del usuario |
| `datos_invalidos` | 400 | Faltan campos obligatorios, formato inválido o cuerpo JSON mal formado |
| `contrasena_invalida` | 400 | Contraseña con menos de 8 caracteres |
| `rol_invalido` | 400 | Rol fuera del catálogo |
| `correo_duplicado` | 409 | Correo ya registrado |
| `usuario_no_encontrado` | 404 | Identificador de usuario inexistente |
| `operacion_no_permitida` | 409 | Desactivar la propia cuenta o cambiar el propio rol |
| `tipo_espacio_invalido` | 400 | Tipo de espacio fuera del catálogo (`laboratorio`, `auditorio`, `sala_de_computo`) |
| `capacidad_invalida` | 400 | Capacidad presente que no es un entero mayor que cero (máximo técnico 2147483647) |
| `espacio_duplicado` | 409 | Nombre ya usado por otro espacio, activo o inactivo, sin distinguir mayúsculas ni espacios exteriores |
| `espacio_no_encontrado` | 404 | Identificador de espacio inexistente |
| `espacio_ya_inactivo` | 409 | Desactivar un espacio que ya está inactivo |
| `espacio_ya_activo` | 409 | Reactivar un espacio que ya está activo |
| `ruta_no_encontrada` | 404 | Ruta inexistente |
| `metodo_no_permitido` | 405 | Método HTTP no permitido en la ruta |
| `error_interno` | 500 | Error interno no controlado |

Cuando una petición protegida no está autenticada se responde 401 antes de comprobar el permiso; con un token válido y un rol sin el permiso, 403 con `permiso_insuficiente`.

## Primer administrador: `flask create-admin`

Como solo el rol `admin` puede crear cuentas, la primera cuenta administradora se crea por consola (design.md, D9). El comando crea una cuenta activa con rol `admin` y nombre `Administrador` (editable después desde la API) únicamente si no existe ningún administrador activo; en cualquier otro caso falla con un mensaje explícito y no crea ninguna cuenta.

- **Correo**: opción `--correo` o, si no se indica, variable de entorno `ADMIN_CORREO`. La opción tiene prioridad sobre la variable. Se guarda en minúsculas.
- **Contraseña**: no existe ninguna opción de línea de comandos para la contraseña, porque quedaría en el historial del shell y en la lista de procesos. Se lee de la variable `ADMIN_CONTRASENA` o, si no está definida y el comando se ejecuta en una terminal interactiva, se pide de forma oculta con confirmación. Sin variable ni terminal interactiva, el comando falla. Debe tener al menos 8 caracteres, sin reglas de composición.

El comando falla, sin crear ninguna cuenta, cuando ya existe un administrador activo, cuando falta el correo o la contraseña, cuando la contraseña tiene menos de 8 caracteres, cuando el correo no tiene un formato válido o cuando ya está registrado. Ningún mensaje del comando muestra la contraseña ni el correo.

**Forma recomendada (prompt oculto)**, desde la raíz del repositorio y con `DATABASE_URL` y `JWT_SECRET_KEY` definidas en la terminal:

```
flask --app backend.app create-admin --correo <correo-del-administrador>
```

El comando pide la contraseña dos veces sin mostrarla en pantalla.

**Con variables de entorno** (por ejemplo, en un despliegue no interactivo): defina `ADMIN_CORREO` y `ADMIN_CONTRASENA` solo en la terminal o en el proceso que ejecuta el comando, y elimínelas al terminar. Nunca las escriba en archivos del repositorio (ni en un `.env`, ni en scripts, ni en la documentación) y nunca las imprima en logs.
