# Design

## Context

Ver proposal.md - Why. `crear_solicitud` (`backend/app/reservas/services.py`) valida en este orden: forma del cuerpo y campos, tipo del espacio, rango con `validar_rango` (fechas con zona y fin posterior al inicio), inicio posterior al reloj inyectable junto con el límite técnico `FIN_MAXIMO_UTC`, existencia y estado del espacio y, por último, solapamiento. `validar_rango` es compartida: la usan también `consultar_disponibilidad` y el filtro `desde`/`hasta` del historial (`backend/app/historial/services.py`). Los errores de dominio son subclases directas de `ErrorDeDominio` en `backend/app/auth/errors.py`, con mensaje fijo. `backend/tests/test_readme.py` exige que la tabla de errores del README coincida con esas subclases.

## Goals / Non-Goals

**Goals:**
- Aplicar la regla en un único lugar y solo en la creación.
- Fijar con escenarios el límite exacto y la precedencia de `duracion_excedida`.
- Mantener intacto el comportamiento de aprobar, rechazar, cancelar, disponibilidad e historial.

**Non-Goals:**
- Migraciones o restricciones en la base de datos.
- Validación en el navegador.
- Hacer configurable la duración máxima.

## Decisions

- **Constante única:** `DURACION_MAXIMA = timedelta(hours=4)` en `backend/app/reservas/services.py`, junto a las demás definiciones del módulo. Es el único lugar del sistema donde figura el valor numérico de la regla, salvo el texto fijo del mensaje en el catálogo de errores.
- **Comprobación en `crear_solicitud`, no en `validar_rango`:** se añade justo después de la llamada a `validar_rango`. Ponerla dentro de `validar_rango` limitaría también la disponibilidad y el historial, lo que está fuera de alcance. La comparación es `fin_utc - inicio_utc > DURACION_MAXIMA`, sobre instantes en UTC y con precisión de microsegundos.
- **Relación con `FIN_MAXIMO_UTC`:** ese límite técnico comparte hoy condición con el inicio no pasado, así que queda después de la duración. Una solicitud que incumple ambos responde `duracion_excedida`. No se cambia su valor ni su código.
- **Sin cambios en otros flujos:** `decidir` y `cancelar` trabajan sobre reservas ya creadas y no llaman a `crear_solicitud`, por lo que no necesitan cambios.
- **Sin rastro al rechazar:** la comprobación ocurre antes de abrir cualquier escritura, de modo que no se crea reserva ni entrada de historial.
- **Código de error nuevo:** clase `DuracionExcedida` (subclase directa de `ErrorDeDominio`, 400, `duracion_excedida`). No hereda de `DatosInvalidos`, porque el catálogo y `test_readme.py` solo reconocen las subclases directas.
- **Rutas:** no cambian; el manejador de errores existente traduce la excepción al formato `{"error": {"codigo", "mensaje"}}`.
- **Alternativa descartada, `CHECK` en la base de datos:** impediría conservar reservas existentes de más de 4 horas y exigiría migración.

## Análisis de impacto

Exigido por `PLAN_INGENIERIA.md` §5.2, riesgo 5.

### (a) Requisitos y escenarios publicados

| Spec | Requisito | Efecto | Expresión en el delta |
|---|---|---|---|
| `reservas` | Creación de solicitudes de reserva | **Contradice la regla.** Leídos literalmente, «Creación válida en estado pendiente» promete 201 a cualquier duración; «Inicio en el pasado» e «Inicio en el instante actual» prometen `datos_invalidos`, «Espacio inexistente» `espacio_no_encontrado` y «Espacio inactivo rechaza la solicitud» `espacio_inactivo`, aunque ahora gane `duracion_excedida` si la duración está excedida. | **MODIFIED** con el texto completo: esos 5 escenarios acotan la duración en su condición y se añaden los de la regla. Los demás se conservan literalmente. |
| `reservas` | Alcance de la regla | Falta dejar constancia de lo que no se limita. | **ADDED** «Alcance de la duración máxima». |
| `reservas` | Ocupación por reservas aprobadas | No se contradice: todas sus solicitudes duran como máximo 4 horas. «Solicitud que contiene a una reserva aprobada» usa [10:00, 14:00), justo 4 h, y sigue respondiendo 409 solo porque el límite es inclusivo. El requisito sigue cumpliéndose para rangos mayores, que también se rechazan, aunque con otro código. | Sin cambios; la precedencia va en «Duración excedida con solapamiento». |
| `reservas` | Garantía de integridad contra solapamientos aprobados | No afectado: inserta directamente en el repositorio y no se añade `CHECK`. | Sin cambios. |
| `reservas` | Consulta de disponibilidad de un espacio por rango | No afectado: sus rangos de 10 h son consultas, no solicitudes. | Sin cambios; se fija en el requisito ADDED. |
| `reservas` | Catálogo de estados; Listado y detalle de solicitudes | No afectados. | Sin cambios. |
| `aprobaciones` | Todos | No afectados: no comprueban la duración. | Sin cambios; se fija en el requisito ADDED de `reservas`. |
| `cancelaciones` | Todos | No afectados. | Sin cambios; ídem. |
| `historial` | Registro de cada cambio de estado | No se contradice: una creación rechazada no es un cambio de estado. | Sin cambios; se cubre con «La solicitud rechazada por duración no deja rastro». |
| `historial` | Filtros del historial | No afectado: el rango de fechas no se limita. | Sin cambios; se fija en el requisito ADDED de `reservas`. |
| `interfaz-web` | Creación de solicitudes en la interfaz | No se contradice, pero «Mensajes de error de la creación» enumera una lista cerrada de códigos que no incluye el nuevo. | **MODIFIED** con el texto completo (ver (c)). |
| `espacios`, `usuarios`, `auth` | Todos | No afectados: no especifican la creación de solicitudes. | Sin cambios. |

### (b) Pruebas existentes

**Método.** Una búsqueda de texto no basta, porque muchas fechas se construyen con funciones auxiliares. Por eso, además de buscar, se ejecutó la suite real de backend contra `reservas_test` el 2026-11-04, sin modificar el repositorio: una vez tal cual y otra con la regla simulada desde un plugin de pytest externo, en la posición definida y con una subclase directa de `ErrorDeDominio`. El plugin anotó cada prueba que activaba la regla.

**Resultado.** Sin la regla: 1330 pasadas. Con la regla: 1324 pasadas y 6 fallidas. Cinco casos crean solicitudes de más de 4 horas y el sexto falla porque el código no está documentado:

| Archivo | Prueba | Duración | Por qué falla | Ajuste necesario |
|---|---|---|---|---|
| `backend/tests/test_reservas_api.py` | `test_creacion_con_datos_invalidos[inicio_en_el_instante_actual]` | 24 h | Espera `datos_invalidos`, recibe `duracion_excedida`. | Conservar el inicio igual al reloj (`2026-11-02T12:00:00Z`) y acortar el fin a `2026-11-02T14:00:00Z`. |
| `backend/tests/test_entradas_no_validas.py` | `test_solicitud_que_termina_despues_de_la_ultima_fecha_admitida[un_segundo_despues_del_limite]` | 24 h | Igual. | Parametrizar también el inicio: `9999-12-30T20:00:01Z`, con el mismo fin. |
| `backend/tests/test_entradas_no_validas.py` | `...[ultimo_segundo]` | 48 h | Igual. | Inicio `9999-12-31T20:00:00Z`, con el mismo fin. |
| `backend/tests/test_entradas_no_validas.py` | `...[desfase_negativo]` | 47 h | Igual. | Inicio `9999-12-31T20:00:00Z`, con el mismo fin. |
| `backend/tests/test_entradas_no_validas.py` | `test_la_ultima_fecha_admitida_se_lee_en_la_zona_con_mayor_desfase` | 24 h | Espera 201, recibe 400. | Inicio `9999-12-30T20:00:00Z` y el mismo fin, de modo que dure 4 h exactas y siga probando la última fecha admitida. |
| `backend/tests/test_readme.py` | `test_el_catalogo_de_errores_coincide_con_el_implementado` | n/a | En la simulación, la excepción nueva existía y la tabla del README no la listaba. | No se modifica la prueba: el código se documenta en la misma tarea que lo registra (tarea 2.1), de modo que no llega a fallar. |

Los ajustes solo cambian datos de entrada: ninguna expectativa de esas pruebas cambia y siguen probando lo mismo. Se aplican antes que la regla (tarea 1.1), porque los datos ajustados duran como máximo 4 horas y pasan tanto con el código actual como con la regla. Las demás pruebas que crean rangos largos no pasan por la creación (disponibilidad, historial y siembras directas en el repositorio) y no se ven afectadas.

**Frontend.** La búsqueda en `frontend/src/**/*.test.*` no encontró solicitudes de más de 4 horas: `CreacionSolicitud.test.jsx` usa 2 h y los listados, como máximo 2 h. El único rango largo es el filtro de un mes de `ConsultaHistorial.test.jsx`, que no se limita. Además, estas pruebas simulan `fetch` y no ejercitan la regla, así que ninguna necesita ajuste. La suite de Vitest no se ejecutó para este análisis, porque la regla no toca el frontend; se ejecuta en la regresión final.

### (c) Frontend

`FormularioSolicitud.jsx` muestra `mensajeDeError(fallo)`, que devuelve el mensaje del servidor para cualquier código distinto de `permiso_insuficiente`, y no valida en el navegador. El código nuevo funciona, por tanto, sin cambios funcionales.

**Sí hace falta añadir un escenario en `interfaz-web`.** «Mensajes de error de la creación» enumera los códigos y, sin un escenario nuevo, `duracion_excedida` quedaría sin requisito ni fila en la matriz de trazabilidad. Añadir un escenario a un requisito existente exige expresarlo como MODIFIED, y es el único cambio de ese requisito. El escenario fija además que la duración no se valida en el navegador, para que la regla siga en un solo lugar. Cambios: un caso de Vitest y el comentario de cabecera de `FormularioSolicitud.jsx`, que enumera los códigos.

## Risks / Trade-offs

- [Fallos transitorios durante la implementación] → Fallos transitorios admitidos: ninguno. El orden de `tasks.md` deja la suite en verde al terminar cada tarea: los datos de las pruebas se ajustan antes de la regla (tarea 1.1) y el código de error se documenta en la misma tarea que lo registra (tarea 2.1). Cualquier fallo detiene la implementación.
- [Un cambio futuro podría mover la regla a `validar_rango`] → Las pruebas de alcance con rangos de más de 4 horas en disponibilidad e historial lo detectarían.
- [Clientes que reciben otro código de error para el mismo defecto] → Una solicitud de más de 4 horas con inicio pasado o espacio inexistente cambia de código. Es el comportamiento definido y queda documentado en el README.
- [La simulación no es la implementación] → El análisis (b) es una predicción fuerte, no una garantía. La regresión final lo confirma; si aparece una prueba no listada, se detiene y se describe.
- [Reservas de más de 4 horas sin migración] → Pueden seguir existiendo y aprobarse. Es una decisión explícita; el sistema aún no tiene datos en producción.

## Migration Plan

No aplica: sin migración ni cambios de datos. Revertir la regla consiste en retirar la comprobación, la constante y el código de error.

## Open Questions

Ninguna. La posición de la tarea de ajuste de pruebas quedó **confirmada por el estudiante**: es la primera tarea de implementación (1.1), antes de registrar el error y de implementar la regla.
