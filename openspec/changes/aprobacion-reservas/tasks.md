# Tasks

## 1. Persistencia del motivo de rechazo

- [ ] 1.1 Crear la migración Alembic que añade a `reservas` la columna `motivo_rechazo` (texto, nula) y `CHECK (estado <> 'rechazada' OR motivo_rechazo IS NOT NULL)`, actualizar el modelo `Reserva` y los fixtures de `reservas-disponibilidad` que usen el estado `rechazada` para que incluyan un motivo; verificar con pruebas de repositorio que una reserva `rechazada` sin motivo es rechazada por la base de datos, que una `pendiente` o `aprobada` sin motivo se acepta y que `alembic upgrade head` y `alembic downgrade -1` funcionan sobre `reservas_test` (requisito «Rechazo de solicitudes pendientes con motivo»).

## 2. Errores nuevos

- [ ] 2.1 Registrar en el catálogo central de errores los códigos `transicion_invalida` (409) y `solicitud_vencida` (409) con un mensaje fijo cada uno, reutilizando el manejador y las excepciones de dominio existentes (los códigos `reserva_solapada`, `espacio_inactivo`, `solicitud_no_encontrada`, `datos_invalidos` y `permiso_insuficiente` ya existen); verificar con una ruta registrada solo en los tests que lanza cada excepción que cada código produce su HTTP y el formato `{"error": {"codigo", "mensaje"}}` (requisitos «Transiciones permitidas desde el estado pendiente» y «Aprobación de solicitudes pendientes»).

## 3. Servicio de decisión

- [ ] 3.1 Implementar en `backend/app/aprobaciones/services.py` la función única `decidir(solicitud_id, usuario, accion, motivo)` con la transacción y el `SELECT ... FOR UPDATE` sobre la solicitud, la comprobación de existencia (404 `solicitud_no_encontrada`), de autoría (403 `permiso_insuficiente` si el usuario es el solicitante, para cualquier rol) y de estado `pendiente` (409 `transicion_invalida`); verificar con pruebas de servicio la solicitud inexistente, la propia de un aprobador y la propia de un admin con aprobar y con rechazar, y las solicitudes `aprobada`, `rechazada` y `cancelada` con ambas acciones sin cambio de estado (requisitos «Prohibición de decidir las propias solicitudes», «Transiciones permitidas desde el estado pendiente» y «Control de acceso a las decisiones»).
- [ ] 3.2 Implementar la rama de rechazo: validar el motivo (obligatorio, recortado, no vacío, hasta 500 caracteres, de lo contrario 400 `datos_invalidos`), cambiar el estado a `rechazada` y guardar el motivo; verificar con pruebas de servicio el rechazo con motivo, sin motivo, con motivo vacío o de espacios, con 500 y con 501 caracteres, el rechazo de una pendiente solapada con una aprobada y el rechazo sobre un espacio inactivo o con inicio pasado, usando el reloj inyectable (requisito «Rechazo de solicitudes pendientes con motivo»).
- [ ] 3.3 Implementar la rama de aprobación con el orden de comprobaciones de `design.md`: vigencia contra el reloj inyectable (409 `solicitud_vencida`), espacio activo (400 `espacio_inactivo`) y solapamiento con reservas aprobadas del mismo espacio (409 `reserva_solapada`), y cambiar el estado a `aprobada`; verificar con pruebas de servicio la aprobación por aprobador y por admin, el solapamiento, el borde exacto permitido, otro espacio sin conflicto, el espacio desactivado después de crear la solicitud, la solicitud vencida, que las pendientes solapadas no cambian de estado al aprobar y que una pendiente en conflicto falla con `reserva_solapada` y sigue pendiente (requisito «Aprobación de solicitudes pendientes»).
- [ ] 3.4 Traducir a 409 `reserva_solapada` la violación de la restricción de exclusión de PostgreSQL durante la actualización de la decisión, deshaciendo la transacción; verificar con una prueba de servicio que fuerce la carrera de forma determinista (insertando la reserva aprobada en conflicto entre la comprobación y la actualización) que el resultado es `reserva_solapada` y no un error interno (requisito «Decisiones simultáneas»).

## 4. API de decisiones

- [ ] 4.1 Exponer `POST /api/reservas/{id}/aprobar` con el permiso `aprobaciones:aprobar` y `POST /api/reservas/{id}/rechazar` con el permiso `aprobaciones:rechazar` y cuerpo `{"motivo": "..."}`, ambas devolviendo la solicitud actualizada con el formato del detalle de `reservas` (incluido `motivo_rechazo` en las rechazadas), y reutilizando el guard existente; verificar con pruebas de integración cada ruta por rol (solicitante 403, aprobador y admin 200), la petición sin token con 401 `token_ausente`, el identificador inexistente con 404 y que el solicitante dueño ve el motivo en el detalle de su solicitud rechazada (requisitos «Control de acceso a las decisiones», «Aprobación de solicitudes pendientes» y «Rechazo de solicitudes pendientes con motivo»).
- [ ] 4.2 Verificar con pruebas de integración que la aprobación de una solicitud aparece en la consulta de disponibilidad del espacio y que una solicitud rechazada no aparece (requisitos «Aprobación de solicitudes pendientes» y «Rechazo de solicitudes pendientes con motivo»).
- [ ] 4.3 Documentar en `backend/README.md` los dos endpoints, el permiso de cada uno, el cuerpo del rechazo y los códigos de error nuevos, y verificar que los ejemplos del documento coinciden con las rutas, los permisos y los códigos implementados (requisitos «Aprobación de solicitudes pendientes» y «Rechazo de solicitudes pendientes con motivo»).

## 5. Pruebas de concurrencia

- [ ] 5.1 Crear el soporte de pruebas de concurrencia contra `reservas_test`: una utilidad que ejecuta varias llamadas en hilos, cada uno con su propia conexión y sesión, sincronizados con una barrera, y verificar que la utilidad lanza las llamadas realmente en paralelo (requisito «Decisiones simultáneas»).
- [ ] 5.2 Escribir las pruebas de dos aprobaciones simultáneas de solicitudes solapadas del mismo espacio (exactamente una 200 y una 409 `reserva_solapada`, y una sola reserva `aprobada` al final), de dos aprobaciones simultáneas de la misma solicitud (una 200 y una 409 `transicion_invalida`) y de una aprobación y un rechazo simultáneos de la misma solicitud (una 200, una 409 `transicion_invalida` y estado final coherente con la que tuvo éxito); repetir cada prueba al menos 20 veces dentro de la misma ejecución y verificar que no aparecen errores internos ni resultados distintos (requisito «Decisiones simultáneas»).

## 6. Interfaz web de decisiones

- [ ] 6.1 Implementar en el listado de solicitudes las acciones de aprobar y rechazar visibles solo para `aprobador` y `admin` y solo sobre solicitudes `pendiente`, con el formulario de motivo que bloquea el envío vacío; verificar con pruebas Vitest las acciones visibles para aprobador y admin, su ausencia para el solicitante y sobre solicitudes `aprobada`, `rechazada` y `cancelada`, y el rechazo sin motivo sin petición al servidor (requisito «Decisión de solicitudes en la interfaz»).
- [ ] 6.2 Implementar la actualización de la solicitud tras la decisión y los mensajes de error, mostrando el estado y el motivo devueltos por el servidor y el mensaje asociado a `reserva_solapada`, `transicion_invalida`, `solicitud_vencida`, `espacio_inactivo` y `permiso_insuficiente`, sin cambiar el estado mostrado cuando hay error; verificar con pruebas Vitest la aprobación correcta, el rechazo con motivo y cada mensaje de error (requisito «Decisión de solicitudes en la interfaz»).

## 7. Verificación integral

- [ ] 7.1 Ejecutar la suite completa de `pytest` y de Vitest contra la base `reservas_test` y verificar que todos los escenarios de las specs `aprobaciones` e `interfaz-web` de este change quedan en verde, incluida la suite de `reservas-disponibilidad` con los fixtures actualizados (todos los requisitos de este change).
- [ ] 7.2 Actualizar la matriz de trazabilidad existente en `docs/matriz-trazabilidad.md` con requisito → escenario → prueba de las specs `aprobaciones` e `interfaz-web` de este change, y verificar que cada requisito tiene al menos una prueba en verde, como exige la sección 5.3 del plan (todos los requisitos de este change).
- [ ] 7.3 Revisar el diff completo contra las specs `aprobaciones` e `interfaz-web` y verificar que no queda funcionalidad implementada que no esté especificada, conforme a la sección 6.4 del plan (todos los requisitos de este change).

## Workflow follow-up

- Archivar el cambio en OpenSpec cuando se satisfagan los requisitos de revisión del proyecto.
- Verificar el resultado archivado y sincronizar las specs principales `aprobaciones` e `interfaz-web`.
