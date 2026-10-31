"""Pruebas de integración de la API de reservas (tarea 4.1).

`POST /api/reservas` (`reservas:crear`), `GET /api/espacios/{id}/disponibilidad`
(`espacios:ver`), `GET /api/reservas` y `GET /api/reservas/{id}`
(`reservas:ver_propias`, ampliado con `reservas:ver_todas`). Requisitos
«Creación de solicitudes de reserva», «Consulta de disponibilidad de un
espacio por rango» y «Listado y detalle de solicitudes» de la spec `reservas`.

El reloj se inyecta con `app.config["RELOJ"]` y las reservas aprobadas se
siembran directamente en el repositorio.
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import pytest
from sqlalchemy import event, text

from backend.app.extensions import db
from backend.app.reservas import repositories

AHORA = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
ROLES = ["solicitante", "aprobador", "admin"]
CAMPOS_DE_SOLICITUD = {"id", "espacio_id", "solicitante_id", "inicio", "fin", "estado"}


def _h(hora, minuto=0):
    return datetime(2026, 11, 3, hora, minuto, tzinfo=timezone.utc)


def _z(hora, minuto=0):
    return f"2026-11-03T{hora:02d}:{minuto:02d}:00Z"


@pytest.fixture(autouse=True)
def reloj_fijo(app):
    app.config["RELOJ"] = lambda: AHORA


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio("Laboratorio A")


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _error(respuesta, http, codigo):
    assert respuesta.status_code == http
    cuerpo = respuesta.get_json()
    assert set(cuerpo) == {"error"}
    assert set(cuerpo["error"]) == {"codigo", "mensaje"}
    assert cuerpo["error"]["codigo"] == codigo


def _cantidad(sesion):
    sesion.expire_all()
    return len(repositories.listar_todas())


def _crear(client, cabecera=None, json=None, **kwargs):
    return client.post("/api/reservas", headers=cabecera, json=json, **kwargs)


def _disponibilidad(client, espacio_id, cabecera=None, **rango):
    consulta = f"?{urlencode(rango)}" if rango else ""
    return client.get(f"/api/espacios/{espacio_id}/disponibilidad{consulta}", headers=cabecera)


def _solicitud(espacio_id, inicio=_z(10), fin=_z(12)):
    return {"espacio_id": espacio_id, "inicio": inicio, "fin": fin}


# --- POST /api/reservas -------------------------------------------------------


@pytest.mark.parametrize("rol", ROLES)
def test_creacion_valida_por_rol(client, sesion, crear_cuenta, cabecera, espacio, rol):
    usuario = crear_cuenta(rol)

    respuesta = _crear(client, cabecera(usuario),
                       _solicitud(espacio, "2026-11-03T05:00:00-05:00", _z(12)))

    assert respuesta.status_code == 201
    creada = respuesta.get_json()
    assert set(creada) == CAMPOS_DE_SOLICITUD
    assert creada == {"id": creada["id"], "espacio_id": espacio, "solicitante_id": usuario,
                      "inicio": _z(10), "fin": _z(12), "estado": "pendiente"}
    assert _cantidad(sesion) == 1


def test_creacion_sin_autenticacion(client, sesion, espacio):
    _error(_crear(client, json=_solicitud(espacio)), 401, "token_ausente")
    assert _cantidad(sesion) == 0


@pytest.mark.parametrize(
    "cambios",
    [
        {"inicio": None},
        {"inicio": "2026-11-03T10:00:00"},
        {"fin": _z(10)},
        {"inicio": "2026-11-02T12:00:00Z", "fin": _z(12)},
        {"inicio": "2026-11-01T10:00:00Z", "fin": "2026-11-01T12:00:00Z"},
        {"solicitante_id": 1},
        {"estado": "aprobada"},
    ],
    ids=["sin_inicio", "sin_zona_horaria", "fin_igual_al_inicio", "inicio_en_el_instante_actual",
         "inicio_en_el_pasado", "solicitante_en_el_cuerpo", "estado_en_el_cuerpo"],
)
def test_creacion_con_datos_invalidos(client, sesion, crear_cuenta, cabecera, espacio, cambios):
    datos = {**_solicitud(espacio), **cambios}
    datos = {k: v for k, v in datos.items() if v is not None}

    _error(_crear(client, cabecera(crear_cuenta("solicitante")), datos), 400, "datos_invalidos")
    assert _cantidad(sesion) == 0


@pytest.mark.parametrize("cuerpo", ["{no es json", "[1, 2]"])
def test_creacion_con_cuerpo_que_no_es_un_objeto_json(client, sesion, crear_cuenta, cabecera,
                                                      cuerpo):
    respuesta = _crear(client, cabecera(crear_cuenta("solicitante")), data=cuerpo,
                       content_type="application/json")
    _error(respuesta, 400, "datos_invalidos")


def test_creacion_sobre_espacio_inexistente(client, sesion, crear_cuenta, cabecera):
    _error(_crear(client, cabecera(crear_cuenta("solicitante")), _solicitud(999)), 404,
           "espacio_no_encontrado")
    assert _cantidad(sesion) == 0


def test_creacion_sobre_espacio_inactivo_y_reactivado(client, sesion, crear_cuenta, cabecera,
                                                      espacio):
    gestor = cabecera(crear_cuenta("aprobador"))
    solicitante = cabecera(crear_cuenta("solicitante"))
    assert client.post(f"/api/espacios/{espacio}/desactivar", headers=gestor).status_code == 200

    _error(_crear(client, solicitante, _solicitud(espacio)), 400, "espacio_inactivo")
    assert _cantidad(sesion) == 0

    assert client.post(f"/api/espacios/{espacio}/activar", headers=gestor).status_code == 200
    respuesta = _crear(client, solicitante, _solicitud(espacio))
    assert (respuesta.status_code, respuesta.get_json()["estado"]) == (201, "pendiente")


def test_creacion_solapada_con_una_aprobada(client, sesion, crear_cuenta, cabecera, espacio,
                                            sembrar_reserva):
    sembrar_reserva(espacio, crear_cuenta("aprobador"), _h(10), _h(12))
    solicitante = cabecera(crear_cuenta("solicitante"))

    _error(_crear(client, solicitante, _solicitud(espacio, _z(11), _z(13))), 409,
           "reserva_solapada")
    assert _cantidad(sesion) == 1

    # Termina exactamente cuando empieza otra: permitida.
    respuesta = _crear(client, solicitante, _solicitud(espacio, _z(12), _z(13)))
    assert respuesta.status_code == 201


# --- GET /api/espacios/{id}/disponibilidad --------------------------------------


@pytest.mark.parametrize("rol", ROLES)
def test_disponibilidad_por_rol(client, sesion, crear_cuenta, cabecera, nuevo_espacio,
                                sembrar_reserva, rol):
    espacio = nuevo_espacio("Laboratorio A")
    otro = crear_cuenta("solicitante", correo="otro@example.com")
    sembrar_reserva(espacio, otro, _h(14), _h(15))
    sembrar_reserva(espacio, otro, _h(10), _h(12))
    sembrar_reserva(espacio, otro, _h(7), _h(9))
    sembrar_reserva(espacio, otro, _h(6), _h(7))  # solo toca el borde de [07:00, ...)
    sembrar_reserva(espacio, otro, _h(12), _h(14), estado="pendiente")

    respuesta = _disponibilidad(client, espacio, cabecera(crear_cuenta(rol)),
                                inicio=_z(8), fin=_z(18))

    assert respuesta.status_code == 200
    assert respuesta.get_json() == [
        {"inicio": _z(7), "fin": _z(9)},
        {"inicio": _z(10), "fin": _z(12)},
        {"inicio": _z(14), "fin": _z(15)},
    ]


def test_disponibilidad_con_desplazamiento_codificado_en_la_url(client, sesion, crear_cuenta,
                                                                 cabecera, espacio,
                                                                 sembrar_reserva):
    sembrar_reserva(espacio, crear_cuenta("aprobador"), _h(10), _h(12))

    respuesta = _disponibilidad(client, espacio, cabecera(crear_cuenta("solicitante")),
                                inicio="2026-11-03T03:00:00-05:00",
                                fin="2026-11-03T13:00:00+00:00")

    assert respuesta.get_json() == [{"inicio": _z(10), "fin": _z(12)}]


def test_disponibilidad_vacia_y_espacio_inactivo(client, sesion, crear_cuenta, cabecera,
                                                 espacio, sembrar_reserva):
    usuario = cabecera(crear_cuenta("solicitante"))
    assert _disponibilidad(client, espacio, usuario, inicio=_z(8), fin=_z(18)).get_json() == []

    sembrar_reserva(espacio, crear_cuenta("aprobador"), _h(10), _h(12))
    desactivado = client.post(f"/api/espacios/{espacio}/desactivar",
                              headers=cabecera(crear_cuenta("admin")))
    assert desactivado.status_code == 200
    respuesta = _disponibilidad(client, espacio, usuario, inicio=_z(8), fin=_z(18))
    assert (respuesta.status_code, respuesta.get_json()) == (
        200, [{"inicio": _z(10), "fin": _z(12)}])


@pytest.mark.parametrize(
    "rango",
    [{"fin": _z(18)}, {"inicio": _z(8)}, {}, {"inicio": "2026-11-03T08:00:00", "fin": _z(18)},
     {"inicio": _z(18), "fin": _z(8)}, {"inicio": _z(8), "fin": _z(8)}],
    ids=["sin_inicio", "sin_fin", "sin_rango", "sin_zona_horaria", "fin_anterior", "fin_igual"],
)
def test_disponibilidad_con_rango_invalido(client, sesion, crear_cuenta, cabecera, espacio,
                                           rango):
    _error(_disponibilidad(client, espacio, cabecera(crear_cuenta("solicitante")), **rango),
           400, "datos_invalidos")


def test_disponibilidad_de_un_espacio_inexistente(client, sesion, crear_cuenta, cabecera):
    _error(_disponibilidad(client, 999, cabecera(crear_cuenta("solicitante")),
                           inicio=_z(8), fin=_z(18)), 404, "espacio_no_encontrado")


def test_disponibilidad_sin_autenticacion(client, sesion, espacio):
    _error(_disponibilidad(client, espacio, inicio=_z(8), fin=_z(18)), 401, "token_ausente")


# --- GET /api/reservas y GET /api/reservas/{id} ---------------------------------


@pytest.fixture
def escenario(sesion, crear_cuenta, nuevo_espacio, sembrar_reserva):
    """Solicitudes de dos solicitantes y del aprobador, sembradas fuera de orden."""
    espacio = nuevo_espacio()
    u = {
        "ana": crear_cuenta("solicitante", correo="ana@example.com"),
        "luis": crear_cuenta("solicitante", correo="luis@example.com"),
        "aprobador": crear_cuenta("aprobador"),
        "admin": crear_cuenta("admin"),
    }
    r = {
        "luis": sembrar_reserva(espacio, u["luis"], _h(15), _h(16), "pendiente"),
        "ana_tarde": sembrar_reserva(espacio, u["ana"], _h(11), _h(12), "aprobada"),
        "ana_temprano": sembrar_reserva(espacio, u["ana"], _h(9), _h(10), "pendiente"),
        "aprobador": sembrar_reserva(espacio, u["aprobador"], _h(9), _h(10), "pendiente"),
    }
    return u, r


def _ids(respuesta):
    assert respuesta.status_code == 200
    return [s["id"] for s in respuesta.get_json()]


def test_listado_del_solicitante_solo_propias(client, cabecera, escenario):
    u, r = escenario
    respuesta = client.get("/api/reservas", headers=cabecera(u["ana"]))
    assert _ids(respuesta) == [r["ana_temprano"], r["ana_tarde"]]
    assert all(set(s) == CAMPOS_DE_SOLICITUD for s in respuesta.get_json())
    assert {s["solicitante_id"] for s in respuesta.get_json()} == {u["ana"]}


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_listado_de_aprobador_y_admin_todas(client, cabecera, escenario, rol):
    u, r = escenario
    assert _ids(client.get("/api/reservas", headers=cabecera(u[rol]))) == [
        r["ana_temprano"], r["aprobador"], r["ana_tarde"], r["luis"]]


@pytest.mark.parametrize("rol", ROLES)
def test_listado_vacio(client, sesion, crear_cuenta, cabecera, rol):
    respuesta = client.get("/api/reservas", headers=cabecera(crear_cuenta(rol)))
    assert (respuesta.status_code, respuesta.get_json()) == (200, [])


def test_detalle_propio(client, cabecera, escenario):
    u, r = escenario
    respuesta = client.get(f"/api/reservas/{r['ana_tarde']}", headers=cabecera(u["ana"]))
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": r["ana_tarde"], "espacio_id": respuesta.get_json()["espacio_id"],
        "solicitante_id": u["ana"], "inicio": _z(11), "fin": _z(12), "estado": "aprobada"}


def test_detalle_ajeno_por_un_solicitante(client, cabecera, escenario):
    u, r = escenario
    respuesta = client.get(f"/api/reservas/{r['luis']}", headers=cabecera(u["ana"]))
    # `_error` comprueba que el cuerpo contiene solo el error, sin datos de la solicitud.
    _error(respuesta, 403, "permiso_insuficiente")


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_detalle_ajeno_por_aprobador_o_admin(client, cabecera, escenario, rol):
    u, r = escenario
    respuesta = client.get(f"/api/reservas/{r['luis']}", headers=cabecera(u[rol]))
    assert (respuesta.status_code, respuesta.get_json()["solicitante_id"]) == (200, u["luis"])


@pytest.mark.parametrize("rol", ["ana", "aprobador", "admin"])
def test_detalle_inexistente(client, cabecera, escenario, rol):
    u, _ = escenario
    _error(client.get("/api/reservas/999999", headers=cabecera(u[rol])), 404,
           "solicitud_no_encontrada")


@pytest.mark.parametrize("ruta", ["/api/reservas", "/api/reservas/1"])
def test_listado_y_detalle_sin_autenticacion(client, sesion, ruta):
    _error(client.get(ruta), 401, "token_ausente")


# --- Fechas en UTC con sufijo Z aunque la sesión de PostgreSQL use otra zona ----


def test_las_fechas_se_serializan_en_utc_con_otra_zona_en_la_sesion(
    client, sesion, crear_cuenta, cabecera, espacio, sembrar_reserva
):
    def _zona_de_bogota(conexion_dbapi, _registro):
        cursor = conexion_dbapi.cursor()
        cursor.execute("SET TIME ZONE 'America/Bogota'")
        cursor.close()
        conexion_dbapi.commit()

    usuario = crear_cuenta("solicitante")
    sembrar_reserva(espacio, usuario, _h(14), _h(15))
    autorizado = cabecera(usuario)
    sesion.close()
    event.listen(db.engine, "connect", _zona_de_bogota)
    db.engine.dispose()

    # La sesión devuelve los instantes en -05:00, no en UTC.
    assert sesion.execute(text("SHOW TIME ZONE")).scalar_one() == "America/Bogota"
    sembrada = repositories.listar_todas()[0]
    assert sembrada.inicio_utc.utcoffset() == timedelta(hours=-5)
    assert sembrada.inicio_utc == _h(14)
    sesion.close()

    creada = _crear(client, autorizado, _solicitud(espacio, "2026-11-03T05:00:00-05:00", _z(12)))
    assert creada.status_code == 201
    assert (creada.get_json()["inicio"], creada.get_json()["fin"]) == (_z(10), _z(12))

    listado = client.get("/api/reservas", headers=autorizado).get_json()
    assert [(s["inicio"], s["fin"]) for s in listado] == [(_z(10), _z(12)), (_z(14), _z(15))]

    detalle = client.get(f"/api/reservas/{creada.get_json()['id']}", headers=autorizado)
    assert (detalle.get_json()["inicio"], detalle.get_json()["fin"]) == (_z(10), _z(12))

    intervalos = _disponibilidad(client, espacio, autorizado, inicio=_z(8), fin=_z(18))
    assert intervalos.get_json() == [{"inicio": _z(14), "fin": _z(15)}]
