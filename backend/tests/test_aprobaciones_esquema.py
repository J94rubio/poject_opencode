"""Persistencia del motivo de rechazo (tarea 1.1 de `aprobacion-reservas`).

Requisito «Rechazo de solicitudes pendientes con motivo» de la spec
`aprobaciones`. Todo se verifica contra `reservas_test`.
"""

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError

from backend.app.models import Reserva
from backend.app.reservas import repositories

CHECK = "ck_reservas_motivo_rechazo"
INICIO = datetime(2030, 1, 10, 10, tzinfo=timezone.utc)
FIN = datetime(2030, 1, 10, 12, tzinfo=timezone.utc)


@contextmanager
def _conectar(url):
    motor = create_engine(url)
    try:
        with motor.connect() as conexion:
            yield conexion
    finally:
        motor.dispose()


def _checks(conexion):
    return {c["name"] for c in inspect(conexion).get_check_constraints("reservas")}


def _columnas(conexion):
    return {c["name"]: c for c in inspect(conexion).get_columns("reservas")}


@pytest.fixture
def ids(sesion, crear_cuenta, nuevo_espacio):
    return nuevo_espacio(), crear_cuenta("solicitante")


def test_una_reserva_rechazada_sin_motivo_es_rechazada_por_la_base(sesion, ids):
    with pytest.raises(IntegrityError) as error:
        repositories.crear(*ids, INICIO, FIN, estado="rechazada")
    assert CHECK in str(error.value.orig)
    sesion.rollback()
    assert sesion.execute(select(Reserva)).scalars().all() == []


def test_una_reserva_rechazada_con_motivo_se_acepta(sesion, ids):
    reserva = repositories.crear(*ids, INICIO, FIN, estado="rechazada",
                                 motivo_rechazo="Sala en mantenimiento")
    sesion.commit()
    assert reserva.motivo_rechazo == "Sala en mantenimiento"


@pytest.mark.parametrize("estado", ["pendiente", "aprobada", "cancelada"])
def test_los_demas_estados_sin_motivo_se_aceptan(sesion, ids, estado):
    reserva = repositories.crear(*ids, INICIO, FIN, estado=estado)
    sesion.commit()
    assert (reserva.estado, reserva.motivo_rechazo) == (estado, None)


def test_el_esquema_declara_la_columna_y_el_check(esquema, test_database_url):
    with _conectar(test_database_url) as conexion:
        columna = _columnas(conexion)["motivo_rechazo"]
        definicion = conexion.execute(
            text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :nombre"),
            {"nombre": CHECK},
        ).scalar_one()
    assert columna["nullable"] is True
    assert str(columna["type"]) == "TEXT"
    assert "motivo_rechazo IS NOT NULL" in definicion
    assert "<> 'rechazada'" in definicion


def test_downgrade_de_0007_quita_check_y_columna_y_upgrade_los_restaura(
    esquema, migrar, test_database_url
):
    try:
        migrar("downgrade", "0006_reservas_exclusion")
        with _conectar(test_database_url) as conexion:
            assert "motivo_rechazo" not in _columnas(conexion)
            assert CHECK not in _checks(conexion)
    finally:
        # Las demás pruebas, y el estado final de reservas_test, necesitan head.
        migrar("upgrade", "head")

    with _conectar(test_database_url) as conexion:
        assert "motivo_rechazo" in _columnas(conexion)
        assert CHECK in _checks(conexion)
        version = conexion.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version == "0009_historial_inmutable"
