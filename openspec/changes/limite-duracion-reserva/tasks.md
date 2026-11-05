# Tasks

## 1. Ajuste de pruebas existentes

- [x] 1.1 Ajustar, antes de implementar la regla, los datos de entrada de los casos que el análisis de impacto marca en `design.md`, sin cambiar lo que esperan: `test_reservas_api.py::test_creacion_con_datos_invalidos[inicio_en_el_instante_actual]`, las tres variantes de `test_entradas_no_validas.py::test_solicitud_que_termina_despues_de_la_ultima_fecha_admitida` y `test_entradas_no_validas.py::test_la_ultima_fecha_admitida_se_lee_en_la_zona_con_mayor_desfase`; verificar que con el código actual los 5 casos pasan con su código original (`datos_invalidos` o 201), que ninguno supera las 4 horas y que la suite completa de `pytest` queda en verde. Si falla una prueba no listada en `design.md`, detenerse y describirla (requisitos «Creación de solicitudes de reserva» y «Alcance de la duración máxima»).

## 2. Código de error y documentación de la API

- [x] 2.1 Registrar en el catálogo central (`backend/app/auth/errors.py`) la clase `DuracionExcedida`, subclase directa de `ErrorDeDominio`, con HTTP 400, código `duracion_excedida` y el mensaje fijo «La duración máxima de una reserva es de 4 horas.», reutilizando el manejador existente, y en la misma tarea documentar en `backend/README.md` la duración máxima, su lugar en el orden de comprobaciones y el error en la sección «Crear una solicitud», y añadir `duracion_excedida` (400) a la tabla de errores, aclarando que aprobar, rechazar, cancelar, la disponibilidad y el historial no se limitan; verificar con una ruta registrada solo en los tests que el error produce su HTTP y el formato `{"error": {"codigo", "mensaje"}}` y que no acepta un mensaje propio, que `test_readme.py` pasa completo, incluido `test_el_catalogo_de_errores_coincide_con_el_implementado`, que el ejemplo de creación existente dura como máximo 4 horas y que la suite completa de `pytest` sigue en verde (requisitos «Creación de solicitudes de reserva» y «Alcance de la duración máxima»).

## 3. Regla en el servicio

- [x] 3.1 Añadir en `backend/app/reservas/services.py` la constante única `DURACION_MAXIMA = timedelta(hours=4)` y, en `crear_solicitud`, la comprobación `fin_utc - inicio_utc > DURACION_MAXIMA` justo después de `validar_rango`, sin modificar `validar_rango`, y actualizar el orden de validación del docstring del módulo; verificar con pruebas de servicio con reloj inyectado que se aceptan 1 h y 4 h exactas, que se rechazan con `DuracionExcedida` 4 h y 1 segundo y 4 h y 1 microsegundo, y los dos casos con zonas horarias distintas de la spec, que los 5 casos ajustados en la tarea 1.1 siguen pasando con la regla y que la suite completa de `pytest` sigue en verde. Si falla una prueba no listada en `design.md`, detenerse y describirla (requisito «Creación de solicitudes de reserva»).
- [x] 3.2 Verificar con pruebas de servicio la precedencia con una duración mayor de 4 horas: inicio pasado, inicio en el instante actual, espacio inexistente, espacio inactivo y solapamiento con una reserva aprobada producen `DuracionExcedida`; un campo no admitido y un espacio no entero producen `DatosInvalidos`; un fin igual o anterior al inicio sigue produciendo `DatosInvalidos`; y cada uno de los escenarios existentes con una duración no mayor de 4 horas conserva su código. En cada rechazo por duración, comprobar que no se añade ninguna reserva ni entrada de historial (requisito «Creación de solicitudes de reserva»).
- [x] 3.3 Verificar con pruebas de servicio, sembrando directamente en el repositorio reservas de más de 4 horas, que `decidir` las aprueba y las rechaza, que `cancelar` las cancela en estado `pendiente` y `aprobada`, y que `consultar_disponibilidad` y la consulta del historial aceptan rangos de más de 4 horas; comprobar que `alembic heads` y `backend/migrations/` no cambian (requisito «Alcance de la duración máxima»).

## 4. API

- [x] 4.1 Verificar con pruebas de integración de `POST /api/reservas`, sin cambiar las rutas, que 1 h y 4 h exactas responden 201; que 4 h y 1 segundo responde 400 con exactamente `{"error": {"codigo": "duracion_excedida", "mensaje": "La duración máxima de una reserva es de 4 horas."}}`; que los casos con inicio pasado y espacio inexistente responden `duracion_excedida`; que un rechazo no cambia el listado ni la respuesta de `GET /api/historial`; y que sin token sigue respondiendo 401 `token_ausente` aunque la duración esté excedida (requisito «Creación de solicitudes de reserva»).
- [x] 4.2 Verificar con pruebas de integración, sembrando reservas de más de 4 horas, que `POST /api/reservas/{id}/aprobar`, `/rechazar` y `/cancelar` responden 200, que el listado y el detalle las devuelven sin cambios, y que `GET /api/espacios/{id}/disponibilidad` y `GET /api/historial` responden 200 con rangos de más de 4 horas (requisito «Alcance de la duración máxima»).

## 5. Interfaz web

- [x] 5.1 Añadir a `CreacionSolicitud.test.jsx` un caso de Vitest con un formulario de más de 4 horas y una respuesta 400 `duracion_excedida`, y añadir el código al comentario de cabecera de `FormularioSolicitud.jsx`, sin ningún otro cambio en el código del frontend; verificar que la petición se envía sin validar la duración en el navegador, que se muestra el mensaje del servidor y que no aparece ninguna solicitud creada (requisito «Creación de solicitudes en la interfaz»).

## 6. Verificación integral

- [x] 6.1 Ejecutar la suite completa de `pytest` contra `reservas_test` y la de Vitest y verificar que no hay ningún fallo ni prueba omitida, que todos los escenarios de los deltas de `reservas` e `interfaz-web` quedan en verde y que las suites de los changes anteriores siguen en verde, como exige la etapa 8 del plan (todos los requisitos de este change).
- [x] 6.2 Actualizar `docs/matriz-trazabilidad.md` con requisito → escenario → prueba de los deltas de `reservas` e `interfaz-web`, incluidos el requisito ADDED, los escenarios nuevos, las pruebas ajustadas, el resumen y los totales de pruebas; verificar que cada requisito y cada escenario de este change tiene al menos una prueba en verde, como exige la sección 5.3 del plan (todos los requisitos de este change).
- [x] 6.3 Revisar el diff completo contra los deltas de `reservas` e `interfaz-web` y verificar que no queda funcionalidad sin especificar, que el valor de la regla solo figura en la constante y en el mensaje fijo, que `validar_rango`, `aprobaciones`, `cancelaciones`, `historial` y `backend/migrations/` no cambian y que no se añadieron dependencias, conforme a la sección 6.4 del plan (todos los requisitos de este change).

## Workflow follow-up

- Archivar el cambio en OpenSpec cuando se satisfagan los requisitos de revisión del proyecto.
- Verificar el resultado archivado y sincronizar las specs principales `reservas` e `interfaz-web`.
