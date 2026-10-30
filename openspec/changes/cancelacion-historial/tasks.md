# Tasks

## 1. Persistencia del historial

- [ ] 1.1 Crear el modelo `EntradaHistorial` y la migración Alembic de la tabla `historial_reservas` con `reserva_id` y `actor_id` como claves foráneas, `espacio_id`, `estado_anterior` y `estado_nuevo` restringidos por `CHECK` al catálogo de estados, `CHECK` que exige `estado_anterior` nulo si y solo si `estado_nuevo = 'pendiente'`, `fecha_utc` como `TIMESTAMP WITH TIME ZONE` e índices por reserva, por espacio y por fecha; verificar con pruebas de repositorio que un estado fuera del catálogo, una clave foránea inexistente y una combinación inválida de estados son rechazados y que `alembic upgrade head` y `alembic downgrade -1` funcionan sobre `reservas_test` (requisito «Registro de cada cambio de estado»).
- [ ] 1.2 Añadir en una migración separada el disparador `BEFORE UPDATE OR DELETE` que lanza una excepción, y configurar los fixtures de pruebas para limpiar con `TRUNCATE` o recreación del esquema y no con `DELETE`; verificar con pruebas de repositorio que un `UPDATE` directo y un `DELETE` directo fallan y que la entrada conserva sus valores (requisito «Inmutabilidad del historial»).

## 2. Repositorio y registro del historial

- [ ] 2.1 Implementar en `backend/app/historial/repositories.py` la función `registrar(sesion, reserva, estado_anterior, estado_nuevo, actor)`, que usa el reloj inyectable para `fecha_utc` y copia el espacio de la reserva, y `listar(usuario_id_o_todos, espacio_id, estado, desde, hasta)` con los filtros combinados con Y lógico, rango `[desde, hasta)` y orden por fecha ascendente y luego por identificador; verificar con pruebas de repositorio cada filtro por separado y combinados, el límite del rango (igual a `desde` incluido, igual a `hasta` excluido) y el orden con fechas iguales (requisitos «Filtros del historial» y «Consulta del historial según el rol»).
- [ ] 2.2 Verificar a nivel de repositorio que `listar` restringido a un solicitante devuelve solo entradas de las reservas que creó, incluidas las decisiones tomadas por otros, y que esa restricción se mantiene al combinarla con el filtro de espacio (requisitos «Consulta del historial según el rol» y «Filtros del historial»).

## 3. Integración del registro en los flujos existentes

- [ ] 3.1 Llamar a `registrar` desde la creación de solicitudes de `reservas-disponibilidad` dentro de la misma transacción (estado anterior vacío, estado nuevo `pendiente`, actor el solicitante); verificar que cada creación correcta añade exactamente una entrada, que una creación rechazada (400, 404 o 409) no añade ninguna y que las pruebas existentes de creación siguen en verde (requisito «Registro de cada cambio de estado»).
- [ ] 3.2 Llamar a `registrar` desde la función `decidir` de `aprobacion-reservas` dentro de su transacción (aprobación y rechazo, actor el aprobador); verificar que cada decisión correcta añade exactamente una entrada con los estados y el actor correctos, que una decisión rechazada con error no añade ninguna y que las pruebas de aprobación y de concurrencia existentes siguen en verde (requisito «Registro de cada cambio de estado»).
- [ ] 3.3 Verificar la atomicidad forzando un fallo de `registrar` (con un doble de prueba que lance una excepción) durante la creación y durante una decisión: el estado de la solicitud no cambia, la creación no deja la solicitud y el historial no contiene entradas nuevas (requisito «Registro de cada cambio de estado»).

## 4. Servicio de cancelación

- [ ] 4.1 Registrar en el catálogo central de errores el código `reserva_iniciada` (409) con un mensaje fijo, reutilizando el manejador existente, y verificar con una ruta registrada solo en los tests que produce su HTTP y el formato `{"error": {"codigo", "mensaje"}}` (requisito «Condiciones de la cancelación»).
- [ ] 4.2 Implementar en `backend/app/cancelaciones/services.py` la función `cancelar(solicitud_id, usuario)` con transacción y `SELECT ... FOR UPDATE`, las comprobaciones en el orden de `design.md` (existencia, dueño, estado `pendiente` o `aprobada`, inicio posterior al reloj inyectable), el cambio a `cancelada` y la llamada a `registrar` en la misma transacción; verificar con pruebas de servicio la cancelación de una pendiente y de una aprobada, la propia de un aprobador y de un admin, la ajena por solicitante, aprobador y admin, la inexistente, las rechazadas y canceladas, la que ya comenzó y la que empieza en el instante actual, y que cada cancelación correcta añade una entrada y cada error ninguna (requisitos «Cancelación de reservas propias», «Condiciones de la cancelación» y «Cancelación restringida al dueño»).
- [ ] 4.3 Verificar con pruebas de servicio que cancelar una reserva aprobada libera el espacio: el intervalo desaparece de la disponibilidad, una solicitud pendiente que se solapaba con ella se puede aprobar y una reserva cancelada no se puede aprobar (`transicion_invalida`) (requisito «Liberación del espacio al cancelar»).

## 5. API de cancelación e historial

- [ ] 5.1 Exponer `POST /api/reservas/{id}/cancelar` con el permiso `reservas:cancelar_propia`, devolviendo la solicitud actualizada con el formato del detalle de `reservas`, y reutilizando el guard existente; verificar con pruebas de integración cada rol, la petición sin token con 401 `token_ausente` y al menos un caso de cada código 403, 404 y 409 con el formato JSON de `usuarios-roles-auth` (requisitos «Cancelación de reservas propias», «Condiciones de la cancelación» y «Cancelación restringida al dueño»).
- [ ] 5.2 Exponer `GET /api/historial` con los permisos `historial:ver_todos` y `historial:ver_propio` y los parámetros `espacio_id`, `estado`, `desde` y `hasta`, validando el estado contra el catálogo, el rango (ambos extremos, zona horaria explícita, `hasta` posterior a `desde`) y la existencia del espacio, y devolviendo cada entrada con reserva, espacio, estados, actor y fecha en UTC; verificar con pruebas de integración la visibilidad por rol, cada filtro, los filtros combinados, la lista vacía, el 401, el 400 por estado fuera del catálogo y por rango inválido y el 404 por espacio inexistente (requisitos «Consulta del historial según el rol» y «Filtros del historial»).
- [ ] 5.3 Verificar con pruebas de integración que `POST`, `PUT`, `PATCH` y `DELETE` sobre `/api/historial` responden 405 `metodo_no_permitido` y que el historial no cambia (requisito «Inmutabilidad del historial»).
- [ ] 5.4 Documentar en `backend/README.md` los endpoints de cancelación e historial, sus permisos, los filtros, el orden de las entradas y el código de error nuevo, y verificar que los ejemplos coinciden con las rutas, los permisos y los códigos implementados (requisitos «Cancelación de reservas propias» y «Consulta del historial según el rol»).

## 6. Pruebas de concurrencia

- [ ] 6.1 Escribir, con la utilidad de concurrencia de `aprobacion-reservas`, las pruebas de dos cancelaciones simultáneas de la misma solicitud (una 200 y una 409 `transicion_invalida`, y una sola entrada de cancelación en el historial) y de una cancelación y una aprobación simultáneas de la misma solicitud pendiente (cancelación 200, aprobación 200 o 409 `transicion_invalida`, estado final `cancelada` y entradas de historial coherentes con la secuencia real); repetir cada prueba al menos 20 veces dentro de la misma ejecución y verificar que no aparecen errores internos (requisito «Cancelaciones simultáneas»).

## 7. Interfaz web de cancelación e historial

- [ ] 7.1 Implementar la acción de cancelar en el listado de solicitudes, visible solo sobre solicitudes propias en estado `pendiente` o `aprobada` con inicio futuro, con la actualización de la solicitud y los mensajes de `transicion_invalida`, `reserva_iniciada` y `permiso_insuficiente` sin cambiar el estado mostrado cuando hay error; verificar con pruebas Vitest la acción visible, su ausencia sobre solicitudes rechazadas, canceladas, iniciadas y ajenas, la cancelación correcta y cada mensaje de error (requisito «Cancelación de reservas en la interfaz»).
- [ ] 7.2 Implementar la pantalla de historial con las entradas devueltas por la API, los filtros de espacio, estado y rango de fechas enviados con zona horaria explícita, el estado vacío sin error y los mensajes de `datos_invalidos` y `espacio_no_encontrado`; verificar con pruebas Vitest las entradas visibles, el envío de los filtros, la lista vacía y cada mensaje de error (requisito «Consulta del historial en la interfaz»).

## 8. Verificación integral

- [ ] 8.1 Ejecutar la suite completa de `pytest` y de Vitest contra la base `reservas_test` y verificar que todos los escenarios de las specs `cancelaciones`, `historial` e `interfaz-web` de este change quedan en verde, y que las suites de los changes anteriores siguen en verde tras integrar el registro del historial (todos los requisitos de este change).
- [ ] 8.2 Actualizar la matriz de trazabilidad existente en `docs/matriz-trazabilidad.md` con requisito → escenario → prueba de las specs `cancelaciones`, `historial` e `interfaz-web` de este change, y verificar que cada requisito tiene al menos una prueba en verde, como exige la sección 5.3 del plan (todos los requisitos de este change).
- [ ] 8.3 Revisar el diff completo contra las specs `cancelaciones`, `historial` e `interfaz-web` y verificar que no queda funcionalidad implementada que no esté especificada, conforme a la sección 6.4 del plan (todos los requisitos de este change).

## Workflow follow-up

- Archivar el cambio en OpenSpec cuando se satisfagan los requisitos de revisión del proyecto.
- Verificar el resultado archivado y sincronizar las specs principales `cancelaciones`, `historial` e `interfaz-web`.
