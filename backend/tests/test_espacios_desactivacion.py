"""Pruebas de integración de la desactivación de espacios (tarea 3.4).

`POST /api/espacios/{id}/desactivar` con el permiso `espacios:desactivar`.
Requisitos «Desactivación de espacios académicos» y «Control de acceso a la
gestión de espacios» de la spec `espacios`.
"""

import pytest

from backend.app.espacios import repositories, services


@pytest.fixture
def espacio_id(sesion):
    espacio = services.crear_espacio({"nombre": "Lab 1", "tipo": "laboratorio", "capacidad": 20})
    sesion.expire_all()
    return espacio.id


def _desactivar(client, cabecera, espacio_id):
    return client.post(f"/api/espacios/{espacio_id}/desactivar", headers=cabecera)


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _datos(sesion, espacio_id):
    sesion.expire_all()
    espacio = repositories.obtener_espacio_por_id(espacio_id)
    return (espacio.nombre, espacio.tipo, espacio.capacidad, espacio.estado)


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_desactivacion_de_un_espacio_activo(
    client, sesion, crear_cuenta, cabecera, espacio_id, rol
):
    respuesta = _desactivar(client, cabecera(crear_cuenta(rol)), espacio_id)

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": espacio_id, "nombre": "Lab 1", "tipo": "laboratorio", "capacidad": 20,
        "estado": "inactivo",
    }
    assert _datos(sesion, espacio_id) == ("Lab 1", "laboratorio", 20, "inactivo")


def test_conservacion_de_los_datos_tras_la_desactivacion(
    client, sesion, crear_cuenta, cabecera, espacio_id
):
    autorizado = cabecera(crear_cuenta("aprobador"))

    _desactivar(client, autorizado, espacio_id)

    assert client.get("/api/espacios", headers=autorizado).get_json() == [
        {"id": espacio_id, "nombre": "Lab 1", "tipo": "laboratorio", "capacidad": 20,
         "estado": "inactivo"},
    ]


def test_desactivacion_denegada_al_solicitante(client, sesion, crear_cuenta, cabecera, espacio_id):
    respuesta = _desactivar(client, cabecera(crear_cuenta("solicitante")), espacio_id)

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _datos(sesion, espacio_id) == ("Lab 1", "laboratorio", 20, "activo")


def test_desactivacion_sin_autenticacion(client, sesion, espacio_id):
    respuesta = _desactivar(client, None, espacio_id)

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"
    assert _datos(sesion, espacio_id) == ("Lab 1", "laboratorio", 20, "activo")


def test_desactivacion_de_un_espacio_ya_inactivo(
    client, sesion, crear_cuenta, cabecera, espacio_id
):
    autorizado = cabecera(crear_cuenta("aprobador"))
    _desactivar(client, autorizado, espacio_id)

    respuesta = _desactivar(client, autorizado, espacio_id)

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "espacio_ya_inactivo"
    assert _datos(sesion, espacio_id) == ("Lab 1", "laboratorio", 20, "inactivo")


def test_desactivacion_de_un_espacio_inexistente(client, sesion, crear_cuenta, cabecera):
    respuesta = _desactivar(client, cabecera(crear_cuenta("aprobador")), 999999)

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "espacio_no_encontrado"
