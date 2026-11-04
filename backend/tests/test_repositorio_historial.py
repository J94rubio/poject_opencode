"""Repositorio del historial (tareas 2.1 y 2.2 de `cancelacion-historial`).

Requisitos «Filtros del historial» y «Consulta del historial según el rol» de la
spec `historial`.
"""

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.historial import repositories
from backend.app.historial.repositories import TODOS, listar, registrar
from backend.app.reservas import repositories as repositorio_reservas
from backend.app.usuarios import repositories as repositorio_usuarios

BASE = datetime(2030, 3, 1, 12, tzinfo=timezone.utc)


def _dia(numero):
    return BASE + timedelta(days=numero)


@pytest.fixture
def mundo(sesion, crear_cuenta, nuevo_espacio):
    """Dos solicitantes, un aprobador y dos espacios, con estas entradas:

    A (Sara, espacio 1): día 0 creación, día 2 aprobación por el aprobador.
    B (Sara, espacio 2): día 1 creación.
    C (Otro, espacio 1): día 3 creación, día 4 rechazo por el aprobador.
    """
    cuentas = {
        "sara": repositorio_usuarios.obtener_usuario_por_id(
            crear_cuenta("solicitante", correo="sara@example.com")),
        "otro": repositorio_usuarios.obtener_usuario_por_id(
            crear_cuenta("solicitante", correo="otro@example.com")),
        "aprobador": repositorio_usuarios.obtener_usuario_por_id(crear_cuenta("aprobador")),
    }
    espacios = {"uno": nuevo_espacio("Espacio uno"), "dos": nuevo_espacio("Espacio dos")}

    def _reserva(espacio, cuenta, desfase):
        inicio = _dia(100 + desfase)
        return repositorio_reservas.crear(espacios[espacio], cuentas[cuenta].id,
                                          inicio, inicio + timedelta(hours=1))

    a, b, c = _reserva("uno", "sara", 0), _reserva("dos", "sara", 1), _reserva("uno", "otro", 2)

    def _anotar(reserva, anterior, nuevo, actor, dia):
        return registrar(sesion, reserva, anterior, nuevo, cuentas[actor],
                         reloj=lambda: _dia(dia)).id

    entradas = {
        "a_creada": _anotar(a, None, "pendiente", "sara", 0),
        "b_creada": _anotar(b, None, "pendiente", "sara", 1),
        "a_aprobada": _anotar(a, "pendiente", "aprobada", "aprobador", 2),
        "c_creada": _anotar(c, None, "pendiente", "otro", 3),
        "c_rechazada": _anotar(c, "pendiente", "rechazada", "aprobador", 4),
    }
    sesion.commit()
    return {"cuentas": cuentas, "espacios": espacios, "reservas": (a, b, c), "entradas": entradas}


def _ids(entradas):
    return [e.id for e in entradas]


def _esperadas(mundo, *nombres):
    return [mundo["entradas"][n] for n in nombres]


def test_registrar_copia_la_reserva_y_usa_el_reloj_inyectado(mundo, sesion):
    a, _, _ = mundo["reservas"]
    sesion.rollback()

    entrada = registrar(sesion, a, "aprobada", "cancelada", mundo["cuentas"]["sara"],
                        reloj=lambda: _dia(9))

    assert (entrada.reserva_id, entrada.espacio_id, entrada.estado_anterior, entrada.estado_nuevo,
            entrada.actor_id, entrada.fecha_utc) == (
        a.id, a.espacio_id, "aprobada", "cancelada", mundo["cuentas"]["sara"].id, _dia(9))


def test_registrar_no_confirma_la_transaccion(mundo, sesion):
    a, _, _ = mundo["reservas"]
    registrar(sesion, a, "aprobada", "cancelada", mundo["cuentas"]["sara"], reloj=lambda: _dia(9))
    sesion.rollback()
    assert len(listar(TODOS)) == len(mundo["entradas"])


def test_sin_filtros_devuelve_todas_por_fecha(mundo):
    assert _ids(listar(TODOS)) == _esperadas(
        mundo, "a_creada", "b_creada", "a_aprobada", "c_creada", "c_rechazada")


def test_filtro_por_espacio(mundo):
    assert _ids(listar(TODOS, espacio_id=mundo["espacios"]["dos"])) == _esperadas(mundo, "b_creada")


def test_filtro_por_estado_coincide_con_el_estado_nuevo(mundo):
    """`pendiente` es estado anterior de la aprobación, pero solo cuenta el nuevo."""
    assert _ids(listar(TODOS, estado="pendiente")) == _esperadas(
        mundo, "a_creada", "b_creada", "c_creada")
    assert _ids(listar(TODOS, estado="rechazada")) == _esperadas(mundo, "c_rechazada")


def test_filtro_por_rango_incluye_desde_y_excluye_hasta(mundo):
    assert _ids(listar(TODOS, desde=_dia(1), hasta=_dia(3))) == _esperadas(
        mundo, "b_creada", "a_aprobada")


def test_el_limite_inferior_del_rango_se_incluye(mundo):
    assert _ids(listar(TODOS, desde=_dia(2), hasta=_dia(2) + timedelta(seconds=1))) == _esperadas(
        mundo, "a_aprobada")


def test_el_limite_superior_del_rango_se_excluye(mundo):
    assert _ids(listar(TODOS, desde=_dia(2) - timedelta(seconds=1), hasta=_dia(2))) == []


def test_filtros_combinados(mundo):
    assert _ids(listar(TODOS, espacio_id=mundo["espacios"]["uno"], estado="pendiente",
                       desde=_dia(0), hasta=_dia(3))) == _esperadas(mundo, "a_creada")
    assert _ids(listar(TODOS, espacio_id=mundo["espacios"]["dos"], estado="aprobada")) == []


def test_a_igual_fecha_se_ordena_por_identificador(mundo, sesion):
    a, b, c = mundo["reservas"]
    sesion.rollback()
    sara = mundo["cuentas"]["sara"]
    fecha = _dia(20)
    ids = [
        registrar(sesion, reserva, "pendiente", "cancelada", sara, reloj=lambda: fecha).id
        for reserva in (c, a, b)
    ]
    sesion.commit()

    assert _ids(listar(TODOS, desde=fecha, hasta=fecha + timedelta(seconds=1))) == sorted(ids)


# --- 2.2 Restricción al solicitante -------------------------------------------


def test_restringido_devuelve_las_entradas_de_sus_reservas_incluidas_decisiones_ajenas(mundo):
    entradas = listar(mundo["cuentas"]["sara"].id)

    assert _ids(entradas) == _esperadas(mundo, "a_creada", "b_creada", "a_aprobada")
    assert mundo["cuentas"]["aprobador"].id in {e.actor_id for e in entradas}


def test_el_actor_de_una_decision_no_ve_por_ello_la_entrada(mundo):
    assert listar(mundo["cuentas"]["aprobador"].id) == []


def test_la_restriccion_se_mantiene_con_el_filtro_de_espacio(mundo):
    """El espacio 1 tiene entradas de otro solicitante que no deben aparecer."""
    assert _ids(listar(mundo["cuentas"]["sara"].id, espacio_id=mundo["espacios"]["uno"])) == (
        _esperadas(mundo, "a_creada", "a_aprobada"))
    assert _ids(listar(mundo["cuentas"]["otro"].id, espacio_id=mundo["espacios"]["dos"])) == []


def test_la_restriccion_se_mantiene_con_todos_los_filtros(mundo):
    assert _ids(listar(mundo["cuentas"]["otro"].id, mundo["espacios"]["uno"], "pendiente",
                       _dia(0), _dia(9))) == _esperadas(mundo, "c_creada")


def test_ninguna_id_de_usuario_equivale_a_todos(mundo):
    assert repositories.TODOS is not None
    assert listar(None) == []
