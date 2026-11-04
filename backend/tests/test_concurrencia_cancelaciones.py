"""Cancelaciones simultáneas (tarea 6.1 de `cancelacion-historial`).

Requisito «Cancelaciones simultáneas» de la spec `cancelaciones`. Se ejecutan contra
PostgreSQL real (`reservas_test`), con los datos confirmados, fechas de 2030 y reloj
inyectado. Las aserciones son sobre el resultado final y la coherencia del historial,
nunca sobre el orden de llegada: quién gana la carrera no está determinado.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.app.aprobaciones import services as servicio_aprobaciones
from backend.app.cancelaciones.services import cancelar
from backend.app.models import EntradaHistorial, Reserva
from backend.app.usuarios import repositories as repositorio_usuarios
from soporte_concurrencia import ejecutar_en_paralelo

REPETICIONES = 20
AHORA = datetime(2030, 1, 1, 8, tzinfo=timezone.utc)


def _dia(repeticion, hora):
    return datetime(2030, 2, 1, hora, tzinfo=timezone.utc) + timedelta(days=repeticion)


@pytest.fixture
def escenario(app, sesion, crear_cuenta, nuevo_espacio, cabecera):
    app.config["RELOJ"] = lambda: AHORA
    solicitante, aprobador = crear_cuenta("solicitante"), crear_cuenta("aprobador")
    return {
        "espacio": nuevo_espacio(),
        "solicitante": solicitante,
        "aprobador": aprobador,
        "cabecera_solicitante": cabecera(solicitante),
        "cabecera_aprobador": cabecera(aprobador),
    }


@pytest.fixture
def acciones(app, sesion):
    """Lanza peticiones HTTP simultáneas, cada una con su propio cliente."""

    def _accion(cabeceras, reserva_id, accion):
        def _llamar():
            respuesta = app.test_client().post(
                f"/api/reservas/{reserva_id}/{accion}", headers=cabeceras
            )
            cuerpo = respuesta.get_json()
            return (respuesta.status_code, cuerpo.get("error", {}).get("codigo"),
                    cuerpo.get("estado"))

        return _llamar

    def _lanzar(*pares):
        sesion.commit()  # Ninguna transacción abierta durante la carrera.
        return ejecutar_en_paralelo(
            app, [_accion(cabeceras, reserva, accion) for cabeceras, reserva, accion in pares]
        )

    return _lanzar


def _estado(sesion, reserva_id):
    sesion.rollback()
    return sesion.execute(select(Reserva.estado).where(Reserva.id == reserva_id)).scalar_one()


def _entradas(sesion, reserva_id):
    sesion.rollback()
    return [
        (e.estado_anterior, e.estado_nuevo, e.actor_id)
        for e in sesion.execute(
            select(EntradaHistorial)
            .where(EntradaHistorial.reserva_id == reserva_id)
            .order_by(EntradaHistorial.fecha_utc, EntradaHistorial.id)
        ).scalars()
    ]


@pytest.mark.parametrize("estado", ["pendiente", "aprobada"])
def test_dos_cancelaciones_simultaneas_de_la_misma_solicitud(sesion, escenario, sembrar_reserva,
                                                             acciones, estado):
    duenio = escenario["solicitante"]
    cabeceras = escenario["cabecera_solicitante"]
    for repeticion in range(REPETICIONES):
        reserva = sembrar_reserva(escenario["espacio"], duenio, _dia(repeticion, 10),
                                  _dia(repeticion, 12), estado)

        resultados = acciones((cabeceras, reserva, "cancelar"), (cabeceras, reserva, "cancelar"))

        contexto = f"repetición {repeticion}"
        assert sorted(resultados, key=lambda r: r[0]) == [
            (200, None, "cancelada"), (409, "transicion_invalida", None)
        ], contexto
        assert _estado(sesion, reserva) == "cancelada", contexto
        assert _entradas(sesion, reserva) == [(estado, "cancelada", duenio)], contexto


def test_cancelacion_y_aprobacion_simultaneas_de_la_misma_solicitud(sesion, escenario,
                                                                    sembrar_reserva, acciones):
    duenio, aprobador = escenario["solicitante"], escenario["aprobador"]
    for repeticion in range(REPETICIONES):
        reserva = sembrar_reserva(escenario["espacio"], duenio, _dia(repeticion, 10),
                                  _dia(repeticion, 12), "pendiente")

        cancelacion, aprobacion = acciones(
            (escenario["cabecera_solicitante"], reserva, "cancelar"),
            (escenario["cabecera_aprobador"], reserva, "aprobar"),
        )

        contexto = f"repetición {repeticion}"
        assert cancelacion == (200, None, "cancelada"), contexto
        assert _estado(sesion, reserva) == "cancelada", contexto
        if aprobacion[0] == 200:
            # La respuesta se serializa tras confirmar la decisión: si la cancelación se
            # confirma en ese intervalo, muestra el estado ya vigente (prueba siguiente).
            assert aprobacion[1] is None and aprobacion[2] in ("aprobada", "cancelada"), contexto
            esperadas = [("pendiente", "aprobada", aprobador),
                         ("aprobada", "cancelada", duenio)]
        else:
            assert aprobacion == (409, "transicion_invalida", None), contexto
            esperadas = [("pendiente", "cancelada", duenio)]
        assert _entradas(sesion, reserva) == esperadas, contexto


def test_la_respuesta_de_aprobar_muestra_una_cancelacion_confirmada_justo_despues(
    app, client, sesion, escenario, sembrar_reserva, monkeypatch
):
    """Reproduce sin carrera el intervalo entre confirmar la decisión y serializarla."""
    duenio, aprobador = escenario["solicitante"], escenario["aprobador"]
    reserva = sembrar_reserva(escenario["espacio"], duenio, _dia(0, 10), _dia(0, 12), "pendiente")
    decidir = servicio_aprobaciones.decidir

    def _decidir_y_cancelar(*args, **kwargs):
        resultado = decidir(*args, **kwargs)
        cancelar(reserva, repositorio_usuarios.obtener_usuario_por_id(duenio), reloj=lambda: AHORA)
        return resultado

    monkeypatch.setattr(servicio_aprobaciones, "decidir", _decidir_y_cancelar)

    respuesta = client.post(f"/api/reservas/{reserva}/aprobar",
                            headers=escenario["cabecera_aprobador"])

    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "cancelada"
    assert _entradas(sesion, reserva) == [("pendiente", "aprobada", aprobador),
                                          ("aprobada", "cancelada", duenio)]
