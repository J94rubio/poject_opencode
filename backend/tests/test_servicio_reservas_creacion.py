"""Servicio de creación de solicitudes de reserva (tareas 3.2, 3.3 y 3.4).

Requisitos «Creación de solicitudes de reserva», «Catálogo de estados de una
reserva» y «Ocupación por reservas aprobadas» de la spec `reservas`. El reloj
se inyecta siempre: ninguna prueba depende de la fecha real. Las reservas
aprobadas se siembran directamente en el repositorio.
"""

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.auth.errors import (
    DatosInvalidos,
    EspacioInactivo,
    EspacioNoEncontrado,
    ReservaSolapada,
)
from backend.app.espacios import services as servicio_espacios
from backend.app.reservas import repositories, services
from backend.app.usuarios import repositories as repositorio_usuarios

AHORA = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)


def reloj():
    return AHORA


def _h(hora, minuto=0):
    return datetime(2026, 11, 3, hora, minuto, tzinfo=timezone.utc)


def _iso(fecha):
    return fecha.isoformat()


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio("Laboratorio A")


@pytest.fixture
def solicitante(crear_cuenta):
    return repositorio_usuarios.obtener_usuario_por_id(crear_cuenta("solicitante"))


def _datos(espacio_id, inicio=_h(10), fin=_h(12)):
    return {"espacio_id": espacio_id, "inicio": _iso(inicio), "fin": _iso(fin)}


def _reservas(sesion):
    sesion.expire_all()
    return [(r.espacio_id, r.solicitante_id, r.inicio_utc, r.fin_utc, r.estado)
            for r in repositories.listar_todas()]


def _rechaza(sesion, datos, usuario, excepcion, http, codigo):
    antes = _reservas(sesion)
    with pytest.raises(excepcion) as error:
        services.crear_solicitud(datos, usuario, reloj=reloj)
    assert (error.value.http, error.value.codigo) == (http, codigo)
    assert _reservas(sesion) == antes


def _datos_invalidos(sesion, datos, usuario):
    _rechaza(sesion, datos, usuario, DatosInvalidos, 400, "datos_invalidos")


# --- 3.2 Validación de fechas y del cuerpo ------------------------------------


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("2026-11-03T10:00:00Z", _h(10)),
        ("2026-11-03T10:00:00+00:00", _h(10)),
        ("2026-11-03T05:00:00-05:00", _h(10)),
        ("2026-11-03T12:30:00+02:30", _h(10)),
        ("2026-11-03T10:00:00.250000Z", _h(10) + timedelta(milliseconds=250)),
    ],
)
def test_convertir_fecha_con_zona_horaria_a_utc(texto, esperado):
    fecha = services.convertir_fecha(texto)
    assert fecha == esperado
    assert fecha.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    "valor",
    ["2026-11-03T10:00:00", "2026-11-03", "10:00", "mañana", "", None, 20261103, True,
     ["2026-11-03T10:00:00Z"]],
)
def test_convertir_fecha_rechaza_sin_zona_horaria_o_formato_invalido(valor):
    with pytest.raises(DatosInvalidos):
        services.convertir_fecha(valor)


def test_creacion_valida_en_estado_pendiente(sesion, espacio, solicitante):
    reserva = services.crear_solicitud(
        {"espacio_id": espacio, "inicio": "2026-11-03T05:00:00-05:00",
         "fin": "2026-11-03T12:00:00Z"},
        solicitante, reloj=reloj,
    )

    assert (reserva.espacio_id, reserva.solicitante_id, reserva.estado) == (
        espacio, solicitante.id, "pendiente")
    assert _reservas(sesion) == [(espacio, solicitante.id, _h(10), _h(12), "pendiente")]


@pytest.mark.parametrize("campo", ["inicio", "fin"])
def test_fecha_sin_zona_horaria_es_invalida(sesion, espacio, solicitante, campo):
    datos = _datos(espacio)
    datos[campo] = datos[campo].replace("+00:00", "")
    _datos_invalidos(sesion, datos, solicitante)


@pytest.mark.parametrize("fin", [_h(10), _h(9)], ids=["fin_igual", "fin_anterior"])
def test_fin_igual_o_anterior_al_inicio(sesion, espacio, solicitante, fin):
    _datos_invalidos(sesion, _datos(espacio, _h(10), fin), solicitante)


def test_fin_igual_al_inicio_expresado_en_otra_zona(sesion, espacio, solicitante):
    datos = {"espacio_id": espacio, "inicio": "2026-11-03T10:00:00Z",
             "fin": "2026-11-03T05:00:00-05:00"}
    _datos_invalidos(sesion, datos, solicitante)


@pytest.mark.parametrize(
    "inicio",
    [AHORA - timedelta(days=1), AHORA - timedelta(microseconds=1), AHORA],
    ids=["un_dia_antes", "un_instante_antes", "instante_actual"],
)
def test_inicio_en_el_pasado_o_en_el_instante_actual(sesion, espacio, solicitante, inicio):
    _datos_invalidos(sesion, _datos(espacio, inicio, inicio + timedelta(hours=1)), solicitante)


def test_inicio_un_instante_despues_del_actual_se_acepta(sesion, espacio, solicitante):
    inicio = AHORA + timedelta(microseconds=1)
    reserva = services.crear_solicitud(
        _datos(espacio, inicio, inicio + timedelta(hours=1)), solicitante, reloj=reloj
    )
    assert reserva.inicio_utc == inicio


def test_el_instante_actual_lo_fija_el_reloj_inyectado(sesion, espacio, solicitante):
    # La misma solicitud es válida o no según el reloj, no según la fecha real.
    datos = _datos(espacio, _h(10), _h(12))
    with pytest.raises(DatosInvalidos):
        services.crear_solicitud(datos, solicitante, reloj=lambda: _h(10))
    assert services.crear_solicitud(datos, solicitante, reloj=lambda: _h(9)).estado == "pendiente"


@pytest.mark.parametrize("campo", ["espacio_id", "inicio", "fin"])
def test_campos_obligatorios_faltantes(sesion, espacio, solicitante, campo):
    datos = _datos(espacio)
    del datos[campo]
    _datos_invalidos(sesion, datos, solicitante)


@pytest.mark.parametrize("campo", ["solicitante_id", "solicitante"])
def test_un_campo_de_solicitante_en_el_cuerpo(sesion, espacio, solicitante, campo):
    # Rechazado aunque coincida con el usuario autenticado.
    _datos_invalidos(sesion, {**_datos(espacio), campo: solicitante.id}, solicitante)


@pytest.mark.parametrize("campo,valor", [("estado", "aprobada"), ("estado", "pendiente"),
                                         ("id", 1)])
def test_la_peticion_no_puede_fijar_el_estado_ni_otros_campos(sesion, espacio, solicitante,
                                                               campo, valor):
    _datos_invalidos(sesion, {**_datos(espacio), campo: valor}, solicitante)


@pytest.mark.parametrize("valor", ["1", 1.0, True, None, [1]])
def test_espacio_id_que_no_es_un_entero(sesion, espacio, solicitante, valor):
    _datos_invalidos(sesion, {**_datos(espacio), "espacio_id": valor}, solicitante)


@pytest.mark.parametrize("datos", [None, [], "texto", 7])
def test_cuerpo_que_no_es_un_objeto(sesion, solicitante, datos):
    _datos_invalidos(sesion, datos, solicitante)


# --- 3.3 Validación del espacio -------------------------------------------------


@pytest.mark.parametrize("espacio_id", [999_999, 0, -1, 2_147_483_648])
def test_espacio_inexistente(sesion, espacio, solicitante, espacio_id):
    _rechaza(sesion, _datos(espacio_id), solicitante, EspacioNoEncontrado, 404,
             "espacio_no_encontrado")


def test_espacio_inactivo_rechaza_la_solicitud(sesion, nuevo_espacio, solicitante):
    inactivo = nuevo_espacio("Auditorio", estado="inactivo")
    _rechaza(sesion, _datos(inactivo), solicitante, EspacioInactivo, 400, "espacio_inactivo")


def test_espacio_desactivado_y_reactivado_admite_solicitudes(sesion, espacio, solicitante):
    servicio_espacios.desactivar_espacio(espacio)
    _rechaza(sesion, _datos(espacio), solicitante, EspacioInactivo, 400, "espacio_inactivo")
    servicio_espacios.activar_espacio(espacio)

    reserva = services.crear_solicitud(_datos(espacio), solicitante, reloj=reloj)

    assert reserva.estado == "pendiente"
    assert len(_reservas(sesion)) == 1


# --- 3.4 Creación y ocupación por reservas aprobadas ----------------------------


@pytest.mark.parametrize("rol", ["solicitante", "aprobador", "admin"])
def test_toda_solicitud_nace_pendiente_del_usuario_autenticado(sesion, espacio, crear_cuenta,
                                                               rol):
    usuario = repositorio_usuarios.obtener_usuario_por_id(crear_cuenta(rol))

    reserva = services.crear_solicitud(_datos(espacio), usuario, reloj=reloj)

    assert (reserva.solicitante_id, reserva.estado) == (usuario.id, "pendiente")


@pytest.mark.parametrize(
    "aprobada,solicitud",
    [((10, 12), (11, 13)), ((10, 14), (11, 12)), ((11, 12), (10, 14)), ((10, 12), (10, 12)),
     ((10, 12), (9, 11))],
    ids=["solapamiento_parcial_final", "contenida", "que_contiene", "mismo_rango",
         "solapamiento_parcial_inicial"],
)
def test_solapamiento_con_una_reserva_aprobada(sesion, espacio, solicitante, crear_cuenta,
                                                sembrar_reserva, aprobada, solicitud):
    otro = crear_cuenta("aprobador")
    sembrar_reserva(espacio, otro, _h(aprobada[0]), _h(aprobada[1]))

    _rechaza(sesion, _datos(espacio, _h(solicitud[0]), _h(solicitud[1])), solicitante,
             ReservaSolapada, 409, "reserva_solapada")


@pytest.mark.parametrize("solicitud", [(12, 13), (8, 10)],
                         ids=["empieza_cuando_termina", "termina_cuando_empieza"])
def test_borde_exacto_permitido(sesion, espacio, solicitante, sembrar_reserva, solicitud):
    sembrar_reserva(espacio, solicitante.id, _h(10), _h(12))

    reserva = services.crear_solicitud(
        _datos(espacio, _h(solicitud[0]), _h(solicitud[1])), solicitante, reloj=reloj
    )

    assert reserva.estado == "pendiente"


def test_la_misma_franja_en_otro_espacio_no_genera_conflicto(sesion, espacio, nuevo_espacio,
                                                             solicitante, sembrar_reserva):
    sembrar_reserva(espacio, solicitante.id, _h(10), _h(12))
    otro = nuevo_espacio("Laboratorio B")

    assert services.crear_solicitud(_datos(otro), solicitante, reloj=reloj).espacio_id == otro


@pytest.mark.parametrize("estado", ["rechazada", "cancelada", "pendiente"])
def test_reservas_no_aprobadas_no_ocupan(sesion, espacio, solicitante, crear_cuenta,
                                         sembrar_reserva, estado):
    sembrar_reserva(espacio, crear_cuenta("aprobador"), _h(10), _h(12), estado=estado)

    reserva = services.crear_solicitud(_datos(espacio, _h(11), _h(13)), solicitante,
                                       reloj=reloj)

    assert reserva.estado == "pendiente"
    assert len(_reservas(sesion)) == 2


def test_varias_solicitudes_pendientes_pueden_solaparse(sesion, espacio, solicitante):
    services.crear_solicitud(_datos(espacio, _h(10), _h(12)), solicitante, reloj=reloj)
    services.crear_solicitud(_datos(espacio, _h(11), _h(13)), solicitante, reloj=reloj)

    assert [r[4] for r in _reservas(sesion)] == ["pendiente", "pendiente"]
