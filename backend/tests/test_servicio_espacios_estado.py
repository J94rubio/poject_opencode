"""Servicios de desactivación y reactivación de espacios (tareas 2.5 y 2.6).

Requisitos «Desactivación de espacios académicos» y «Reactivación de espacios
académicos» de la spec `espacios`.
"""

import pytest

from backend.app.auth.errors import EspacioNoEncontrado, EspacioYaActivo, EspacioYaInactivo
from backend.app.espacios import repositories, services


@pytest.fixture
def espacio_id(sesion):
    return services.crear_espacio(
        {"nombre": "Laboratorio de Redes", "tipo": "laboratorio", "capacidad": 24}
    ).id


def _foto(sesion, espacio_id):
    sesion.expire_all()
    e = repositories.obtener_espacio_por_id(espacio_id)
    return (e.nombre, e.tipo, e.capacidad, e.estado, e.actualizado_en)


def _en_listado(sesion, espacio_id):
    sesion.expire_all()
    return [(e.nombre, e.tipo, e.capacidad, e.estado)
            for e in services.listar_espacios() if e.id == espacio_id]


def _rechaza(sesion, operacion, espacio_id, excepcion, http, codigo):
    antes = _foto(sesion, espacio_id)
    with pytest.raises(excepcion) as error:
        operacion(espacio_id)
    assert (error.value.http, error.value.codigo) == (http, codigo)
    assert _foto(sesion, espacio_id) == antes


# --- Desactivación (2.5) ----------------------------------------------------


def test_desactivacion_de_un_espacio_activo(sesion, espacio_id):
    espacio = services.desactivar_espacio(espacio_id)

    assert (espacio.id, espacio.estado) == (espacio_id, "inactivo")


def test_conservacion_de_los_datos_tras_la_desactivacion(sesion, espacio_id):
    services.desactivar_espacio(espacio_id)

    assert _foto(sesion, espacio_id)[:4] == ("Laboratorio de Redes", "laboratorio", 24, "inactivo")
    assert _en_listado(sesion, espacio_id) == [
        ("Laboratorio de Redes", "laboratorio", 24, "inactivo")
    ]


def test_desactivacion_de_un_espacio_ya_inactivo(sesion, espacio_id):
    services.desactivar_espacio(espacio_id)
    _rechaza(sesion, services.desactivar_espacio, espacio_id,
             EspacioYaInactivo, 409, "espacio_ya_inactivo")


def test_desactivacion_de_un_espacio_inexistente(sesion):
    with pytest.raises(EspacioNoEncontrado) as error:
        services.desactivar_espacio(999)

    assert (error.value.http, error.value.codigo) == (404, "espacio_no_encontrado")


# --- Reactivación (2.6) -----------------------------------------------------


def test_reactivacion_de_un_espacio_inactivo(sesion, espacio_id):
    services.desactivar_espacio(espacio_id)

    espacio = services.activar_espacio(espacio_id)

    assert (espacio.id, espacio.estado) == (espacio_id, "activo")
    assert _foto(sesion, espacio_id)[:4] == ("Laboratorio de Redes", "laboratorio", 24, "activo")


def test_reactivacion_aparece_en_el_listado_como_activo(sesion, espacio_id):
    services.desactivar_espacio(espacio_id)
    services.activar_espacio(espacio_id)

    assert _en_listado(sesion, espacio_id) == [
        ("Laboratorio de Redes", "laboratorio", 24, "activo")
    ]


def test_reactivacion_de_un_espacio_ya_activo(sesion, espacio_id):
    _rechaza(sesion, services.activar_espacio, espacio_id,
             EspacioYaActivo, 409, "espacio_ya_activo")


def test_reactivacion_de_un_espacio_inexistente(sesion):
    with pytest.raises(EspacioNoEncontrado) as error:
        services.activar_espacio(999)

    assert (error.value.http, error.value.codigo) == (404, "espacio_no_encontrado")
