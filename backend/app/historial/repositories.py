"""Repositorio del historial: acceso a datos con SQLAlchemy.

No confirma transacciones: `registrar` escribe en la transacción del cambio de
estado que la llama, de modo que ambos se confirman o se deshacen juntos.
"""

from sqlalchemy import select

from ..extensions import db
from ..models import EntradaHistorial, Reserva
from ..models.usuario import ahora_utc

# Valor de `usuario_id_o_todos` para consultar sin restringir por solicitante.
TODOS = object()


def registrar(sesion, reserva, estado_anterior, estado_nuevo, actor, reloj=ahora_utc):
    """Añade la entrada del cambio de estado; la fecha sale del reloj inyectable."""
    entrada = EntradaHistorial(
        reserva_id=reserva.id,
        espacio_id=reserva.espacio_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        actor_id=actor.id,
        fecha_utc=reloj(),
    )
    sesion.add(entrada)
    sesion.flush()
    return entrada


def listar(usuario_id_o_todos, espacio_id=None, estado=None, desde=None, hasta=None):
    """Entradas visibles por fecha ascendente y luego por id, en el rango `[desde, hasta)`.

    La restricción al solicitante se aplica antes que los filtros, que se combinan
    con Y lógico. `estado` filtra por el estado nuevo.
    """
    consulta = select(EntradaHistorial)
    if usuario_id_o_todos is not TODOS:
        consulta = consulta.join(Reserva, Reserva.id == EntradaHistorial.reserva_id).where(
            Reserva.solicitante_id == usuario_id_o_todos
        )
    if espacio_id is not None:
        consulta = consulta.where(EntradaHistorial.espacio_id == espacio_id)
    if estado is not None:
        consulta = consulta.where(EntradaHistorial.estado_nuevo == estado)
    if desde is not None:
        consulta = consulta.where(EntradaHistorial.fecha_utc >= desde)
    if hasta is not None:
        consulta = consulta.where(EntradaHistorial.fecha_utc < hasta)
    return db.session.execute(
        consulta.order_by(EntradaHistorial.fecha_utc, EntradaHistorial.id)
    ).scalars().all()
