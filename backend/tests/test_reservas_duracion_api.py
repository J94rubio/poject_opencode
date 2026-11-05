"""API de la duración máxima (tareas 4.1 y 4.2 de `limite-duracion-reserva`).

Requisitos «Creación de solicitudes de reserva» y «Alcance de la duración máxima» de
la spec `reservas`. El reloj se inyecta con `app.config["RELOJ"]`, las fechas son fijas
y las reservas de más de 4 horas se siembran directamente en el repositorio.
"""

from datetime import datetime, timezone
from urllib.parse import urlencode

import pytest

AHORA = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
INICIO_LARGA = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)
FIN_LARGA = datetime(2026, 11, 3, 16, 0, tzinfo=timezone.utc)
INICIO_Z, FIN_Z = "2026-11-03T10:00:00Z", "2026-11-03T16:00:00Z"
ESPACIO_INEXISTENTE = 999999
RESPUESTA_DURACION_EXCEDIDA = {
    "error": {
        "codigo": "duracion_excedida",
        "mensaje": "La duración máxima de una reserva es de 4 horas.",
    }
}


@pytest.fixture(autouse=True)
def reloj_fijo(app):
    app.config["RELOJ"] = lambda: AHORA


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio("Laboratorio A")


@pytest.fixture
def solicitante(crear_cuenta):
    return crear_cuenta("solicitante")


@pytest.fixture
def aprobador(crear_cuenta):
    return crear_cuenta("aprobador")


def _crear(client, cabeceras, espacio_id, inicio, fin):
    return client.post("/api/reservas", headers=cabeceras,
                       json={"espacio_id": espacio_id, "inicio": inicio, "fin": fin})


# --- 4.1 POST /api/reservas ---------------------------------------------------


@pytest.mark.parametrize(
    "fin",
    ["2026-11-03T11:00:00Z", "2026-11-03T14:00:00Z"],
    ids=["una_hora", "cuatro_horas_exactas"],
)
def test_duracion_aceptada(client, sesion, cabecera, solicitante, espacio, fin):
    respuesta = _crear(client, cabecera(solicitante), espacio, INICIO_Z, fin)

    assert respuesta.status_code == 201
    creada = respuesta.get_json()
    assert (creada["inicio"], creada["fin"], creada["estado"]) == (INICIO_Z, fin, "pendiente")


def test_cuatro_horas_y_un_segundo_rechazadas_con_el_cuerpo_exacto(client, sesion, cabecera,
                                                                   solicitante, espacio):
    respuesta = _crear(client, cabecera(solicitante), espacio, INICIO_Z, "2026-11-03T14:00:01Z")

    assert respuesta.status_code == 400
    assert respuesta.get_json() == RESPUESTA_DURACION_EXCEDIDA


def test_duracion_excedida_con_inicio_pasado(client, sesion, cabecera, solicitante, espacio):
    respuesta = _crear(client, cabecera(solicitante), espacio,
                       "2026-11-02T11:00:00Z", "2026-11-02T16:00:00Z")

    assert respuesta.status_code == 400
    assert respuesta.get_json() == RESPUESTA_DURACION_EXCEDIDA


def test_duracion_excedida_con_espacio_inexistente(client, sesion, cabecera, solicitante):
    respuesta = _crear(client, cabecera(solicitante), ESPACIO_INEXISTENTE,
                       INICIO_Z, "2026-11-03T15:00:00Z")

    assert respuesta.status_code == 400
    assert respuesta.get_json() == RESPUESTA_DURACION_EXCEDIDA


def test_un_rechazo_no_cambia_el_listado_ni_el_historial(client, sesion, cabecera, solicitante,
                                                         aprobador, espacio):
    cabeceras = cabecera(solicitante)
    assert _crear(client, cabeceras, espacio, INICIO_Z, "2026-11-03T11:00:00Z").status_code == 201
    consultas = ["/api/reservas", "/api/historial"]
    antes = [client.get(ruta, headers=cabecera(aprobador)) for ruta in consultas]
    assert [r.status_code for r in antes] == [200, 200]
    assert [len(r.get_json()) for r in antes] == [1, 1]

    rechazada = _crear(client, cabeceras, espacio, INICIO_Z, "2026-11-03T14:00:01Z")

    assert rechazada.status_code == 400
    despues = [client.get(ruta, headers=cabecera(aprobador)) for ruta in consultas]
    assert [r.get_json() for r in despues] == [r.get_json() for r in antes]


def test_sin_token_responde_401_aunque_la_duracion_este_excedida(client, sesion, cabecera, aprobador,
                                                                 espacio):
    respuesta = _crear(client, None, espacio, INICIO_Z, "2026-11-03T15:00:00Z")

    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"]["codigo"] == "token_ausente"
    assert client.get("/api/reservas", headers=cabecera(aprobador)).get_json() == []


# --- 4.2 La regla solo se aplica al crear -------------------------------------


@pytest.fixture
def larga(sembrar_reserva, solicitante, espacio):
    """Siembra una reserva de 6 horas del solicitante en el estado indicado."""

    def _sembrar(estado="pendiente"):
        return sembrar_reserva(espacio, solicitante, INICIO_LARGA, FIN_LARGA, estado=estado)

    return _sembrar


def test_aprobar_una_solicitud_existente_de_mas_de_cuatro_horas(client, cabecera, aprobador, larga):
    respuesta = client.post(f"/api/reservas/{larga()}/aprobar", headers=cabecera(aprobador))

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert (cuerpo["estado"], cuerpo["inicio"], cuerpo["fin"]) == ("aprobada", INICIO_Z, FIN_Z)


def test_rechazar_una_solicitud_existente_de_mas_de_cuatro_horas(client, cabecera, aprobador, larga):
    respuesta = client.post(f"/api/reservas/{larga()}/rechazar", headers=cabecera(aprobador),
                            json={"motivo": "Sala en obras"})

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert (cuerpo["estado"], cuerpo["inicio"], cuerpo["fin"]) == ("rechazada", INICIO_Z, FIN_Z)


@pytest.mark.parametrize("estado", ["pendiente", "aprobada"])
def test_cancelar_una_reserva_existente_de_mas_de_cuatro_horas(client, cabecera, solicitante, larga,
                                                               estado):
    respuesta = client.post(f"/api/reservas/{larga(estado)}/cancelar",
                            headers=cabecera(solicitante))

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert (cuerpo["estado"], cuerpo["inicio"], cuerpo["fin"]) == ("cancelada", INICIO_Z, FIN_Z)


def test_listado_y_detalle_devuelven_la_reserva_sin_cambios(client, cabecera, solicitante,
                                                            aprobador, larga):
    reserva = larga("aprobada")

    for usuario in (solicitante, aprobador):
        listado = client.get("/api/reservas", headers=cabecera(usuario))
        detalle = client.get(f"/api/reservas/{reserva}", headers=cabecera(usuario))

        assert (listado.status_code, detalle.status_code) == (200, 200)
        assert [(r["id"], r["inicio"], r["fin"]) for r in listado.get_json()] == [
            (reserva, INICIO_Z, FIN_Z)
        ]
        assert (detalle.get_json()["inicio"], detalle.get_json()["fin"]) == (INICIO_Z, FIN_Z)


def test_disponibilidad_con_un_rango_de_mas_de_cuatro_horas(client, cabecera, solicitante, espacio,
                                                            larga):
    larga("aprobada")
    rango = urlencode({"inicio": "2026-11-03T08:00:00Z", "fin": "2026-11-03T18:00:00Z"})

    respuesta = client.get(f"/api/espacios/{espacio}/disponibilidad?{rango}",
                           headers=cabecera(solicitante))

    assert respuesta.status_code == 200
    assert respuesta.get_json() == [{"inicio": INICIO_Z, "fin": FIN_Z}]


def test_historial_con_un_rango_de_mas_de_cuatro_horas(client, cabecera, aprobador, larga):
    reserva = larga()
    assert client.post(f"/api/reservas/{reserva}/aprobar",
                       headers=cabecera(aprobador)).status_code == 200
    rango = urlencode({"desde": "2026-11-02T09:00:00Z", "hasta": "2026-11-02T15:00:00Z"})

    respuesta = client.get(f"/api/historial?{rango}", headers=cabecera(aprobador))

    assert respuesta.status_code == 200
    assert [(e["reserva_id"], e["estado_nuevo"]) for e in respuesta.get_json()] == [
        (reserva, "aprobada")
    ]
