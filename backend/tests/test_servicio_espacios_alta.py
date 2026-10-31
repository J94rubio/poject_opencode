"""Servicio de alta de espacios (tarea 2.2).

Requisitos «Registro de espacios académicos» y «Unicidad y normalización del
nombre del espacio» de la spec `espacios`.
"""

import pytest

from backend.app.auth.errors import (
    CapacidadInvalida,
    DatosInvalidos,
    EspacioDuplicado,
    TipoEspacioInvalido,
)
from backend.app.espacios import repositories, services

VALIDO = {"nombre": "Laboratorio de Física", "tipo": "laboratorio", "capacidad": 30}


def _con(**cambios):
    return {**VALIDO, **cambios}


def _sin(campo):
    return {k: v for k, v in VALIDO.items() if k != campo}


def _espacios(sesion):
    sesion.expire_all()
    return [(e.nombre, e.tipo, e.capacidad, e.estado) for e in repositories.listar_espacios()]


def _rechaza(sesion, datos, excepcion, http, codigo):
    antes = _espacios(sesion)
    with pytest.raises(excepcion) as error:
        services.crear_espacio(datos)
    assert (error.value.http, error.value.codigo) == (http, codigo)
    assert _espacios(sesion) == antes


# --- Alta válida ------------------------------------------------------------


def test_alta_valida_de_un_espacio(sesion):
    espacio = services.crear_espacio(dict(VALIDO))

    assert espacio.id is not None
    assert espacio.estado == "activo"
    assert _espacios(sesion) == [("Laboratorio de Física", "laboratorio", 30, "activo")]
    assert services.obtener_espacio(espacio.id).nombre == "Laboratorio de Física"


@pytest.mark.parametrize("tipo", ["laboratorio", "auditorio", "sala_de_computo"])
def test_alta_valida_con_cada_tipo_del_catalogo(sesion, tipo):
    assert services.crear_espacio(_con(tipo=tipo)).tipo == tipo


def test_alta_elimina_los_espacios_exteriores_del_nombre(sesion):
    assert services.crear_espacio(_con(nombre="  Sala 1  ")).nombre == "Sala 1"


# --- Capacidad --------------------------------------------------------------


@pytest.mark.parametrize(
    "capacidad",
    [0, -1, -30, 10.5, 10.0, "10", "diez", None, "", True, False, [10], {"n": 10}],
    ids=["cero", "negativa", "negativa_grande", "decimal", "decimal_exacto", "texto_numerico",
         "texto", "nula", "cadena_vacia", "booleano_true", "booleano_false", "lista", "objeto"],
)
def test_alta_con_capacidad_invalida(sesion, capacidad):
    _rechaza(sesion, _con(capacidad=capacidad), CapacidadInvalida, 400, "capacidad_invalida")


def test_alta_con_la_capacidad_maxima_de_integer_se_acepta(sesion):
    espacio = services.crear_espacio(_con(capacidad=2_147_483_647))

    assert _espacios(sesion) == [("Laboratorio de Física", "laboratorio", 2_147_483_647, "activo")]
    assert espacio.capacidad == 2_147_483_647


@pytest.mark.parametrize("capacidad", [2_147_483_648, 10**20])
def test_alta_con_capacidad_mayor_que_el_maximo_de_integer(sesion, capacidad):
    _rechaza(sesion, _con(capacidad=capacidad), CapacidadInvalida, 400, "capacidad_invalida")


# --- Tipo -------------------------------------------------------------------


@pytest.mark.parametrize("tipo", ["aula", "Laboratorio", " auditorio", "", None, 3])
def test_alta_con_tipo_fuera_del_catalogo(sesion, tipo):
    _rechaza(sesion, _con(tipo=tipo), TipoEspacioInvalido, 400, "tipo_espacio_invalido")


# --- Campos obligatorios, nombre y forma del cuerpo -------------------------


@pytest.mark.parametrize("campo", ["nombre", "tipo", "capacidad"])
def test_alta_con_campo_obligatorio_ausente(sesion, campo):
    _rechaza(sesion, _sin(campo), DatosInvalidos, 400, "datos_invalidos")


@pytest.mark.parametrize("nombre", ["", " ", "   \t  "])
def test_alta_con_nombre_vacio_o_solo_espacios(sesion, nombre):
    _rechaza(sesion, _con(nombre=nombre), DatosInvalidos, 400, "datos_invalidos")


@pytest.mark.parametrize("nombre", [None, 123, True, ["Sala"], {"n": "Sala"}])
def test_alta_con_nombre_que_no_es_texto(sesion, nombre):
    _rechaza(sesion, _con(nombre=nombre), DatosInvalidos, 400, "datos_invalidos")


@pytest.mark.parametrize("extra", [{"estado": "inactivo"}, {"estado": "activo"}, {"id": 99},
                                   {"color": "azul"}])
def test_alta_con_campo_ajeno_al_alta(sesion, extra):
    _rechaza(sesion, {**VALIDO, **extra}, DatosInvalidos, 400, "datos_invalidos")


@pytest.mark.parametrize("cuerpo", [None, [], "texto", 5, {}])
def test_alta_con_cuerpo_ausente_o_que_no_es_objeto(sesion, cuerpo):
    _rechaza(sesion, cuerpo, DatosInvalidos, 400, "datos_invalidos")


# --- Unicidad del nombre ----------------------------------------------------


def test_alta_con_nombre_ya_registrado(sesion):
    services.crear_espacio(dict(VALIDO))
    _rechaza(sesion, _con(tipo="auditorio"), EspacioDuplicado, 409, "espacio_duplicado")


@pytest.mark.parametrize(
    "nombre",
    ["LABORATORIO DE FÍSICA", "laboratorio de física", "  Laboratorio de Física  ",
     " lAbOrAtOrIo DE fÍsIcA\t"],
)
def test_duplicado_que_solo_difiere_en_mayusculas_o_espacios_exteriores(sesion, nombre):
    services.crear_espacio(dict(VALIDO))
    _rechaza(sesion, _con(nombre=nombre), EspacioDuplicado, 409, "espacio_duplicado")


def test_duplicado_con_tildes_y_enie(sesion):
    services.crear_espacio(_con(nombre="Sala Ñandú"))
    _rechaza(sesion, _con(nombre="  SALA ÑANDÚ  "), EspacioDuplicado, 409, "espacio_duplicado")


def test_el_indice_trata_como_iguales_los_nombres_con_tildes_y_enie(sesion):
    # Sin pasar por la comprobación del servicio: el índice único por sí solo
    # rechaza el duplicado y el servicio traduce la violación.
    services.crear_espacio(_con(nombre="Sala Ñandú"))
    sesion.expire_all()
    assert repositories.obtener_espacio_por_nombre("sala ñandú") is not None

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(repositories, "obtener_espacio_por_nombre", lambda _nombre: None)
        _rechaza(sesion, _con(nombre="  SALA ÑANDÚ  "), EspacioDuplicado, 409,
                 "espacio_duplicado")


def test_la_violacion_del_indice_unico_se_traduce_a_espacio_duplicado(sesion):
    # Simula la carrera de dos altas concurrentes: la comprobación previa no
    # ve el otro registro y el índice único resuelve el conflicto.
    services.crear_espacio(dict(VALIDO))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(repositories, "obtener_espacio_por_nombre", lambda _nombre: None)
        _rechaza(sesion, _con(nombre="LABORATORIO DE FÍSICA"), EspacioDuplicado, 409,
                 "espacio_duplicado")


def test_duplicado_contra_un_espacio_inactivo(sesion):
    espacio = services.crear_espacio(dict(VALIDO))
    services.desactivar_espacio(espacio.id)

    _rechaza(sesion, _con(nombre="laboratorio de física"), EspacioDuplicado, 409,
             "espacio_duplicado")
