"""Registro del historial en los flujos existentes (sección 3 de `cancelacion-historial`).

Requisito «Registro de cada cambio de estado» de la spec `historial`: creación,
aprobación, rechazo, operaciones fallidas y atomicidad (también de la cancelación).
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.app.aprobaciones.services import APROBAR, RECHAZAR, decidir
from backend.app.auth.errors import (
    DatosInvalidos,
    EspacioInactivo,
    EspacioNoEncontrado,
    PermisoInsuficiente,
    ReservaSolapada,
    SolicitudNoEncontrada,
    SolicitudVencida,
    TransicionInvalida,
)
from backend.app.cancelaciones.services import cancelar
from backend.app.historial import repositories as repositorio_historial
from backend.app.models import EntradaHistorial, Reserva
from backend.app.reservas.services import crear_solicitud
from backend.app.usuarios import repositories as repositorio_usuarios

AHORA = datetime(2030, 1, 10, 8, tzinfo=timezone.utc)
MOTIVO = "Sala en mantenimiento"


def reloj():
    return AHORA


def _h(hora):
    return datetime(2030, 1, 10, hora, tzinfo=timezone.utc)


def _z(hora):
    return f"2030-01-10T{hora:02d}:00:00Z"


def _entradas(sesion):
    """Entradas confirmadas, leídas directamente de la base."""
    sesion.rollback()
    return [
        (e.reserva_id, e.espacio_id, e.estado_anterior, e.estado_nuevo, e.actor_id, e.fecha_utc)
        for e in sesion.execute(select(EntradaHistorial).order_by(EntradaHistorial.id)).scalars()
    ]


def _estado(sesion, reserva_id):
    sesion.rollback()
    return sesion.execute(select(Reserva.estado).where(Reserva.id == reserva_id)).scalar_one()


@pytest.fixture
def cuentas(crear_cuenta):
    ids = {rol: crear_cuenta(rol) for rol in ("solicitante", "aprobador", "admin")}
    return {rol: repositorio_usuarios.obtener_usuario_por_id(i) for rol, i in ids.items()}


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio()


@pytest.fixture
def pendiente(sembrar_reserva, espacio, cuentas):
    def _crear(inicio=_h(10), fin=_h(12)):
        return sembrar_reserva(espacio, cuentas["solicitante"].id, inicio, fin, "pendiente")

    return _crear


def _datos(espacio, inicio=10, fin=12):
    return {"espacio_id": espacio, "inicio": _z(inicio), "fin": _z(fin)}


# --- 3.1 Creación ------------------------------------------------------------


@pytest.mark.parametrize("rol", ["solicitante", "aprobador", "admin"])
def test_cada_creacion_correcta_anade_exactamente_una_entrada(sesion, cuentas, espacio, rol):
    reserva = crear_solicitud(_datos(espacio), cuentas[rol], reloj=reloj)

    assert _entradas(sesion) == [
        (reserva.id, espacio, None, "pendiente", cuentas[rol].id, AHORA)
    ]


def test_una_creacion_invalida_no_anade_ninguna_entrada(sesion, cuentas, espacio):
    with pytest.raises(DatosInvalidos):
        crear_solicitud({"espacio_id": espacio}, cuentas["solicitante"], reloj=reloj)
    with pytest.raises(DatosInvalidos):
        crear_solicitud(_datos(espacio, 12, 10), cuentas["solicitante"], reloj=reloj)
    assert _entradas(sesion) == []


def test_una_creacion_sobre_espacio_inexistente_no_anade_ninguna_entrada(sesion, cuentas):
    with pytest.raises(EspacioNoEncontrado):
        crear_solicitud(_datos(999_999), cuentas["solicitante"], reloj=reloj)
    assert _entradas(sesion) == []


def test_una_creacion_sobre_espacio_inactivo_no_anade_ninguna_entrada(sesion, cuentas,
                                                                      nuevo_espacio):
    with pytest.raises(EspacioInactivo):
        crear_solicitud(_datos(nuevo_espacio(estado="inactivo")), cuentas["solicitante"],
                        reloj=reloj)
    assert _entradas(sesion) == []


def test_una_creacion_solapada_no_anade_ninguna_entrada(sesion, cuentas, espacio, sembrar_reserva):
    sembrar_reserva(espacio, cuentas["aprobador"].id, _h(10), _h(12), "aprobada")
    with pytest.raises(ReservaSolapada):
        crear_solicitud(_datos(espacio, 11, 13), cuentas["solicitante"], reloj=reloj)
    assert _entradas(sesion) == []


# --- 3.2 Decisiones ----------------------------------------------------------


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_la_aprobacion_anade_una_entrada_con_el_aprobador_como_actor(sesion, cuentas, espacio,
                                                                     pendiente, rol):
    reserva_id = pendiente()
    decidir(reserva_id, cuentas[rol], APROBAR, reloj=reloj)

    assert _entradas(sesion) == [
        (reserva_id, espacio, "pendiente", "aprobada", cuentas[rol].id, AHORA)
    ]


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_el_rechazo_anade_una_entrada_con_el_aprobador_como_actor(sesion, cuentas, espacio,
                                                                  pendiente, rol):
    reserva_id = pendiente()
    decidir(reserva_id, cuentas[rol], RECHAZAR, MOTIVO, reloj=reloj)

    assert _entradas(sesion) == [
        (reserva_id, espacio, "pendiente", "rechazada", cuentas[rol].id, AHORA)
    ]


@pytest.mark.parametrize("accion", [APROBAR, RECHAZAR])
def test_decision_inexistente_no_anade_entrada(sesion, cuentas, accion):
    with pytest.raises(SolicitudNoEncontrada):
        decidir(999_999, cuentas["aprobador"], accion, MOTIVO, reloj=reloj)
    assert _entradas(sesion) == []


@pytest.mark.parametrize("accion", [APROBAR, RECHAZAR])
def test_decision_propia_no_anade_entrada(sesion, cuentas, sembrar_reserva, espacio, accion):
    reserva_id = sembrar_reserva(espacio, cuentas["aprobador"].id, _h(10), _h(12), "pendiente")
    with pytest.raises(PermisoInsuficiente):
        decidir(reserva_id, cuentas["aprobador"], accion, MOTIVO, reloj=reloj)
    assert _entradas(sesion) == []


@pytest.mark.parametrize("accion", [APROBAR, RECHAZAR])
def test_decision_sobre_no_pendiente_no_anade_entrada(sesion, cuentas, sembrar_reserva, espacio,
                                                      accion):
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"].id, _h(10), _h(12), "cancelada")
    with pytest.raises(TransicionInvalida):
        decidir(reserva_id, cuentas["aprobador"], accion, MOTIVO, reloj=reloj)
    assert _entradas(sesion) == []


def test_aprobacion_con_solapamiento_no_anade_entrada(sesion, cuentas, sembrar_reserva, espacio,
                                                      pendiente):
    sembrar_reserva(espacio, cuentas["admin"].id, _h(10), _h(12), "aprobada")
    with pytest.raises(ReservaSolapada):
        decidir(pendiente(_h(11), _h(13)), cuentas["aprobador"], APROBAR, reloj=reloj)
    assert _entradas(sesion) == []


def test_aprobacion_vencida_no_anade_entrada(sesion, cuentas, pendiente):
    with pytest.raises(SolicitudVencida):
        decidir(pendiente(AHORA, AHORA + timedelta(hours=1)), cuentas["aprobador"], APROBAR,
                reloj=reloj)
    assert _entradas(sesion) == []


def test_rechazo_sin_motivo_no_anade_entrada(sesion, cuentas, pendiente):
    with pytest.raises(DatosInvalidos):
        decidir(pendiente(), cuentas["aprobador"], RECHAZAR, None, reloj=reloj)
    assert _entradas(sesion) == []


def test_la_ruta_de_rechazo_usa_el_reloj_inyectado(app, client, sesion, cuentas, pendiente, cabecera):
    """Sin reloj en el servicio de rechazo, la fecha dependería de la fecha real."""
    app.config["RELOJ"] = reloj
    reserva_id = pendiente()

    respuesta = client.post(f"/api/reservas/{reserva_id}/rechazar",
                            headers=cabecera(cuentas["aprobador"].id), json={"motivo": MOTIVO})

    assert respuesta.status_code == 200
    assert _entradas(sesion)[0][5] == AHORA


# --- 3.3 Atomicidad ----------------------------------------------------------


class FalloDeRegistro(RuntimeError):
    pass


@pytest.fixture(params=["antes_de_escribir", "tras_escribir"])
def registrar_que_falla(request, monkeypatch):
    """Doble de `registrar`: falla sin escribir, o después de escribir la entrada."""
    original = repositorio_historial.registrar

    def _doble(*args, **kwargs):
        if request.param == "tras_escribir":
            original(*args, **kwargs)
        raise FalloDeRegistro()

    def _activar():
        monkeypatch.setattr(repositorio_historial, "registrar", _doble)

    return _activar


def test_fallo_al_registrar_durante_la_creacion_no_deja_la_solicitud(sesion, cuentas, espacio,
                                                                     registrar_que_falla):
    registrar_que_falla()

    with pytest.raises(FalloDeRegistro):
        crear_solicitud(_datos(espacio), cuentas["solicitante"], reloj=reloj)

    assert sesion.execute(select(Reserva)).scalars().all() == []
    assert _entradas(sesion) == []


@pytest.mark.parametrize("accion,motivo", [(APROBAR, None), (RECHAZAR, MOTIVO)])
def test_fallo_al_registrar_durante_una_decision_no_cambia_el_estado(sesion, cuentas, pendiente,
                                                                     registrar_que_falla, accion,
                                                                     motivo):
    reserva_id = pendiente()
    registrar_que_falla()

    with pytest.raises(FalloDeRegistro):
        decidir(reserva_id, cuentas["aprobador"], accion, motivo, reloj=reloj)

    assert _estado(sesion, reserva_id) == "pendiente"
    assert _entradas(sesion) == []


def test_fallo_al_registrar_durante_una_cancelacion_no_cambia_el_estado(sesion, cuentas, pendiente,
                                                                        registrar_que_falla):
    reserva_id = pendiente()
    registrar_que_falla()

    with pytest.raises(FalloDeRegistro):
        cancelar(reserva_id, cuentas["solicitante"], reloj=reloj)

    assert _estado(sesion, reserva_id) == "pendiente"
    assert _entradas(sesion) == []


def test_fallo_al_registrar_responde_error_interno_por_la_api(app, client, sesion, cuentas,
                                                              pendiente, cabecera,
                                                              registrar_que_falla):
    app.config["RELOJ"] = reloj
    reserva_id = pendiente()
    registrar_que_falla()

    respuesta = client.post(f"/api/reservas/{reserva_id}/aprobar",
                            headers=cabecera(cuentas["aprobador"].id))

    assert respuesta.status_code == 500
    assert respuesta.get_json()["error"]["codigo"] == "error_interno"
    assert _estado(sesion, reserva_id) == "pendiente"
    assert _entradas(sesion) == []
