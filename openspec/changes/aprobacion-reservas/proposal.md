# Proposal

## Why

Las solicitudes de reserva nacen en estado `pendiente` y, según `PLAN_INGENIERIA.md`, solo ocupan un espacio cuando un aprobador o un administrador las aprueba. Sin esta decisión, el sistema no puede confirmar ninguna reserva ni rechazarla con una razón. Este change formaliza el cuarto incremento vertical: las decisiones sobre solicitudes pendientes, con la garantía de que dos aprobaciones simultáneas nunca producen reservas aprobadas solapadas.

## What Changes

- Nueva capacidad `aprobaciones` con dos acciones sobre una solicitud `pendiente`: **aprobar** (pasa a `aprobada`) y **rechazar** con motivo obligatorio (pasa a `rechazada`).
- **Sin rechazo automático:** al aprobar una solicitud, las demás solicitudes pendientes que se solapan con ella no cambian de estado. Si luego se intenta aprobarlas, fallan con 409 `reserva_solapada`; el aprobador puede rechazarlas manualmente.
- **Transiciones permitidas:** solo se decide sobre solicitudes `pendiente`. Cualquier otro estado de origen responde 409 `transicion_invalida`.
- **Nadie decide sus propias solicitudes:** aunque aprobador y admin hereden los permisos de solicitante, no pueden aprobar ni rechazar una solicitud creada por ellos mismos (403 `permiso_insuficiente`).
- **Aprobaciones simultáneas:** la aprobación se ejecuta en una transacción que bloquea la fila de la solicitud, y la restricción de exclusión de la base de datos (creada en `reservas-disponibilidad`) actúa como última barrera. De dos aprobaciones concurrentes de solicitudes solapadas, exactamente una tiene éxito.
- **Motivo del rechazo:** se guarda en la solicitud y aparece en su detalle.
- Se añade a `interfaz-web` **un requisito nuevo** (ADDED) con el comportamiento observable de las acciones de decisión.

### Fuera de alcance

- Cancelación de reservas e historial de cambios de estado, incluido quién decidió y cuándo: change `cancelacion-historial`. Las decisiones de este change pasan por una única función de servicio para que ese change pueda registrarlas sin reescribirlas.
- Rechazo o aprobación en lote.
- Edición del motivo de un rechazo ya emitido.
- Notificaciones al solicitante.
- Reversión de una decisión (aprobada → pendiente, rechazada → pendiente).

## Capabilities

### New Capabilities

- `aprobaciones`: aprobación y rechazo de solicitudes pendientes, transiciones permitidas, prohibición de decidir las propias solicitudes, motivo del rechazo, control de acceso y comportamiento ante aprobaciones simultáneas.
- `interfaz-web`: el change reutiliza esta capability, que aún no está publicada en `openspec/specs/` porque ningún change se ha archivado. Se añade solo un requisito ADDED, con nombre distinto de los ya propuestos, dedicado a las decisiones sobre solicitudes.

### Modified Capabilities

_(Ninguna. El proyecto no tiene specs publicadas, por lo que todo se expresa con requisitos ADDED.)_

## Impact

- **Backend (Flask, monolito modular en capas):** nuevo módulo `aprobaciones` con servicio y rutas, que reutiliza el repositorio y el modelo de `reservas`.
- **Base de datos (PostgreSQL):** una migración que añade a `reservas` la columna `motivo_rechazo` y una restricción `CHECK` que exige motivo cuando el estado es `rechazada`. La restricción de exclusión de `reservas-disponibilidad` no cambia.
- **API:** `POST /api/reservas/{id}/aprobar` y `POST /api/reservas/{id}/rechazar` (este último con el motivo en el cuerpo). El detalle de una solicitud rechazada incluye `motivo_rechazo`.
- **Permisos:** se usan `aprobaciones:aprobar` y `aprobaciones:rechazar` de la matriz de `usuarios-roles-auth` (aprobador y admin). No se crean permisos nuevos.
- **Errores:** códigos nuevos `transicion_invalida` (409) y `solicitud_vencida` (409); se reutilizan `reserva_solapada`, `espacio_inactivo`, `solicitud_no_encontrada`, `datos_invalidos` y `permiso_insuficiente`.
- **Frontend (React):** acciones de aprobar y rechazar en el listado y el detalle de solicitudes.
- **Dependencias:** ninguna nueva.
- **Contrato con el resto del sistema:** `cancelacion-historial` consumirá el estado `aprobada` y el motivo de rechazo definidos aquí. Las pruebas de este change ya no necesitan sembrar reservas aprobadas: las crean aprobando solicitudes.
- **Datos existentes:** ninguno.

## Decisiones

1. **Sin rechazo automático de pendientes solapadas.** Se evaluó y se descartó: es irreversible si la reserva aprobada se cancela después y añade complejidad (transacción atómica y eventos adicionales en el historial). Decisión confirmada por el estudiante.
2. **Rechazo con motivo obligatorio:** texto no vacío tras recortar espacios, de hasta 500 caracteres; de lo contrario, 400 `datos_invalidos`.
3. **Aprobar sobre un espacio desactivado después de crear la solicitud:** responde 400 `espacio_inactivo` y la solicitud sigue pendiente, coherente con la regla de creación (un espacio inactivo no admite nuevas ocupaciones). Rechazarla sigue permitido. Las reservas ya aprobadas de un espacio que se desactiva no se tocan (decisión de `espacios`). **Decisión pendiente de confirmar por el estudiante.**
4. **Aprobar una solicitud cuyo inicio ya pasó:** responde 409 `solicitud_vencida` y la solicitud sigue pendiente; rechazarla sigue permitido. Se compara contra el reloj inyectable. **Decisión pendiente de confirmar por el estudiante.**
5. **Decisión sobre la propia solicitud:** 403 `permiso_insuficiente` para cualquier rol, incluido admin.
6. **Orden de las comprobaciones al aprobar:** permiso, existencia, autoría, estado `pendiente`, solicitud vigente, espacio activo y, por último, solapamiento.
