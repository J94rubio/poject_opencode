"""Pruebas de integración del alta de espacios (tarea 3.2).

`POST /api/espacios` con el permiso `espacios:crear`. Requisitos «Registro de
espacios académicos», «Unicidad y normalización del nombre del espacio» y
«Control de acceso a la gestión de espacios» de la spec `espacios`.
"""

import pytest

from backend.app.espacios import repositories, services

VALIDO = {"nombre": "Lab 1", "tipo": "laboratorio", "capacidad": 20}


def _alta(client, cabecera=None, json=None, **kwargs):
    return client.post("/api/espacios", headers=cabecera, json=json, **kwargs)


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _espacios(sesion):
    sesion.expire_all()
    return [(e.nombre, e.tipo, e.capacidad, e.estado) for e in repositories.listar_espacios()]


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_alta_valida_de_un_espacio(client, sesion, crear_cuenta, cabecera, rol):
    autorizado = cabecera(crear_cuenta(rol))

    respuesta = _alta(client, autorizado, {"nombre": "  Lab 1  ", "tipo": "laboratorio",
                                           "capacidad": 20})

    assert respuesta.status_code == 201
    creado = respuesta.get_json()
    assert set(creado) == {"id", "nombre", "tipo", "capacidad", "estado"}
    assert creado == {"id": creado["id"], "nombre": "Lab 1", "tipo": "laboratorio",
                      "capacidad": 20, "estado": "activo"}
    # El espacio aparece en las consultas posteriores.
    assert client.get(f"/api/espacios/{creado['id']}", headers=autorizado).get_json() == creado
    assert client.get("/api/espacios", headers=autorizado).get_json() == [creado]


def test_alta_denegada_al_solicitante(client, sesion, crear_cuenta, cabecera):
    respuesta = _alta(client, cabecera(crear_cuenta("solicitante")), VALIDO)

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _espacios(sesion) == []


def test_alta_sin_autenticacion(client, sesion):
    respuesta = _alta(client, json=VALIDO)

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"
    assert _espacios(sesion) == []


@pytest.mark.parametrize(
    "cuerpo,http,codigo",
    [
        ({**VALIDO, "capacidad": 0}, 400, "capacidad_invalida"),
        ({**VALIDO, "capacidad": -5}, 400, "capacidad_invalida"),
        ({**VALIDO, "capacidad": 10.5}, 400, "capacidad_invalida"),
        ({**VALIDO, "capacidad": "veinte"}, 400, "capacidad_invalida"),
        ({**VALIDO, "capacidad": None}, 400, "capacidad_invalida"),
        ({**VALIDO, "capacidad": ""}, 400, "capacidad_invalida"),
        ({**VALIDO, "tipo": "oficina"}, 400, "tipo_espacio_invalido"),
        ({"tipo": "laboratorio", "capacidad": 20}, 400, "datos_invalidos"),
        ({"nombre": "Lab 1", "capacidad": 20}, 400, "datos_invalidos"),
        ({"nombre": "Lab 1", "tipo": "laboratorio"}, 400, "datos_invalidos"),
        ({**VALIDO, "nombre": "   "}, 400, "datos_invalidos"),
        ({**VALIDO, "estado": "inactivo"}, 400, "datos_invalidos"),
    ],
    ids=[
        "capacidad_cero", "capacidad_negativa", "capacidad_decimal", "capacidad_texto",
        "capacidad_nula", "capacidad_cadena_vacia", "tipo_fuera_del_catalogo", "sin_nombre",
        "sin_tipo", "sin_capacidad", "nombre_solo_espacios", "con_estado",
    ],
)
def test_alta_propaga_los_errores_400_del_servicio(
    client, sesion, crear_cuenta, cabecera, cuerpo, http, codigo
):
    respuesta = _alta(client, cabecera(crear_cuenta("aprobador")), cuerpo)

    assert respuesta.status_code == http
    assert _codigo(respuesta) == codigo
    assert _espacios(sesion) == []


def test_alta_con_cuerpo_que_no_es_json(client, sesion, crear_cuenta, cabecera):
    respuesta = _alta(client, cabecera(crear_cuenta("aprobador")), data="no-json",
                      content_type="application/json")

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _espacios(sesion) == []


@pytest.mark.parametrize("nombre", ["Lab 1", "  LAB 1 "])
@pytest.mark.parametrize("inactivo", [False, True], ids=["contra_activo", "contra_inactivo"])
def test_alta_propaga_el_error_409_de_nombre_duplicado(
    client, sesion, crear_cuenta, cabecera, nombre, inactivo
):
    existente = services.crear_espacio(VALIDO)
    if inactivo:
        services.desactivar_espacio(existente.id)
    antes = _espacios(sesion)

    respuesta = _alta(client, cabecera(crear_cuenta("admin")),
                      {"nombre": nombre, "tipo": "auditorio", "capacidad": 80})

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "espacio_duplicado"
    assert _espacios(sesion) == antes
