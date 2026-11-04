"""Servicio de decisión (tareas 3.1 a 3.4 de `aprobacion-reservas`).

Requisitos de la spec `aprobaciones`. Se usan fechas de 2030 y un reloj inyectado
para no depender de la fecha real.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.app.aprobaciones import services
from backend.app.aprobaciones.services import APROBAR, RECHAZAR, decidir
from backend.app.auth.errors import (
    DatosInvalidos,
    EspacioInactivo,
    PermisoInsuficiente,
    ReservaSolapada,
    SolicitudNoEncontrada,
    SolicitudVencida,
    TransicionInvalida,
)
from backend.app.espacios import repositories as repositorio_espacios
from backend.app.extensions import db
from backend.app.models import Reserva
from backend.app.reservas import repositories as repositorio_reservas
from backend.app.usuarios import repositories as repositorio_usuarios

AHORA = datetime(2030, 1, 10, 8, 0, tzinfo=timezone.utc)
MOTIVO = "Sala en mantenimiento"
ACCIONES = [APROBAR, RECHAZAR]


def reloj():
    return AHORA


def _h(hora, minuto=0):
    return datetime(2030, 1, 10, hora, minuto, tzinfo=timezone.utc)


def _decidir(reserva_id, usuario, accion, motivo=MOTIVO):
    return decidir(reserva_id, usuario, accion, motivo if accion == RECHAZAR else None, reloj=reloj)


def _estado(sesion, reserva_id):
    """Estado y motivo confirmados, leídos directamente de la base."""
    sesion.rollback()
    return tuple(sesion.execute(
        select(Reserva.estado, Reserva.motivo_rechazo).where(Reserva.id == reserva_id)
    ).one())


@pytest.fixture
def cuentas(crear_cuenta):
    ids = {
        "solicitante": crear_cuenta("solicitante"),
        "aprobador": crear_cuenta("aprobador"),
        "admin": crear_cuenta("admin"),
    }
    return {rol: repositorio_usuarios.obtener_usuario_por_id(i) for rol, i in ids.items()}


@pytest.fixture
def espacio(nuevo_espacio):
    return nuevo_espacio("Laboratorio A")


@pytest.fixture
def pendiente(sembrar_reserva, espacio, cuentas):
    """Crea una solicitud pendiente del solicitante; devuelve su id."""

    def _crear(inicio=_h(10), fin=_h(12), espacio_id=None, solicitante="solicitante"):
        return sembrar_reserva(espacio_id or espacio, cuentas[solicitante].id, inicio, fin,
                               "pendiente")

    return _crear


# --- 3.1 Existencia, autoría y estado -----------------------------------------


@pytest.mark.parametrize("accion", ACCIONES)
@pytest.mark.parametrize("reserva_id", [999_999, 0, 2_147_483_648], ids=["inexistente", "cero",
                                                                         "fuera_de_rango"])
def test_solicitud_inexistente(sesion, cuentas, accion, reserva_id):
    with pytest.raises(SolicitudNoEncontrada):
        _decidir(reserva_id, cuentas["aprobador"], accion)


@pytest.mark.parametrize("accion", ACCIONES)
@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_nadie_decide_su_propia_solicitud(sesion, cuentas, pendiente, rol, accion):
    reserva_id = pendiente(solicitante=rol)

    with pytest.raises(PermisoInsuficiente):
        _decidir(reserva_id, cuentas[rol], accion)

    assert _estado(sesion, reserva_id) == ("pendiente", None)


@pytest.mark.parametrize("accion", ACCIONES)
@pytest.mark.parametrize("estado", ["aprobada", "rechazada", "cancelada"])
def test_solo_se_decide_sobre_solicitudes_pendientes(sesion, sembrar_reserva, espacio, cuentas,
                                                     estado, accion):
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"].id, _h(10), _h(12), estado)
    antes = _estado(sesion, reserva_id)

    with pytest.raises(TransicionInvalida):
        _decidir(reserva_id, cuentas["aprobador"], accion, "Otro motivo")

    assert _estado(sesion, reserva_id) == antes


def test_una_accion_desconocida_es_un_error_de_desarrollo(sesion, cuentas, pendiente):
    with pytest.raises(ValueError):
        decidir(pendiente(), cuentas["aprobador"], "cancelar")


def test_un_error_de_dominio_libera_el_bloqueo_de_la_fila(sesion, cuentas, pendiente):
    reserva_id = pendiente(solicitante="aprobador")

    with pytest.raises(PermisoInsuficiente):
        _decidir(reserva_id, cuentas["aprobador"], APROBAR)

    with db.engine.connect() as otra:
        otra.execute(text("SET lock_timeout = '2s'"))
        otra.execute(text("SELECT id FROM reservas WHERE id = :id FOR UPDATE"), {"id": reserva_id})
        otra.rollback()


# --- 3.2 Rechazo ----------------------------------------------------------------


def test_rechazo_con_motivo(sesion, cuentas, pendiente):
    reserva_id = pendiente()

    reserva = _decidir(reserva_id, cuentas["aprobador"], RECHAZAR)

    assert (reserva.estado, reserva.motivo_rechazo) == ("rechazada", MOTIVO)
    assert _estado(sesion, reserva_id) == ("rechazada", MOTIVO)


def test_rechazo_por_admin(sesion, cuentas, pendiente):
    assert _decidir(pendiente(), cuentas["admin"], RECHAZAR).estado == "rechazada"


def test_el_motivo_se_guarda_recortado(sesion, cuentas, pendiente):
    reserva_id = pendiente()

    _decidir(reserva_id, cuentas["aprobador"], RECHAZAR, f"  {MOTIVO}\n")

    assert _estado(sesion, reserva_id) == ("rechazada", MOTIVO)


@pytest.mark.parametrize(
    "motivo",
    [None, "", "   ", "\t\n ", "x" * 501, 123, True, ["motivo"], {"texto": "motivo"},
     "con\x00nulo", "sustituto \ud800 suelto"],
    ids=["ausente", "vacio", "espacios", "blancos", "501", "numero", "booleano", "lista",
         "objeto", "nul", "sustituto"],
)
def test_rechazo_con_motivo_invalido(sesion, cuentas, pendiente, motivo):
    reserva_id = pendiente()

    with pytest.raises(DatosInvalidos):
        _decidir(reserva_id, cuentas["aprobador"], RECHAZAR, motivo)

    assert _estado(sesion, reserva_id) == ("pendiente", None)


def test_rechazo_con_500_caracteres(sesion, cuentas, pendiente):
    reserva_id = pendiente()

    _decidir(reserva_id, cuentas["aprobador"], RECHAZAR, "x" * 500)

    assert _estado(sesion, reserva_id) == ("rechazada", "x" * 500)


def test_los_500_caracteres_se_cuentan_tras_recortar(sesion, cuentas, pendiente):
    reserva_id = pendiente()

    _decidir(reserva_id, cuentas["aprobador"], RECHAZAR, f"  {'x' * 500}  ")

    assert _estado(sesion, reserva_id) == ("rechazada", "x" * 500)


def test_al_rechazar_el_motivo_se_valida_antes_que_el_estado(sesion, sembrar_reserva, espacio,
                                                             cuentas):
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"].id, _h(10), _h(12), "aprobada")

    with pytest.raises(DatosInvalidos):
        _decidir(reserva_id, cuentas["aprobador"], RECHAZAR, "   ")


def test_al_rechazar_la_autoria_se_valida_antes_que_el_motivo(sesion, cuentas, pendiente):
    with pytest.raises(PermisoInsuficiente):
        _decidir(pendiente(solicitante="admin"), cuentas["admin"], RECHAZAR, "   ")


def test_rechazo_de_una_pendiente_solapada_con_una_aprobada(sesion, sembrar_reserva, espacio,
                                                            cuentas, pendiente):
    reserva_id = pendiente(_h(11), _h(13))
    sembrar_reserva(espacio, cuentas["solicitante"].id, _h(10), _h(12), "aprobada")

    assert _decidir(reserva_id, cuentas["aprobador"], RECHAZAR).estado == "rechazada"


def test_rechazo_sobre_un_espacio_inactivo(sesion, espacio, cuentas, pendiente):
    reserva_id = pendiente()
    repositorio_espacios.cambiar_estado(repositorio_espacios.obtener_espacio_por_id(espacio),
                                        "inactivo")
    sesion.commit()

    assert _decidir(reserva_id, cuentas["aprobador"], RECHAZAR).estado == "rechazada"


@pytest.mark.parametrize("inicio", [AHORA, AHORA - timedelta(hours=1)], ids=["igual", "anterior"])
def test_rechazo_con_la_solicitud_ya_comenzada(sesion, cuentas, pendiente, inicio):
    reserva_id = pendiente(inicio, inicio + timedelta(hours=2))

    assert _decidir(reserva_id, cuentas["aprobador"], RECHAZAR).estado == "rechazada"


# --- 3.3 Aprobación ---------------------------------------------------------------


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_aprobacion(sesion, cuentas, pendiente, rol):
    reserva_id = pendiente()

    reserva = _decidir(reserva_id, cuentas[rol], APROBAR)

    assert (reserva.estado, reserva.motivo_rechazo) == ("aprobada", None)
    assert _estado(sesion, reserva_id) == ("aprobada", None)


@pytest.mark.parametrize(
    "inicio,fin",
    [(_h(11), _h(13)), (_h(10, 30), _h(11)), (_h(9), _h(14)), (_h(10), _h(12))],
    ids=["parcial", "contenida", "contiene", "identica"],
)
def test_aprobacion_con_solapamiento(sesion, sembrar_reserva, espacio, cuentas, pendiente, inicio,
                                     fin):
    reserva_id = pendiente(inicio, fin)
    sembrar_reserva(espacio, cuentas["solicitante"].id, _h(10), _h(12), "aprobada")

    with pytest.raises(ReservaSolapada):
        _decidir(reserva_id, cuentas["aprobador"], APROBAR)

    assert _estado(sesion, reserva_id) == ("pendiente", None)


@pytest.mark.parametrize("inicio,fin", [(_h(12), _h(13)), (_h(9), _h(10))],
                         ids=["empieza_al_terminar", "termina_al_empezar"])
def test_aprobacion_con_borde_exacto(sesion, sembrar_reserva, espacio, cuentas, pendiente, inicio,
                                     fin):
    reserva_id = pendiente(inicio, fin)
    sembrar_reserva(espacio, cuentas["solicitante"].id, _h(10), _h(12), "aprobada")

    assert _decidir(reserva_id, cuentas["aprobador"], APROBAR).estado == "aprobada"


def test_aprobacion_en_otro_espacio(sesion, sembrar_reserva, espacio, nuevo_espacio, cuentas,
                                    pendiente):
    otro = nuevo_espacio("Laboratorio B")
    sembrar_reserva(otro, cuentas["solicitante"].id, _h(10), _h(12), "aprobada")

    assert _decidir(pendiente(), cuentas["aprobador"], APROBAR).estado == "aprobada"


def test_las_pendientes_solapadas_no_cambian_y_luego_fallan(sesion, cuentas, pendiente):
    primera, en_conflicto = pendiente(_h(10), _h(12)), pendiente(_h(11), _h(13))

    _decidir(primera, cuentas["aprobador"], APROBAR)
    assert _estado(sesion, en_conflicto) == ("pendiente", None)

    with pytest.raises(ReservaSolapada):
        _decidir(en_conflicto, cuentas["aprobador"], APROBAR)
    assert _estado(sesion, en_conflicto) == ("pendiente", None)


def test_aprobacion_sobre_un_espacio_desactivado(sesion, espacio, cuentas, pendiente):
    reserva_id = pendiente()
    repositorio_espacios.cambiar_estado(repositorio_espacios.obtener_espacio_por_id(espacio),
                                        "inactivo")
    sesion.commit()

    with pytest.raises(EspacioInactivo):
        _decidir(reserva_id, cuentas["aprobador"], APROBAR)

    assert _estado(sesion, reserva_id) == ("pendiente", None)


@pytest.mark.parametrize(
    "inicio", [AHORA - timedelta(seconds=1), AHORA], ids=["anterior", "en_el_instante_actual"]
)
def test_aprobacion_de_una_solicitud_ya_comenzada(sesion, cuentas, pendiente, inicio):
    reserva_id = pendiente(inicio, inicio + timedelta(hours=2))

    with pytest.raises(SolicitudVencida):
        _decidir(reserva_id, cuentas["aprobador"], APROBAR)

    assert _estado(sesion, reserva_id) == ("pendiente", None)


def test_aprobacion_de_una_solicitud_que_empieza_justo_despues(sesion, cuentas, pendiente):
    inicio = AHORA + timedelta(microseconds=1)
    reserva = _decidir(pendiente(inicio, inicio + timedelta(hours=1)), cuentas["aprobador"], APROBAR)
    assert reserva.estado == "aprobada"


def test_orden_estado_antes_que_vigencia(sesion, sembrar_reserva, espacio, cuentas):
    vencida = AHORA - timedelta(hours=3)
    reserva_id = sembrar_reserva(espacio, cuentas["solicitante"].id, vencida,
                                 vencida + timedelta(hours=1), "aprobada")

    with pytest.raises(TransicionInvalida):
        _decidir(reserva_id, cuentas["aprobador"], APROBAR)


def test_orden_vigencia_antes_que_espacio_activo(sesion, espacio, cuentas, pendiente):
    vencida = AHORA - timedelta(hours=3)
    reserva_id = pendiente(vencida, vencida + timedelta(hours=1))
    repositorio_espacios.cambiar_estado(repositorio_espacios.obtener_espacio_por_id(espacio),
                                        "inactivo")
    sesion.commit()

    with pytest.raises(SolicitudVencida):
        _decidir(reserva_id, cuentas["aprobador"], APROBAR)


def test_orden_espacio_activo_antes_que_solapamiento(sesion, sembrar_reserva, espacio, cuentas,
                                                     pendiente):
    reserva_id = pendiente(_h(11), _h(13))
    sembrar_reserva(espacio, cuentas["solicitante"].id, _h(10), _h(12), "aprobada")
    repositorio_espacios.cambiar_estado(repositorio_espacios.obtener_espacio_por_id(espacio),
                                        "inactivo")
    sesion.commit()

    with pytest.raises(EspacioInactivo):
        _decidir(reserva_id, cuentas["aprobador"], APROBAR)


# --- 3.4 Violación de la restricción de exclusión ----------------------------------


def test_la_carrera_contra_la_exclusion_se_traduce_a_reserva_solapada(
    sesion, monkeypatch, espacio, cuentas, pendiente
):
    """Entre la comprobación y la actualización, otra conexión confirma una
    reserva aprobada en conflicto: la restricción de exclusión hace fallar la
    actualización de forma determinista."""
    reserva_id = pendiente()
    solicitante_id = cuentas["solicitante"].id
    sesion.commit()
    comprobar = repositorio_reservas.listar_aprobadas_por_espacio_y_rango
    llamadas = []

    def _comprobar_e_insertar_en_conflicto(espacio_id, inicio, fin):
        resultado = comprobar(espacio_id, inicio, fin)
        llamadas.append(resultado)
        with db.engine.begin() as otra:
            otra.execute(
                text(
                    "INSERT INTO reservas (espacio_id, solicitante_id, inicio_utc, fin_utc, estado)"
                    " VALUES (:espacio, :solicitante, :inicio, :fin, 'aprobada')"
                ),
                {"espacio": espacio_id, "solicitante": solicitante_id, "inicio": inicio, "fin": fin},
            )
        return resultado

    monkeypatch.setattr(repositorio_reservas, "listar_aprobadas_por_espacio_y_rango",
                        _comprobar_e_insertar_en_conflicto)

    with pytest.raises(ReservaSolapada):
        _decidir(reserva_id, cuentas["aprobador"], APROBAR)

    assert llamadas == [[]]  # La comprobación del servicio pasó: falló la restricción.
    assert _estado(sesion, reserva_id) == ("pendiente", None)
    # La transacción se deshizo: la sesión sigue utilizable.
    assert sesion.execute(text("SELECT 1")).scalar_one() == 1


def test_aprobar_bloquea_el_espacio_sin_impedir_nuevas_solicitudes(
    sesion, monkeypatch, espacio, cuentas, pendiente
):
    """Durante la comprobación de solapamiento, el espacio está bloqueado frente
    a otra aprobación, pero no frente a las claves foráneas de una solicitud nueva."""
    reserva_id = pendiente()
    comprobar = repositorio_reservas.listar_aprobadas_por_espacio_y_rango
    consulta = "SELECT id FROM espacios WHERE id = :id FOR {modo} NOWAIT"
    comprobado = []

    def _comprobar_con_el_bloqueo_tomado(espacio_id, inicio, fin):
        with db.engine.connect() as otra:
            with pytest.raises(OperationalError) as error:
                otra.execute(text(consulta.format(modo="NO KEY UPDATE")), {"id": espacio_id})
            assert error.value.orig.sqlstate == "55P03"
            otra.rollback()
            otra.execute(text(consulta.format(modo="KEY SHARE")), {"id": espacio_id})
            otra.rollback()
        comprobado.append(True)
        return comprobar(espacio_id, inicio, fin)

    monkeypatch.setattr(repositorio_reservas, "listar_aprobadas_por_espacio_y_rango",
                        _comprobar_con_el_bloqueo_tomado)

    assert _decidir(reserva_id, cuentas["aprobador"], APROBAR).estado == "aprobada"
    assert comprobado == [True]

    # Al confirmar, el bloqueo se libera.
    with db.engine.connect() as otra:
        otra.execute(text(consulta.format(modo="NO KEY UPDATE")), {"id": espacio})
        otra.rollback()


def test_otra_violacion_de_integridad_no_se_traduce(sesion, monkeypatch, cuentas, pendiente):
    """Un `CHECK` real (rechazada sin motivo) no es la restricción de exclusión:
    sigue siendo un error interno y la transacción se deshace."""
    reserva_id = pendiente()
    monkeypatch.setattr(services, "_validar_motivo", lambda _motivo: None)

    with pytest.raises(IntegrityError) as error:
        _decidir(reserva_id, cuentas["aprobador"], RECHAZAR)

    assert error.value.orig.sqlstate == "23514"
    assert _estado(sesion, reserva_id) == ("pendiente", None)
