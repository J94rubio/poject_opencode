# Matriz de trazabilidad — change `usuarios-roles-auth`

Requisito de OpenSpec → escenario → prueba → commit, según la sección 5.3 de `PLAN_INGENIERIA.md` (tarea 9.2 de `openspec/changes/usuarios-roles-auth/tasks.md`).

- Specs: `openspec/changes/usuarios-roles-auth/specs/{auth,usuarios,interfaz-web}/spec.md`.
- Backend: `pytest` contra la base `reservas_test`. Las rutas son relativas a `backend/tests/`.
- Frontend: `Vitest`. Las rutas son relativas a `frontend/src/` y la prueba se identifica como `describe › it`.
- Commit: el commit que introdujo la prueba. «Pendiente de commit» marca la prueba añadida durante la tarea 9.3.
- Estado: todas las pruebas citadas están en verde en la última ejecución: **342 pasadas en pytest** y **48 pasadas en Vitest**, sin fallos ni pruebas omitidas.

Las pruebas parametrizadas se citan por su nombre base. Cada variante se ejecuta como una prueba independiente.

## Resumen

| Spec | Requisitos | Escenarios | Escenarios con prueba en verde |
|---|---|---|---|
| `auth` | 9 | 35 | 35 |
| `usuarios` | 10 | 40 | 40 |
| `interfaz-web` | 5 | 15 | 15 |
| **Total** | **24** | **90** | **90** |

Todos los requisitos tienen al menos una prueba en verde. Las notas sobre la cobertura están en [Observaciones](#observaciones).

---

## Spec `auth`

### Requisito: Emisión de token de acceso tras validar credenciales

| Escenario | Prueba | Commit |
|---|---|---|
| Credenciales válidas de una cuenta activa | `test_login.py::test_credenciales_validas_de_una_cuenta_activa` | `9472367` |
| Contenido del token emitido | `test_tokens.py::test_el_token_contiene_unicamente_sub_iat_y_exp`; `test_login.py::test_credenciales_validas_de_una_cuenta_activa` (decodifica el token del login) | `9472367` |
| Contraseña incorrecta | `test_login.py::test_contrasena_incorrecta`; `test_login.py::test_correo_inexistente_con_el_mismo_mensaje_que_la_contrasena_incorrecta` (mensaje idéntico) | `9472367` |
| Correo inexistente | `test_login.py::test_correo_inexistente_con_el_mismo_mensaje_que_la_contrasena_incorrecta` | `9472367` |
| Cuenta desactivada | `test_login.py::test_cuenta_desactivada` | `9472367` |
| Datos de acceso incompletos | `test_login.py::test_datos_de_acceso_incompletos` (6 variantes); `test_login.py::test_login_sin_cuerpo_json` | `9472367` |

### Requisito: Validación del token en peticiones protegidas

| Escenario | Prueba | Commit |
|---|---|---|
| Petición sin token | `test_verificacion_token.py::test_peticion_sin_token` | `9472367` |
| Token mal formado | `test_verificacion_token.py::test_cabecera_mal_formada` (8 variantes) | `9472367` |
| Firma inválida o token manipulado | `test_verificacion_token.py::test_firma_invalida` | `9472367` |
| Token expirado | `test_verificacion_token.py::test_token_expirado` | `9472367` |
| Token válido | `test_verificacion_token.py::test_token_valido_ejecuta_la_peticion_con_la_identidad_del_usuario` | `9472367` |

### Requisito: Revocación inmediata del acceso de una cuenta desactivada

| Escenario | Prueba | Commit |
|---|---|---|
| Token vigente después de la desactivación | `test_usuarios_estado.py::test_desactivacion_revoca_el_acceso_de_inmediato` (desactivación por el admin vía API); `test_verificacion_token.py::test_token_vigente_de_una_cuenta_desactivada` | `150e108`, `9472367` |
| Reactivación antes de la expiración del token | `test_usuarios_estado.py::test_reactivacion_antes_de_la_expiracion_del_token` | `150e108` |

### Requisito: Consulta del usuario autenticado

| Escenario | Prueba | Commit |
|---|---|---|
| Consulta con token válido | `test_me.py::test_consulta_con_token_valido`; `test_me.py::test_consulta_con_el_token_emitido_por_el_login` | `9472367` |
| Consulta sin token | `test_me.py::test_consulta_sin_token` | `9472367` |
| Consulta con token expirado | `test_me.py::test_consulta_con_token_expirado` | `9472367` |

### Requisito: Jerarquía y matriz de permisos por rol

| Escenario | Prueba | Commit |
|---|---|---|
| La matriz respeta la jerarquía de roles | `test_matriz_usuarios.py::test_la_matriz_respeta_la_jerarquia_de_roles` (un caso por permiso); `test_matriz_usuarios.py::test_cada_rol_incluye_los_permisos_del_anterior`; `test_permisos.py::test_los_roles_que_poseen_cada_permiso_respetan_la_jerarquia`; `test_permisos.py::test_cada_rol_tiene_exactamente_los_permisos_de_la_matriz`; `test_permisos.py::test_tiene_permiso_coincide_con_cada_celda_de_la_matriz` | `150e108`, `c65c9c0` |
| Gestión de usuarios denegada al solicitante | `test_matriz_usuarios.py::test_gestion_de_usuarios_denegada[*-solicitante]` (listar, crear, editar, desactivar) | `150e108` |
| Gestión de usuarios denegada al aprobador | `test_matriz_usuarios.py::test_gestion_de_usuarios_denegada[*-aprobador]` (listar, crear, editar, desactivar) | `150e108` |
| Gestión de usuarios permitida al administrador | `test_matriz_usuarios.py::test_gestion_de_usuarios_permitida_al_administrador` | `150e108` |

### Requisito: Denegación de acceso sin permiso

| Escenario | Prueba | Commit |
|---|---|---|
| Denegación sobre una operación de escritura | `test_guard_permisos.py::test_escritura_denegada_por_rol_no_modifica_datos`; `test_matriz_usuarios.py::test_gestion_de_usuarios_denegada` (crear, editar y desactivar, con la comprobación de que los datos no cambian) | `c65c9c0`, `150e108` |
| Denegación sobre una operación de lectura | `test_guard_permisos.py::test_lectura_denegada_por_rol`; `test_usuarios_consulta.py::test_listado_solicitado_por_un_rol_sin_permiso` | `c65c9c0`, `150e108` |

### Requisito: Resolución del rol efectivo desde el registro del usuario

| Escenario | Prueba | Commit |
|---|---|---|
| Cambio de rol con token vigente | `test_verificacion_token.py::test_el_rol_efectivo_cambia_en_la_siguiente_peticion_sin_reautenticarse`; `test_guard_permisos.py::test_el_permiso_se_evalua_con_el_rol_vigente`; `test_usuarios_edicion.py::test_cambio_de_rol` (cambio hecho por el admin vía API) | `9472367`, `c65c9c0`, `150e108` |

### Requisito: Vigencia del token de acceso

| Escenario | Prueba | Commit |
|---|---|---|
| Vigencia por defecto | `test_tokens.py::test_vigencia_por_defecto_de_60_minutos`; `test_tokens.py::test_el_token_expira_al_cumplirse_la_vigencia`; `test_login.py::test_credenciales_validas_de_una_cuenta_activa` (`expira_en` = 3600 en el login) | `9472367` |
| Vigencia configurada | `test_login.py::test_vigencia_configurada_en_el_login` (con `JWT_ACCESS_TOKEN_MINUTES=5`, el login responde `expira_en` = 300); `test_tokens.py::test_vigencia_configurada`; `test_config.py::test_vigencia_del_token_configurable_desde_el_entorno` | pendiente de commit, `9472367`, `3a79345` |

### Requisito: Formato de las respuestas de error de la API

| Escenario | Prueba | Commit |
|---|---|---|
| Error de credenciales | `test_errores.py::test_cada_excepcion_de_dominio_produce_su_codigo_http_y_su_codigo_de_error[credenciales_invalidas]`; `test_login.py::test_contrasena_incorrecta` | `9472367` |
| Error de datos inválidos | `test_errores.py::test_cada_excepcion_de_dominio_produce_su_codigo_http_y_su_codigo_de_error[datos_invalidos]`; `test_usuarios_alta.py::test_alta_con_correo_de_formato_invalido` | `9472367`, `150e108` |
| Error de permiso | `test_errores.py::test_cada_excepcion_de_dominio_produce_su_codigo_http_y_su_codigo_de_error[permiso_insuficiente]`; `test_matriz_usuarios.py::test_gestion_de_usuarios_denegada` (comprueba el cuerpo completo) | `9472367`, `150e108` |
| Recurso inexistente | `test_errores.py::test_cada_excepcion_de_dominio_produce_su_codigo_http_y_su_codigo_de_error[usuario_no_encontrado]`; `test_usuarios_consulta.py::test_detalle_de_una_cuenta_inexistente` | `9472367`, `150e108` |
| Conflicto de unicidad | `test_errores.py::test_cada_excepcion_de_dominio_produce_su_codigo_http_y_su_codigo_de_error[correo_duplicado]`; `test_usuarios_alta.py::test_alta_con_correo_ya_registrado` | `9472367`, `150e108` |
| Ruta inexistente | `test_errores.py::test_ruta_inexistente` | `9472367` |
| Método no permitido | `test_errores.py::test_metodo_no_permitido` | `9472367` |
| Cuerpo JSON mal formado | `test_errores.py::test_cuerpo_json_mal_formado` | `9472367` |
| Error interno no controlado | `test_errores.py::test_error_interno_no_controlado` | `9472367` |
| Los mensajes de error son textos fijos | `test_errores.py::test_los_mensajes_del_catalogo_son_textos_fijos`; `test_errores.py::test_cada_excepcion_de_dominio_produce_su_codigo_http_y_su_codigo_de_error` (el mensaje no contiene el correo ni la contraseña enviados) | `9472367` |

---

## Spec `usuarios`

### Requisito: Alta de usuarios por el administrador

| Escenario | Prueba | Commit |
|---|---|---|
| Alta válida | `test_usuarios_alta.py::test_alta_valida`; `test_usuarios_alta.py::test_alta_con_cada_rol_del_catalogo` | `150e108` |
| Alta con correo ya registrado | `test_usuarios_alta.py::test_alta_con_correo_ya_registrado` | `150e108` |
| Alta con rol fuera del catálogo | `test_usuarios_alta.py::test_alta_con_rol_fuera_del_catalogo` (3 variantes) | `150e108` |
| Alta con contraseña que no cumple la política | `test_usuarios_alta.py::test_alta_con_contrasena_de_menos_de_8_caracteres` (2 variantes) | `150e108` |
| Alta con contraseña que solo cumple el mínimo | `test_usuarios_alta.py::test_alta_con_contrasena_que_solo_cumple_el_minimo` | `150e108` |
| Alta con correo de formato inválido | `test_usuarios_alta.py::test_alta_con_correo_de_formato_invalido` (7 variantes) | `150e108` |
| Alta con campos obligatorios faltantes | `test_usuarios_alta.py::test_alta_con_campos_obligatorios_faltantes` (nombre, correo, contraseña); `test_usuarios_alta.py::test_alta_con_nombre_vacio` | `150e108` |
| Alta solicitada por un rol sin permiso | `test_usuarios_alta.py::test_alta_solicitada_por_un_rol_sin_permiso` (solicitante, aprobador) | `150e108` |
| Alta sin autenticación | `test_usuarios_alta.py::test_alta_sin_autenticacion` | `150e108` |

### Requisito: Almacenamiento seguro de las contraseñas

| Escenario | Prueba | Commit |
|---|---|---|
| Verificación de la contraseña con el valor almacenado | `test_hash_password.py::test_el_valor_almacenado_difiere_de_la_contrasena_en_texto_plano`; `test_hash_password.py::test_la_verificacion_con_la_contrasena_correcta_resulta_exitosa`; `test_hash_password.py::test_dos_cuentas_con_la_misma_contrasena_almacenan_valores_distintos` | `1b898b1` |
| El detalle de usuario no expone credenciales | `test_usuarios_consulta.py::test_el_detalle_de_usuario_no_expone_credenciales` | `150e108` |

### Requisito: Normalización y unicidad del correo

| Escenario | Prueba | Commit |
|---|---|---|
| Inicio de sesión con correo en mayúsculas | `test_login.py::test_login_con_el_correo_en_mayusculas` | `9472367` |
| Duplicado que solo difiere en mayúsculas | `test_usuarios_alta.py::test_duplicado_que_solo_difiere_en_mayusculas`; `test_correo.py::test_la_base_rechaza_dos_cuentas_con_el_mismo_correo_en_distinto_caso` (índice único sobre `lower(correo)`); `test_correo.py::test_el_correo_se_guarda_en_minusculas` | `150e108`, `1b898b1` |

### Requisito: Listado de cuentas de usuario

| Escenario | Prueba | Commit |
|---|---|---|
| Listado solicitado por el administrador | `test_usuarios_consulta.py::test_listado_solicitado_por_el_administrador` | `150e108` |
| El listado incluye cuentas desactivadas | `test_usuarios_consulta.py::test_el_listado_incluye_cuentas_desactivadas` | `150e108` |
| Listado solicitado por un rol sin permiso | `test_usuarios_consulta.py::test_listado_solicitado_por_un_rol_sin_permiso` (solicitante, aprobador) | `150e108` |

### Requisito: Consulta del detalle de una cuenta

| Escenario | Prueba | Commit |
|---|---|---|
| Detalle de una cuenta existente | `test_usuarios_consulta.py::test_detalle_de_una_cuenta_existente` | `150e108` |
| Detalle de una cuenta inexistente | `test_usuarios_consulta.py::test_detalle_de_una_cuenta_inexistente` | `150e108` |
| Detalle solicitado por un rol sin permiso | `test_usuarios_consulta.py::test_detalle_solicitado_por_un_rol_sin_permiso` (solicitante, aprobador) | `150e108` |

### Requisito: Edición de los datos de una cuenta

| Escenario | Prueba | Commit |
|---|---|---|
| Cambio de nombre | `test_usuarios_edicion.py::test_cambio_de_nombre`; `test_usuarios_edicion.py::test_la_edicion_no_altera_estado_ni_contrasena` | `150e108` |
| Cambio de rol | `test_usuarios_edicion.py::test_cambio_de_rol` | `150e108` |
| Cambio de correo a uno ya registrado | `test_usuarios_edicion.py::test_cambio_de_correo_a_uno_ya_registrado` | `150e108` |
| Cambio de rol fuera del catálogo | `test_usuarios_edicion.py::test_cambio_de_rol_fuera_del_catalogo` (3 variantes) | `150e108` |
| Cambio del propio rol | `test_usuarios_edicion.py::test_cambio_del_propio_rol`; `test_usuarios_edicion.py::test_cambio_del_propio_rol_no_aplica_ningun_otro_cambio` | `150e108` |
| Edición solicitada por un rol sin permiso | `test_usuarios_edicion.py::test_edicion_solicitada_por_un_rol_sin_permiso` (solicitante, aprobador) | `150e108` |

### Requisito: Restablecimiento de contraseña por el administrador

| Escenario | Prueba | Commit |
|---|---|---|
| Restablecimiento válido | `test_usuarios_password.py::test_restablecimiento_valido`; `test_usuarios_password.py::test_restablecimiento_guarda_solo_el_hash` | `150e108` |
| Contraseña que no cumple la política | `test_usuarios_password.py::test_contrasena_que_no_cumple_la_politica` (2 variantes) | `150e108` |
| Restablecimiento solicitado por un rol sin permiso | `test_usuarios_password.py::test_restablecimiento_solicitado_por_un_rol_sin_permiso` (solicitante, aprobador) | `150e108` |

### Requisito: Desactivación y activación de cuentas

| Escenario | Prueba | Commit |
|---|---|---|
| Desactivación de una cuenta activa | `test_usuarios_estado.py::test_desactivacion_de_una_cuenta_activa` | `150e108` |
| Reactivación de una cuenta desactivada | `test_usuarios_estado.py::test_reactivacion_de_una_cuenta_desactivada` | `150e108` |
| Conservación de los datos tras desactivar | `test_usuarios_estado.py::test_conservacion_de_los_datos_tras_desactivar` | `150e108` |
| Desactivación solicitada por un rol sin permiso | `test_usuarios_estado.py::test_desactivacion_solicitada_por_un_rol_sin_permiso` (solicitante, aprobador); `test_usuarios_estado.py::test_activacion_solicitada_por_un_rol_sin_permiso` | `150e108` |
| Desactivación de la propia cuenta | `test_usuarios_estado.py::test_desactivacion_de_la_propia_cuenta` | `150e108` |
| Desactivación de la cuenta de otro administrador | `test_usuarios_estado.py::test_desactivacion_de_la_cuenta_de_otro_administrador` | `150e108` |

### Requisito: Catálogo de roles del sistema

| Escenario | Prueba | Commit |
|---|---|---|
| Consulta del catálogo por el administrador | `test_roles.py::test_consulta_del_catalogo_por_el_administrador` | `150e108` |
| Consulta del catálogo por un rol sin permiso | `test_roles.py::test_consulta_del_catalogo_por_un_rol_sin_permiso` (solicitante, aprobador) | `150e108` |

El rechazo de cualquier otro valor de rol, que también declara este requisito, lo cubren `test_usuarios_alta.py::test_alta_con_rol_fuera_del_catalogo` y `test_usuarios_edicion.py::test_cambio_de_rol_fuera_del_catalogo`.

### Requisito: Creación del primer administrador por línea de comandos

| Escenario | Prueba | Commit |
|---|---|---|
| Creación del primer administrador | `test_create_admin.py::test_creacion_del_primer_admin_con_opcion_y_variable`; `test_create_admin.py::test_creacion_con_correo_desde_la_variable`; `test_create_admin.py::test_contrasena_de_8_caracteres_sin_reglas_de_composicion`; `test_create_admin.py::test_creacion_si_solo_hay_un_admin_desactivado` | `22e291a` |
| Ya existe un administrador activo | `test_create_admin.py::test_falla_si_ya_existe_un_admin_activo` | `22e291a` |
| Contraseña que no cumple la política | `test_create_admin.py::test_falla_con_contrasena_de_menos_de_8_caracteres` (2 variantes) | `22e291a` |
| Correo inválido o duplicado | `test_create_admin.py::test_falla_con_correo_de_formato_invalido` (3 variantes); `test_create_admin.py::test_falla_con_correo_duplicado` | `22e291a` |

---

## Spec `interfaz-web`

### Requisito: Pantalla de inicio de sesión

| Escenario | Prueba | Commit |
|---|---|---|
| Credenciales inválidas | `features/auth/LoginPage.test.jsx` › Pantalla de inicio de sesión › «Credenciales inválidas: muestra el mensaje de credenciales_invalidas y no inicia sesión» | `005a096` |
| Cuenta desactivada | `features/auth/LoginPage.test.jsx` › Pantalla de inicio de sesión › «Cuenta desactivada: muestra el mensaje de usuario_desactivado y no inicia sesión» | `005a096` |
| Datos de acceso inválidos | `features/auth/LoginPage.test.jsx` › Pantalla de inicio de sesión › «Datos de acceso inválidos: con campos vacíos envía al servidor y muestra el mensaje de datos_invalidos»; «Datos de acceso inválidos: con correo de formato inválido envía al servidor y muestra credenciales_invalidas» | `005a096` |
| Credenciales válidas | `features/auth/LoginPage.test.jsx` › Pantalla de inicio de sesión › «Credenciales válidas: inicia sesión con el token devuelto por el backend» | `005a096` |

### Requisito: Ciclo de vida de la sesión

| Escenario | Prueba | Commit |
|---|---|---|
| Restauración de la sesión | `features/auth/LoginPage.test.jsx` › Ciclo de vida de la sesión › «Restauración de la sesión: con un token guardado válido no vuelve a pedir credenciales»; «Restauración de la sesión: con un token guardado expirado vuelve al login y lo descarta» | `005a096` |
| Cierre de sesión | `features/auth/LoginPage.test.jsx` › Ciclo de vida de la sesión › «Cierre de sesión: descarta el token guardado y vuelve a la pantalla de inicio de sesión» | `005a096` |
| Token expirado | `features/auth/sesion.test.jsx` › respuesta 401 y 403 en una sesión iniciada › «Token expirado: descarta el token y vuelve a la pantalla de inicio de sesión»; `api/client.test.js` › cliente HTTP › «un 401 con token_expirado en una petición autenticada avisa de la pérdida de sesión» | `005a096` |

### Requisito: Mensaje de error por permisos insuficientes

| Escenario | Prueba | Commit |
|---|---|---|
| Error de permisos insuficientes | `features/auth/sesion.test.jsx` › respuesta 401 y 403 en una sesión iniciada › «Error de permisos insuficientes: muestra un mensaje y la sesión permanece activa»; `api/client.test.js` › cliente HTTP › «un 403 con permiso_insuficiente avisa del permiso sin perder la sesión» | `005a096` |

### Requisito: Protección de las rutas de la aplicación

| Escenario | Prueba | Commit |
|---|---|---|
| Ruta protegida sin sesión | `features/auth/RutaProtegida.test.jsx` › Protección de las rutas de la aplicación › «Ruta protegida sin sesión: / redirige al login»; «Ruta protegida sin sesión: /admin/usuarios redirige al login» | `005a096` |
| Acceso de un rol sin permiso | `features/auth/RutaProtegida.test.jsx` › Protección de las rutas de la aplicación › «Acceso de un rol sin permiso: un solicitante no alcanza la sección de administración»; «Acceso de un rol sin permiso: un aprobador no alcanza la sección de administración» | `005a096` |
| Acceso del administrador | `features/auth/RutaProtegida.test.jsx` › Protección de las rutas de la aplicación › «Acceso del administrador: un admin alcanza la sección de administración» | `005a096` |

### Requisito: Pantallas de administración de usuarios

| Escenario | Prueba | Commit |
|---|---|---|
| Listado de cuentas con su estado | `features/usuarios/ListadoUsuarios.test.jsx` › Listado de cuentas con su estado › «muestra cada cuenta con su nombre, correo, rol y estado activo o inactivo» | `7c561d8` |
| Alta y edición de una cuenta | `features/usuarios/FormularioUsuario.test.jsx` › Alta de una cuenta › «Alta correcta…», «Alta rechazada con 409 correo_duplicado…», «Alta rechazada con 400 rol_invalido…», «Alta rechazada con 400 contrasena_invalida…», «Alta rechazada con 400 datos_invalidos…»; › Edición de una cuenta › «Edición correcta…», «Edición rechazada con 409 correo_duplicado…», «Edición rechazada con 400 rol_invalido…», «Edición rechazada con 400 datos_invalidos…», «Cambio del propio rol: muestra el mensaje de operacion_no_permitida y el rol no cambia» | `7c561d8` |
| Desactivación y reactivación de una cuenta | `features/usuarios/ListadoUsuarios.test.jsx` › Desactivación y reactivación de una cuenta › «Desactivar llama a POST /api/usuarios/{id}/desactivar y el listado refleja el estado inactivo»; «Reactivar llama a POST /api/usuarios/{id}/activar y el listado refleja el estado activo» | `7c561d8` |
| Restablecimiento de la contraseña | `features/usuarios/FormularioContrasena.test.jsx` › Restablecimiento de la contraseña › «Envío correcto: envía la nueva contraseña a POST /api/usuarios/{id}/password y vuelve al listado»; «Respuesta con contrasena_invalida: muestra el mensaje del servidor y vacía el campo» | `7c561d8` |

Las pruebas de `interfaz-web` usan un backend simulado (`frontend/src/test/backendFalso.js`) que responde con los códigos y cuerpos del contrato de errores de la API. Verifican el comportamiento de la interfaz, no el del servidor, que cubren las pruebas de `pytest`.

---

## Pruebas de tareas sin escenario de spec

Estas pruebas verifican tareas de `tasks.md` (infraestructura, configuración y documentación) que no corresponden a ningún escenario de las specs. Se listan para que la matriz recoja todas las pruebas de la suite.

| Archivo | Tarea | Commit |
|---|---|---|
| `backend/tests/test_app_factory.py` | 1.1, 1.5, 1.6 | `3a79345` |
| `backend/tests/test_config.py` | 1.3 (y `JWT_ACCESS_TOKEN_MINUTES`, ver observación 1) | `3a79345` |
| `backend/tests/test_cors.py` | 1.7 | `3a79345` |
| `backend/tests/test_modelos.py` | 2.1 | `d50687e` |
| `backend/tests/test_migraciones.py` | 2.2 | `d50687e` |
| `backend/tests/test_repositorio_usuarios.py` | 2.2 | `d50687e` |
| `backend/tests/test_readme.py` | 5.7 | `150e108` |
| `frontend/src/App.test.jsx` | 1.7 | `3a79345` |
| `frontend/src/features/auth/almacenToken.test.jsx` | 7.2 (almacenamiento del token sin `sessionStorage`) | `005a096` |

Algunas pruebas de los archivos citados en las specs cubren casos que ningún escenario nombra, como la cuenta inexistente en edición, activación o restablecimiento (404), los campos no editables en la edición o la cuenta desactivada con contraseña incorrecta. No figuran en las tablas anteriores porque no corresponden a un escenario.

## Observaciones

1. **«Vigencia configurada» (spec `auth`).** La revisión de la tarea 9.2 detectó que este escenario solo se probaba al nivel de la emisión del token. Para cubrir el recorrido completo se añadió `test_login.py::test_vigencia_configurada_en_el_login`, que ejecuta el login con `JWT_ACCESS_TOKEN_MINUTES=5` y comprueba que `expira_en` es 300.
2. **Errores HTTP fuera del contrato.** El manejador de errores (`backend/app/auth/errors.py`) traduce al formato JSON los errores 400, 404, 405 y 500. Cualquier otro error HTTP del framework (por ejemplo, 413 o 415) conserva la respuesta por defecto de Flask, que no tiene el formato `{"error": {...}}`. Con el código actual ninguna de esas respuestas es alcanzable: las rutas leen el cuerpo con `get_json(silent=True)` y no se configura un tamaño máximo de petición. Por eso no tienen prueba.
