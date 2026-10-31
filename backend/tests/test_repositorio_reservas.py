"""Repositorio de reservas contra reservas_test (tareas 2.1 y 2.2).

Requisitos «Listado y detalle de solicitudes», «Consulta de disponibilidad de
un espacio por rango» y «Garantía de integridad contra solapamientos
aprobados» de la spec `reservas`. Las reservas se insertan directamente.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.reservas import repositories


def _h(hora, minuto=0):
    return datetime(2026, 11, 3, hora, minuto, tzinfo=timezone.utc)


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio("Laboratorio A")


@pytest.fixture
def otro_espacio(nuevo_espacio):
    return nuevo_espacio("Laboratorio B")


@pytest.fixture
def ana(crear_cuenta):
    return crear_cuenta("solicitante", correo="ana@example.com")


@pytest.fixture
def luis(crear_cuenta):
    return crear_cuenta("solicitante", correo="luis@example.com")


def _rangos(reservas):
    return [(r.inicio_utc, r.fin_utc) for r in reservas]


# --- 2.1 Métodos del repositorio ---------------------------------------------


def test_crear_y_buscar_por_id(sesion, espacio, ana):
    creada = repositories.crear(espacio, ana, _h(10), _h(12))
    sesion.commit()
    reserva_id = creada.id
    sesion.expunge_all()

    reserva = repositories.buscar_por_id(reserva_id)

    assert (reserva.espacio_id, reserva.solicitante_id, reserva.estado) == (
        espacio, ana, "pendiente")
    assert (reserva.inicio_utc, reserva.fin_utc) == (_h(10), _h(12))
    assert reserva.inicio_utc.utcoffset() is not None


def test_buscar_un_id_inexistente_devuelve_none(sesion):
    assert repositories.buscar_por_id(999) is None


def test_listados_ordenados_por_inicio_y_luego_por_id(sesion, espacio, ana, luis):
    tarde = repositories.crear(espacio, ana, _h(15), _h(16)).id
    temprano_a = repositories.crear(espacio, luis, _h(8), _h(9)).id
    temprano_b = repositories.crear(espacio, ana, _h(8), _h(10)).id
    media = repositories.crear(espacio, ana, _h(11), _h(12), estado="aprobada").id
    sesion.commit()
    sesion.expunge_all()

    assert [r.id for r in repositories.listar_todas()] == [temprano_a, temprano_b, media, tarde]
    assert [r.id for r in repositories.listar_por_solicitante(ana)] == [temprano_b, media, tarde]
    assert [r.id for r in repositories.listar_por_solicitante(luis)] == [temprano_a]


def test_listados_vacios(sesion, ana):
    assert repositories.listar_todas() == []
    assert repositories.listar_por_solicitante(ana) == []


def test_aprobadas_por_espacio_y_rango(sesion, espacio, otro_espacio, ana):
    # Dentro, en orden inverso de inserción para comprobar el orden ascendente.
    repositories.crear(espacio, ana, _h(14), _h(15), estado="aprobada")
    repositories.crear(espacio, ana, _h(10), _h(12), estado="aprobada")
    # Solapa parcialmente el inicio y el fin del rango: se devuelven completas.
    repositories.crear(espacio, ana, _h(7), _h(9), estado="aprobada")
    repositories.crear(espacio, ana, _h(17), _h(19), estado="aprobada")
    # Las que solo tocan los bordes del rango se prueban aparte: solaparían con
    # las anteriores y la restricción de exclusión las rechazaría.
    # No aprobadas o de otro espacio: excluidas.
    for estado in ("pendiente", "rechazada", "cancelada"):
        repositories.crear(espacio, ana, _h(12), _h(13), estado=estado)
    repositories.crear(otro_espacio, ana, _h(12), _h(13), estado="aprobada")
    sesion.commit()
    sesion.expunge_all()

    ocupadas = repositories.listar_aprobadas_por_espacio_y_rango(espacio, _h(8), _h(18))

    assert _rangos(ocupadas) == [(_h(7), _h(9)), (_h(10), _h(12)), (_h(14), _h(15)),
                                 (_h(17), _h(19))]
    assert {r.estado for r in ocupadas} == {"aprobada"}


def test_aprobadas_por_espacio_y_rango_sin_coincidencias(sesion, espacio, ana):
    # Solo tocan el inicio y el fin del rango consultado: excluidas.
    repositories.crear(espacio, ana, _h(6), _h(8), estado="aprobada")
    repositories.crear(espacio, ana, _h(18), _h(20), estado="aprobada")
    sesion.commit()

    assert repositories.listar_aprobadas_por_espacio_y_rango(espacio, _h(8), _h(18)) == []


# --- 2.2 Garantía de integridad contra solapamientos aprobados ----------------


def test_dos_aprobadas_solapadas_en_el_mismo_espacio(sesion, espacio, ana, luis):
    primera = repositories.crear(espacio, ana, _h(10), _h(12), estado="aprobada").id
    sesion.commit()

    with pytest.raises(IntegrityError) as error:
        repositories.crear(espacio, luis, _h(11), _h(13), estado="aprobada")
    sesion.rollback()

    assert error.value.orig.diag.constraint_name == "ex_reservas_aprobadas_sin_solape"
    assert [r.id for r in repositories.listar_todas()] == [primera]


@pytest.mark.parametrize(
    "estados,mismo_espacio,segundo_rango",
    [
        (("aprobada", "aprobada"), True, (12, 14)),
        (("aprobada", "aprobada"), False, (10, 12)),
        (("pendiente", "pendiente"), True, (11, 13)),
        (("aprobada", "pendiente"), True, (11, 13)),
    ],
    ids=["aprobadas_comparten_extremo", "aprobadas_en_espacios_distintos",
         "pendientes_solapadas", "aprobada_y_pendiente_solapadas"],
)
def test_inserciones_aceptadas(sesion, espacio, otro_espacio, ana, estados, mismo_espacio,
                               segundo_rango):
    repositories.crear(espacio, ana, _h(10), _h(12), estado=estados[0])
    repositories.crear(espacio if mismo_espacio else otro_espacio, ana,
                       _h(segundo_rango[0]), _h(segundo_rango[1]), estado=estados[1])
    sesion.commit()

    assert len(repositories.listar_todas()) == 2
