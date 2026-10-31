"""Pruebas de integración de la consulta de espacios (tarea 3.1).

`GET /api/espacios` y `GET /api/espacios/{id}` con el permiso `espacios:ver`.
Requisitos «Consulta del catálogo de espacios» y «Control de acceso a la
gestión de espacios» de la spec `espacios`.
"""

import pytest

from backend.app.espacios import services

ROLES = ["solicitante", "aprobador", "admin"]


def _crear(sesion, nombre, tipo="laboratorio", capacidad=20, inactivo=False):
    espacio = services.crear_espacio({"nombre": nombre, "tipo": tipo, "capacidad": capacidad})
    if inactivo:
        services.desactivar_espacio(espacio.id)
    sesion.expire_all()
    return espacio.id


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


@pytest.mark.parametrize("rol", ROLES)
def test_listado_con_espacios_activos_e_inactivos(client, sesion, crear_cuenta, cabecera, rol):
    activo_id = _crear(sesion, "Lab 1")
    inactivo_id = _crear(sesion, "Auditorio 1", "auditorio", 150, inactivo=True)

    respuesta = client.get("/api/espacios", headers=cabecera(crear_cuenta(rol)))

    assert respuesta.status_code == 200
    assert respuesta.get_json() == [
        {"id": activo_id, "nombre": "Lab 1", "tipo": "laboratorio", "capacidad": 20,
         "estado": "activo"},
        {"id": inactivo_id, "nombre": "Auditorio 1", "tipo": "auditorio", "capacidad": 150,
         "estado": "inactivo"},
    ]


def test_listado_sin_espacios_registrados(client, sesion, crear_cuenta, cabecera):
    respuesta = client.get("/api/espacios", headers=cabecera(crear_cuenta("solicitante")))

    assert respuesta.status_code == 200
    assert respuesta.get_json() == []


@pytest.mark.parametrize("rol", ROLES)
def test_detalle_de_un_espacio_existente(client, sesion, crear_cuenta, cabecera, rol):
    espacio_id = _crear(sesion, "Sala de cómputo 3", "sala_de_computo", 25)

    respuesta = client.get(f"/api/espacios/{espacio_id}", headers=cabecera(crear_cuenta(rol)))

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": espacio_id, "nombre": "Sala de cómputo 3", "tipo": "sala_de_computo",
        "capacidad": 25, "estado": "activo",
    }


def test_detalle_de_un_espacio_inactivo(client, sesion, crear_cuenta, cabecera):
    espacio_id = _crear(sesion, "Auditorio 2", "auditorio", 300, inactivo=True)

    respuesta = client.get(
        f"/api/espacios/{espacio_id}", headers=cabecera(crear_cuenta("solicitante"))
    )

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": espacio_id, "nombre": "Auditorio 2", "tipo": "auditorio", "capacidad": 300,
        "estado": "inactivo",
    }


def test_detalle_de_un_espacio_inexistente(client, sesion, crear_cuenta, cabecera):
    respuesta = client.get("/api/espacios/999999", headers=cabecera(crear_cuenta("solicitante")))

    assert respuesta.status_code == 404
    assert respuesta.get_json() == {
        "error": {"codigo": "espacio_no_encontrado", "mensaje": "El espacio solicitado no existe."}
    }


@pytest.mark.parametrize("ruta", ["/api/espacios", "/api/espacios/{id}"])
def test_consulta_sin_autenticacion(client, sesion, ruta):
    espacio_id = _crear(sesion, "Lab 1")

    respuesta = client.get(ruta.replace("{id}", str(espacio_id)))

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"
