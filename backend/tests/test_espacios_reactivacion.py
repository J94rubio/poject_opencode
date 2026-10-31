"""Pruebas de integración de la reactivación de espacios (tarea 3.5).

`POST /api/espacios/{id}/activar` con el permiso `espacios:activar`.
Requisitos «Reactivación de espacios académicos» y «Control de acceso a la
gestión de espacios» de la spec `espacios`.
"""

import pytest

from backend.app.espacios import repositories, services


@pytest.fixture
def espacio_id(sesion):
    espacio = services.crear_espacio({"nombre": "Auditorio 1", "tipo": "auditorio",
                                      "capacidad": 150})
    services.desactivar_espacio(espacio.id)
    sesion.expire_all()
    return espacio.id


def _activar(client, cabecera, espacio_id):
    return client.post(f"/api/espacios/{espacio_id}/activar", headers=cabecera)


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _datos(sesion, espacio_id):
    sesion.expire_all()
    espacio = repositories.obtener_espacio_por_id(espacio_id)
    return (espacio.nombre, espacio.tipo, espacio.capacidad, espacio.estado)


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_reactivacion_de_un_espacio_inactivo(
    client, sesion, crear_cuenta, cabecera, espacio_id, rol
):
    respuesta = _activar(client, cabecera(crear_cuenta(rol)), espacio_id)

    assert respuesta.status_code == 200
    # Nombre, tipo y capacidad se conservan sin cambios.
    assert respuesta.get_json() == {
        "id": espacio_id, "nombre": "Auditorio 1", "tipo": "auditorio", "capacidad": 150,
        "estado": "activo",
    }
    assert _datos(sesion, espacio_id) == ("Auditorio 1", "auditorio", 150, "activo")


def test_reactivacion_denegada_al_solicitante(client, sesion, crear_cuenta, cabecera, espacio_id):
    respuesta = _activar(client, cabecera(crear_cuenta("solicitante")), espacio_id)

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _datos(sesion, espacio_id) == ("Auditorio 1", "auditorio", 150, "inactivo")


def test_reactivacion_sin_autenticacion(client, sesion, espacio_id):
    respuesta = _activar(client, None, espacio_id)

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"
    assert _datos(sesion, espacio_id) == ("Auditorio 1", "auditorio", 150, "inactivo")


def test_reactivacion_de_un_espacio_ya_activo(client, sesion, crear_cuenta, cabecera, espacio_id):
    autorizado = cabecera(crear_cuenta("aprobador"))
    _activar(client, autorizado, espacio_id)

    respuesta = _activar(client, autorizado, espacio_id)

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "espacio_ya_activo"
    assert _datos(sesion, espacio_id) == ("Auditorio 1", "auditorio", 150, "activo")


def test_reactivacion_de_un_espacio_inexistente(client, sesion, crear_cuenta, cabecera):
    respuesta = _activar(client, cabecera(crear_cuenta("aprobador")), 999999)

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "espacio_no_encontrado"
