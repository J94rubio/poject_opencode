# Sistema de reservas de espacios académicos

Proyecto individual de Ingeniería de Software (Fundación Universitaria Uninpahu). Sistema web para reservar laboratorios, auditorios y salas de cómputo, con un flujo de solicitud y aprobación, desarrollado con **Spec-Driven Development (SDD)** usando **OpenSpec** y un agente de programación con IA.

## Qué hace

- Gestión de cuentas con tres roles jerárquicos: `solicitante`, `aprobador` y `admin`.
- Catálogo de espacios académicos (laboratorio, auditorio, sala de cómputo) con alta, edición, desactivación y reactivación.
- Solicitudes de reserva que nacen `pendiente` y solo ocupan el espacio cuando un aprobador las aprueba.
- Prevención de solapamientos con una restricción de exclusión en la base de datos.
- Aprobación y rechazo con motivo, cancelación por el solicitante e historial inmutable de cambios de estado.
- Duración máxima de 4 horas por solicitud (`400 duracion_excedida` si se supera).
- Consulta de disponibilidad por espacio y de historial con filtros (espacio, estado, rango de fechas).
- Interfaz con estilos modernos: modo claro y oscuro automático e insignias de estado.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python, Flask, SQLAlchemy 2.x, Alembic, PyJWT, flask-cors |
| Base de datos | PostgreSQL 17 (`reservas` y `reservas_test`) |
| Frontend | React, Vite, Vitest y React Testing Library |
| Metodología | OpenSpec (SDD) |
| Arquitectura | Monolito modular en capas: rutas → servicios → repositorios |

## Metodología: plan, specs e implementación

El historial de Git refleja el orden del proceso:

1. **Plan:** `PLAN_INGENIERIA.md` fija el alcance, la arquitectura y las decisiones.
2. **Specs:** cada incremento se especifica con OpenSpec (`proposal`, `design`, specs con escenarios y `tasks`) y se valida con `openspec validate <change> --strict` antes de escribir código.
3. **Implementación asistida:** un agente de IA implementa las tareas de cada change, sección por sección, con las reglas de `CLAUDE.md`. Cada artefacto generado se revisa antes de hacer commit.
4. **Archivado:** al terminar un change se archiva y sus specs pasan a `openspec/specs/`.

## Estructura del repositorio

```text
backend/        API Flask, migraciones Alembic y pruebas pytest
frontend/       Interfaz React con pruebas Vitest
openspec/       specs publicadas (specs/), changes pendientes y archivados (changes/)
docs/           matriz de trazabilidad requisito → escenario → prueba
CLAUDE.md       reglas de trabajo del agente de programación
```

## Puesta en marcha

Las instrucciones completas están en `backend/README.md` y `frontend/README.md`. Resumen, en PowerShell, desde la raíz del repositorio:

1. Crear y activar el entorno virtual e instalar `backend/requirements.txt`.
2. Definir **solo en la terminal** `DATABASE_URL`, `CORS_ORIGINS` y `JWT_SECRET_KEY`. Ninguna contraseña ni clave se escribe en archivos del repositorio.
3. Aplicar las migraciones: `alembic -c backend/alembic.ini upgrade head`.
4. Crear el primer administrador con `flask --app backend.app create-admin`, definiendo `ADMIN_CORREO` en la terminal; la contraseña viene de `ADMIN_CONTRASENA` o de un prompt oculto. Detalles en `backend/README.md`.
5. Arrancar el backend: `flask --app backend.app run --port 5000`.
6. En `frontend/`: definir `VITE_API_URL`, ejecutar `npm install` y `npm run dev`.

## Pruebas

- Backend: `python -m pytest backend`, contra la base `reservas_test` (variable `TEST_DATABASE_URL`).
- Frontend: `npm test` dentro de `frontend/`.
- Trazabilidad: `docs/matriz-trazabilidad.md` enlaza cada requisito con sus escenarios y sus pruebas.

## Decisiones y limitaciones conocidas

Las decisiones de diseño están en el `design.md` de cada change (archivado en `openspec/changes/archive/`). Limitaciones asumidas; las tres últimas son de `estilos-interfaz` y las demás están documentadas en el informe final:

- El token JWT vive en `sessionStorage` y es legible por un script malicioso (XSS).
- Cambiar la contraseña no invalida los tokens ya emitidos; caducan a los 60 minutos como máximo.
- Dos administradores que se desactivan entre sí a la vez podrían dejar el sistema sin administradores activos; se recupera con `flask create-admin`.
- El enrutado del frontend es propio, sin dependencias, y se reevaluará cuando crezca el número de pantallas.
- El disparador que hace inmutable `historial_reservas` bloquea UPDATE y DELETE, pero no TRUNCATE ni al propietario de la tabla.
- No hay límite de tamaño del cuerpo de las peticiones (`MAX_CONTENT_LENGTH`) y la cancelación no pide confirmación en la interfaz.
- Las horas se muestran en UTC en la interfaz.
- La tabla de solicitudes necesita scroll horizontal, dentro de su tarjeta, en anchos menores a unos 1200 px.
- En Safari, las tablas sin botones pueden no desplazarse con el teclado.
- La navegación no marca el enlace de la página actual.

## Estado de los changes

| Change | Estado |
|---|---|
| `usuarios-roles-auth` | Implementado y archivado |
| `espacios` | Implementado y archivado |
| `reservas-disponibilidad` | Implementado y archivado |
| `aprobacion-reservas` | Implementado y archivado |
| `cancelacion-historial` | Implementado y archivado |
| `limite-duracion-reserva` | Implementado y archivado (cambio de regla, etapa 8) |
| `estilos-interfaz` | Implementado y archivado (etapa 9) |

Resultado de la verificación final: 9 specs publicadas en `openspec/specs/` (`openspec validate --all --strict` en verde), 1388 pruebas de backend y 300 de frontend en verde, migraciones 0001 a 0009 y matriz de trazabilidad sin filas pendientes.

## Uso de IA

La implementación se hizo con un agente de programación (OpenCode al inicio y Claude Code después, por agotamiento de la cuota gratuita; el profesor confirmó que el cambio no era problema). El estudiante revisó cada artefacto y cada sección antes de hacer commit, y el INFORME_FINAL registra los hallazgos y las correcciones de esa revisión.

## Autor

José Fernando Rubio Morales, Ingeniería de Software, Fundación Universitaria Uninpahu.
