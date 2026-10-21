# PLAN_INGENIERIA — Sistema de reservas de espacios académicos

**Autor:** José Fernando Rubio Morales
**Fecha:** 20 de octubre de 2026

---

## 1. Análisis del problema

### 1.1 Identificación de la problemática

La institución gestiona las reservas de laboratorios, auditorios y salas de cómputo mediante correos electrónicos y hojas de cálculo. Esto genera:

- **Duplicidad de solicitudes:** varias personas piden el mismo espacio por canales distintos.
- **Conflictos de horario:** no hay un mecanismo que impida dos reservas simultáneas sobre el mismo espacio.
- **Disponibilidad difícil de consultar:** la información está dispersa y desactualizada.
- **Falta de trazabilidad:** no hay un historial confiable de quién reservó, quién aprobó y qué se canceló.

### 1.2 Necesidades de la institución

- Centralizar las reservas en una única fuente de verdad.
- Consultar la disponibilidad en tiempo real.
- Garantizar que no existan reservas solapadas sobre un mismo espacio.
- Controlar quién puede solicitar, aprobar y administrar.
- Conservar un historial auditable de solicitudes, decisiones y cancelaciones.
- Poder incorporar nuevas reglas de negocio sin reescribir el sistema (por ejemplo, límites de duración).

### 1.3 Actores involucrados

| Actor | Rol en el sistema |
|---|---|
| **Solicitante** (docente, estudiante autorizado, personal) | Consulta disponibilidad, crea solicitudes, cancela las propias, ve su historial |
| **Administrador de espacios / aprobador** | Aprueba o rechaza solicitudes, gestiona espacios |
| **Administrador del sistema** | Gestiona usuarios, roles y permisos |
| **Institución** (stakeholder) | Define las reglas de negocio y sus cambios |

El sistema manejará tres roles: `solicitante`, `aprobador` y `admin`.

### 1.4 Alcance

**Incluye:** gestión de espacios, usuarios, roles y permisos, solicitudes de reserva, validación de disponibilidad, prevención de reservas simultáneas, aprobación y rechazo, cancelación e historial.

### 1.5 Limitaciones (fuera de alcance)

- No incluye pagos ni integración con sistemas académicos externos (matrícula, horarios de clase).
- No incluye notificaciones por correo ni aplicación móvil nativa.
- No gestiona inventario de equipos dentro de los espacios.
- Se asume una sola sede y una zona horaria.
- Despliegue en entorno local o de demostración, no en producción institucional.

---

## 2. Propuesta de solución

### 2.1 Descripción general

Aplicación web que centraliza la gestión de reservas de espacios académicos. Un frontend en React consume una API REST en Flask, que aplica las reglas de negocio y persiste en PostgreSQL. La base de datos garantiza que dos reservas aprobadas no puedan solaparse sobre el mismo espacio.

Toda solicitud nace en estado `pendiente` y requiere la decisión de un aprobador (`aprobada` o `rechazada`), sin aprobación automática para ningún tipo de espacio.

### 2.2 Funcionalidades prioritarias

| Prioridad | Funcionalidad | Por qué va en ese lugar |
|---|---|---|
| 1 | Autenticación, usuarios, roles y permisos | Todo lo demás depende de saber quién actúa |
| 2 | Gestión de espacios | Sin espacios no hay qué reservar |
| 3 | Solicitudes de reserva y validación de disponibilidad | Núcleo del sistema |
| 4 | Prevención de reservas simultáneas | Problema crítico de la institución |
| 5 | Aprobación y rechazo | Completa el flujo de la solicitud |
| 6 | Cancelación e historial | Trazabilidad |

### 2.3 Módulos del sistema

- **auth:** login, sesiones o tokens, control de permisos por rol.
- **usuarios:** registro y administración de usuarios y roles.
- **espacios:** CRUD de laboratorios, auditorios y salas (tipo, capacidad, estado).
- **reservas:** solicitudes, disponibilidad, conflictos, cancelación.
- **aprobaciones:** decisión del aprobador y registro de quién decidió y cuándo.
- **historial:** consulta de reservas pasadas y cambios de estado.

### 2.4 Estrategia de desarrollo progresivo

Desarrollo por **incrementos verticales**: cada incremento entrega una funcionalidad completa (base de datos, API, interfaz y pruebas) antes de pasar a la siguiente, siguiendo el orden de prioridad de la tabla. Así siempre hay una versión funcional y verificable, y la regla de las cuatro horas se podrá incorporar sin romper lo existente.

---

## 3. Decisiones de arquitectura y tecnología

### 3.1 Arquitectura: monolito modular en capas

Un solo despliegue en Flask, organizado por módulos (`auth`, `usuarios`, `espacios`, `reservas`, `aprobaciones`, `historial`). Cada módulo se divide en tres capas: **rutas** (HTTP), **servicios** (reglas de negocio) y **repositorios** (acceso a datos). Las reglas, como la de las cuatro horas, viven en la capa de servicios, así un cambio de regla toca un solo lugar.

### 3.2 Stack tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | React |
| Backend | Python + Flask (API REST) |
| ORM y migraciones | SQLAlchemy + Alembic |
| Base de datos | PostgreSQL |
| Autenticación | JWT |
| Pruebas | pytest (backend), Vitest + React Testing Library (frontend) |

### 3.3 Estrategia de persistencia

PostgreSQL con tablas `usuarios`, `roles`, `espacios`, `reservas` e `historial_reservas`. La prevención de reservas simultáneas se delega a la base de datos con una **restricción de exclusión** (`EXCLUDE USING gist`) sobre el rango de tiempo por espacio, de modo que ni dos peticiones concurrentes puedan crear un solapamiento.

### 3.4 Comparación de decisiones técnicas

| Decisión | Elegida | Alternativa descartada | Justificación |
|---|---|---|---|
| Arquitectura | Monolito modular | Microservicios | Proyecto individual y acotado; los microservicios añaden complejidad operativa sin beneficio |
| Base de datos | PostgreSQL | SQLite / MongoDB | Se necesita integridad transaccional y restricciones de exclusión de rangos, que SQLite no ofrece y MongoDB no garantiza igual |
| Backend | Flask | Django / FastAPI | Flask da control sobre la estructura en capas y es el framework con el que más experiencia hay, lo que reduce el riesgo al revisar código generado por IA |
| Prevención de solapamientos | Restricción en la base de datos | Validación solo en el código | El código solo no es seguro ante concurrencia: dos peticiones simultáneas pasarían la validación |
| Autenticación | JWT | Sesiones con cookie | Encaja con una API REST consumida por React y es más simple de probar con pytest |

---

## 4. Estrategia de desarrollo

### 4.1 Metodología de trabajo

Proceso **iterativo e incremental con tablero Kanban en GitHub Projects**, combinado con SDD: cada incremento sigue el ciclo *especificar → revisar la especificación → implementar → probar → registrar el commit*. Al ser un proyecto individual, Scrum completo (roles, ceremonias) no aporta; Kanban con límite de trabajo en curso (una funcionalidad a la vez) sí. El tablero vive junto al repositorio y refuerza la trazabilidad del proceso.

### 4.2 Etapas, orden y criterio de terminado

| Etapa | Contenido | Depende de | Se considera terminada cuando |
|---|---|---|---|
| 0 | Plan de ingeniería | n/a | `PLAN_INGENIERIA.md` en commit independiente |
| 1 | Specs con OpenSpec y revisión | Etapa 0 | Specs consistentes, sin ambigüedades, alineadas con el plan, tareas definidas |
| 2 | Base del proyecto: repo, estructura de módulos, conexión a PostgreSQL, migraciones | Etapa 1 | La app arranca y las migraciones se aplican |
| 3 | Auth, usuarios, roles y permisos | Etapa 2 | Login con JWT y control por rol, con pruebas en verde |
| 4 | Gestión de espacios | Etapa 3 | CRUD protegido por rol, con pruebas |
| 5 | Solicitudes, disponibilidad y prevención de solapamientos | Etapa 4 | Escenarios de aceptación pasan, incluida una prueba de concurrencia |
| 6 | Aprobación/rechazo, cancelación e historial | Etapa 5 | Flujo completo de estados verificado |
| 7 | Frontend React | Etapas 3 a 6 (se construye en paralelo a cada una) | Cada pantalla consume su endpoint y cubre sus escenarios |
| 8 | Cambio de regla (máximo 4 horas) | Etapa 6 | Spec actualizada, pruebas nuevas y regresión sin fallos |
| 9 | Verificación y cierre | Todas | Pruebas ejecutadas, `README.md` e `INFORME_FINAL.md` listos |

### 4.3 Dependencias clave

`auth` es la base de todo; `espacios` es requisito de `reservas`; `aprobaciones` e `historial` dependen del modelo de estados de `reservas`.

---

## 5. Estrategia de calidad

### 5.1 Tipos de pruebas

| Tipo | Qué verifica | Herramienta |
|---|---|---|
| Unitarias | Reglas de negocio en la capa de servicios (duración, estados, permisos) | pytest |
| Integración | Endpoints de la API contra una base PostgreSQL de pruebas | pytest + cliente de pruebas de Flask |
| Concurrencia | Que dos reservas simultáneas sobre el mismo espacio no se solapen | pytest con hilos sobre PostgreSQL real |
| Frontend | Flujos clave: login y crear reserva | Vitest + React Testing Library |
| Regresión | Que el cambio de las cuatro horas no rompa lo existente | Suite completa en cada commit |
| Aceptación | Cada escenario de las specs de OpenSpec tiene al menos una prueba | pytest, nombrada según el escenario |

### 5.2 Riesgos y mitigación

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | La IA implementa funcionalidades no especificadas o incorrectas | Revisión de cada cambio contra su spec; commits pequeños y pruebas antes de aceptar |
| 2 | Condiciones de carrera permiten reservas solapadas | Restricción de exclusión en PostgreSQL y prueba de concurrencia |
| 3 | Especificaciones ambiguas o contradictorias | Fase de revisión obligatoria antes de implementar; contraste con este plan |
| 4 | Zonas horarias o límites de rango mal manejados (una reserva que termina cuando otra empieza) | Guardar en UTC, rangos semiabiertos `[inicio, fin)` y pruebas de casos límite |
| 5 | El cambio de regla de las cuatro horas rompe funcionalidades existentes | Análisis de impacto, spec actualizada primero y regresión completa |
| 6 | Falta de tiempo antes de la entrega | Incrementos verticales por prioridad: lo esencial queda funcional primero |
| 7 | Fallos de seguridad en roles y JWT | Pruebas de permisos por rol y de expiración de tokens |

### 5.3 Verificación del cumplimiento de requisitos

Una **matriz de trazabilidad** enlaza requisito de OpenSpec → escenario → prueba → commit. Antes del cierre, todo requisito debe tener al menos una prueba en verde.

---

## 6. Uso de SDD e inteligencia artificial

### 6.1 ¿Cómo se utilizará OpenSpec?

OpenSpec será la **fuente de verdad** del comportamiento del sistema. Las especificaciones viven en el repositorio y todo cambio funcional pasa por el mismo ciclo: **proponer → revisar → implementar → archivar**. Nada se programa sin una spec revisada, y las modificaciones (como la regla de las cuatro horas) se registran como cambios en OpenSpec antes de tocar el código. El agente de IA de programación será **OpenCode**.

### 6.2 ¿Cómo se transforma este plan en especificaciones?

Cada módulo de la sección 2.3 se convierte en una especificación (`auth`, `usuarios`, `espacios`, `reservas`, `aprobaciones`, `historial`). Cada funcionalidad se expresa como **requisitos** verificables con **escenarios de aceptación** (condición inicial, acción, resultado esperado). Las decisiones de este plan, como la aprobación obligatoria, los tres roles y los rangos `[inicio, fin)`, se vuelven restricciones explícitas en las specs, y la fase de revisión comprueba que ninguna las contradiga.

### 6.3 Actividades delegadas a la IA

| Se delega a OpenCode | Se mantiene bajo control del estudiante |
|---|---|
| Borradores de especificaciones a partir de este plan | Aprobación final de cada spec |
| Código de módulos, rutas, servicios y componentes según las tareas | Arquitectura, stack y estructura de capas |
| Migraciones y borradores de pruebas | Reglas de negocio y alcance |
| Documentación base (README, informe) | Decisión de aceptar, modificar o rechazar cada cambio |

### 6.4 ¿Cómo se verificará el código generado?

- Revisión del *diff* contra la spec antes de cada commit; lo que no esté en la spec se elimina.
- Ejecución de la suite de pruebas y revisión de que cada escenario tenga su prueba (matriz de trazabilidad).
- Commits pequeños y atómicos, uno por tarea, para poder auditar el historial.
- Verificación manual de los casos críticos: solapamientos, permisos y límites de rango.

### 6.5 Decisiones que son responsabilidad del estudiante

Arquitectura y stack, alcance, reglas de negocio, contenido final de las specs, análisis de impacto de los cambios, aceptación del código y la sustentación del sistema. La IA propone y ejecuta; el estudiante decide y responde por el resultado.
