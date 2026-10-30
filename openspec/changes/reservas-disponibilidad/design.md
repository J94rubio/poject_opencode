# Design

## Context

Ver proposal.md - Why. El proyecto ya cuenta con estructura modular en capas (usuarios-roles-auth, espacios) con auth/JWT, guard de permisos, manejador de errores, rutas protegidas, cliente HTTP y catálogo de espacios. Las decisiones fijas del proyecto se mantienen (Flask + PostgreSQL + React, monolito modular en capas, JWT, roles solicitante/aprobador/admin, toda solicitud nace "pendiente" y requiere aprobación, fechas en UTC, rangos semiabiertos [inicio, fin), sin límite máximo de duración en este change). Los errores siguen el formato JSON y códigos HTTP definidos en usuarios-roles-auth.

## Goals / Non-Goals

**Goals:**
- Modelo de datos para reservas con estados `pendiente`, `aprobada`, `rechazada`, `cancelada` (catálogo cerrado).
- Creación de solicitudes con validaciones (fechas con zona horaria, fin>inicio, inicio>=ahora, espacio existe y activo).
- Prevención de solapamientos con reservas aprobadas: validación en servicio + restricción de exclusión en PostgreSQL sobre rango `[inicio, fin)` por espacio, solo para estado `aprobada`.
- Consulta de disponibilidad por espacio/rango (solo reservas aprobadas ocupan).
- Listado/detalle con control por rol (solicitante solo propias; aprobador/admin todas) reutilizando permisos de usuarios-roles-auth.
- Requisitos mínimos observables en interfaz-web para este módulo.

**Non-Goals:**
- Transiciones de estado (aprobación/rechazo/cancelación) - se especifican en otros changes.
- Límite máximo de duración - llegará en change separado.
- Notificaciones, pagos, inventario, múltiples sedes.
- Prueba de aprobaciones simultáneas en este change.

## Decisions

- **Almacenamiento de fechas**: enviar ISO 8601 con zona horaria explícita; convertir y almacenar en UTC. Una fecha sin zona horaria es inválida.
- **Rangos semiabiertos**: usar `[inicio, fin)` para evitar solapamiento en el caso "termina exactamente cuando empieza".
- **Ocupación**: solo `aprobada` ocupa espacio. Pendientes pueden solaparse entre sí.
- **Garantía de integridad**: restricción de exclusión `EXCLUDE USING gist` (o equivalente) sobre `(espacio_id, tstzrange(inicio_utc, fin_utc, '[)'))` con `WHERE estado = 'aprobada'` para prevenir solapamientos aprobados incluso con concurrencia. Validación adicional en servicio.
- **Verificación**: prueba a nivel de repositorio insertando directamente reservas aprobadas solapadas debe fallar por la restricción.
- **Permisos/errores**: reutilizar matriz y formato/códigos de usuarios-roles-auth (400/401/403/404/409 con códigos snake_case).
- **Datos de solicitud**: solo espacio, solicitante (usuario autenticado), inicio, fin - sin campos adicionales.

## Risks / Trade-offs

- [Restricción de exclusión compleja] → Implementar correctamente con GIST sobre tstzrange y predicado por estado; verificar con inserción directa.
- [Manejo de zonas horarias] → Rechazar fechas sin zona horaria explícita y normalizar a UTC.
- [Rangos límite] → Probar caso "termina exactamente cuando empieza" (permitido).
- [Espacio inactivo/reactivado] → Verificar estado del espacio al crear solicitud (inactivo rechaza; reactivado vuelve a admitir).

## Open Questions

Ninguna. Todas las decisiones están fijadas por las instrucciones.
