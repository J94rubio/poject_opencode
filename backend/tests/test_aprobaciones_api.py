"""API de decisiones (tareas 4.1 y 4.2 de `aprobacion-reservas`).

Requisitos «Aprobación de solicitudes pendientes», «Rechazo de solicitudes
pendientes con motivo», «Transiciones permitidas desde el estado pendiente»,
«Prohibición de decidir las propias solicitudes» y «Control de acceso a las
decisiones» de la spec `aprobaciones`. El reloj se inyecta con
`app.config["RELOJ"]` y las fechas son de 2030.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.aprobaciones import services
from backend.app.auth.errors import PermisoInsuficiente

AHORA = datetime(2030, 1, 10, 8, 0, tzinfo=timezone.utc)
MOTIVO = {"motivo": "Sala en mantenimiento"}
CAMPOS = {"id", "espacio_id", "solicitante_id", "inicio", "fin", "estado"}


def _h(hora):
    return datetime(2030, 1, 10, hora, tzinfo=timezone.utc)


def _z(hora):
    return f"2030-01-10T{hora:02d}:00:00Z"


@pytest.fixture(autouse=True)
def reloj_fijo(app):
    app.config["RELOJ"] = lambda: AHORA


@pytest.fixture
def usuarios(crear_cuenta):
    return {rol: crear_cuenta(rol) for rol in ("solicitante", "aprobador", "admin")}


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio()


@pytest.fixture
def pendiente(sembrar_reserva, espacio, usuarios):
    def _crear(inicio=_h(10), fin=_h(12), rol="solicitante"):
        return sembrar_reserva(espacio, usuarios[rol], inicio, fin, "pendiente")

    return _crear


def _aprobar(client, cabeceras, reserva_id, **kwargs):
    return client.post(f"/api/reservas/{reserva_id}/aprobar", headers=cabeceras, **kwargs)


def _rechazar(client, cabeceras, reserva_id, **kwargs):
    kwargs = kwargs or {"json": MOTIVO}
    return client.post(f"/api/reservas/{reserva_id}/rechazar", headers=cabeceras, **kwargs)


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _detalle(client, cabeceras, reserva_id):
    return client.get(f"/api/reservas/{reserva_id}", headers=cabeceras).get_json()


# --- Roles -------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_aprobacion_por_rol(client, sesion, usuarios, cabecera, pendiente, espacio, rol):
    reserva_id = pendiente()

    respuesta = _aprobar(client, cabecera(usuarios[rol]), reserva_id)

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": reserva_id, "espacio_id": espacio, "solicitante_id": usuarios["solicitante"],
        "inicio": _z(10), "fin": _z(12), "estado": "aprobada",
    }


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_rechazo_por_rol(client, sesion, usuarios, cabecera, pendiente, espacio, rol):
    reserva_id = pendiente()

    respuesta = _rechazar(client, cabecera(usuarios[rol]), reserva_id)

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": reserva_id, "espacio_id": espacio, "solicitante_id": usuarios["solicitante"],
        "inicio": _z(10), "fin": _z(12), "estado": "rechazada",
        "motivo_rechazo": MOTIVO["motivo"],
    }


@pytest.mark.parametrize("accion", [_aprobar, _rechazar], ids=["aprobar", "rechazar"])
def test_decision_de_un_solicitante(client, sesion, crear_cuenta, usuarios, cabecera, pendiente,
                                    accion):
    reserva_id = pendiente()
    otro = crear_cuenta("solicitante", correo="otro@example.com")

    respuesta = accion(client, cabecera(otro), reserva_id)

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _detalle(client, cabecera(usuarios["admin"]), reserva_id)["estado"] == "pendiente"


@pytest.mark.parametrize("accion", ["aprobar", "rechazar"])
def test_decision_sin_sesion(client, sesion, pendiente, accion):
    respuesta = client.post(f"/api/reservas/{pendiente()}/{accion}", json=MOTIVO)

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"


@pytest.mark.parametrize("accion", [_aprobar, _rechazar], ids=["aprobar", "rechazar"])
@pytest.mark.parametrize("reserva_id", [999_999, 2_147_483_648], ids=["inexistente", "fuera_de_rango"])
def test_decision_sobre_una_solicitud_inexistente(client, sesion, usuarios, cabecera, accion,
                                                  reserva_id):
    respuesta = accion(client, cabecera(usuarios["aprobador"]), reserva_id)

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "solicitud_no_encontrada"


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
@pytest.mark.parametrize("accion", [_aprobar, _rechazar], ids=["aprobar", "rechazar"])
def test_decision_sobre_la_solicitud_propia(client, sesion, usuarios, cabecera, pendiente, rol,
                                            accion):
    reserva_id = pendiente(rol=rol)

    respuesta = accion(client, cabecera(usuarios[rol]), reserva_id)

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _detalle(client, cabecera(usuarios[rol]), reserva_id)["estado"] == "pendiente"


# --- Códigos de error de aprobar ------------------------------------------------


def test_aprobacion_con_solapamiento(client, sesion, usuarios, cabecera, pendiente, espacio,
                                     sembrar_reserva):
    reserva_id = pendiente(_h(11), _h(13))
    sembrar_reserva(espacio, usuarios["solicitante"], _h(10), _h(12), "aprobada")

    respuesta = _aprobar(client, cabecera(usuarios["aprobador"]), reserva_id)

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "reserva_solapada"


def test_aprobacion_vencida_usa_el_reloj_inyectado(client, app, sesion, usuarios, cabecera,
                                                   pendiente):
    reserva_id = pendiente()
    app.config["RELOJ"] = lambda: _h(10)

    respuesta = _aprobar(client, cabecera(usuarios["aprobador"]), reserva_id)

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "solicitud_vencida"


def test_aprobacion_sobre_un_espacio_inactivo(client, sesion, usuarios, cabecera, pendiente,
                                              espacio):
    reserva_id = pendiente()
    autorizado = cabecera(usuarios["aprobador"])
    assert client.post(f"/api/espacios/{espacio}/desactivar", headers=autorizado).status_code == 200

    respuesta = _aprobar(client, autorizado, reserva_id)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "espacio_inactivo"


@pytest.mark.parametrize("accion", [_aprobar, _rechazar], ids=["aprobar", "rechazar"])
def test_segunda_decision_con_transicion_invalida(client, sesion, usuarios, cabecera, pendiente,
                                                  accion):
    reserva_id = pendiente()
    autorizado = cabecera(usuarios["aprobador"])
    assert _rechazar(client, autorizado, reserva_id).status_code == 200

    respuesta = accion(client, autorizado, reserva_id, json={"motivo": "Otro motivo"})

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "transicion_invalida"
    assert _detalle(client, autorizado, reserva_id)["motivo_rechazo"] == MOTIVO["motivo"]


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"json": {"motivo": 1, "extra": True}}, {"json": []},
     {"data": "no es json", "content_type": "text/plain"},
     {"data": "{mal formado", "content_type": "application/json"}],
    ids=["sin_cuerpo", "objeto_cualquiera", "lista", "texto", "json_mal_formado"],
)
def test_aprobar_ignora_el_cuerpo(client, sesion, usuarios, cabecera, pendiente, kwargs):
    respuesta = _aprobar(client, cabecera(usuarios["aprobador"]), pendiente(), **kwargs)

    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "aprobada"


# --- Cuerpo del rechazo -----------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"json": {}},
        {"json": {"motivo": ""}},
        {"json": {"motivo": "   "}},
        {"json": {"motivo": "x" * 501}},
        {"json": {"motivo": 123}},
        {"json": {"motivo": None}},
        {"json": {"motivo": ["texto"]}},
        {"json": {"motivo": "Válido", "estado": "aprobada"}},
        {"json": ["motivo"]},
        {"json": "motivo"},
        {"data": "motivo", "content_type": "text/plain"},
        {"data": "{mal formado", "content_type": "application/json"},
        {"data": b'{"motivo": "a\\u0000b"}', "content_type": "application/json"},
        {"data": b'{"motivo": "a\\ud800b"}', "content_type": "application/json"},
    ],
    ids=["sin_motivo", "vacio", "espacios", "501", "numero", "nulo", "lista", "campo_adicional",
         "cuerpo_lista", "cuerpo_texto_json", "no_json", "json_mal_formado", "nul", "sustituto"],
)
def test_rechazo_con_cuerpo_invalido(client, sesion, usuarios, cabecera, pendiente, kwargs):
    reserva_id = pendiente()
    autorizado = cabecera(usuarios["aprobador"])

    respuesta = _rechazar(client, autorizado, reserva_id, **kwargs)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _detalle(client, autorizado, reserva_id)["estado"] == "pendiente"


def test_rechazo_sin_cuerpo(client, sesion, usuarios, cabecera, pendiente):
    respuesta = client.post(f"/api/reservas/{pendiente()}/rechazar",
                            headers=cabecera(usuarios["aprobador"]))

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"


def test_el_cuerpo_del_rechazo_se_valida_en_su_lugar_del_orden(client, sesion, usuarios, cabecera,
                                                               pendiente, sembrar_reserva, espacio):
    autorizado = cabecera(usuarios["aprobador"])
    cuerpo = {"data": "no es json", "content_type": "text/plain"}

    # Existencia y autoría van antes que el cuerpo.
    assert _codigo(_rechazar(client, autorizado, 999_999, **cuerpo)) == "solicitud_no_encontrada"
    propia = pendiente(rol="aprobador")
    assert _codigo(_rechazar(client, autorizado, propia, **cuerpo)) == "permiso_insuficiente"
    # El cuerpo va antes que el estado.
    aprobada = sembrar_reserva(espacio, usuarios["solicitante"], _h(10), _h(12), "aprobada")
    assert _codigo(_rechazar(client, autorizado, aprobada, **cuerpo)) == "datos_invalidos"


# --- Motivo en las respuestas de solicitudes ----------------------------------------


def test_el_solicitante_ve_el_motivo_en_el_detalle_de_su_solicitud(client, sesion, usuarios,
                                                                   cabecera, pendiente):
    reserva_id = pendiente()
    assert _rechazar(client, cabecera(usuarios["aprobador"]), reserva_id).status_code == 200

    respuesta = client.get(f"/api/reservas/{reserva_id}", headers=cabecera(usuarios["solicitante"]))

    assert respuesta.status_code == 200
    assert respuesta.get_json()["motivo_rechazo"] == MOTIVO["motivo"]


def test_el_motivo_aparece_en_el_listado_solo_en_las_rechazadas(client, sesion, usuarios, cabecera,
                                                                sembrar_reserva, espacio):
    for hora, estado in ((8, "cancelada"), (9, "pendiente"), (10, "aprobada"), (11, "rechazada")):
        sembrar_reserva(espacio, usuarios["solicitante"], _h(hora), _h(hora + 1), estado)

    lista = client.get("/api/reservas", headers=cabecera(usuarios["aprobador"])).get_json()

    assert {s["estado"]: set(s) for s in lista} == {
        "cancelada": CAMPOS, "pendiente": CAMPOS, "aprobada": CAMPOS,
        "rechazada": CAMPOS | {"motivo_rechazo"},
    }


# --- 4.2 Disponibilidad ---------------------------------------------------------------


def _disponibilidad(client, cabeceras, espacio):
    return client.get(
        f"/api/espacios/{espacio}/disponibilidad",
        query_string={"inicio": _z(8), "fin": _z(18)},
        headers=cabeceras,
    ).get_json()


def test_la_reserva_aprobada_ocupa_el_espacio(client, sesion, usuarios, cabecera, pendiente, espacio):
    autorizado = cabecera(usuarios["aprobador"])
    reserva_id = pendiente()
    assert _disponibilidad(client, autorizado, espacio) == []

    assert _aprobar(client, autorizado, reserva_id).status_code == 200

    assert _disponibilidad(client, autorizado, espacio) == [{"inicio": _z(10), "fin": _z(12)}]


def test_la_reserva_rechazada_no_ocupa_el_espacio(client, sesion, usuarios, cabecera, pendiente,
                                                  espacio):
    autorizado = cabecera(usuarios["aprobador"])

    assert _rechazar(client, autorizado, pendiente()).status_code == 200

    assert _disponibilidad(client, autorizado, espacio) == []


# --- Errores internos -----------------------------------------------------------------


def test_otra_violacion_de_integridad_responde_error_interno(client, sesion, monkeypatch, usuarios,
                                                             cabecera, pendiente):
    reserva_id = pendiente()
    autorizado = cabecera(usuarios["aprobador"])
    monkeypatch.setattr(services, "_validar_motivo", lambda _motivo: None)

    respuesta = _rechazar(client, autorizado, reserva_id)

    assert respuesta.status_code == 500
    assert _codigo(respuesta) == "error_interno"
    assert _detalle(client, autorizado, reserva_id)["estado"] == "pendiente"
