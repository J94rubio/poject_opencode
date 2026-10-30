# Design

## Context

Ver proposal.md - Why. El proyecto ya cuenta con estructura modular en capas (usuarios-roles-auth, espacios, reservas-disponibilidad, aprobacion-reservas) con auth/JWT, guard de permisos, manejador de errores, modelo de reservas con estados cerrados, restricción de exclusión sobre reservas aprobadas, función única `decidir` con transacción y bloqueo de fila, y reloj inyectable. Los errores siguen el formato `{"error": {"codigo", "mensaje"}}` de usuarios-roles-auth. El plan atribuye a `aprobaciones` el «registro de quién decidió y cuándo»; ese registro se implementa aquí, en el historial.

## Goals / Non-Goals

**Goals:**
- Cancelación de reservas propias con las reglas de la capacidad `cancelaciones`.
- Historial atómico e inmutable de todos los cambios de estado, con consulta por rol y filtros.
- Integrar el registro sin cambiar el comportamiento observable de la creación ni de la decisión.
- Comportamiento observable mínimo en `interfaz-web`.

**Non-Goals:**
- Cancelación de reservas ajenas o administrativa, de reservas ya iniciadas, y reactivación de canceladas.
- Paginación, exportación, historial por reserva como ruta propia e historial de usuarios o espacios.
- Notificaciones.

## Decisions

- **Tabla `historial_reservas`:** `id`, `reserva_id` (clave foránea a `reservas`), `espacio_id` (copia al momento del cambio, para filtrar sin unir), `estado_anterior` (nulo solo en la creación), `estado_nuevo`, `actor_id` (clave foránea a `usuarios`) y `fecha_utc` (`TIMESTAMP WITH TIME ZONE`, asignada por el servicio con el reloj inyectable). `CHECK` de ambos estados contra el catálogo y `CHECK` que exige `estado_anterior` nulo si y solo si `estado_nuevo = 'pendiente'`.
- **Inmutabilidad en la base de datos:** disparador `BEFORE UPDATE OR DELETE` sobre `historial_reservas` que lanza una excepción. Se verifica con pruebas de repositorio que ejecutan `UPDATE` y `DELETE` directos. La API no expone rutas de escritura, de modo que `POST`, `PUT`, `PATCH` y `DELETE` sobre `/api/historial` caen en el manejador de 405.
- **Atomicidad:** el registro se escribe en la misma transacción que el cambio de estado, con una única función `registrar(sesion, reserva, estado_anterior, estado_nuevo, actor)` llamada desde la creación, desde `decidir` y desde la cancelación. Si falla, la transacción completa se deshace.
- **Cancelación:** función `cancelar(solicitud_id, usuario)` en `backend/app/cancelaciones/services.py`, con la misma técnica de `decidir`: transacción, `SELECT ... FOR UPDATE` sobre la solicitud y validación del estado dentro de la transacción. Orden de comprobaciones: permiso (guard `reservas:cancelar_propia`), existencia (404), dueño (403), estado `pendiente` o `aprobada` (409 `transicion_invalida`), inicio posterior al momento actual (409 `reserva_iniciada`).
- **Cancelación y aprobación simultáneas:** ambas bloquean la misma fila, por lo que se serializan. Si la aprobación va primero, la cancelación después tiene éxito sobre una `aprobada`; si la cancelación va primero, la aprobación recibe `transicion_invalida`. En ambos casos el estado final es `cancelada`, y el historial refleja la secuencia real de transiciones.
- **Liberación del espacio:** no requiere lógica adicional: la restricción de exclusión y la disponibilidad solo consideran estado `aprobada`, por lo que cambiar a `cancelada` libera el rango.
- **Consulta del historial:** `GET /api/historial` con los permisos `historial:ver_todos` o `historial:ver_propio`. Para el solicitante, el repositorio añade siempre la condición de que la reserva le pertenezca, antes de aplicar los filtros. Los filtros presentes se combinan con Y lógico; `estado` filtra por estado nuevo; `desde` y `hasta` se exigen juntos, con zona horaria y `hasta` posterior a `desde`; un `espacio_id` inexistente responde 404 `espacio_no_encontrado`.
- **Código de error nuevo:** `reserva_iniciada` (409), registrado en el catálogo central con mensaje fijo. Se reutilizan los demás.
- **Rutas:** `POST /api/reservas/{id}/cancelar` devuelve la solicitud actualizada con el formato del detalle de `reservas`; `GET /api/historial` devuelve una lista de entradas.

## Risks / Trade-offs

- [Cambio de comportamiento en creación y decisión] → Las pruebas existentes de `reservas-disponibilidad` y `aprobacion-reservas` deben seguir en verde; el registro solo añade una escritura en la misma transacción.
- [Disparador de inmutabilidad frente a la limpieza de datos de pruebas] → Los tests deben limpiar con `TRUNCATE` o con recreación del esquema, no con `DELETE`; verificarlo al configurar los fixtures.
- [Rendimiento de las consultas del historial] → Índices por reserva, espacio y fecha; sin paginación porque el volumen del proyecto es pequeño (decisión explícita).
- [Pruebas de concurrencia inestables] → Reutilizar la utilidad con barrera y conexiones independientes de `aprobacion-reservas`, con aserciones sobre el resultado final.
- [Falta de historial para reservas creadas antes del cambio] → No aplica: el sistema aún no tiene datos en producción.

## Open Questions

Ninguna bloqueante. Las decisiones 5 (filtro de estado) y 6 (rango de fechas sobre la fecha del cambio) de proposal.md quedan pendientes de confirmación del estudiante, con el valor por defecto indicado allí.
