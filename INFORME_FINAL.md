# INFORME\_FINAL — Sistema de reservas de espacios académicos

José Fernando Rubio Morales · Documento vivo: se actualiza durante todo el proyecto

## 1. Estado del proceso

- **Etapa 1 (plan de ingeniería):** completa. `PLAN_INGENIERIA.md` está en el repositorio.
- Etapa 2, Fases 1 y 2 completas: los cinco changes están commiteados, validados y revisados entre sí. La implementación asistida (Fase 3) se completó después.
- **Etapas 3 a 8 completas: los seis changes (cinco originales y limite-duracion-reserva) están implementados, verificados, archivados y con sus 8 specs publicadas. Pendiente: README raíz, tablero Kanban, conclusión y sustentación oral**.

## 2. Cronología verificable en Git

| Orden | Commit | Mensaje | Qué demuestra |
| --- | --- | --- | --- |
| 1 | `d6285b0` | `docs: plan de ingeniería inicial` | El plan precede a las especificaciones |
| 2 | `b267e8d` | `chore: inicializar OpenSpec` | OpenSpec se inicializó después del plan |
| 3 | `dbe6305` | `spec: propuesta usuarios-roles-auth` | Primera propuesta, ya revisada tres veces antes del commit |
| 4 | `e18cdb4` | `spec: ajuste de orden y dependencias de tareas en usuarios-roles-auth` | Defectos de orden de tareas corregidos antes de implementar (H10, H11) |
| 5 | `5276ed5` | `spec: errores del framework, permiso espacios:activar y ajustes de redacción en usuarios-roles-auth` | Hallazgos H19 y H22 corregidos antes de implementar |
| 6 | `e04ce2f` | `spec: propuesta espacios` | Segunda propuesta, con los hallazgos H15 a H21 ya corregidos |
| 7 | ae3970f | spec: propuesta reservas-disponibilidad | Tercera propuesta, con los hallazgos H23 a H29 ya corregidos a mano (cupo gratuito de OpenCode agotado) |
| 8 | 81047d1 | spec: ajuste design reservas-disponibilidad | design.md alineado con las specs y las tareas (H30) |
| 9 | 1567455 | spec: propuesta aprobacion-reservas | Cuarta propuesta, redactada y revisada manualmente con el asistente conversacional porque el cupo gratuito de OpenCode seguía agotado; incluye la prueba de aprobaciones simultáneas (H12) |
| 10 | fe0d581 | spec: propuesta cancelacion-historial | Quinta y última propuesta; historial atómico e inmutable (disparador en la base de datos) y cancelación con análisis de concurrencia cancelar/aprobar |
| 11 | eb451b4 | spec: unificar criterio de inicio en aprobacion-reservas | Hallazgo H31 de la revisión cruzada corregido antes de implementar |
| 12 | 5bf214a | spec: unificar criterio de inicio en reservas-disponibilidad | Cierre de la revisión cruzada: los cinco changes comparten el criterio de «ya comenzó» |
| 13 | 1a9a6ab | chore: agregar .gitignore | Protección de secretos y dependencias antes de generar código (Fase 3) |
| 14 | 8d2519b | docs: reglas de trabajo para el agente de implementación | CLAUDE.md con las reglas del agente: no modificar artefactos, detenerse ante contradicciones, no commitear, no exponer secretos |
| 15 | 8d8dc41 | spec: JWT\_SECRET\_KEY obligatoria en todos los entornos en usuarios-roles-auth | Hallazgo H34 detectado por el agente durante la implementación; la especificación se corrige antes de continuar con el código |
| 16 | 3a79345 | feat(auth): base del proyecto (sección 1 de usuarios-roles-auth) | Primer código del proyecto, posterior a todas las especificaciones; 21 pruebas de backend y 1 de frontend en verde |
| 17 | a2d768d | spec: algoritmo de hash por defecto de Werkzeug en usuarios-roles-auth | Hallazgo H35 detectado por el agente; la especificación se corrige antes de implementar la tarea |
| 18 | d50687e | feat(auth): modelos Rol y Usuario, migración inicial y repositorio (tareas 2.1 y 2.2) | Esquema de roles y usuarios con migraciones reversibles y base de pruebas preparada desde cero en cada sesión |
| 19 | 1b898b1 | feat(auth): hash de contraseñas, correo en minúsculas e índice único por lower(correo) (tareas 2.3 a 2.5) | Cierre de la sección 2; 33 pruebas de backend en verde |
| 20 | 317cb3f | spec: alinear D7 con los errores del framework en usuarios-roles-auth | Corrección de design.md hallada por el agente al implementar la sección 3 (H38); commit aparte del código |
| 21 | 9472367 | feat(auth): errores, token JWT, guard y login (sección 3 de usuarios-roles-auth) | Cierre de la sección 3 con Claude Code; 86 pruebas de backend en verde; 12 archivos |
| 22 | c65c9c0 | feat(auth): matriz de permisos y guard por permiso (sección 4 de usuarios-roles-auth) | Matriz de 20 permisos verificada celda por celda contra la spec; 186 pruebas en verde |
| 23 | 150e108 | feat(usuarios): gestión de cuentas y catálogo de roles (sección 5 de usuarios-roles-auth) | 8 endpoints, README del backend y ajuste del PATCH tras revisión (H41); 322 pruebas en verde |
| 24 | 9b62725 | spec: fijar en D9 las entradas y el nombre de create-admin en usuarios-roles-auth | Corrección de design.md (D9 y Open Questions) antes del código; resuelve H44 y H45 |
| 25 | 22e291a | feat(usuarios): comando create-admin para el primer administrador (sección 6 de usuarios-roles-auth) | Cierre de la sección 6; 341 pruebas de backend en verde, 19 nuevas |
| 26 | 0de884c | spec: alinear el escenario de datos de acceso inválidos de interfaz-web con el backend | Corrección de spec hallada por el agente al empezar la sección 7 (H47) |
| 27 | 377e265 | spec: aclarar en D12 que el frontend usa el rol solo para mostrar secciones | Corrección de design.md (D12) antes del código del frontend (H48) |
| 28 | 005a096 | feat(frontend): sesión, login y rutas protegidas (sección 7 de usuarios-roles-auth) | Cierre de la sección 7; 25 pruebas de frontend en verde y build correcto; 16 archivos |
| 29 | 7c561d8 | feat(frontend): administración de usuarios (sección 8 de usuarios-roles-auth) | Cierre de la sección 8; 48 pruebas de frontend en verde; contraseñas en campos no controlados (leidas de una ref, nunca en el estado de React) |
| 30 | 1a9b03d | spec: recoger en D10 y D12 las decisiones del frontend (VITE\_API\_URL, token y 401) | Corrección de design.md y CLAUDE.md surgida de la revisión 9.3 (H52) |
| 31 | b0c942f | test: verificación y matriz de trazabilidad de usuarios-roles-auth (sección 9) | Cierre de la sección 9: 24 requisitos y 90 escenarios con prueba en verde; 342 pruebas de backend y 48 de frontend |
| 32 | d9b700b | docs: completar el commit de la prueba de vigencia en la matriz | Matriz de trazabilidad sin filas pendientes |
| 33 | 3bbc513 | docs: documentar la puesta en marcha del backend y del frontend | Tras la prueba manual contra el backend real, que mostró la laguna de documentación (H54) |
| 34 | d791130 | chore(openspec): archivar usuarios-roles-auth y publicar sus specs | Cierre del change 1: 24 requisitos publicados en openspec/specs (9 auth, 10 usuarios, 5 interfaz-web); validate --all --strict con 7 de 7 en verde |
| 35 | 9064d93 | feat(espacios): modelo, migración y repositorio (sección 1 de espacios) | Change 2 (espacios), sección 1: tabla con tres CHECK e índice único lower(btrim(nombre)) declarado con text() en el modelo; migración 0003 con downgrade verificado; 360 pruebas de backend en verde |
| 36 | 08159a7 | feat(espacios): errores y servicios del catálogo (sección 2 de espacios) | Sección 2: seis códigos de error nuevos y servicios de alta, consulta, edición y cambios de estado; 481 pruebas de backend en verde |
| 37 | 4ea3b2a | feat(espacios): rutas de la API y documentación de endpoints (sección 3 de espacios) | API del catálogo de espacios con su documentación; sección 3 del change 2 |
| 38 | 5e9f0d0 | feat(espacios): interfaz web y verificación (secciones 4 y 5 de espacios) | Cierre del código del change 2: interfaz web y matriz de trazabilidad |
| 39 | acd51a9 | chore(openspec): archivar espacios y publicar su spec | Cierre del change 2: la spec de espacios pasa a openspec/specs |
| 40 | 7519869 | feat(reservas): persistencia, servicios y API de reservas (secciones 1 a 4 de reservas-disponibilidad) | Change 3: solicitudes, restricción EXCLUDE sobre reservas aprobadas y disponibilidad |
| 41 | acf861c | feat(reservas): interfaz de solicitudes, disponibilidad y trazabilidad (secciones 5 y 6 de reservas-disponibilidad) | Interfaz del change 3 y filas de la matriz de trazabilidad |
| 42 | 304a67e | chore(openspec): archivar reservas-disponibilidad, publicar specs y actualizar matriz de trazabilidad | Cierre del change 3 |
| 43 | 364eb26 | docs(openspec): corregir proposal y design de aprobacion-reservas | Artefactos corregidos antes de implementar el change 4 |
| 44 | e12e17a | feat(aprobaciones): servicio de decisión, API y pruebas de concurrencia (secciones 1 a 5 de aprobacion-reservas) | Aprobar y rechazar con bloqueo de filas; pruebas de decisiones simultáneas (H62) |
| 45 | dc83a55 | feat(aprobaciones): acciones de aprobar y rechazar en la interfaz y trazabilidad (secciones 6 y 7 de aprobacion-reservas) | Interfaz del change 4 y matriz de trazabilidad |
| 46 | 218dbba | chore(openspec): archivar aprobacion-reservas, publicar specs y actualizar matriz de trazabilidad | Cierre del change 4 |
| 47 | d478e5c | docs(openspec): corregir proposal y design de cancelacion-historial | Artefactos corregidos antes de implementar el change 5 |
| 48 | dfab30e | feat(historial): historial inmutable, cancelaciones y pruebas de concurrencia (secciones 1 a 6 de cancelacion-historial) | Historial con disparador de inmutabilidad (H65) y cancelación con prueba cancelar/aprobar |
| 49 | 961c28e | feat(historial): cancelación y consulta de historial en la interfaz y trazabilidad (secciones 7 y 8 de cancelacion-historial) | Interfaz del change 5 y matriz de trazabilidad |
| 50 | 62f04a6 | chore(openspec): archivar cancelacion-historial, publicar specs y actualizar matriz de trazabilidad | Cierre del change 5: las cinco specs originales quedan publicadas |
| 51 | 901cc53 | fix: respuesta de decisión, fechas fuera de rango y caracteres NUL en nombres de espacios | Correcciones tras la revisión y el barrido de peticiones (H63, H64) |
| 52 | 33b9fae | fix: respuesta de creación y entradas no válidas (NUL, sustitutos, identificadores y JSON anidado) sin errores 500 | Segunda ronda del barrido: ninguna entrada hostil produce 500 (H64) |
| 53 | 267506a | fix: rechazar caracteres de control y no ASCII en fechas ISO 8601 | Tercera ronda: convertir\_fecha estricta (H64) |
| 54 | 4ddf7f0 | docs(openspec): proponer limite-duracion-reserva (cambio de regla de las cuatro horas, etapa 8) | Cambio de regla posterior a la entrega inicial: el proceso SDD se repite completo (propuesta, specs, código, archivo) |
| 55 | 76fc7a2 | feat(reservas): duración máxima de 4 horas en la creación de solicitudes (secciones 1 a 4 de limite-duracion-reserva) | Regla implementada con constante DURACION\_MAXIMA y 400 duracion\_excedida (H68) |
| 56 | 1edb441 | feat(reservas): mensaje de duración excedida en la interfaz y trazabilidad (secciones 5 y 6 de limite-duracion-reserva) | Mensaje del servidor en la interfaz y filas de la matriz |
| 57 | 59eaa8e | chore(openspec): archivar limite-duracion-reserva, publicar specs y actualizar matriz de trazabilidad | Cierre del sexto change; 8 specs publicadas, 1388 pruebas de backend y 178 de frontend en verde |

## 3. Hallazgos de la revisión de especificaciones (Fase 2)

| # | Hallazgo | Corrección |
| --- | --- | --- |
| H1 | La spec `auth` incluía escenarios de otros módulos (aprobar, gestionar espacios, crear solicitudes, historial). No eran verificables en el primer change y duplicaban lo que dirán los changes posteriores | La spec `auth` define solo la jerarquía y la matriz de permisos; cada change prueba sus propios permisos |
| H2 | Contradicción: el token transportaba el rol y a la vez se decía que no se confiaba en él | El token lleva solo identificador, emisión y expiración; el rol se lee siempre de la base de datos |
| H3 | Faltaba la excepción «nadie decide sus propias solicitudes»: aprobador y admin heredan de solicitante y podían aprobar las propias | Regla declarada en la matriz y verificada en `aprobacion-reservas` |
| H4 | El formato de errores era incompleto (sin 404 ni 409) y mencionaba un código sin escenario | Aplica a toda la API, con códigos 400, 401, 403, 404 y 409 y un escenario por cada uno |
| H5 | Escenarios no verificables (vigencia «sin reiniciar los datos», mensajes sin «detalle técnico») | Eliminados o reformulados con criterios comprobables |
| H6 | Contradicción entre documentos: el plan (1.3) dice que el aprobador gestiona espacios, pero el prompt inicial del change `espacios` lo asignaba solo al admin | Se corrigió el prompt según el plan: aprobador y admin gestionan espacios |
| H7 | Ubicación de la cancelación: la sección 2.3 del plan la ponía en el módulo `reservas`, pero la tabla de etapas la agrupa con aprobación e historial | Change propio `cancelacion-historial`, porque ambos dependen del modelo de estados |
| H8 | Ambigüedad del plan: no decía qué reservas bloquean un espacio | Solo las reservas aprobadas ocupan el espacio; las pendientes pueden solaparse entre sí |
| H9 | Tareas sin requisito que las respaldara (comando `create-admin`, todo el frontend) | Nuevo requisito en `usuarios` y nueva spec pequeña `interfaz-web` |
| H10 | Dependencias rotas en `tasks.md`: login probado antes de existir el hash, pruebas de endpoints de usuarios antes de implementarlos, manejador de errores al final, pruebas de repositorio antes de la migración | Reordenamiento de tareas para que cada una dependa solo de las anteriores |
| H11 | Huecos de infraestructura no cubiertos por ninguna spec funcional: driver de PostgreSQL y CORS entre React y Flask | Tareas explícitas con verificación (`psycopg`, `flask-cors`, variable `CORS_ORIGINS`) |
| H12 | La prueba de concurrencia estaba asignada al change equivocado: con la regla de H8, crear solicitudes solapadas no es conflicto; la concurrencia relevante es la aprobación simultánea | La restricción de la base de datos se verifica a nivel de repositorio en `reservas-disponibilidad`; la prueba de aprobaciones simultáneas va en `aprobacion-reservas` |
| H13 | Solapamiento de permisos `reservas:ver_*` e `historial:ver_*` en la matriz | `reservas` es el estado actual de las solicitudes; `historial` es el registro de cambios de estado |
| H14 | La regla «un espacio inactivo no admite solicitudes» no se puede probar en el change `espacios`, porque las solicitudes aún no existen | Se trasladó a `reservas-disponibilidad` |

### Hallazgos del change `espacios`

| # | Hallazgo | Corrección |
| --- | --- | --- |
| H15 | Contradicción entre la spec y las tareas: la spec de edición exige validar «campos obligatorios», pero la tarea 2.4 define una edición parcial (PATCH) | Edición parcial: los campos omitidos no cambian y los enviados se validan; escenario nuevo para la edición de un solo campo |
| H16 | La spec permite desactivar espacios pero no reactivarlos, y el nombre es único incluso entre inactivos: un espacio desactivado por error queda bloqueado y su nombre no se puede reutilizar | Permiso nuevo `espacios:activar` en la matriz y requisito de reactivación (decisión del estudiante pendiente) |
| H17 | La tarea 3.3 dice que la edición no acepta cambios de estado, pero ningún escenario define qué ocurre si la petición incluye el campo `estado` | Escenario: la petición se rechaza con `datos_invalidos` y el estado no cambia |
| H18 | Ambigüedad entre campo ausente y valor vacío: «capacidad vacía» daba `capacidad_invalida` y «capacidad faltante» daba `datos_invalidos` | Ausente produce `datos_invalidos`; presente pero nulo, vacío, decimal o texto produce `capacidad_invalida` |
| H19 | El requisito «todas las respuestas de error de la API son JSON» no cubría los errores del framework (ruta inexistente, método no permitido, cuerpo JSON mal formado, error interno), que por defecto devuelven HTML | Escenarios y tarea nuevos en `usuarios-roles-auth` con códigos `ruta_no_encontrada`, `metodo_no_permitido` y `error_interno` |

### Hallazgos en las propuestas (`proposal.md`)

| # | Hallazgo | Corrección |
| --- | --- | --- |
| H20 | La propuesta de `espacios` nombraba un change inexistente (`historial-reservas`); el nombre real es `cancelacion-historial` | Referencia corregida |
| H21 | La IA especuló sobre un efecto de la capacidad en reservas ya aprobadas, que no existe: las solicitudes no llevan número de asistentes. Es un ejemplo de regla inventada | Frase eliminada de la pregunta abierta |
| H22 | La propuesta de `usuarios-roles-auth` no mencionaba los errores del framework (H19), usaba un término sin sentido («autodominio de contraseña») y atribuía el hash a Flask en lugar de a Werkzeug | Propuesta alineada con las specs y redacción corregida |

### Hallazgos del change `reservas-disponibilidad`

| # | Hallazgo | Corrección |
| --- | --- | --- |
| H23 | La restricción de exclusión usa `espacio_id WITH =` dentro de un índice `gist`, lo que exige la extensión `btree_gist` de PostgreSQL. La migración no la creaba y habría fallado al aplicarse | La migración ejecuta `CREATE EXTENSION IF NOT EXISTS btree_gist` y se verifica en las bases de desarrollo y de pruebas |
| H24 | Las pruebas de rechazo por solapamiento, disponibilidad y listado necesitan reservas aprobadas, pero la aprobación no existe hasta el change `aprobacion-reservas`; además «inicio en el pasado» depende del reloj | Las reservas aprobadas se siembran directamente en el repositorio y las pruebas usan un reloj inyectable |
| H25 | El catálogo cerrado de estados de una reserva no tenía requisito que respaldara la tarea 1.1 | Requisito nuevo «Catálogo de estados de una reserva» |
| H26 | Faltaban escenarios clave: campos faltantes, el solicitante enviado en el cuerpo, otro espacio sin conflicto, solapamiento parcial o por contención, pendientes solapadas permitidas por la base de datos, rango de disponibilidad inválido y espacio inexistente en la disponibilidad | Escenarios añadidos a la spec `reservas` |
| H27 | La consulta de disponibilidad no tenía permiso definido en la matriz (no existe `disponibilidad:ver`) | Decisión del estudiante: la puede consultar cualquier usuario autenticado con `espacios:ver`, y el resultado no revela al solicitante |
| H28 | La spec de `interfaz-web` no cubría los errores del servidor ni el envío de fechas con zona horaria, tenía un escenario con dos pares WHEN/THEN y un requisito mal redactado | Escenarios y redacción corregidos, sin superar los 3 requisitos |
| H29 | Las tareas no registraban los códigos de error nuevos, ni documentaban los endpoints, ni actualizaban la matriz de trazabilidad, y usaban abreviaturas que dificultan la trazabilidad; la propuesta no tenía «Fuera de alcance» ni mencionaba `btree_gist` | Tareas y propuesta completadas con los nombres completos de los requisitos |
| H30 | El design.md generado por la IA no mencionaba btree\_gist, dejaba la restricción como «o equivalente», usaba «inicio>=ahora» (la spec dice que un inicio en el pasado es inválido) y omitía espacio\_inactivo, la forma de la disponibilidad, la ausencia de paginación y el reloj inyectable | design.md reescrito y alineado con proposal, specs y tareas; commit aparte |

### Hallazgos de la revisión cruzada de los cinco changes

Verificación mecánica: todos los permisos y códigos de error usados en los changes 3, 4 y 5 están definidos en un change anterior; los 16 archivos de los changes 3, 4 y 5 se comprobaron por huella contra la versión revisada.

| # | Hallazgo | Corrección |
| --- | --- | --- |
| H31 | Criterio inconsistente de «ya comenzó»: la cancelación trataba el inicio igual al instante actual como iniciado, pero aprobar y crear lo permitían, lo que dejaba una solicitud que no se podía aprobar ni cancelar | Criterio único: ya comenzó si el inicio es anterior o igual al momento actual, en creación, aprobación y cancelación, con escenario de borde en cada spec |
| H32 | Error del asistente al escribir la concurrencia de cancelar y aprobar: se afirmó que exactamente una operación tiene éxito, pero si la aprobación entra primero ambas responden 200 en secuencia | Escenario reescrito: la cancelación responde 200, el estado final es cancelada y la aprobación responde 200 o 409 transicion\_invalida |
| H33 | Estados HTTP distintos para códigos parecidos: espacio\_ya\_inactivo y espacio\_ya\_activo responden 409, espacio\_inactivo responde 400 | Se mantiene por decisión: es una solicitud no procesable sobre un recurso inactivo y no un conflicto de estado repetido; queda documentado para la sustentación |
| H34 | Detectado durante la implementación: la tarea de config.py decía «entorno no local» sin que ningún artefacto definiera qué es un entorno local, y el design.md hablaba de un valor de desarrollo para la clave JWT y de fallar si la clave «es el valor por defecto». El agente se detuvo en lugar de inventar un criterio, como exige CLAUDE.md | JWT\_SECRET\_KEY obligatoria en todos los entornos, sin valor por defecto ni de desarrollo; si falta o está vacía la app falla con un mensaje explícito. Las pruebas definen su propia clave. Corrección de design.md (D4 y riesgos) y de la tarea 1.3, commiteada antes de seguir con el código |
| H35 | Detectado durante la implementación: el design.md (D6) afirmaba que Werkzeug usa PBKDF2 por defecto, pero la versión instalada (3.1.9) usa scrypt. El texto provenía de una versión anterior de la librería. El agente se detuvo en lugar de elegir | Se usa el algoritmo por defecto de Werkzeug sin indicarlo en el código, y la verificación lee el algoritmo del propio hash. Se descartó fijar PBKDF2 porque alarga las pruebas sin ganar seguridad real. D6 corregido y commiteado antes de la tarea |
| H36 | Hallazgo de implementación: el modelo Usuario declaraba el índice único sobre lower(correo) como texto literal y no como expresión sobre la columna, por lo que el modelo y la migración quedaban desalineados sin que ninguna prueba lo detectara | El agente lo corrigió con una expresión SQL sobre la columna y verificó que coincide con la migración |
| H37 | Riesgo conocido: la sesión de PostgreSQL devuelve las fechas en la zona horaria del servidor (America/Bogota). El instante almacenado es correcto y está en UTC, pero las specs exigen respuestas en UTC | Resuelto en las secciones que devuelven fechas: todas las respuestas se serializan en UTC con sufijo Z, y la interfaz las muestra en UTC |
| H38 | D7 de design.md listaba solo los códigos HTTP 400, 401, 403, 404 y 409, mientras la spec de auth y la tarea 3.1 exigen además ruta\_no\_encontrada (404), metodo\_no\_permitido (405) y error\_interno (500). Lo detectó el agente al implementar | Resuelto: modificación excepcional autorizada de design.md (solo D7), validación estricta en verde, commit 317cb3f antes del código |
| H39 | proposal.md (línea 12) sigue enumerando 400, 401, 403, 404 y 409 sin 405 ni 500, aunque añade que el formato cubre también los errores del framework | Aceptado sin cambios: incompleto pero no contradictorio; spec y D7 son la fuente de verdad. Se evita tocar más artefactos |
| H40 | Limitaciones conocidas de la sección 3, fuera de la spec: (1) el login responde más rápido con un correo inexistente que con contraseña incorrecta, lo que permitiría deducir correos por tiempos; (2) el esquema Bearer en minúsculas se rechaza; (3) JWT\_ACCESS\_TOKEN\_MINUTES acepta valores menores o iguales a 0 | Documentadas para la sustentación. Mitigación posible de (1): verificación de hash ficticia cuando el correo no existe |
| H41 | El agente decidió que el PATCH de usuarios ignorara en silencio los campos no editables (activo, contrasena). Un cliente podría creer que desactivó una cuenta recibiendo 200, e incoherente con reservas, donde un campo de solicitante en el cuerpo se rechaza | Resuelto en la revisión: 400 datos\_invalidos ante cualquier campo fuera de nombre, correo y rol; el cuerpo vacío devuelve 200 sin cambios; 4 pruebas nuevas y README actualizado |
| H42 | Carrera entre administradores: si dos admins se desactivan entre sí a la vez, cada transacción ve al otro activo, ambas pasan la aserción de D7 y quedan cero administradores activos. La aserción también desaparece con python -O | Limitación aceptada: improbable y recuperable con el comando de primer administrador (sección 6). Barrera real posible: bloquear las filas de admins al desactivar |
| H43 | El restablecimiento de contraseña no invalida los tokens ya emitidos (sin refresh ni lista de revocación): siguen válidos hasta su exp, 60 minutos como máximo. La desactivación sí surte efecto de inmediato porque el guard lee la base de datos en cada petición | Limitación documentada para la sustentación; la mitigación sería una versión de sesión en el usuario comprobada al verificar el token |
| H44 | Hueco de especificación hallado por el agente: usuarios.nombre es obligatorio, pero D9 y la spec dicen que create-admin solo lee correo y contraseña. Además, design.md dejaba abierta la pregunta de los nombres de las variables de entorno | Resuelto: nombre fijo Administrador (editable después por PATCH) y variables ADMIN\_CORREO y ADMIN\_CONTRASENA; fijado en D9 en el commit 9b62725 |
| H45 | La opción propuesta por el agente incluía --contrasena en la línea de comandos, que dejaría la contraseña en el historial del shell y en la lista de procesos. D9 decía también argumentos o variables | Corregido: la contraseña solo se lee de ADMIN\_CONTRASENA o de un prompt oculto con confirmación; no existe --contrasena y hay prueba de ello. D9 alineado con lo implementado |
| H46 | Mejora menor: create-admin pide la contraseña antes de comprobar si ya existe un administrador activo, por lo que en terminal interactiva se teclea la contraseña para recibir luego el aviso | Aceptado sin cambios: sin riesgo de seguridad; mejora posible comprobando antes el administrador activo |
| H47 | Contradicción entre la spec interfaz-web y el backend ya implementado: el escenario de datos de acceso inválidos exigía mostrar datos\_invalidos también ante un correo mal formado, pero el login devuelve credenciales\_invalidas en ese caso (y no debe distinguir correos inexistentes de mal escritos) | Resuelto corrigiendo la spec, no el backend: el frontend no valida el formato del correo, envía siempre al servidor y muestra el código devuelto. Commit 0de884c |
| H48 | Tensión entre D12 (el control de permisos no se reimplementa en el frontend, la sección se oculta por el 403) y la tarea 7.3 y la spec interfaz-web (proteger la administración por rol en el frontend) | Resuelto alineando D12: la interfaz usa el rol de GET /api/auth/me solo para decidir qué secciones mostrar, sin replicar la matriz; la autorización real sigue siendo el 403 del backend. Commit 377e265 |
| H49 | Huecos de especificación del frontend: dónde guardar el token, qué enrutado usar sin dependencias nuevas y de dónde sale la URL del backend | Decididos por el estudiante sin editar artefactos: sessionStorage (limitación: legible ante XSS; alternativa cookie HttpOnly, fuera de alcance); enrutado propio con window.history en un módulo único, a reevaluar cuando lleguen espacios y reservas; VITE\_API\_URL con rutas relativas por defecto y sin .env |
| H50 | Fallo hallado en la revisión del frontend: si sessionStorage no está disponible, guardarToken fallaba en silencio y el login dejaba de funcionar, porque la llamada siguiente a /api/auth/me leía un token nulo. El comentario del código afirmaba lo contrario | Corregido antes del commit: el token también se guarda en una variable del módulo; 2 pruebas nuevas con almacenamiento que lanza error. La corrección rompió 5 pruebas por falta de aislamiento (la variable no la limpia sessionStorage.clear) y se arregló limpiando el token en el afterEach de los tres archivos afectados |
| H51 | Limitación: al restaurar la sesión tras una recarga, cualquier error de /api/auth/me (corte de red o error 500, además del 401) cierra la sesión y borra el token | Aceptada para este change. Mejora posible: distinguir el 401 de los demás errores y mostrar un aviso de conexión sin borrar el token. La prueba manual posterior mostró que no se avisa de la sesión caducada (ver H55) |
| H52 | La revisión 9.3 contra las specs encontró código y decisiones del frontend que no estaban en design.md: VITE\_API\_URL, la copia del token en memoria, que cualquier 401 con token cierra la sesión, y errores HTTP fuera de 400, 404, 405 y 500 sin formato JSON (no alcanzables con el código actual) | Resuelto: las tres primeras se documentaron en D10, D12 y CLAUDE.md (commit 1a9b03d); la cuarta se aceptó como limitación y consta en la matriz de trazabilidad |
| H53 | La matriz de trazabilidad detectó que el escenario Vigencia configurada solo se probaba al nivel de la emisión del token, no en el recorrido del login | Resuelto: prueba nueva del login con JWT\_ACCESS\_TOKEN\_MINUTES=5 que comprueba expira\_en = 300 (commit b0c942f). Hash completado en la matriz (commit d9b700b) |
| H54 | La prueba manual con el backend real mostró que el README del backend no documentaba cómo aplicar las migraciones ni cómo arrancar el servidor, y que el ejemplo de generación de la clave del token no funcionaba en PowerShell 5.1 (RandomNumberGenerator.Fill no existe y la línea dejaba una clave de ceros) | Resuelto: sección Puesta en marcha en los dos README (commit 3bbc513) con la clave generada con secrets.token\_urlsafe y la contraseña de la base pedida con Read-Host oculto |
| H55 | Con un token inválido guardado, la interfaz descarta el token y vuelve al login en silencio, sin avisar de que la sesión caducó. Cumple D12 y la spec, que no exigen aviso. El paso de la prueba manual que borraba el token por completo no probaba ese caso, porque no hay petición con token | Aceptado. Mejora de usabilidad posible en un change futuro: aviso de sesión caducada |
| H56 | Tras archivar usuarios-roles-auth, docs/matriz-trazabilidad.md sigue citando las specs en openspec/changes/usuarios-roles-auth/specs, ruta que ya no existe; además los proposals de los cuatro changes pendientes dicen que interfaz-web no está publicada | Resuelto: la matriz apunta a openspec/specs al archivar cada change. Los proposals no se tocan: solo añaden requisitos con nombres distintos y validate --all --strict pasa |
| H57 | Espacios: la spec y D3/D4 solo rechazan el campo estado en la edición; cualquier otro campo extra (id, desconocidos) se ignoraría en silencio, la misma trampa de H41. Tampoco se especificaban el PATCH con cuerpo vacío ni el nombre que no es texto | Decidido por el estudiante sin editar artefactos, coherente con usuarios: cualquier campo fuera de nombre, tipo y capacidad da 400 datos\_invalidos en el alta y la edición; el cuerpo vacío da 200 sin cambios; el nombre que no es texto da datos\_invalidos |
| H58 | Hueco hallado por el agente: la capacidad no tiene límite superior en la spec, pero la columna INTEGER de PostgreSQL rechaza valores mayores que 2147483647 con un error que llegaba al cliente como 500 error\_interno | Resuelto: 400 capacidad\_invalida para capacidades por encima de 2147483647, como límite técnico y no regla de negocio; el sistema no impone un aforo máximo porque el plan no lo define. Pruebas en 2147483647 y 2147483648 |
| H59 | Acoplamiento entre tests: test\_readme.py (tarea 5.7 de usuarios) exige que la tabla de errores del README coincida con el catálogo implementado, así que registrar códigos nuevos deja la suite en rojo hasta documentarlos (tarea 3.6 de espacios) | Resuelto adelantando solo la tabla de los seis códigos al README, sin tocar la prueba de usuarios. Observación: ocurrirá igual en los changes siguientes; la tabla de errores se documenta en la misma sección que los registra |
| H60 | Limitación de concurrencia en espacios: dos desactivaciones (o reactivaciones) simultáneas del mismo espacio pueden responder ambas 200 en lugar de 200 y 409, porque no hay bloqueo de fila. El estado final es correcto | Aceptada: la spec no exige lo contrario. En aprobacion-reservas la fila sí se bloqueará con SELECT FOR UPDATE |
| H61 | La traza larga de pytest (--tb por defecto) volcó en el log del agente la cadena de conexión con la contraseña de PostgreSQL | Contraseña rotada con \\password en psql; las pruebas se ejecutan con --tb=short. Mejora posible: fijarlo en addopts |
| H62 | Aprobaciones simultáneas sobre un mismo espacio producían interbloqueo (SQLSTATE 40P01) con FOR UPDATE; el análisis de diseño del asistente no lo había previsto | Se bloquea la solicitud con FOR UPDATE y el espacio con FOR NO KEY UPDATE, y el SQLSTATE 23P01 de la restricción EXCLUDE se traduce a 409 reserva\_solapada; prueba de concurrencia en verde |
| H63 | La respuesta de aprobar mostraba el estado cancelada cuando una cancelación concurrente se confirmaba entre la escritura y la lectura de la respuesta | La respuesta se arma antes del commit (expunge) con el estado que escribió esta transacción; prueba nueva |
| H64 | Un barrido de unas 950 peticiones hostiles halló respuestas 500: OverflowError por fechas fuera de rango, caracteres NUL y sustitutos, JSON anidado e identificadores mayores que el INTEGER de PostgreSQL | Validación compartida en backend/app/validaciones.py: fechas fuera de rango y caracteres de control dan 400 y los identificadores enormes dan 404; sin 500 en el barrido y con pruebas de regresión |
| H65 | El historial es inmutable por un disparador BEFORE UPDATE OR DELETE, que no bloquea TRUNCATE ni al propietario de la tabla | Limitación documentada. Verificación manual el 2026-11-05 en la base de desarrollo: UPDATE y DELETE rechazados con «historial\_reservas es inmutable» y el conteo de filas sin cambios (4) |
| H66 | Decisiones de forma de respuesta no cubiertas en la spec: motivo\_rechazo solo aparece cuando la solicitud está rechazada (máximo 500 caracteres) y los parámetros de consulta desconocidos se ignoran, igual que en disponibilidad | Decididas por el estudiante y cubiertas por pruebas |
| H67 | Excepción a la regla de no validar en el cliente: el frontend exige un motivo no vacío al rechazar, porque lo pide la spec de interfaz-web | Aceptada y limitada a ese caso; en el resto el frontend muestra el mensaje del servidor |
| H68 | Regla de 4 horas (limite-duracion-reserva): la duración se calcula sin truncar microsegundos y la precedencia del fin máximo en UTC solo constaba en design.md, no en la spec | Máximo de 4 horas inclusive (constante DURACION\_MAXIMA), 400 duracion\_excedida tras validar el rango; escenarios de borde en 4 h exactas y 4 h más un microsegundo |
| H69 | validate --all --strict falló porque un requisito de spec/reservas superaba los 500 caracteres (advertencia tratada como error) | Texto acortado a 468 caracteres sin cambiar el significado; 8 specs en verde |
| H70 | Limitaciones menores de las pruebas manuales y el barrido: no hay MAX\_CONTENT\_LENGTH, el mensaje de create-admin induce a error, la cancelación no pide confirmación, el mensaje de transicion\_invalida es impreciso, espacio\_inactivo al aprobar dice «no admite solicitudes» y el actor se muestra por id | Aceptadas y documentadas para la sustentación; ninguna incumple un requisito de las specs |
| H71 | Incoherencias documentales: el encabezado de la matriz de trazabilidad conservaba el texto «hasta que se archive» y PLAN\_INGENIERIA.md (línea 182) aún nombra a OpenCode como agente, aunque la implementación se hizo con Claude Code | Encabezado de la matriz corregido; el cambio de agente consta en este informe y se aclarará en la sustentación |
| H72 | Pruebas con fechas fijas de 2026 frente a fechas reales: al avanzar el calendario las reservas quedan en el pasado; además un fallo intermitente de Vitest apareció una vez y no se reprodujo | Las pruebas calculan las fechas respecto al momento actual; el fallo intermitente queda anotado como no reproducido |

## 4. Decisiones del plan que cambiaron o se precisaron

| Plan original | Decisión posterior | Motivo |
| --- | --- | --- |
| Módulo `reservas` incluía la cancelación (2.3) | La cancelación va con el historial en su propio change | H7 |
| La autenticación con JWT no precisaba el contenido del token | Token sin rol; rol leído de la base de datos en cada petición | H2 |
| Tres roles sin jerarquía definida | Jerarquía admin ⊇ aprobador ⊇ solicitante | Modelo más simple de explicar y de probar |
| Stack sin driver ni CORS | Se añaden `psycopg[binary]` y `flask-cors` | H11 |
| Frontend React sin especificación propia | Capability `interfaz-web`, limitada a comportamiento observable | H9 |
| Cálculo de ocupación no definido | Solo las reservas aprobadas ocupan un espacio | H8 |

## 5. Decisiones de diseño tomadas por el estudiante

- Sin autoregistro: el administrador crea las cuentas, y el primer administrador se crea por línea de comandos.
- Token de 60 minutos configurable, sin refresh token.
- Contraseña de mínimo 8 caracteres, sin reglas de composición.
- Un único rol por usuario; login por correo, único sin distinguir mayúsculas.
- Sin tabla de auditoría de usuarios: el historial exigido es el de reservas.
- El administrador no puede desactivarse ni cambiar su propio rol.
- Toda solicitud nace pendiente y requiere aprobación, para todos los tipos de espacio.
- PostgreSQL local (versión 17), sin Docker.
- Tablero Kanban en GitHub Projects.
- Pruebas de frontend ligeras (login y crear reserva) además de pytest en el backend.

* Al aprobar una solicitud, las demás solicitudes pendientes que se solapan con ella no cambian de estado: siguen pendientes y, si se intenta aprobarlas, fallan por conflicto; el aprobador puede rechazarlas manualmente. Se evaluó el rechazo automático y se descartó: es irreversible si la reserva aprobada se cancela después y añade complejidad (transacción atómica y eventos adicionales en el historial).

## 6. Dificultades encontradas

| Dificultad | Causa probable | Solución |
| --- | --- | --- |
| El comando `opencode` no existía en la terminal | OpenSpec solo generó los archivos de comandos; el programa no estaba instalado | Instalación con `npm install -g opencode-ai` |
| Pantalla negra al abrir la interfaz de OpenCode y error de base de datos al ejecutar comandos | Base de datos local de OpenCode a medio crear tras un primer arranque interrumpido; coexistían la aplicación de escritorio y la versión de terminal | Cierre del servicio en segundo plano, respaldo de la base de datos con otro nombre y reinicio |
| Contraseña de PostgreSQL olvidada | n/a | Cambio temporal del método de autenticación local, nueva contraseña y restauración de la configuración original |
| Comprobar que el pegado de textos largos funciona en la terminal de Windows | Reportes de fallos de pegado en terminales de Windows | Prueba previa sin enviar el mensaje; funcionó |
| Cupo gratuito de OpenCode agotado («Free usage exceeded») durante varios días, incluso después de la fecha de regeneración, y errores EPERM/EEXIST al reinstalar | Límite del modelo gratuito y servicio en segundo plano de OpenCode bloqueando archivos durante la reinstalación | Detención del servicio, reinstalación de opencode-ai (1.19.5) y corrección manual de los artefactos del change 3 con el asistente conversacional; decisión de proveedor propio (/connect) para la implementación |
| Archivo ya commiteado (proposal.md de espacios) apareció modificado en git status | Un espacio en blanco añadido al inicio de la primera línea al abrir el archivo; sin cambio de contenido | Revisión con git diff y descarte con git restore antes de commitear, para mantener un commit por cambio |
| La API gratuita de Gemini permite solo 20 solicitudes diarias por modelo, insuficiente para un agente de programación que consume una solicitud por cada paso | Límite del nivel gratuito de la API, distinto de la suscripción Gemini Pro de estudiante, que cubre la aplicación y no la API | Se cambió el agente de implementación a Claude Code (plan Claude Pro), conservando OpenSpec, las tareas y la revisión por secciones |

## 7. Uso de la inteligencia artificial

- **Agente de programación:** OpenCode con el modelo por defecto (Big Pickle), mediante los comandos `/opsx-propose`, `/opsx-apply` y `/opsx-archive`.
- **Qué hizo bien:** ante ambigüedades dejó «Preguntas abiertas» con un valor por defecto en lugar de inventar reglas; las especificaciones pasaron la validación estricta.
- **Dónde necesitó corrección:** generó escenarios válidos individualmente pero inconsistentes entre sí o con el orden de implementación (H1, H2, H10); no incluyó infraestructura necesaria (H11).
- **Cómo se evitaron implementaciones incorrectas:** revisión humana de cada artefacto contra el plan, validación con `openspec validate --strict`, instrucciones explícitas de no inventar reglas, y revisión de que cada tarea corresponda a un requisito.
- **Asistente conversacional:** se usó también para redactar el plan de ingeniería y revisar las especificaciones; las decisiones finales las tomó el estudiante.
- Cambio de agente: la implementación pasó de OpenCode a Claude Code por agotamiento del cupo gratuito. El profesor confirmó el 2026-11-05 que no hay inconveniente.

## 8. Respuestas preliminares para la sustentación

| Pregunta | Material disponible hasta ahora |
| --- | --- |
| ¿Qué decisiones de ingeniería tomó antes de programar? | Sección 5 y el propio plan |
| ¿Qué problemas identificó al transformar su propuesta en especificaciones? | Hallazgos H1 a H29 (sección 3) |
| ¿Cómo evitó que la IA implementara funcionalidades incorrectas? | Sección 7: revisión, validación estricta, trazabilidad |
| ¿Qué diferencias encontró entre la planificación inicial y la implementación final? | Sección 4; se completa tras la Fase 3 |
| ¿Qué ventajas y limitaciones tiene SDD con OpenSpec frente a instrucciones directas a una IA? | Sección 10; se completa al cierre |

## 9. Resultados de pruebas y trazabilidad

Resultado al archivar el sexto change (commit 59eaa8e): 1388 pruebas de backend y 178 de frontend en verde, compilación correcta, migraciones 0001 a 0009, validate --all --strict con 8 specs en verde y matriz de trazabilidad en docs/matriz-trazabilidad.md sin filas pendientes. Recorrido manual completo el 2026-11-05 contra el backend real: creación de usuarios y espacio, solicitudes solapadas, rechazo de 5 horas, aprobación, conflicto, rechazo con motivo, cancelación, disponibilidad, historial con filtros y prueba de inmutabilidad en psql.

## 10. Conclusiones sobre SDD (observaciones preliminares)

- **Ventaja observada:** la revisión de las especificaciones detectó defectos de consistencia, alcance y orden de dependencias antes de escribir código.
- **Limitación observada:** el costo de revisión es alto, porque la IA produce especificaciones correctas por separado pero necesitan contrastarse entre sí y con el plan.
- Conclusión final: el sistema quedó completo y verificado: seis changes archivados, 8 specs publicadas, 1388 pruebas de backend y 178 de frontend en verde, y un historial de Git que muestra el orden plan, specs, código y archivo. Las pruebas de concurrencia, el barrido de peticiones hostiles y el recorrido manual encontraron fallos (interbloqueo, respuestas 500, lectura posterior al commit) que las specs no habían anticipado, por lo que la verificación independiente de lo que genera la IA fue tan importante como la especificación. El cambio de regla de las cuatro horas se absorbió repitiendo el ciclo SDD completo en un change nuevo, sin tocar los anteriores. Quedan limitaciones aceptadas y documentadas (sección 3), ninguna incumple un requisito.
