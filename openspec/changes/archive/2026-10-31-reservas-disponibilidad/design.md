# Design

## Context

Ver proposal.md - Why. El proyecto ya cuenta con estructura modular en capas (usuarios-roles-auth, espacios) con auth/JWT, guard de permisos, manejador de errores, rutas protegidas, cliente HTTP y catálogo de espacios. Las decisiones fijas del proyecto se mantienen (Flask + PostgreSQL + React, monolito modular en capas, JWT, roles solicitante/aprobador/admin, toda solicitud nace `pendiente` y requiere aprobación, fechas en UTC, rangos semiabiertos `[inicio, fin)`, sin límite máximo de duración en este change). Los errores siguen el formato JSON y los códigos HTTP definidos en usuarios-roles-auth.

## Goals / Non-Goals

**Goals:**
- Modelo de datos para reservas con estados `pendiente`, `aprobada`, `rechazada`, `cancelada` (catálogo cerrado, impuesto también con `CHECK` en la base de datos).
- Creación de solicitudes con validaciones: fechas con zona horaria explícita, fin posterior al inicio, inicio posterior al momento actual (una solicitud que empieza en el instante actual ya comenzó y se rechaza, el mismo criterio que aprobación y cancelación), espacio existente y activo.
- Prevención de solapamientos con reservas aprobadas: validación en servicio (409 `reserva_solapada`) más restricción de exclusión en PostgreSQL sobre el rango `[inicio, fin)` por espacio, solo para estado `aprobada`.
- Consulta de disponibilidad por espacio y rango (solo las reservas aprobadas ocupan).
- Listado y detalle con control por rol (solicitante solo propias; aprobador y admin todas), reutilizando los permisos de usuarios-roles-auth.
- Requisitos mínimos observables en `interfaz-web` para este módulo.

**Non-Goals:**
- Transiciones de estado (aprobación, rechazo, cancelación): se especifican en otros changes.
- Límite máximo de duración: llegará en un change separado.
- Paginación y filtros del listado.
- Edición o eliminación de solicitudes.
- Notificaciones, pagos, inventario, múltiples sedes.
- Prueba de aprobaciones simultáneas: pertenece a `aprobacion-reservas`.

## Decisions

- **Almacenamiento de fechas:** se envía ISO 8601 con zona horaria explícita; se convierte y almacena en UTC (`TIMESTAMP WITH TIME ZONE`). Una fecha sin zona horaria es inválida (400 `datos_invalidos`).
- **Reloj inyectable:** el servicio recibe el reloj como dependencia para que las pruebas de "inicio en el pasado" no dependan de la fecha real.
- **Rangos semiabiertos:** `[inicio, fin)` para permitir el caso "termina exactamente cuando empieza".
- **Ocupación:** solo `aprobada` ocupa espacio. Las pendientes pueden solaparse entre sí. Una solicitud que se solape con una aprobada se rechaza con 409 `reserva_solapada`.
- **Garantía de integridad:** migración previa con `CREATE EXTENSION IF NOT EXISTS btree_gist` (necesaria para combinar `espacio_id WITH =` con un rango en un índice gist) y restricción `EXCLUDE USING gist (espacio_id WITH =, tstzrange(inicio_utc, fin_utc, '[)') WITH &&) WHERE (estado = 'aprobada')`, que protege también ante concurrencia. Se añade `CHECK (fin_utc > inicio_utc)`. La validación del servicio da el error amigable; la restricción es la última barrera.
- **Verificación de la restricción:** pruebas a nivel de repositorio insertando directamente reservas aprobadas solapadas, que deben fallar. Como la aprobación aún no existe, las pruebas de servicio y API siembran reservas aprobadas directamente en el repositorio.
- **Espacio inactivo:** crear una solicitud sobre un espacio inactivo responde 400 `espacio_inactivo`; un espacio inexistente responde 404 `espacio_no_encontrado`. Un espacio reactivado vuelve a admitir solicitudes.
- **Disponibilidad:** lista de intervalos `inicio` y `fin` en UTC, ascendente, sin datos del solicitante; los intervalos que solapan parcialmente el rango se devuelven completos y los que solo tocan el borde se excluyen. Consultable con el permiso `espacios:ver`, también sobre espacios inactivos.
- **Listados:** sin paginación, ordenados por inicio ascendente y luego por identificador.
- **Detalle ajeno:** el solicitante recibe 403 `permiso_insuficiente`; aprobador y admin pueden verlo; un identificador inexistente responde 404 `solicitud_no_encontrada`.
- **Permisos y errores:** se reutilizan la matriz y el formato `{"error": {"codigo", "mensaje"}}` de usuarios-roles-auth. Los códigos nuevos (`espacio_inactivo`, `reserva_solapada`, `solicitud_no_encontrada`) se registran en el catálogo central.
- **Datos de solicitud:** solo espacio, inicio y fin. El solicitante siempre es el usuario autenticado y un campo de solicitante en el cuerpo se rechaza con 400.

## Risks / Trade-offs

- [Restricción de exclusión] → Requiere `btree_gist` en `reservas` y `reservas_test`; verificar la extensión en la primera migración y probar la restricción con inserción directa.
- [Manejo de zonas horarias] → Rechazar fechas sin zona explícita y normalizar a UTC.
- [Rangos límite] → Probar el caso "termina exactamente cuando empieza" (permitido).
- [Espacio inactivo o reactivado] → Verificar el estado del espacio al crear la solicitud.
- [Sin aprobación disponible aún] → Sembrar reservas aprobadas directamente en el repositorio para las pruebas; el flujo real se prueba en `aprobacion-reservas`.

## Open Questions

Ninguna. Las decisiones están fijadas en proposal.md.
