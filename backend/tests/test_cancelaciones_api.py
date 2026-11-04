"""API de cancelación (tarea 5.1 de `cancelacion-historial`).

Requisitos «Cancelación de reservas propias», «Condiciones de la cancelación» y
«Cancelación restringida al dueño» de la spec `cancelaciones`. El reloj se inyecta
con `app.config["RELOJ"]`.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.app.auth import errors
from backend.app.models import EntradaHistorial, Reserva

AHORA = datetime(2030, 1, 10, 8, tzinfo=timezone.utc)
INICIO = datetime(2030, 1, 10, 10, tzinfo=timezone.utc)
FIN = datetime(2030, 1, 10, 12, tzinfo=timezone.utc)
ROLES = ["solicitante", "aprobador", "admin"]


@pytest.fixture(autouse=True)
def reloj_fijo(app):
    app.config["RELOJ"] = lambda: AHORA


@pytest.fixture
def cuentas(crear_cuenta):
    return {rol: crear_cuenta(rol) for rol in ROLES}


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio()


def _cancelar(client, cabeceras, reserva_id, **kwargs):
    return client.post(f"/api/reservas/{reserva_id}/cancelar", headers=cabeceras, **kwargs)


def _estado(sesion, reserva_id):
    sesion.rollback()
    return sesion.execute(select(Reserva.estado).where(Reserva.id == reserva_id)).scalar_one()


def _num_entradas(sesion):
    sesion.rollback()
    return len(sesion.execute(select(EntradaHistorial)).scalars().all())


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


@pytest.mark.parametrize("rol", ROLES)
@pytest.mark.parametrize("estado", ["pendiente", "aprobada"])
def test_cancelacion_propia_responde_con_el_detalle_de_la_solicitud(client, sesion, cuentas, espacio,
                                                                    sembrar_reserva, cabecera, rol,
                                                                    estado):
    reserva_id = sembrar_reserva(espacio, cuentas[rol], INICIO, FIN, estado)

    respuesta = _cancelar(client, cabecera(cuentas[rol]), reserva_id)

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": reserva_id,
        "espacio_id": espacio,
        "solicitante_id": cuentas[rol],
        "inicio": "2030-01-10T10:00:00Z",
        "fin": "2030-01-10T12:00:00Z",
        "estado": "cancelada",
    }
    assert _estado(sesion, reserva_id) == "cancelada"
    assert _num_entradas(sesion) == 1


@pytest.mark.parametrize(
    "kwargs",
    [{"json": {"motivo": "x"}}, {"json": [1]}, {"data": "{no json",
                                               "content_type": "application/json"}],
    ids=["objeto", "lista", "mal_formado"],
)
def test_el_cuerpo_se_ignora(client, sesion, cuentas, espacio, sembrar_reserva, cabecera, kwargs):
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"], INICIO, FIN, "pendiente")

    respuesta = _cancelar(client, cabecera(cuentas["solicitante"]), reserva_id, **kwargs)

    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "cancelada"


def test_cancelacion_sin_token(client, sesion, cuentas, espacio, sembrar_reserva):
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"], INICIO, FIN, "pendiente")

    respuesta = client.post(f"/api/reservas/{reserva_id}/cancelar")

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"
    assert _estado(sesion, reserva_id) == "pendiente"
    assert _num_entradas(sesion) == 0


@pytest.mark.parametrize("rol", ROLES)
def test_cancelacion_ajena_para_cada_rol(client, sesion, crear_cuenta, cuentas, espacio,
                                         sembrar_reserva, cabecera, rol):
    duenio = crear_cuenta("solicitante", correo="duenio@example.com")
    reserva_id = sembrar_reserva(espacio, duenio, INICIO, FIN, "aprobada")

    respuesta = _cancelar(client, cabecera(cuentas[rol]), reserva_id)

    assert respuesta.status_code == 403
    assert respuesta.get_json() == {
        "error": {"codigo": "permiso_insuficiente",
                  "mensaje": errors.PermisoInsuficiente.mensaje}
    }
    assert _estado(sesion, reserva_id) == "aprobada"
    assert _num_entradas(sesion) == 0


def test_cancelacion_de_una_solicitud_inexistente(client, cuentas, cabecera):
    respuesta = _cancelar(client, cabecera(cuentas["solicitante"]), 999_999)

    assert respuesta.status_code == 404
    assert respuesta.get_json() == {
        "error": {"codigo": "solicitud_no_encontrada",
                  "mensaje": errors.SolicitudNoEncontrada.mensaje}
    }


def test_identificador_fuera_del_rango_de_postgresql(client, cuentas, cabecera):
    respuesta = _cancelar(client, cabecera(cuentas["solicitante"]), 2_147_483_648)
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "solicitud_no_encontrada"


@pytest.mark.parametrize("estado", ["rechazada", "cancelada"])
def test_transicion_invalida(client, sesion, cuentas, espacio, sembrar_reserva, cabecera, estado):
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"], INICIO, FIN, estado)

    respuesta = _cancelar(client, cabecera(cuentas["solicitante"]), reserva_id)

    assert respuesta.status_code == 409
    assert respuesta.get_json() == {
        "error": {"codigo": "transicion_invalida", "mensaje": errors.TransicionInvalida.mensaje}
    }
    assert _estado(sesion, reserva_id) == estado
    assert _num_entradas(sesion) == 0


@pytest.mark.parametrize(
    "inicio", [AHORA, AHORA - timedelta(minutes=1)], ids=["en_el_instante", "ya_comenzo"]
)
def test_reserva_iniciada(client, sesion, cuentas, espacio, sembrar_reserva, cabecera, inicio):
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"], inicio, FIN, "aprobada")

    respuesta = _cancelar(client, cabecera(cuentas["solicitante"]), reserva_id)

    assert respuesta.status_code == 409
    assert respuesta.get_json() == {
        "error": {"codigo": "reserva_iniciada", "mensaje": errors.ReservaIniciada.mensaje}
    }
    assert _estado(sesion, reserva_id) == "aprobada"
    assert _num_entradas(sesion) == 0


def test_cancelacion_usa_el_reloj_inyectado(app, client, sesion, cuentas, espacio, sembrar_reserva,
                                            cabecera):
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"], INICIO, FIN, "pendiente")
    app.config["RELOJ"] = lambda: INICIO

    respuesta = _cancelar(client, cabecera(cuentas["solicitante"]), reserva_id)

    assert _codigo(respuesta) == "reserva_iniciada"


def test_el_ciclo_completo_queda_en_el_historial_por_la_api(client, sesion, cuentas, espacio, cabecera):
    creada = client.post(
        "/api/reservas",
        headers=cabecera(cuentas["solicitante"]),
        json={"espacio_id": espacio, "inicio": "2030-01-10T10:00:00Z",
              "fin": "2030-01-10T12:00:00Z"},
    ).get_json()
    client.post(f"/api/reservas/{creada['id']}/aprobar", headers=cabecera(cuentas["aprobador"]))
    _cancelar(client, cabecera(cuentas["solicitante"]), creada["id"])

    entradas = client.get("/api/historial", headers=cabecera(cuentas["solicitante"])).get_json()

    assert [(e["estado_anterior"], e["estado_nuevo"], e["actor_id"]) for e in entradas] == [
        (None, "pendiente", cuentas["solicitante"]),
        ("pendiente", "aprobada", cuentas["aprobador"]),
        ("aprobada", "cancelada", cuentas["solicitante"]),
    ]
