# Design

## Context

Primer incremento funcional del proyecto (etapa 3 de `PLAN_INGENIERIA.md`). El repositorio contiene hoy únicamente el plan de ingeniería y la configuración de OpenSpec: no existe código de aplicación, ni esquema de base de datos, ni infraestructura de pruebas. Este diseño debe fijar la estructura base que usarán los módulos posteriores (`espacios`, `reservas`, `aprobaciones`, `historial`) al construirse, sin tener que reescribirse.

Restricciones heredadas del plan que condicionan el diseño:

- Monolito modular en capas (`rutas` → `servicios` → `repositorios`), con las reglas de negocio en la capa de servicios.
- Flask + SQLAlchemy + Alembic + PostgreSQL; React en el frontend; `pytest` y `Vitest`.
- Las reglas se cambian en un solo lugar: la matriz de permisos debe ser un dato, no código disperso.
- Fechas en UTC. (Los rangos semiabiertos `[inicio, fin)` no aplican todavía: no hay reservas en este incremento.)
- JWT como mecanismo de autenticación frente a sesiones con cookie.

## Goals / Non-Goals

**Goals:**

- Dejar una estructura base reutilizable por los módulos posteriores, con la frontera de autorización ya resuelta.
- Que el control de permisos sea declarativo y verificable en un solo archivo.
- Que los errores de seguridad sean distinguibles por código, para que el frontend reaccione de forma distinta a "credenciales inválidas", "token expirado" y "sin permiso".
- Que toda regla de negocio de esta etapa tenga un escenario de aceptación y una prueba asociada, según la matriz de trazabilidad del plan.

**Non-Goals:**

- Cualquier lógica de espacios, reservas, aprobaciones o historial: aquí solo se define quién puede invocarla.
- Límite de duración máxima de una reserva (llegará como cambio separado en la etapa 8).
- Refresh tokens, lista de revocación, cierre de sesión en el servidor, autoregistro de usuarios, rate limiting y tabla de auditoría de usuarios: descartados por decisión del estudiante (ver *Decisiones* en `proposal.md`), no forman parte del sistema.
- Autodominio de contraseña por el usuario final y recuperación por correo.

## Decisions

### D1. La matriz de permisos es un dato declarativo en la capa de servicios

Los permisos se declaran como cadenas con espacio de nombres (`espacios:crear`, `aprobaciones:aprobar`, `usuarios:editar`) en un único módulo `app/auth/permissions.py`, que asocia a cada rol el conjunto de permisos que posee. Las rutas declaran qué permisos exigen mediante un guard reusable.

**Alternativa descartada:** decoradores por rol (`@solo_admin`). Rechazada porque cada permiso nuevo obligaría a tocar cada ruta y a mantener varias listas de decoradores equivalentes; con la tabla declarativa, añadir una capacidad es añadir una fila.

**Consecuencia:** la jerarquía se expresa en la propia tabla, no en el código de las rutas: `aprobador` hereda de `solicitante` y `admin` hereda de `aprobador`. Un permiso nuevo se añade en una sola fila y se propaga a los roles superiores por la herencia. Las restricciones que no dependen de la jerarquía, como la exclusión de las solicitudes propias en `aprobaciones:aprobar` y `aprobaciones:rechazar`, se declaran también en la tabla, para que el control de permisos no se disperse entre rutas y servicios.

### D2. Matriz de permisos por rol

Los roles forman una cadena de herencia: `admin` ⊇ `aprobador` ⊇ `solicitante`. La tabla siguiente muestra el permiso efectivo de cada rol y es la misma que declara la spec `auth`.

| Permiso | `solicitante` | `aprobador` | `admin` |
|---|---|---|---|
| `espacios:ver` | Sí | Sí | Sí |
| `espacios:crear` | No | Sí | Sí |
| `espacios:editar` | No | Sí | Sí |
| `espacios:desactivar` | No | Sí | Sí |
| `reservas:crear` | Sí | Sí | Sí |
| `reservas:ver_propias` | Sí | Sí | Sí |
| `reservas:cancelar_propia` | Sí | Sí | Sí |
| `reservas:ver_todas` | No | Sí | Sí |
| `aprobaciones:aprobar` | No | Sí | Sí |
| `aprobaciones:rechazar` | No | Sí | Sí |
| `historial:ver_propio` | Sí | Sí | Sí |
| `historial:ver_todos` | No | Sí | Sí |
| `usuarios:ver` | No | No | Sí |
| `usuarios:crear` | No | No | Sí |
| `usuarios:editar` | No | No | Sí |
| `usuarios:desactivar` | No | No | Sí |
| `usuarios:activar` | No | No | Sí |
| `usuarios:resetear_password` | No | No | Sí |
| `roles:ver` | No | No | Sí |

Correspondencia con el plan: el `solicitante` consulta disponibilidad, crea solicitudes, cancela las propias y ve su historial; el `aprobador` aprueba o rechaza y gestiona espacios; el `admin` gestiona usuarios, roles y permisos, y por jerarquía reúne además todo lo anterior. Los módulos que aún no existen consumirán esta tabla cuando se construyan; este incremento solo la aplica a las rutas de `usuarios`.

**Consecuencia aceptada:** `aprobaciones:aprobar` y `aprobaciones:rechazar` no se aplican a las solicitudes creadas por el propio usuario. Así, aunque el `admin` reúne los permisos de `solicitante` y `aprobador`, nadie se autoaprueba ni se autorechaza. El comportamiento de esas operaciones se detallará en el change `aprobacion-reservas`, que construirá el módulo correspondiente.

### D3. Modelo de datos

Dos tablas, siguiendo la nomenclatura de `PLAN_INGENIERIA.md` (sección 3.3):

- `roles`: `id` (PK), `nombre` (único, `solicitante` | `aprobador` | `admin`).
- `usuarios`: `id` (PK), `nombre`, `correo` (único), `password_hash`, `rol_id` (FK → `roles.id`, un único rol por usuario), `activo` (booleano), `creado_en`, `actualizado_en`.

Detalles de implementación:

- Índice único funcional `UNIQUE (lower(correo))` además de la normalización a minúsculas al escribir. La normalización sola deja fuera carreras (dos altas concurrentes con el mismo correo en mayúsculas); el índice único en la base de datos las resuelve.
- `creado_en` / `actualizado_en` son `TIMESTAMP WITH TIME ZONE` y se rellenan con `datetime.now(timezone.utc)`, por la restricción de fechas en UTC del plan.
- Los tres roles se insertan en una migración Alembic (datos de catálogo, no datos de negocio), de modo que el catálogo existe desde el primer despliegue y las claves foráneas nunca quedan sin destino.
- `password_hash` almacena el resultado de `generate_password_hash`, que ya incluye algoritmo, iteraciones y sal en el propio valor.

### D4. Autenticación: JWT HS256 con PyJWT, emitido en el backend

El backend emite el token en el login y lo verifica en cada petición protegida. Claims: **únicamente** `sub` (id de usuario), `iat` (fecha de emisión) y `exp` (fecha de expiración). El token no transporta el rol: el rol efectivo se lee siempre de la base de datos (ver D5). La clave es configuración (`JWT_SECRET_KEY`) y la vigencia (`JWT_ACCESS_TOKEN_MINUTES`) tiene un **valor por defecto de 60 minutos**; ambas se leen de variables de entorno y nunca se fijan en el código. No existe refresh token: el único token emitido es el de acceso.

**Alternativas descartadas:**

- *Sesiones con cookie*: el plan las descarta explícitamente al elegir JWT, y con un frontend React servido aparte complican el entorno local.
- *RS256 / pares de claves*: no hay consumidor externo ni necesidad de verificar tokens en otro servicio; la asimétrica solo añadiría gestión de claves.
- *`flask-jwt-extended`*: trae refresh tokens, blocklist y captura de errores que este incremento no usa, y oculta el flujo de emisión y verificación que el proyecto debe poder explicar y probar. PyJWT es explícito y suficiente.

### D5. El rol efectivo se lee de la base de datos, no del token

El token de acceso no transporta el rol: sus claims son solo el identificador del usuario, la fecha de emisión y la fecha de expiración. En cada petición protegida, la verificación carga el usuario y su rol vigente. Por eso un cambio de rol surta efecto en la petición siguiente sin obligar a reautenticarse, y una cuenta desactivada pierde el acceso de inmediato aunque su token no haya expirado.

**Alternativa descartada:** incluir el rol en el token (claim `rol`) y usarlo para autorizar. Se descarta porque un cambio de rol no se aplicaría hasta el siguiente login, lo que rompería el escenario "cambio de rol con token vigente" de la spec `auth`, y porque un rol desactualizado dentro del token ampliaría el alcance de un token robado.

**Consecuencia:** una consulta a la base de datos por petición protegida. Es aceptable en esta etapa y se mitiga con una única consulta que une usuario y rol (ver riesgos).

### D6. Hash de contraseñas con las utilidades de Flask

`werkzeug.security.generate_password_hash` / `check_password_hash` (PBKDF2 por defecto), sin dependencias nuevas de terceros.

**Alternativas descartadas:** bcrypt y argon2 requieren paquetes nativos o compilados, que complican el entorno local de demostración del plan sin aportar valor a un proyecto con contraseñas gestionadas por el administrador.

La política de contraseñas es: **mínimo de 8 caracteres y ninguna regla de composición** (no se exigen mayúsculas, dígitos ni símbolos). El valor vive en la configuración de la aplicación (`PASSWORD_MIN_LENGTH = 8`); cambiarlo exige actualizar la spec `usuarios` en el mismo cambio, porque el escenario de aceptación fija el número.

### D7. Contrato de errores de la API

Un único manejador de errores traduce excepciones de dominio a respuestas JSON. Formato: `{"error": {"codigo": "...", "mensaje": "..."}}`. Los códigos HTTP del contrato son 400, 401, 403, 404 y 409, y la capacidad `auth` los fija para todas las respuestas de error de la API.

| Código | HTTP | Se produce cuando |
|---|---|---|
| `credenciales_invalidas` | 401 | Login con correo inexistente o contraseña incorrecta (mensaje genérico en ambos casos) |
| `usuario_desactivado` | 401 | Login o petición protegida de una cuenta desactivada |
| `token_ausente` | 401 | Petición protegida sin cabecera `Authorization` |
| `token_invalido` | 401 | Token malformado o firma inválida |
| `token_expirado` | 401 | Token con `exp` ya pasado |
| `permiso_insuficiente` | 403 | Operación no permitida al rol del usuario |
| `datos_invalidos` | 400 | Faltan campos obligatorios o formato inválido |
| `contrasena_invalida` | 400 | Contraseña con menos de 8 caracteres |
| `rol_invalido` | 400 | Rol fuera del catálogo |
| `correo_duplicado` | 409 | Correo ya registrado |
| `usuario_no_encontrado` | 404 | Identificador de usuario inexistente |
| `operacion_no_permitida` | 409 | Autoadministración prohibida (desactivar la propia cuenta o cambiar su propio rol) |

El contrato de error de la API es único para todo el sistema: la capacidad `auth` declara la forma JSON del cuerpo y los códigos HTTP 400, 401, 403, 404 y 409, y la capacidad `usuarios` concreta el código de error propio de cada caso (por ejemplo `correo_duplicado` para el 409 de correo repetido y `usuario_no_encontrado` para el 404 de identificador inexistente).

El login con correo inexistente y con contraseña incorrecta devuelve el mismo código y el mismo mensaje, para no revelar qué correos existen. La única excepción es `usuario_desactivado`, que sí distingue el caso porque el usuario necesita saber que su cuenta está desactivada y no que falló su contraseña; se asume el riesgo de enumeración de cuentas, tolerable en un sistema institucional con alta controlada por el administrador.

**Protección del acceso administrativo.** Un `admin` no puede desactivarse ni cambiar su propio rol (`operacion_no_permitida`). Con esta regla el sistema siempre conserva al menos un administrador activo, porque el único administrador solo puede ser desactivado o degradado por sí mismo, y esa vía está bloqueada. Por eso no hace falta una comprobación adicional de "último administrador"; el servicio la conserva únicamente como aserción defensiva, sin código de error propio.

### D8. Endpoints

| Método y ruta | Permiso | Respuesta |
|---|---|---|
| `POST /api/auth/login` | Público | 200 `{token, tipo_token, expira_en, usuario}` |
| `GET /api/auth/me` | Autenticado | 200 con los datos del usuario autenticado |
| `GET /api/usuarios` | `usuarios:ver` | 200 con la lista de cuentas (incluye inactivas) |
| `POST /api/usuarios` | `usuarios:crear` | 201 con los datos de la cuenta creada |
| `GET /api/usuarios/{id}` | `usuarios:ver` | 200 con los datos de la cuenta |
| `PATCH /api/usuarios/{id}` | `usuarios:editar` | 200 con los datos actualizados |
| `POST /api/usuarios/{id}/password` | `usuarios:resetear_password` | 200 sin cuerpo de negocio |
| `POST /api/usuarios/{id}/desactivar` | `usuarios:desactivar` | 200 con el estado actualizado |
| `POST /api/usuarios/{id}/activar` | `usuarios:activar` | 200 con el estado actualizado |
| `GET /api/roles` | `roles:ver` | 200 con el catálogo de roles |

Las rutas declaran su permiso; el guard de la capa de servicios decide. Una ruta sin permiso declarado es un error de desarrollo y falla en las pruebas.

### D9. El primer administrador se crea por consola

Como solo el `admin` puede crear usuarios, hace falta un camino de arranque que no dependa de la aplicación web. Se implementa un comando de la CLI de Flask (`flask create-admin`) que crea la cuenta `admin` inicial leyendo correo y contraseña de argumentos o de variables de entorno, y que falla con mensaje explícito si ya existe un administrador activo. El comportamiento esperado está fijado en el requisito *Creación del primer administrador por línea de comandos* de la capacidad `usuarios`.

**Alternativa descartada:** variables de entorno que crean el admin en cada arranque. Se descarta porque oculta el efecto en el arranque, complica los entornos de prueba y no da control sobre el momento de la creación.

### D10. Estructura de carpetas

```
backend/
  app/
    __init__.py            # creación de la app, registro de blueprints y manejadores de error
    config.py              # configuración por entorno (JWT, BD, política de contraseña)
    extensions.py          # db, migraciones
    auth/
      routes.py  services.py  repositories.py
      permissions.py       # tabla de permisos por rol (D1)
      tokens.py            # emisión y verificación de JWT
      errors.py            # excepciones de dominio
    usuarios/
      routes.py  services.py  repositories.py
    models/
      usuario.py  rol.py
    commands.py            # flask create-admin
  migrations/
  tests/
frontend/
  src/
    api/                   # cliente HTTP con interceptor de 401/403
    features/auth/         # login, sesión, contexto de autenticación
    features/usuarios/     # administración de cuentas (solo admin)
```

El backend y el frontend se crean en este mismo incremento porque el plan exige incrementos verticales verificables (base de datos, API, interfaz y pruebas).

### D11. Estrategia de pruebas

Cada escenario de las specs `auth`, `usuarios` e `interfaz-web` tiene al menos una prueba, nombrada según el escenario, en `backend/tests/` con `pytest` contra la base PostgreSQL de pruebas `reservas_test` (URL en `TEST_DATABASE_URL`), siguiendo la sección 5.1 del plan. La base de desarrollo `reservas` es una base aparte, con su URL en `DATABASE_URL`, y las migraciones se ejecutan sobre ella con `alembic upgrade head`. El frontend se prueba con `Vitest` y React Testing Library para el flujo de login y para el almacenamiento y expiración del token.

### D12. La interfaz web se especifica por comportamiento observable

La capacidad `interfaz-web` describe lo que el usuario percibe, no cómo se dibuja: no fija colores, tipografías ni disposición, y ningún detalle de diseño visual entra en los escenarios. Sus requisitos se apoyan en los códigos de error de la API: la pantalla de login muestra el mensaje del servidor según el código recibido (`credenciales_invalidas`, `usuario_desactivado`, `datos_invalidos`), un 403 con `permiso_insuficiente` produce un mensaje sin cerrar la sesión, y un `token_expirado` devuelve al login. El control de permisos no se reimplementa en el frontend: la sección de administración de usuarios se oculta a los roles sin permiso porque el backend responde 403, y el token decide qué puede invocarse.

## Risks / Trade-offs

- **Una consulta a la base de datos por petición protegida** → Mitigación: una sola consulta que une usuario y rol por identificador, con índice en la clave primaria; el coste se revisa si el volumen real lo justifica.
- **Clave de firma JWT en el entorno** → Mitigación: se lee de variable de entorno, con un valor de desarrollo explícito en `.env.example` fuera del control de versiones; el arranque falla si en un entorno no local la clave es el valor por defecto.
- **Sin revocación de tokens emitidos antes de un cambio de rol** → Mitigación: el rol efectivo se lee de la base de datos (D5), así que el cambio surte efecto de inmediato; solo el alcance del token queda obsoleto, sin impacto en permisos.
- **La matriz declara permisos de módulos que todavía no existen** (`espacios`, `reservas`, `aprobaciones`, `historial`) → Mitigación: la tabla es declarativa y en este incremento solo la consumen las rutas de `usuarios`; cada módulo adopts la tabla al construirse y define en su propio change el comportamiento de sus permisos, incluida la exclusión de las solicitudes propias en `aprobaciones:aprobar` y `aprobaciones:rechazar`.
- **La reactivación de una cuenta revive tokens emitidos antes de la desactivación** → Mitigación: es una consecuencia coherente con JWT sin estado; si se considera inaceptable, se puede activar un cambio que limite la vigencia al estado de la cuenta.
- **Sin auditoría de cambios sobre cuentas** → Mitigación: decisión consciente del estudiante; el plan solo define `historial_reservas` y el rastro de cambios de usuario no se guarda en este incremento.
- **Contraseña administrada por el administrador** → Mitigación: la política mínima es de 8 caracteres sin reglas de composición y el frontend no expone el hash en ninguna respuesta.

## Migration Plan

1. Migración Alembic que crea `roles` e `usuarios` con su clave foránea, índices y columnas de marca temporal; en la misma migración se insertan los tres roles del catálogo.
2. Migración Alembic que añade el índice único funcional sobre `lower(correo)`.
3. Comando `flask create-admin` para crear la primera cuenta administradora.
4. Verificación: la suite de pruebas corre contra una base PostgreSQL efímera creada desde cero, de modo que el orden de migraciones queda cubierto.

**Rollback:** `alembic downgrade base` elimina las dos tablas. Como este incremento no introduce datos reales más allá del catálogo de roles y la cuenta inicial de administrador, no se requiere estrategia de migración de datos.

## Open Questions

Diferibles sin cambiar las specs, el enfoque ni el desglose de tareas:

- ¿Conviene cachear el catálogo de roles y el conjunto de permisos en memoria, invalidándolo cuando cambia un rol? Hoy no lo compensa el volumen, pero es el primer candidato si el número de peticiones crece.
- ¿Cómo se documentará la CLI `create-admin` en el `README.md` (etapa 9 del plan) y qué variables de entorno exigirá en un despliegue real?
