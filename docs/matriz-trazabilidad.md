# Matriz de trazabilidad

Requisito de OpenSpec → escenario → prueba → commit, según la sección 5.3 de `PLAN_INGENIERIA.md`. Cubre los changes `usuarios-roles-auth` (tarea 9.2 de su `tasks.md`, archivado en `openspec/changes/archive/2026-10-31-usuarios-roles-auth/`), `espacios` (tarea 5.2 de su `tasks.md`, archivado en `openspec/changes/archive/2026-10-31-espacios/`) y `reservas-disponibilidad` (tarea 6.2 de `openspec/changes/reservas-disponibilidad/tasks.md`).

- Specs:
  - `auth`, `usuarios` e `interfaz-web` (requisitos de `usuarios-roles-auth`): specs publicadas en `openspec/specs/{auth,usuarios,interfaz-web}/spec.md`.
  - `espacios` y los requisitos de espacios de `interfaz-web`: specs publicadas en `openspec/specs/{espacios,interfaz-web}/spec.md`.
  - `reservas` y los requisitos de reservas de `interfaz-web` (change `reservas-disponibilidad`): specs delta del change en `openspec/changes/reservas-disponibilidad/specs/{reservas,interfaz-web}/spec.md`, que se publicarán en `openspec/specs/` al archivar el change.
- Backend: `pytest` contra la base `reservas_test`. Las rutas son relativas a `backend/tests/`.
- Frontend: `Vitest`. Las rutas son relativas a `frontend/src/` y la prueba se identifica como `describe › it`.
- Commit: el commit que introdujo la prueba. «pendiente» indica una prueba de la sección 5 de `reservas-disponibilidad` que aún no tiene commit.
- Estado: todas las pruebas citadas están en verde en la última ejecución: **775 pasadas en pytest** y **119 pasadas en Vitest**, sin fallos ni pruebas omitidas.

Las pruebas parametrizadas (`pytest.mark.parametrize`, `it.each`) se citan por su nombre base. Cada variante se ejecuta como una prueba independiente.

## Resumen

| Spec | Requisitos | Escenarios | Escenarios con prueba en verde |
|---|---|---|---|
| `auth` | 9 | 35 | 35 |
| `usuarios` | 10 | 40 | 40 |
| `espacios` | 7 | 36 | 36 |
| `reservas` | 6 | 46 | 46 |
| `interfaz-web` | 11 (5 de `usuarios-roles-auth`, 3 de `espacios` y 3 de `reservas-disponibilidad`) | 39 | 39 |
| **Total** | **43** | **196** | **196** |

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
| Vigencia configurada | `test_login.py::test_vigencia_configurada_en_el_login` (con `JWT_ACCESS_TOKEN_MINUTES=5`, el login responde `expira_en` = 300); `test_tokens.py::test_vigencia_configurada`; `test_config.py::test_vigencia_del_token_configurable_desde_el_entorno` | `b0c942f`, `9472367`, `3a79345` |

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

## Spec `espacios`

Cada escenario se cita con la prueba del servicio (`test_servicio_espacios_*.py`, sección 2) y la de integración HTTP (`test_espacios_*.py`, sección 3) cuando existen ambas.

### Requisito: Registro de espacios académicos

| Escenario | Prueba | Commit |
|---|---|---|
| Alta válida de un espacio | `test_servicio_espacios_alta.py::test_alta_valida_de_un_espacio`; `test_espacios_alta.py::test_alta_valida_de_un_espacio` (aprobador y admin; comprueba que aparece en el listado y el detalle) | `08159a7`, `4ea3b2a` |
| Alta con capacidad igual a cero | `test_servicio_espacios_alta.py::test_alta_con_capacidad_invalida[cero]`; `test_espacios_alta.py::test_alta_propaga_los_errores_400_del_servicio[capacidad_cero]` | `08159a7`, `4ea3b2a` |
| Alta con capacidad negativa | `test_servicio_espacios_alta.py::test_alta_con_capacidad_invalida[negativa, negativa_grande]`; `test_espacios_alta.py::test_alta_propaga_los_errores_400_del_servicio[capacidad_negativa]` | `08159a7`, `4ea3b2a` |
| Alta con capacidad no entera | `test_servicio_espacios_alta.py::test_alta_con_capacidad_invalida[decimal, decimal_exacto, texto_numerico, texto, nula, cadena_vacia, booleano_true, booleano_false, lista, objeto]`; `test_espacios_alta.py::test_alta_propaga_los_errores_400_del_servicio[capacidad_decimal, capacidad_texto, capacidad_nula, capacidad_cadena_vacia]` | `08159a7`, `4ea3b2a` |
| Alta con tipo fuera del catálogo | `test_servicio_espacios_alta.py::test_alta_con_tipo_fuera_del_catalogo`; `test_espacios_alta.py::test_alta_propaga_los_errores_400_del_servicio[tipo_fuera_del_catalogo]` | `08159a7`, `4ea3b2a` |
| Alta con campos obligatorios faltantes | `test_servicio_espacios_alta.py::test_alta_con_campo_obligatorio_ausente`; `test_espacios_alta.py::test_alta_propaga_los_errores_400_del_servicio[sin_nombre, sin_tipo, sin_capacidad]` | `08159a7`, `4ea3b2a` |
| Alta con nombre vacío o compuesto solo por espacios | `test_servicio_espacios_alta.py::test_alta_con_nombre_vacio_o_solo_espacios`; `test_espacios_alta.py::test_alta_propaga_los_errores_400_del_servicio[nombre_solo_espacios]` | `08159a7`, `4ea3b2a` |

### Requisito: Unicidad y normalización del nombre del espacio

| Escenario | Prueba | Commit |
|---|---|---|
| Alta con nombre ya registrado | `test_servicio_espacios_alta.py::test_alta_con_nombre_ya_registrado`; `test_espacios_alta.py::test_alta_propaga_el_error_409_de_nombre_duplicado[contra_activo-Lab 1]` | `08159a7`, `4ea3b2a` |
| Duplicado que solo difiere en mayúsculas o espacios exteriores | `test_servicio_espacios_alta.py::test_duplicado_que_solo_difiere_en_mayusculas_o_espacios_exteriores`; `test_espacios_alta.py::test_alta_propaga_el_error_409_de_nombre_duplicado` (variantes con `"  LAB 1 "`); `test_repositorio_espacios.py::test_dos_altas_con_nombres_equivalentes_violan_el_indice_unico`; `test_servicio_espacios_alta.py::test_la_violacion_del_indice_unico_se_traduce_a_espacio_duplicado` | `08159a7`, `4ea3b2a`, `9064d93` |
| Duplicado contra un espacio inactivo | `test_servicio_espacios_alta.py::test_duplicado_contra_un_espacio_inactivo`; `test_espacios_alta.py::test_alta_propaga_el_error_409_de_nombre_duplicado` (variantes `contra_inactivo`) | `08159a7`, `4ea3b2a` |

### Requisito: Consulta del catálogo de espacios

| Escenario | Prueba | Commit |
|---|---|---|
| Listado con espacios activos e inactivos | `test_servicio_espacios_consulta.py::test_listado_con_espacios_activos_e_inactivos`; `test_espacios_consulta.py::test_listado_con_espacios_activos_e_inactivos` (3 roles) | `08159a7`, `4ea3b2a` |
| Listado sin espacios registrados | `test_servicio_espacios_consulta.py::test_listado_sin_espacios_registrados`; `test_espacios_consulta.py::test_listado_sin_espacios_registrados` | `08159a7`, `4ea3b2a` |
| Detalle de un espacio existente | `test_servicio_espacios_consulta.py::test_detalle_de_un_espacio_existente`; `test_espacios_consulta.py::test_detalle_de_un_espacio_existente` (3 roles) | `08159a7`, `4ea3b2a` |
| Detalle de un espacio inactivo | `test_servicio_espacios_consulta.py::test_detalle_de_un_espacio_inactivo`; `test_espacios_consulta.py::test_detalle_de_un_espacio_inactivo` | `08159a7`, `4ea3b2a` |
| Detalle de un espacio inexistente | `test_servicio_espacios_consulta.py::test_detalle_de_un_espacio_inexistente`; `test_espacios_consulta.py::test_detalle_de_un_espacio_inexistente` (cuerpo exacto, sin datos de espacio) | `08159a7`, `4ea3b2a` |

### Requisito: Edición de espacios académicos

| Escenario | Prueba | Commit |
|---|---|---|
| Edición válida de nombre, tipo y capacidad | `test_servicio_espacios_edicion.py::test_edicion_valida_de_nombre_tipo_y_capacidad`; `test_espacios_edicion.py::test_edicion_valida_de_nombre_tipo_y_capacidad` (aprobador y admin); `test_espacios_edicion.py::test_edicion_conserva_el_estado_de_un_espacio_inactivo` | `08159a7`, `4ea3b2a` |
| Edición de un solo campo | `test_servicio_espacios_edicion.py::test_edicion_de_un_solo_campo`; `test_espacios_edicion.py::test_edicion_de_un_solo_campo` | `08159a7`, `4ea3b2a` |
| Edición que conserva el propio nombre | `test_servicio_espacios_edicion.py::test_edicion_que_conserva_el_propio_nombre`; `test_espacios_edicion.py::test_edicion_que_conserva_el_propio_nombre` | `08159a7`, `4ea3b2a` |
| Edición con el nombre de otro espacio | `test_servicio_espacios_edicion.py::test_edicion_con_el_nombre_de_otro_espacio`; `test_espacios_edicion.py::test_edicion_con_el_nombre_de_otro_espacio` | `08159a7`, `4ea3b2a` |
| Edición con nombre vacío | `test_servicio_espacios_edicion.py::test_edicion_con_nombre_vacio_o_que_no_es_texto`; `test_espacios_edicion.py::test_edicion_propaga_los_errores_400_del_servicio[nombre_vacio, nombre_solo_espacios]` | `08159a7`, `4ea3b2a` |
| Edición con tipo fuera del catálogo | `test_servicio_espacios_edicion.py::test_edicion_con_tipo_fuera_del_catalogo`; `test_espacios_edicion.py::test_edicion_propaga_los_errores_400_del_servicio[tipo_fuera_del_catalogo]` | `08159a7`, `4ea3b2a` |
| Edición con capacidad inválida | `test_servicio_espacios_edicion.py::test_edicion_con_capacidad_invalida`; `test_espacios_edicion.py::test_edicion_propaga_los_errores_400_del_servicio[capacidad_*]` (5 variantes) | `08159a7`, `4ea3b2a` |
| Edición que intenta cambiar el estado | `test_servicio_espacios_edicion.py::test_edicion_que_intenta_cambiar_el_estado`; `test_espacios_edicion.py::test_edicion_que_intenta_cambiar_el_estado` (2 variantes) | `08159a7`, `4ea3b2a` |
| Edición de un espacio inexistente | `test_servicio_espacios_edicion.py::test_edicion_de_un_espacio_inexistente`; `test_espacios_edicion.py::test_edicion_de_un_espacio_inexistente` (comprueba que no se crea ningún espacio) | `08159a7`, `4ea3b2a` |

### Requisito: Desactivación de espacios académicos

| Escenario | Prueba | Commit |
|---|---|---|
| Desactivación de un espacio activo | `test_servicio_espacios_estado.py::test_desactivacion_de_un_espacio_activo`; `test_espacios_desactivacion.py::test_desactivacion_de_un_espacio_activo` (aprobador y admin) | `08159a7`, `4ea3b2a` |
| Conservación de los datos tras la desactivación | `test_servicio_espacios_estado.py::test_conservacion_de_los_datos_tras_la_desactivacion`; `test_espacios_desactivacion.py::test_conservacion_de_los_datos_tras_la_desactivacion` (listado posterior) | `08159a7`, `4ea3b2a` |
| Desactivación de un espacio ya inactivo | `test_servicio_espacios_estado.py::test_desactivacion_de_un_espacio_ya_inactivo`; `test_espacios_desactivacion.py::test_desactivacion_de_un_espacio_ya_inactivo` | `08159a7`, `4ea3b2a` |
| Desactivación de un espacio inexistente | `test_servicio_espacios_estado.py::test_desactivacion_de_un_espacio_inexistente`; `test_espacios_desactivacion.py::test_desactivacion_de_un_espacio_inexistente` | `08159a7`, `4ea3b2a` |

### Requisito: Reactivación de espacios académicos

| Escenario | Prueba | Commit |
|---|---|---|
| Reactivación de un espacio inactivo | `test_servicio_espacios_estado.py::test_reactivacion_de_un_espacio_inactivo`; `test_servicio_espacios_estado.py::test_reactivacion_aparece_en_el_listado_como_activo`; `test_espacios_reactivacion.py::test_reactivacion_de_un_espacio_inactivo` (aprobador y admin; conserva nombre, tipo y capacidad) | `08159a7`, `4ea3b2a` |
| Reactivación de un espacio ya activo | `test_servicio_espacios_estado.py::test_reactivacion_de_un_espacio_ya_activo`; `test_espacios_reactivacion.py::test_reactivacion_de_un_espacio_ya_activo` | `08159a7`, `4ea3b2a` |
| Reactivación de un espacio inexistente | `test_servicio_espacios_estado.py::test_reactivacion_de_un_espacio_inexistente`; `test_espacios_reactivacion.py::test_reactivacion_de_un_espacio_inexistente` | `08159a7`, `4ea3b2a` |
| Reactivación denegada al solicitante | `test_espacios_reactivacion.py::test_reactivacion_denegada_al_solicitante` | `4ea3b2a` |

### Requisito: Control de acceso a la gestión de espacios

| Escenario | Prueba | Commit |
|---|---|---|
| Consulta permitida a todos los roles autenticados | `test_espacios_consulta.py::test_listado_con_espacios_activos_e_inactivos` y `test_espacios_consulta.py::test_detalle_de_un_espacio_existente` (variantes `solicitante`, `aprobador` y `admin`) | `4ea3b2a` |
| Gestión permitida al aprobador y al administrador | `test_espacios_alta.py::test_alta_valida_de_un_espacio`; `test_espacios_edicion.py::test_edicion_valida_de_nombre_tipo_y_capacidad`; `test_espacios_desactivacion.py::test_desactivacion_de_un_espacio_activo`; `test_espacios_reactivacion.py::test_reactivacion_de_un_espacio_inactivo` (variantes `aprobador` y `admin`) | `4ea3b2a` |
| Alta, edición, desactivación o reactivación denegada al solicitante | `test_espacios_alta.py::test_alta_denegada_al_solicitante`; `test_espacios_edicion.py::test_edicion_denegada_al_solicitante`; `test_espacios_desactivacion.py::test_desactivacion_denegada_al_solicitante`; `test_espacios_reactivacion.py::test_reactivacion_denegada_al_solicitante` (todas comprueban que los datos no cambian) | `4ea3b2a` |
| Operación de gestión sin autenticación | `test_espacios_consulta.py::test_consulta_sin_autenticacion` (listado y detalle); `test_espacios_alta.py::test_alta_sin_autenticacion`; `test_espacios_edicion.py::test_edicion_sin_autenticacion`; `test_espacios_desactivacion.py::test_desactivacion_sin_autenticacion`; `test_espacios_reactivacion.py::test_reactivacion_sin_autenticacion` | `4ea3b2a` |

---

## Spec `reservas`

Spec delta del change `reservas-disponibilidad` (`openspec/changes/reservas-disponibilidad/specs/reservas/spec.md`). Cada escenario se cita con la prueba del servicio (`test_servicio_reservas_*.py`, sección 3) y la de integración HTTP (`test_reservas_api.py`, sección 4) cuando existen ambas. Los escenarios de la garantía de integridad se verifican a nivel de repositorio y de esquema (secciones 1 y 2). Como la aprobación llega con `aprobacion-reservas`, las reservas aprobadas se siembran directamente en el repositorio. Las validaciones de fechas usan un reloj inyectado.

### Requisito: Creación de solicitudes de reserva

| Escenario | Prueba | Commit |
|---|---|---|
| Creación válida en estado pendiente | `test_servicio_reservas_creacion.py::test_creacion_valida_en_estado_pendiente`; `test_reservas_api.py::test_creacion_valida_por_rol[solicitante]` | `7519869` |
| Creación por aprobador o administrador | `test_servicio_reservas_creacion.py::test_toda_solicitud_nace_pendiente_del_usuario_autenticado[aprobador, admin]`; `test_reservas_api.py::test_creacion_valida_por_rol[aprobador, admin]` | `7519869` |
| Solicitante enviado en el cuerpo de la petición | `test_servicio_reservas_creacion.py::test_un_campo_de_solicitante_en_el_cuerpo` (2 variantes); `test_reservas_api.py::test_creacion_con_datos_invalidos[solicitante_en_el_cuerpo]` | `7519869` |
| Campos obligatorios faltantes | `test_servicio_reservas_creacion.py::test_campos_obligatorios_faltantes` (3 variantes); `test_reservas_api.py::test_creacion_con_datos_invalidos[sin_inicio]` | `7519869` |
| Fecha sin zona horaria es inválida | `test_servicio_reservas_creacion.py::test_fecha_sin_zona_horaria_es_invalida` (inicio y fin); `test_servicio_reservas_creacion.py::test_convertir_fecha_rechaza_sin_zona_horaria_o_formato_invalido` (9 variantes); `test_reservas_api.py::test_creacion_con_datos_invalidos[sin_zona_horaria]` | `7519869` |
| Fin anterior o igual al inicio | `test_servicio_reservas_creacion.py::test_fin_igual_o_anterior_al_inicio` (2 variantes); `test_servicio_reservas_creacion.py::test_fin_igual_al_inicio_expresado_en_otra_zona`; `test_reservas_api.py::test_creacion_con_datos_invalidos[fin_igual_al_inicio]` | `7519869` |
| Inicio en el pasado | `test_servicio_reservas_creacion.py::test_inicio_en_el_pasado_o_en_el_instante_actual[un_dia_antes, un_instante_antes]`; `test_servicio_reservas_creacion.py::test_el_instante_actual_lo_fija_el_reloj_inyectado`; `test_reservas_api.py::test_creacion_con_datos_invalidos[inicio_en_el_pasado]` | `7519869` |
| Inicio en el instante actual | `test_servicio_reservas_creacion.py::test_inicio_en_el_pasado_o_en_el_instante_actual[instante_actual]`; `test_servicio_reservas_creacion.py::test_inicio_un_instante_despues_del_actual_se_acepta` (límite aceptado); `test_reservas_api.py::test_creacion_con_datos_invalidos[inicio_en_el_instante_actual]` | `7519869` |
| Espacio inexistente | `test_servicio_reservas_creacion.py::test_espacio_inexistente` (4 variantes); `test_reservas_api.py::test_creacion_sobre_espacio_inexistente` | `7519869` |
| Espacio inactivo rechaza la solicitud | `test_servicio_reservas_creacion.py::test_espacio_inactivo_rechaza_la_solicitud`; `test_reservas_api.py::test_creacion_sobre_espacio_inactivo_y_reactivado` | `7519869` |
| Espacio desactivado y luego reactivado admite solicitudes | `test_servicio_reservas_creacion.py::test_espacio_desactivado_y_reactivado_admite_solicitudes`; `test_reservas_api.py::test_creacion_sobre_espacio_inactivo_y_reactivado` | `7519869` |
| Creación sin autenticación | `test_reservas_api.py::test_creacion_sin_autenticacion` (comprueba que no se crea ninguna solicitud) | `7519869` |

### Requisito: Catálogo de estados de una reserva

| Escenario | Prueba | Commit |
|---|---|---|
| Toda solicitud creada por la API queda pendiente | `test_servicio_reservas_creacion.py::test_toda_solicitud_nace_pendiente_del_usuario_autenticado` (3 roles); `test_servicio_reservas_creacion.py::test_la_peticion_no_puede_fijar_el_estado_ni_otros_campos` (3 variantes); `test_reservas_api.py::test_creacion_con_datos_invalidos[estado_en_el_cuerpo]` | `7519869` |
| Estado fuera del catálogo rechazado al persistir | `test_reservas_esquema.py::test_un_estado_fuera_del_catalogo_es_rechazado` (3 variantes); `test_reservas_esquema.py::test_cada_estado_del_catalogo_se_acepta` (4 estados) | `7519869` |

### Requisito: Ocupación por reservas aprobadas

| Escenario | Prueba | Commit |
|---|---|---|
| Solapamiento parcial con una reserva aprobada | `test_servicio_reservas_creacion.py::test_solapamiento_con_una_reserva_aprobada[solapamiento_parcial_final, solapamiento_parcial_inicial, mismo_rango]`; `test_reservas_api.py::test_creacion_solapada_con_una_aprobada` | `7519869` |
| Solicitud contenida en una reserva aprobada | `test_servicio_reservas_creacion.py::test_solapamiento_con_una_reserva_aprobada[contenida]` | `7519869` |
| Solicitud que contiene a una reserva aprobada | `test_servicio_reservas_creacion.py::test_solapamiento_con_una_reserva_aprobada[que_contiene]` | `7519869` |
| Reserva que termina exactamente cuando otra empieza es permitida | `test_servicio_reservas_creacion.py::test_borde_exacto_permitido[empieza_cuando_termina, termina_cuando_empieza]` | `7519869` |
| La misma franja en otro espacio no genera conflicto | `test_servicio_reservas_creacion.py::test_la_misma_franja_en_otro_espacio_no_genera_conflicto` | `7519869` |
| Una reserva rechazada o cancelada no ocupa el espacio | `test_servicio_reservas_creacion.py::test_reservas_no_aprobadas_no_ocupan[rechazada, cancelada]` | `7519869` |
| Varias solicitudes pendientes pueden solaparse entre sí | `test_servicio_reservas_creacion.py::test_varias_solicitudes_pendientes_pueden_solaparse`; `test_servicio_reservas_creacion.py::test_reservas_no_aprobadas_no_ocupan[pendiente]` | `7519869` |

### Requisito: Garantía de integridad contra solapamientos aprobados

| Escenario | Prueba | Commit |
|---|---|---|
| Dos reservas aprobadas solapadas en el mismo espacio | `test_repositorio_reservas.py::test_dos_aprobadas_solapadas_en_el_mismo_espacio` | `7519869` |
| Dos reservas aprobadas que solo comparten el extremo | `test_repositorio_reservas.py::test_inserciones_aceptadas[aprobadas_comparten_extremo]` | `7519869` |
| Reservas aprobadas con el mismo rango en espacios distintos | `test_repositorio_reservas.py::test_inserciones_aceptadas[aprobadas_en_espacios_distintos]` | `7519869` |
| Dos reservas pendientes solapadas | `test_repositorio_reservas.py::test_inserciones_aceptadas[pendientes_solapadas]` | `7519869` |
| Una reserva aprobada y una pendiente solapadas | `test_repositorio_reservas.py::test_inserciones_aceptadas[aprobada_y_pendiente_solapadas]` | `7519869` |
| Rango con fin igual o anterior al inicio | `test_reservas_esquema.py::test_un_rango_con_fin_igual_o_anterior_al_inicio_es_rechazado[fin_igual, fin_anterior]` | `7519869` |

### Requisito: Consulta de disponibilidad de un espacio por rango

| Escenario | Prueba | Commit |
|---|---|---|
| Disponibilidad devuelve los intervalos de reservas aprobadas | `test_servicio_reservas_disponibilidad.py::test_devuelve_los_intervalos_de_reservas_aprobadas_en_orden`; `test_reservas_api.py::test_disponibilidad_por_rol` (3 roles; solo `inicio` y `fin` en UTC); `test_repositorio_reservas.py::test_aprobadas_por_espacio_y_rango` | `7519869` |
| Disponibilidad ignora reservas que no están aprobadas | `test_servicio_reservas_disponibilidad.py::test_ignora_las_reservas_no_aprobadas` (3 estados) | `7519869` |
| Intervalo que solapa parcialmente el rango se devuelve completo | `test_servicio_reservas_disponibilidad.py::test_intervalo_parcial_se_devuelve_completo` | `7519869` |
| Reserva que solo toca el borde del rango | `test_servicio_reservas_disponibilidad.py::test_reserva_que_solo_toca_el_borde[borde_inicial, borde_final]` | `7519869` |
| Espacio sin reservas aprobadas en el rango | `test_servicio_reservas_disponibilidad.py::test_espacio_sin_reservas_aprobadas_devuelve_lista_vacia`; `test_reservas_api.py::test_disponibilidad_vacia_y_espacio_inactivo`; `test_repositorio_reservas.py::test_aprobadas_por_espacio_y_rango_sin_coincidencias` | `7519869` |
| Rango inválido | `test_servicio_reservas_disponibilidad.py::test_rango_invalido` (9 variantes); `test_reservas_api.py::test_disponibilidad_con_rango_invalido` (6 variantes) | `7519869` |
| Espacio inexistente en la consulta | `test_servicio_reservas_disponibilidad.py::test_espacio_inexistente` (2 variantes); `test_reservas_api.py::test_disponibilidad_de_un_espacio_inexistente` | `7519869` |
| Espacio inactivo en la consulta | `test_servicio_reservas_disponibilidad.py::test_espacio_inactivo_procede`; `test_reservas_api.py::test_disponibilidad_vacia_y_espacio_inactivo` | `7519869` |
| Consulta sin autenticación | `test_reservas_api.py::test_disponibilidad_sin_autenticacion` | `7519869` |

### Requisito: Listado y detalle de solicitudes

| Escenario | Prueba | Commit |
|---|---|---|
| Solicitante ve solo sus propias solicitudes | `test_servicio_reservas_consulta.py::test_solicitante_ve_solo_sus_solicitudes_en_orden`; `test_servicio_reservas_consulta.py::test_solicitante_sin_solicitudes_propias_aunque_existan_ajenas`; `test_reservas_api.py::test_listado_del_solicitante_solo_propias` | `7519869` |
| Aprobador ve todas las solicitudes | `test_servicio_reservas_consulta.py::test_aprobador_y_admin_ven_todas_en_orden[aprobador]`; `test_reservas_api.py::test_listado_de_aprobador_y_admin_todas[aprobador]` | `7519869` |
| Admin ve todas las solicitudes | `test_servicio_reservas_consulta.py::test_aprobador_y_admin_ven_todas_en_orden[admin]`; `test_reservas_api.py::test_listado_de_aprobador_y_admin_todas[admin]` | `7519869` |
| Orden del listado | `test_repositorio_reservas.py::test_listados_ordenados_por_inicio_y_luego_por_id`; `test_servicio_reservas_consulta.py::test_solicitante_ve_solo_sus_solicitudes_en_orden`; `test_servicio_reservas_consulta.py::test_aprobador_y_admin_ven_todas_en_orden` | `7519869` |
| Listado sin solicitudes | `test_servicio_reservas_consulta.py::test_listado_sin_solicitudes_visibles` (3 roles); `test_reservas_api.py::test_listado_vacio` (3 roles); `test_repositorio_reservas.py::test_listados_vacios` | `7519869` |
| Detalle de una solicitud propia | `test_servicio_reservas_consulta.py::test_detalle_de_una_solicitud_propia`; `test_reservas_api.py::test_detalle_propio` | `7519869` |
| Detalle de una solicitud ajena por un solicitante | `test_servicio_reservas_consulta.py::test_detalle_ajeno_por_un_solicitante`; `test_reservas_api.py::test_detalle_ajeno_por_un_solicitante` (sin datos de la solicitud) | `7519869` |
| Detalle de una solicitud ajena por aprobador o admin | `test_servicio_reservas_consulta.py::test_detalle_ajeno_por_aprobador_o_admin` (2 roles); `test_reservas_api.py::test_detalle_ajeno_por_aprobador_o_admin` (2 roles) | `7519869` |
| Detalle de una solicitud inexistente | `test_servicio_reservas_consulta.py::test_detalle_de_una_solicitud_inexistente` (6 variantes); `test_reservas_api.py::test_detalle_inexistente` (3 roles) | `7519869` |
| Consulta sin autenticación | `test_reservas_api.py::test_listado_y_detalle_sin_autenticacion` (listado y detalle) | `7519869` |

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

### Requisito: Consulta de espacios en la interfaz

| Escenario | Prueba | Commit |
|---|---|---|
| Listado con espacios activos e inactivos | `features/espacios/ConsultaEspacios.test.jsx` › Listado con espacios activos e inactivos › «muestra a un %s cada espacio con su nombre, tipo, capacidad y estado» (3 roles); «identifica los espacios inactivos como tales» | `5e9f0d0` |
| Catálogo sin espacios | `features/espacios/ConsultaEspacios.test.jsx` › Catálogo sin espacios › «muestra el catálogo vacío sin un mensaje de error» | `5e9f0d0` |
| Detalle de un espacio | `features/espacios/ConsultaEspacios.test.jsx` › Detalle de un espacio › «consulta GET /api/espacios/{id} y muestra su nombre, tipo, capacidad y estado» | `5e9f0d0` |
| Error al consultar un espacio inexistente | `features/espacios/ConsultaEspacios.test.jsx` › Error al consultar un espacio inexistente › «muestra el mensaje de espacio_no_encontrado y ningún dato de espacio» | `5e9f0d0` |

### Requisito: Alta y edición de espacios en la interfaz

| Escenario | Prueba | Commit |
|---|---|---|
| Alta correcta de un espacio | `features/espacios/FormularioEspacio.test.jsx` › Alta correcta de un espacio › «un %s envía nombre, tipo y capacidad y el catálogo muestra el espacio activo» (aprobador y admin) | `5e9f0d0` |
| Edición correcta de un espacio | `features/espacios/FormularioEspacio.test.jsx` › Edición correcta de un espacio › «envía PATCH con nombre, tipo y capacidad y el catálogo refleja los datos sin alterar el estado» | `5e9f0d0` |
| Mensajes de error del alta y de la edición | `features/espacios/FormularioEspacio.test.jsx` › Mensajes de error del alta y de la edición › «el alta muestra el mensaje de %s y no refleja el espacio como creado»; «la edición muestra el mensaje de %s y no refleja el espacio como modificado» (4 códigos cada una); «no valida en el navegador: envía al servidor lo escrito» | `5e9f0d0` |
| Acciones de alta y edición no ofrecidas a un rol sin permiso | `features/espacios/FormularioEspacio.test.jsx` › Acciones de alta y edición no ofrecidas a un rol sin permiso › «un solicitante no ve las acciones de alta ni de edición»; `features/espacios/permisos.test.js` › puedeGestionarEspacios | `5e9f0d0` |

### Requisito: Activación y desactivación de espacios en la interfaz

| Escenario | Prueba | Commit |
|---|---|---|
| Desactivación correcta de un espacio | `features/espacios/DesactivacionEspacios.test.jsx` › Desactivación correcta de un espacio › «un %s desactiva un espacio y el catálogo lo muestra inactivo conservando sus datos» (aprobador y admin) | `5e9f0d0` |
| Reactivación correcta de un espacio | `features/espacios/ReactivacionEspacios.test.jsx` › Reactivación correcta de un espacio › «un %s reactiva un espacio y el catálogo lo muestra activo conservando sus datos» (aprobador y admin) | `5e9f0d0` |
| Error al desactivar un espacio ya inactivo | `features/espacios/DesactivacionEspacios.test.jsx` › Error al desactivar un espacio ya inactivo › «muestra el mensaje de espacio_ya_inactivo y el catálogo mantiene el espacio inactivo» | `5e9f0d0` |
| Error al desactivar un espacio inexistente | `features/espacios/DesactivacionEspacios.test.jsx` › Error al desactivar un espacio inexistente › «muestra el mensaje de espacio_no_encontrado» | `5e9f0d0` |
| Acción de desactivación no ofrecida a un rol sin permiso | `features/espacios/DesactivacionEspacios.test.jsx` › Acción de desactivación no ofrecida a un rol sin permiso › «un solicitante no ve la acción de desactivación» | `5e9f0d0` |
| Acción de reactivación no ofrecida a un rol sin permiso | `features/espacios/ReactivacionEspacios.test.jsx` › Acción de reactivación no ofrecida a un rol sin permiso › «un solicitante no ve la acción de reactivación» | `5e9f0d0` |

### Requisito: Creación de solicitudes en la interfaz

| Escenario | Prueba | Commit |
|---|---|---|
| Acceso al formulario de creación | `features/reservas/CreacionSolicitud.test.jsx` › Acceso al formulario de creación › «un %s abre la sección desde la navegación y ve los campos de espacio, inicio y fin» (3 roles) | pendiente |
| Envío con zona horaria explícita | `features/reservas/CreacionSolicitud.test.jsx` › Envío con zona horaria explícita › «envía a POST /api/reservas el espacio y el inicio y el fin en ISO 8601 con zona horaria»; «la conversión conserva el instante del valor local y lo expresa en UTC» | pendiente |
| Creación correcta | `features/reservas/CreacionSolicitud.test.jsx` › Creación correcta › «un %s ve la solicitud creada en estado pendiente con las fechas en UTC» (3 roles) | pendiente |
| Mensajes de error de la creación | `features/reservas/CreacionSolicitud.test.jsx` › Mensajes de error de la creación › «con %i %s muestra el mensaje del servidor y ninguna solicitud creada» (4 códigos); «un error tras una creación correcta deja de mostrar la solicitud anterior»; › Envío con zona horaria explícita › «no valida en el navegador: con campos vacíos envía la petición y el servidor decide» | pendiente |

### Requisito: Consulta de disponibilidad en la interfaz

| Escenario | Prueba | Commit |
|---|---|---|
| Intervalos ocupados visibles | `features/reservas/ConsultaDisponibilidad.test.jsx` › Intervalos ocupados visibles › «consulta el rango con zona horaria explícita y muestra cada intervalo en UTC tal como llega»; «también está disponible para un %s desde la navegación» (aprobador y admin) | pendiente |
| Rango sin reservas aprobadas | `features/reservas/ConsultaDisponibilidad.test.jsx` › Rango sin reservas aprobadas › «con una lista vacía indica que no hay intervalos ocupados, sin mensaje de error» | pendiente |
| Error en la consulta | `features/reservas/ConsultaDisponibilidad.test.jsx` › Error en la consulta › «con %i %s muestra el mensaje del servidor y ningún intervalo» (2 códigos); «un error tras una consulta correcta deja de mostrar los intervalos anteriores»; «no valida en el navegador: sin fechas envía la consulta sin el rango y muestra datos_invalidos» | pendiente |

### Requisito: Listado de solicitudes en la interfaz

| Escenario | Prueba | Commit |
|---|---|---|
| Listado de un solicitante | `features/reservas/ListadoSolicitudes.test.jsx` › Listado de un solicitante › «muestra únicamente las solicitudes que devuelve la API, en su orden y con fechas en UTC» | pendiente |
| Listado de un aprobador o administrador | `features/reservas/ListadoSolicitudes.test.jsx` › Listado de un aprobador o administrador › «un %s ve todas las solicitudes que devuelve la API» (aprobador y admin) | pendiente |
| Listado vacío | `features/reservas/ListadoSolicitudes.test.jsx` › Listado vacío › «con una lista vacía muestra el listado vacío sin mensaje de error» | pendiente |

El requisito «Listado de solicitudes en la interfaz» exige además mostrar el mensaje del servidor cuando la consulta falla, aunque no tiene un escenario propio. Lo cubre `features/reservas/ListadoSolicitudes.test.jsx` › Error al consultar el listado › «muestra el mensaje del servidor y ningún listado».

Las pruebas de `interfaz-web` usan un backend simulado (`frontend/src/test/backendFalso.js`) que responde con los códigos y cuerpos del contrato de errores de la API. Verifican el comportamiento de la interfaz, no el del servidor, que cubren las pruebas de `pytest`.

---

## Pruebas de tareas sin escenario de spec

Estas pruebas verifican tareas de `tasks.md` (infraestructura, configuración y documentación) que no corresponden a ningún escenario de las specs. Se listan para que la matriz recoja todas las pruebas de la suite.

| Archivo | Change | Tarea | Commit |
|---|---|---|---|
| `backend/tests/test_app_factory.py` | `usuarios-roles-auth` | 1.1, 1.5, 1.6 | `3a79345` |
| `backend/tests/test_config.py` | `usuarios-roles-auth` | 1.3 (y `JWT_ACCESS_TOKEN_MINUTES`, ver observación 1) | `3a79345` |
| `backend/tests/test_cors.py` | `usuarios-roles-auth` | 1.7 | `3a79345` |
| `backend/tests/test_modelos.py` | `usuarios-roles-auth` | 2.1 | `d50687e` |
| `backend/tests/test_migraciones.py` | `usuarios-roles-auth` | 2.2 | `d50687e` |
| `backend/tests/test_repositorio_usuarios.py` | `usuarios-roles-auth` | 2.2 | `d50687e` |
| `backend/tests/test_readme.py` | `usuarios-roles-auth`; `espacios` | 5.7; 3.6 (generalizada a los módulos `usuarios` y `espacios`) | `150e108`, `4ea3b2a` |
| `backend/tests/test_espacios_esquema.py` | `espacios` | 1.1 | `9064d93` |
| `backend/tests/test_repositorio_espacios.py` | `espacios` | 1.2 | `9064d93` |
| `backend/tests/test_errores_espacios.py` | `espacios` | 2.1 | `08159a7` |
| `frontend/src/App.test.jsx` | `usuarios-roles-auth` | 1.7 | `3a79345` |
| `frontend/src/features/auth/almacenToken.test.jsx` | `usuarios-roles-auth` | 7.2 (almacenamiento del token sin `sessionStorage`) | `005a096` |
| `frontend/src/features/espacios/ConsultaEspacios.test.jsx` › Navegación a la sección de espacios | `espacios` | 4.1 (enlace «Espacios» visible para todos los roles) | `5e9f0d0` |
| `backend/tests/test_reservas_esquema.py` (extensión `btree_gist`, migraciones paso a paso, esquema, claves foráneas, exclusión e índices, DDL del modelo frente a las migraciones) | `reservas-disponibilidad` | 1.1, 1.2, 1.3 | `7519869` |
| `backend/tests/test_repositorio_reservas.py::test_crear_y_buscar_por_id`, `::test_buscar_un_id_inexistente_devuelve_none` | `reservas-disponibilidad` | 2.1 | `7519869` |
| `backend/tests/test_errores_reservas.py` | `reservas-disponibilidad` | 3.1 | `7519869` |
| `backend/tests/test_servicio_reservas_creacion.py::test_convertir_fecha_con_zona_horaria_a_utc`, `::test_espacio_id_que_no_es_un_entero`, `::test_cuerpo_que_no_es_un_objeto` | `reservas-disponibilidad` | 3.2 | `7519869` |
| `backend/tests/test_servicio_reservas_disponibilidad.py::test_otro_espacio_no_aparece`, `::test_el_rango_con_zona_horaria_se_convierte_a_utc` | `reservas-disponibilidad` | 3.5 | `7519869` |
| `backend/tests/test_reservas_api.py::test_creacion_con_cuerpo_que_no_es_un_objeto_json`, `::test_disponibilidad_con_desplazamiento_codificado_en_la_url`, `::test_las_fechas_se_serializan_en_utc_con_otra_zona_en_la_sesion` | `reservas-disponibilidad` | 4.1 | `7519869` |
| `backend/tests/test_readme.py` (módulo `reservas`) | `reservas-disponibilidad` | 4.2 | `7519869` |
| `frontend/src/features/reservas/CreacionSolicitud.test.jsx` › Envío con zona horaria explícita › «un identificador de espacio no numérico se envía tal como se escribió» | `reservas-disponibilidad` | 5.1 | pendiente |
| `frontend/src/features/reservas/ListadoSolicitudes.test.jsx` › Navegación al listado de solicitudes | `reservas-disponibilidad` | 5.3 (enlace «Solicitudes» visible para todos los roles) | pendiente |

Algunas pruebas de los archivos citados en las specs cubren casos que ningún escenario nombra, como la cuenta inexistente en edición, activación o restablecimiento (404), los campos no editables en la edición o la cuenta desactivada con contraseña incorrecta; en `espacios`, el límite técnico de la capacidad (2147483647), los nombres con tildes y eñe, los campos ajenos y los cuerpos que no son JSON. No figuran en las tablas anteriores porque no corresponden a un escenario.

## Observaciones

1. **«Vigencia configurada» (spec `auth`).** La revisión de la tarea 9.2 detectó que este escenario solo se probaba al nivel de la emisión del token. Para cubrir el recorrido completo se añadió `test_login.py::test_vigencia_configurada_en_el_login`, que ejecuta el login con `JWT_ACCESS_TOKEN_MINUTES=5` y comprueba que `expira_en` es 300.
2. **Errores HTTP fuera del contrato.** El manejador de errores (`backend/app/auth/errors.py`) traduce al formato JSON los errores 400, 404, 405 y 500. Cualquier otro error HTTP del framework (por ejemplo, 413 o 415) conserva la respuesta por defecto de Flask, que no tiene el formato `{"error": {...}}`. Con el código actual ninguna de esas respuestas es alcanzable: las rutas leen el cuerpo con `get_json(silent=True)` y no se configura un tamaño máximo de petición. Por eso no tienen prueba.
3. **Catálogo desactualizado en la interfaz de espacios (spec `interfaz-web`).** El escenario «Error al desactivar un espacio ya inactivo» y la prueba de `espacio_ya_activo` de la tarea 4.4 solo pueden darse cuando el catálogo mostrado está desactualizado, porque la interfaz ofrece desactivar solo los espacios activos y reactivar solo los inactivos. Para que el catálogo «mantenga» el estado real, la interfaz vuelve a pedir `GET /api/espacios` cuando la operación responde 404 o 409. Las pruebas simulan ese desfase: la primera consulta devuelve el estado anterior y la segunda el real.
