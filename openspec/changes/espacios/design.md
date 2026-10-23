# Design

## Context

Segundo incremento vertical del proyecto (etapa 4 de `PLAN_INGENIERIA.md`). Se asume implementado el change `usuarios-roles-auth`: estructura del backend en capas, configuración por entorno, conexión a PostgreSQL y migraciones Alembic, manejador único de errores, guard de permisos, autenticación JWT, cliente HTTP del frontend con tratamiento de 401/403 y rutas protegidas. También se asume que la matriz de permisos de la capability `auth` incluye `espacios:ver`, `espacios:crear`, `espacios:editar`, `espacios:desactivar` y `espacios:activar` (los dos últimos para `aprobador` y `admin`).

Restricciones heredadas del plan que condicionan el diseño:

- Monolito modular en capas (`rutas` → `servicios` → `repositorios`) y reglas de negocio en la capa de servicios.
- Flask + SQLAlchemy + Alembic + PostgreSQL; React en el frontend; `pytest` y `Vitest`.
- Fechas en UTC. Los rangos semiabiertos `[inicio, fin)` no aplican en este incremento porque no hay reservas.
- Los permisos y el contrato de errores se consumen del change `usuarios-roles-auth`; la única incorporación es `espacios:activar` en su matriz, para esta funcionalidad.

El repositorio aún no contiene el código de los incrementos anteriores; este diseño describe la integración esperada con esa base y no repite sus tareas.

## Goals / Non-Goals

**Goals:**

- Que el catálogo de espacios sea la única fuente de verdad para nombre, tipo, capacidad y estado.
- Que las validaciones se apliquen en un solo lugar (capa de servicios) y que la base de datos impida estados inválidos incluso ante concurrencia.
- Reutilizar el guard de permisos, el manejador de errores y el cliente HTTP ya existentes, sin introducir una segunda forma de autorizar ni de responder errores.
- Dejar el catálogo listo para que `reservas-disponibilidad` lo consuma sin cambios de esquema.

**Non-Goals:**

- Rechazo de solicitudes sobre espacios inactivos: pertenece a `reservas-disponibilidad`.
- Reservas, disponibilidad, solapamientos, aprobaciones e historial.
- Eliminación física de espacios, paginación, búsqueda, filtros y ordenamiento configurable.
- Detalles de diseño visual de las pantallas; la capability `interfaz-web` solo fija comportamiento observable.
- Un límite máximo de longitud del nombre: ni el plan ni el pedido lo definen, así que la columna es `TEXT` y no se impone esa regla.

## Decisiones

### D1. Módulo `espacios` con la misma estructura en capas

Se añade `backend/app/espacios/` con `routes.py`, `services.py` y `repositories.py`, y el modelo en `backend/app/models/espacio.py`. Las rutas declaran el permiso requerido con el guard existente; los servicios aplican validaciones y transiciones de estado; los repositorios encapsulan las consultas. No se crea un segundo mecanismo de autorización ni se comprueban roles a mano.

**Alternativa descartada:** un módulo genérico de "recursos" parametrizable. Se descarta porque el plan organiza el monolito por módulos de negocio (`espacios`, `reservas`, `aprobaciones`, `historial`) y un módulo genérico dispersaría las reglas de espacios fuera de su módulo.

### D2. Modelo de datos: tabla `espacios`

| Columna | Tipo | Restricción |
|---|---|---|
| `id` | entero | PK, autoincremental |
| `nombre` | `TEXT` | `NOT NULL`, no vacío después de `btrim` (validado en servicio) |
| `tipo` | `TEXT` | `NOT NULL`, `CHECK (tipo IN ('laboratorio','auditorio','sala_de_computo'))` |
| `capacidad` | entero | `NOT NULL`, `CHECK (capacidad > 0)` |
| `estado` | `TEXT` | `NOT NULL DEFAULT 'activo'`, `CHECK (estado IN ('activo','inactivo'))` |
| `creado_en` | `TIMESTAMPTZ` | `NOT NULL`, valor UTC |
| `actualizado_en` | `TIMESTAMPTZ` | `NOT NULL`, valor UTC |

Índice único funcional: `CREATE UNIQUE INDEX ux_espacios_nombre ON espacios (lower(btrim(nombre)))`. El servicio elimina los espacios exteriores del nombre antes de escribir, y el índice resuelve la carrera entre dos altas concurrentes con el mismo nombre.

**Alternativas descartadas:**

- *Columna booleana `activo` como en `usuarios`*: obligaría a traducir en cada respuesta y no aporta ventaja; el estado textual `activo`/`inactivo` es el que expone la spec y el `CHECK` ya impide valores fuera del catálogo.
- *Extensión `citext`*: añade una dependencia de base de datos para un único campo; el índice funcional sobre `lower(btrim(nombre))` consigue lo mismo sin extensión.
- *Validación de unicidad solo en el servicio*: es vulnerable a dos altas concurrentes; el índice único es la garantía y el servicio lo traduce a `espacio_duplicado`.
- *Longitud máxima del nombre*: no está definida en el plan; imponerla sería inventar una regla. `TEXT` no la limita.

Los tiempos se guardan en UTC con `datetime.now(timezone.utc)`, conforme a la sección 3.3 del plan, aunque la API no los expone en este incremento.

### D3. Las transiciones de estado ocurren solo por desactivación y reactivación

El alta crea el espacio en `activo`. `PATCH /api/espacios/{id}` acepta únicamente `nombre`, `tipo` y `capacidad`; si la petición incluye `estado`, responde 400 con `datos_invalidos` y no modifica nada. Los únicos cambios de estado son `POST /api/espacios/{id}/desactivar` (`activo` → `inactivo`) y `POST /api/espacios/{id}/activar` (`inactivo` → `activo`). No hay `DELETE`.

Consecuencia: un espacio inactivo se conserva y sigue apareciendo en las consultas, como exige la spec. La desactivación repetida responde 409 con `espacio_ya_inactivo` y la reactivación repetida 409 con `espacio_ya_activo`, en lugar de ser idempotentes, para que el cliente distinga el cambio efectivo de un conflicto de estado.

**Alternativa descartada:** hacer idempotentes la desactivación y la reactivación (200 siempre). Se descarta porque ocultaría un conflicto de estado que el contrato de errores permite expresar con 409, y el pedido exige casos de error verificables.

### D4. Validaciones en la capa de servicios

El servicio de espacios valida, en este orden:

1. En el alta, cada campo obligatorio debe estar presente: `nombre`, `tipo` y `capacidad` → `datos_invalidos` (400). Un campo presente con valor `null` se valida según su tipo y no se trata como ausente.
2. `nombre` no vacío después de normalizar → `datos_invalidos` (400).
3. `tipo` dentro del catálogo cerrado → `tipo_espacio_invalido` (400).
4. `capacidad` de tipo entero (se rechaza `bool`, aunque en Python sea subtipo de `int`) y mayor que cero → `capacidad_invalida` (400). Un valor `null`, decimal, texto o cadena vacía también produce `capacidad_invalida` cuando el campo está presente.
5. Unicidad del nombre contra cualquier espacio, activo o inactivo → `espacio_duplicado` (409); la violación del índice único también se traduce a ese código.

En la edición parcial, cada campo presente se valida con la misma regla y los ausentes se conservan. Un `nombre` vacío produce `datos_invalidos`, y si la petición incluye el campo `estado` se rechaza con `datos_invalidos` (400) sin cambiar el registro. La comprobación de unicidad excluye el propio registro, de modo que editar solo mayúsculas o espacios exteriores del mismo nombre no se considera duplicado.

**Alternativa descartada:** validar en las rutas. Se descarta porque las reglas deben vivir en un solo lugar (sección 3.1 del plan) y porque las pruebas unitarias del servicio deben cubrir todos los casos sin pasar por HTTP.

### D5. Extensión del catálogo de errores sin cambiar el contrato

Se reutiliza el manejador de errores y las excepciones de dominio del change `usuarios-roles-auth`. Se registran estos códigos nuevos en el catálogo central, con el formato `{"error": {"codigo", "mensaje"}}` y los HTTP 400, 401, 403, 404 y 409 ya definidos:

| Código | HTTP | Se produce cuando |
|---|---|---|
| `datos_invalidos` | 400 | Faltan campos obligatorios en el alta, el nombre está vacío, la edición incluye `estado` o la petición no tiene forma válida |
| `tipo_espacio_invalido` | 400 | El tipo no pertenece al catálogo cerrado |
| `capacidad_invalida` | 400 | La capacidad está presente pero no es un entero mayor que cero |
| `espacio_duplicado` | 409 | El nombre ya pertenece a otro espacio, incluidos los inactivos |
| `espacio_no_encontrado` | 404 | El identificador no corresponde a ningún espacio |
| `espacio_ya_inactivo` | 409 | Se intenta desactivar un espacio que ya está inactivo |
| `espacio_ya_activo` | 409 | Se intenta reactivar un espacio que ya está activo |

Los códigos de autenticación y autorización (`token_ausente`, `token_invalido`, `token_expirado`, `usuario_desactivado`, `permiso_insuficiente`) son los del change anterior y no se redefinen. Los mensajes son textos fijos del catálogo y no repiten los valores enviados por el cliente.

### D6. Endpoints

| Método y ruta | Permiso | Respuesta |
|---|---|---|
| `GET /api/espacios` | `espacios:ver` | 200 con la lista completa, incluidos los inactivos |
| `GET /api/espacios/{id}` | `espacios:ver` | 200 con el espacio; 404 `espacio_no_encontrado` |
| `POST /api/espacios` | `espacios:crear` | 201 con el espacio creado en estado `activo` |
| `PATCH /api/espacios/{id}` | `espacios:editar` | 200 con el espacio actualizado; 400/404/409 |
| `POST /api/espacios/{id}/desactivar` | `espacios:desactivar` | 200 con el espacio en estado `inactivo`; 404/409 |
| `POST /api/espacios/{id}/activar` | `espacios:activar` | 200 con el espacio en estado `activo`; 404/409 |

Cada espacio se representa con exactamente `id`, `nombre`, `tipo`, `capacidad` y `estado`; no se exponen marcas de tiempo ni datos internos. El listado no pagina ni filtra en este incremento.

**Alternativa descartada:** `PUT` para la edición completa. Se descarta para mantener la coherencia con `PATCH /api/usuarios/{id}` del change anterior y permitir actualizaciones parciales sin exigir todos los campos.

### D7. Reutilización del frontend existente

Se añade `frontend/src/features/espacios/` y se reutilizan el cliente HTTP con token, el tratamiento de `token_expirado` (vuelta al login) y de `permiso_insuficiente` (mensaje sin cerrar sesión) y la protección de rutas ya implementados. Las acciones de alta, edición, desactivación y reactivación se ofrecen solo a sesiones con rol `aprobador` o `admin`; el backend sigue siendo la fuente de verdad y un 403 se muestra como error. No se reimplementa la matriz de permisos en el frontend.

La interfaz refleja el resultado de cada operación recargando o actualizando el catálogo con la respuesta del servidor, de modo que los estados mostrados siempre provienen de la API. La spec `interfaz-web` no fija componentes, estilos ni disposición.

**Alternativa descartada:** calcular la visibilidad de acciones consultando la matriz de permisos en el cliente. Se descarta porque duplicaría la matriz y podría desincronizarse; el rol de la sesión basta para ocultar acciones y el backend valida cada petición.

### D8. Estrategia de pruebas

- **Unitarias (pytest):** validaciones del servicio para nombre, tipo, capacidad, duplicados, edición parcial y transiciones de estado.
- **Integración (pytest + PostgreSQL de pruebas `reservas_test`):** cada escenario de las specs `espacios` e `interfaz-web` con al menos una prueba nombrada según el escenario, siguiendo la sección 5.1 del plan. Se incluye una prueba que inserta dos nombres equivalentes de forma directa para comprobar el índice único.
- **Frontend (Vitest + React Testing Library):** catálogo con activos e inactivos, alta y edición correctas, activación y desactivación correctas, mensajes de error del servidor y ocultamiento de acciones al `solicitante`.
- **Trazabilidad:** cada requisito de las specs queda enlazado a su escenario y a su prueba, como exige la sección 5.3 del plan.

### D9. Relación con los módulos posteriores

El change `reservas-disponibilidad` consumirá el catálogo de espacios; su comportamiento se define en ese change y no se especifica aquí. No se crea clave foránea en este change porque la tabla `reservas` todavía no existe; la relación se introducirá en la migración del change de reservas.

### D10. Desactivar un espacio no modifica las reservas existentes

La desactivación procede, deja el espacio en estado `inactivo` y no modifica ni cancela las reservas ya existentes. Solo impide nuevas solicitudes sobre ese espacio, regla que se especifica en el change `reservas-disponibilidad`; este change no ejecuta ninguna acción sobre reservas. Se conserva el registro y sus datos para no romper el historial.

**Alternativa descartada:** cancelar o rechazar automáticamente las reservas existentes al desactivar. Se descarta porque modificaría datos de un módulo que este change no posee y porque la regla de rechazo pertenece a `reservas-disponibilidad`.

## Risks / Trade-offs

- **Dos altas concurrentes con el mismo nombre** → Mitigación: índice único funcional en la base de datos; el servicio traduce la violación a `espacio_duplicado` sin dejar registros parciales.
- **JSON con tipos inesperados (por ejemplo `true` como capacidad, `10.5`, `null` o `""`)** → Mitigación: validación explícita de tipo entero en el servicio y `CHECK (capacidad > 0)` en la base de datos.
- **El catálogo crece sin paginación** → Mitigación: el plan no exige paginación y el volumen institucional es acotado; si crece, se añade como cambio posterior sin alterar el contrato actual.
- **Reactivar un espacio lo vuelve a habilitar para nuevas solicitudes** → Mitigación: la reactivación solo cambia el estado y conserva los datos; el efecto sobre solicitudes se define en `reservas-disponibilidad`.
- **Editar tipo o capacidad de un espacio con reservas futuras** → Mitigación: este incremento no recalcula reservas; la decisión de permitir la edición sin recalcular las reservas existentes está registrada en `proposal.md`.
- **La interfaz oculta acciones por rol y podría desincronizarse de la matriz** → Mitigación: el backend valida siempre con el guard; la interfaz solo oculta y muestra el 403 como error.
- **Crecimiento del catálogo de errores** → Mitigación: los códigos nuevos se registran en el catálogo central del manejador existente, sin manejadores paralelos.
- **Suposición de que los incrementos anteriores están implementados** → Mitigación: las tareas de este change verifican explícitamente la disponibilidad del guard, del manejador de errores y del cliente HTTP antes de usarlos; no se reimplementan.

## Migration Plan

1. Migración Alembic que crea la tabla `espacios` con sus `CHECK`, marcas de tiempo y el índice único funcional sobre `lower(btrim(nombre))`.
2. Sin migración de datos: no hay espacios previos.
3. Despliegue: ejecutar `alembic upgrade head` antes de arrancar la API; después se despliega el frontend. Los endpoints son nuevos y no rompen contratos existentes.
4. **Rollback:** `alembic downgrade -1` elimina la tabla `espacios` y su índice. Al no existir dependencias de otras tablas en este incremento, el rollback no requiere limpieza adicional.

## Open Questions

Diferibles sin cambiar las specs, el enfoque ni el desglose de tareas:

- ¿Se expondrán `creado_en` y `actualizado_en` en la API cuando el módulo de historial los necesite, o se consultarán solo desde la base de datos?
- ¿Se añadirán búsqueda, filtros por tipo y paginación al listado en un cambio posterior?
