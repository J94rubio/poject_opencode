# Proposal

## Why

El sistema de reservas de espacios académicos reemplaza hoy los correos y hojas de cálculo por una fuente de verdad única, pero ningún módulo posterior (espacios, reservas, aprobaciones, historial) puede construirse sin saber **quién** actúa y **qué** puede hacer. `PLAN_INGENIERIA.md` (etapa 3, dependencia crítica `auth` → `espacios` → `reservas`) define que toda solicitud nace `pendiente` y requiere aprobación: esa regla solo es exigible si existe una identidad verificada, tres roles diferenciados y un control de permisos verificable. Esta propuesta formaliza ese primer incremento vertical.

## What Changes

- Se introduce la **autenticación con JWT**: emisión de token de acceso tras validar credenciales, verificación de firma y expiración en cada petición protegida, y consulta del usuario autenticado. El token contiene únicamente el identificador del usuario, la fecha de emisión y la fecha de expiración: el rol efectivo siempre se lee de la base de datos. La vigencia del token es de **60 minutos** y se puede ajustar por configuración.
- Se introduce el **registro y la administración de usuarios**: alta, edición de datos, asignación de rol, activación/desactivación de cuentas y restablecimiento de contraseña por parte del `admin`. Solo el `admin` crea cuentas: **no hay autoregistro**.
- Se define el **catálogo de tres roles** (`solicitante`, `aprobador`, `admin`) con **jerarquía**: cada rol incluye los permisos del rol inferior, de modo que `admin` ⊇ `aprobador` ⊇ `solicitante`. La jerarquía se materializa en una **matriz de permisos** que determina qué puede hacer cada rol sobre los módulos de espacios, reservas, aprobaciones e historial; en esa matriz, aprobar y rechazar excluyen las solicitudes propias del usuario.
- Se unifican las respuestas de error de la API: credenciales inválidas, token ausente/expirado/inválido, acceso sin permiso, datos inválidos, recurso inexistente y conflicto de unicidad producen respuestas **distintas, estables y verificables** (códigos HTTP 400, 401, 403, 404 y 409, con un código de error propio). El mismo formato cubre también los errores del framework: ruta inexistente, método no permitido, cuerpo JSON mal formado y error interno.
- Se especifica la **interfaz web por comportamiento observable**: pantalla de inicio de sesión con los mensajes del servidor, ciclo de vida de la sesión, tratamiento del error de permisos insuficientes, protección de rutas y pantallas de administración de usuarios.
- Se fija que un usuario **desactivado pierde el acceso de inmediato**, aunque su token siga sin expirar.
- La contraseña exige un **mínimo de 8 caracteres** y **ninguna regla de composición** adicional.

### Fuera de alcance

- **Límite de duración máxima de una reserva.** No se define en esta propuesta; llegará como un cambio separado (etapa 8 del plan).
- Notificaciones por correo, aplicación móvil, pagos e integración con sistemas académicos externos (fuera de alcance según el plan, sección 1.5).
- Cambio de contraseña por el propio usuario y recuperación de contraseña por correo.
- **Autoregistro de usuarios**, **refresh token**, lista de revocación de tokens, cierre de sesión en el servidor y **tabla de auditoría de usuarios**: descartados por decisión (ver *Decisiones*).
- Lógica de negocio de espacios, reservas, aprobaciones e historial: aquí solo se define **quién puede invocarla**.

## Capabilities

### New Capabilities

- `auth`: autenticación mediante token JWT (emisión, validación y expiración) y aplicación de la matriz jerárquica de permisos por rol que gobierna el acceso a espacios, reservas, aprobaciones e historial.
- `usuarios`: ciclo de vida de las cuentas de usuario (alta, edición, estado activo/inactivo, cambio de rol, restablecimiento de contraseña), catálogo de roles del sistema y creación del primer administrador por línea de comandos.
- `interfaz-web`: comportamiento observable de la interfaz web (pantalla de inicio de sesión, ciclo de vida de la sesión, mensajes de error por permisos insuficientes, protección de rutas y pantallas de administración de usuarios).

### Modified Capabilities

_(Ninguna. El proyecto aún no tiene specs publicadas: `openspec list --specs` no devuelve ninguna.)_

## Impact

- **Backend (Flask, nuevo):** módulos `auth` y `usuarios` siguiendo el monolito modular en capas del plan (`rutas` → `servicios` → `repositorios`), con el control de permisos en la capa de servicios para que la matriz se cambie en un solo lugar.
- **Base de datos (PostgreSQL):** migraciones Alembic que crean las tablas `usuarios` y `roles` con la relación `usuarios.rol_id` → `roles.id`, unicidad de correo y columna de estado de la cuenta. No se toca ninguna tabla de `espacios`, `reservas` ni `historial_reservas`.
- **Frontend (React):** pantalla de login, manejo de sesión y expiración del token, y pantallas de administración de usuarios accesibles solo para `admin`. Su comportamiento observable se especifica en la capacidad `interfaz-web`.
- **Dependencias:** generación de hash de contraseñas con las utilidades de hash de Werkzeug (incluidas con Flask) y sin dependencias nuevas de terceros; además, librería de JWT, SQLAlchemy/Alembic y `pytest`.
- **Contrato con el resto del sistema:** `espacios`, `reservas`, `aprobaciones` e `historial` consumirán la matriz de permisos definida en la capacidad `auth`; esos módulos todavía no existen, por lo que este cambio no altera su comportamiento.
- **Datos existentes:** ninguno. Es el primer incremento del proyecto y no hay migración de datos reales.

## Decisiones

Respuestas del estudiante a las ambigüedades detectadas al redactar esta propuesta. Quedan fijadas y se reflejan en `design.md` y en las specs `auth` y `usuarios`.

1. **Jerarquía de roles.** `admin` incluye todos los permisos de `aprobador`, y `aprobador` incluye todos los de `solicitante`. La jerarquía se expresa en la tabla de permisos; el `admin` es, en la práctica, un superusuario del sistema.
2. **Sin autoregistro.** Solo el `admin` crea cuentas de usuario.
3. **Vigencia del token.** 60 minutos, configurable por la aplicación.
4. **Sin refresh token.** Solo existe token de acceso; cerrar sesión consiste en descartarlo en el cliente y la revocación efectiva se logra desactivando la cuenta.
5. **Contraseña.** Mínimo de 8 caracteres, sin reglas de composición (no se exigen mayúsculas, dígitos ni símbolos).
6. **Un rol por usuario.** Cada usuario tiene exactamente un rol, coherente con un control de permisos "por rol".
7. **Autoadministración del `admin`.** Un `admin` no puede desactivarse ni cambiar su propio rol.
8. **Acceso por correo.** El login es por correo y es único sin distinguir mayúsculas y minúsculas, también entre cuentas desactivadas.
9. **Sin tabla de auditoría de usuarios.** Los cambios sobre cuentas no se registran en una tabla propia en este incremento.

**Consecuencia a vigilar:** la matriz deja fuera del alcance de `aprobaciones:aprobar` y `aprobaciones:rechazar` las solicitudes creadas por el propio usuario, de modo que, pese a la jerarquía, nadie se autoaprueba ni se autorechaza. La regla queda registrada en la capacidad `auth`; su comportamiento se detallará en el change `aprobacion-reservas`, que construirá ese módulo.
