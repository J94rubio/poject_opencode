"""Servicio de consulta de espacios (tarea 2.3).

Requisito «Consulta del catálogo de espacios» de la spec `espacios`.
"""

import pytest

from backend.app.auth.errors import EspacioNoEncontrado
from backend.app.espacios import services


def _crear(nombre, tipo="laboratorio", capacidad=20):
    return services.crear_espacio({"nombre": nombre, "tipo": tipo, "capacidad": capacidad})


def test_listado_con_espacios_activos_e_inactivos(sesion):
    activo = _crear("Lab 1")
    inactivo = _crear("Auditorio 1", "auditorio", 150)
    services.desactivar_espacio(inactivo.id)
    sesion.expire_all()

    listado = services.listar_espacios()

    assert [(e.id, e.nombre, e.tipo, e.capacidad, e.estado) for e in listado] == [
        (activo.id, "Lab 1", "laboratorio", 20, "activo"),
        (inactivo.id, "Auditorio 1", "auditorio", 150, "inactivo"),
    ]


def test_listado_sin_espacios_registrados(sesion):
    assert services.listar_espacios() == []


def test_detalle_de_un_espacio_existente(sesion):
    espacio_id = _crear("Sala de cómputo 3", "sala_de_computo", 25).id
    sesion.expire_all()

    espacio = services.obtener_espacio(espacio_id)

    assert (espacio.nombre, espacio.tipo, espacio.capacidad, espacio.estado) == (
        "Sala de cómputo 3", "sala_de_computo", 25, "activo",
    )


def test_detalle_de_un_espacio_inactivo(sesion):
    espacio_id = _crear("Lab 2", capacidad=12).id
    services.desactivar_espacio(espacio_id)
    sesion.expire_all()

    espacio = services.obtener_espacio(espacio_id)

    assert (espacio.nombre, espacio.capacidad, espacio.estado) == ("Lab 2", 12, "inactivo")


def test_detalle_de_un_espacio_inexistente(sesion):
    with pytest.raises(EspacioNoEncontrado) as error:
        services.obtener_espacio(999)

    assert (error.value.http, error.value.codigo) == (404, "espacio_no_encontrado")
