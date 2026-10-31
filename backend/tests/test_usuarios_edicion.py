"""Pruebas de la edición `PATCH /api/usuarios/{id}` (tarea 5.3).

Requisito «Edición de los datos de una cuenta» de la spec `usuarios`.
"""

import pytest

from backend.app.auth.services import verificar_password
from backend.app.usuarios import repositories


@pytest.fixture
def admin_id(crear_cuenta):
    return crear_cuenta("admin")


@pytest.fixture
def objetivo_id(crear_cuenta):
    return crear_cuenta("solicitante", nombre="Original", correo="original@example.com")


def _editar(client, cabecera, usuario_id, **cuerpo):
    return client.patch(f"/api/usuarios/{usuario_id}", json=cuerpo, headers=cabecera)


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _recargar(sesion, usuario_id):
    sesion.expire_all()
    return repositories.obtener_usuario_por_id(usuario_id)


def _foto(usuario):
    """Estado completo de la cuenta, para comprobar que nada cambia."""
    return (usuario.nombre, usuario.correo, usuario.rol_id, usuario.activo,
            usuario.password_hash, usuario.actualizado_en)


# --- Cambios válidos --------------------------------------------------------


def test_cambio_de_nombre(client, sesion, cabecera, admin_id, objetivo_id):
    respuesta = _editar(client, cabecera(admin_id), objetivo_id, nombre="Nuevo nombre")

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": objetivo_id, "nombre": "Nuevo nombre", "correo": "original@example.com",
        "rol": "solicitante", "activo": True,
    }
    assert _recargar(sesion, objetivo_id).nombre == "Nuevo nombre"


def test_cambio_de_correo_se_guarda_en_minusculas(client, sesion, cabecera, admin_id, objetivo_id):
    respuesta = _editar(client, cabecera(admin_id), objetivo_id, correo="Nuevo@Example.com")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["correo"] == "nuevo@example.com"
    assert _recargar(sesion, objetivo_id).correo == "nuevo@example.com"


def test_cambio_de_correo_al_mismo_correo_en_otro_caso(client, cabecera, admin_id, objetivo_id):
    respuesta = _editar(client, cabecera(admin_id), objetivo_id, correo="ORIGINAL@example.com")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["correo"] == "original@example.com"


def test_cambio_de_rol(client, sesion, cabecera, admin_id, objetivo_id):
    cabecera_objetivo = cabecera(objetivo_id)
    assert client.get("/api/usuarios", headers=cabecera_objetivo).status_code == 403

    respuesta = _editar(client, cabecera(admin_id), objetivo_id, rol="admin")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["rol"] == "admin"
    assert _recargar(sesion, objetivo_id).rol.nombre == "admin"
    # El rol nuevo se aplica a la siguiente petición con el mismo token.
    assert client.get("/api/usuarios", headers=cabecera_objetivo).status_code == 200


def test_la_edicion_no_altera_estado_ni_contrasena(client, sesion, cabecera, admin_id, objetivo_id):
    hash_antes = _recargar(sesion, objetivo_id).password_hash

    respuesta = _editar(
        client, cabecera(admin_id), objetivo_id,
        nombre="Otro", correo="otro@example.com", rol="aprobador",
    )

    assert respuesta.status_code == 200
    usuario = _recargar(sesion, objetivo_id)
    assert usuario.activo is True
    assert usuario.password_hash == hash_antes
    assert verificar_password(usuario.password_hash, "contrasena-valida")


def test_edicion_con_cuerpo_vacio_no_cambia_nada(client, sesion, cabecera, admin_id, objetivo_id):
    antes = _foto(_recargar(sesion, objetivo_id))

    respuesta = _editar(client, cabecera(admin_id), objetivo_id)

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": objetivo_id, "nombre": "Original", "correo": "original@example.com",
        "rol": "solicitante", "activo": True,
    }
    assert _foto(_recargar(sesion, objetivo_id)) == antes


def test_el_admin_puede_editar_su_propio_nombre(client, cabecera, admin_id):
    respuesta = _editar(client, cabecera(admin_id), admin_id, nombre="Admin renombrado")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["nombre"] == "Admin renombrado"


# --- Rechazos ---------------------------------------------------------------


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"nombre": "Otro", "activo": False},
        {"nombre": "Otro", "contrasena": "otra-contrasena"},
        {"nombre": "Otro", "campo_desconocido": "x"},
    ],
    ids=["campo_activo", "campo_contrasena", "campo_desconocido"],
)
def test_edicion_con_campo_no_editable(client, sesion, cabecera, admin_id, objetivo_id, cuerpo):
    antes = _foto(_recargar(sesion, objetivo_id))

    respuesta = _editar(client, cabecera(admin_id), objetivo_id, **cuerpo)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    usuario = _recargar(sesion, objetivo_id)
    assert _foto(usuario) == antes
    assert usuario.activo is True
    assert verificar_password(usuario.password_hash, "contrasena-valida")


def test_cambio_de_correo_a_uno_ya_registrado(
    client, sesion, crear_cuenta, cabecera, admin_id, objetivo_id
):
    crear_cuenta("aprobador", correo="ocupado@example.com")

    respuesta = _editar(client, cabecera(admin_id), objetivo_id, correo="Ocupado@example.com")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "correo_duplicado"
    assert _recargar(sesion, objetivo_id).correo == "original@example.com"


@pytest.mark.parametrize("rol", ["superusuario", "", None])
def test_cambio_de_rol_fuera_del_catalogo(client, sesion, cabecera, admin_id, objetivo_id, rol):
    respuesta = _editar(client, cabecera(admin_id), objetivo_id, rol=rol)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "rol_invalido"
    assert _recargar(sesion, objetivo_id).rol.nombre == "solicitante"


@pytest.mark.parametrize(
    "cuerpo",
    [{"nombre": ""}, {"nombre": None}, {"correo": "no-es-correo"}, {"correo": None}],
    ids=["nombre_vacio", "nombre_nulo", "correo_invalido", "correo_nulo"],
)
def test_edicion_con_datos_invalidos(client, sesion, cabecera, admin_id, objetivo_id, cuerpo):
    respuesta = _editar(client, cabecera(admin_id), objetivo_id, **cuerpo)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    usuario = _recargar(sesion, objetivo_id)
    assert (usuario.nombre, usuario.correo) == ("Original", "original@example.com")


def test_cambio_del_propio_rol(client, sesion, cabecera, admin_id):
    respuesta = _editar(client, cabecera(admin_id), admin_id, rol="solicitante")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "operacion_no_permitida"
    assert _recargar(sesion, admin_id).rol.nombre == "admin"


def test_cambio_del_propio_rol_no_aplica_ningun_otro_cambio(client, sesion, cabecera, admin_id):
    respuesta = _editar(client, cabecera(admin_id), admin_id, nombre="Otro", rol="aprobador")

    assert respuesta.status_code == 409
    usuario = _recargar(sesion, admin_id)
    assert (usuario.nombre, usuario.rol.nombre) == ("Persona", "admin")


def test_edicion_de_una_cuenta_inexistente(client, cabecera, admin_id):
    respuesta = _editar(client, cabecera(admin_id), 999999, nombre="Nadie")

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "usuario_no_encontrado"


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_edicion_solicitada_por_un_rol_sin_permiso(
    client, sesion, crear_cuenta, cabecera, objetivo_id, rol
):
    usuario_id = crear_cuenta(rol, correo=f"{rol}-actor@example.com")

    respuesta = _editar(
        client, cabecera(usuario_id), objetivo_id,
        nombre="Modificado", correo="modificado@example.com", rol="admin",
    )

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    usuario = _recargar(sesion, objetivo_id)
    assert (usuario.nombre, usuario.correo, usuario.rol.nombre) == (
        "Original", "original@example.com", "solicitante",
    )
