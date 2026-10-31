"""Servicio de consulta de disponibilidad (tarea 3.5).

Requisito «Consulta de disponibilidad de un espacio por rango» de la spec
`reservas`. Las reservas se siembran directamente en el repositorio.
"""

from datetime import datetime, timezone

import pytest

from backend.app.auth.errors import DatosInvalidos, EspacioNoEncontrado
from backend.app.espacios import services as servicio_espacios
from backend.app.reservas import services


def _h(hora, minuto=0):
    return datetime(2026, 11, 3, hora, minuto, tzinfo=timezone.utc)


RANGO = ("2026-11-03T08:00:00Z", "2026-11-03T18:00:00Z")


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio("Laboratorio A")


@pytest.fixture
def usuario(crear_cuenta):
    return crear_cuenta("solicitante")


def _intervalos(reservas):
    return [(r.inicio_utc, r.fin_utc) for r in reservas]


def test_devuelve_los_intervalos_de_reservas_aprobadas_en_orden(sesion, espacio, usuario,
                                                                 sembrar_reserva):
    sembrar_reserva(espacio, usuario, _h(14), _h(15))
    sembrar_reserva(espacio, usuario, _h(10), _h(12))

    ocupadas = services.consultar_disponibilidad(espacio, *RANGO)

    assert _intervalos(ocupadas) == [(_h(10), _h(12)), (_h(14), _h(15))]


@pytest.mark.parametrize("estado", ["pendiente", "rechazada", "cancelada"])
def test_ignora_las_reservas_no_aprobadas(sesion, espacio, usuario, sembrar_reserva, estado):
    sembrar_reserva(espacio, usuario, _h(10), _h(12), estado=estado)
    sembrar_reserva(espacio, usuario, _h(14), _h(15))

    assert _intervalos(services.consultar_disponibilidad(espacio, *RANGO)) == [(_h(14), _h(15))]


def test_intervalo_parcial_se_devuelve_completo(sesion, espacio, usuario, sembrar_reserva):
    sembrar_reserva(espacio, usuario, _h(7), _h(9))

    assert _intervalos(services.consultar_disponibilidad(espacio, *RANGO)) == [(_h(7), _h(9))]


@pytest.mark.parametrize("ocupada", [(6, 8), (18, 20)], ids=["borde_inicial", "borde_final"])
def test_reserva_que_solo_toca_el_borde(sesion, espacio, usuario, sembrar_reserva, ocupada):
    sembrar_reserva(espacio, usuario, _h(ocupada[0]), _h(ocupada[1]))

    assert services.consultar_disponibilidad(espacio, *RANGO) == []


def test_espacio_sin_reservas_aprobadas_devuelve_lista_vacia(sesion, espacio):
    assert services.consultar_disponibilidad(espacio, *RANGO) == []


def test_otro_espacio_no_aparece(sesion, espacio, nuevo_espacio, usuario, sembrar_reserva):
    sembrar_reserva(nuevo_espacio("Laboratorio B"), usuario, _h(10), _h(12))

    assert services.consultar_disponibilidad(espacio, *RANGO) == []


def test_el_rango_con_zona_horaria_se_convierte_a_utc(sesion, espacio, usuario,
                                                       sembrar_reserva):
    sembrar_reserva(espacio, usuario, _h(6), _h(8))
    # [03:00, 13:00) en -05:00 es [08:00, 18:00) UTC: la reserva solo toca el borde.
    assert services.consultar_disponibilidad(
        espacio, "2026-11-03T03:00:00-05:00", "2026-11-03T13:00:00-05:00") == []
    # [02:00, 13:00) en -05:00 es [07:00, 18:00) UTC: la reserva se solapa.
    assert _intervalos(services.consultar_disponibilidad(
        espacio, "2026-11-03T02:00:00-05:00", "2026-11-03T13:00:00-05:00")) == [(_h(6), _h(8))]


@pytest.mark.parametrize(
    "inicio,fin",
    [
        (None, RANGO[1]),
        (RANGO[0], None),
        (None, None),
        ("2026-11-03T08:00:00", RANGO[1]),
        (RANGO[0], "2026-11-03T18:00:00"),
        (RANGO[0], RANGO[0]),
        (RANGO[1], RANGO[0]),
        ("", RANGO[1]),
        ("no-es-fecha", RANGO[1]),
    ],
    ids=["sin_inicio", "sin_fin", "sin_ambos", "inicio_sin_zona", "fin_sin_zona", "fin_igual",
         "fin_anterior", "inicio_vacio", "inicio_mal_formado"],
)
def test_rango_invalido(sesion, espacio, inicio, fin):
    with pytest.raises(DatosInvalidos) as error:
        services.consultar_disponibilidad(espacio, inicio, fin)
    assert (error.value.http, error.value.codigo) == (400, "datos_invalidos")


@pytest.mark.parametrize("espacio_id", [999_999, 2_147_483_648])
def test_espacio_inexistente(sesion, espacio_id):
    with pytest.raises(EspacioNoEncontrado) as error:
        services.consultar_disponibilidad(espacio_id, *RANGO)
    assert (error.value.http, error.value.codigo) == (404, "espacio_no_encontrado")


def test_espacio_inactivo_procede(sesion, nuevo_espacio, usuario, sembrar_reserva):
    inactivo = nuevo_espacio("Auditorio")
    sembrar_reserva(inactivo, usuario, _h(10), _h(12))
    servicio_espacios.desactivar_espacio(inactivo)

    assert _intervalos(services.consultar_disponibilidad(inactivo, *RANGO)) == [(_h(10), _h(12))]
