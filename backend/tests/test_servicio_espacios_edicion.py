"""Servicio de edición parcial de espacios (tarea 2.4).

Requisito «Edición de espacios académicos» de la spec `espacios`.
"""

import pytest

from backend.app.auth.errors import (
    CapacidadInvalida,
    DatosInvalidos,
    EspacioDuplicado,
    EspacioNoEncontrado,
    TipoEspacioInvalido,
)
from backend.app.espacios import repositories, services


@pytest.fixture
def espacio_id(sesion):
    return services.crear_espacio(
        {"nombre": "Laboratorio A", "tipo": "laboratorio", "capacidad": 30}
    ).id


@pytest.fixture
def otro_id(sesion):
    return services.crear_espacio(
        {"nombre": "Auditorio Central", "tipo": "auditorio", "capacidad": 200}
    ).id


def _foto(sesion, espacio_id):
    sesion.expire_all()
    e = repositories.obtener_espacio_por_id(espacio_id)
    return (e.nombre, e.tipo, e.capacidad, e.estado, e.actualizado_en)


def _datos(sesion, espacio_id):
    return _foto(sesion, espacio_id)[:4]


def _rechaza(sesion, espacio_id, datos, excepcion, http, codigo):
    antes = _foto(sesion, espacio_id)
    with pytest.raises(excepcion) as error:
        services.editar_espacio(espacio_id, datos)
    assert (error.value.http, error.value.codigo) == (http, codigo)
    assert _foto(sesion, espacio_id) == antes


# --- Ediciones válidas ------------------------------------------------------


def test_edicion_valida_de_nombre_tipo_y_capacidad(sesion, espacio_id):
    espacio = services.editar_espacio(
        espacio_id, {"nombre": "  Sala de cómputo B ", "tipo": "sala_de_computo", "capacidad": 40}
    )

    assert espacio.id == espacio_id
    assert _datos(sesion, espacio_id) == ("Sala de cómputo B", "sala_de_computo", 40, "activo")


def test_edicion_valida_no_cambia_el_estado_de_un_espacio_inactivo(sesion, espacio_id):
    services.desactivar_espacio(espacio_id)

    services.editar_espacio(espacio_id, {"nombre": "Lab Z", "tipo": "auditorio", "capacidad": 5})

    assert _datos(sesion, espacio_id) == ("Lab Z", "auditorio", 5, "inactivo")


def test_edicion_de_un_solo_campo(sesion, espacio_id):
    services.editar_espacio(espacio_id, {"capacidad": 45})

    assert _datos(sesion, espacio_id) == ("Laboratorio A", "laboratorio", 45, "activo")


@pytest.mark.parametrize("nombre", ["LABORATORIO A", "laboratorio a", "  Laboratorio A  "])
def test_edicion_que_conserva_el_propio_nombre(sesion, espacio_id, nombre):
    services.editar_espacio(espacio_id, {"nombre": nombre, "capacidad": 35})

    assert _datos(sesion, espacio_id) == (nombre.strip(), "laboratorio", 35, "activo")


def test_edicion_con_cuerpo_vacio_no_cambia_nada(sesion, espacio_id):
    antes = _datos(sesion, espacio_id)

    espacio = services.editar_espacio(espacio_id, {})

    assert espacio.id == espacio_id
    assert _datos(sesion, espacio_id) == antes


# --- Ediciones rechazadas ---------------------------------------------------


@pytest.mark.parametrize(
    "nombre", ["Auditorio Central", "AUDITORIO CENTRAL", "  auditorio central  "]
)
def test_edicion_con_el_nombre_de_otro_espacio(sesion, espacio_id, otro_id, nombre):
    _rechaza(sesion, espacio_id, {"nombre": nombre, "capacidad": 99},
             EspacioDuplicado, 409, "espacio_duplicado")


def test_edicion_con_el_nombre_de_otro_espacio_inactivo(sesion, espacio_id, otro_id):
    services.desactivar_espacio(otro_id)
    _rechaza(sesion, espacio_id, {"nombre": "auditorio central"},
             EspacioDuplicado, 409, "espacio_duplicado")


def test_edicion_con_el_nombre_de_otro_espacio_con_tildes_y_enie(sesion, espacio_id):
    services.crear_espacio({"nombre": "Sala Ñandú", "tipo": "auditorio", "capacidad": 10})
    _rechaza(sesion, espacio_id, {"nombre": "  SALA ÑANDÚ  "},
             EspacioDuplicado, 409, "espacio_duplicado")


def test_edicion_cuya_violacion_del_indice_se_traduce_a_espacio_duplicado(
    sesion, espacio_id, otro_id
):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(repositories, "obtener_espacio_por_nombre", lambda _nombre: None)
        _rechaza(sesion, espacio_id, {"nombre": "AUDITORIO CENTRAL"},
                 EspacioDuplicado, 409, "espacio_duplicado")


@pytest.mark.parametrize("nombre", ["", "   ", None, 7])
def test_edicion_con_nombre_vacio_o_que_no_es_texto(sesion, espacio_id, nombre):
    _rechaza(sesion, espacio_id, {"nombre": nombre}, DatosInvalidos, 400, "datos_invalidos")


@pytest.mark.parametrize("tipo", ["aula", "", None])
def test_edicion_con_tipo_fuera_del_catalogo(sesion, espacio_id, tipo):
    _rechaza(sesion, espacio_id, {"tipo": tipo, "capacidad": 50},
             TipoEspacioInvalido, 400, "tipo_espacio_invalido")


@pytest.mark.parametrize("capacidad", [0, -3, 2.5, "40", "", None, True])
def test_edicion_con_capacidad_invalida(sesion, espacio_id, capacidad):
    _rechaza(sesion, espacio_id, {"capacidad": capacidad},
             CapacidadInvalida, 400, "capacidad_invalida")


def test_edicion_con_la_capacidad_maxima_de_integer_se_acepta(sesion, espacio_id):
    services.editar_espacio(espacio_id, {"capacidad": 2_147_483_647})

    assert _datos(sesion, espacio_id) == ("Laboratorio A", "laboratorio", 2_147_483_647, "activo")


@pytest.mark.parametrize("capacidad", [2_147_483_648, 10**20])
def test_edicion_con_capacidad_mayor_que_el_maximo_de_integer(sesion, espacio_id, capacidad):
    _rechaza(sesion, espacio_id, {"capacidad": capacidad},
             CapacidadInvalida, 400, "capacidad_invalida")


@pytest.mark.parametrize("estado", ["inactivo", "activo"])
def test_edicion_que_intenta_cambiar_el_estado(sesion, espacio_id, estado):
    _rechaza(sesion, espacio_id, {"estado": estado, "capacidad": 50},
             DatosInvalidos, 400, "datos_invalidos")


@pytest.mark.parametrize("extra", [{"id": 99}, {"creado_en": "2026-01-01"}, {"color": "azul"}])
def test_edicion_con_campo_ajeno(sesion, espacio_id, extra):
    _rechaza(sesion, espacio_id, {"nombre": "Lab nuevo", **extra},
             DatosInvalidos, 400, "datos_invalidos")


@pytest.mark.parametrize("cuerpo", [None, [], "texto", 5])
def test_edicion_con_cuerpo_ausente_o_que_no_es_objeto(sesion, espacio_id, cuerpo):
    _rechaza(sesion, espacio_id, cuerpo, DatosInvalidos, 400, "datos_invalidos")


def test_edicion_de_un_espacio_inexistente(sesion, espacio_id):
    with pytest.raises(EspacioNoEncontrado) as error:
        services.editar_espacio(999, {"capacidad": 10})

    assert (error.value.http, error.value.codigo) == (404, "espacio_no_encontrado")
    sesion.expire_all()
    assert [e.id for e in repositories.listar_espacios()] == [espacio_id]
