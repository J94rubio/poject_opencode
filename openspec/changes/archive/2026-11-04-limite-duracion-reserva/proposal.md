# Proposal

## Why

La etapa 8 de `PLAN_INGENIERIA.md` (§4.2) introduce un cambio de regla sobre el sistema ya construido: una solicitud de reserva no puede durar más de 4 horas. Hoy la creación admite cualquier duración. El plan identifica este cambio como un riesgo (§5.2, riesgo 5) y exige análisis de impacto, spec actualizada primero y regresión completa. La arquitectura en capas (§3.1) prevé que una regla así toque un solo lugar: la capa de servicios.

## What Changes

- **Nueva regla en la creación (`POST /api/reservas`):** duración = fin − inicio, calculada sobre los instantes en UTC; la máxima es de 4 horas exactas, inclusive. Se aceptan 4 h exactas y se rechazan 4 h y 1 segundo.
- **Error nuevo:** 400 con el código `duracion_excedida` y el mensaje fijo «La duración máxima de una reserva es de 4 horas.», registrado en el catálogo central. **BREAKING** para quien cree solicitudes de más de 4 horas, que hasta ahora se aceptaban.
- **Orden de comprobaciones de la creación:** la duración se comprueba justo después de validar que el fin es posterior al inicio y antes de las demás (inicio no pasado, espacio existente, espacio activo y solapamiento). Una solicitud con duración excedida y otro defecto posterior responde `duracion_excedida`.
- Se actualiza el requisito «Creación de solicitudes de reserva» (MODIFIED), porque varios de sus escenarios contradicen literalmente la regla, y se añade el requisito «Alcance de la duración máxima» (ADDED).
- Se actualiza el requisito «Creación de solicitudes en la interfaz» (MODIFIED) solo para añadir el escenario del mensaje nuevo. La interfaz ya muestra el mensaje del servidor y no necesita cambios funcionales.
- Se ajustan las pruebas existentes que el análisis de impacto de `design.md` señala.

### Fuera de alcance

- Aprobar, rechazar y cancelar: no comprueban la duración.
- Reservas existentes de más de 4 horas: se conservan y siguen su flujo normal.
- Consulta de disponibilidad y rango del historial: no se limitan.
- Migraciones y `CHECK` en la base de datos.
- Validación de la duración en el navegador y duración máxima configurable o distinta por espacio o por rol.

## Capabilities

### New Capabilities

_(Ninguna.)_

### Modified Capabilities

- `reservas`: la creación de solicitudes incorpora la duración máxima y su lugar en el orden de comprobaciones (MODIFIED), y se delimita el alcance de la regla (ADDED).
- `interfaz-web`: la creación de solicitudes incorpora el escenario del mensaje `duracion_excedida` (MODIFIED).

Las specs `aprobaciones`, `historial`, `cancelaciones`, `espacios`, `usuarios` y `auth` no cambian (ver el análisis de impacto en `design.md`).

## Impact

- **Backend (Flask, monolito modular en capas):** una constante y una comprobación en `backend/app/reservas/services.py`, y una excepción nueva en `backend/app/auth/errors.py`. Las rutas no cambian.
- **Base de datos (PostgreSQL):** sin cambios y sin migración.
- **API:** `POST /api/reservas` puede responder el código nuevo `duracion_excedida` (400). Los demás endpoints no cambian.
- **Permisos:** sin cambios.
- **Errores:** código nuevo `duracion_excedida` (400). Las solicitudes de más de 4 horas que tenían otro defecto posterior a la duración cambian de código de error, por el orden de comprobaciones.
- **Frontend (React):** sin cambios funcionales; una prueba nueva y la actualización de un comentario que enumera los códigos.
- **Documentación:** `backend/README.md` (endpoint y tabla de errores) y `docs/matriz-trazabilidad.md`.
- **Pruebas existentes:** 5 casos de backend necesitan ajustar sus datos y 1 prueba de coherencia del README depende de documentar el código nuevo; ninguna de frontend (detalle en `design.md`).
- **Dependencias:** ninguna nueva.
- **Datos existentes:** ninguno modificado.

## Decisiones

1. **Definición de la regla:** duración = fin − inicio; máximo de 4 horas exactas, inclusive. Cualquier exceso se rechaza, también el de una fracción de segundo, porque las fechas admiten microsegundos. **Definida por el estudiante.**
2. **Alcance:** solo la creación. **Definida por el estudiante.**
3. **Código y mensaje:** `duracion_excedida` (400) con «La duración máxima de una reserva es de 4 horas.». **Definidos por el estudiante.**
4. **Posición en el orden de comprobaciones:** justo después de validar que el fin es posterior al inicio. Las comprobaciones de forma del cuerpo, campos obligatorios, tipo del espacio y fechas válidas siguen antes. **Definida por el estudiante.**
5. **Ubicación:** capa de servicios y una única constante, sin `CHECK` ni migración. **Definida por el estudiante.**
6. **Posición de la tarea de ajuste de pruebas:** primera tarea de implementación (1.1), antes de registrar el error y de implementar la regla. **Decisión confirmada por el estudiante.**
