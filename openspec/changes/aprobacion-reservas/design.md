# Design

## Context

Ver proposal.md - Why. El proyecto ya cuenta con estructura modular en capas (usuarios-roles-auth, espacios, reservas-disponibilidad) con auth/JWT, guard de permisos, manejador de errores, catálogo de espacios, modelo de reservas con estados cerrados y restricción de exclusión sobre reservas aprobadas. Las decisiones fijas del proyecto se mantienen (Flask + PostgreSQL + React, monolito modular en capas, roles solicitante/aprobador/admin con jerarquía, solo las reservas aprobadas ocupan un espacio, fechas en UTC, rangos semiabiertos `[inicio, fin)`). Los errores siguen el formato `{"error": {"codigo", "mensaje"}}` definido en usuarios-roles-auth.

## Goals / Non-Goals

**Goals:**
- Aprobar y rechazar solicitudes pendientes con las reglas de la capacidad `aprobaciones`.
- Garantizar que decisiones concurrentes nunca produzcan reservas aprobadas solapadas ni dos decisiones sobre la misma solicitud.
- Que toda decisión pase por una única función de servicio, para que `cancelacion-historial` pueda registrarla después sin reescribirla.
- Comportamiento observable mínimo de las acciones de decisión en `interfaz-web`.

**Non-Goals:**
- Cancelación de reservas e historial de cambios de estado (incluido quién decidió y cuándo).
- Rechazo automático de pendientes solapadas.
- Decisiones en lote, reversión de decisiones, edición del motivo y notificaciones.

## Decisions

- **Una única función de decisión:** `decidir(solicitud_id, usuario, accion, motivo)` en `backend/app/aprobaciones/services.py`, usada por ambas rutas. Es el único punto donde cambia el estado, lo que permite que el historial se añada después en un solo sitio.
- **Transacción con bloqueo de fila:** la decisión abre una transacción, lee la solicitud con `SELECT ... FOR UPDATE` y valida el estado dentro de esa misma transacción. Así, dos decisiones sobre la misma solicitud se serializan y la segunda ve el estado ya cambiado (`transicion_invalida`).
- **Aprobaciones solapadas:** el servicio comprueba el solapamiento antes de actualizar para dar el error amigable (`reserva_solapada`). Ante una carrera entre dos solicitudes distintas, la comprobación puede pasar en ambas; la restricción `EXCLUDE` de PostgreSQL hace fallar la segunda actualización, y el servicio traduce esa violación a 409 `reserva_solapada` y deshace la transacción.
- **Orden de comprobaciones al aprobar:** permiso (guard) → existencia (404) → autoría (403) → estado `pendiente` (409 `transicion_invalida`) → vigencia (409 `solicitud_vencida`) → espacio activo (400 `espacio_inactivo`) → solapamiento (409 `reserva_solapada`). Al rechazar: permiso → existencia → autoría → motivo (400) → estado.
- **Vigencia:** una solicitud ya comenzó cuando su inicio es anterior o igual al momento actual (mismo criterio que la cancelación en `cancelacion-historial`); se compara con el reloj inyectable del servicio de `reservas-disponibilidad`; las pruebas no dependen de la fecha real.
- **Motivo del rechazo:** columna `motivo_rechazo` (texto, nula salvo en rechazadas) y `CHECK` que exige motivo cuando el estado es `rechazada`. Se recorta y se valida (no vacío, hasta 500 caracteres) en el servicio.
- **Autoría:** se compara el usuario autenticado con el solicitante de la solicitud. La regla aplica a todos los roles, incluido admin, y responde 403 `permiso_insuficiente`.
- **Códigos de error nuevos:** `transicion_invalida` (409) y `solicitud_vencida` (409), registrados en el catálogo central con un mensaje fijo. Se reutilizan `reserva_solapada`, `espacio_inactivo`, `solicitud_no_encontrada`, `datos_invalidos` y `permiso_insuficiente`.
- **Rutas:** `POST /api/reservas/{id}/aprobar` y `POST /api/reservas/{id}/rechazar` (cuerpo `{"motivo": "..."}`), protegidas con `aprobaciones:aprobar` y `aprobaciones:rechazar` respectivamente. Ambas devuelven la solicitud actualizada con el mismo formato del detalle de `reservas`.
- **Pruebas de concurrencia:** se ejecutan contra PostgreSQL real (`reservas_test`) con varios hilos, cada uno con su propia conexión y sincronizados con una barrera, porque SQLite o una única conexión no reproducen la carrera. Se repiten varias veces por prueba para reducir falsos positivos.

## Risks / Trade-offs

- [Pruebas de concurrencia inestables] → Barrera de sincronización, conexiones independientes, aserciones sobre el resultado final (exactamente una aprobada) y no sobre el orden de llegada.
- [Violación de la restricción tratada como error interno] → Capturar la excepción de integridad específica de la restricción de exclusión y traducirla a `reserva_solapada`; verificarlo con una prueba de repositorio que fuerce la violación.
- [Fixtures de `reservas-disponibilidad` con estado `rechazada` sin motivo] → El nuevo `CHECK` las rechazaría; actualizar esos fixtures para incluir un motivo.
- [Bloqueo de filas] → La transacción es corta (lectura, validación, actualización) y bloquea una sola fila, por lo que el riesgo de contención es bajo.

## Open Questions

Ninguna bloqueante. Las decisiones 3 (espacio desactivado) y 4 (solicitud vencida) de proposal.md quedan pendientes de confirmación del estudiante, con el valor por defecto indicado allí.
