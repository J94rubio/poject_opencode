# Proposal

## Why

`PLAN_INGENIERIA.md` fija la gestión de espacios como etapa 4 y como requisito previo de reservas (dependencia `auth` → `espacios` → `reservas`): sin un catálogo confiable de laboratorios, auditorios y salas de cómputo no hay objeto que reservar ni disponibilidad que consultar. Hoy esa información vive en correos y hojas de cálculo, sin una fuente de verdad única ni control de quién puede modificarla. Este change formaliza el segundo incremento vertical del sistema.

## What Changes

- Se introduce el **catálogo de espacios académicos** con `nombre`, `tipo` (catálogo cerrado de tres valores: `laboratorio`, `auditorio`, `sala_de_computo`), `capacidad` (entero mayor que cero) y `estado` (`activo` o `inactivo`).
- Se habilita el **alta, la edición, la desactivación y la reactivación** de espacios para los roles `aprobador` y `admin`, según los permisos `espacios:crear`, `espacios:editar`, `espacios:desactivar` y `espacios:activar` de la matriz de la capability `auth`. El permiso `espacios:activar` se incorpora a esa matriz para `aprobador` y `admin`; los permisos existentes no cambian.
- Se habilita la **consulta** de espacios para todos los roles autenticados (`espacios:ver`), tanto en listado como en detalle. Los espacios inactivos se conservan y se devuelven identificados como inactivos.
- Se fijan **validaciones verificables**: nombre obligatorio y único, tipo dentro del catálogo cerrado, capacidad entera positiva y presencia de los campos obligatorios.
- La **edición es parcial**: los campos omitidos en la petición conservan su valor, los enviados se validan (tipo, capacidad, nombre no vacío y unicidad) y la edición no acepta cambios de estado.
- Se reutiliza el **contrato de errores** del change `usuarios-roles-auth`: cuerpo JSON `{"error": {"codigo", "mensaje"}}`, códigos HTTP 400, 401, 403, 404 y 409, y un código específico en snake_case para cada caso de este módulo (`datos_invalidos`, `tipo_espacio_invalido`, `capacidad_invalida`, `espacio_duplicado`, `espacio_no_encontrado`, `espacio_ya_inactivo` y `espacio_ya_activo`).
- Se añaden a la capability `interfaz-web` **tres requisitos nuevos** (ADDED) con el comportamiento observable de las pantallas de espacios: consulta del catálogo, alta y edición con mensajes del servidor, y activación y desactivación con reflejo del estado.

### Fuera de alcance

- **Rechazo de solicitudes sobre espacios inactivos**: se especifica en el change `reservas-disponibilidad`, no aquí.
- Reservas, disponibilidad, solapamientos, aprobaciones, cancelación e historial.
- **Límite de duración máxima de una reserva**: llegará como cambio separado (etapa 8 del plan).
- Eliminación física de espacios, inventario de equipos dentro de los espacios, notificaciones y soporte multi-sede (fuera de alcance del plan, sección 1.5).
- Paginación, búsqueda y filtros del listado: ni el plan ni el pedido los definen; el listado devuelve el catálogo completo.

## Capabilities

### New Capabilities

- `espacios`: catálogo de espacios académicos (laboratorios, auditorios y salas de cómputo) con su alta, consulta, edición, desactivación y reactivación, sus validaciones y el control de acceso por rol.
- `interfaz-web`: el change reutiliza esta capability, que aún no está publicada en `openspec/specs/` porque el change `usuarios-roles-auth` sigue en curso. Se añaden **solo requisitos ADDED** con nombres distintos de los ya propuestos, dedicados a las pantallas de espacios.

### Modified Capabilities

_(Ninguna. El proyecto no tiene specs publicadas: `openspec/specs/` solo contiene `.gitkeep`. Por eso todo se expresa con requisitos ADDED y no se usa MODIFIED, que exigiría una spec principal existente.)_

## Impact

- **Backend (Flask, monolito modular en capas):** nuevo módulo `espacios` con `routes.py`, `services.py` y `repositories.py`, siguiendo la estructura creada por `usuarios-roles-auth`. Las reglas de validación viven en la capa de servicios y las rutas declaran sus permisos con el guard existente.
- **Base de datos (PostgreSQL):** migración Alembic que crea la tabla `espacios` con restricciones de tipo, capacidad y unicidad de nombre, y marcas de tiempo en UTC. No se tocan las tablas `roles`, `usuarios`, `reservas` ni `historial_reservas`.
- **Frontend (React):** nuevas pantallas de consulta, alta, edición, desactivación y reactivación de espacios, reutilizando el cliente HTTP, el manejo de 401/403 y la protección de rutas del change anterior. Su comportamiento observable se especifica en `interfaz-web`.
- **Dependencias:** ninguna nueva. Se reutilizan Flask, SQLAlchemy, Alembic, PostgreSQL, el manejador de errores, el guard de permisos y las utilidades de pruebas ya definidos.
- **Contrato con el resto del sistema:** los changes `reservas-disponibilidad`, `aprobacion-reservas` e `cancelacion-historial` consumirán el catálogo de espacios y sus estados; este change no especifica su comportamiento. La tabla `espacios` no tiene relación con `reservas` en este incremento porque esa tabla aún no existe.
- **Datos existentes:** ninguno. Es un incremento nuevo y no requiere migración de datos.

## Decisiones

1. **Desactivar un espacio con reservas futuras no afecta las reservas existentes.** La desactivación procede y el espacio queda `inactivo`; las reservas ya existentes no se modifican ni se cancelan. La desactivación solo impide nuevas solicitudes sobre ese espacio, regla que se especifica en el change `reservas-disponibilidad`. Este change no define ni ejecuta ninguna acción sobre reservas.
2. **Unicidad del nombre.** El nombre es único sin distinguir mayúsculas, minúsculas ni espacios exteriores. Se normaliza con `trim` y se compara sin distinguir mayúsculas de minúsculas, incluidos los espacios inactivos.
3. **Estado inicial del espacio.** Todo espacio nuevo nace `activo`; el alta lo crea en estado `activo`.
4. **Catálogo de tipos.** Los valores exactos son `laboratorio`, `auditorio` y `sala_de_computo`, en minúsculas y sin acentos, como identificadores estables de API.
5. **Edición con reservas futuras.** Se pueden editar el tipo y la capacidad de un espacio que ya tiene reservas futuras: la edición se permite y las reservas existentes no se recalculan.
6. **Desactivación de un espacio ya inactivo.** Desactivar un espacio ya inactivo responde 409 con `espacio_ya_inactivo`, coherente con los conflictos de estado del contrato existente.
