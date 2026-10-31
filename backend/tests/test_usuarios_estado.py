"""Pruebas de la desactivación y activación de cuentas (tarea 5.5).

`POST /api/usuarios/{id}/desactivar` y `POST /api/usuarios/{id}/activar`.
Requisito «Desactivación y activación de cuentas» de la spec `usuarios` y
requisito «Revocación inmediata del acceso de una cuenta desactivada» de la
spec `auth`.
"""

import pytest

from backend.app.usuarios import repositories


@pytest.fixture
def admin_id(crear_cuenta):
    return crear_cuenta("admin")


@pytest.fixture
def objetivo_id(crear_cuenta):
    return crear_cuenta(
        "aprobador", nombre="Objetivo", correo="objetivo@example.com", contrasena="clave-objetivo"
    )


def _accion(client, cabecera, usuario_id, accion):
    return client.post(f"/api/usuarios/{usuario_id}/{accion}", headers=cabecera)


def _login(client):
    return client.post(
        "/api/auth/login", json={"correo": "objetivo@example.com", "contrasena": "clave-objetivo"}
    )


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _recargar(sesion, usuario_id):
    sesion.expire_all()
    return repositories.obtener_usuario_por_id(usuario_id)


def _datos(usuario):
    return (usuario.nombre, usuario.correo, usuario.rol.nombre, usuario.password_hash,
            usuario.creado_en)


# --- Desactivación ----------------------------------------------------------


def test_desactivacion_de_una_cuenta_activa(client, sesion, cabecera, admin_id, objetivo_id):
    respuesta = _accion(client, cabecera(admin_id), objetivo_id, "desactivar")

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": objetivo_id, "nombre": "Objetivo", "correo": "objetivo@example.com",
        "rol": "aprobador", "activo": False,
    }
    assert _recargar(sesion, objetivo_id).activo is False
    login = _login(client)
    assert login.status_code == 401
    assert _codigo(login) == "usuario_desactivado"


def test_desactivacion_revoca_el_acceso_de_inmediato(client, cabecera, admin_id, objetivo_id):
    cabecera_objetivo = cabecera(objetivo_id)
    assert client.get("/api/auth/me", headers=cabecera_objetivo).status_code == 200

    _accion(client, cabecera(admin_id), objetivo_id, "desactivar")

    respuesta = client.get("/api/auth/me", headers=cabecera_objetivo)
    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "usuario_desactivado"


def test_conservacion_de_los_datos_tras_desactivar(client, sesion, cabecera, admin_id, objetivo_id):
    antes = _datos(_recargar(sesion, objetivo_id))

    _accion(client, cabecera(admin_id), objetivo_id, "desactivar")

    assert _datos(_recargar(sesion, objetivo_id)) == antes


def test_desactivacion_de_la_cuenta_de_otro_administrador(
    client, sesion, crear_cuenta, cabecera, admin_id
):
    otro_admin_id = crear_cuenta("admin", correo="otro.admin@example.com")

    respuesta = _accion(client, cabecera(admin_id), otro_admin_id, "desactivar")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["activo"] is False
    assert _recargar(sesion, otro_admin_id).activo is False


def test_desactivacion_de_la_propia_cuenta(client, sesion, cabecera, admin_id):
    respuesta = _accion(client, cabecera(admin_id), admin_id, "desactivar")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "operacion_no_permitida"
    assert _recargar(sesion, admin_id).activo is True


def test_desactivacion_de_una_cuenta_inexistente(client, cabecera, admin_id):
    respuesta = _accion(client, cabecera(admin_id), 999999, "desactivar")

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "usuario_no_encontrado"


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_desactivacion_solicitada_por_un_rol_sin_permiso(
    client, sesion, crear_cuenta, cabecera, objetivo_id, rol
):
    usuario_id = crear_cuenta(rol, correo=f"{rol}-actor@example.com")

    respuesta = _accion(client, cabecera(usuario_id), objetivo_id, "desactivar")

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _recargar(sesion, objetivo_id).activo is True


# --- Reactivación -----------------------------------------------------------


def test_reactivacion_de_una_cuenta_desactivada(client, sesion, cabecera, admin_id, objetivo_id):
    _accion(client, cabecera(admin_id), objetivo_id, "desactivar")

    respuesta = _accion(client, cabecera(admin_id), objetivo_id, "activar")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["activo"] is True
    assert _recargar(sesion, objetivo_id).activo is True
    assert _login(client).status_code == 200


def test_reactivacion_antes_de_la_expiracion_del_token(client, cabecera, admin_id, objetivo_id):
    cabecera_objetivo = cabecera(objetivo_id)
    _accion(client, cabecera(admin_id), objetivo_id, "desactivar")
    assert client.get("/api/auth/me", headers=cabecera_objetivo).status_code == 401

    _accion(client, cabecera(admin_id), objetivo_id, "activar")

    assert client.get("/api/auth/me", headers=cabecera_objetivo).status_code == 200


def test_activacion_de_una_cuenta_inexistente(client, cabecera, admin_id):
    respuesta = _accion(client, cabecera(admin_id), 999999, "activar")

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "usuario_no_encontrado"


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_activacion_solicitada_por_un_rol_sin_permiso(
    client, sesion, crear_cuenta, cabecera, rol
):
    inactiva_id = crear_cuenta("solicitante", correo="inactiva@example.com", activo=False)
    usuario_id = crear_cuenta(rol, correo=f"{rol}-actor@example.com")

    respuesta = _accion(client, cabecera(usuario_id), inactiva_id, "activar")

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _recargar(sesion, inactiva_id).activo is False
