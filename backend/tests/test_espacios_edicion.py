"""Pruebas de integración de la edición de espacios (tarea 3.3).

`PATCH /api/espacios/{id}` con el permiso `espacios:editar`. Requisitos
«Edición de espacios académicos» y «Control de acceso a la gestión de
espacios» de la spec `espacios`.
"""

import pytest

from backend.app.espacios import repositories, services


@pytest.fixture
def espacio_id(sesion):
    espacio = services.crear_espacio({"nombre": "Lab 1", "tipo": "laboratorio", "capacidad": 20})
    sesion.expire_all()
    return espacio.id


def _editar(client, cabecera, espacio_id, json=None, **kwargs):
    return client.patch(f"/api/espacios/{espacio_id}", headers=cabecera, json=json, **kwargs)


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _datos(sesion, espacio_id):
    sesion.expire_all()
    espacio = repositories.obtener_espacio_por_id(espacio_id)
    return (espacio.nombre, espacio.tipo, espacio.capacidad, espacio.estado)


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_edicion_valida_de_nombre_tipo_y_capacidad(
    client, sesion, crear_cuenta, cabecera, espacio_id, rol
):
    respuesta = _editar(client, cabecera(crear_cuenta(rol)), espacio_id,
                        {"nombre": " Auditorio Central ", "tipo": "auditorio", "capacidad": 200})

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": espacio_id, "nombre": "Auditorio Central", "tipo": "auditorio", "capacidad": 200,
        "estado": "activo",
    }
    assert _datos(sesion, espacio_id) == ("Auditorio Central", "auditorio", 200, "activo")


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_edicion_de_un_solo_campo(client, sesion, crear_cuenta, cabecera, espacio_id, rol):
    respuesta = _editar(client, cabecera(crear_cuenta(rol)), espacio_id, {"capacidad": 35})

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": espacio_id, "nombre": "Lab 1", "tipo": "laboratorio", "capacidad": 35,
        "estado": "activo",
    }
    assert _datos(sesion, espacio_id) == ("Lab 1", "laboratorio", 35, "activo")


def test_edicion_conserva_el_estado_de_un_espacio_inactivo(
    client, sesion, crear_cuenta, cabecera, espacio_id
):
    services.desactivar_espacio(espacio_id)

    respuesta = _editar(client, cabecera(crear_cuenta("aprobador")), espacio_id,
                        {"nombre": "Lab 1 bis", "tipo": "sala_de_computo", "capacidad": 30})

    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "inactivo"
    assert _datos(sesion, espacio_id) == ("Lab 1 bis", "sala_de_computo", 30, "inactivo")


def test_edicion_que_conserva_el_propio_nombre(client, sesion, crear_cuenta, cabecera, espacio_id):
    respuesta = _editar(client, cabecera(crear_cuenta("aprobador")), espacio_id,
                        {"nombre": "  LAB 1 ", "capacidad": 25})

    assert respuesta.status_code == 200
    assert _datos(sesion, espacio_id) == ("LAB 1", "laboratorio", 25, "activo")


@pytest.mark.parametrize("estado", ["inactivo", "activo"])
def test_edicion_que_intenta_cambiar_el_estado(
    client, sesion, crear_cuenta, cabecera, espacio_id, estado
):
    antes = _datos(sesion, espacio_id)

    respuesta = _editar(client, cabecera(crear_cuenta("admin")), espacio_id,
                        {"capacidad": 50, "estado": estado})

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _datos(sesion, espacio_id) == antes


def test_edicion_denegada_al_solicitante(client, sesion, crear_cuenta, cabecera, espacio_id):
    antes = _datos(sesion, espacio_id)

    respuesta = _editar(client, cabecera(crear_cuenta("solicitante")), espacio_id,
                        {"capacidad": 99})

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _datos(sesion, espacio_id) == antes


def test_edicion_sin_autenticacion(client, sesion, espacio_id):
    antes = _datos(sesion, espacio_id)

    respuesta = _editar(client, None, espacio_id, {"capacidad": 99})

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"
    assert _datos(sesion, espacio_id) == antes


@pytest.mark.parametrize(
    "cuerpo,codigo",
    [
        ({"nombre": ""}, "datos_invalidos"),
        ({"nombre": "   "}, "datos_invalidos"),
        ({"tipo": "oficina"}, "tipo_espacio_invalido"),
        ({"capacidad": 0}, "capacidad_invalida"),
        ({"capacidad": -3}, "capacidad_invalida"),
        ({"capacidad": 12.5}, "capacidad_invalida"),
        ({"capacidad": None}, "capacidad_invalida"),
        ({"capacidad": True}, "capacidad_invalida"),
    ],
    ids=[
        "nombre_vacio", "nombre_solo_espacios", "tipo_fuera_del_catalogo", "capacidad_cero",
        "capacidad_negativa", "capacidad_decimal", "capacidad_nula", "capacidad_booleana",
    ],
)
def test_edicion_propaga_los_errores_400_del_servicio(
    client, sesion, crear_cuenta, cabecera, espacio_id, cuerpo, codigo
):
    antes = _datos(sesion, espacio_id)

    respuesta = _editar(client, cabecera(crear_cuenta("aprobador")), espacio_id, cuerpo)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == codigo
    assert _datos(sesion, espacio_id) == antes


def test_edicion_con_cuerpo_que_no_es_json(client, sesion, crear_cuenta, cabecera, espacio_id):
    antes = _datos(sesion, espacio_id)

    respuesta = _editar(client, cabecera(crear_cuenta("aprobador")), espacio_id,
                        data="no-json", content_type="application/json")

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _datos(sesion, espacio_id) == antes


def test_edicion_con_el_nombre_de_otro_espacio(client, sesion, crear_cuenta, cabecera, espacio_id):
    services.crear_espacio({"nombre": "Auditorio 1", "tipo": "auditorio", "capacidad": 150})
    antes = _datos(sesion, espacio_id)

    respuesta = _editar(client, cabecera(crear_cuenta("aprobador")), espacio_id,
                        {"nombre": " auditorio 1 ", "capacidad": 40})

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "espacio_duplicado"
    assert _datos(sesion, espacio_id) == antes


def test_edicion_de_un_espacio_inexistente(client, sesion, crear_cuenta, cabecera):
    respuesta = _editar(client, cabecera(crear_cuenta("aprobador")), 999999, {"capacidad": 10})

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "espacio_no_encontrado"
    sesion.expire_all()
    assert repositories.listar_espacios() == []
