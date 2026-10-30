# Proposal

## Why

Con la creación y la aprobación implementadas, faltan dos piezas del plan: que el solicitante pueda cancelar sus propias reservas (liberando el espacio cuando estaban aprobadas) y que cada cambio de estado quede registrado con su actor y su fecha, sin posibilidad de editarlo ni borrarlo. El plan atribuye el «registro de quién decidió y cuándo» al historial. Este change formaliza el quinto y último incremento funcional del sistema.

## What Changes

- Nueva capacidad `cancelaciones`: el solicitante dueño cancela sus reservas en estado `pendiente` o `aprobada` cuyo inicio aún no ha ocurrido. Cancelar una reserva aprobada libera el espacio.
- **Solo el dueño cancela:** no existe la cancelación de reservas ajenas, ni siquiera para admin.
- Nueva capacidad `historial`: cada cambio de estado (creación, aprobación, rechazo, cancelación) se registra con estado anterior, estado nuevo, actor y fecha en UTC. El registro se escribe en la misma transacción que el cambio de estado.
- **Inmutabilidad:** el historial no se edita ni se borra, ni por la API (no existen rutas de escritura) ni desde la base de datos (un disparador rechaza `UPDATE` y `DELETE`).
- **Consulta del historial** con filtros por espacio, estado y rango de fechas: aprobador y admin consultan todo; el solicitante solo el de sus propias reservas.
- Se integra el registro en la creación de `reservas-disponibilidad` y en la función única de decisión de `aprobacion-reservas`, sin cambiar su comportamiento observable.
- Se añaden a `interfaz-web` **dos requisitos nuevos** (ADDED): cancelación y consulta del historial.

### Fuera de alcance

- Cancelación de reservas ajenas o cancelación administrativa.
- Cancelación de reservas que ya comenzaron o terminaron.
- Historial por reserva individual como ruta propia, exportación y paginación.
- Historial de cambios de usuarios o de espacios (decisión del plan: el historial exigido es el de reservas).
- Reactivar una reserva cancelada.
- Notificaciones.

## Capabilities

### New Capabilities

- `cancelaciones`: cancelación de reservas propias, condiciones de estado e inicio, liberación del espacio, control de acceso y cancelaciones simultáneas.
- `historial`: registro de cada cambio de estado, inmutabilidad, consulta según rol y filtros.
- `interfaz-web`: el change reutiliza esta capability, aún no publicada en `openspec/specs/`. Se añaden solo requisitos ADDED, con nombres distintos de los ya propuestos.

### Modified Capabilities

_(Ninguna. El proyecto no tiene specs publicadas, por lo que todo se expresa con requisitos ADDED.)_

## Impact

- **Backend (Flask, monolito modular en capas):** nuevos módulos `cancelaciones` e `historial`; el registro del historial se integra en la creación (`reservas`) y en `decidir` (`aprobaciones`).
- **Base de datos (PostgreSQL):** migración con la tabla `historial_reservas` (clave foránea a `reservas` y a `usuarios`, `CHECK` de estados contra el catálogo, `estado_anterior` nulo solo en la creación), índices por reserva, espacio y fecha, y el disparador que impide `UPDATE` y `DELETE`.
- **API:** `POST /api/reservas/{id}/cancelar` y `GET /api/historial` con los filtros `espacio_id`, `estado`, `desde` y `hasta`.
- **Permisos:** se usan `reservas:cancelar_propia`, `historial:ver_propio` e `historial:ver_todos` de la matriz de `usuarios-roles-auth`. No se crean permisos nuevos.
- **Errores:** código nuevo `reserva_iniciada` (409); se reutilizan `transicion_invalida`, `permiso_insuficiente`, `solicitud_no_encontrada`, `datos_invalidos`, `espacio_no_encontrado` y `metodo_no_permitido`.
- **Frontend (React):** acción de cancelar en el listado de solicitudes y pantalla de historial con filtros.
- **Dependencias:** ninguna nueva.
- **Datos existentes:** ninguno.

## Decisiones

1. **Inicio ya ocurrido:** una reserva se puede cancelar solo si su inicio es posterior al momento actual; si el inicio es igual o anterior, responde 409 `reserva_iniciada`. Se compara contra el reloj inyectable.
2. **Cancelación de reservas ajenas:** 403 `permiso_insuficiente` para cualquier rol, incluido admin, porque el permiso es `reservas:cancelar_propia`.
3. **Orden de comprobaciones al cancelar:** permiso, existencia, dueño, estado (`pendiente` o `aprobada`) e inicio no ocurrido.
4. **Contenido de cada entrada del historial:** reserva, espacio, estado anterior (nulo en la creación), estado nuevo, actor y fecha en UTC. El motivo del rechazo sigue en la reserva y no se duplica.
5. **Filtro de estado:** coincide con el estado nuevo de la entrada. **Decisión pendiente de confirmar por el estudiante.**
6. **Filtro de rango de fechas:** se aplica a la fecha del cambio, con rango semiabierto `[desde, hasta)`, ISO 8601 con zona horaria explícita. **Decisión pendiente de confirmar por el estudiante.**
7. **Orden del historial:** ascendente por fecha del cambio y luego por identificador; sin paginación.
8. **Visibilidad del solicitante:** ve todas las entradas de sus reservas, incluidas las decisiones tomadas por un aprobador.
9. **Atomicidad:** si no se puede escribir la entrada del historial, el cambio de estado o la creación no se aplican.
10. **Filtro por espacio inexistente:** 404 `espacio_no_encontrado`, como en la consulta de disponibilidad.
