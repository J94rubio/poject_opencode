"""Duración máxima de una solicitud (tareas 3.1, 3.2 y 3.3 de `limite-duracion-reserva`).

Requisitos «Creación de solicitudes de reserva» y «Alcance de la duración máxima» de
la spec `reservas`. El reloj se inyecta siempre y todas las fechas son fijas y llevan
zona horaria explícita: ninguna prueba depende del día real ni de la zona de la máquina.
Las reservas de más de 4 horas se siembran directamente en el repositorio.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.app.aprobaciones.services import APROBAR, RECHAZAR, decidir
from backend.app.auth.errors import (
    DatosInvalidos,
    DuracionExcedida,
    EspacioInactivo,
    EspacioNoEncontrado,
    ReservaSolapada,
)
from backend.app.cancelaciones.services import cancelar
from backend.app.espacios import services as servicio_espacios
from backend.app.historial import services as servicio_historial
from backend.app.models import EntradaHistorial, Reserva
from backend.app.reservas import services
from backend.app.usuarios import repositories as repositorio_usuarios

AHORA = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
CUATRO_HORAS = timedelta(hours=4)
ESPACIO_INEXISTENTE = 999999


def reloj():
    return AHORA


def _h(hora, minuto=0, segundo=0):
    return datetime(2026, 11, 3, hora, minuto, segundo, tzinfo=timezone.utc)


def _datos(espacio_id, inicio=_h(10), fin=_h(12)):
    return {"espacio_id": espacio_id, "inicio": inicio.isoformat(), "fin": fin.isoformat()}


def _crear(datos, usuario):
    return services.crear_solicitud(datos, usuario, reloj=reloj)


def _rastro(sesion):
    """Reservas y entradas de historial confirmadas, leídas directamente de la base."""
    sesion.rollback()
    reservas = sesion.execute(
        select(Reserva.id, Reserva.inicio_utc, Reserva.fin_utc, Reserva.estado).order_by(Reserva.id)
    ).all()
    entradas = sesion.execute(select(EntradaHistorial.id).order_by(EntradaHistorial.id)).all()
    return reservas, entradas


def _reserva_en_base(sesion, reserva_id):
    sesion.rollback()
    return tuple(sesion.execute(
        select(Reserva.estado, Reserva.inicio_utc, Reserva.fin_utc).where(Reserva.id == reserva_id)
    ).one())


def _rechaza(sesion, datos, usuario, excepcion):
    """La creación falla con `excepcion` sin añadir reservas ni entradas de historial."""
    antes = _rastro(sesion)
    with pytest.raises(excepcion) as error:
        _crear(datos, usuario)
    assert type(error.value) is excepcion
    assert _rastro(sesion) == antes
    return error.value


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio("Laboratorio A")


@pytest.fixture
def solicitante(crear_cuenta):
    return repositorio_usuarios.obtener_usuario_por_id(crear_cuenta("solicitante"))


# --- 3.1 Límite exacto de la duración -----------------------------------------


def test_la_duracion_maxima_es_de_cuatro_horas():
    assert services.DURACION_MAXIMA == CUATRO_HORAS


@pytest.mark.parametrize("fin", [_h(11), _h(14)], ids=["una_hora", "cuatro_horas_exactas"])
def test_duracion_aceptada(sesion, espacio, solicitante, fin):
    reserva = _crear(_datos(espacio, _h(10), fin), solicitante)

    assert reserva.estado == "pendiente"
    assert _reserva_en_base(sesion, reserva.id) == ("pendiente", _h(10), fin)


@pytest.mark.parametrize(
    "exceso",
    [timedelta(seconds=1), timedelta(microseconds=1)],
    ids=["un_segundo", "un_microsegundo"],
)
def test_duracion_mayor_de_cuatro_horas_rechazada(sesion, espacio, solicitante, exceso):
    error = _rechaza(sesion, _datos(espacio, _h(10), _h(14) + exceso), solicitante, DuracionExcedida)

    assert (error.http, error.codigo, error.mensaje) == (
        400, "duracion_excedida", "La duración máxima de una reserva es de 4 horas.")


def test_cuatro_horas_exactas_con_zonas_horarias_distintas(sesion, espacio, solicitante):
    reserva = _crear({"espacio_id": espacio, "inicio": "2026-11-03T10:00:00-05:00",
                      "fin": "2026-11-03T19:00:00+00:00"}, solicitante)

    assert _reserva_en_base(sesion, reserva.id) == ("pendiente", _h(15), _h(19))


def test_duracion_excedida_con_zonas_horarias_distintas(sesion, espacio, solicitante):
    _rechaza(sesion, {"espacio_id": espacio, "inicio": "2026-11-03T10:00:00+00:00",
                      "fin": "2026-11-03T10:00:01-05:00"}, solicitante, DuracionExcedida)


# --- 3.2 Precedencia con una duración mayor de 4 horas ------------------------


@pytest.mark.parametrize(
    "inicio",
    [AHORA - timedelta(hours=1), AHORA],
    ids=["inicio_pasado", "inicio_en_el_instante_actual"],
)
def test_duracion_excedida_gana_al_inicio_no_posterior_al_actual(sesion, espacio, solicitante,
                                                                 inicio):
    datos = _datos(espacio, inicio, inicio + CUATRO_HORAS + timedelta(seconds=1))
    _rechaza(sesion, datos, solicitante, DuracionExcedida)


def test_duracion_excedida_gana_al_espacio_inexistente(sesion, solicitante):
    _rechaza(sesion, _datos(ESPACIO_INEXISTENTE, _h(10), _h(15)), solicitante, DuracionExcedida)


def test_duracion_excedida_gana_al_espacio_inactivo(sesion, nuevo_espacio, solicitante):
    inactivo = nuevo_espacio("Sala inactiva", estado="inactivo")
    _rechaza(sesion, _datos(inactivo, _h(10), _h(15)), solicitante, DuracionExcedida)


def test_duracion_excedida_gana_al_solapamiento(sesion, espacio, solicitante, sembrar_reserva):
    sembrar_reserva(espacio, solicitante.id, _h(11), _h(12))
    _rechaza(sesion, _datos(espacio, _h(10), _h(15)), solicitante, DuracionExcedida)


def test_duracion_excedida_gana_al_ultimo_fin_admitido(sesion, espacio, solicitante):
    datos = {"espacio_id": espacio, "inicio": "9999-12-30T00:00:00Z",
             "fin": "9999-12-31T00:00:01Z"}
    _rechaza(sesion, datos, solicitante, DuracionExcedida)


@pytest.mark.parametrize(
    "cambios",
    [{"solicitante_id": 1}, {"estado": "aprobada"}],
    ids=["campo_de_solicitante", "campo_de_estado"],
)
def test_un_campo_no_admitido_se_valida_antes_que_la_duracion(sesion, espacio, solicitante,
                                                              cambios):
    datos = {**_datos(espacio, _h(10), _h(15)), **cambios}
    _rechaza(sesion, datos, solicitante, DatosInvalidos)


@pytest.mark.parametrize("espacio_id", ["1", 1.5, True, None])
def test_un_espacio_no_entero_se_valida_antes_que_la_duracion(sesion, solicitante, espacio_id):
    _rechaza(sesion, _datos(espacio_id, _h(10), _h(15)), solicitante, DatosInvalidos)


def test_una_fecha_sin_zona_se_valida_antes_que_la_duracion(sesion, espacio, solicitante):
    datos = {**_datos(espacio, _h(10), _h(15)), "fin": "2026-11-03T15:00:00"}
    _rechaza(sesion, datos, solicitante, DatosInvalidos)


@pytest.mark.parametrize(
    "inicio,fin",
    [(_h(10), _h(10)), (_h(10), _h(9)), (_h(20), _h(10))],
    ids=["fin_igual", "fin_anterior", "fin_anterior_por_mas_de_cuatro_horas"],
)
def test_fin_igual_o_anterior_al_inicio_sigue_siendo_datos_invalidos(sesion, espacio, solicitante,
                                                                     inicio, fin):
    _rechaza(sesion, _datos(espacio, inicio, fin), solicitante, DatosInvalidos)


# --- 3.2 Con una duración no mayor de 4 horas cada escenario conserva su código


@pytest.mark.parametrize(
    "inicio",
    [AHORA - timedelta(hours=1), AHORA],
    ids=["inicio_pasado", "inicio_en_el_instante_actual"],
)
def test_inicio_no_posterior_al_actual_conserva_su_codigo(sesion, espacio, solicitante, inicio):
    _rechaza(sesion, _datos(espacio, inicio, inicio + CUATRO_HORAS), solicitante, DatosInvalidos)


def test_espacio_inexistente_conserva_su_codigo(sesion, solicitante):
    error = _rechaza(sesion, _datos(ESPACIO_INEXISTENTE, _h(10), _h(14)), solicitante,
                     EspacioNoEncontrado)
    assert error.http == 404


def test_espacio_inactivo_conserva_su_codigo(sesion, nuevo_espacio, solicitante):
    inactivo = nuevo_espacio("Sala inactiva", estado="inactivo")
    _rechaza(sesion, _datos(inactivo, _h(10), _h(14)), solicitante, EspacioInactivo)


def test_solapamiento_conserva_su_codigo(sesion, espacio, solicitante, sembrar_reserva):
    sembrar_reserva(espacio, solicitante.id, _h(11), _h(12))
    error = _rechaza(sesion, _datos(espacio, _h(10), _h(14)), solicitante, ReservaSolapada)
    assert error.http == 409


@pytest.mark.parametrize(
    "cambios",
    [{"solicitante_id": 1}, {"fin": "2026-11-03T14:00:00"}, {"fin": None}],
    ids=["campo_de_solicitante", "fecha_sin_zona", "fin_no_es_texto"],
)
def test_datos_no_validos_conservan_su_codigo(sesion, espacio, solicitante, cambios):
    datos = {**_datos(espacio, _h(10), _h(14)), **cambios}
    _rechaza(sesion, datos, solicitante, DatosInvalidos)


def test_campo_obligatorio_faltante_conserva_su_codigo(sesion, espacio, solicitante):
    datos = _datos(espacio, _h(10), _h(14))
    del datos["fin"]
    _rechaza(sesion, datos, solicitante, DatosInvalidos)


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_creacion_por_aprobador_o_administrador_de_cuatro_horas(sesion, espacio, crear_cuenta, rol):
    usuario = repositorio_usuarios.obtener_usuario_por_id(crear_cuenta(rol))
    reserva = _crear(_datos(espacio, _h(10), _h(14)), usuario)
    assert (reserva.solicitante_id, reserva.estado) == (usuario.id, "pendiente")


def test_espacio_reactivado_admite_una_solicitud_de_cuatro_horas(sesion, nuevo_espacio, solicitante):
    reactivado = nuevo_espacio("Sala reactivada", estado="inactivo")
    servicio_espacios.activar_espacio(reactivado)
    reserva = _crear(_datos(reactivado, _h(10), _h(14)), solicitante)
    assert reserva.estado == "pendiente"


# --- 3.3 La regla solo se aplica al crear -------------------------------------


@pytest.fixture
def aprobador(crear_cuenta):
    return repositorio_usuarios.obtener_usuario_por_id(crear_cuenta("aprobador"))


def test_decidir_aprueba_una_solicitud_existente_de_mas_de_cuatro_horas(
    sesion, espacio, solicitante, aprobador, sembrar_reserva
):
    reserva = sembrar_reserva(espacio, solicitante.id, _h(10), _h(16), estado="pendiente")

    assert decidir(reserva, aprobador, APROBAR, reloj=reloj).estado == "aprobada"
    assert _reserva_en_base(sesion, reserva) == ("aprobada", _h(10), _h(16))


def test_decidir_rechaza_una_solicitud_existente_de_mas_de_cuatro_horas(
    sesion, espacio, solicitante, aprobador, sembrar_reserva
):
    reserva = sembrar_reserva(espacio, solicitante.id, _h(10), _h(16), estado="pendiente")

    assert decidir(reserva, aprobador, RECHAZAR, "Sala en obras", reloj=reloj).estado == "rechazada"
    assert _reserva_en_base(sesion, reserva) == ("rechazada", _h(10), _h(16))


@pytest.mark.parametrize("estado", ["pendiente", "aprobada"])
def test_cancelar_una_reserva_existente_de_mas_de_cuatro_horas(sesion, espacio, solicitante,
                                                               sembrar_reserva, estado):
    reserva = sembrar_reserva(espacio, solicitante.id, _h(10), _h(16), estado=estado)

    assert cancelar(reserva, solicitante, reloj=reloj).estado == "cancelada"
    assert _reserva_en_base(sesion, reserva) == ("cancelada", _h(10), _h(16))


def test_consultar_disponibilidad_con_un_rango_de_mas_de_cuatro_horas(sesion, espacio, solicitante,
                                                                      sembrar_reserva):
    sembrar_reserva(espacio, solicitante.id, _h(10), _h(16))

    ocupados = services.consultar_disponibilidad(espacio, _h(8).isoformat(), _h(18).isoformat())

    assert [(r.inicio_utc, r.fin_utc) for r in ocupados] == [(_h(10), _h(16))]


def test_consultar_el_historial_con_un_rango_de_mas_de_cuatro_horas(sesion, espacio, solicitante,
                                                                    aprobador, sembrar_reserva):
    reserva = sembrar_reserva(espacio, solicitante.id, _h(10), _h(16), estado="pendiente")
    decidir(reserva, aprobador, APROBAR, reloj=reloj)

    entradas = servicio_historial.consultar(
        aprobador,
        desde=(AHORA - timedelta(hours=3)).isoformat(),
        hasta=(AHORA + timedelta(hours=3)).isoformat(),
    )

    assert [(e.reserva_id, e.estado_nuevo, e.fecha_utc) for e in entradas] == [
        (reserva, "aprobada", AHORA)
    ]
