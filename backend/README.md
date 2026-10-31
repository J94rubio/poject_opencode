# Backend: sistema de reservas de espacios académicos

API REST en Flask. Este documento describe los endpoints del módulo `usuarios` y el catálogo de códigos de error de la API (design.md, D7 y D8, del change `usuarios-roles-auth`).

Todas las rutas del módulo `usuarios` son protegidas: exigen la cabecera `Authorization: Bearer <token>` con un token obtenido en `POST /api/auth/login`, y el permiso indicado en la tabla. Los permisos de gestión de usuarios y de consulta de roles los tiene únicamente el rol `admin`.

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
| `ruta_no_encontrada` | 404 | Ruta inexistente |
| `metodo_no_permitido` | 405 | Método HTTP no permitido en la ruta |
| `error_interno` | 500 | Error interno no controlado |

Cuando una petición protegida no está autenticada se responde 401 antes de comprobar el permiso; con un token válido y un rol sin el permiso, 403 con `permiso_insuficiente`.
