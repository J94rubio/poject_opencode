# Tasks

## 1. Base del proyecto

- [x] 1.1 Crear la estructura de carpetas del backend (`backend/app`, `backend/app/auth`, `backend/app/usuarios`, `backend/app/models`, `backend/migrations`, `backend/tests`) y verificar que la app factory arranca sin error con `flask --app backend.app run`.
- [x] 1.2 Declarar las dependencias del backend (Flask, SQLAlchemy, Alembic, PyJWT, pytest, `psycopg[binary]` como driver de PostgreSQL y flask-cors) en `backend/requirements.txt` y verificar que `pip install -r backend/requirements.txt` completa sin errores y que `python -c "import psycopg, flask_cors"` no falla.
- [x] 1.3 Implementar `backend/app/config.py` con `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_MINUTES` con valor por defecto de 60, `PASSWORD_MIN_LENGTH` con valor de 8 y la URL de la base de datos leídos del entorno, y verificar con una prueba que arrancar sin `JWT_SECRET_KEY` (ausente o vacía) falla con un mensaje explícito, en cualquier entorno.
- [x] 1.4 Crear la base de datos PostgreSQL de desarrollo `reservas` y exponer su URL en la variable de entorno `DATABASE_URL`, y verificar que la conexión con `DATABASE_URL` responde a una consulta de comprobación.
- [x] 1.5 Configurar la app factory en `backend/app/__init__.py` (extensiones, blueprints, manejadores de errores) y verificar que la conexión a PostgreSQL responde con una consulta de comprobación.
- [x] 1.6 Crear la base de datos PostgreSQL dedicada de pruebas `reservas_test`, exponer su URL en la variable de entorno `TEST_DATABASE_URL`, configurar `backend/tests/conftest.py` para usarla y verificar que `pytest` se ejecuta sin errores de collection.
- [x] 1.7 Crear el proyecto React con Vite y Vitest en `frontend/`, con la configuración de pruebas de Vitest lista, y verificar que `npm install` completa sin errores, que `npm test` ejecuta la suite de Vitest sin fallos de collection y que el origen de desarrollo del frontend (el servidor de Vite) puede llamar al backend sin bloqueo de CORS, con la lista de orígenes permitidos definida en la configuración del backend y leída del entorno (variable `CORS_ORIGINS`).

## 2. Modelo de datos y migraciones

- [ ] 2.1 Implementar los modelos `Rol` y `Usuario` en `backend/app/models/` con la relación, el rol único por usuario, el estado `activo` y las marcas de tiempo en UTC, y verificar que los modelos se importan sin error y que sus metadatos declaran las tablas `roles` y `usuarios`, la clave foránea y el rol único por usuario.
- [ ] 2.2 Crear la migración Alembic que genera las tablas `roles` y `usuarios` con clave foránea, índices y columnas `TIMESTAMP WITH TIME ZONE`, e inserta los tres roles del catálogo; verificar que `alembic upgrade head` y `alembic downgrade base` funcionan sobre una base vacía, que `backend/tests/conftest.py` prepara el esquema de la base `reservas_test` con `alembic upgrade head` antes de las pruebas de repositorio, y que con ese esquema ya preparado una prueba de repositorio verifica que un usuario se persiste y se recupera con su rol.
- [ ] 2.3 Implementar el hash y la verificación de contraseñas con las utilidades de Werkzeug (incluidas con Flask), y verificar con pruebas que el valor almacenado difiere de la contraseña en texto plano, que la verificación con la contraseña correcta resulta exitosa y que dos cuentas con la misma contraseña almacenan valores distintos.
- [ ] 2.4 Normalizar el correo a minúsculas en la capa de repositorios y verificar con una prueba de repositorio que el correo se guarda en minúsculas.
- [ ] 2.5 Añadir en una migración separada el índice único funcional sobre `lower(correo)` y verificar con una prueba que el alta de dos cuentas con el mismo correo en distinto caso es rechazada por la base de datos.

## 3. Autenticación con JWT

- [ ] 3.1 Implementar el manejador de errores de la API con el formato `{"error": {"codigo", "mensaje"}}` y verificar con pruebas que cada excepción de dominio produce su código HTTP y su código de error, y que el mensaje no filtra correo, contraseña ni detalle técnico; además cubrir con rutas de prueba registradas únicamente en los tests la ruta inexistente (404, `ruta_no_encontrada`), el método no permitido (405, `metodo_no_permitido`), el cuerpo JSON mal formado (400, `datos_invalidos`) y el error interno no controlado (500, `error_interno` con mensaje fijo sin detalle técnico ni traza).
- [ ] 3.2 Implementar la emisión del token de acceso en `backend/app/auth/tokens.py` con los claims `sub`, `iat` y `exp` —sin rol ni `jti`— y la vigencia por defecto de 60 minutos, y verificar con una prueba que el token contiene únicamente esos tres claims y expira según la vigencia configurada.
- [ ] 3.3 Implementar la verificación del token con los códigos `token_ausente`, `token_invalido` y `token_expirado`, y verificar con pruebas para token ausente, cabecera mal formada, firma inválida y token expirado, usando en las pruebas una ruta protegida de prueba registrada únicamente en los tests, porque la primera ruta protegida real llega con `GET /api/auth/me`.
- [ ] 3.4 Implementar la carga del usuario y de su rol vigente en cada petición protegida, y verificar con una prueba, sobre esa misma ruta protegida de prueba registrada únicamente en los tests, que el rol efectivo cambia en la siguiente petición tras un cambio de rol, sin reautenticarse, porque la primera ruta protegida real llega con `GET /api/auth/me`.
- [ ] 3.5 Implementar el servicio y la ruta de login con los códigos `credenciales_invalidas` y `usuario_desactivado`, y verificar con pruebas de credenciales válidas, de login con el correo en mayúsculas, contraseña incorrecta, correo inexistente, cuenta desactivada y datos de acceso incompletos.
- [ ] 3.6 Implementar la ruta `GET /api/auth/me` y verificar con pruebas de token válido, petición sin token y token expirado.

## 4. Matriz de permisos

- [ ] 4.1 Implementar en `backend/app/auth/permissions.py` la tabla de permisos por rol con la jerarquía `admin` ⊇ `aprobador` ⊇ `solicitante`, y verificar con una prueba unitaria que cada rol tiene exactamente los permisos de la matriz declarada en la spec `auth` (y en `design.md`, D2) y que cada rol incluye la totalidad de los del anterior.
- [ ] 4.2 Implementar el guard que exige un permiso y produce `permiso_insuficiente` con HTTP 403, y verificar con pruebas de acceso permitido y de acceso denegado por rol.

## 5. Gestión de usuarios

- [ ] 5.1 Implementar el servicio de alta de usuario con las validaciones de nombre, correo, contraseña (mínimo 8 caracteres, sin reglas de composición) y rol, y verificar con pruebas de alta válida, correo duplicado, correo de formato inválido, campos faltantes, rol inválido, contraseña de menos de 8 caracteres y contraseña sin mayúsculas, dígitos ni símbolos.
- [ ] 5.2 Implementar el listado y el detalle de usuarios, y verificar con pruebas del listado con cuentas desactivadas, del detalle existente, del detalle inexistente con HTTP 404 y de la denegación por rol.
- [ ] 5.3 Implementar la edición de nombre, correo y rol, y verificar con pruebas de cambio válido, de correo duplicado, de rol inválido, de denegación por rol y de rechazo del cambio del propio rol con el código `operacion_no_permitida`.
- [ ] 5.4 Implementar el restablecimiento de contraseña, y verificar con pruebas de restablecimiento válido, de contraseña con menos de 8 caracteres y de denegación por rol.
- [ ] 5.5 Implementar la desactivación y la activación de cuentas con la pérdida de acceso inmediata y la conservación de los datos de la cuenta, y verificar con pruebas de desactivación, de reactivación, de desactivación de otro administrador, de denegación por rol y de autoadministración rechazada con HTTP 409.
- [ ] 5.6 Exponer la ruta `GET /api/roles` y verificar con pruebas del catálogo con los tres roles y de denegación por rol.
- [ ] 5.7 Documentar en `backend/README.md` los endpoints del módulo `usuarios` y el catálogo de códigos de error, y verificar que los ejemplos del documento coinciden con las rutas y los códigos implementados.
- [ ] 5.8 Verificar con pruebas que la matriz respeta la jerarquía de roles, que un `solicitante` y un `aprobador` reciben HTTP 403 con `permiso_insuficiente` al intentar listar, crear, editar o desactivar usuarios, y que un `admin` sí puede crear una cuenta, comprobando que los datos quedan intactos tras cada denegación.

## 6. Arranque con el primer administrador

- [ ] 6.1 Implementar el comando `flask create-admin` que crea la cuenta administradora inicial desde argumentos o variables de entorno, y verificar con pruebas de creación correcta, de fallo con error explícito cuando ya existe un administrador activo, de validación de la contraseña y de correo inválido o duplicado, sin que ninguna de esas cuentas se cree (requisito «Creación del primer administrador por línea de comandos» de la spec `usuarios`).

## 7. Frontend: autenticación y sesión

- [ ] 7.1 Implementar el cliente HTTP de React con el envío del token y el tratamiento diferenciado de 401 y 403, y verificar con una prueba Vitest que un 401 con `token_expirado` vuelve a la pantalla de inicio de sesión y que un 403 con `permiso_insuficiente` muestra un mensaje sin cerrar la sesión (requisitos «Ciclo de vida de la sesión» y «Mensaje de error por permisos insuficientes» de la spec `interfaz-web`).
- [ ] 7.2 Implementar la pantalla de login y el contexto de autenticación (guardar token, restaurar sesión, cerrar sesión), y verificar con pruebas Vitest del inicio de sesión correcto, de credenciales inválidas, de cuenta desactivada y de datos inválidos, de restauración de la sesión al recargar y de cierre de sesión (requisitos «Pantalla de inicio de sesión» y «Ciclo de vida de la sesión» de la spec `interfaz-web`).
- [ ] 7.3 Implementar la protección de rutas por sesión y por rol en el frontend, y verificar con pruebas Vitest que sin sesión se redirige al login, que un `solicitante` no alcanza la sección de administración y que un `admin` sí la alcanza (requisito «Protección de las rutas de la aplicación» de la spec `interfaz-web`).

## 8. Frontend: administración de usuarios

- [ ] 8.1 Implementar la pantalla de listado de usuarios con su estado activo o inactivo y las acciones de editar, desactivar y reactivar, y verificar con pruebas Vitest del renderizado y de que cada acción llama al endpoint correspondiente (requisito «Pantallas de administración de usuarios» de la spec `interfaz-web`).
- [ ] 8.2 Implementar el formulario de alta y de edición con los mensajes de error del servidor (`correo_duplicado`, `rol_invalido`, `contrasena_invalida`, `datos_invalidos`, `operacion_no_permitida`), y verificar con pruebas Vitest de cada mensaje de error y del alta correcta (requisito «Pantallas de administración de usuarios» de la spec `interfaz-web`).
- [ ] 8.3 Implementar el formulario de restablecimiento de contraseña y verificar con pruebas Vitest del envío correcto y de la respuesta con el error `contrasena_invalida` (requisito «Pantallas de administración de usuarios» de la spec `interfaz-web`).

## 9. Verificación integral

- [ ] 9.1 Ejecutar la suite completa de `pytest` y de `Vitest` contra la base PostgreSQL de pruebas `reservas_test` y verificar que todas las pruebas quedan en verde.
- [ ] 9.2 Construir la matriz de trazabilidad requisito → escenario → prueba en `docs/matriz-trazabilidad.md` y verificar que cada requisito de las specs `auth`, `usuarios` e `interfaz-web` tiene al menos una prueba en verde, como exige la sección 5.3 del plan.
- [ ] 9.3 Revisar el diff completo contra las specs `auth`, `usuarios` e `interfaz-web` y verificar que no queda ninguna funcionalidad implementada que no esté en la spec, conforme a la sección 6.4 del plan.

## Workflow follow-up

- Archivar el cambio en OpenSpec cuando se satisfagan los requisitos de revisión del proyecto.
- Verificar el resultado archivado y sincronizar las specs principales `auth`, `usuarios` e `interfaz-web`.
