# Proposal

## Why

El sistema necesita centralizar la creación y consulta de solicitudes de reserva de espacios académicos, garantizar la prevención de solapamientos entre reservas aprobadas y permitir consultar la disponibilidad. Esto resuelve la duplicidad de solicitudes, los conflictos de horario y la dificultad para consultar disponibilidad que describe `PLAN_INGENIERIA.md`, manteniendo el flujo con aprobación obligatoria y los roles y permisos definidos en `usuarios-roles-auth`. Este change formaliza el tercer incremento vertical del sistema.

## What Changes

- Nueva capacidad `reservas` para crear solicitudes (espacio, solicitante autenticado, inicio y fin), validar fechas y espacio, aplicar la regla de ocupación y consultar solicitudes.
- **Catálogo cerrado de estados** de una reserva: `pendiente`, `aprobada`, `rechazada` y `cancelada`. En este change solo se crean solicitudes `pendiente`; las transiciones se especifican en `aprobacion-reservas` y `cancelacion-historial`.
- **Regla de ocupación:** solo las reservas `aprobada` ocupan un espacio. Una solicitud que se solape con una aprobada se rechaza de inmediato con 409 `reserva_solapada`; las pendientes pueden solaparse entre sí. Los rangos son semiabiertos `[inicio, fin)` y las fechas se envían en ISO 8601 con zona horaria explícita y se almacenan en UTC.
- **Garantía en la base de datos:** restricción de exclusión por espacio sobre el rango, solo para filas `aprobada`, además de la validación en el servicio. Requiere la extensión `btree_gist` de PostgreSQL. Se verifica a nivel de repositorio insertando directamente reservas.
- **Consulta de disponibilidad** por espacio y rango, con los intervalos ocupados por reservas aprobadas.
- **Listado y detalle de solicitudes** según la matriz de permisos `reservas:*` de `usuarios-roles-auth`.
- Se añaden a `interfaz-web` **tres requisitos nuevos** (ADDED) con el comportamiento observable de las pantallas de creación, disponibilidad y listado.

### Fuera de alcance

- Aprobación y rechazo de solicitudes, y la prueba de aprobaciones simultáneas: change `aprobacion-reservas`.
- Cancelación e historial de cambios de estado: change `cancelacion-historial`.
- Edición o eliminación de solicitudes.
- **Límite de duración máxima de una reserva:** llegará como cambio separado (etapa 8 del plan).
- Paginación y filtros del listado.
- Notificaciones, pagos e integración con sistemas académicos externos (sección 1.5 del plan).

## Capabilities

### New Capabilities

- `reservas`: creación de solicitudes, catálogo de estados, regla de ocupación, garantía contra solapamientos aprobados, consulta de disponibilidad por rango y listado y detalle de solicitudes con control por rol.
- `interfaz-web`: el change reutiliza esta capability, que aún no está publicada en `openspec/specs/` porque `usuarios-roles-auth` sigue en curso. Se añaden solo requisitos ADDED, con nombres distintos de los ya propuestos, dedicados a las pantallas de reservas.

### Modified Capabilities

_(Ninguna. El proyecto no tiene specs publicadas, por lo que todo se expresa con requisitos ADDED.)_

## Impact

- **Backend (Flask, monolito modular en capas):** nuevo módulo `reservas` con modelo, repositorio, servicio y rutas, siguiendo la estructura de `usuarios-roles-auth`.
- **Base de datos (PostgreSQL):** migraciones que instalan la extensión `btree_gist`, crean la tabla `reservas` con claves foráneas, `CHECK` de estado y de rango, la restricción de exclusión parcial y los índices. La extensión debe poder instalarse en las bases `reservas` y `reservas_test`.
- **API:** crear solicitud, consultar disponibilidad por espacio y rango, listar solicitudes y obtener el detalle de una solicitud.
- **Frontend (React):** pantallas de creación, disponibilidad y listado, reutilizando el cliente HTTP y las rutas protegidas. Su comportamiento observable se especifica en `interfaz-web`.
- **Dependencias:** ninguna nueva.
- **Contrato con el resto del sistema:** `aprobacion-reservas` y `cancelacion-historial` consumirán el modelo y los estados definidos aquí. Las pruebas de este change siembran las reservas aprobadas directamente en el repositorio, porque la aprobación aún no existe.
- **Datos existentes:** ninguno.

## Decisiones

1. **Espacio inactivo:** crear una solicitud sobre un espacio inactivo responde 400 con `espacio_inactivo`, por tratarse de una solicitud no procesable con los datos actuales y no de un conflicto de estado de la reserva.
2. **Forma de la disponibilidad:** lista de intervalos con `inicio` y `fin` en UTC, en orden ascendente, sin datos del solicitante; los intervalos que solapan parcialmente el rango se devuelven completos y los que solo tocan el borde no se incluyen.
3. **Sin paginación** en el listado de solicitudes, ordenado por inicio ascendente y luego por identificador.
4. **Disponibilidad consultable** por cualquier usuario autenticado con el permiso `espacios:ver`, y la consulta procede también sobre espacios inactivos.
5. **El solicitante siempre es el usuario autenticado:** la petición no puede indicar otro solicitante ni fijar el estado.
