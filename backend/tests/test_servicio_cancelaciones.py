"""Servicio de cancelación (tareas 4.2 y 4.3 de `cancelacion-historial`).

Requisitos de la spec `cancelaciones` y registro de la cancelación de la spec
`historial`. Se usan fechas de 2030 y un reloj inyectado.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError

from backend.app.aprobaciones.services import APROBAR, decidir
from backend.app.auth.errors import (
    PermisoInsuficiente,
    ReservaIniciada,
    SolicitudNoEncontrada,
    TransicionInvalida,
)
from backend.app.cancelaciones.services import cancelar
from backend.app.extensions import db
from backend.app.models import EntradaHistorial, Reserva
from backend.app.reservas.services import consultar_disponibilidad
from backend.app.usuarios import repositories as repositorio_usuarios

AHORA = datetime(2030, 1, 10, 8, tzinfo=timezone.utc)
ROLES = ["solicitante", "aprobador", "admin"]


def reloj():
    return AHORA


def _h(hora):
    return datetime(2030, 1, 10, hora, tzinfo=timezone.utc)


def _z(hora):
    return f"2030-01-10T{hora:02d}:00:00Z"


def _estado(sesion, reserva_id):
    sesion.rollback()
    return sesion.execute(select(Reserva.estado).where(Reserva.id == reserva_id)).scalar_one()


def _entradas(sesion):
    sesion.rollback()
    return [
        (e.reserva_id, e.espacio_id, e.estado_anterior, e.estado_nuevo, e.actor_id, e.fecha_utc)
        for e in sesion.execute(select(EntradaHistorial).order_by(EntradaHistorial.id)).scalars()
    ]


@pytest.fixture
def cuentas(crear_cuenta):
    cuentas = {rol: crear_cuenta(rol) for rol in ROLES}
    cuentas["otro"] = crear_cuenta("solicitante", correo="otro@example.com")
    return {rol: repositorio_usuarios.obtener_usuario_por_id(i) for rol, i in cuentas.items()}


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio()


@pytest.fixture
def reserva(sembrar_reserva, espacio, cuentas):
    def _crear(estado="pendiente", rol="solicitante", inicio=_h(10), fin=_h(12)):
        return sembrar_reserva(espacio, cuentas[rol].id, inicio, fin, estado)

    return _crear


# --- 4.2 Cancelaciones correctas ---------------------------------------------


@pytest.mark.parametrize("rol", ROLES)
@pytest.mark.parametrize("estado", ["pendiente", "aprobada"])
def test_cancelacion_de_una_reserva_propia(sesion, cuentas, espacio, reserva, rol, estado):
    """Cubre al solicitante y al aprobador y al admin sobre sus propias solicitudes."""
    reserva_id = reserva(estado, rol)

    resultado = cancelar(reserva_id, cuentas[rol], reloj=reloj)

    assert resultado.id == reserva_id
    assert resultado.estado == "cancelada"
    assert _estado(sesion, reserva_id) == "cancelada"
    assert _entradas(sesion) == [
        (reserva_id, espacio, estado, "cancelada", cuentas[rol].id, AHORA)
    ]


def test_cancelacion_cuando_el_inicio_es_justo_despues_del_instante_actual(sesion, cuentas, reserva):
    reserva_id = reserva(inicio=AHORA + timedelta(microseconds=1))
    assert cancelar(reserva_id, cuentas["solicitante"], reloj=reloj).estado == "cancelada"


# --- 4.2 Cancelaciones rechazadas --------------------------------------------


@pytest.mark.parametrize("rol", ROLES)
@pytest.mark.parametrize("estado", ["pendiente", "aprobada"])
def test_cancelacion_de_una_reserva_ajena(sesion, cuentas, reserva, rol, estado):
    """Ajena para cualquier rol, incluido admin."""
    duenio = "otro"
    reserva_id = reserva(estado, duenio)

    with pytest.raises(PermisoInsuficiente):
        cancelar(reserva_id, cuentas[rol], reloj=reloj)

    assert _estado(sesion, reserva_id) == estado
    assert _entradas(sesion) == []


@pytest.mark.parametrize("reserva_id", [999_999, 0, -1, 2_147_483_648])
def test_cancelacion_de_una_solicitud_inexistente(sesion, cuentas, reserva_id):
    with pytest.raises(SolicitudNoEncontrada):
        cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)
    assert _entradas(sesion) == []


@pytest.mark.parametrize("estado", ["rechazada", "cancelada"])
def test_cancelacion_de_una_solicitud_rechazada_o_cancelada(sesion, cuentas, reserva, estado):
    reserva_id = reserva(estado)

    with pytest.raises(TransicionInvalida):
        cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)

    assert _estado(sesion, reserva_id) == estado
    assert _entradas(sesion) == []


@pytest.mark.parametrize("estado", ["pendiente", "aprobada"])
def test_cancelacion_de_una_reserva_que_ya_comenzo(sesion, cuentas, reserva, estado):
    reserva_id = reserva(estado, inicio=AHORA - timedelta(hours=1), fin=AHORA + timedelta(hours=1))

    with pytest.raises(ReservaIniciada):
        cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)

    assert _estado(sesion, reserva_id) == estado
    assert _entradas(sesion) == []


@pytest.mark.parametrize("estado", ["pendiente", "aprobada"])
def test_cancelacion_en_el_instante_de_inicio(sesion, cuentas, reserva, estado):
    reserva_id = reserva(estado, inicio=AHORA)

    with pytest.raises(ReservaIniciada):
        cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)

    assert _estado(sesion, reserva_id) == estado
    assert _entradas(sesion) == []


# --- 4.2 Orden de comprobaciones ---------------------------------------------


def test_orden_dueno_antes_que_estado(sesion, cuentas, reserva):
    with pytest.raises(PermisoInsuficiente):
        cancelar(reserva("cancelada", "otro"), cuentas["solicitante"], reloj=reloj)


def test_orden_dueno_antes_que_inicio(sesion, cuentas, reserva):
    with pytest.raises(PermisoInsuficiente):
        cancelar(reserva("pendiente", "otro", inicio=AHORA), cuentas["solicitante"], reloj=reloj)


def test_orden_estado_antes_que_inicio(sesion, cuentas, reserva):
    with pytest.raises(TransicionInvalida):
        cancelar(reserva("rechazada", inicio=AHORA), cuentas["solicitante"], reloj=reloj)


# --- 4.2 Técnica de bloqueo ---------------------------------------------------


def test_un_error_de_dominio_libera_el_bloqueo_de_la_fila(app, sesion, cuentas, reserva):
    reserva_id = reserva("cancelada")
    with pytest.raises(TransicionInvalida):
        cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)

    with db.engine.connect() as otra:
        otra.execute(text("SET LOCAL lock_timeout = '100ms'"))
        fila = otra.execute(
            text("SELECT id FROM reservas WHERE id = :id FOR UPDATE"), {"id": reserva_id}
        ).scalar_one()
        otra.rollback()
    assert fila == reserva_id


def test_la_fila_de_la_solicitud_queda_bloqueada_y_la_del_espacio_no(app, sesion, cuentas, espacio,
                                                                     reserva, monkeypatch):
    """Durante el registro: la solicitud está bloqueada y el espacio se puede bloquear."""
    from backend.app.historial import repositories as repositorio_historial

    reserva_id = reserva()
    original = repositorio_historial.registrar
    observado = {}

    def _espiar(*args, **kwargs):
        with db.engine.connect() as otra:
            otra.execute(text("SET LOCAL lock_timeout = '100ms'"))
            observado["espacio"] = otra.execute(
                text("SELECT id FROM espacios WHERE id = :id FOR UPDATE"), {"id": espacio}
            ).scalar_one()
            otra.rollback()
            otra.execute(text("SET LOCAL lock_timeout = '100ms'"))
            with pytest.raises(OperationalError):
                otra.execute(
                    text("SELECT id FROM reservas WHERE id = :id FOR UPDATE"), {"id": reserva_id}
                )
            otra.rollback()
        return original(*args, **kwargs)

    monkeypatch.setattr(repositorio_historial, "registrar", _espiar)
    cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)

    assert observado["espacio"] == espacio


# --- 4.3 Liberación del espacio ---------------------------------------------


def test_cancelar_una_aprobada_libera_la_disponibilidad(sesion, cuentas, espacio, reserva):
    reserva_id = reserva("aprobada")
    assert [r.id for r in consultar_disponibilidad(espacio, _z(8), _z(18))] == [reserva_id]

    cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)

    assert consultar_disponibilidad(espacio, _z(8), _z(18)) == []


def test_se_puede_aprobar_una_pendiente_que_estaba_en_conflicto(sesion, cuentas, reserva):
    aprobada = reserva("aprobada")
    en_conflicto = reserva("pendiente", "otro", _h(11), _h(13))

    cancelar(aprobada, cuentas["solicitante"], reloj=reloj)
    resultado = decidir(en_conflicto, cuentas["aprobador"], APROBAR, reloj=reloj)

    assert resultado.estado == "aprobada"


def test_una_reserva_cancelada_no_se_puede_aprobar(sesion, cuentas, reserva):
    reserva_id = reserva()
    cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)

    with pytest.raises(TransicionInvalida):
        decidir(reserva_id, cuentas["aprobador"], APROBAR, reloj=reloj)

    assert _estado(sesion, reserva_id) == "cancelada"
    assert [e[3] for e in _entradas(sesion)] == ["cancelada"]
