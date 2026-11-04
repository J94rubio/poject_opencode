"""Decisiones simultáneas (sección 5 de `aprobacion-reservas`).

Requisito «Decisiones simultáneas» de la spec `aprobaciones`. Se ejecutan contra
PostgreSQL real (`reservas_test`), con los datos confirmados, fechas de 2030 y
reloj inyectado. Las aserciones son sobre el resultado final, nunca sobre el
orden de llegada: quién gana la carrera no está determinado.
"""

from datetime import datetime, timedelta, timezone
from threading import Event

import pytest
from sqlalchemy import select, text

from backend.app.extensions import db
from backend.app.models import Reserva
from soporte_concurrencia import ejecutar_en_paralelo

REPETICIONES = 20
AHORA = datetime(2030, 1, 1, 8, 0, tzinfo=timezone.utc)
MOTIVO = {"motivo": "Sala en mantenimiento"}


def _dia(repeticion, hora):
    return datetime(2030, 2, 1, hora, tzinfo=timezone.utc) + timedelta(days=repeticion)


@pytest.fixture
def escenario(app, sesion, crear_cuenta, nuevo_espacio, cabecera):
    app.config["RELOJ"] = lambda: AHORA
    return {
        "espacio": nuevo_espacio(),
        "solicitante": crear_cuenta("solicitante"),
        "aprobador": cabecera(crear_cuenta("aprobador")),
        "admin": cabecera(crear_cuenta("admin")),
    }


@pytest.fixture
def decisiones(app, sesion, escenario):
    """Lanza decisiones HTTP simultáneas, cada una con su propio cliente."""

    def _decision(cabeceras, reserva_id, accion):
        cuerpo = {"json": MOTIVO} if accion == "rechazar" else {}

        def _llamar():
            respuesta = app.test_client().post(
                f"/api/reservas/{reserva_id}/{accion}", headers=cabeceras, **cuerpo
            )
            cuerpo_respuesta = respuesta.get_json()
            return (respuesta.status_code,
                    cuerpo_respuesta.get("error", {}).get("codigo"),
                    cuerpo_respuesta.get("estado"))

        return _llamar

    def _lanzar(*pares):
        sesion.commit()  # Ninguna transacción abierta durante la carrera.
        return ejecutar_en_paralelo(
            app, [_decision(cabeceras, reserva, accion) for cabeceras, reserva, accion in pares]
        )

    return _lanzar


def _estados(sesion, *reservas):
    sesion.rollback()
    filas = sesion.execute(
        select(Reserva.id, Reserva.estado, Reserva.motivo_rechazo).where(Reserva.id.in_(reservas))
    ).all()
    return {fila.id: (fila.estado, fila.motivo_rechazo) for fila in filas}


# --- 5.1 La utilidad lanza las llamadas realmente en paralelo --------------------


def test_las_llamadas_se_solapan_en_el_tiempo(app):
    """Cada llamada solo termina si la otra está en marcha al mismo tiempo: en
    serie, la primera agotaría la espera y devolvería False."""
    primera, segunda = Event(), Event()

    def _a():
        primera.set()
        return segunda.wait(10)

    def _b():
        segunda.set()
        return primera.wait(10)

    assert ejecutar_en_paralelo(app, [_a, _b]) == [True, True]


def test_cada_llamada_usa_su_propia_sesion_y_su_propia_conexion(app, esquema):
    """Las dos conexiones se mantienen abiertas a la vez hasta que ambas conocen
    su identificador de proceso; distintos, son conexiones distintas."""
    primera, segunda = Event(), Event()

    def _llamada(propio, ajeno):
        def _ejecutar():
            pid = db.session.execute(text("SELECT pg_backend_pid()")).scalar_one()
            sesion = db.session()
            propio.set()
            assert ajeno.wait(10)
            return pid, id(sesion)

        return _ejecutar

    (pid_a, sesion_a), (pid_b, sesion_b) = ejecutar_en_paralelo(
        app, [_llamada(primera, segunda), _llamada(segunda, primera)]
    )

    assert pid_a != pid_b
    assert sesion_a != sesion_b


def test_la_utilidad_propaga_las_excepciones_de_las_llamadas(app):
    def _falla():
        raise LookupError("fallo de la llamada")

    with pytest.raises(LookupError):
        ejecutar_en_paralelo(app, [_falla, lambda: None])


def test_la_utilidad_devuelve_las_conexiones_al_pool(app, esquema):
    def _consultar():
        return db.session.execute(text("SELECT 1")).scalar_one()

    ejecutar_en_paralelo(app, [_consultar, _consultar])

    assert db.engine.pool.checkedout() == 0


# --- 5.2 Decisiones simultáneas ------------------------------------------------------


def test_dos_aprobaciones_simultaneas_de_solicitudes_solapadas(sesion, escenario, sembrar_reserva,
                                                               decisiones):
    for repeticion in range(REPETICIONES):
        a = sembrar_reserva(escenario["espacio"], escenario["solicitante"],
                            _dia(repeticion, 10), _dia(repeticion, 12), "pendiente")
        b = sembrar_reserva(escenario["espacio"], escenario["solicitante"],
                            _dia(repeticion, 11), _dia(repeticion, 13), "pendiente")

        resultados = decisiones((escenario["aprobador"], a, "aprobar"),
                                (escenario["admin"], b, "aprobar"))

        assert sorted(resultados, key=lambda r: r[0]) == [
            (200, None, "aprobada"), (409, "reserva_solapada", None)
        ], f"repetición {repeticion}"
        ganadora, perdedora = (a, b) if resultados[0][0] == 200 else (b, a)
        assert _estados(sesion, a, b) == {ganadora: ("aprobada", None),
                                          perdedora: ("pendiente", None)}


def test_dos_aprobaciones_simultaneas_de_la_misma_solicitud(sesion, escenario, sembrar_reserva,
                                                            decisiones):
    for repeticion in range(REPETICIONES):
        reserva = sembrar_reserva(escenario["espacio"], escenario["solicitante"],
                                  _dia(repeticion, 10), _dia(repeticion, 12), "pendiente")

        resultados = decisiones((escenario["aprobador"], reserva, "aprobar"),
                                (escenario["admin"], reserva, "aprobar"))

        assert sorted(resultados, key=lambda r: r[0]) == [
            (200, None, "aprobada"), (409, "transicion_invalida", None)
        ], f"repetición {repeticion}"
        assert _estados(sesion, reserva) == {reserva: ("aprobada", None)}


def test_aprobacion_y_rechazo_simultaneos_de_la_misma_solicitud(sesion, escenario, sembrar_reserva,
                                                                decisiones):
    for repeticion in range(REPETICIONES):
        reserva = sembrar_reserva(escenario["espacio"], escenario["solicitante"],
                                  _dia(repeticion, 10), _dia(repeticion, 12), "pendiente")

        aprobacion, rechazo = decisiones((escenario["aprobador"], reserva, "aprobar"),
                                         (escenario["admin"], reserva, "rechazar"))

        contexto = f"repetición {repeticion}"
        if aprobacion[0] == 200:
            assert aprobacion == (200, None, "aprobada"), contexto
            assert rechazo == (409, "transicion_invalida", None), contexto
            esperado = ("aprobada", None)
        else:
            assert aprobacion == (409, "transicion_invalida", None), contexto
            assert rechazo == (200, None, "rechazada"), contexto
            esperado = ("rechazada", MOTIVO["motivo"])
        assert _estados(sesion, reserva) == {reserva: esperado}, contexto
