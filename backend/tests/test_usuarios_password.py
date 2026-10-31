"""Pruebas del restablecimiento `POST /api/usuarios/{id}/password` (tarea 5.4).

Requisito «Restablecimiento de contraseña por el administrador» de la spec
`usuarios`.
"""

import pytest

from backend.app.usuarios import repositories

CONTRASENA_VIGENTE = "contrasena-valida"
CONTRASENA_NUEVA = "nueva-clave"


@pytest.fixture
def admin_id(crear_cuenta):
    return crear_cuenta("admin")


@pytest.fixture
def objetivo_id(crear_cuenta):
    return crear_cuenta("solicitante", correo="objetivo@example.com")


def _restablecer(client, cabecera, usuario_id, cuerpo):
    return client.post(f"/api/usuarios/{usuario_id}/password", json=cuerpo, headers=cabecera)


def _login(client, contrasena):
    return client.post(
        "/api/auth/login", json={"correo": "objetivo@example.com", "contrasena": contrasena}
    )


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _hash(sesion, usuario_id):
    sesion.expire_all()
    return repositories.obtener_usuario_por_id(usuario_id).password_hash


def test_restablecimiento_valido(client, cabecera, admin_id, objetivo_id):
    respuesta = _restablecer(
        client, cabecera(admin_id), objetivo_id, {"contrasena": CONTRASENA_NUEVA}
    )

    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == ""
    assert _login(client, CONTRASENA_NUEVA).status_code == 200
    assert _login(client, CONTRASENA_VIGENTE).status_code == 401


def test_restablecimiento_guarda_solo_el_hash(client, sesion, cabecera, admin_id, objetivo_id):
    _restablecer(client, cabecera(admin_id), objetivo_id, {"contrasena": CONTRASENA_NUEVA})

    assert _hash(sesion, objetivo_id) != CONTRASENA_NUEVA


@pytest.mark.parametrize("contrasena", ["corta", "1234567"])
def test_contrasena_que_no_cumple_la_politica(
    client, sesion, cabecera, admin_id, objetivo_id, contrasena
):
    hash_antes = _hash(sesion, objetivo_id)

    respuesta = _restablecer(client, cabecera(admin_id), objetivo_id, {"contrasena": contrasena})

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "contrasena_invalida"
    assert _hash(sesion, objetivo_id) == hash_antes
    assert _login(client, CONTRASENA_VIGENTE).status_code == 200


def test_restablecimiento_sin_contrasena(client, sesion, cabecera, admin_id, objetivo_id):
    hash_antes = _hash(sesion, objetivo_id)

    respuesta = _restablecer(client, cabecera(admin_id), objetivo_id, {})

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _hash(sesion, objetivo_id) == hash_antes


def test_restablecimiento_de_una_cuenta_inexistente(client, cabecera, admin_id):
    respuesta = _restablecer(client, cabecera(admin_id), 999999, {"contrasena": CONTRASENA_NUEVA})

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "usuario_no_encontrado"


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_restablecimiento_solicitado_por_un_rol_sin_permiso(
    client, sesion, crear_cuenta, cabecera, objetivo_id, rol
):
    usuario_id = crear_cuenta(rol, correo=f"{rol}-actor@example.com")
    hash_antes = _hash(sesion, objetivo_id)

    respuesta = _restablecer(
        client, cabecera(usuario_id), objetivo_id, {"contrasena": CONTRASENA_NUEVA}
    )

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _hash(sesion, objetivo_id) == hash_antes
